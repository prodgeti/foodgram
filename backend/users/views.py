from django.contrib.auth import get_user_model

from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from api.pagination import LimitPagination
from users.serializers import (
    CustomUserProfileSerializer,
    SubscribeSerializer,
    SubscribeGetSerializer,
    AvatarSerializer,
)
from users.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewset):
    """ViewSet для пользователей. Унаследован от Djoser.
    Регистрация, авторизация, подписки на других пользователей,
    список подписок, изменение аватара у пользователя.
    """

    queryset = User.objects.all()
    serializer_class = CustomUserProfileSerializer
    pagination_class = LimitPagination

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        """Создаёт связь между пользователями."""
        serializer = SubscribeSerializer(
            data={
                'user': get_object_or_404(User, id=request.user.id).id,
                'following': get_object_or_404(
                    User, id=self.kwargs.get('id')
                ).id,
            },
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Удалет связь между пользователями."""
        following = get_object_or_404(User, id=self.kwargs.get('id'))
        user = request.user.id
        deleted, _ = Subscription.objects.filter(
            following=following, user=user
        ).delete()
        return (
            Response(
                "Пользователь отсутствует в подписках.",
                status=status.HTTP_400_BAD_REQUEST
            )
            if not deleted
            else Response(status=status.HTTP_204_NO_CONTENT)
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Показывает всех юзеров на которых подписан текущий пользователь.
        Дополнительно показываются созданные рецепты.
        """
        subscriptions = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(subscriptions)
        serializer = SubscribeGetSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        """Переопределение методов для эндпоинта /me/."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        """Изменение аватара."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара."""
        request.user.avatar.delete(save=True)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
