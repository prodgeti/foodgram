from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.serializers import CustomUserProfileSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientGetRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов в рецепте"""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientGetRecipeSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для коротного ингредиента для рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор страницы рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, intance):
        return RecipeSerializer(intance, context=self.context).data

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        if not tags:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тэг.'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        return data

    def validate_image(self, img_data):
        if not img_data:
            raise serializers.ValidationError(
                'Необходимо прикрепить изображение.'
            )
        return img_data

    def add_tags_ingredients(self, recipe, tags, ingredients):
        """Добавляет тэги или ингредиенты к рецепту."""

        recipe.tags.set(tags)

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self.add_tags_ingredients(recipe, tags_data, ingredients_data)
        return recipe

    def update(self, instance, validated):
        instance.name = validated.get('name', instance.name)
        if 'image' in validated:
            instance.image = validated.pop('image')
        instance.cooking_time = validated.get(
            'cooking_time', instance.cooking_time
        )
        instance.text = validated.get('text', instance.text)
        tags = validated.pop('tags')
        ingredients = validated.pop('ingredients')
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_tags_ingredients(instance, tags, ingredients)
        super().update(instance, validated)
        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов с укороченными данными."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранных и списка покупок."""

    related = None

    class Meta:
        model = None
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, attrib):
        recipe = attrib['recipe']
        user = self.context['request'].user
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {self.related}'
            )
        return attrib

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data


class FavoritesSerializer(RecipeBaseSerializer):
    """Сериализатор избранного."""

    related = 'избранное'

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(RecipeBaseSerializer):
    """Сериализатор списка покупок."""

    related = 'корзина'

    class Meta:
        model = ShoppingCart
        fields = '__all__'
