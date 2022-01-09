from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post   # isort:skip

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='someone')
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.first_user)
        cls.post_without_group = Post.objects.create(
            text='какой-то текст, нет группы',
            author=cls.first_user
        )

    def test_cashe_index(self):
        text_post = CacheTests.post_without_group.text
        response = self.authorized_client_1.get(reverse('posts:index'))
        CacheTests.post_without_group.delete()
        self.assertIn(text_post, response.content.decode('utf-8'))
        page_obj = response.context.get('page_obj')
        key = make_template_fragment_key('index_page', [page_obj.number])
        cache.delete(key)
        response = self.authorized_client_1.get(reverse('posts:index'))
        self.assertNotIn(text_post, response.content.decode('utf-8'))
