from django.contrib import admin
from .models import Contact, Email, Label, Thread, ThreadSummary, Action, SpecificInstruction, SystemParameter
from .gmail_helper import gmail_helper
from datetime import datetime, timedelta

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("date", "sender", "subject")

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id",)
    filter_horizontal = ("emails", "labels")

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
