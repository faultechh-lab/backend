from django.urls import path
from .views import NotificationListView, NotificationCreateView, NotificationDeleteView, NotificationMarkAllReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('create/', NotificationCreateView.as_view(), name='notification-create'),
    path('delete/<int:pk>/', NotificationDeleteView.as_view(), name='notification-delete'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
]
