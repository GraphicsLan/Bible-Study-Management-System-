from django.urls import path
from . import views

app_name = 'registration'  

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

urlpatterns += [
    # Dashboard URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.login_view, name='home'),    
    path('mygroup/', views.mygroup_view, name='mygroup'),
    path('discussion/', views.discussion_view, name='discussion'),
    path('biblestudies/', views.biblestudy_view, name='biblestudies'),
    path('profile/', views.profile_view, name='profile'),
    path('update_profile/', views.profile_view, name='update_profile'),
]