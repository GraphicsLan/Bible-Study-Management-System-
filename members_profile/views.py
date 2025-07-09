from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Create your views here.
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        full_name_str = request.POST.get('fullName', '').strip()
        if not full_name_str:
            messages.error(request, 'Full name is required.')
            return redirect('profile')
        full_name_parts = full_name_str.split(' ', 1)
        user.first_name = full_name_parts[0]
        user.last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        

        # Update other profile fields
        user.gender = request.POST.get('gender', user.gender)
        user.year_of_study = request.POST.get('yearOfStudy', user.year_of_study)
        user.residency_type = request.POST.get('residencyType', user.residency_type)
        user.hall = request.POST.get('hall', user.hall)
        user.area = request.POST.get('area', user.area)
        user.estate = request.POST.get('estate', user.estate)
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')