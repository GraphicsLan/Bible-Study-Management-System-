from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from registration.models import Member
from .models import Group, GroupMember
from .services import GroupingService

@login_required
def mygroup_view(request):
    """View for members to see their group details"""
    member = request.user
    group = None
    group_members = []
    
    # Check if member is a leader
    if member.leader_now:
        led_group = member.led_groups.first()
        if led_group:
            group = led_group
            group_members = led_group.members.all()
    else:
        # Check if member is in a group
        membership = member.group_memberships.first()
        if membership:
            group = membership.group
            group_members = group.members.all()
    
    context = {
        'group': group,
        'group_members': group_members,
        'is_leader': member.leader_now,
    }
    
    return render(request, 'dashboard/bs_group.html', context)

@staff_member_required
def admin_groups_view(request):
    """Admin view to see all groups"""
    groups = Group.objects.filter(is_active=True).prefetch_related('members', 'leader')
    
    context = {
        'groups': groups,
    }
    
    return render(request, 'bs_grouping/admin_groups.html', context)

@staff_member_required
def admin_unassigned_view(request):
    """Admin view to see unassigned members"""
    unassigned_members = Member.objects.filter(
        leader_now=False,
        group_memberships__isnull=True
    ).order_by('date_joined')
    
    context = {
        'unassigned_members': unassigned_members,
    }
    
    return render(request, 'bs_grouping/admin_unassigned.html', context)

@staff_member_required
def assign_member_to_group(request, member_id):
    """Assign a member to a specific group"""
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        group_id = request.POST.get('group_id')
        
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            
            # Remove from current group if any
            current_membership = member.group_memberships.first()
            if current_membership:
                current_membership.delete()
            
            # Add to new group
            GroupMember.objects.create(group=group, member=member)
            messages.success(request, f'{member.get_full_name()} assigned to {group.name}')
        else:
            messages.error(request, 'Please select a group')
    
    return redirect('admin_unassigned')

@staff_member_required
def assign_leader_to_group(request, member_id):
    """Assign a member as leader to a group"""
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        group_id = request.POST.get('group_id')
        
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            
            # Remove member from current group if any
            current_membership = member.group_memberships.first()
            if current_membership:
                current_membership.delete()
            
            # Set as leader
            group.leader = member
            group.save()
            
            # Update member's leader status
            member.leader_now = True
            member.save()
            
            messages.success(request, f'{member.get_full_name()} assigned as leader to {group.name}')
        else:
            messages.error(request, 'Please select a group')
    
    return redirect('admin_unassigned')

@staff_member_required
def remove_member_from_group(request, member_id):
    """Remove a member from their current group"""
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        
        # Remove from current group
        membership = member.group_memberships.first()
        if membership:
            group_name = membership.group.name
            membership.delete()
            messages.success(request, f'{member.get_full_name()} removed from {group_name}')
        else:
            messages.error(request, 'Member is not in any group')
    
    return redirect('admin_groups')

@staff_member_required
def run_manual_grouping(request):
    """Manually trigger the grouping process"""
    if request.method == 'POST':
        try:
            grouping_service = GroupingService()
            grouping_service.run_automatic_grouping()
            messages.success(request, 'Manual grouping completed successfully')
        except Exception as e:
            messages.error(request, f'Error during grouping: {str(e)}')
    
    return redirect('admin_groups')

@staff_member_required
def get_available_groups(request):
    """AJAX endpoint to get available groups for assignment"""
    groups = Group.objects.filter(is_active=True)
    group_data = []
    
    for group in groups:
        member_count = group.get_member_count()
        if member_count < 8:  # Only show groups with space
            group_data.append({
                'id': group.id,
                'name': group.name,
                'location': group.get_location_display(),
                'member_count': member_count,
                'available_slots': 8 - member_count
            })
    
    return JsonResponse({'groups': group_data})
