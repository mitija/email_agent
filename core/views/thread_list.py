from django.shortcuts import render
from django.http import JsonResponse
from core.models import Thread, ThreadSummary, Label
from core.llm.nodes import summarize_thread_node

def get_labels(request):
    query = request.GET.get('query', '').lower()
    labels = Label.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse({'labels': list(labels)})

def thread_list(request):
    threads = Thread.objects.all().order_by('-created_at')
    thread_data = []
    
    for thread in threads:
        first_email = thread.email_set.first()
        has_summary = ThreadSummary.objects.filter(thread=thread).exists()
        latest_summary = ThreadSummary.objects.filter(thread=thread).order_by('-timestamp').first()
        
        thread_data.append({
            'id': thread.id,
            'subject': thread.subject,
            'date': thread.created_at,
            'has_summary': has_summary,
            'summary': latest_summary.summary if latest_summary else None,
            'action': latest_summary.action if latest_summary else None,
            'rationale': latest_summary.rationale if latest_summary else None,
            'labels': [label.name for label in first_email.labels.all()] if first_email else [],
        })
    
    return render(request, 'core/thread_list.html', {'threads': thread_data})

def summarize_thread(request, thread_id):
    try:
        thread = Thread.objects.get(id=thread_id)
        state = {
            "thread": thread,
            "conversation": "",
            "message_headers": "",
            "knowledge": "",
            "participant_set": None
        }
        
        # Run the summary node
        result = summarize_thread_node(state)
        
        return JsonResponse({
            'success': True,
            'summary': result['summary'],
            'action': result['action'],
            'rationale': result['rationale']
        })
    except Thread.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Thread not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500) 