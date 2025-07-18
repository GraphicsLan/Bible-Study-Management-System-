from django.db import models
from django.contrib.auth import get_user_model
from registration.models import Member

User = get_user_model()

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location_type = models.CharField(
        max_length=20, 
        choices=[('campus', 'Within Campus'), ('offCampus', 'Non-Resident')]
    )
    hall = models.CharField(max_length=100, blank=True, null=True)  # For campus groups
    area = models.CharField(max_length=100, blank=True, null=True)  # For off-campus groups
    estate = models.CharField(max_length=100, blank=True, null=True)  # For off-campus groups
    leader = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='led_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_location_display(self):
        if self.location_type == 'campus':
            return f"Campus - {self.hall}"
        else:
            return f"{self.area} - {self.estate}"
    
    def get_member_count(self):
        return self.members.count()
    
    def is_full(self):
        return self.get_member_count() >= 8

class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['group', 'member']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.group.name}"

class AdminAction(models.Model):
    ACTION_TYPES = [
        ('member_create', 'Member Created'),
        ('member_edit', 'Member Edited'),
        ('member_delete', 'Member Deleted'),
        ('group_create', 'Group Created'),
        ('group_edit', 'Group Edited'),
        ('group_delete', 'Group Deleted'),
        ('member_assign', 'Member Assigned to Group'),
        ('member_remove', 'Member Removed from Group'),
        ('member_move', 'Member Moved Between Groups'),
        ('leader_assign', 'Leader Assigned'),
        ('leader_remove', 'Leader Removed'),
        ('grouping_run', 'Automatic Grouping Run'),
        ('grouping_stop', 'Automatic Grouping Stopped'),
        ('group_rebalance', 'Groups Rebalanced'),
        ('impersonate', 'Admin Impersonated Member'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performed_admin_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True, related_name='received_admin_actions')
    target_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_actions')
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin_user.get_full_name()} - {self.get_action_type_display()} - {self.timestamp}"
