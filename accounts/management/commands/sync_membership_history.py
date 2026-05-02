from django.core.management.base import BaseCommand
from accounts.models import User, Company, MembershipHistory
from django.db import transaction

class Command(BaseCommand):
    help = 'Premium kullanıcılar ve şirketler için ilk üyelik tarihlerini ve MembershipHistory kayıtlarını eşitler/oluşturur.'

    def handle(self, *args, **options):
        with transaction.atomic():
            user_count = 0
            company_count = 0
            
            # Users update
            users = User.objects.filter(membership_status='PREMIUM', membership_created_at__isnull=False)
            for user in users:
                if not user.first_membership_date:
                    user.first_membership_date = user.membership_created_at
                    user.renewal_count = 1
                    user.save(update_fields=['first_membership_date', 'renewal_count'])
                
                # Sadece eğer geçmişi boşsa ilk kaydı ekle
                if not MembershipHistory.objects.filter(user=user).exists():
                    MembershipHistory.objects.create(
                        user=user,
                        start_date=user.membership_created_at,
                        end_date=user.membership_expires_at,
                        renewal_index=1
                    )
                    user_count += 1

            # Companies update
            companies = Company.objects.filter(membership_created_at__isnull=False)
            for company in companies:
                if not company.first_membership_date:
                    company.first_membership_date = company.membership_created_at
                    company.renewal_count = 1
                    company.save(update_fields=['first_membership_date', 'renewal_count'])

                # Sadece eğer geçmişi boşsa ilk kaydı ekle
                if not MembershipHistory.objects.filter(company=company).exists():
                    MembershipHistory.objects.create(
                        company=company,
                        start_date=company.membership_created_at,
                        end_date=company.membership_expires_at,
                        renewal_index=1
                    )
                    company_count += 1

            self.stdout.write(self.style.SUCCESS(f'İşlem başarıyla tamamlandı. {user_count} adet Bireysel Kullanıcı ve {company_count} adet Şirket için geçmiş oluşturuldu.'))
