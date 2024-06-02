from random import randint
from string import ascii_lowercase, ascii_uppercase, digits

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from foodgram_backend import constants


User = get_user_model()


class Tag(models.Model):
    """
    Модель для хранения информации о тегах.

    Поля:
    - name (str): Название тега.
    - slug (str): Уникальное сокращение для URL.
    """

    name = models.CharField(
        max_length=constants.TAG_MAX_LENGTH,
        db_index=True,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=constants.TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Уникальный слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель для хранения информации об ингредиентах.

    Поля:
    - name (str): Название ингредиента.
    - measurement_unit (str): Единицы измерения.
    """

    name = models.CharField(
        max_length=constants.INGR_MAX_LENGTH,
        db_index=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASURMENT_MAX_LENGTH,
        verbose_name='Единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_name_unit'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель для хранения информации о рецептах.

    Поля:
    - author (User): Автор публикации (связь с моделью User).
    - name (str): Название рецепта.
    - image (ImageField): Изображение рецепта.
    - text (str): Текстовое описание.
    - ingredients (ManyToManyField): Список ингредиентов (связь с моделью
      Ingredient через промежуточную модель RecipeIngredient).
    - tags (ManyToManyField): Теги рецепта (связь с моделью Tag).
    - cooking_time (int): Время приготовления в минутах.
    - pub_date (datetime): Дата публикации.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации',
        db_index=True
    )
    name = models.CharField(
        max_length=constants.RECIPE_MAX_LENGTH,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes',
        null=True,
        blank=True,
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                constants.MIN_TIME,
                message=f'Время не может быть меньше {constants.MIN_TIME}',
            ),
            MaxValueValidator(
                constants.MAX_TIME,
                message=f'Время не может быть больше {constants.MAX_TIME}',
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель для хранения информации об ингредиентах в рецептах.

    Поля:
    - recipe (Recipe): Рецепт (связь с моделью Recipe).
    - ingredient (Ingredient): Ингредиент (связь с моделью Ingredient).
    - amount (int): Количество ингредиента.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                constants.MIN_TIME,
                message=f'Количество не меньше {constants.MIN_AMOUNT}',
            ),
            MaxValueValidator(
                constants.MAX_TIME,
                message=f'Количество не больше {constants.MAX_AMOUNT}'
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ['id']

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount}"


class FavoriteShoppingBasemodel(models.Model):
    """
    Модель для хранения информации о списках покупок.
    Поля:
    - user (User): Пользователь (связь с моделью User).
    - recipe (Recipe): Рецепт (связь с моделью Recipe).
    """
    from recipes.models import Recipe

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class Favorite(FavoriteShoppingBasemodel):

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        default_related_name = 'favorites'

    def __str__(self):
        return 'Избранное'


class ShoppingCart(FavoriteShoppingBasemodel):

    class Meta:
        verbose_name = 'ShoppingCart'
        verbose_name_plural = 'ShoppingCart'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return 'Список покупок'


class Link(models.Model):
    original_link = models.URLField(blank=True)
    short_code = models.SlugField(max_length=5, unique=True, blank=True)
    EMAIL_RANGDOM_CHARS = ascii_lowercase + ascii_uppercase + digits
    __host = None

    class Meta:
        verbose_name = 'Link'
        verbose_name_plural = 'Links'

    def __str__(self):
        return self.short_link

    @classmethod
    def create_short_code(cls):
        length = len(cls.EMAIL_RANGDOM_CHARS) - 1
        short_code = ''.join(
            cls.EMAIL_RANGDOM_CHARS[randint(0, length)] for _ in range(4)
        )
        return short_code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.create_short_code()
        super().save(*args, **kwargs)

    @property
    def short_link(self):
        from foodgram_backend import settings

        if not self.__host:
            self.__host = 'localhost'
        port = getattr(settings, 'PORT', None)
        if port:
            return f'http://{self.__host}:{port}/s/{self.short_code}'
        else:
            return f'http://{self.__host}/s/{self.short_code}'

    @short_link.setter
    def short_link(self, host):
        self.__host = str(host)
