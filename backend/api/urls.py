from django.urls import include, path
from rest_framework import routers

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)
from users.views import UserViewSet

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register(
    'ingredients', IngredientViewSet,
    basename='ingredients'
)
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path(
        'recipes/<int:id>/get-link/',
        RecipeViewSet.as_view({'get': 'get_link'}), name='recipe-get-link'
    ),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
