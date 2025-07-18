from django.urls import path
from . import views

app_name = 'members_profile'

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('edit/', views.profile_edit_view, name='profile_edit'),
] 