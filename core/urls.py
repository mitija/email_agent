from django.urls import path
from core.views.contact_review import ContactReviewListView, ContactReviewUpdateView, complete_review, search_contacts, update_contact_details
from core.views.orphaned_contacts import OrphanedContactsListView, delete_contact, delete_all_orphaned_contacts
from core.views.thread_list import thread_list, summarize_thread, get_labels, thread_detail
from core.views.home import HomeView
from core.views.contact_list import ContactListView, ContactDetailView
from core.views.email_string_list import email_string_list, update_email_string_contact, create_contact
from core.views.timeframe_threads import timeframe_threads

urlpatterns = [
    # Home page
    path('', HomeView.as_view(), name='home'),
    
    # Contact list and details
    path('contacts/', ContactListView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    
    # Contact review
    path('contact-review/', ContactReviewListView.as_view(), name='contact_review_list'),
    path('contact-review/update/<int:pk>/', ContactReviewUpdateView.as_view(), name='contact_review_update'),
    path('contact-review/complete/', complete_review, name='contact_review_complete'),
    path('contact-review/search-contacts/', search_contacts, name='search_contacts'),
    path('contact-review/update-details/<int:contact_id>/', update_contact_details, name='update_contact_details'),
    
    # Orphaned contacts
    path('orphaned-contacts/', OrphanedContactsListView.as_view(), name='orphaned_contacts_list'),
    path('orphaned-contacts/delete/<int:contact_id>/', delete_contact, name='delete_contact'),
    path('orphaned-contacts/delete-all/', delete_all_orphaned_contacts, name='delete_all_orphaned_contacts'),
    
    # Thread operations
    path('threads/', thread_list, name='thread_list'),
    path('threads/<int:thread_id>/', thread_detail, name='thread_detail'),
    path('threads/<int:thread_id>/summarize/', summarize_thread, name='summarize_thread'),
    path('threads/labels/', get_labels, name='get_labels'),
    path('timeframe-threads/', timeframe_threads, name='timeframe_threads'),
    
    # Email strings
    path('email-strings/', email_string_list, name='email_string_list'),
    path('api/email-strings/update-contact/', update_email_string_contact, name='update_email_string_contact'),
    path('api/contacts/search/', search_contacts, name='api_search_contacts'),
    path('api/contacts/<int:contact_id>/', ContactDetailView.as_view(), name='api_contact_detail'),
    path('api/contacts/create/', create_contact, name='api_create_contact'),
] 