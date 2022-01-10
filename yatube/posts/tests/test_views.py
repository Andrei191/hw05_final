import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow   # isort:skip
from yatube.settings import PAGE_COUNT  # isort:skip
User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.first_user = User.objects.create_user(username='someone')
        cls.second_user = User.objects.create_user(username='sometwo')
        # неавторизованный пользователь
        cls.guest_user = User.objects.create(username='nobody')
        # первый авторизованный пользователь
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.first_user)
        # второй авторизованный пользователь
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.second_user)
        # создаем первую тестовую группу
        cls.first_group = Group.objects.create(
            title='Первая Тестовая группа',
            slug='test-slug_1',
            description='Тестовое описание_группы_1',
        )
        # создаем вторую тестовую группу
        cls.second_group = Group.objects.create(
            title='Вторая Тестовая группа',
            slug='test-slug_2',
            description='Тестовое описание_группы_2',
        )
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        # 5 постов первой группы первого автора
        posts = [
            Post(
                text=f'post_num {post_num}',
                author=cls.first_user,
                group=cls.first_group,
                image=cls.uploaded
            ) for post_num in range(1, 6)
        ]
        Post.objects.bulk_create(posts)
        # 5 постов второй группы второго автора
        posts = [
            Post(
                text=f'post_num {post_num} second',
                author=cls.second_user,
                group=cls.second_group,
                image=cls.uploaded
            ) for post_num in range(1, 6)
        ]
        Post.objects.bulk_create(posts)
        # пост с группой
        cls.post_with_group = Post.objects.create(
            text='какой-то текст, есть группа',
            author=cls.first_user,
            group=cls.first_group)
        # пост без группы
        cls.post_without_group = Post.objects.create(
            text='какой-то текст, нет группы',
            author=cls.second_user,
            image=cls.uploaded)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        name = PostPagesTests.post_with_group.author.username
        post_id = PostPagesTests.post_with_group.id
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.first_group.slug}'}):
                    'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    args=[post_id]): 'posts/create_post.html',
            reverse('posts:post_detail',
                    args=[post_id]): 'posts/post_detail.html',
            reverse('posts:profile', args=[name]): 'posts/profile.html',
        }
        # Проверяем, что при обращении к name вызывается соотв HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем, что шаблон index сформирован с праильным контекстом
    def test_index_context(self):
        response = self.authorized_client_1.get(reverse('posts:index'))
        # Проверка, что в контекст передан список постов
        self.assertIsInstance(response.context, list)
        # Проверка, что каждый пост - объект модели Post
        # проверяем, что изображение передано в контекст
        page_obj = response.context.get('page_obj')
        for post in page_obj:
            with self.subTest(post=post):
                self.assertIsInstance(post, Post)
                self.assertIsNotNone(post.image)

    # Проверяем, что шаблон gtoup_list сформирован с праильным контекстом
    def test_group_list_context(self):
        response = self.authorized_client_1.get(reverse(
            'posts:group_list',
            args=(PostPagesTests.first_group.slug, )))
        # Проверка, что в контекст передан список постов
        self.assertIsInstance(response.context, list)
        # Проверка, что посты относятся к одной группе
        # проверяем, что изображение передано в контекст
        page_obj = response.context.get('page_obj')
        for post in page_obj:
            with self.subTest(post=post):
                self.assertEqual(post.group, PostPagesTests.first_group)
                self.assertIsNotNone(post.image)
        # проверка првильности переданного контекста
        test_obj = response.context.get('page_obj')[0]
        self.assertEqual(test_obj.group, PostPagesTests.first_group)

    # Проверяем, что шаблон profile сформирован с праильным контекстом
    def test_profile_context(self):
        response = self.authorized_client_2.get(
            reverse('posts:profile',
                    args=(PostPagesTests.second_user.username, )))
        # Проверка, что в контекст передан список постов
        self.assertIsInstance(response.context, list)
        # Проверка, что посты написаны одним автором
        # проверяем, что изображение передано в контекст
        page_obj = response.context.get('page_obj')
        for post in page_obj:
            with self.subTest(post=post):
                self.assertEqual(post.author, PostPagesTests.second_user)
                self.assertIsNotNone(post.image)
        # проверка првильности переданного контекста
        test_obj = response.context.get('page_obj')[0]
        self.assertEqual(test_obj.author, PostPagesTests.second_user)

    # Проверяем, что шаблон post_detail сформирован с праильным контекстом
    def test_post_detail_context(self):
        response = self.authorized_client_2.get(
            reverse('posts:post_detail',
                    args=(PostPagesTests.post_without_group.id, )))
        # Проверка контекста
        post = response.context.get('post')
        count = response.context.get('count')
        author = response.context.get('author')
        self.assertEqual(post, PostPagesTests.post_without_group)
        self.assertEqual(count, PostPagesTests.first_user.posts.count())
        self.assertEqual(author, PostPagesTests.second_user)
        # проверяем, что изображение передано в контекст
        self.assertIsNotNone(post.image)

    # Проверяем, что post_edit сформирован с правильным контекстом
    def test_post_edit_context(self):
        response = self.authorized_client_2.get(
            reverse('posts:post_edit',
                    args=(PostPagesTests.post_without_group.id, )))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        # Проверяем, что типы полей формы в словаре context соотв ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    # Проверяем, что post_create сформирован с правильным контекстом
    def test_post_create_context(self):
        response = self.authorized_client_2.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        # Проверяем, что типы полей формы в словаре context соотв ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_new_post_create_with_group(self):
        self.new_post_with_group = Post.objects.create(
            text='текст, есть группа',
            author=PostPagesTests.first_user,
            group=PostPagesTests.first_group)
        # проверка, что новый пост есть на главной странице
        response = self.authorized_client_1.get(reverse('posts:index'))
        self.assertEqual(
            response.context['page_obj'][0], self.new_post_with_group)
        # проверка, что новый пост есть на странице группы
        response = self.authorized_client_1.get(
            reverse('posts:group_list',
                    args=(PostPagesTests.first_group.slug, )))
        self.assertEqual(
            response.context['page_obj'][0], self.new_post_with_group)
        # проверка, что новый пост есть на странице пользователя
        response = self.authorized_client_2.get(
            reverse('posts:profile',
                    args=(PostPagesTests.first_user.username, )))
        self.assertEqual(response.context['page_obj'][0],
                         self.new_post_with_group)
        # проверка, что новый пост отсутствует в другой группе
        response = self.authorized_client_1.get(
            reverse('posts:group_list',
                    args=(PostPagesTests.second_group.slug, )))
        self.assertNotIn(self.new_post_with_group,
                         response.context['page_obj'])

    def test_authorized_client_can_subscribe(self):
        # проверка, что авторизованный пользователь может подписаться
        count_before_follow = Follow.objects.filter(
            author=PostPagesTests.second_user.id).count()
        self.authorized_client_1.get(
            reverse('posts:profile_follow',
                    args=(PostPagesTests.second_user.username, )))
        follow = Follow.objects.get(author=PostPagesTests.second_user.id)
        self.assertEqual(follow.user, PostPagesTests.first_user)
        count_after_follow = Follow.objects.filter(
            author=PostPagesTests.second_user.id).count()
        self.assertEqual(count_after_follow, count_before_follow + 1)

    def test_authorized_client_see_authors_posts(self):
        """ проверка, что у пользователя отоброжаются
        посты автора, на которого он подписан """
        # создание подписки
        Follow.objects.create(
            user=PostPagesTests.first_user,
            author=PostPagesTests.second_user
        )
        # создаем пост
        post = Post.objects.create(
            text='tututu',
            author=PostPagesTests.second_user
        )
        # проверяем, что пост отображается в подписках
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        authors = [post.author for post in response.context['page_obj']]
        self.assertIn(PostPagesTests.second_user, authors)
        # проверяем, что пост не отображается у неподписчика
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])

    def test_authorized_client_can_unsubscribe(self):
        """ проверка, что авторизованный пользователь может отписаться """
        Follow.objects.create(
            user=PostPagesTests.first_user,
            author=PostPagesTests.second_user
        )
        # создаем пост
        post = Post.objects.create(
            text='tututu',
            author=PostPagesTests.second_user
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        # отписка от автора
        self.authorized_client_1.get(
            reverse('posts:profile_unfollow',
                    args=(PostPagesTests.second_user.username, )))
        # проверка, что поста нет в подписках
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])


# Класс для тестирования паджинатора страниц со спиcками постов
class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user = User.objects.create_user(username='someone')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        number_of_posts = 56
        posts = [
            Post(
                text=f'post_num {post_num}',
                author=cls.user,
                group=cls.group
            ) for post_num in range(number_of_posts)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = PaginatorTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def number_of_page(self, count):
        return count // PAGE_COUNT

    def count_posts_on_last_page(self, count):
        return count % PAGE_COUNT

    # Проверяем паджинатор страницы Index
    def test_index_paginator(self):
        response = self.client.get(reverse('posts:index'))
        # количество страниц
        count_of_posts = response.context.get('page_obj').paginator.count
        # количество страниц с 10 постами
        count_of_pages = self.number_of_page(count_of_posts)
        # количество постов на последней странице
        posts_on_last_page = self.count_posts_on_last_page(count_of_posts)
        # Проверка: количество постов на страницах, кроме последней, равно 10
        for num_of_page in range(count_of_pages):
            with self.subTest(num_of_page=num_of_page):
                response = self.client.get(
                    reverse('posts:index') + f'?page={num_of_page + 1}')
                self.assertEqual(
                    len(response.context.get('page_obj')), PAGE_COUNT)
        # Проверка: кол-во постов на последней странице совпадает с ожидаемым.
        response = self.client.get(
            reverse('posts:index') + f'?page={count_of_pages + 1}')
        self.assertEqual(len(response.context.get('page_obj')),
                         posts_on_last_page)

    # Проверяем паджинатор страницы profile
    def test_profile_paginator(self):
        response = self.client.get(reverse('posts:profile',
                                   args=(PaginatorTests.user.username, )))
        # количество страниц
        count_of_posts = response.context.get('page_obj').paginator.count
        # количество страниц с 10 постами
        count_of_pages = self.number_of_page(count_of_posts)
        # количество постов на последней странице
        posts_on_last_page = self.count_posts_on_last_page(count_of_posts)
        # Проверка: количество постов на страницах, кроме последней, равно 10
        for num_of_page in range(count_of_pages):
            with self.subTest(num_of_page=num_of_page):
                response = self.client.get(
                    reverse('posts:index') + f'?page={num_of_page + 1}')
                self.assertEqual(
                    len(response.context.get('page_obj')), PAGE_COUNT)
        # Проверка: кол-во постов на последней странице совпадает с ожидаемым.
        response = self.client.get(reverse('posts:profile',
                                   args=(PaginatorTests.user.username, ))
                                   + f'?page={count_of_pages + 1}')
        self.assertEqual(len(response.context.get('page_obj')),
                         posts_on_last_page)

        # Проверяем паджинатор страницы gtoup_list
    def test_group_list_paginator(self):
        response = self.client.get(reverse('posts:group_list',
                                   args=(PaginatorTests.group.slug, )))
        # количество страниц
        count_of_posts = response.context.get('page_obj').paginator.count
        # количество страниц с 10 постами
        count_of_pages = self.number_of_page(count_of_posts)
        # количество постов на последней странице
        posts_on_last_page = self.count_posts_on_last_page(count_of_posts)
        # Проверка: количество постов на страницах, кроме последней, равно 10
        for num_of_page in range(count_of_pages):
            with self.subTest(num_of_page=num_of_page):
                response = self.client.get(reverse('posts:group_list',
                                           args=(PaginatorTests.group.slug, ))
                                           + f'?page={num_of_page + 1}')
                self.assertEqual(len(response.context.get('page_obj')),
                                 PAGE_COUNT)
        # Проверка: кол-во постов на последней странице совпадает с ожидаемым.
        response = self.client.get(reverse('posts:group_list',
                                   args=(PaginatorTests.group.slug, ))
                                   + f'?page={count_of_pages + 1}')
        self.assertEqual(len(response.context.get('page_obj')),
                         posts_on_last_page)
