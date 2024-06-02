from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField

from djoser.serializers import UserSerializer as MeUS

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscription

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        avatar = data.get('avatar', None)
        if not avatar:
            raise serializers.ValidationError('Прекрепите аватар.')
        return data


class CustomUserProfileSerializer(MeUS):
    """Сериализатор для текущего пользователя. Унаследован от Djoser."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj: User):
        """Проверяет статус подписки.
        Args:
            obj (User): исходный пользователь.
        Returns:
            bool: true or false.
        """
        request = self.context.get('request')
        return (
            bool(request)
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                following=obj
            ).exists()
            and not obj == request.user
        )


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'following'],
            )
        ]

    def to_representation(self, instance):
        return SubscribeGetSerializer(
            instance.following, context={
                'request': self.context.get('request')
            }
        ).data

    def validate_following(self, val):
        if self.context['request'].user == val:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return val


class SubscribeGetSerializer(CustomUserProfileSerializer):
    """Сериализатор для отображения всех подписанных пользователей,
    их рецептов, количества рецептов."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserProfileSerializer.Meta):
        fields = CustomUserProfileSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj: User):
        """Подсчет количества рецептов."""
        return obj.recipes.count()

    def get_recipes(self, obj: User):
        """Получает список репептов пользователя.
        Args:
            recipe (User): исходный пользователь.

        Returns:
            QuerySet[dict]: Список рецептов пользователя.
        """
        from api.serializers import RecipeShortSerializer

        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit', 0)
        try:
            recipes = recipes[: int(recipes_limit)]
        except (TypeError, ValueError):
            pass
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data
