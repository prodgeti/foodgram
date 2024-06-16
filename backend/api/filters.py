from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name='favorites__user', method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopping_cart__user', method='filter_is_in_shopping_cart'
    )

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        if value:
            user = getattr(self.request, 'user', None)
            if user and user.is_authenticated:
                return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            user = getattr(self.request, 'user', None)
            if user and user.is_authenticated:
                return queryset.filter(shopping_cart__user=user)
        return queryset
