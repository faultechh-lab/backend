from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User


class AdminLoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin-test",
            email="admin-test@example.com",
            password="correct-horse-battery-staple",
        )

    def test_admin_login_rejects_missing_or_invalid_password(self):
        for payload in (
            {"username": self.user.username},
            {"username": self.user.username, "password": "wrong-password"},
        ):
            response = self.client.post("/api/config/admin-login/", payload, format="json")
            self.assertIn(response.status_code, (400, 401))
            self.assertNotIn("token", response.data)

    def test_admin_login_returns_token_only_after_password_verification(self):
        response = self.client.post(
            "/api/config/admin-login/",
            {"username": self.user.username, "password": "correct-horse-battery-staple"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("token"))
