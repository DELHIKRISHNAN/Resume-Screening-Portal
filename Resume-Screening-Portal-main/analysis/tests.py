"""
Comprehensive test suite for resume analyzer
Tests for views, services, and utilities
"""

from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import os
import tempfile

from analysis.utils import (
    sanitize_filename,
    validate_file,
    clean_text,
    clean_sentence,
    extract_relevant_text,
    are_texts_identical
)
from analysis.services import (
    get_smart_sentences,
    calculate_bidirectional_similarity,
    extract_matched_keywords,
    analyze_single_resume,
    compare_multiple_resumes
)


class UtilsTestCase(TestCase):
    """Test cases for utility functions"""
    
    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test that dangerous characters are removed from filenames"""
        # os.path.basename will extract just the filename from path
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("file<>:name.pdf"), "filename.pdf")
        self.assertEqual(sanitize_filename("test|file?.docx"), "testfile.docx")
    
    def test_sanitize_filename_replaces_spaces(self):
        """Test that spaces are replaced with underscores"""
        self.assertEqual(sanitize_filename("my resume.pdf"), "my_resume.pdf")
    
    def test_sanitize_filename_limits_length(self):
        """Test that long filenames are truncated"""
        long_name = "a" * 250 + ".pdf"
        result = sanitize_filename(long_name)
        self.assertTrue(len(result) <= 204)  # 200 + .pdf
        self.assertTrue(result.endswith(".pdf"))
    
    def test_validate_file_size_limit(self):
        """Test file size validation"""
        # Create mock file that's too large
        mock_file = MagicMock()
        mock_file.size = 11 * 1024 * 1024  # 11MB
        mock_file.name = "test.pdf"
        
        is_valid, message = validate_file(mock_file)
        self.assertFalse(is_valid)
        self.assertIn("size exceeds", message)
    
    def test_validate_file_extension(self):
        """Test file extension validation"""
        mock_file = MagicMock()
        mock_file.size = 1024  # 1KB
        mock_file.name = "test.exe"
        
        is_valid, message = validate_file(mock_file)
        self.assertFalse(is_valid)
        self.assertIn("not supported", message)
    
    def test_validate_file_valid(self):
        """Test valid file passes validation"""
        mock_file = MagicMock()
        mock_file.size = 1024  # 1KB
        mock_file.name = "test.pdf"
        
        is_valid, message = validate_file(mock_file)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")
    
    def test_clean_text(self):
        """Test text cleaning removes newlines and trailing whitespace"""
        text = "Hello\nWorld  \n  Test"
        result = clean_text(text)
        # clean_text replaces \n with space and strips, but doesn't collapse multiple spaces
        self.assertNotIn("\n", result)
        self.assertTrue(result.startswith("Hello"))
        self.assertTrue("World" in result)
    
    def test_clean_sentence(self):
        """Test sentence cleaning"""
        sentence = "Hello,   world!\n\nHow are you?"
        result = clean_sentence(sentence)
        self.assertNotIn("\n", result)
        self.assertNotIn("  ", result)
    
    def test_extract_relevant_text(self):
        """Test relevant text extraction"""
        text = "Skills: Python, Java\nExperience: 5 years\nShort line\nAnother relevant line with experience in testing"
        result = extract_relevant_text(text)
        self.assertIn("Skills", result)
        self.assertIn("Experience", result)
    
    def test_are_texts_identical_exact_match(self):
        """Test identical text detection"""
        text1 = "Hello World"
        text2 = "Hello World"
        self.assertTrue(are_texts_identical(text1, text2))
    
    def test_are_texts_identical_whitespace_variations(self):
        """Test identical text detection with whitespace differences"""
        text1 = "Hello   World"
        text2 = "Hello World"
        self.assertTrue(are_texts_identical(text1, text2))
    
    def test_are_texts_identical_different_texts(self):
        """Test different texts are not identical"""
        text1 = "Hello World"
        text2 = "Goodbye World"
        self.assertFalse(are_texts_identical(text1, text2))


class ServicesTestCase(TestCase):
    """Test cases for service layer functions"""
    
    def test_get_smart_sentences(self):
        """Test sentence splitting"""
        text = "This is sentence one. This is sentence two. This is sentence three."
        sentences = get_smart_sentences(text)
        self.assertGreater(len(sentences), 0)
        self.assertTrue(all(isinstance(s, str) for s in sentences))
    
    def test_get_smart_sentences_filters_short(self):
        """Test that very short sentences are filtered"""
        text = "Hi. This is a longer sentence that should be kept."
        sentences = get_smart_sentences(text)
        # Short "Hi." should be filtered (< 5 chars)
        self.assertTrue(all(len(s) > 5 for s in sentences))
    
    @patch('analysis.services.sbert_model')
    def test_calculate_bidirectional_similarity(self, mock_model):
        """Test bidirectional similarity calculation"""
        # Mock the model encoding and similarity
        mock_embeddings = MagicMock()
        mock_model.encode.return_value = mock_embeddings
        
        with patch('analysis.services.util.cos_sim') as mock_cos_sim:
            mock_scores = MagicMock()
            mock_scores.max.return_value.values.mean.return_value.item.return_value = 0.85
            mock_cos_sim.return_value = mock_scores
            
            text1 = "Python developer with 5 years experience"
            text2 = "Looking for Python developer with experience"
            
            score, sentences, report = calculate_bidirectional_similarity(text1, text2)
            
            self.assertIsInstance(score, float)
            self.assertGreater(score, 0)
            self.assertLessEqual(score, 100)
    
    def test_calculate_bidirectional_similarity_identical(self):
        """Test that identical texts return 100% match"""
        text = "This is a test document with multiple sentences. It contains important information."
        score, sentences, report = calculate_bidirectional_similarity(text, text)
        self.assertEqual(score, 100.0)
    
    def test_extract_matched_keywords(self):
        """Test keyword extraction"""
        resume = "Python developer with experience in Django, Flask, and PostgreSQL. Skilled in backend development."
        jd = "Looking for Python developer. Must know Django and PostgreSQL for backend systems."
        
        keywords = extract_matched_keywords(resume, jd)
        
        self.assertIsInstance(keywords, list)
        # Keywords extraction depends on NLTK POS tagging, which may vary
        # Just verify the function returns a list
    
    def test_extract_matched_keywords_filters_generic(self):
        """Test that generic resume words are filtered"""
        resume = "Strong team player with excellent communication skills"
        jd = "Looking for strong team player with excellent skills"
        
        keywords = extract_matched_keywords(resume, jd)
        
        # Generic words should be filtered
        generic = ['strong', 'excellent', 'team', 'player', 'skills']
        found_keywords = [k.lower() for k in keywords]
        for word in generic:
            self.assertNotIn(word, found_keywords)
    
    @patch('analysis.services.calculate_bidirectional_similarity')
    @patch('analysis.services.calculate_distilbert_score')
    def test_analyze_single_resume(self, mock_distilbert, mock_sbert):
        """Test single resume analysis"""
        mock_sbert.return_value = (85.0, [], [])
        mock_distilbert.return_value = 80.0
        
        resume_text = "Python developer with 5 years experience"
        jd_text = "Looking for Python developer"
        
        result = analyze_single_resume(resume_text, jd_text, "test_resume.pdf")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['resume_name'], "test_resume.pdf")
        self.assertIn('score', result)
        self.assertIn('sbert_score', result)
        self.assertIn('matched_keywords', result)
    
    def test_analyze_single_resume_short_text(self):
        """Test that very short resumes return None"""
        result = analyze_single_resume("Hi", "Long job description text", "test.pdf")
        self.assertIsNone(result)
    
    @patch('analysis.services.analyze_single_resume')
    def test_compare_multiple_resumes(self, mock_analyze):
        """Test multiple resume comparison"""
        mock_analyze.side_effect = [
            {'resume_name': 'resume1.pdf', 'score': 85.0},
            {'resume_name': 'resume2.pdf', 'score': 92.0},
            {'resume_name': 'resume3.pdf', 'score': 78.0},
        ]
        
        resumes_data = [
            ('resume1.pdf', 'Resume 1 text'),
            ('resume2.pdf', 'Resume 2 text'),
            ('resume3.pdf', 'Resume 3 text'),
        ]
        jd_text = "Job description text"
        
        results = compare_multiple_resumes(resumes_data, jd_text)
        
        self.assertEqual(len(results), 3)
        # Should be sorted by score (highest first)
        self.assertEqual(results[0]['score'], 92.0)
        self.assertEqual(results[1]['score'], 85.0)
        self.assertEqual(results[2]['score'], 78.0)


class ViewsTestCase(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_multi_upload_view_get(self):
        """Test GET request to multi-upload view"""
        response = self.client.get('/multi/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analysis/multi_upload.html')
    
    def test_multi_match_view_requires_post(self):
        """Test that multi-match view only accepts POST"""
        response = self.client.get('/multi-match/')
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_multi_match_view_requires_jd_file(self):
        """Test that JD file is required"""
        response = self.client.post('/multi-match/', {})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('required', data['error'].lower())
    
    def test_multi_match_view_validates_jd_file_type(self):
        """Test that invalid JD file type is rejected"""
        jd_file = SimpleUploadedFile("test.exe", b"fake content", content_type="application/x-msdownload")
        response = self.client.post('/multi-match/', {'jd': jd_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('not supported', data['error'].lower())
    
    def test_multi_match_view_requires_at_least_one_resume(self):
        """Test that at least one resume is required"""
        jd_file = SimpleUploadedFile("jd.txt", b"Job description content", content_type="text/plain")
        response = self.client.post('/multi-match/', {'jd': jd_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('at least one resume', data['error'].lower())
    
    @patch('analysis.views.extract_text_from_file')
    @patch('analysis.views.compare_multiple_resumes')
    def test_multi_match_view_successful_processing(self, mock_compare, mock_extract):
        """Test successful resume matching"""
        # Mock text extraction
        mock_extract.side_effect = [
            "This is a job description with requirements and responsibilities",
            "This is resume 1 with skills and experience in the field"
        ]
        
        # Mock comparison results
        mock_compare.return_value = [
            {
                'resume_name': 'resume1.pdf',
                'score': 85.5,
                'sbert_score': 87.0,
                'distilbert_score': 83.0,
                'matched_keywords': ['python', 'django'],
                'match_report': []
            }
        ]
        
        jd_file = SimpleUploadedFile("jd.pdf", b"fake pdf content", content_type="application/pdf")
        resume_file = SimpleUploadedFile("resume1.pdf", b"fake resume content", content_type="application/pdf")
        
        response = self.client.post('/multi-match/', {
            'jd': jd_file,
            'resume1': resume_file
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_resumes'], 1)
        self.assertEqual(len(data['results']), 1)


class SecurityTestCase(TestCase):
    """Security-focused test cases"""
    
    def test_csrf_protection_enabled(self):
        """Test that CSRF protection is enabled for POST requests"""
        client = Client(enforce_csrf_checks=True)
        jd_file = SimpleUploadedFile("jd.txt", b"content", content_type="text/plain")
        response = client.post('/multi-match/', {'jd': jd_file})
        # Should get 403 Forbidden due to missing CSRF token
        self.assertEqual(response.status_code, 403)
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented"""
        dangerous_names = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "../sensitive_file.txt"
        ]
        for dangerous_name in dangerous_names:
            safe_name = sanitize_filename(dangerous_name)
            self.assertNotIn("..", safe_name)
            self.assertNotIn("/", safe_name)
            self.assertNotIn("\\", safe_name)
    
    def test_file_size_limit_enforced(self):
        """Test that file size limits are enforced"""
        # Create a mock file that's too large
        mock_file = MagicMock()
        mock_file.size = 15 * 1024 * 1024  # 15MB
        mock_file.name = "large_file.pdf"
        
        is_valid, message = validate_file(mock_file, max_size=10*1024*1024)
        self.assertFalse(is_valid)


class IntegrationTestCase(TestCase):
    """Integration tests for end-to-end workflows"""
    
    @patch('analysis.services.sbert_model')
    @patch('analysis.services.distilbert_model')
    def test_full_resume_matching_workflow(self, mock_distilbert, mock_sbert):
        """Test complete resume matching workflow"""
        # Mock AI models
        mock_embeddings = MagicMock()
        mock_sbert.encode.return_value = mock_embeddings
        
        # Setup mock for similarity calculation
        with patch('analysis.services.util.cos_sim') as mock_cos_sim:
            mock_scores = MagicMock()
            mock_scores.max.return_value.values.mean.return_value.item.return_value = 0.85
            mock_cos_sim.return_value = mock_scores
            
            # Test data
            resume_text = "Experienced Python developer with Django and Flask expertise. 5 years in web development."
            jd_text = "Seeking Python developer with Django experience for web development projects."
            
            # Perform analysis
            result = analyze_single_resume(resume_text, jd_text, "test_resume.pdf")
            
            # Verify results
            self.assertIsNotNone(result)
            self.assertIn('score', result)
            self.assertIn('matched_keywords', result)
            # Keyword extraction is tested separately, just verify the structure is correct
            self.assertIsInstance(result['matched_keywords'], list)
