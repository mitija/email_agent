from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from core.models import EmailString, Contact

@login_required
def email_string_list(request):
    email_strings = EmailString.objects.all().order_by('name')
    return render(request, 'core/email_string_list.html', {
        'email_strings': email_strings
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
        
        return JsonResponse({'success': True})
    except EmailString.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Email string not found'})
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contact not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}) 