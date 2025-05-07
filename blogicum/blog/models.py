from django.contrib.auth import get_user_model
from django.db import models

from .managers import PublishedPostManager
from .querysets import PostQuerySet

MAX_CHARFIELD_LENGHT: int = 256
MAX_ADMIN_FIELD_LENGHT: int = 16
User = get_user_model()


def convert_long_string(input: str) -> str:
    """Обрезает длинную строку до заданной длины и добавляет многоточие."""
    if len(input) > MAX_ADMIN_FIELD_LENGHT:
        return input[: MAX_ADMIN_FIELD_LENGHT - 3] + '...'
    return input


class CreatedFieldModel(models.Model):
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class PostInformationModel(CreatedFieldModel):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True
        ordering = ('-created_at')


class Category(PostInformationModel):
    title = models.CharField('Заголовок', max_length=MAX_CHARFIELD_LENGHT)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return convert_long_string(self.title)


class Location(PostInformationModel):
    name = models.CharField('Название места', max_length=MAX_CHARFIELD_LENGHT)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return convert_long_string(self.name)


class Post(PostInformationModel):
    title = models.CharField('Заголовок', max_length=MAX_CHARFIELD_LENGHT)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем — '
                  'можно делать отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)

    objects = PostQuerySet.as_manager()
    published = PublishedPostManager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'
        ordering = ('-pub_date', 'title')

    def comment_count(self):
        return self.comments.count()

    def __str__(self):
        return convert_long_string(self.title)


class Comment(CreatedFieldModel):
    text = models.TextField('Текст комментария')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'
        ordering = ('created_at',)

    def __str__(self):
        return convert_long_string(self.title)
