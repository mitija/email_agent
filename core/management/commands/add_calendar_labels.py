from django.core.management.base import BaseCommand
from core.models import Email, Label
from core.utils import is_calendar_invite

class Command(BaseCommand):
    help = "Process existing emails and add Calendar label where appropriate"

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of emails to process in each batch'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        
        # Get or create the Calendar label
        calendar_label, created = Label.objects.get_or_create(
            name="Calendar",
            defaults={
                "gmail_label_id": "CALENDAR",  # This is a custom label, not a Gmail system label
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Calendar label'))
        else:
            self.stdout.write(self.style.SUCCESS('Found existing Calendar label'))

        # Process emails in batches
        total_processed = 0
        total_updated = 0
        offset = 0
        
        while True:
            # Get a batch of emails that don't have the Calendar label
            emails = Email.objects.exclude(labels=calendar_label).order_by('id')[offset:offset + batch_size]
            if not emails:
                break

            self.stdout.write(f"Processing batch of {len(emails)} emails...")

            for email in emails:
                # Create headers list
                headers = [
                    {'name': 'From', 'value': email.sender_str.original_string},
                    {'name': 'Subject', 'value': email.subject},
                    {'name': 'To', 'value': ', '.join(to.original_string for to in email.to_str.all())},
                    {'name': 'Cc', 'value': ', '.join(cc.original_string for cc in email.cc_str.all())},
                ]

                # Debug logging
                self.stdout.write(f"\nChecking email:")
                self.stdout.write(f"ID: {email.gmail_message_id}")
                self.stdout.write(f"Subject: '{email.subject}'")
                self.stdout.write(f"From: {email.sender_str.original_string}")
                
                # Check if it's a calendar invite
                if is_calendar_invite(
                    subject=email.subject,
                    body=email.body,
                    headers=headers
                ):
                    email.labels.add(calendar_label)
                    total_updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Added Calendar label to email: {email.subject} (ID: {email.gmail_message_id})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Not a calendar invite: {email.subject} (ID: {email.gmail_message_id})'
                        )
                    )

            total_processed += len(emails)
            offset += batch_size
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {total_processed} emails, updated {total_updated} with Calendar label'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Finished processing {total_processed} emails. Added Calendar label to {total_updated} emails.'
            )
        ) 