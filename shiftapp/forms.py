from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Members


class MembersCreationForm(UserCreationForm):
    class Meta:
        model = Members
        fields = ("email", "username", "first_name", "last_name", "mobile", "position_type", "part_time_rate", "is_staff")


class MembersChangeForm(UserChangeForm):
    class Meta:
        model = Members
        fields = "__all__"