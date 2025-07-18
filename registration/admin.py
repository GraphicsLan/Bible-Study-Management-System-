# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.sessions.models import Session
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Member, BibleStudy, WeeklyReflection
from bs_grouping.models import Group, GroupMember, AdminAction
from bs_grouping.services import GroupingService

class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'member_id', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff', 'is_active',
        'phone', 'gender', 'year_of_study', 'sessions_attended',
        'leader_before', 'leader_now', 'residency_type', 'hall', 'area', 'estate', 'date_joined', 'group_info', 'superuser_highlight'
    )
    list_editable = ('first_name', 'last_name', 'email', 'phone', 'gender', 'year_of_study', 'sessions_attended', 
                     'leader_before', 'leader_now', 'residency_type', 'hall', 'area', 'estate')
    search_fields = ('member_id', 'email', 'phone', 'first_name', 'last_name', 'hall', 'area', 'estate')
    list_filter = ('is_superuser', 'is_staff', 'is_active', 'gender', 'year_of_study', 'residency_type', 'leader_before', 'leader_now')
    actions = ['assign_to_group', 'remove_from_group', 'make_leader', 'remove_leader', 'impersonate_member', 'run_automatic_grouping', 'stop_automatic_grouping', 'export_members']
    
    def group_info(self, obj):
        group_membership = obj.group_memberships.first()
        if group_membership:
            return format_html('<a href="{}">{}</a>', 
                             reverse('admin:bs_grouping_group_change', args=[group_membership.group.id]),
                             group_membership.group.name)
        return "Unassigned"
    group_info.short_description = 'Group'
    
    def superuser_highlight(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color: red; font-weight: bold;">SUPERUSER</span>')
        elif obj.is_staff:
            return format_html('<span style="color: #007bff; font-weight: bold;">STAFF</span>')
        return ''
    superuser_highlight.short_description = 'Role'
    
    def assign_to_group(self, request, queryset):
        # Exclude superusers and staff
        filtered_queryset = queryset.filter(is_superuser=False, is_staff=False)
        if queryset.exclude(is_superuser=False, is_staff=False).exists():
            self.message_user(request, "Superusers and staff cannot be assigned to groups.", messages.ERROR)
            return
        if len(filtered_queryset) != 1:
            self.message_user(request, "Please select exactly one eligible member to assign to a group (not superuser or staff).", messages.ERROR)
            return
        member = filtered_queryset.first()
        # Only assign to a group with the same residency_type
        if member.residency_type == 'campus':
            if not member.hall:
                self.message_user(request, "Campus member must have a hall specified to be assigned to a group.", messages.ERROR)
                return
            available_groups = Group.objects.filter(is_active=True, location_type='campus', hall=member.hall)
            if not available_groups.exists():
                # Create a new group for this hall
                base_name = f"{member.hall} Group"
                existing_names = set(Group.objects.filter(location_type='campus', hall=member.hall).values_list('name', flat=True))
                i = 1
                while f"{base_name} {i}" in existing_names:
                    i += 1
                group_name = f"{base_name} {i}"
                group = Group.objects.create(name=group_name, location_type='campus', hall=member.hall)
            else:
                group = available_groups.first()
        elif member.residency_type == 'offCampus':
            if not member.area:
                self.message_user(request, "Off-campus member must have an area specified to be assigned to a group.", messages.ERROR)
                return
            available_groups = Group.objects.filter(is_active=True, location_type='offCampus', area=member.area)
            if not available_groups.exists():
                # Create a new group for this area
                base_name = f"{member.area} Group"
                existing_names = set(Group.objects.filter(location_type='offCampus', area=member.area).values_list('name', flat=True))
                i = 1
                while f"{base_name} {i}" in existing_names:
                    i += 1
                group_name = f"{base_name} {i}"
                group = Group.objects.create(name=group_name, location_type='offCampus', area=member.area)
            else:
                group = available_groups.first()
        else:
            self.message_user(request, "Member residency type is not set or not recognized.", messages.ERROR)
            return
        GroupMember.objects.get_or_create(group=group, member=member)
        # Log admin action
        AdminAction.objects.create(
            admin_user=request.user,
            action_type='member_assign',
            target_member=member,
            target_group=group,
            description=f'Assigned {member.get_full_name()} to {group.name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        self.message_user(request, f"Member {member.get_full_name()} assigned to {group.name}")
    assign_to_group.short_description = "Assign selected member to group"
    
    def remove_from_group(self, request, queryset):
        for member in queryset:
            group_memberships = member.group_memberships.all()
            for membership in group_memberships:
                group_name = membership.group.name
                membership.delete()
                
                # Log admin action
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='member_remove',
                    target_member=member,
                    target_group=membership.group,
                    description=f'Removed {member.get_full_name()} from {group_name}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        
        self.message_user(request, f"Removed {queryset.count()} member(s) from their groups")
    remove_from_group.short_description = "Remove selected members from groups"
    
    def make_leader(self, request, queryset):
        # Exclude superusers and staff
        filtered_queryset = queryset.filter(is_superuser=False, is_staff=False)
        if queryset.exclude(is_superuser=False, is_staff=False).exists():
            self.message_user(request, "Superusers and staff cannot be made leaders.", messages.ERROR)
            return
        for member in filtered_queryset:
            # Only assign as leader to a group with the same residency_type and location
            if member.residency_type == 'campus':
                if not member.hall:
                    self.message_user(request, f"Campus member {member.get_full_name()} must have a hall specified to be made a leader.", messages.ERROR)
                    continue
                available_groups = Group.objects.filter(is_active=True, location_type='campus', hall=member.hall)
            elif member.residency_type == 'offCampus':
                if not member.area:
                    self.message_user(request, f"Off-campus member {member.get_full_name()} must have an area specified to be made a leader.", messages.ERROR)
                    continue
                available_groups = Group.objects.filter(is_active=True, location_type='offCampus', area=member.area)
            else:
                self.message_user(request, f"Member {member.get_full_name()} residency type is not set or not recognized.", messages.ERROR)
                continue
            if not available_groups.exists():
                self.message_user(request, f"No suitable group found for {member.get_full_name()}'s residency and location.", messages.ERROR)
                continue
            # For simplicity, assign as leader to the first available group
            group = available_groups.first()
            group.leader = member
            group.save()
            member.leader_now = True
            member.save()
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='leader_assign',
                target_member=member,
                target_group=group,
                description=f'Made {member.get_full_name()} a leader of {group.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        self.message_user(request, f"Processed leader assignment for {filtered_queryset.count()} member(s)")
    make_leader.short_description = "Make selected members leaders"
    
    def remove_leader(self, request, queryset):
        for member in queryset:
            member.leader_now = False
            member.save()
            
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='leader_remove',
                target_member=member,
                description=f'Removed leadership from {member.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        self.message_user(request, f"Removed leadership from {queryset.count()} member(s)")
    remove_leader.short_description = "Remove leadership from selected members"
    
    def impersonate_member(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, "Please select exactly one member to impersonate.", messages.ERROR)
            return
        
        member = queryset.first()
        
        # Store original user in session
        request.session['original_user_id'] = request.user.id
        request.session['impersonated_member_id'] = member.id
        
        # Log in as the member
        login(request, member)
        
        # Log admin action
        AdminAction.objects.create(
            admin_user=request.user,
            action_type='impersonate',
            target_member=member,
            description=f'Impersonated {member.get_full_name()}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        self.message_user(request, f"Now impersonating {member.get_full_name()}")
        return redirect('dashboard')
    impersonate_member.short_description = "Impersonate selected member"
    
    def run_automatic_grouping(self, request, queryset):
        try:
            grouping_service = GroupingService()
            result = grouping_service.run_automatic_grouping()
            
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='grouping_run',
                description=f'Ran automatic grouping: {result}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            self.message_user(request, f"Automatic grouping completed: {result}")
        except Exception as e:
            self.message_user(request, f"Error running automatic grouping: {str(e)}", messages.ERROR)
    run_automatic_grouping.short_description = "Run automatic grouping"
    
    def stop_automatic_grouping(self, request, queryset):
        try:

            AdminAction.objects.create(
                admin_user=request.user,
                action_type='grouping_stop',
                description='Stopped automatic grouping process',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            self.message_user(request, "Automatic grouping process stopped")
        except Exception as e:
            self.message_user(request, f"Error stopping automatic grouping: {str(e)}", messages.ERROR)
    stop_automatic_grouping.short_description = "Stop automatic grouping"

    def export_members(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="members.csv"'
        writer = csv.writer(response)
        # header
        writer.writerow([
            'Group', 'Member Name', 'Email', 'Phone', 'Gender', 'Year of Study', 'Residency', 'Joined At'
        ])
        for member in queryset:
            group_membership = member.group_memberships.first()
            group_name = group_membership.group.name if group_membership else ''
            writer.writerow([
                group_name,
                member.get_full_name(),
                member.email,
                member.phone,
                member.gender,
                member.year_of_study,
                member.residency_type,
                member.date_joined
            ])
        return response
    export_members.short_description = "Export selected members as CSV"

class WeeklyReflectionInline(admin.TabularInline):
    model = WeeklyReflection
    extra = 1

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

class WeeklyReflectionAdmin(admin.ModelAdmin):
    list_display = ('bible_study', 'week_number', 'scripture_reference', 'date')
    list_filter = ('bible_study',)
    search_fields = ('scripture_reference', 'scripture_text')

# Register models with Django's default admin
admin.site.register(Member, MemberAdmin)
admin.site.register(BibleStudy, BibleStudyAdmin)
admin.site.register(WeeklyReflection, WeeklyReflectionAdmin)