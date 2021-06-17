import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Папка с временными файлами
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Анонимный пользователь
        self.guest_client = Client()
        # Авторизованный пользователь
        self.user = User.objects.create_user(username='post_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_authorized_client_create_post(self):
        # Проверка создания поста авторизованного пользователя
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        cache.clear()
        post_request = self.client.get(reverse('posts:index'))
        first_object = post_request.context['page'][0]
        self.assertEqual(first_object.text, 'Текст поста')
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.image.name, 'posts/small.gif')
        self.assertEqual(first_object.group, self.group)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                author=self.user,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_author_post_delete_post(self):
        post_count = Post.objects.count()
        self.assertEqual(post_count, 0)
        form_data = {
            'text': 'Текст поста'
        }
        self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.last()
        response = self.authorized_client.get(
            reverse('posts:post_delete',
                    kwargs={
                        'username': self.user.username,
                        'post_id': post.id,
                    }))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), 0)

    def test_guest_client_delete_post(self):
        self.assertEqual(Post.objects.count(), 0)
        form_data = {
            'text': 'Текст поста'
        }
        self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        response = self.guest_client.get(
            reverse('posts:post_delete',
                    kwargs={
                        'username': self.user.username,
                        'post_id': post.id,
                    }))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), 1)

    def test_guest_client_create_post(self):
        # Анонимный пользователь не может создать пост
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('login')
        new = reverse('posts:new_post')
        redirect = login + '?next=' + new
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), 0)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем юзера, для автора поста
        cls.user = User.objects.create_user(
            username='post_author',
        )
        # Создаем группу
        cls.group_1 = Group.objects.create(
            title='Тестовое название группы',
            slug='group1-slug',
            description='Тестовое описание группы',
        )
        # Создаем пост
        cls.post = Post.objects.create(
            text='рандомный текст',
            author=PostEditFormTests.user,
            group=PostEditFormTests.group_1,
        )
        # группа без постов
        cls.group_2 = Group.objects.create(
            title='Фейк группа',
            slug='group2-slug',
            description='Описание фейк группы',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Анонимный пользователь
        self.guest_client = Client()
        # Авторизовываем автора
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Случайный авторизованный пользователь
        self.user_2 = User.objects.create_user(username='another_user')
        self.anouther_user = Client()
        self.anouther_user.force_login(self.user_2)
        cache.clear()

    def test_author_edit_post(self):
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
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.id,
            }))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_request = self.authorized_client.get(reverse('posts:index'))
        first_object = post_request.context.get('page').object_list[0]
        self.assertEqual(first_object.text, 'Новый текст поста')
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.image.name, 'posts/small.gif')
        self.assertEqual(first_object.group, self.group_2)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст поста',
                author=self.user,
                group=self.group_2,
                image='posts/small.gif'
            ).exists()
        )
        self.assertEqual(Post.objects.filter(group=self.group_1).count(), 0)

    def test_guest_client_edit_post(self):
        # Анонимный пользователь не может редактировать пост
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_2.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post',
                             kwargs={
                                 'username': self.user.username,
                                 'post_id': self.post.id,
                             }),)
        self.assertTrue(
            Post.objects.filter(
                text='рандомный текст',
                author=self.user,
                group=self.group_1,
            ).exists()
        )

    def test_another_user_edit_post(self):
        # Другой пользователь не может редактировать чужой пост
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_2.id,
        }
        response = self.anouther_user.post(
            reverse('posts:post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post',
                             kwargs={
                                 'username': self.user.username,
                                 'post_id': self.post.id,
                             }),)
        self.assertTrue(
            Post.objects.filter(
                text='рандомный текст',
                author=self.user,
                group=self.group_1,
            ).exists()
        )


class CommentPostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем юзера, для автора поста
        cls.user = User.objects.create_user(
            username='post_author',
        )
        # Создаем пост
        cls.post = Post.objects.create(
            text='Рандомный текст',
            author=CommentPostCreateTest.user,
        )
        cls.form = CommentForm()

    def setUp(self):
        # Анонимный пользователь
        self.guest_client = Client()
        # Авторизовываем автора
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_add_comment(self):
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post',
                             kwargs={
                                 'username': self.user.username,
                                 'post_id': self.post.id,
                             }))
        self.assertEqual(self.post.comments.count(), 1)
        comment_request = self.authorized_client.get(
            reverse('posts:post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }))
        first_object = comment_request.context['comments'][0]
        self.assertEqual(first_object.text, 'Текст комментария')
        self.assertEqual(first_object.author, self.user)

    def test_guest_client_add_comment(self):
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('login')
        post = reverse('posts:add_comment', kwargs={
            'username': self.user.username,
            'post_id': self.post.id,
        })
        redirect = login + '?next=' + post
        self.assertRedirects(response, redirect)
        self.assertEqual(self.post.comments.count(), 0)
