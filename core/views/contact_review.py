from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.db.models.functions import Lower
from ..models import EmailString, Contact, SystemParameter

class ContactReviewListView(LoginRequiredMixin, ListView):
    template_name = 'core/contact_review_list.html'
    context_object_name = 'email_strings'
    
    def get_queryset(self):
        # Get the last review time from system parameters
        last_review_time = SystemParameter.objects.filter(key='last_contact_review').first()
        
        # Get unreviewed email strings
        if last_review_time:
            queryset = EmailString.objects.filter(
                reviewed=False,
                created_at__gt=last_review_time.value
            ).select_related('contact', 'email')
        else:
            queryset = EmailString.objects.filter(reviewed=False).select_related('contact', 'email')
        
        # Convert to list and sort by name
        email_strings = list(queryset)
        return sorted(email_strings, key=lambda x: x.name.lower())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_review = SystemParameter.objects.filter(key='last_contact_review').first()
        if last_review:
            context['last_review'] = timezone.datetime.fromisoformat(last_review.value)
        
        # Get all contacts and explicitly sort them by name (case-insensitive)
        all_contacts = list(Contact.objects.all())
        sorted_contacts = sorted(all_contacts, key=lambda x: x.name.lower())
        context['contacts'] = sorted_contacts
        
        return context

class ContactReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailString
    fields = ['contact']
    
    def post(self, request, *args, **kwargs):
        email_string = self.get_object()
        contact_id = request.POST.get('contact_id')
        
        if contact_id == 'new':
            # Create new contact
            name = request.POST.get('name')
            email = request.POST.get('email')
            contact = Contact.objects.create(name=name)
            contact.emails.add(email_string.email)
        else:
            contact = Contact.objects.get(id=contact_id)
        
        email_string.contact = contact
        email_string.reviewed = True
        email_string.reviewed_at = timezone.now()
        email_string.save()
        
        return JsonResponse({'status': 'success'})

def complete_review(request):
    """Mark the current review session as complete"""
    SystemParameter.objects.update_or_create(
        key='last_contact_review',
        defaults={'value': timezone.now().isoformat()}
    )
    return JsonResponse({'status': 'success'}) 