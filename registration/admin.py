# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Member
from .models import BibleStudy, WeeklyReflection

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'first_name', 'last_name', 'email', 'phone', 'gender', 'year_of_study', 'sessions_attended',
                    'leader_before', 'leader_now', 'residency_type', 'hall', 'area', 'estate', 'date_joined')
    list_editable = ('first_name', 'last_name', 'email', 'phone', 'gender', 'year_of_study', 'sessions_attended', 
                     'leader_before', 'leader_now', 'residency_type', 'hall', 'area', 'estate')
    search_fields = ('member_id', 'email', 'phone', 'first_name', 'last_name', 'hall', 'area', 'estate')
    list_filter = ('gender', 'year_of_study', 'residency_type', 'leader_before', 'leader_now')
    

class WeeklyReflectionInline(admin.TabularInline):
    model = WeeklyReflection
    extra = 1

@admin.register(BibleStudy)
class BibleStudyAdmin(admin.ModelAdmin):
    list_display = ('book', 'title', 'is_current', 'start_date', 'end_date')
    list_filter = ('is_current',)
    search_fields = ('book', 'title')
    inlines = [WeeklyReflectionInline]
    
    def save_model(self, request, obj, form, change):
        # Ensure only one study is marked as current
        if obj.is_current:
            BibleStudy.objects.exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)

@admin.register(WeeklyReflection)
class WeeklyReflectionAdmin(admin.ModelAdmin):
    list_display = ('bible_study', 'week_number', 'scripture_reference', 'date')
    list_filter = ('bible_study',)
    search_fields = ('scripture_reference', 'scripture_text')