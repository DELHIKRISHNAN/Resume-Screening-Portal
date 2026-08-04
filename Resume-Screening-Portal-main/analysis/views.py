"""
Views for resume analysis
HTTP handling only - business logic delegated to services
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
import logging

from .utils import (
    extract_text_from_file,
    clean_text,
    extract_relevant_text,
    sanitize_filename,
    validate_file
)
from .services import compare_multiple_resumes, compare_resumes_enhanced

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def upload_view(request):
    """Render single resume upload form (legacy)"""
    return render(request, 'analysis/upload.html')


@require_http_methods(["GET"])
def multi_upload_view(request):
    """Render multi-resume upload form"""
    return render(request, 'analysis/multi_upload.html')


@require_http_methods(["GET"])
def dashboard_view(request):
    """Render the modern dashboard UI"""
    return render(request, 'analysis/dashboard.html')


@require_http_methods(["POST"])
def multi_match_view(request):
    """
    Multi-resume match endpoint
    Compare multiple resumes against a job description
    """
    # Get job description file
    jd_file = request.FILES.get('jd')
    if not jd_file:
        return JsonResponse({'error': 'Job description file is required'}, status=400)
    
    # Validate JD file
    is_valid, message = validate_file(jd_file)
    if not is_valid:
        return JsonResponse({'error': f'Invalid JD file: {message}'}, status=400)
    
    # Collect and validate resume files
    resume_files = []
    for i in range(1, 6):  # resume1 to resume5
        resume_file = request.FILES.get(f'resume{i}')
        if resume_file:
            is_valid, message = validate_file(resume_file)
            if not is_valid:
                return JsonResponse({'error': f'Invalid resume file {i}: {message}'}, status=400)
            resume_files.append(resume_file)
    
    if not resume_files:
        return JsonResponse({'error': 'At least one resume file is required'}, status=400)
    
    # Process files
    jd_path = None
    resume_paths = []
    
    try:
        # Save and process JD with sanitized filename
        jd_safe_name = sanitize_filename(jd_file.name)
        jd_path = default_storage.save(f"jds/{jd_safe_name}", jd_file)
        jd_full_path = os.path.join("media", jd_path)
        
        jd_text_raw = extract_text_from_file(jd_full_path)
        jd_text = clean_text(extract_relevant_text(jd_text_raw))
        
        if len(jd_text) < 50:
            return JsonResponse({'error': 'Job description content is too short or unreadable'}, status=400)

        # Process resumes with sanitized filenames
        resumes_data = []
        for resume_file in resume_files:
            resume_safe_name = sanitize_filename(resume_file.name)
            resume_path = default_storage.save(f"resumes/{resume_safe_name}", resume_file)
            resume_paths.append(resume_path)
            
            resume_full_path = os.path.join("media", resume_path)
            resume_text_raw = extract_text_from_file(resume_full_path)
            resume_text = clean_text(extract_relevant_text(resume_text_raw))
            
            if len(resume_text) >= 50:
                resumes_data.append((resume_file.name, resume_text))
        
        if not resumes_data:
            return JsonResponse({'error': 'No valid resume content found'}, status=400)
        
        # Perform analysis using service layer
        results = compare_multiple_resumes(resumes_data, jd_text)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total_resumes': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)
        
    finally:
        # Clean up uploaded files
        try:
            if jd_path:
                default_storage.delete(jd_path)
            for resume_path in resume_paths:
                default_storage.delete(resume_path)
        except Exception as e:
            logger.warning(f"Error cleaning up files: {e}")


@csrf_exempt
@require_http_methods(["POST"])
def api_analyze_view(request):
    """
    Enhanced API endpoint for the modern dashboard UI.
    Returns rich analysis data including per-skill scores,
    skills gap, experience matching, and recommendations.
    """
    # Get job description file
    jd_file = request.FILES.get('jd')
    if not jd_file:
        return JsonResponse({'error': 'Job description file is required'}, status=400)
    
    # Validate JD file
    is_valid, message = validate_file(jd_file)
    if not is_valid:
        return JsonResponse({'error': f'Invalid JD file: {message}'}, status=400)
    
    # Collect and validate resume files
    resume_files = []
    for i in range(1, 6):
        resume_file = request.FILES.get(f'resume{i}')
        if resume_file:
            is_valid, message = validate_file(resume_file)
            if not is_valid:
                return JsonResponse({'error': f'Invalid resume file {i}: {message}'}, status=400)
            resume_files.append((i, resume_file))
    
    if not resume_files:
        return JsonResponse({'error': 'At least one resume file is required'}, status=400)
    
    # Process files
    jd_path = None
    resume_paths = []
    
    try:
        # Save and process JD
        jd_safe_name = sanitize_filename(jd_file.name)
        jd_path = default_storage.save(f"jds/{jd_safe_name}", jd_file)
        jd_full_path = os.path.join("media", jd_path)
        
        jd_text_raw = extract_text_from_file(jd_full_path)
        jd_text = clean_text(extract_relevant_text(jd_text_raw))
        
        if len(jd_text) < 50:
            return JsonResponse({'error': 'Job description content is too short or unreadable'}, status=400)

        # Process resumes
        resumes_data = []
        for idx, resume_file in resume_files:
            resume_safe_name = sanitize_filename(resume_file.name)
            resume_path = default_storage.save(f"resumes/{resume_safe_name}", resume_file)
            resume_paths.append(resume_path)
            
            resume_full_path = os.path.join("media", resume_path)
            resume_text_raw = extract_text_from_file(resume_full_path)
            resume_text = clean_text(extract_relevant_text(resume_text_raw))
            
            if len(resume_text) >= 50:
                resumes_data.append((resume_file.name, resume_text))
        
        if not resumes_data:
            return JsonResponse({'error': 'No valid resume content found'}, status=400)
        
        # Enhanced analysis
        analysis = compare_resumes_enhanced(resumes_data, jd_text)
        
        return JsonResponse(analysis)
        
    except Exception as e:
        logger.error(f"Error in enhanced analysis: {e}", exc_info=True)
        return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)
        
    finally:
        try:
            if jd_path:
                default_storage.delete(jd_path)
            for resume_path in resume_paths:
                default_storage.delete(resume_path)
        except Exception as e:
            logger.warning(f"Error cleaning up files: {e}")
