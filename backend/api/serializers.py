from foodgram import settings as s
import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscribe, Tag

User = get_user_model()

ERR_EMAIL = 'Необходимо указать Вашу электронную почту.'
ERR_PASSWORD = 'Необходимо указать Ваш пароль.'
ERR_MSG = 'Невозможно войти в систему с введнными учетными данными.'


class TokenSerializer(serializers.Serializer):
    email = serializers.CharField(
        label='Электронная почта',
        write_only=True
    )
    password = serializers.CharField(
        label='Пароль',
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label='Токен',
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        if not email:
            raise serializers.ValidationError(
                ERR_EMAIL,
                code='authorization'
            )
        password = attrs.get('password')
        if not password:
            raise serializers.ValidationError(
                ERR_PASSWORD,
                code='authorization'
            )
        user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password)
        if not user:
            raise serializers.ValidationError(
                    ERR_MSG,
                    code='authorization'
            )
        attrs['user'] = user
        return attrs


class GetIsSubscribedMixin:

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()


class UserListSerializer(
        GetIsSubscribedMixin,
        serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',
        )

    def validate_password(self, password):
        validators.validate_password(password)
        return password


class UserPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        label='Введите новый пароль'
    )
    current_password = serializers.CharField(
        label='Введите текущий пароль'
    )

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        authorization = authenticate(
                username=user.email,
                password=current_password
        )
        if not authorization:
            raise serializers.ValidationError(
                ERR_MSG,
                code='authorization'
            )
        return current_password

    def validate_new_password(self, new_password):
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        user = self.context['request'].user
        password = make_password(
            validated_data.get('new_password')
        )
        user.password = password
        user.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeUserSerializer(
        GetIsSubscribedMixin,
        serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )


class IngredientsEditSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeAddSerializer(serializers.ModelSerializer):
    ingredients = IngredientsEditSerializer(many=True)
    image = Base64ImageField(
        max_length=None,
        use_url=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_list = []
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы 1 ингредиент в рецепт')
        for item in ingredients:
            name = item['name']
            if int(item.get('amount')) < s.MIN_INGREDIENT_AMOUNT:
                raise serializers.ValidationError(
                    f'Кол-во ингредиента - {name} - '
                    f'не может быть меньше единицы')
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    f'Ингредиент - {name} - уже добавлен в рецепт')
            ingredient_list.append(ingredient)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тэг')
        for tag_name in tags:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэга - {tag_name} - не существует')
        cooking_time = data['cooking_time']
        if int(cooking_time) < s.MIN_COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше минуты')
        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = RecipeUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='recipe'
    )
    is_favorited = serializers.BooleanField(
        read_only=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = '__all__'


class SubscribeRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='author.id'
    )
    email = serializers.EmailField(
        source='author.email')
    username = serializers.CharField(
        source='author.username'
    )
    first_name = serializers.CharField(
        source='author.first_name'
    )
    last_name = serializers.CharField(
        source='author.last_name'
    )
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(
        read_only=True
    )
    recipes_count = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author',)
            )
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[:int(limit)] if limit
            else obj.author.recipe.all())
        return SubscribeRecipeSerializer(
            recipes,
            many=True).data
