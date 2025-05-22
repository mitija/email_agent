from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import Thread, Contact, Email, ThreadSummary, EmailString
from django.db.models import Count, Q

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        context['total_threads'] = Thread.objects.count()
        context['total_contacts'] = Contact.objects.count()
        context['total_emails'] = Email.objects.count()
        context['summarized_threads'] = ThreadSummary.objects.values('thread').distinct().count()
        context['pending_summaries'] = context['total_threads'] - context['summarized_threads']
        
        # Get unreviewed email strings count
        context['unreviewed_email_strings'] = EmailString.objects.filter(reviewed=False).count()
        
        # Get orphaned contacts count
        context['orphaned_contacts'] = Contact.objects.annotate(
            has_email_string=Q(emails__emailstring__isnull=False)
        ).filter(has_email_string=False).count()
        
        return context 