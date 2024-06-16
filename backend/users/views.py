from api.pagination import LimitPagination
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription
from users.serializers import (AvatarSerializer, CustomUserProfileSerializer,
                               SubscribeGetSerializer, SubscribeSerializer)

User = get_user_model()


class UserViewSet(UserViewSet):
    """ViewSet для пользователей."""

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
        """Связь между пользователями"""
        follower = get_object_or_404(User, id=request.user.id)
        publisher = get_object_or_404(User, id=self.kwargs.get('id'))
        if follower == publisher:
            return Response(
                {"detail": "Нельзя подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {'follower': follower.id, 'publisher': publisher.id}
        serializer = SubscribeSerializer(
            data=data, context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Удаление связи между пользователями."""
        following = get_object_or_404(User, id=self.kwargs.get('id'))
        user = request.user.id
        deleted, _ = Subscription.objects.filter(
            follower=user, publisher=following
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            "Нет в подписках.",
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(follower=request.user)
        pages = self.paginate_queryset(subscriptions)
        serializer = SubscribeGetSerializer(
            [subscription.publisher for subscription in pages],
            many=True,
            context={'request': request}
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
