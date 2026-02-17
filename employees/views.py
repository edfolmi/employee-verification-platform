"""
Views for employee management and facial verification.
"""
import os
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Employee
from .forms import EmployeeForm, VerificationForm
from .services import FaceService, FaceRecognitionError, ChromaService

logger = logging.getLogger(__name__)


def home(request):
    """
    Home page with navigation to add or verify employees.
    """
    stats = ChromaService.get_collection_stats()
    employee_count = Employee.objects.count()
    
    context = {
        'employee_count': employee_count,
        'chroma_stats': stats
    }
    
    return render(request, 'home.html', context)


def add_employee(request):
    """
    View for adding a new employee with facial recognition.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Save the employee instance
                employee = form.save()
                
                # Get the full path to the uploaded image
                image_path = employee.image.path
                
                # Extract facial embedding
                logger.info(f"Processing face for employee: {employee.full_name}")
                embedding = FaceService.extract_embedding(image_path)
                
                # Prepare metadata for ChromaDB
                metadata = {
                    'full_name': employee.full_name,
                    'employer': employee.employer_name,
                    'reputation_score': float(employee.reputation_score)
                }
                
                # Store embedding in ChromaDB
                embedding_list = FaceService.embedding_to_list(embedding)
                success = ChromaService.add_employee_embedding(
                    employee_uuid=str(employee.uuid),
                    embedding=embedding_list,
                    metadata=metadata
                )
                
                if success:
                    messages.success(
                        request,
                        f'Employee "{employee.full_name}" added successfully with facial recognition data.'
                    )
                    return redirect('home')
                else:
                    # If ChromaDB storage fails, delete the employee
                    employee.delete()
                    messages.error(
                        request,
                        'Failed to store facial recognition data. Please try again.'
                    )
                    
            except FaceRecognitionError as e:
                # If face extraction fails, delete the employee
                if 'employee' in locals():
                    employee.delete()
                messages.error(request, str(e))
                
            except Exception as e:
                # Catch any other errors
                if 'employee' in locals():
                    employee.delete()
                logger.error(f"Error adding employee: {str(e)}")
                messages.error(
                    request,
                    f'An unexpected error occurred: {str(e)}'
                )
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'Add New Employee'
    }
    
    return render(request, 'add_employee.html', context)


def verify_employee(request):
    """
    View for verifying an employee using facial recognition.
    """
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Get the uploaded image
                uploaded_image = request.FILES['image']
                
                # Save temporarily to process
                temp_path = default_storage.save(
                    f'temp/{uploaded_image.name}',
                    ContentFile(uploaded_image.read())
                )
                full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)
                
                try:
                    # Extract embedding from verification image
                    logger.info("Extracting embedding from verification image")
                    query_embedding = FaceService.extract_embedding(full_temp_path)
                    
                    # Search in ChromaDB
                    embedding_list = FaceService.embedding_to_list(query_embedding)
                    match_result = ChromaService.search_embedding(embedding_list)
                    
                    # Clean up temporary file
                    default_storage.delete(temp_path)
                    
                    if match_result:
                        similarity = match_result['similarity']
                        threshold = settings.SIMILARITY_THRESHOLD
                        
                        logger.info(
                            f"Match found with similarity: {similarity:.4f}, "
                            f"Threshold: {threshold}"
                        )
                        
                        if similarity >= threshold:
                            # Match found - retrieve employee from database
                            try:
                                employee = Employee.objects.get(uuid=match_result['id'])
                                
                                context = {
                                    'match_found': True,
                                    'employee': employee,
                                    'similarity': similarity,
                                    'similarity_percentage': similarity * 100,
                                    'threshold': threshold,
                                    'confidence': 'High' if similarity >= 0.8 else 'Medium'
                                }
                                
                                return render(request, 'result.html', context)
                                
                            except Employee.DoesNotExist:
                                logger.error(f"Employee not found in database: {match_result['id']}")
                                messages.error(
                                    request,
                                    'Match found in facial database but employee record not found.'
                                )
                        else:
                            # Similarity below threshold
                            context = {
                                'match_found': False,
                                'similarity': similarity,
                                'similarity_percentage': similarity * 100,
                                'threshold': threshold,
                                'message': f'No confident match found. Closest match: {similarity*100:.1f}% (threshold: {threshold*100:.1f}%)'
                            }
                            
                            return render(request, 'result.html', context)
                    else:
                        # No match found in database
                        context = {
                            'match_found': False,
                            'message': 'No matching employee found in the database.'
                        }
                        
                        return render(request, 'result.html', context)
                
                finally:
                    # Ensure temp file is deleted even if error occurs
                    if default_storage.exists(temp_path):
                        default_storage.delete(temp_path)
                        
            except FaceRecognitionError as e:
                messages.error(request, str(e))
                
            except Exception as e:
                logger.error(f"Error during verification: {str(e)}")
                messages.error(
                    request,
                    f'An error occurred during verification: {str(e)}'
                )
    else:
        form = VerificationForm()
    
    context = {
        'form': form,
        'title': 'Verify Employee'
    }
    
    return render(request, 'verify_employee.html', context)


def employee_list(request):
    """
    View to list all employees.
    """
    employees = Employee.objects.all()
    
    context = {
        'employees': employees,
        'title': 'Employee List'
    }
    
    return render(request, 'employee_list.html', context)
