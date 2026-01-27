from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
import fitz
from sentence_transformers import SentenceTransformer, util
import spacy
import re
import logging
from docx import Document
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Configure logging
logger = logging.getLogger(__name__)


# ✅ Load spaCy model with sentencizer
nlp = spacy.load("en_core_web_sm")
if not nlp.has_pipe("sentencizer"):
    nlp.add_pipe("sentencizer")


# ✅ Load Sentence-BERT model (for similarity)
model = SentenceTransformer('output/job_bert')

# ✅ Load DistilBERT resume screening model (for classification)
try:
    logger.info("Loading DistilBERT resume screening model...")
    distilbert_tokenizer = AutoTokenizer.from_pretrained("Poojan11/resume-screening-distilbert")
    distilbert_model = AutoModelForSequenceClassification.from_pretrained("Poojan11/resume-screening-distilbert")
    distilbert_model.eval()  # Set to evaluation mode
    logger.info("✓ DistilBERT model loaded successfully")
except Exception as e:
    logger.warning(f"Could not load DistilBERT model: {e}")
    distilbert_tokenizer = None
    distilbert_model = None


# ✅ Sentence splitter using spaCy
def get_smart_sentences(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]


# ✅ Clean each sentence for embedding
def clean_sentence(sentence):
    sentence = sentence.replace('\n', ' ').strip()
    sentence = re.sub(r'\s+', ' ', sentence)
    sentence = re.sub(r'[^\w\s.,;!?/-]', '', sentence)
    return sentence


# ✅ Check if two texts are identical or nearly identical
def are_texts_identical(text1, text2, threshold=0.95):
    """Check if two texts are identical based on character overlap"""
    # Normalize texts
    clean1 = re.sub(r'\s+', ' ', text1.lower().strip())
    clean2 = re.sub(r'\s+', ' ', text2.lower().strip())
    
    # Check exact match
    if clean1 == clean2:
        return True
    
    # Check character-level similarity
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, clean1, clean2).ratio()
    
    return similarity >= threshold


# ✅ NEW: Bidirectional semantic similarity
def get_avg_similarity_bidirectional(text1, text2):
    # Check if texts are identical first
    if are_texts_identical(text1, text2):
        logger.info("Identical documents detected - returning 100% match")
        sentences = [clean_sentence(s) for s in get_smart_sentences(text1)]
        perfect_report = [{
            'resume_sentence': sent,
            'matched_jd_sentence': sent,
            'score': 100.0
        } for sent in sentences[:5]]
        return 100.0, sentences, perfect_report
    
    sentences1 = [clean_sentence(s) for s in get_smart_sentences(text1)]
    sentences2 = [clean_sentence(s) for s in get_smart_sentences(text2)]

    if not sentences1 or not sentences2:
        return 0.0, [], []

    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # 🔁 Resume ➝ JD
    r2j_best = cosine_scores.max(dim=1).values
    r2j_score = r2j_best.mean().item()

    # 🔁 JD ➝ Resume
    j2r_best = cosine_scores.max(dim=0).values
    j2r_score = j2r_best.mean().item()

    # 🧠 Final bidirectional score
    final_score = (r2j_score + j2r_score) / 2

    # 🧾 Match report (from Resume ➝ JD only)
    indices = cosine_scores.max(dim=1).indices
    match_report = []
    for i, score in enumerate(r2j_best):
        match_report.append({
            'resume_sentence': sentences1[i],
            'matched_jd_sentence': sentences2[indices[i]],
            'score': round(score.item() * 100, 2)
        })

    return round(final_score * 100, 2), sentences1, match_report


# ✅ NEW: DistilBERT Resume-JD Match Score
def get_distilbert_score(resume_text, jd_text):
    """Get resume-JD match score using DistilBERT classification model"""
    if distilbert_model is None or distilbert_tokenizer is None:
        logger.warning("DistilBERT model not available, skipping...")
        return None
    
    try:
        # Combine resume and JD for classification
        combined_text = f"Resume: {resume_text[:500]} Job Description: {jd_text[:500]}"
        
        # Tokenize
        inputs = distilbert_tokenizer(
            combined_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Get predictions
        with torch.no_grad():
            outputs = distilbert_model(**inputs)
            logits = outputs.logits
            probabilities = F.softmax(logits, dim=-1)
            
            # Get the probability of positive match (adjust based on model's label mapping)
            # Assuming binary classification: 0=no match, 1=match
            match_probability = probabilities[0][1].item() if probabilities.shape[1] > 1 else probabilities[0][0].item()
            
        return round(match_probability * 100, 2)
    except Exception as e:
        logger.error(f"Error in DistilBERT scoring: {e}")
        return None


# ✅ Extract text from PDF, DOCX, image, txt
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            doc = fitz.open(file_path)
            return " ".join(page.get_text() for page in doc)
        elif ext == ".docx":
            doc = Document(file_path)
            return " ".join([paragraph.text for paragraph in doc.paragraphs])
        elif ext in [".jpg", ".png", ".jpeg"]:
            from PIL import Image
            import pytesseract
            return pytesseract.image_to_string(Image.open(file_path))
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
    return ""


# ✅ Basic cleanup
def clean_text(text):
    return text.replace('\n', ' ').strip()


# ✅ NEW: Extract matched keywords between resume and JD
def extract_matched_keywords(resume_text, jd_text, min_score=0.7):
    """Extract keywords that appear in both resume and JD with high semantic similarity"""
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        from nltk import pos_tag
        try:
            stop_words = set(stopwords.words('english'))
        except:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            stop_words = set(stopwords.words('english'))

        # Add custom resume/jd generic words and adjectives to filter
        generic_words = set([
            'strong', 'excellent', 'good', 'great', 'proven', 'demonstrated', 'solid', 'effective', 'outstanding',
            'dynamic', 'motivated', 'dedicated', 'hardworking', 'reliable', 'responsible', 'skilled', 'experienced',
            'knowledge', 'ability', 'capable', 'team', 'player', 'leadership', 'communication', 'problem', 'solving',
            'results', 'oriented', 'self', 'motivated', 'passionate', 'driven', 'detail', 'focused', 'adaptable',
            'fast', 'quick', 'learning', 'learn', 'work', 'works', 'well', 'independently', 'collaborative', 'creative',
            'organized', 'organization', 'manage', 'managed', 'management', 'support', 'supporting', 'help', 'helped',
            'responsible', 'responsibility', 'responsibilities', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives', 'objective', 'objectives', 'summary', 'summaries',
            'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
            'success', 'successful', 'successfully', 'ability', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
            'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
            'motivating', 'motivation', 'initiative', 'initiatives',
        ])
        all_stopwords = stop_words | generic_words

        # Tokenize and POS tag
        resume_tokens = [w for w in word_tokenize(resume_text) if w.isalpha() and len(w) > 2]
        jd_tokens = [w for w in word_tokenize(jd_text) if w.isalpha() and len(w) > 2]
        resume_nouns = [w.lower() for w, pos in pos_tag(resume_tokens) if pos.startswith('NN') and w.lower() not in all_stopwords]
        jd_nouns = [w.lower() for w, pos in pos_tag(jd_tokens) if pos.startswith('NN') and w.lower() not in all_stopwords]

        # Find common nouns (skills/domains)
        common_nouns = set(resume_nouns) & set(jd_nouns)

        # Add some domain-specific keywords if found
        tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node', 'django', 'flask',
            'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
            'machine learning', 'data science', 'artificial intelligence', 'deep learning', 'nlp', 'pytorch', 'tensorflow',
            'linux', 'git', 'rest', 'api', 'graphql', 'cloud', 'devops', 'ci/cd', 'microservices', 'spark', 'hadoop',
            'etl', 'tableau', 'powerbi', 'excel', 'jira', 'scrum', 'kanban', 'agile', 'blockchain', 'cybersecurity',
            'big data', 'data engineering', 'data analysis', 'data visualization', 'statistics', 'matplotlib', 'seaborn',
            'opencv', 'computer vision', 'aws lambda', 'gcp', 'cloud functions', 'firebase', 'react native', 'flutter',
            'android', 'ios', 'swift', 'kotlin', 'c++', 'c#', 'php', 'ruby', 'perl', 'scala', 'go', 'rust', 'html', 'css',
            'sass', 'less', 'bootstrap', 'tailwind', 'redux', 'mobx', 'express', 'spring', 'laravel', 'dotnet', 'unity',
            'unreal', 'jira', 'confluence', 'trello', 'asana', 'notion', 'figma', 'adobe', 'photoshop', 'illustrator',
            'xd', 'sketch', 'zeplin', 'salesforce', 'sap', 'oracle', 'erp', 'crm', 'r', 'sas', 'spacy', 'nltk', 'gensim',
        ]
        for keyword in tech_keywords:
            if keyword in resume_text.lower() and keyword in jd_text.lower():
                common_nouns.add(keyword)

        # Return sorted by length (longer first), up to 20 unique keywords
        return sorted(list(set(common_nouns)), key=lambda x: (-len(x), x))[:20]
    except Exception as e:
        # Fallback: return empty list if error
        return []


# ✅ NEW: Multi-resume comparison function
def compare_multiple_resumes(resumes_data, jd_text):
    """Compare multiple resumes against a job description"""
    results = []
    
    for resume_name, resume_text in resumes_data:
        if len(resume_text.strip()) < 20:
            continue
        
        # Check if resume and JD are identical
        is_identical = are_texts_identical(resume_text, jd_text)
            
        # Get semantic similarity score (Sentence-BERT)
        sbert_score, _, match_report = get_avg_similarity_bidirectional(resume_text, jd_text)
        
        # Get DistilBERT classification score (skip for identical docs)
        if is_identical:
            distilbert_score = 100.0  # Perfect match
            final_score = 100.0
        else:
            distilbert_score = get_distilbert_score(resume_text, jd_text)
            
            # Combine scores (weighted average if both available)
            if distilbert_score is not None:
                # 60% Sentence-BERT (similarity) + 40% DistilBERT (classification)
                final_score = (sbert_score * 0.6) + (distilbert_score * 0.4)
            else:
                final_score = sbert_score
        
        # Extract matched keywords
        matched_keywords = extract_matched_keywords(resume_text, jd_text)
        
        results.append({
            'resume_name': resume_name,
            'score': round(final_score, 2),
            'sbert_score': sbert_score,
            'distilbert_score': distilbert_score,
            'matched_keywords': matched_keywords,
            'match_report': match_report[:5]  # Top 5 matches only
        })
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


# ✅ Validate uploaded file
def validate_file(file):
    """Validate file size and type"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']
    
    if file.size > MAX_FILE_SIZE:
        return False, "File size exceeds 10MB limit"
    
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, "Valid"


# ✅ Extract only job-relevant lines (skills, projects, etc.)
def extract_relevant_text(text):
    keywords = ['skills', 'projects', 'experience', 'responsibilities', 'requirements']
    lines = text.splitlines()
    relevant = [line for line in lines if any(k in line.lower() for k in keywords) or len(line.split()) > 5]
    filtered = " ".join(relevant)
    return filtered if len(filtered.split()) >= 50 else text


# ✅ Upload form view (original single resume)
def upload_view(request):
    return render(request, 'analysis/upload.html')


# ✅ Upload form view for multi-resume
def multi_upload_view(request):
    return render(request, 'analysis/multi_upload.html')


# ✅ NEW: Multi-resume match endpoint
@csrf_exempt
def multi_match_view(request):
    if request.method == 'POST':
        jd_file = request.FILES.get('jd')
        
        if not jd_file:
            return JsonResponse({'error': 'Job description file is required'}, status=400)
        
        # Validate JD file
        is_valid, message = validate_file(jd_file)
        if not is_valid:
            return JsonResponse({'error': f'Invalid JD file: {message}'}, status=400)
        
        # Collect resume files
        resume_files = []
        for i in range(1, 6):  # resume1 to resume5
            resume_file = request.FILES.get(f'resume{i}')
            if resume_file:
                # Validate each resume file
                is_valid, message = validate_file(resume_file)
                if not is_valid:
                    return JsonResponse({'error': f'Invalid resume file {i}: {message}'}, status=400)
                resume_files.append(resume_file)
        
        if not resume_files:
            return JsonResponse({'error': 'At least one resume file is required'}, status=400)
        
        try:
            # Save and process JD
            jd_path = default_storage.save(f"jds/{jd_file.name}", jd_file)
            jd_text_raw = extract_text(os.path.join("media", jd_path))
            jd_text = clean_text(extract_relevant_text(jd_text_raw))
            
            if len(jd_text) < 50:
                return JsonResponse({'error': 'Job description content is too short or unreadable'}, status=400)

            # Process resumes
            resumes_data = []
            resume_paths = []
            for resume_file in resume_files:
                resume_path = default_storage.save(f"resumes/{resume_file.name}", resume_file)
                resume_paths.append(resume_path)
                resume_text_raw = extract_text(os.path.join("media", resume_path))
                resume_text = clean_text(extract_relevant_text(resume_text_raw))
                if len(resume_text) >= 50:
                    resumes_data.append((resume_file.name, resume_text))
            if not resumes_data:
                return JsonResponse({'error': 'No valid resume content found'}, status=400)
            # Compare all resumes
            results = compare_multiple_resumes(resumes_data, jd_text)
            # Clean up uploaded files
            default_storage.delete(jd_path)
            for resume_path in resume_paths:
                default_storage.delete(resume_path)
            return JsonResponse({
                'success': True,
                'results': results,
                'total_resumes': len(results)
            })
        except Exception as e:
            try:
                default_storage.delete(jd_path)
                for resume_path in resume_paths:
                    default_storage.delete(resume_path)
            except:
                pass
            return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
