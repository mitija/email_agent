from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models.thread import Thread
from core.models.email import Email
from django.db.models import Min, Max
from django.utils import timezone
from core.utils.thread_utils import enhance_thread_data

@login_required
def timeframe_threads(request):
    # Get timeframe from query parameter, default to 24h
    timeframe = request.GET.get('timeframe', '24h')
    
    # Calculate the start time based on the timeframe
    now = timezone.now()
    if timeframe == '1h':
        start_time = now - timedelta(hours=1)
    elif timeframe == '8h':
        start_time = now - timedelta(hours=8)
    elif timeframe == '12h':
        start_time = now - timedelta(hours=12)
    else:  # 24h
        start_time = now - timedelta(hours=24)
    
    # Get all emails within the timeframe
    recent_emails = Email.objects.filter(
        date__gte=start_time
    ).values_list('thread_id', flat=True).distinct()
    
    # Get threads that contain these emails with additional information
    threads = Thread.objects.filter(
        id__in=recent_emails
    ).prefetch_related('labels', 'email_set').order_by('-last_email__date')
    
    # Enhance thread data with additional information
    enhanced_threads = [enhance_thread_data(thread) for thread in threads]
    
    context = {
        'threads': enhanced_threads,
        'timeframe': timeframe
    }
    
    return render(request, 'core/timeframe_threads.html', context) 