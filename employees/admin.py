"""
Admin configuration for employees app.
"""
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin interface for Employee model.
    """
    list_display = [
        'full_name',
        'employer_name',
        'position',
        'reputation_score',
        'email',
        'created_at'
    ]
    
    list_filter = [
        'employer_name',
        'reputation_score',
        'created_at'
    ]
    
    search_fields = [
        'full_name',
        'email',
        'employer_name',
        'position'
    ]
    
    readonly_fields = [
        'uuid',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('uuid', 'full_name', 'phone', 'email', 'image')
        }),
        ('Employment Details', {
            'fields': ('employer_name', 'position', 'reputation_score', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
