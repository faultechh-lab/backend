from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .models import Company, DefinedDevice, MembershipChoices, PlanType
from .trial_access import TRIAL_DURATION


class HasPremiumContentAccess(BasePermission):
    """Authorize content on each request; never trust the mobile access flags."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_staff:
            return True
        now = timezone.now()
        if user.membership_status == MembershipChoices.PREMIUM:
            if user.membership_type == PlanType.TEAM:
                company = Company.objects.filter(user=user).first()
                if not company:
                    device = DefinedDevice.objects.filter(user=user).select_related('company').first()
                    company = device.company if device else None
                expires_at = company.membership_expires_at if company else None
            else:
                expires_at = user.membership_expires_at
            allowed = bool(expires_at and now < expires_at)
        else:
            start = user.trial_started_at
            allowed = bool(
                user.membership_status == MembershipChoices.FREE
                and user.has_used_trial and start and start <= now < start + TRIAL_DURATION
            )
        if not allowed:
            raise PermissionDenied({
                'detail': 'An active premium membership or trial is required.',
                'code': 'premium_required',
            })
        return True
