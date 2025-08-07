from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    ozon_client_id = forms.CharField(
        label='Ozon Client ID',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ozon_api_key = forms.CharField(
        label='Ozon API Key',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['ozon_client_id', 'ozon_api_key']

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
