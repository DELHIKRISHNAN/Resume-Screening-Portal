from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),  # New modern dashboard as default
    path('legacy/', views.multi_upload_view, name='multi_upload'),
    path('multi/', views.multi_upload_view, name='multi_upload_alt'),
    path('multi-match/', views.multi_match_view, name='multi_match'),
    path('api/analyze/', views.api_analyze_view, name='api_analyze'),
]
