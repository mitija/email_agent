from django.contrib import admin
from .models import Contact, Email, Label, Thread, ThreadSummary, Action, SpecificInstruction, SystemParameter
from .langgraph_helper import langgraph_helper

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    search_fields = ("name", "email")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("date", "sender", "subject")
    autocomplete_fields = ("sender", "to", "cc", "labels")

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.action(description="Create Thread Summary")
def create_thread_summary(modeladmin, request, queryset):
    for thread in queryset:
        # We log the names of the thread included on print
        print(f"Thread ID: {thread.id} - Subject: {thread.subject} - Date: {thread.date}")
        summary = langgraph_helper.create_thread_summary(thread)
        # We create a ThreadSummary object for each thread
        thread_summary = ThreadSummary.objects.create(
            thread=thread,
            email=thread.emails.last(),
            summary=summary
        )
        # We log the summary created
        print(f"Thread Summary: {thread_summary.summary}")

        modeladmin.message_user(request, f"Thread summary created for {thread}")

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("date","subject", "number_of_emails")
    autocomplete_fields = ("labels",)
    readonly_fields = ("subject", "date")

    change_form_template = "admin/thread_form.html"

    actions = [create_thread_summary]

@admin.register(ThreadSummary)
class ThreadSummaryAdmin(admin.ModelAdmin):
    list_display = ("thread", "timestamp")

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("email", "action", "timestamp")

@admin.register(SpecificInstruction)
class SpecificInstructionAdmin(admin.ModelAdmin):
    list_display = ("contact", "label", "instruction")

@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
