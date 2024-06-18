import base62
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import SAFE_METHODS, AllowAny
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (FavoritesSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeIngredient,
                             RecipeSerializer, ShoppingCartSerializer,
                             TagSerializer)
from recipes.models import Ingredient, Recipe, Tag

from .utils import create_shopping_list_pdf

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для получения ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для получения тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination
    permission_classes = (IsAuthorAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def add_recipe(self, request, pk, serializer_class):
        """Добавление рецепта в избранное или в корзину покупок."""
        recipe = get_object_or_404(self.queryset, pk=pk)
        serializer = serializer_class(
            data={'recipe': recipe.pk, 'user': request.user.pk},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_recipe(self, request, pk, related_name):
        """Удаление рецепта из избранного или из корзины покупок."""

        recipe = get_object_or_404(Recipe, id=pk)
        related_manager = getattr(request.user, related_name)
        deleted, _ = related_manager.filter(recipe=recipe).delete()
        if not deleted:
            return Response(
                'Рецепт отсутствует в списке.',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='favorite')
    def favorite(self, request, pk):
        """Добавление рецепта в избранное."""
        return self.add_recipe(request, pk, FavoritesSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаление рецепта из избранного."""
        return self.delete_recipe(request, pk, 'favorites')

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        """Добавление рецепта в корзину покупок."""
        return self.add_recipe(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):
        """Удаление рецепта из корзины покупок."""
        return self.delete_recipe(request, pk, 'shopping_cart')

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )

        response = create_shopping_list_pdf(user, ingredients)
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, id=None):
        """Создает короткую ссылку для рецепта на основе его ID."""
        if not id:
            return Response(
                'ID рецепта не указан.',
                status=status.HTTP_400_BAD_REQUEST
            )
        short_id = base62.encode(int(id))
        short_link = request.build_absolute_uri(f'/s/{short_id}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


@api_view(['GET'])
def redirect_short_link(request, short_id):
    """Перенаправляет короткую ссылку на страницу рецепта."""
    try:
        recipe_id = base62.decode(short_id)
        return redirect(f'/recipes/{recipe_id}/')
    except ValueError:
        return Response(
            "Некорректная короткая ссылка.",
            status=status.HTTP_400_BAD_REQUEST
        )
