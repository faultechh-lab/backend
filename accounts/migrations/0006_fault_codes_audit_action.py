from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0005_mark_premium_trial_used')]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(choices=[('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('REGISTER', 'Register'), ('PASSWORD_CHANGE', 'Password Change'), ('PASSWORD_RESET', 'Password Reset'), ('DEVICE_CHANGE', 'Device Change'), ('EMAIL_VERIFY', 'Email Verify'), ('PROFILE_UPDATE', 'Profile Update'), ('FAILED_LOGIN', 'Failed Login'), ('FAULT_CODES_ACCESS', 'Fault Codes Access')], max_length=50),
        ),
    ]
