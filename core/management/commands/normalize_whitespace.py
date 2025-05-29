from django.core.management.base import BaseCommand
from core.models import Email
from core.utils import normalize_whitespace

class Command(BaseCommand):
    help = 'Normalize whitespace in all existing email bodies'

    def handle(self, *args, **options):
        emails = Email.objects.all()
        total_emails = emails.count()
        processed = 0
        updated = 0

        self.stdout.write(f"Processing {total_emails} emails...")

        for email in emails:
            processed += 1
            original_body = email.body
            normalized_body = normalize_whitespace(original_body)
            
            if original_body != normalized_body:
                email.body = normalized_body
                email.save()
                updated += 1
                self.stdout.write(f"Updated email {email.id} ({processed}/{total_emails})")
            else:
                self.stdout.write(f"No changes needed for email {email.id} ({processed}/{total_emails})")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {processed} emails. Updated {updated} emails."
        )) 