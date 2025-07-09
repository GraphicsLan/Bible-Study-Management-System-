from django.contrib.auth.backends import ModelBackend
from .models import Member

class MemberAuthBackend(ModelBackend):
    def authenticate(self, request, member_id=None, password=None, **kwargs):
        try:
            member = Member.objects.get(member_id=member_id)
            if member.check_password(password):
                return member
        except Member.DoesNotExist:
            return None

    def get_user(self, member_id):
        try:
            return Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return None