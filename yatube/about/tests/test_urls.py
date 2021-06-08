from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/."""
        field_response_urls_code = {
            '/about/author/': 200,
            '/about/tech/': 200,
        }
        for url, response_code in field_response_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                adress_url = self.guest_client.get(adress)
                self.assertTemplateUsed(adress_url, template)
