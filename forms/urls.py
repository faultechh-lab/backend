from django.urls import path
from .views import (
    FormListView, FormCreateView, FormVerifiedView, FormDeleteView, 
    FormUpdateView, FormMyListView, FormImageCreateView,
    ReportCreateView, UserBlockView, UserUnblockView
)

urlpatterns = [
    path('forms/', FormListView.as_view(), name='form-list'),
    path('forms/my/', FormMyListView.as_view(), name='form-my-list'),
    path('forms/create/', FormCreateView.as_view(), name='form-create'),
    path('forms/verified/<int:pk>/', FormVerifiedView.as_view(), name='form-verified'),
    path('forms/delete/<int:pk>/', FormDeleteView.as_view(), name='form-delete'),
    path('forms/update/<int:pk>/', FormUpdateView.as_view(), name='form-update'),
    path('forms/<int:pk>/images/', FormImageCreateView.as_view(), name='form-image-create'),
    path('forms/report/', ReportCreateView.as_view(), name='form-report'),
    path('users/block/', UserBlockView.as_view(), name='user-block'),
    path('users/unblock/', UserUnblockView.as_view(), name='user-unblock'),
]