import random
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import BibleStudy, WeeklyReflection
from .models import Member
from .backend import MemberAuthBackend

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Member.objects.filter(email=email).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Email already registered.'})
            else:
                messages.error(request, 'Email already registered.')
                return render(request, 'registration/reg.html')

        # Generate random member ID
        member_id = random.randint(1000, 9999)
        while Member.objects.filter(member_id=member_id).exists():
            member_id = random.randint(1000, 9999)
        
        # Split full name into first and last names
        full_name_str = request.POST.get('fullName', '').strip()
        if not full_name_str:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Full name is required.'})
            else:
                messages.error(request, 'Full name is required.')
                return render(request, 'registration/reg.html')
        full_name = full_name_str.split(' ', 1)
        first_name = full_name[0]
        last_name = full_name[1] if len(full_name) > 1 else ''
        
        # Create member with password 
        password = str(member_id)  
        try:
            new_member = Member.objects.create_user(
                email=email,
                member_id=member_id,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=request.POST.get('phone'),
                gender=request.POST.get('gender'),
                year_of_study=request.POST.get('yearOfStudy'),
                sessions_attended=int(request.POST.get('sessionsAttended', 0)),
                leader_before=request.POST.get('leaderBefore', '').lower() == 'yes',
                leader_now=request.POST.get('leaderNow', '').lower() == 'yes',
                residency_type=request.POST.get('residencyType'),
                hall=request.POST.get('hall', ''),
                area=request.POST.get('area', ''),
                estate=request.POST.get('estate', '')
            )
            
            # Send email with login details
            subject = 'Your EUNCCU Bible Study Login Details'
            html_message = render_to_string('registration/email_template.html', {
                'member': new_member,
                'member_id': new_member.member_id,
                'password': password,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [new_member.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Return JSON response for AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                'status': 'success',
                'member_id': new_member.member_id,
                'loginUrl': reverse('login'),  
                 })
            
            messages.success(request, 'Registration successful! Please check your email for login details.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'registration/reg.html')
    
    return render(request, 'registration/reg.html')

def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('loginId')  #  email or phone
        member_id = request.POST.get('memberId')
        password = str(member_id)  # Default password is member ID
        
        # First try authenticating with email
        user = authenticate(request, email=login_id, password=password)
        
        # If that fails, try with phone
        if user is None:
            try:
                member = Member.objects.get(phone=login_id)
                user = authenticate(request, email=member.email, password=password)
            except Member.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    
    return render(request, 'registration/login.html')

from .models import BibleStudy, WeeklyReflection

@login_required
def dashboard_view(request):
    try:
        current_study = BibleStudy.objects.get(is_current=True)
    except BibleStudy.DoesNotExist:
        current_study = None
    
    try:
        latest_reflection = WeeklyReflection.objects.filter(
            bible_study=current_study
        ).latest('date') if current_study else None
    except WeeklyReflection.DoesNotExist:
        latest_reflection = None
    
    context = {
        'current_study': current_study,
        'latest_reflection': latest_reflection,
    }
    return render(request, 'dashboard/dashboard.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def mygroup_view(request):
    return render(request, 'dashboard/bs_group.html')

@login_required
def discussion_view(request):
    return render(request, 'dashboard/discussion.html')

@login_required
def biblestudy_view(request):
    return render(request, 'dashboard/biblestudies.html')

@login_required
def profile_view (request):
    return render(request, 'dashboard/profile.html')


