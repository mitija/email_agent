from django.urls import path
from core.views.contact_review import ContactReviewListView, ContactReviewUpdateView, complete_review

urlpatterns = [
    # ... existing urls ...
    path('contact-review/', ContactReviewListView.as_view(), name='contact_review_list'),
    path('contact-review/update/<int:pk>/', ContactReviewUpdateView.as_view(), name='contact_review_update'),
    path('contact-review/complete/', complete_review, name='contact_review_complete'),
] 