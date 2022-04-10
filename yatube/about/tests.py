from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response_av = self.guest_client.get('/about/author/')
        response_t = self.guest_client.get('/about/tech/')
        self.assertEqual(response_av.status_code, HTTPStatus.OK.value)
        self.assertEqual(response_t.status_code, HTTPStatus.OK.value)
