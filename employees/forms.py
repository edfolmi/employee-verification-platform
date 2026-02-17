"""
Forms for employee management and verification.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Employee


class EmployeeForm(forms.ModelForm):
    """
    Form for adding new employees with facial recognition data.
    """
    
    class Meta:
        model = Employee
        fields = [
            'full_name',
            'phone',
            'email',
            'employer_name',
            'position',
            'reputation_score',
            'notes',
            'image'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'employee@example.com'
            }),
            'employer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job position'
            }),
            'reputation_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.0 - 10.0',
                'step': '0.1',
                'min': '0',
                'max': '10'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes (optional)',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_image(self):
        """
        Validate the uploaded image.
        """
        image = self.cleaned_data.get('image')
        
        if not image:
            raise ValidationError("Please upload an employee photo.")
        
        # Check file size
        if image.size > settings.MAX_UPLOAD_SIZE:
            max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise ValidationError(
                f"Image file is too large. Maximum size is {max_size_mb}MB."
            )
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image.content_type not in allowed_types:
            raise ValidationError(
                "Invalid image format. Please upload JPEG, PNG, or WebP."
            )
        
        return image


class VerificationForm(forms.Form):
    """
    Form for uploading a photo for employee verification.
    """
    
    image = forms.ImageField(
        label='Upload Photo',
        help_text='Upload a clear face photo for verification',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean_image(self):
        """
        Validate the uploaded verification image.
        """
        image = self.cleaned_data.get('image')
        
        if not image:
            raise ValidationError("Please upload a photo for verification.")
        
        # Check file size
        if image.size > settings.MAX_UPLOAD_SIZE:
            max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise ValidationError(
                f"Image file is too large. Maximum size is {max_size_mb}MB."
            )
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image.content_type not in allowed_types:
            raise ValidationError(
                "Invalid image format. Please upload JPEG, PNG, or WebP."
            )
        
        return image
