"""
Business logic services for resume analysis
Separates AI/ML processing from HTTP handling
"""

import logging
import spacy
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag

from .utils import clean_sentence, are_texts_identical

logger = logging.getLogger(__name__)

# Load spaCy model with sentencizer
nlp = spacy.load("en_core_web_sm")
if not nlp.has_pipe("sentencizer"):
    nlp.add_pipe("sentencizer")

# Load Sentence-BERT model (for similarity)
sbert_model = SentenceTransformer('output/job_bert')

# Load DistilBERT resume screening model (for classification)
distilbert_tokenizer = None
distilbert_model = None

try:
    logger.info("Loading DistilBERT resume screening model...")
    distilbert_tokenizer = AutoTokenizer.from_pretrained("Poojan11/resume-screening-distilbert")
    distilbert_model = AutoModelForSequenceClassification.from_pretrained("Poojan11/resume-screening-distilbert")
    distilbert_model.eval()  # Set to evaluation mode
    logger.info("DistilBERT model loaded successfully")
except Exception as e:
    logger.warning(f"Could not load DistilBERT model: {e}")


# Constants - moved from views to eliminate duplication
GENERIC_RESUME_WORDS = {
    'strong', 'excellent', 'good', 'great', 'proven', 'demonstrated', 'solid', 'effective', 'outstanding',
    'dynamic', 'motivated', 'dedicated', 'hardworking', 'reliable', 'responsible', 'skilled', 'experienced',
    'knowledge', 'ability', 'capable', 'team', 'player', 'leadership', 'communication', 'problem', 'solving',
    'results', 'oriented', 'self', 'passionate', 'driven', 'detail', 'focused', 'adaptable',
    'fast', 'quick', 'learning', 'learn', 'work', 'works', 'well', 'independently', 'collaborative', 'creative',
    'organized', 'organization', 'manage', 'managed', 'management', 'support', 'supporting', 'help', 'helped',
    'responsibility', 'responsibilities', 'objective', 'objectives', 'summary', 'summaries',
    'background', 'backgrounds', 'goal', 'goals', 'achieve', 'achieved', 'achievement', 'achievements',
    'success', 'successful', 'successfully', 'abilities', 'enthusiastic', 'enthusiasm', 'passion',
    'interest', 'interests', 'personal', 'professional', 'career', 'careers', 'growth', 'opportunity', 'opportunities',
    'motivating', 'motivation', 'initiative', 'initiatives',
}

TECH_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node', 'django', 'flask',
    'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
    'machine learning', 'data science', 'artificial intelligence', 'deep learning', 'nlp', 'pytorch', 'tensorflow',
    'linux', 'git', 'rest', 'api', 'graphql', 'cloud', 'devops', 'ci/cd', 'microservices', 'spark', 'hadoop',
    'etl', 'tableau', 'powerbi', 'excel', 'jira', 'scrum', 'kanban', 'agile', 'blockchain', 'cybersecurity',
    'big data', 'data engineering', 'data analysis', 'data visualization', 'statistics', 'matplotlib', 'seaborn',
    'opencv', 'computer vision', 'aws lambda', 'gcp', 'cloud functions', 'firebase', 'react native', 'flutter',
    'android', 'ios', 'swift', 'kotlin', 'c++', 'c#', 'php', 'ruby', 'perl', 'scala', 'go', 'rust', 'html', 'css',
    'sass', 'less', 'bootstrap', 'tailwind', 'redux', 'mobx', 'express', 'spring', 'laravel', 'dotnet', 'unity',
    'unreal', 'confluence', 'trello', 'asana', 'notion', 'figma', 'adobe', 'photoshop', 'illustrator',
    'xd', 'sketch', 'zeplin', 'salesforce', 'sap', 'oracle', 'erp', 'crm', 'r', 'sas', 'spacy', 'nltk', 'gensim',
]


def get_smart_sentences(text):
    """
    Split text into sentences using spaCy
    
    Args:
        text (str): Input text
        
    Returns:
        list: List of sentences
    """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]


def calculate_bidirectional_similarity(text1, text2):
    """
    Calculate bidirectional semantic similarity between two texts
    
    Args:
        text1 (str): First text (e.g., resume)
        text2 (str): Second text (e.g., job description)
        
    Returns:
        tuple: (score: float, sentences1: list, match_report: list)
    """
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

    embeddings1 = sbert_model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = sbert_model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # Resume → JD
    r2j_best = cosine_scores.max(dim=1).values
    r2j_score = r2j_best.mean().item()

    # JD → Resume
    j2r_best = cosine_scores.max(dim=0).values
    j2r_score = j2r_best.mean().item()

    # Final bidirectional score
    final_score = (r2j_score + j2r_score) / 2

    # Match report (from Resume → JD only)
    indices = cosine_scores.max(dim=1).indices
    match_report = []
    for i, score in enumerate(r2j_best):
        match_report.append({
            'resume_sentence': sentences1[i],
            'matched_jd_sentence': sentences2[indices[i]],
            'score': round(score.item() * 100, 2)
        })

    return round(final_score * 100, 2), sentences1, match_report


def calculate_distilbert_score(resume_text, jd_text):
    """
    Calculate resume-JD match score using DistilBERT classification model
    
    Args:
        resume_text (str): Resume text
        jd_text (str): Job description text
        
    Returns:
        float or None: Match score (0-100) or None if model unavailable
    """
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
            
            # Get the probability of positive match
            match_probability = probabilities[0][1].item() if probabilities.shape[1] > 1 else probabilities[0][0].item()
            
        return round(match_probability * 100, 2)
    except Exception as e:
        logger.error(f"Error in DistilBERT scoring: {e}")
        return None


def extract_matched_keywords(resume_text, jd_text, min_score=0.7):
    """
    Extract keywords that appear in both resume and JD with high semantic similarity
    
    Args:
        resume_text (str): Resume text
        jd_text (str): Job description text
        min_score (float): Minimum similarity score (unused, kept for API compatibility)
        
    Returns:
        list: List of matched keywords
    """
    try:
        # Ensure NLTK data is available
        try:
            stop_words = set(stopwords.words('english'))
        except:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            stop_words = set(stopwords.words('english'))

        # Combine stopwords with generic resume words
        all_stopwords = stop_words | GENERIC_RESUME_WORDS

        # Tokenize and POS tag
        resume_tokens = [w for w in word_tokenize(resume_text) if w.isalpha() and len(w) > 2]
        jd_tokens = [w for w in word_tokenize(jd_text) if w.isalpha() and len(w) > 2]
        resume_nouns = [w.lower() for w, pos in pos_tag(resume_tokens) if pos.startswith('NN') and w.lower() not in all_stopwords]
        jd_nouns = [w.lower() for w, pos in pos_tag(jd_tokens) if pos.startswith('NN') and w.lower() not in all_stopwords]

        # Find common nouns (skills/domains)
        common_nouns = set(resume_nouns) & set(jd_nouns)

        # Add domain-specific keywords if found
        for keyword in TECH_KEYWORDS:
            if keyword in resume_text.lower() and keyword in jd_text.lower():
                common_nouns.add(keyword)

        # Return sorted by length (longer first), up to 20 unique keywords
        return sorted(list(set(common_nouns)), key=lambda x: (-len(x), x))[:20]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []


def analyze_single_resume(resume_text, jd_text, resume_name="Resume"):
    """
    Analyze a single resume against a job description
    
    Args:
        resume_text (str): Resume text
        jd_text (str): Job description text
        resume_name (str): Name/identifier for the resume
        
    Returns:
        dict: Analysis results with scores and matched keywords
    """
    if len(resume_text.strip()) < 20:
        return None
    
    # Check if resume and JD are identical
    is_identical = are_texts_identical(resume_text, jd_text)
        
    # Get semantic similarity score (Sentence-BERT)
    sbert_score, _, match_report = calculate_bidirectional_similarity(resume_text, jd_text)
    
    # Get DistilBERT classification score (skip for identical docs)
    if is_identical:
        distilbert_score = 100.0
        final_score = 100.0
    else:
        distilbert_score = calculate_distilbert_score(resume_text, jd_text)
        
        # Combine scores (weighted average if both available)
        if distilbert_score is not None:
            # 60% Sentence-BERT (similarity) + 40% DistilBERT (classification)
            final_score = (sbert_score * 0.6) + (distilbert_score * 0.4)
        else:
            final_score = sbert_score
    
    # Extract matched keywords
    matched_keywords = extract_matched_keywords(resume_text, jd_text)
    
    return {
        'resume_name': resume_name,
        'score': round(final_score, 2),
        'sbert_score': sbert_score,
        'distilbert_score': distilbert_score,
        'matched_keywords': matched_keywords,
        'match_report': match_report[:5]  # Top 5 matches only
    }


def compare_multiple_resumes(resumes_data, jd_text):
    """
    Compare multiple resumes against a job description
    
    Args:
        resumes_data (list): List of tuples (resume_name, resume_text)
        jd_text (str): Job description text
        
    Returns:
        list: Sorted list of analysis results
    """
    results = []
    
    for resume_name, resume_text in resumes_data:
        result = analyze_single_resume(resume_text, jd_text, resume_name)
        if result:
            results.append(result)
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results
