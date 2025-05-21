from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import OuterRef, Exists
from ..models import Contact, EmailString

class OrphanedContactsListView(LoginRequiredMixin, ListView):
    template_name = 'core/orphaned_contacts_list.html'
    context_object_name = 'contacts'
    
    def get_queryset(self):
        # Find contacts not associated with any email string
        # Using a subquery to check if there are no email strings referencing this contact
        return Contact.objects.annotate(
            has_email_string=Exists(
                EmailString.objects.filter(contact=OuterRef('pk'))
            )
        ).filter(has_email_string=False).order_by('name')

def delete_contact(request, contact_id):
    """Delete a contact that is not associated with any email string"""
    if request.method == 'POST':
        try:
            # Get the contact
            contact = Contact.objects.get(id=contact_id)
            
            # Check if it's really orphaned (not associated with any email string)
            if not EmailString.objects.filter(contact=contact).exists():
                # Delete the contact
                contact.delete()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Contact is associated with email strings and cannot be deleted'
                })
        except Contact.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Contact not found'
            }, status=404)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

def delete_all_orphaned_contacts(request):
    """Delete all contacts that are not associated with any email string"""
    if request.method == 'POST':
        # Find all orphaned contacts
        orphaned_contacts = Contact.objects.annotate(
            has_email_string=Exists(
                EmailString.objects.filter(contact=OuterRef('pk'))
            )
        ).filter(has_email_string=False)
        
        # Get the count for the response
        count = orphaned_contacts.count()
        
        # Delete them all
        orphaned_contacts.delete()
        
        return JsonResponse({
            'status': 'success', 
            'count': count,
            'message': f'{count} orphaned contacts deleted'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400) 