from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import KYCSubmission

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "application/pdf"}
ALLOWED_SELFIE_TYPES = {"image/jpeg", "image/png"}


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
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="You must be at least 18 years old.",
    )

    class Meta:
        model = KYCSubmission
        fields = ["full_name", "date_of_birth", "id_type", "id_number", "id_document", "selfie", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "id_document": "JPG, PNG or PDF, up to 5MB. Make sure all four corners and text are visible.",
            "selfie": "Optional but speeds up review. A clear, well-lit photo of your face, JPG or PNG up to 5MB.",
        }

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"].strip()
        if len(full_name.split()) < 2:
            raise forms.ValidationError("Enter your full legal name as it appears on your ID document.")
        return full_name

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        if dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        age = (date.today() - dob).days // 365
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old to verify your identity.")
        return dob

    def clean_id_document(self):
        return self._validate_upload(self.cleaned_data["id_document"], ALLOWED_UPLOAD_TYPES)

    def clean_selfie(self):
        selfie = self.cleaned_data.get("selfie")
        if not selfie:
            return selfie
        return self._validate_upload(selfie, ALLOWED_SELFIE_TYPES)

    def _validate_upload(self, upload, allowed_types):
        if upload.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("File is too large. Please upload a file under 5MB.")
        if upload.content_type not in allowed_types:
            raise forms.ValidationError("Unsupported file type. Please upload a JPG, PNG, or PDF.")
        return upload

    def clean(self):
        cleaned = super().clean()
        id_type = cleaned.get("id_type")
        id_number = cleaned.get("id_number", "")
        if id_type in (KYCSubmission.IDType.BVN, KYCSubmission.IDType.NIN):
            if not (id_number.isdigit() and len(id_number) == 11):
                self.add_error("id_number", "BVN and NIN must be exactly 11 digits.")
        return cleaned
