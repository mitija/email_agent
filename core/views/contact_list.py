from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from core.models.contact import Contact

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'core/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 20

    def get_queryset(self):
        queryset = Contact.objects.all()
        
        # Get search query
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(emails__email__icontains=search_query)
            ).distinct()
        
        # Get sort parameter with default to name
        sort_by = self.request.GET.get('sort', 'name')
        
        # Validate sort parameter to prevent SQL injection
        valid_sort_fields = ['name', '-name', 'created_at', '-created_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'name'
        
        return queryset.order_by(sort_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contacts'
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['search_query'] = self.request.GET.get('search', '')
        context['total_contacts'] = self.get_queryset().count()
        return context

class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'core/contact_detail.html'
    context_object_name = 'contact'
    pk_url_kwarg = 'contact_id'  # This matches the URL parameter name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Contact: {self.object.name}'
        return context

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            
            # If it's an API request (checking the URL pattern)
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'id': self.object.id,
                    'name': self.object.name,
                    'knowledge': self.object.knowledge,
                    'emails': [email.email for email in self.object.emails.all()]
                })
            
            # Otherwise, return the normal template response
            context = self.get_context_data()
            return self.render_to_response(context)
        except Contact.DoesNotExist:
            return JsonResponse({
                'error': 'Contact not found'
            }, status=404) 