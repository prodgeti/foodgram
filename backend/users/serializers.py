from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscription

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError('Аватар не добавлен.')
        return data


class CustomUserProfileSerializer(UserSerializer):
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

    def get_is_subscribed(self, obj):
        return self._check_subscription_status(
            self.context.get('request'), obj
        )

    def _check_subscription_status(self, request, obj):
        if not request or not request.user.is_authenticated:
            return False
        if obj == request.user:
            return False
        return Subscription.objects.filter(
            follower=request.user,
            publisher=obj
        ).exists()


class SubscribeSerializer(serializers.ModelSerializer):

    follower = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('follower', 'publisher')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['follower', 'publisher'],
            )
        ]

    def to_representation(self, instance):
        serializer = SubscribeGetSerializer(
            instance.publisher,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate(self, data):
        request = self.context.get('request')
        follower = request.user
        publisher = data['publisher']

        if follower == publisher:
            raise serializers.ValidationError('Нельзя подписаться на себя.')

        if Subscription.objects.filter(
            follower=follower, publisher=publisher
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return data


class SubscribeGetSerializer(CustomUserProfileSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserProfileSerializer.Meta):
        fields = CustomUserProfileSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        from api.serializers import RecipeShortSerializer
        recipes = self._get_limited_recipes(obj, self.context.get('request'))
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def _get_limited_recipes(self, obj, request):
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit > 0:
                    return recipes[:recipes_limit]
            except (TypeError, ValueError):
                pass
