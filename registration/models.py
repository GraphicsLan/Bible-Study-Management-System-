from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class MemberManager(BaseUserManager):
    def create_user(self, email, member_id, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not member_id:
            raise ValueError('The Member ID must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, member_id=member_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, member_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, member_id, password, **extra_fields)

class Member(AbstractBaseUser, PermissionsMixin):
    member_id = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(1000), MaxValueValidator(9999)],
        help_text="4-digit unique member ID"
    )
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    year_of_study = models.CharField(max_length=10, null=True, blank=True)
    sessions_attended = models.IntegerField(default=0)
    leader_before = models.BooleanField(default=False)
    leader_now = models.BooleanField(default=False)
    residency_type = models.CharField(
        max_length=20, 
        choices=[('campus', 'Within Campus'), ('offCampus', 'Non-Resident')]
    )
    hall = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    estate = models.CharField(max_length=100, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MemberManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['member_id', 'phone']

    def __str__(self):
        return f"{self.get_full_name()} (ID: {self.member_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name
    
    

class BibleStudy(models.Model):
    title = models.CharField(max_length=200)
    book = models.CharField(max_length=100)
    total_sessions = models.PositiveIntegerField()
    current_session = models.PositiveIntegerField()
    meeting_day = models.CharField(max_length=20)
    meeting_time = models.CharField(max_length=50)
    meeting_venue = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.book} - {self.title}"
    
    class Meta:
        verbose_name_plural = "Bible Studies"

class WeeklyReflection(models.Model):
    bible_study = models.ForeignKey(BibleStudy, on_delete=models.CASCADE)
    week_number = models.PositiveIntegerField()
    scripture_reference = models.CharField(max_length=100)
    scripture_text = models.TextField()
    reflection_text = models.TextField()
    discussion_question = models.TextField(blank=True)
    date = models.DateField()
    
    def __str__(self):
        return f"Week {self.week_number}: {self.scripture_reference}"
    
    class Meta:
        ordering = ['-date'] 