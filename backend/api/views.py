import io
from foodgram import settings as s

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly
from api.serializers import (
    IngredientSerializer, RecipeAddSerializer, RecipeReadSerializer,
    SubscribeRecipeSerializer, SubscribeSerializer, TagSerializer,
    TokenSerializer, UserCreateSerializer, UserListSerializer,
    UserPasswordSerializer)
from foodgram import settings as s

User = get_user_model()


class GetObjectMixin:
    """Миксин для удаления или добавления избранных рецептов или в корзину."""

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class PermissionAndPaginationMixin:
    """Миксин для списков ингридиентов и тэгов."""

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class AddAndDeleteSubscribe(
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Подписка/отписка пользователей."""

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True),)

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'Вы не можете подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': 'Вы уже подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.follower.filter(author=instance).delete()


class AddDeleteFavoriteRecipe(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта из избранных."""

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class AddDeleteShoppingCart(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта из корзины."""

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)


class AuthToken(ObtainAuthToken):
    """Авторизация для пользователей."""

    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)


class UsersViewSet(UserViewSet):

    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                self.request.user.follower.filter(
                    author=OuterRef('id'))
            )).prefetch_related(
                'follower', 'following'
        ) if self.request.user.is_authenticated else User.objects.annotate(
            is_subscribed=Value(False))

    def get_serializer_class(self):
        if self.request.method.lower() == 'post':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Получить список подписок."""

        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeAddSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        user=self.request.user, recipe=OuterRef('id'))),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef('id')))
                        ).select_related('author').prefetch_related(
                            'tags', 'ingredients', 'recipe',
                            'shopping_cart', 'favorite_recipe')
        else:
            return Recipe.objects.annotate(
                is_in_shopping_cart=Value(False),
                is_favorited=Value(False),
                    ).select_related('author').prefetch_related(
                    'tags', 'ingredients', 'recipe',
                    'shopping_cart', 'favorite_recipe')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачать рецепт."""

        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Courier', 'Courier.ttf'))
        x_position, y_position = 50, 800
        page.setFont('Courier', 14)
        shopping_cart = (
            request.user.shopping_cart.recipe.
            values(
                'ingredients__name',
                'ingredients__measurement_unit'
            ).annotate(amount=Sum('recipe__amount')))

        if not shopping_cart:
            page.setFont('Courier', 24)
            page.drawString(
                x_position,
                y_position,
                'Cписок покупок пуст!')
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename=s.FILENAME)
        indent = 20
        page.drawString(x_position, y_position, 'Cписок покупок:')
        for index, recipe in enumerate(shopping_cart, start=1):
            page.drawString(
                x_position, y_position - indent,
                f'{index}. {recipe["ingredients__name"]} - '
                f'{recipe["amount"]} '
                f'{recipe["ingredients__measurement_unit"]}.')
            y_position -= 15
            if y_position <= 50:
                page.showPage()
                y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename=s.FILENAME)


class TagsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


@api_view(['post'])
def set_password(request):
    """Изменить пароль."""

    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
            {'message': 'Ваш пароль успешно изменен'},
            status=status.HTTP_201_CREATED)
