from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import Throttled
from rest_framework.test import APIClient

from .models import AuditLog


class LoginAuditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login") + "?lang=en"
        self.user = get_user_model().objects.create_user(
            "login-audit-user", "audit@example.test", "test-password", device_id="registered-device"
        )
        self.credentials = {
            "username_or_email": self.user.email,
            "password": "test-password",
            "device_id": "registered-device",
        }

    def assert_failed_login(self, response, status_code, reason, user=None):
        self.assertEqual(response.status_code, status_code)
        log = AuditLog.objects.get(action=AuditLog.ActionChoices.FAILED_LOGIN)
        self.assertEqual(log.user, user)
        self.assertEqual(log.details, {
            "source": "mobile_login", "http_status": status_code, "reason": reason,
        })

    def test_wrong_password_is_linked_to_known_account(self):
        response = self.client.post(self.url, {**self.credentials, "password": "wrong"})
        self.assert_failed_login(response, 400, "invalid_credentials", self.user)

    def test_unknown_account_has_no_user_or_submitted_identifier(self):
        response = self.client.post(self.url, {**self.credentials, "username_or_email": "unknown@example.test"})
        self.assert_failed_login(response, 400, "invalid_credentials")

    def test_invalid_request_is_logged(self):
        response = self.client.post(self.url, {"username_or_email": self.user.email})
        self.assert_failed_login(response, 400, "invalid_request")

    def test_wrong_device_is_linked_to_known_account(self):
        response = self.client.post(self.url, {**self.credentials, "device_id": "other-device"})
        self.assert_failed_login(response, 400, "unregistered_device", self.user)

    def test_rate_limit_is_logged(self):
        with patch("accounts.views.LoginView.check_throttles", side_effect=Throttled(wait=1)):
            response = self.client.post(self.url, self.credentials)
        self.assert_failed_login(response, 429, "rate_limited")

    def test_server_error_is_logged_without_changing_the_response(self):
        self.client.raise_request_exception = False
        with patch("accounts.views.update_last_login", side_effect=RuntimeError("test error")):
            response = self.client.post(self.url, self.credentials)
        self.assert_failed_login(response, 500, "server_error", self.user)

    def test_success_does_not_create_failed_login_log(self):
        response = self.client.post(self.url, self.credentials)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuditLog.objects.filter(action=AuditLog.ActionChoices.FAILED_LOGIN).exists())
