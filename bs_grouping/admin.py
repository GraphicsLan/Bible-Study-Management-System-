from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Group, GroupMember, AdminAction
from registration.models import Member
from .services import GroupingService

class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1
    autocomplete_fields = ['member']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'leader', 'member_count', 'is_active', 'created_at', 'group_status')
    list_filter = ('location_type', 'is_active', 'created_at')
    search_fields = ('name', 'hall', 'area', 'estate')
    autocomplete_fields = ['leader']
    inlines = [GroupMemberInline]
    actions = ['activate_groups', 'deactivate_groups', 'assign_leader', 'remove_leader', 'run_automatic_grouping', 'stop_automatic_grouping', 'rebalance_groups', 'export_groups_with_members']
    
    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = 'Members'
    
    def group_status(self, obj):
        member_count = obj.get_member_count()
        if member_count == 0:
            return format_html('<span style="color: #dc3545;">Empty</span>')
        elif member_count < 4:
            return format_html('<span style="color: #ffc107;">Small</span>')
        elif member_count <= 8:
            return format_html('<span style="color: #28a745;">Optimal</span>')
        else:
            return format_html('<span style="color: #dc3545;">Overflow</span>')
    group_status.short_description = 'Status'
    
    def activate_groups(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} group(s)")
    activate_groups.short_description = "Activate selected groups"
    
    def deactivate_groups(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} group(s)")
    deactivate_groups.short_description = "Deactivate selected groups"
    
    def assign_leader(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, "Please select exactly one group to assign a leader.", messages.ERROR)
            return
        
        group = queryset.first()
        available_leaders = Member.objects.filter(leader_now=True, group_memberships__isnull=True)
        
        if not available_leaders.exists():
            self.message_user(request, "No available leaders found.", messages.ERROR)
            return
        
        # For simplicity, assign the first available leader
        leader = available_leaders.first()
        group.leader = leader
        group.save()
        
        # Add leader to group members
        GroupMember.objects.get_or_create(group=group, member=leader)
        
        # Log admin action
        AdminAction.objects.create(
            admin_user=request.user,
            action_type='leader_assign',
            target_member=leader,
            target_group=group,
            description=f'Assigned {leader.get_full_name()} as leader of {group.name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        self.message_user(request, f"Assigned {leader.get_full_name()} as leader of {group.name}")
    assign_leader.short_description = "Assign leader to selected group"
    
    def remove_leader(self, request, queryset):
        for group in queryset:
            if group.leader:
                leader_name = group.leader.get_full_name()
                group.leader = None
                group.save()
                
                # Log admin action
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='leader_remove',
                    target_member=group.leader,
                    target_group=group,
                    description=f'Removed {leader_name} as leader of {group.name}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        
        self.message_user(request, f"Removed leaders from {queryset.count()} group(s)")
    remove_leader.short_description = "Remove leader from selected groups"
    
    def run_automatic_grouping(self, request, queryset):
        try:
            grouping_service = GroupingService()
            result = grouping_service.run_automatic_grouping()
            
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='grouping_run',
                description=f'Ran automatic grouping from group admin: {result}',
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
                description='Stopped automatic grouping process from group admin',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            self.message_user(request, "Automatic grouping process stopped")
        except Exception as e:
            self.message_user(request, f"Error stopping automatic grouping: {str(e)}", messages.ERROR)
    stop_automatic_grouping.short_description = "Stop automatic grouping"
    
    def rebalance_groups(self, request, queryset):
        try:
            # Gather all members from selected groups
            all_members = []
            for group in queryset:
                all_members.extend([gm.member for gm in group.members.all()])
                group.members.all().delete()
            # Sort and redistribute members for balance
            grouping_service = GroupingService()
            sorted_members = grouping_service.sort_members_for_balancing(all_members)
            group_list = list(queryset)
            group_count = len(group_list)
            if group_count == 0:
                self.message_user(request, "No groups selected for rebalancing.", messages.ERROR)
                return
            # Distribute members round-robin
            for idx, member in enumerate(sorted_members):
                group = group_list[idx % group_count]
                GroupMember.objects.create(group=group, member=member)
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='group_rebalance',
                description=f'Rebalanced {queryset.count()} groups',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            self.message_user(request, f"Rebalanced {queryset.count()} group(s)")
        except Exception as e:
            self.message_user(request, f"Error rebalancing groups: {str(e)}", messages.ERROR)
    rebalance_groups.short_description = "Rebalance selected groups"

    def export_groups_with_members(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="groups_with_members.csv"'
        writer = csv.writer(response)
        # Write header
        writer.writerow([
            'Group Name', 'Location', 'Leader', 'Member Name', 'Member Email', 'Member Phone', 'Gender', 'Year of Study', 'Joined At'
        ])
        for group in queryset:
            leader_name = group.leader.get_full_name() if group.leader else ''
            location = group.get_location_display()
            members = group.members.all()
            if members:
                for gm in members:
                    member = gm.member
                    writer.writerow([
                        group.name,
                        location,
                        leader_name,
                        member.get_full_name(),
                        member.email,
                        member.phone,
                        member.gender,
                        member.year_of_study,
                        gm.joined_at
                    ])
            else:
                writer.writerow([
                    group.name,
                    location,
                    leader_name,
                    '', '', '', '', '', ''
                ])
        return response
    export_groups_with_members.short_description = "Export selected groups and members as CSV"

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('member', 'group', 'joined_at', 'member_info')
    list_filter = ('group', 'joined_at', 'member__gender', 'member__year_of_study')
    search_fields = ('member__first_name', 'member__last_name', 'member__email', 'group__name')
    autocomplete_fields = ['member', 'group']
    actions = ['remove_from_groups', 'move_to_different_group']
    
    def member_info(self, obj):
        return f"{obj.member.gender} | Year {obj.member.year_of_study or 'N/A'} | {obj.member.residency_type}"
    member_info.short_description = 'Member Details'
    
    def remove_from_groups(self, request, queryset):
        for membership in queryset:
            member_name = membership.member.get_full_name()
            group_name = membership.group.name
            membership.delete()
            
            # Log admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='member_remove',
                target_member=membership.member,
                target_group=membership.group,
                description=f'Removed {member_name} from {group_name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        self.message_user(request, f"Removed {queryset.count()} member(s) from their groups")
    remove_from_groups.short_description = "Remove selected members from groups"
    
    def move_to_different_group(self, request, queryset):
        if len(queryset) != 1:
            self.message_user(request, "Please select exactly one member to move.", messages.ERROR)
            return
        
        membership = queryset.first()
        available_groups = Group.objects.filter(is_active=True).exclude(id=membership.group.id)
        
        if not available_groups.exists():
            self.message_user(request, "No other groups available.", messages.ERROR)
            return
        
        # For simplicity, move to the first available group
        new_group = available_groups.first()
        old_group_name = membership.group.name
        new_group_name = new_group.name
        
        # Create new membership and delete old one
        GroupMember.objects.create(group=new_group, member=membership.member)
        membership.delete()
        
        # Log admin action
        AdminAction.objects.create(
            admin_user=request.user,
            action_type='member_move',
            target_member=membership.member,
            target_group=new_group,
            description=f'Moved {membership.member.get_full_name()} from {old_group_name} to {new_group_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        self.message_user(request, f"Moved {membership.member.get_full_name()} from {old_group_name} to {new_group_name}")
    move_to_different_group.short_description = "Move selected member to different group"

@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'action_type', 'target_member', 'target_group', 'timestamp', 'ip_address', 'action_summary')
    list_filter = ('action_type', 'timestamp', 'admin_user')
    search_fields = ('admin_user__username', 'admin_user__first_name', 'admin_user__last_name', 
                    'target_member__first_name', 'target_member__last_name', 'target_member__email',
                    'target_group__name', 'description')
    readonly_fields = ('admin_user', 'action_type', 'target_member', 'target_group', 'description', 'timestamp', 'ip_address')
    date_hierarchy = 'timestamp'
    actions = ['export_actions']
    
    def action_summary(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    action_summary.short_description = 'Summary'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def export_actions(self, request, queryset):
        import csv
        from django.http import HttpResponse
        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_actions.csv"'
        writer = csv.writer(response)
        # Write header
        writer.writerow([
            'Admin User', 'Action Type', 'Target Member', 'Target Group', 'Description', 'Timestamp', 'IP Address'
        ])
        # Write data rows
        for action in queryset:
            writer.writerow([
                str(action.admin_user),
                action.get_action_type_display(),
                str(action.target_member) if action.target_member else '',
                str(action.target_group) if action.target_group else '',
                action.description,
                action.timestamp,
                action.ip_address or ''
            ])
        return response
    export_actions.short_description = "Export selected actions"
