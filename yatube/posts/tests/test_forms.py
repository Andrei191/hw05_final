import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment   # isort:skip

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user(username='someone')
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.first_user)
        self.guest_client = Client()
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            group=self.group,
            author=self.first_user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст для поста в креате пост',
            'group': self.group.id,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client_1.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # проверка статуса ответа
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertRedirects(response, reverse('posts:profile',
                             args=['someone', ]))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # сравнение полей нового поста с ожидаемыми значениями
        checked_post = Post.objects.all().first()
        self.assertEqual(checked_post.text, form_data['text'])
        self.assertEqual(checked_post.group, self.group)
        self.assertEqual(checked_post.author, self.first_user)
        self.assertEqual(checked_post.image.name,
                         f'posts/{form_data["image"].name}')

    def test_edit_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='smallest.gif',
            content=small_gif,
            content_type='image/gif',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый Тестовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        # Отправляем POST-запрос
        response = self.authorized_client_1.post(
            reverse('posts:post_edit', args=[self.post.id, ]),
            data=form_data,
            follow=True
        )
        # проверка статуса ответа
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[self.post.id, ]))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # сравнение полей отредактированного поста с ожидаемыми значениями
        checked_post = Post.objects.all().first()
        self.assertEqual(checked_post.text, form_data['text'])
        self.assertEqual(checked_post.group, self.group)
        self.assertEqual(checked_post.author, self.first_user)
        self.assertEqual(checked_post.image.name,
                         f'posts/{form_data["image"].name}')

    def test_redirects_not_auth_user(self):
        count = Post.objects.all().count()
        form_data = {
            'text': 'Новый Тестовый текст',
            'group': self.group.id
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # проверка, что пост не создался
        self.assertEqual(count, Post.objects.all().count())
        self.assertRedirects(response, (reverse('users:login')
                             + '?next=' + reverse('posts:post_create')))

    def test_comment_post_only_authorized_client(self):
        count = Comment.objects.all().count()
        form_data = {
            'text': 'Новый Тестовый текст'
        }
        checked_post = Post.objects.all().first()
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(checked_post.id,)),
            data=form_data,
            follow=True
        )
        # проверка, что коммент не создался
        self.assertEqual(count, Comment.objects.all().count())
        self.assertRedirects(response, (reverse('users:login')
                             + '?next='
                             + reverse('posts:add_comment',
                             args=(checked_post.id,))))

    def test_comment_add_succesfully(self):
        count = Comment.objects.all().count()
        form_data = {
            'text': 'Еще Новый Тестовый коммент'
        }
        checked_post = Post.objects.all().first()
        # Отправляем POST-запрос
        response = self.authorized_client_1.post(
            reverse('posts:add_comment', args=(checked_post.id,)),
            data=form_data,
            follow=True
        )
        # проверка статуса ответа
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        # проверка, что коммент создался
        self.assertEqual(count + 1, Comment.objects.all().count())
        self.assertEqual(
            checked_post.comments.all().first().text,
            form_data['text'])
