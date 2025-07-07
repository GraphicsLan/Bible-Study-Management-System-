from django.shortcuts import render
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User
import random
from django.urls import reverse
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Email already registered.'})
            else:
                messages.error(request, 'Email already registered.')
                return render(request, 'registration/reg.html')

        # Generate random user ID
        user_id = 'EUNCCU' + str(random.randint(10000, 99999))
        
        # Create user
        user = User.objects.create_user(
            username=user_id,
            email=request.POST.get('email'),
            password=user_id,  # Using user ID as initial password
            phone=request.POST.get('phone'),
            gender=request.POST.get('gender'),
            year_of_study=request.POST.get('yearOfStudy'),
            sessions_attended=int(request.POST.get('sessionsAttended', 0)),
            leader_before=request.POST.get('leaderBefore') == 'yes',
            leader_now=request.POST.get('leaderNow') == 'yes',
            residency_type=request.POST.get('residencyType'),
            hall=request.POST.get('hall', ''),
            area=request.POST.get('area', ''),
            estate=request.POST.get('estate', '')
        )
        
        # Set first_name and last_name from fullName
        full_name = request.POST.get('fullName', '').split(' ', 1)
        user.first_name = full_name[0]
        if len(full_name) > 1:
            user.last_name = full_name[1]
        user.save()
        
        # Send email
        subject = 'Your EUNCCU Bible Study Login Details'
        html_message = render_to_string('registration/email_template.html', {
            'user': user,
            'user_id': user_id,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            None,  # Uses DEFAULT_FROM_EMAIL
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Return JSON response for modal
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'user_id': user_id,
                'email': user.email,
                'phone': user.phone,
                'loginUrl': reverse('login'),
            })
    
    return render(request, 'registration/reg.html')



def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('loginId')
        user_id = request.POST.get('userId')
        
        
        user = authenticate(
            request, 
            username=user_id,
            password=user_id  # Password is same as user ID 
        )
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'registration/login.html')



@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def mygroup_view(request):
    return render(request, 'dashboard/bs_group.html')

def discussion_view(request):
    return render(request, 'dashboard/discussion.html')

def biblestudy_view(request):
    return render(request, 'dashboard/biblestudies.html')
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('fullName', '').split(' ')[0]
        user.last_name = ' '.join(request.POST.get('fullName', '').split(' ')[1:])
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.id = request.POST.get('userId')
        user.save()
    return render(request, 'dashboard/profile.html')