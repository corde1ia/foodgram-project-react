![foodgram-project-react Workflow Status](https://github.com/corde1ia/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg?branch=master&event=push)

# Продуктовый помощник Foodgram

## Описание проекта Foodgram
«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты, подписываться на публикации других авторов и добавлять рецепты в избранное. Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Проект доступен по адресу http:/158.160.8.223/recipes

## Запуск с использованием CI/CD

Установить docker, docker-compose на сервере ВМ Yandex.Cloud:
```bash
ssh username@ip
sudo apt update && sudo apt upgrade -y && sudo apt install curl -y
sudo curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo rm get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
Создать папку infra:
```bash
mkdir infra
```
- Перенести файлы docker-compose.yml и default.conf на сервер с помощью команд:

```bash
scp docker-compose.yml username@server_ip:/home/<username>/
scp default.conf <username>@<server_ip>:/home/<username>/
```
- Создать файл .env в дериктории infra:

```bash
touch .env
```
- Заполнить в настройках репозитория секреты .env

```python
DB_ENGINE='django.db.backends.postgresql'
DB_NAME=
POSTGRES_USER=
POSTGRES_PASSWORD=
DB_HOST=db
DB_PORT='5432'
SECRET_KEY=
ALLOWED_HOSTS=
```

## Запуск проекта через Docker
- В папке infra выполните команду, чтобы собрать контейнер:
```bash
sudo docker-compose up -d
```

Для доступа к контейнеру выполните следующие команды:

```bash
sudo docker-compose exec backend python manage.py makemigrations
sudo docker-compose exec backend python manage.py migrate --noinput 
sudo docker-compose exec backend python manage.py createsuperuser
sudo docker-compose exec backend python manage.py collectstatic --no-input
```

Наполните Базу данных ингредиентами и тэгами:

```bash
sudo docker-compose exec backend python manage.py load_tags
sudo docker-compose exec backend python manage.py load_ingrs
```

## Запуск проекта в dev-режиме

- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Выполните миграции:

```bash
python manage.py migrate
```

- В папке с файлом manage.py выполните команду:
```bash
python manage.py runserver
```