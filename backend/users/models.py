from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator

from foodgram_backend import constants


class CustomUser(AbstractUser):
    """
    Модель пользователя.

    Поля:
    ---------
    first_name (str): Имя пользователя.
    last_name (str): Фамилия пользователя.
    username (str): Имя пользователя для входа.
    email (str): Адрес электронной почты пользователя.
    аватар (img): Аватар пользователя.

    Мета:
    -----
        verbose_name (str): удобочитаемое имя модели.
        порядок (список): порядок модели по умолчанию.

    Методы:
    -------
    __str__(): возвращает имя пользователя в виде строки.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    first_name = models.CharField(
        max_length=constants.FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя',
        help_text='Введите имя пользователя'
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия',
        help_text='Введите фамилию пользователя'
    )
    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
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
    """
    Модель для хранения информации о подписках.

    Поля:
    - user (User): Пользователь (связь с моделью User).
    - following (User): Подписчик (связь с моделью User).
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_user_following'
            ),
            models.CheckConstraint(
                check=models.Q(
                    user=models.F('user')),
                name='prevent_self_follow'
            ),
        ]

    def __str__(self):
        return f'Подписка {self.following.username} на {self.user.username}'
