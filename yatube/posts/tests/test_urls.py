# posts/tests/test_urls.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_common_urls_exists_at_desired_location(self):
        post_id = PostURLTests.post.id
        name = PostURLTests.post.author.username
        slug = PostURLTests.post.group.slug
        addresses = ['/', f'/group/{slug}/',
                     f'/posts/{post_id}/', f'/profile/{name}/']
        for address in addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_create_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_edit_url_exists_at_desired_location(self):
        post = PostURLTests.post
        response = self.authorized_client.get(f'/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_unexesting_page_does_not_exists(self):
        response = self.guest_client.get('/unexesting/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_urls_uses_correct_template(self):
        name = PostURLTests.post.author.username
        post_id = PostURLTests.post.id
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{name}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
