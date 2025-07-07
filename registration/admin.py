# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('user_id','full_name', 'email', 'phone', 'gender', 'year_of_study', 'sessions_attended')
    search_fields = ('user_id', 'email', 'phone')
    list_filter = ('gender', 'year_of_study')



