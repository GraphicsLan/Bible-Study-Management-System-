import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Member, BibleStudy, WeeklyReflection
from django.contrib.sites.shortcuts import get_current_site
from bs_grouping.services import GroupingService

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Member.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'registration/reg.html')

        # Generate random member ID
        member_id = random.randint(1000, 9999)
        while Member.objects.filter(member_id=member_id).exists():
            member_id = random.randint(1000, 9999)
        
        # Split full name into first and last names
        full_name_str = request.POST.get('fullName', '').strip()
        if not full_name_str:
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
            site_url = f"https://{get_current_site(request)}"
            html_message = render_to_string('registration/email_template.html', {
                'member': new_member,
                'member_id': new_member.member_id,
                'password': password,
                'site_url': site_url,
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

            # Trigger automatic grouping after registration
            grouping_service = GroupingService()
            grouping_service.increment_registration_count()

            # Success: show message and redirect to login with countdown
            messages.success(request, f'Registration successful! Your Member ID is {new_member.member_id}. Please check your email for login details.')
            request.session['show_countdown'] = True
            request.session['registered_member_id'] = new_member.member_id
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'registration/reg.html')
    
    return render(request, 'registration/reg.html')

def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('loginId')  # email or phone
        member_id = request.POST.get('memberId')
        password = str(member_id)  # Default password is member ID

        # Try to find member by email or phone
        member = Member.objects.filter(email=login_id).first()
        if not member:
            member = Member.objects.filter(phone=login_id).first()

        if member:
            user = authenticate(request, email=member.email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome {user.get_full_name()}! You have successfully logged in.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid member ID or password. Please try again.')
        else:
            messages.error(request, 'No account found with that email or phone number.')

    # Show countdown and member ID if redirected from registration
    show_countdown = request.session.pop('show_countdown', False)
    registered_member_id = request.session.pop('registered_member_id', None)
    context = {
        'show_countdown': show_countdown,
        'registered_member_id': registered_member_id,
    }
    return render(request, 'registration/login.html', context)


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
    # TODO: Implement group summary and details for the user
    # Pass the user to the template and let it handle the logic like dashboard.html does
    return render(request, 'dashboard/bs_group.html')

@login_required
def discussion_view(request):
    # TODO: Implement group discussion feature
    return render(request, 'dashboard/discussion.html')

@login_required
def biblestudy_view(request):
    # TODO: Implement Bible studies listing and details
    return render(request, 'dashboard/biblestudies.html')

@login_required
def stop_impersonation_view(request):
    """Stop impersonating a member and return to admin user"""
    if 'original_user_id' in request.session:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            original_user = User.objects.get(id=request.session['original_user_id'])
            login(request, original_user)
            
            # Clear session data
            request.session.pop('original_user_id', None)
            request.session.pop('impersonated_member_id', None)
            
            messages.success(request, 'Stopped impersonating member and returned to admin account.')
            return redirect('admin:index')
        except User.DoesNotExist:
            messages.error(request, 'Original admin user not found.')
            return redirect('login')
    else:
        messages.error(request, 'No impersonation session found.')
        return redirect('admin:index')




