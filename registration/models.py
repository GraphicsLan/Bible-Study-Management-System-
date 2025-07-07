from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True, null=True, default='unknown')
    email = models.EmailField(max_length=254, unique=True, blank=False, null=False, default='')
    user_id = models.IntegerField(default=0, unique=False, editable=True)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    year_of_study = models.CharField(max_length=10, null=True, blank=True)
    sessions_attended = models.IntegerField(null=True, blank=True)
    leader_before = models.BooleanField(null=True, blank=True)
    leader_now = models.BooleanField(null=True, blank=True)
    residency_type = models.CharField(max_length=20, choices=[('campus', 'Within Campus'), ('offCampus', 'Non-Resident')])
    hall = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    estate = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.username