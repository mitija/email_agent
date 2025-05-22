from django.shortcuts import render
from django.http import JsonResponse
from core.models import Thread, ThreadSummary, Label
from core.llm.helper import build_graph
from django.core.paginator import Paginator

def get_labels(request):
    query = request.GET.get('query', '').lower()
    labels = Label.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse({'labels': list(labels)})

def thread_list(request):
    threads = Thread.objects.all().order_by('-created_at')
    page_number = request.GET.get('page', 1)
    paginator = Paginator(threads, 10)  # Show 10 threads per page
    page_obj = paginator.get_page(page_number)
    
    thread_data = []
    
    for thread in page_obj:
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
    
    return render(request, 'core/thread_list.html', {
        'threads': thread_data,
        'page_obj': page_obj,
        'paginator': paginator
    })

def summarize_thread(request, thread_id):
    thread = Thread.objects.get(id=thread_id)
    
    # Get the compiled graph
    graph = build_graph()
    
    # Run the graph with initial state
    result = graph.invoke({
        "thread": thread,
        "conversation": "",
        "message_headers": "",
        "knowledge": "",
        "participant_set": None
    })
    
    # The summary data is nested under thread_summary
    summary_data = result['thread_summary']
    
    return JsonResponse({
        'success': True,
        'summary': summary_data['summary'],
        'action': summary_data['action'],
        'rationale': summary_data['rationale']
    }) 