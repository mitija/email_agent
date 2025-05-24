from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
import json
from core.models import EmailString, Contact, Email

@login_required
def email_string_list(request):
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get sort parameter with default to name
    sort_by = request.GET.get('sort', 'name')
    
    # Validate sort parameter to prevent SQL injection
    valid_sort_fields = ['name', '-name', 'email', '-email', 'contact', '-contact', 'original_string', '-original_string']
    if sort_by not in valid_sort_fields:
        sort_by = 'name'
    
    # Base queryset
    email_strings = EmailString.objects.all().select_related('contact', 'email')
    
    # Apply search filter if query exists
    if search_query:
        email_strings = email_strings.filter(
            Q(name__icontains=search_query) |
            Q(email__email__icontains=search_query) |
            Q(original_string__icontains=search_query) |
            Q(contact__name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    email_strings = email_strings.order_by(sort_by)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(email_strings, 20)  # Show 20 items per page
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/email_string_list.html', {
        'email_strings': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'title': 'Email Strings',
        'current_sort': sort_by,
        'search_query': search_query,
        'total_email_strings': paginator.count
    })

@login_required
@csrf_exempt
@require_http_methods(['POST'])
def update_email_string_contact(request):
    try:
        data = json.loads(request.body)
        email_string_id = data.get('email_string_id')
        contact_id = data.get('contact_id')
        
        if not email_string_id or not contact_id:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        email_string = EmailString.objects.get(id=email_string_id)
        contact = Contact.objects.get(id=contact_id)
        
        email_string.contact = contact
        email_string.save()
        
        return JsonResponse({
            'success': True,
            'contact': {
                'id': contact.id,
                'name': contact.name
            }
        })
    except (EmailString.DoesNotExist, Contact.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def create_contact(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email_string_id = data.get('email_string_id')
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Name is required'
            }, status=400)
        
        # Create the new contact
        contact = Contact.objects.create(name=name)
        
        # If an email string ID is provided, associate the contact with that email string
        if email_string_id:
            try:
                email_string = EmailString.objects.get(id=email_string_id)
                email_string.contact = contact
                email_string.save()
            except EmailString.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'contact': {
                'id': contact.id,
                'name': contact.name
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400) 