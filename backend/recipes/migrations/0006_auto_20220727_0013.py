# Generated by Django 3.2.13 on 2022-07-26 21:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0005_auto_20220727_0009'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='favoriterecipe',
            name='recipe',
        ),
        migrations.AddField(
            model_name='favoriterecipe',
            name='recipe',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='favorite_recipe', to='recipes.recipe', verbose_name='Избранный рецепт'),
        ),
        migrations.AlterField(
            model_name='favoriterecipe',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='favorite_recipe', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.RemoveField(
            model_name='shoppingcart',
            name='recipe',
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='recipe',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='shopping_cart', to='recipes.recipe', verbose_name='Покупка'),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
