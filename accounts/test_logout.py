from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import AuditLog, User


class LogoutTests(TestCase):
    def test_superuser_logout_preserves_token_used_by_another_device(self):
        user = User.objects.create_user(
            username="logout-admin",
            email="logout-admin@example.test",
            password="test-password",
            is_superuser=True,
            is_staff=True,
        )
        token = Token.objects.create(user=user)
        first_device = APIClient()
        first_device.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        other_device = APIClient()
        other_device.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.assertEqual(first_device.post(reverse("logout"), {"lang": "en"}).status_code, 200)
        self.assertEqual(other_device.get(reverse("check-auth"), {"lang": "en"}).status_code, 200)

        response = first_device.post(reverse("login") + "?lang=en", {
            "username_or_email": user.username, "password": "test-password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["token"], token.key)
        self.assertTrue(AuditLog.objects.filter(user=user, action=AuditLog.ActionChoices.LOGOUT).exists())

    def test_regular_user_logout_still_revokes_token(self):
        user = User.objects.create_user(username="logout-user", email="logout-user@example.test")
        token = Token.objects.create(user=user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.assertEqual(self.client.post(reverse("logout"), {"lang": "en"}).status_code, 200)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
        self.assertEqual(self.client.get(reverse("check-auth"), {"lang": "en"}).status_code, 401)
