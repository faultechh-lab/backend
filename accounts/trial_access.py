from datetime import timedelta

from django.utils import timezone

from .models import User, MembershipChoices


TRIAL_DURATION = timedelta(days=3)


def ensure_trial(user):
    """Start an unused free account's trial once, using the server clock."""
    user.refresh_from_db(fields=['membership_status', 'first_membership_date', 'renewal_count', 'has_used_trial', 'trial_started_at'])
    if user.membership_status == MembershipChoices.PREMIUM or user.first_membership_date or user.renewal_count:
        User.objects.filter(pk=user.pk, has_used_trial=False).update(has_used_trial=True)
    elif user.membership_status == MembershipChoices.FREE:
        User.objects.filter(pk=user.pk, has_used_trial=False, trial_started_at__isnull=True).update(
            has_used_trial=True, trial_started_at=timezone.now()
        )
    user.refresh_from_db(fields=['has_used_trial', 'trial_started_at'])
    return user
