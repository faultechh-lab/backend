from django.core.management.base import BaseCommand

from accounts.models import AuditLog


class Command(BaseCommand):
    help = 'Delete all rows from the application audit log.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many audit log entries would be deleted.',
        )

    def handle(self, *args, **options):
        audit_logs = AuditLog.objects.all()

        if options['dry_run']:
            self.stdout.write(f'{audit_logs.count()} audit log entries would be deleted.')
            return

        _, deleted_by_model = audit_logs.delete()
        deleted_count = deleted_by_model.get(AuditLog._meta.label, 0)
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} audit log entries.'))
