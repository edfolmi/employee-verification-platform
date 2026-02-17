"""
Employee models for the verification platform.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Employee(models.Model):
    """
    Employee model to store employee information and facial recognition data.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the employee"
    )
    
    full_name = models.CharField(
        max_length=255,
        help_text="Employee's full name"
    )
    
    phone = models.CharField(
        max_length=20,
        help_text="Employee's phone number"
    )
    
    email = models.EmailField(
        help_text="Employee's email address"
    )
    
    employer_name = models.CharField(
        max_length=255,
        help_text="Name of the employer/company"
    )
    
    position = models.CharField(
        max_length=255,
        help_text="Employee's job position"
    )
    
    reputation_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Reputation score (0-10)"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the employee"
    )
    
    image = models.ImageField(
        upload_to='employee_photos/',
        help_text="Employee's photo for facial recognition"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the employee was added"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the employee was last updated"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['employer_name']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.employer_name}"
    
    def get_reputation_display(self):
        """Return reputation score with label."""
        if self.reputation_score >= 8.0:
            return "Excellent"
        elif self.reputation_score >= 6.0:
            return "Good"
        elif self.reputation_score >= 4.0:
            return "Average"
        else:
            return "Poor"
    
    def get_reputation_color(self):
        """Return Bootstrap color class based on reputation."""
        if self.reputation_score >= 8.0:
            return "success"
        elif self.reputation_score >= 6.0:
            return "info"
        elif self.reputation_score >= 4.0:
            return "warning"
        else:
            return "danger"
