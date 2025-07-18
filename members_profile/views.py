from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from registration.models import Member
from bs_grouping.models import AdminAction

User = get_user_model()

@login_required
def profile_view(request):
    """Display and update user profile"""
    user = request.user
    old_residency = user.residency_type
    old_hall = user.hall
    old_area = user.area
    group_changed = False
    if request.method == 'POST':
        try:
            # Split full name into first and last names
            full_name_str = request.POST.get('fullName', '').strip()
            if not full_name_str:
                messages.error(request, 'Full name is required.')
                return redirect('profile')
            full_name_parts = full_name_str.split(' ', 1)
            user.first_name = full_name_parts[0]
            user.last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''
            # Update other profile fields
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.gender = request.POST.get('gender', user.gender)
            user.year_of_study = request.POST.get('yearOfStudy', user.year_of_study)
            new_residency = request.POST.get('residencyType', user.residency_type)
            new_hall = request.POST.get('hall', user.hall)
            new_area = request.POST.get('area', user.area)
            user.residency_type = new_residency
            user.hall = new_hall
            user.area = new_area
            user.estate = request.POST.get('estate', user.estate)
            user.sessions_attended = int(request.POST.get('sessionsAttended', user.sessions_attended))
            # Check if residency/location changed
            if (old_residency != new_residency) or (old_hall != new_hall) or (old_area != new_area):
                group_changed = True
            user.save()
            # If residency/location changed, update group assignment
            if group_changed:
                # Remove from old group
                if hasattr(user, 'group_memberships'):
                    user.group_memberships.all().delete()
                # Assign to new group if available
                from bs_grouping.models import Group, GroupMember
                group = None
                if new_residency == 'campus' and new_hall:
                    group = Group.objects.filter(is_active=True, location_type='campus', hall=new_hall).first()
                elif new_residency == 'offCampus' and new_area:
                    group = Group.objects.filter(is_active=True, location_type='offCampus', area=new_area).first()
                if group:
                    GroupMember.objects.get_or_create(group=group, member=user)
                    messages.info(request, f'You have been assigned to group: {group.name}')
                else:
                    messages.info(request, 'No suitable group found for your new residency/location. You are currently unassigned.')
            # Log admin action if user is admin
            if hasattr(user, 'is_superuser') and user.is_superuser:
                AdminAction.objects.create(
                    admin_user=user,
                    action_type='member_edit',
                    target_member=user,
                    description=f'Updated own profile',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    # Get user's group info for display
    group_membership = user.group_memberships.first() if hasattr(user, 'group_memberships') else None
    led_groups = user.led_groups.all() if hasattr(user, 'led_groups') else []
    context = {
        'user': user,
        'group_membership': group_membership,
        'led_groups': led_groups,
    }
    return render(request, 'members_profile/profile.html', context)

@login_required
def profile_edit_view(request):
    """Edit profile view with form"""
    user = request.user
    
    if request.method == 'POST':
        return profile_view(request)  # Handle the POST in profile_view
    
    # Get user's group info for display
    group_membership = user.group_memberships.first() if hasattr(user, 'group_memberships') else None
    led_groups = user.led_groups.all() if hasattr(user, 'led_groups') else []
    
    context = {
        'user': user,
        'group_membership': group_membership,
        'led_groups': led_groups,
        'is_edit': True,
    }
    
    return render(request, 'members_profile/profile_edit.html', context)