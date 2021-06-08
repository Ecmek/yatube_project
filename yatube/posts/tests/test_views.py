import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group, User

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        # Создаем юзера, для автора поста
        cls.user = User.objects.create(
            username='post_author',
        )
        # Создаем группу
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        # Подготавливаем изображение
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создаем пост
        cls.post = Post.objects.create(
            text='Рандомный текст',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
            image=uploaded,
        )
        # группа без постов
        cls.group_fake = Group.objects.create(
            title='Фейк группа',
            slug='fake-slug',
            description='Описание фейк группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Авторизовываем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.follower = User.objects.create(
            username='follower'
        )
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.user.username}))
        cache.clear()

    def test_views_use_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'index.html',
            reverse('posts:group_slug',
                    kwargs={'slug': self.group.slug}): 'group.html',
            reverse('posts:new_post'): 'new_post.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): 'profile.html',
            reverse('posts:post',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}): 'post.html',
            reverse('posts:follow_index'): 'follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        context = {reverse('posts:index'): self.post,
                   reverse('posts:group_slug',
                   kwargs={'slug': self.group.slug,
                           }): self.post,
                   reverse('posts:profile',
                   kwargs={'username': self.user.username,
                           }): self.post,
                   reverse('posts:follow_index'): self.post,
                   }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.follower_client.get(reverse_page)
                page_object = response.context['page'][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.pub_date, object.pub_date)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)
                self.assertEqual(page_object.image, object.image)

    def test_groups_page_show_correct_context(self):
        context = {reverse('posts:group_slug',
                   kwargs={'slug': self.group.slug}): self.group,
                   reverse('posts:group_slug',
                   kwargs={'slug': self.group_fake.slug}): self.group_fake,
                   }
        response = self.authorized_client.get(
            reverse('posts:group_slug',
                    kwargs={'slug': self.group_fake.slug}))
        self.assertFalse(response.context['page'])
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                group_object = response.context['group']
                self.assertEqual(group_object.title, object.title)
                self.assertEqual(group_object.slug, object.slug)
                self.assertEqual(group_object.description,
                                 object.description)

    def test_authors_show_correct_context(self):
        context = {reverse('posts:profile',
                   kwargs={'username': self.user.username}): self.user,
                   reverse('posts:post',
                   kwargs={'username': self.user.username,
                           'post_id': self.post.id}): self.user,
                   }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                author_object = response.context['author']
                self.assertEqual(author_object.id, object.id)
                self.assertEqual(author_object.username, object.username)

    def test_post_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}))
        post_object = response.context['post']
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.pub_date, self.post.pub_date)
        self.assertEqual(post_object.author, self.user)
        self.assertEqual(post_object.group, self.group)
        self.assertEqual(post_object.image, self.post.image)

    def test_forms_show_correct_instance(self):
        context = {
            reverse('posts:new_post'),
            reverse('posts:post_edit',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id,
                            }),
        }
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(response.context['form'].fields['text'],
                                      forms.fields.CharField)
                self.assertIsInstance(response.context['form'].fields['group'],
                                      forms.fields.ChoiceField)
                self.assertIsInstance(response.context['form'].fields['image'],
                                      forms.fields.ImageField)

    def test_forms_post_show_correct_instance(self):
        response = self.authorized_client.get(
            reverse('posts:post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id
                    }))
        self.assertIsInstance(response.context['form'].fields['text'],
                              forms.fields.CharField)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        # Создаем 13 постов
        cls.post = [
            Post.objects.create(
                text='Пост №' + str(i),
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group
            )
            for i in range(13)]

    def setUp(self):
        cache.clear()
        self.follower = User.objects.create(
            username='follower'
        )
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.user.username}))

    def test_paginator_on_pages(self):
        first_page_len_posts = 10
        second_page_len_posts = 3
        context = {
            reverse('posts:index'): first_page_len_posts,
            reverse('posts:index') + '?page=2': second_page_len_posts,
            reverse('posts:group_slug', kwargs={'slug': self.group.slug, }):
            first_page_len_posts,
            reverse('posts:group_slug', kwargs={'slug': self.group.slug, })
            + '?page=2': second_page_len_posts,
            reverse('posts:profile', kwargs={'username': self.user.username}):
            first_page_len_posts,
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2': second_page_len_posts,
            reverse('posts:follow_index'): first_page_len_posts,
            reverse('posts:follow_index') + '?page=2': second_page_len_posts,
        }
        for reverse_page, len_posts in context.items():
            with self.subTest(reverse=reverse):
                self.assertEqual(len(self.follower_client.get(
                    reverse_page).context.get('page')), len_posts)

    def test_object_list_first_page(self):
        response = self.client.get(reverse('posts:index'))
        for i in range(10):
            page_object = response.context.get('page').object_list[i]
            expected_object = response.context['page'][i]
            self.assertEqual(page_object.author, expected_object.author)
            self.assertEqual(page_object.text, expected_object.text)
            self.assertEqual(page_object.group, expected_object.group)
            self.assertEqual(page_object.pub_date,
                             expected_object.pub_date)

    def test_object_list_second_page(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        for i in range(3):
            page_object = response.context.get('page').object_list[i]
            expected_object = response.context['page'][i]
            self.assertEqual(page_object.author, expected_object.author)
            self.assertEqual(page_object.text, expected_object.text)
            self.assertEqual(page_object.group, expected_object.group)
            self.assertEqual(page_object.pub_date,
                             expected_object.pub_date)


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )

    def setUp(self):
        # Авторизовываем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        content = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.create(
            text='Пост №1',
            author=self.user,
        )
        content_1 = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(content, content_1)
        cache.clear()
        content_2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(content_1, content_2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='posts_author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Рандомный текст статьи',
        )

    def setUp(self):
        cache.clear()
        # Клиент подписчика
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        # Клиент автора
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow_page_context(self):
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page').object_list
        self.assertEqual((len(page_object)), 0)
        # Подписываемся на автора
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(response.context['page'])), 1)
        page_object = response.context.get('page').object_list[0]
        self.assertEqual(page_object.author, self.author)
        self.assertEqual(page_object.text, self.post.text)
        self.assertEqual(page_object.pub_date, self.post.pub_date)
        # Отписываемся от автора
        self.follower_client.get(reverse('posts:profile_unfollow',
                                 kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page').object_list
        self.assertEqual((len(page_object)), 0)

    def test_u_cant_following_self(self):
        response = self.author_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page').object_list
        self.assertEqual((len(page_object)), 0)
        self.author_client.get(
            reverse('posts:profile_follow',
                    kwargs={
                        'username': self.author.username
                    })
        )
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(page_object)), 0)
