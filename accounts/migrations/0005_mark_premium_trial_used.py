from django.db import migrations
from django.db.models import Q


def mark_paid_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.using(schema_editor.connection.alias).filter(
        Q(membership_status='PREMIUM') | Q(first_membership_date__isnull=False) | Q(renewal_count__gt=0)
    ).update(has_used_trial=True)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_user_has_used_trial_user_trial_started_at')]
    operations = [migrations.RunPython(mark_paid_users, migrations.RunPython.noop)]
