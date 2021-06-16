from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()

index = '/'
group = 'group'
test_slug = 'test_slug'
fake_slug = 'fake_slug'
new_post = 'new'
post_edit = 'edit'
post_delete = 'delete'
follow_index = 'follow'
profile_follow = 'follow'
profile_unfollow = 'unfollow'
post_author = 'post_author'
another_user = 'another_user'
fake_author = 'fake_author'
login = 'auth/login'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим группу для проверки доступа к /group/test-slug/
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        # Создаем автора поста
        cls.user = User.objects.create_user(
            username='post_author'
        )
        # Создаем обычного пользователя
        cls.user_2 = User.objects.create_user(
            username='another_user'
        )
        # Создаем пост от имени post_author
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=StaticURLTests.user,
            group=StaticURLTests.group,
        )

    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()
        # Авторизовыаем автора поста
        self.post_author = Client()
        self.post_author.force_login(self.user)
        # Авторизовыаем обычного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        cache.clear()

    def test_guest_client_urls_status_code(self):
        # статус коды НЕ авторизованного пользователя
        field_response_urls_code = {
            f'{index}': 200,
            f'/{group}/{test_slug}/': 200,
            f'/{group}/{fake_slug}/': 404,
            f'/{new_post}/': 302,
            f'/{follow_index}/': 302,
            f'/{post_author}/{profile_follow}/': 302,
            f'/{post_author}/{profile_unfollow}/': 302,
            f'/{post_author}/': 200,
            f'/{post_author}/1/': 200,
            f'/{post_author}/1/{post_edit}/': 302,
            f'/{post_author}/1/{post_delete}/': 302,
            f'/{fake_author}/': 404,
            f'/{fake_author}/1/': 404,
        }
        for url, response_code in field_response_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_authorized_client_urls_status_code(self):
        # Статус коды авторизованного пользователя
        field_response_urls_code = {
            f'{index}': 200,
            f'/{group}/{test_slug}/': 200,
            f'/{group}/{fake_slug}/': 404,
            f'/{follow_index}/': 200,
            f'/{new_post}/': 200,
            f'/{post_author}/{profile_follow}/': 302,
            f'/{post_author}/{profile_unfollow}/': 302,
            f'/{another_user}/{profile_follow}/': 302,
            f'/{another_user}/{profile_unfollow}/': 302,
            f'/{post_author}/': 200,
            f'/{post_author}/1/': 200,
            f'/{post_author}/1/{post_edit}/': 302,
        }
        for url, response_code in field_response_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_guest_client_redirect(self):
        # Проверка на редирект НЕ авторизованного пользователя
        redirect_response = {
            f'/{new_post}/': f'/{login}/?next=/{new_post}/',
            f'/{post_author}/1/{post_edit}/': f'/{post_author}/1/',
            f'/{follow_index}/': f'/{login}/?next=/{follow_index}/',
            f'/{another_user}/{profile_follow}/':
            f'/{login}/?next=/{another_user}/{profile_follow}/',
            f'/{another_user}/{profile_unfollow}/':
            f'/{login}/?next=/{another_user}/{profile_unfollow}/',
        }
        for url, redirect in redirect_response.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect)

    def test_authorized_client_redirect(self):
        # проверка на редирект, не автора поста
        response = self.authorized_client.get(f'/{post_author}/1/{post_edit}/')
        self.assertRedirects(response, f'/{post_author}/1/')

    def test_author_post_status_code(self):
        # Доступносить редактирования автору поста
        response = self.post_author.get(
            f'/{post_author}/1/{post_edit}/'
        ).status_code
        self.assertEqual(response, 200)

    def test_urls_use_correct_template(self):
        # Юрл использует соответсвующий шаблон
        templates_url_names = {
            f'{index}': 'index.html',
            f'/{group}/{test_slug}/': 'group.html',
            f'/{follow_index}/': 'follow.html',
            f'/{new_post}/': 'new_post.html',
            f'/{post_author}/': 'profile.html',
            f'/{post_author}/1/': 'post.html',
            f'/{post_author}/1/{post_edit}/': 'new_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                adress_url = self.post_author.get(adress)
                self.assertTemplateUsed(adress_url, template)
