# Yatube
Yatube - социальная сеть блогеров, созданная в рамках учебного курса Яндекс.Практикум.

В Yatube можно создавать посты с фотографиями, комментировать записи и подписываться на других авторов.

Посты могут быть привязаны к тематической группе, на которую также можно подписаться.

## Стек технологий
---
 - проект написан на Python с использованием веб-фреймворка Django.
 - работа с изображениями - sorl-thumbnail, pillow
 - развернут на сервере Яндекс.Облако - nginx, ginicorn
 - система управления версиями - git
 - база данных - SQLite3
 ---
## Как запустить проект:
Клонируйте репозитроий с программой:
```
git clone https://github.com/leks20/yatube
```
В созданной директории установите виртуальное окружение, активируйте его и установите необходимые зависимости:
```
python3 -m venv venv
```
```
source venv/scripts/activate
```
```
pip install -r requirements.txt
```
Создайте в директории файл .env и поместите туда SECRET_KEY, необходимый для запуска проекта:

Выполните миграции:

```
python manage.py migrate
```
Создайте суперпользователя:
```
python manage.py createsuperuser
```
Запустите сервер:
```
python manage.py runserver
```
Ваш проект запустился на http://127.0.0.1:8000/

С помощью команды pytest вы можете запустить тесты и проверить работу модулей

Для подтверждения регистрации и сброса пароля используйте папку sent_emails
