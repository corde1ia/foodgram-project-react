# Generated by Django 3.2.13 on 2022-08-10 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0012_alter_favoriterecipe_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(null=True, upload_to='static/recipe/', verbose_name='Картинка'),
        ),
    ]
