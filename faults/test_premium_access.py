from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Company, DefinedDevice, User
from .models import Brand, Category, FaultCodes, FavoriteFaultCode, Model


class PremiumContentTests(TestCase):
    endpoints = (
        'fault-codes-list', 'parameter-list', 'boiler-card-repair',
        'boiler-parts-list', 'video-list', 'room-thermostat',
        'search-fault-codes', 'favorite-brand', 'favorite-model', 'favorite-fault-code',
    )

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='content-user', email='content@example.com')
        cls.token = Token.objects.create(user=cls.user)
        cls.category = Category.objects.create(name='Test', type='Arıza Kodu')
        cls.brand = Brand.objects.create(name='Test', category=cls.category)
        cls.model = Model.objects.create(name='Test', category=cls.category, brand=cls.brand)
        cls.fault = FaultCodes.objects.create(
            category=cls.category, brand=cls.brand, model=cls.model,
            code='F01', fault_description='PREMIUM_SECRET',
        )
        FavoriteFaultCode.objects.create(user=cls.user, fault=cls.fault)

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def assert_endpoints(self, expected):
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f'/api/faults/{endpoint}/', {
                    'model_id': self.model.pk, 'search': 'F01', 'lang': 'tr',
                })
                self.assertEqual(response.status_code, expected)
                if expected != 200:
                    self.assertNotIn('PREMIUM_SECRET', str(response.data))
                if expected == 403:
                    self.assertEqual(response.data['code'], 'premium_required')

    def test_anonymous_denied(self):
        self.client.credentials()
        self.assert_endpoints(401)

    def test_unused_free_account_denied_without_starting_trial(self):
        self.assert_endpoints(403)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.trial_started_at)

    def test_active_trial_allowed(self):
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True, trial_started_at=timezone.now())
        self.assert_endpoints(200)
        response = self.client.get('/api/faults/search-fault-codes/', {'search': 'F01', 'lang': 'tr'})
        self.assertIn('PREMIUM_SECRET', str(response.data))

    def test_expired_trial_denied(self):
        User.objects.filter(pk=self.user.pk).update(
            has_used_trial=True, trial_started_at=timezone.now() - timedelta(days=4),
        )
        self.assert_endpoints(403)

    def test_exact_trial_end_denied(self):
        now = timezone.now()
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True, trial_started_at=now - timedelta(days=3))
        with patch('accounts.permissions.timezone.now', return_value=now):
            self.assert_endpoints(403)

    def test_same_session_loses_access_when_trial_ends(self):
        start = timezone.now()
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True, trial_started_at=start)
        self.assert_endpoints(200)
        with patch('accounts.permissions.timezone.now', return_value=start + timedelta(days=3)):
            self.assert_endpoints(403)

    def test_future_start_denied(self):
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True, trial_started_at=timezone.now() + timedelta(days=1))
        self.assert_endpoints(403)

    def test_active_premium_allowed(self):
        User.objects.filter(pk=self.user.pk).update(
            membership_status='PREMIUM', membership_expires_at=timezone.now() + timedelta(days=1),
        )
        self.assert_endpoints(200)

    def test_expired_premium_cannot_fall_back_to_trial(self):
        User.objects.filter(pk=self.user.pk).update(
            membership_status='PREMIUM', membership_expires_at=timezone.now() - timedelta(days=1),
            has_used_trial=True, trial_started_at=timezone.now(),
        )
        self.assert_endpoints(403)

    def test_missing_premium_expiration_denied(self):
        User.objects.filter(pk=self.user.pk).update(membership_status='PREMIUM')
        self.assert_endpoints(403)

    def test_team_uses_company_expiry(self):
        owner = User.objects.create_user(username='company-owner', email='owner@example.com')
        company = Company.objects.create(user=owner, service_name='Test', membership_expires_at=timezone.now() + timedelta(days=1))
        DefinedDevice.objects.create(user=self.user, company=company, device_id='test-device')
        User.objects.filter(pk=self.user.pk).update(membership_status='PREMIUM', membership_type='TEAM')
        self.assert_endpoints(200)
        Company.objects.filter(pk=company.pk).update(membership_expires_at=timezone.now() - timedelta(days=1))
        self.assert_endpoints(403)

    def test_staff_can_manage_content_without_subscription(self):
        User.objects.filter(pk=self.user.pk).update(is_staff=True)
        self.assert_endpoints(200)

    def test_free_information_still_public(self):
        self.client.credentials()
        for endpoint in ('category-list', 'spare-parts-definitions', 'boiler-working-principle', 'instrument-usage', 'boiler-repair-guide'):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(f'/api/faults/{endpoint}/', {'lang': 'tr'}).status_code, 200)
