from django.contrib import admin
from .models import Contact, Email, Label, Thread, ThreadSummary, SystemParameter, EmailAddress, EmailString
from core.llm import get_langgraph_helper
from django import forms
from django.utils.html import format_html
import json

@admin.register(EmailAddress)
class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_generic', 'is_active')
    search_fields = ('email',)
    list_filter = ('is_generic', 'is_active')

#Admin for EmailString
@admin.register(EmailString)
class EmailStringAdmin(admin.ModelAdmin):
    list_display = ('original_string', 'name', 'email', 'contact')
    search_fields = ('original_string', 'name', 'email__email')
    autocomplete_fields = ('contact',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_email')
    search_fields = ('name', 'emails__email')
    filter_horizontal = ('emails',)
    autocomplete_fields = ('emails',)

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('date', 'sender_str', 'subject')
    search_fields = ('subject', 'sender_str', 'sender__name')
    autocomplete_fields = ('sender_str', 'to_str', 'cc_str', 'labels')
    list_filter = ('date',)

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.action(description="Create Thread Summary")
def create_thread_summary(modeladmin, request, queryset):
    # Get the langgraph helper on demand
    langgraph_helper = get_langgraph_helper()
    
    for thread in queryset:
        # We log the names of the thread included on print
        print(f"Thread ID: {thread.id} - Subject: {thread.subject} - Date: {thread.date}")
        summary_data = langgraph_helper.invoke({"thread":thread})
        # We create a ThreadSummary object for each thread
        thread_summary = ThreadSummary.objects.create(
            thread=thread,
            email=thread.email_set.last(),
            summary=summary_data["summary"],
            action=summary_data["action"],
            rationale=summary_data["rationale"],
            participants=summary_data["participants"]
        )
        # We log the summary created
        print(f"Thread Summary: {thread_summary.summary}")

        modeladmin.message_user(request, f"Thread summary created for {thread}")

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("date","subject", "number_of_emails")
    autocomplete_fields = ("labels",)
    readonly_fields = ("subject", "date")
    search_fields = ("subject", "date")

    change_form_template = "admin/thread_form.html"

    actions = [create_thread_summary]

class ThreadSummaryForm(forms.ModelForm):
    class Meta:
        model = ThreadSummary
        fields = '__all__'
        exclude = ['participants']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'thread' in self.data:
            try:
                thread_id = int(self.data.get('thread'))
                self.fields['email'].queryset = Email.objects.filter(thread_id=thread_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.thread:
            self.fields['email'].queryset = self.instance.thread.email_set.all()

@admin.register(ThreadSummary)
class ThreadSummaryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "thread")
    autocomplete_fields = ("thread", "email")
    form = ThreadSummaryForm
    readonly_fields = ("formatted_participants",)
    fieldsets = (
        (None, {
            'fields': ('thread', 'email', 'summary', 'action', 'rationale')
        }),
        ('Participants', {
            'fields': ('formatted_participants',),
            'classes': ('monospace',)
        }),
    )

    def formatted_participants(self, obj):
        if obj.participants:
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', 
                             json.dumps(obj.participants, indent=2))
        return ""
    formatted_participants.short_description = "Participants"

    class Media:
        css = {
            'all': ('admin/css/thread_summary.css',)
        }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "email":
            if request.resolver_match.kwargs.get('object_id'):
                # If editing an existing object
                thread_summary = self.get_object(request, request.resolver_match.kwargs['object_id'])
                if thread_summary:
                    kwargs["queryset"] = thread_summary.thread.email_set.all()
            else:
                # If creating a new object, we'll handle this in the form
                kwargs["queryset"] = Email.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
