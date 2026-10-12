from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import User
from .trial_access import ensure_trial


class TrialAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='trial-test', email='trial@example.com', password='test-password')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_unused_free_account_starts_once(self):
        response = self.client.get('/api/accounts/check-auth/?lang=tr')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        start = self.user.trial_started_at
        self.assertTrue(self.user.has_used_trial)
        self.assertIsNotNone(start)
        self.assertEqual(response.data['trial_ends_at'], start + timedelta(days=3))
        ensure_trial(self.user)
        self.assertEqual(self.user.trial_started_at, start)

    def test_used_trial_without_date_is_not_restarted(self):
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True)
        ensure_trial(self.user)
        self.assertIsNone(self.user.trial_started_at)

    def test_premium_marks_trial_used_even_with_update_fields(self):
        self.user.membership_status = 'PREMIUM'
        self.user.save(update_fields=['membership_status'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_used_trial)
        self.user.membership_status = 'FREE'
        self.user.save(update_fields=['membership_status'])
        ensure_trial(self.user)
        self.assertIsNone(self.user.trial_started_at)

    def test_expired_trial_cannot_be_extended_by_client(self):
        start = timezone.now() - timedelta(days=4)
        User.objects.filter(pk=self.user.pk).update(has_used_trial=True, trial_started_at=start)
        response = self.client.post('/api/accounts/trial-usage-track/', {
            'trial_started_at_ms': int(timezone.now().timestamp() * 1000),
            'trial_days': 365,
        }, format='json')
        self.assertIn(response.status_code, (200, 201))
        self.user.refresh_from_db()
        self.assertEqual(self.user.trial_started_at, start)

    def test_previous_premium_account_is_not_eligible(self):
        User.objects.filter(pk=self.user.pk).update(first_membership_date=timezone.now())
        ensure_trial(self.user)
        self.assertTrue(self.user.has_used_trial)
        self.assertIsNone(self.user.trial_started_at)
