from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import KYCSubmission


class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=160)
    email = forms.EmailField()
    phone = forms.CharField(max_length=24)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    accepted_terms = forms.BooleanField()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        if cleaned.get("password") and len(cleaned["password"]) < 8:
            raise forms.ValidationError("Use at least 8 characters for your password.")
        return cleaned

    def save(self):
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split(" ", 1)
        user = User.objects.create_user(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else "",
        )
        user.profile.phone = self.cleaned_data["phone"]
        user.profile.accepted_terms = self.cleaned_data["accepted_terms"]
        user.profile.save()
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


class KYCSubmissionForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = KYCSubmission
        fields = ["full_name", "date_of_birth", "id_type", "id_number", "id_document", "selfie", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        id_type = cleaned.get("id_type")
        id_number = cleaned.get("id_number", "")
        if id_type in (KYCSubmission.IDType.BVN, KYCSubmission.IDType.NIN):
            if not (id_number.isdigit() and len(id_number) == 11):
                self.add_error("id_number", "BVN and NIN must be exactly 11 digits.")
        return cleaned
