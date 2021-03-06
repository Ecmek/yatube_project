import datetime as dt

from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model

from tinymce import models as tinymce_models

User = get_user_model()


class Ip(models.Model):
    ip = models.CharField(
        max_length=100, verbose_name='ip пользователя',
        )

    def __str__(self):
        return self.ip


class PageHit(models.Model):
    client = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='page_hit',
        verbose_name='Кто переходил',
    )
    url = models.CharField(max_length=100)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['client', '-count']


class Group(models.Model):
    title = models.CharField(
        max_length=200, null=False,
        verbose_name='Название тематики',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Url адрес тематики',
    )
    description = models.TextField(
        verbose_name='Описание тематики',
    )

    class Meta:
        verbose_name = 'Тематика'
        verbose_name_plural = 'Тематики'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = tinymce_models.HTMLField(
        verbose_name='Текст статьи',
        help_text='Что у вас нового?'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор статьи',
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='group_posts',
        verbose_name='Тематика статьи',
        help_text='Можете выбрать тематику'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name='Изображение',
        help_text='Можете загрузить изображение',
    )
    views = models.ManyToManyField(
        Ip, related_name="post_views",
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.text[:15]

    def is_recently_pub(self):
        now = timezone.now()
        return self.pub_date >= (now - dt.timedelta(hours=1))

    def total_views(self):
        return self.views.count()


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Cтатья с комментариями',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    text = tinymce_models.HTMLField(
        verbose_name='Комментарий',
        help_text='Напишите комменатрий',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]

    def is_recently_pub(self):
        now = timezone.now()
        return self.created >= (now - dt.timedelta(minutes=20))


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Отслеживается',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique subs')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
