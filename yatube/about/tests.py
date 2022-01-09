from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_urls_exists_at_desired_location(self):
        adresses = ['/about/tech/', '/about/author/']
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }
        for template, adress in templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
