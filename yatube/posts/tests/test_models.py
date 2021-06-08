from django.test import TestCase

from posts.models import Post, Group, User, Comment, Follow


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем юзера, для автора поста
        cls.user = User.objects.create_user(
            username='post_author',
        )
        cls.user_2 = User.objects.create_user(
            username='another_user',
        )
        # Создаем группу
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        # Создаем пост
        cls.post = Post.objects.create(
            text='рандомный текст больше чем на 15 символов',
            author=PostsModelTest.user,
            group=PostsModelTest.group,
        )
        # Комментарий
        cls.comment = Comment.objects.create(
            post=PostsModelTest.post,
            author=PostsModelTest.user,
            text='Рандомный комментарий',
        )
        # Подписка
        cls.follow = Follow.objects.create(
            user=PostsModelTest.user_2,
            author=PostsModelTest.user,
        )

    def test_post_verbose_name(self):
        post = self.post
        field_verboses = {
            'text': 'Текст статьи',
            'pub_date': 'Дата публикации',
            'author': 'Автор статьи',
            'group': 'Тематика статьи',
            'image': 'Изображение',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        post = self.post
        feild_help_texts = {
            'text': 'Что у вас нового?',
            'group': 'Можете выбрать тематику',
            'image': 'Можете загрузить изображение',
        }
        for value, expected in feild_help_texts.items():
            with self.subTest(value=value):
                help_text = post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)

    def test_group_verbose_name(self):
        group = self.group
        field_verboses = {
            'title': 'Название тематики',
            'slug': 'Url адрес тематики',
            'description': 'Описание тематики',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = group._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_verbose_name(self):
        comment = self.comment
        field_verboses = {
            'post': 'Cтатья с комментариями',
            'author': 'Автор комментария',
            'text': 'Комментарий',
            'created': 'Дата публикации',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_verbose_name(self):
        follow = self.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Отслеживается',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_help_text(self):
        comment = self.comment
        help_text = comment._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Напишите комменатрий')

    def test_object_name(self):
        post = self.post
        group = self.group
        comment = self.comment
        str_objects_names = {
            post.text[:15]: str(post),
            group.title: str(group),
            comment.text[:15]: str(comment),
        }
        for value, expected in str_objects_names.items():
            self.assertEqual(value, expected)
