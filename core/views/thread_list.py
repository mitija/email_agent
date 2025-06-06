from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import Thread, ThreadSummary, Label, Email
from core.llm.helper import build_graph
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import models
from core.utils import enhance_thread_data

@login_required
def get_labels(request):
    query = request.GET.get('query', '').lower()
    labels = Label.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse({'labels': list(labels)})

@login_required
def thread_list(request):
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get sort parameter with default to newest first
    sort_by = request.GET.get('sort', '-created_at')
    
    # Validate sort parameter to prevent SQL injection
    valid_sort_fields = ['created_at', '-created_at', 'subject', '-subject']
    if sort_by not in valid_sort_fields:
        sort_by = '-created_at'
    
    # Base queryset
    threads = Thread.objects.all()
    
    # Apply search filter if query exists
    if search_query:
        threads = threads.filter(
            Q(email__subject__icontains=search_query) |
            Q(email__body__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    if sort_by in ['subject', '-subject']:
        # For subject sorting, we need to join with the email table
        threads = threads.annotate(
            first_subject=models.Subquery(
                Email.objects.filter(
                    thread=models.OuterRef('pk')
                ).order_by('date').values('subject')[:1]
            )
        ).order_by(f"{'-' if sort_by.startswith('-') else ''}first_subject")
    else:
        threads = threads.order_by(sort_by)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(threads, 10)  # Show 10 threads per page
    page_obj = paginator.get_page(page_number)
    
    # Count all summarized threads, not just those on current page
    summarized_count = ThreadSummary.objects.values('thread').distinct().count()
    
    # Enhance thread data with additional information including summaries
    thread_data = [enhance_thread_data(thread, include_summary=True) for thread in page_obj]
    
    return render(request, 'core/thread_list.html', {
        'threads': thread_data,
        'page_obj': page_obj,
        'paginator': paginator,
        'current_sort': sort_by,
        'search_query': search_query,
        'total_threads': paginator.count,
        'summarized_count': summarized_count,
        'pending_count': paginator.count - summarized_count
    })

@login_required
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

@login_required
def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    emails = thread.email_set.all().order_by('date')
    latest_summary = ThreadSummary.objects.filter(thread=thread).order_by('-timestamp').first()
    
    context = {
        'thread': thread,
        'emails': emails,
        'summary': latest_summary.summary if latest_summary else None,
        'action': latest_summary.action if latest_summary else None,
        'rationale': latest_summary.rationale if latest_summary else None,
    }
    
    return render(request, 'core/thread_detail.html', context) 