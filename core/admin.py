from django.contrib import admin
from .models import Contact, Email, Tag, Thread, ThreadSummary, Action, SpecificInstruction, SystemParameter
from .gmail_fetch import fetch_emails_from_gmail

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "date")
    filter_horizontal = ("sender", "receiver")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id",)
    filter_horizontal = ("emails", "tags")

@admin.register(ThreadSummary)
class ThreadSummaryAdmin(admin.ModelAdmin):
    list_display = ("thread", "timestamp")

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("email", "action", "timestamp")

@admin.register(SpecificInstruction)
class SpecificInstructionAdmin(admin.ModelAdmin):
    list_display = ("contact", "tag", "instruction")

@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    actions = ["fetch_emails_from_gmail"]

def fetch_emails_from_gmail(self, request, queryset):
    if not queryset.filter(key="last_fetch_timestamp").exists():
        self.message_user(request, "No 'last_fetch_timestamp' found in SystemParameter.")
        return

    # Call the function to fetch emails from Gmail
    count = fetch_emails_from_gmail()
    self.message_user(request, f"Fetched {count} emails from Gmail.")

fetch_emails_from_gmail.short_description = "Fetch emails from Gmail since last sync"

