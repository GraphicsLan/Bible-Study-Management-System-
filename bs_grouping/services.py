from django.db import transaction
from django.contrib import messages
from registration.models import Member
from .models import Group, GroupMember
import random
from django.db.models import Count

class GroupingService:
    def __init__(self):
        self.registration_count = 0
    
    def increment_registration_count(self):
        """Increment registration count and trigger grouping if needed"""
        self.registration_count += 1
        if self.registration_count >= 10:
            self.run_automatic_grouping()
            self.registration_count = 0
    
    def run_automatic_grouping(self):
        """Main method to run automatic grouping"""
        try:
            print('Starting automatic grouping...')
            with transaction.atomic():
                # Get unassigned members (not leaders, not already in groups)
                unassigned_members = self.get_unassigned_members()
                print(f'Unassigned members: {list(unassigned_members)}')
                if not unassigned_members:
                    print('No unassigned members found.')
                    return None
                
                # Group by location
                campus_groups = self.group_campus_members(unassigned_members)
                off_campus_groups = self.group_off_campus_members(unassigned_members)
                print(f'Campus groups: {campus_groups}')
                print(f'Off-campus groups: {off_campus_groups}')
                
                # Create groups and assign members
                self.create_groups_from_locations(campus_groups, 'campus')
                self.create_groups_from_locations(off_campus_groups, 'offCampus')
                print('Grouping complete.')
                return 'Grouping complete.'
        except Exception as e:
            print(f"Error in automatic grouping: {e}")
            return f"Error: {e}"
    
    def get_unassigned_members(self):
        """Get members who are not leaders, not already in groups, not staff, not superuser"""
        return Member.objects.filter(
            leader_now=False,
            group_memberships__isnull=True,
            is_superuser=False,
            is_staff=False
        ).order_by('date_joined')
    
    def group_campus_members(self, members):
        """Group campus members by hall"""
        campus_members = members.filter(residency_type='campus')
        groups_by_hall = {}
        
        for member in campus_members:
            hall = member.hall
            if hall not in groups_by_hall:
                groups_by_hall[hall] = []
            groups_by_hall[hall].append(member)
        
        return groups_by_hall
    
    def group_off_campus_members(self, members):
        """Group off-campus members by area only (ignore estate)"""
        off_campus_members = members.filter(residency_type='offCampus')
        groups_by_area = {}
        for member in off_campus_members:
            area = member.area
            if area not in groups_by_area:
                groups_by_area[area] = []
            groups_by_area[area].append(member)
        return groups_by_area
    
    def create_groups_from_locations(self, location_groups, location_type):
        """Create groups from location-based member lists"""
        for location, members in location_groups.items():
            if location_type == 'campus':
                self.create_campus_groups(location, members)
            else:
                area = location
                self.create_off_campus_groups(area, members)
    
    def create_campus_groups(self, hall, members):
        print(f'Creating campus groups for hall: {hall} with members: {members}')
        # Check if there's an existing group with space
        existing_group = Group.objects.filter(
            location_type='campus',
            hall=hall,
            is_active=True
        ).annotate(num_members=Count('members')).filter(num_members__lt=8).first()
        
        if existing_group and existing_group.get_member_count() < 8:
            # Add members to existing group
            available_slots = 8 - existing_group.get_member_count()
            members_to_add = members[:available_slots]
            print(f'Adding to existing group {existing_group.name}: {members_to_add}')
            self.add_members_to_group(existing_group, members_to_add)
            members = members[available_slots:]
        
        # Create new groups for remaining members
        while members:
            group_size = min(8, len(members))
            group_members = members[:group_size]
            members = members[group_size:]
            # Create unique group name
            base_name = f"{hall} Group"
            existing_names = set(Group.objects.filter(location_type='campus', hall=hall).values_list('name', flat=True))
            i = 1
            while f"{base_name} {i}" in existing_names:
                i += 1
            group_name = f"{base_name} {i}"
            print(f'Creating new group: {group_name} with members: {group_members}')
            # Create group
            group = Group.objects.create(
                name=group_name,
                location_type='campus',
                hall=hall
            )
            # Add members with balancing
            self.add_members_to_group(group, group_members)
    
    def create_off_campus_groups(self, area, members):
        print(f'Creating off-campus groups for area: {area} with members: {members}')
        # Check if there's an existing group with space
        existing_group = Group.objects.filter(
            location_type='offCampus',
            area=area,
            is_active=True
        ).annotate(num_members=Count('members')).filter(num_members__lt=8).first()
        if existing_group and existing_group.get_member_count() < 8:
            # Add members to existing group
            available_slots = 8 - existing_group.get_member_count()
            members_to_add = members[:available_slots]
            print(f'Adding to existing group {existing_group.name}: {members_to_add}')
            self.add_members_to_group(existing_group, members_to_add)
            members = members[available_slots:]
        # Create new groups for remaining members
        while members:
            group_size = min(8, len(members))
            group_members = members[:group_size]
            members = members[group_size:]
            # Create unique group name
            base_name = f"{area} Group"
            existing_names = set(Group.objects.filter(location_type='offCampus', area=area).values_list('name', flat=True))
            i = 1
            while f"{base_name} {i}" in existing_names:
                i += 1
            group_name = f"{base_name} {i}"
            print(f'Creating new group: {group_name} with members: {group_members}')
            # Create group
            group = Group.objects.create(
                name=group_name,
                location_type='offCampus',
                area=area
            )
            # Add members with balancing
            self.add_members_to_group(group, group_members)
    
    def add_members_to_group(self, group, members):
        """Add members to a group with balancing considerations"""
        # Sort members by various criteria for better distribution
        sorted_members = self.sort_members_for_balancing(members)
        
        for member in sorted_members:
            GroupMember.objects.create(group=group, member=member)
    
    def sort_members_for_balancing(self, members):
        """Sort members to balance years of study, gender, and session experience"""
        # Convert to list for sorting
        member_list = list(members)
        
        # Sort by sessions attended (descending) to distribute experienced members
        member_list.sort(key=lambda x: x.sessions_attended, reverse=True)
        
        # Sort by year of study to distribute years
        member_list.sort(key=lambda x: x.year_of_study or '0')
        
        # Sort by gender to mix genders
        member_list.sort(key=lambda x: x.gender)
        
        return member_list
    
    def get_member_group(self, member):
        """Get the group a member belongs to"""
        try:
            return member.group_memberships.first().group
        except:
            return None
    
    def assign_leader_to_group(self, member, group):
        """Assign a member as leader to a group"""
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
    
    def remove_leader_from_group(self, member):
        """Remove a member from leadership"""
        # Remove from led groups
        led_groups = member.led_groups.all()
        for group in led_groups:
            group.leader = None
            group.save()
        
        # Update member's leader status
        member.leader_now = False
        member.save() 