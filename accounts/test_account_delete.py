from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


class AccountDeleteTests(TestCase):
    def setUp(self):
        self.users = get_user_model().objects
        self.user = self.users.create_user("delete-test", "delete@example.test", "test-password")
        self.url = reverse("account-delete")
        self.client = APIClient()

    def test_delete_requires_authentication(self):
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertTrue(self.users.filter(pk=self.user.pk).exists())

    def test_delete_targets_authenticated_user_and_removes_token(self):
        other = self.users.create_user("other", "other@example.test")
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.delete(self.url, {"email": other.email}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.users.filter(pk=self.user.pk).exists())
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
        self.assertTrue(self.users.filter(pk=other.pk).exists())

    def test_legacy_post_requires_a_valid_password(self):
        for payload in ({"email": self.user.email}, {"email": self.user.email, "password": "wrong"}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(self.url, payload).status_code, 400)
                self.assertTrue(self.users.filter(pk=self.user.pk).exists())

        response = self.client.post(self.url, {"email": self.user.email, "password": "test-password"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.users.filter(pk=self.user.pk).exists())
