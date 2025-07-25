from django import forms
from .models import UserProfile, SignalData

class RegisterForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'email', 'phone', 'password', 'dob', 'state']
        widgets = {
            'password': forms.PasswordInput(),
            'dob': forms.DateInput(attrs={'type': 'date'})
        }

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class SignalUploadForm(forms.ModelForm):
    class Meta:
        model = SignalData
        fields = ['csv_file']
