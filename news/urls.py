from django.urls import path
from .views import NewsListView, NewsCreateView, NewsDeleteView, NewsUpdateView

urlpatterns = [
    path('news/', NewsListView.as_view(), name='news-list'),
    path('news/create/', NewsCreateView.as_view(), name='news-create'),
    path('news/delete/<int:pk>/', NewsDeleteView.as_view(), name='news-delete'),
    path('news/update/<int:pk>/', NewsUpdateView.as_view(), name='news-update'),
]
