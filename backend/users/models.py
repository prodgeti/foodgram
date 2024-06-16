from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from foodgram_backend import constants


class CustomUser(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    first_name = models.CharField(
        max_length=constants.FIRST_NAME_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_LENGTH,
        verbose_name='Фамилия',
    )
    username = models.CharField(
        max_length=constants.USERNAME_LENGTH,
        unique=True,
        verbose_name='Логин',
        help_text='Введите логин пользователя',
        validators=[
            UnicodeUsernameValidator()
        ],
    )
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail',
        help_text='Введите email пользователя'
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars',
        null=True,
        blank=True
    )

    class Meta:
        """Класс Meta модели User."""
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для хранения информации о подписках."""

    follower = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',

    )
    publisher = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецепта',

    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'publisher'], name='unique_following'
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('publisher')),
                name='self-subscription'
            ),
        ]

    def __str__(self):
        return (
            f'Подписка {self.follower.username} на {self.publisher.username}'
        )
