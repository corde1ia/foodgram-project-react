from django.contrib import admin

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Subscribe, Tag)


class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_author', 'name', 'text',
        'cooking_time', 'get_tags', 'get_ingredients',
        'pub_date', 'get_favorite_count'
    )
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name')
    list_filter = ('pub_date', 'tags',)
    inlines = (RecipeIngredientAdmin,)

    @admin.display(
        description='Электронная почта')
    def get_author(self, obj):
        return obj.author.email

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        list_ = [_.name for _ in obj.tags.all()]
        return ', '.join(list_)

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return '\n '.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f' {item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')]
        )

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'color', 'slug',
    )
    search_fields = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit',)
    list_filter = ('measurement_unit',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'author', 'created',
    )
    search_fields = (
        'user__email', 'author__email', 'user__username', 'author__username'
    )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_recipe', 'get_count', 'get_tags')
    search_fields = (
        'recipe__name',
        'user__username',
        'user__email',
    )
    list_filter = ('recipe__tags',)

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        return [
            f'{item["tags__name"]} ' for item in obj.recipe.values('tags__name')[:10]
        ]


    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:10]
        ]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class SoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_recipe', 'get_count', 'get_tags')
    search_fields = (
        'recipe__name',
        'user__username',
        'user__email'
    )
    list_filter = ('recipe__tags',)

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:10]
        ]

    @admin.display(description='Рецепт в избранных')
    def get_count(self, obj):
        return obj.recipe.count()

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        return [
            f'{item["tags__name"]} ' for item in obj.recipe.values('tags__name')[:10]
        ]
