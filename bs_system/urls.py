"""
URL configuration for bs_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from registration import views
from django.conf.urls.static import static
from django.conf import settings
from bs_grouping import views as grouping_views

# Customize the default admin site
admin.site.site_header = "Bible Study System Administration"
admin.site.site_title = "Bible Study Admin"
admin.site.index_title = "Bible Study System Dashboard"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.login_view, name='home'),
    path('mygroup/', grouping_views.mygroup_view, name='mygroup'),
    path('discussion/', views.discussion_view, name='discussion'),
    path('biblestudies/', views.biblestudy_view, name='biblestudies'),
    path('profile/', include('members_profile.urls')),
    path('stop-impersonation/', views.stop_impersonation_view, name='stop_impersonation'),
]

