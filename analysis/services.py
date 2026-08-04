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
import os
try:
    if os.path.exists('output/job_bert'):
        sbert_model = SentenceTransformer('output/job_bert')
        logger.info("Loaded local fine-tuned Sentence-BERT model (output/job_bert).")
    else:
        logger.info("Local model 'output/job_bert' not found. Loading pre-trained 'all-mpnet-base-v2'...")
        sbert_model = SentenceTransformer('all-mpnet-base-v2')
except Exception as e:
    logger.warning(f"Error loading local model, falling back to pre-trained: {e}")
    sbert_model = SentenceTransformer('all-mpnet-base-v2')

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


# ============================================================
# Enhanced Analysis Functions for Dashboard UI
# ============================================================

def extract_job_role(jd_text):
    """
    Extract job role/title from job description text.
    Looks at the first few lines for common title patterns.
    """
    import re
    lines = jd_text.strip().split('\n')
    
    # Try explicit patterns first
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        for pattern in ['job title:', 'position:', 'role:', 'title:', 'job role:']:
            if lower.startswith(pattern):
                role = line.split(':', 1)[1].strip()
                if role:
                    return role
    
    # Fallback: first short, meaningful line is likely the title
    for line in lines[:5]:
        line = line.strip()
        if 3 < len(line) < 80 and len(line.split()) <= 10:
            # Skip lines that look like meta text
            skip = ['about', 'company', 'overview', 'description', 'summary', 'we are']
            if not any(s in line.lower() for s in skip):
                return line
    
    return "Job Position"


def extract_experience_years(text):
    """
    Extract experience requirement from text using regex patterns.
    """
    import re
    text_lower = text.lower()
    
    patterns = [
        r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:\+)?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?',
        r'minimum\s*(?:of)?\s*(\d+)\s*(?:years?|yrs?)',
        r'at\s*least\s*(\d+)\s*(?:years?|yrs?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2 and groups[1]:
                return f"{groups[0]}-{groups[1]} Years"
            return f"{groups[0]}+ Years"
    
    return "Not Specified"


def get_jd_tech_skills(jd_text):
    """
    Extract all tech/domain skills mentioned in the job description.
    Uses the TECH_KEYWORDS list and NLP noun extraction.
    """
    jd_lower = jd_text.lower()
    found_skills = []
    
    for keyword in TECH_KEYWORDS:
        if keyword in jd_lower:
            found_skills.append(keyword)
    
    # Also extract capitalized multi-word terms that look like skills
    try:
        tokens = word_tokenize(jd_text)
        tagged = pos_tag(tokens)
        
        stop_words = set(stopwords.words('english')) | GENERIC_RESUME_WORDS
        nouns = [w for w, pos in tagged
                 if pos.startswith('NN') and len(w) > 2
                 and w.lower() not in stop_words
                 and w[0].isupper()]
        
        for noun in nouns:
            if noun.lower() not in [s.lower() for s in found_skills]:
                found_skills.append(noun)
    except Exception:
        pass
    
    # Deduplicate preserving order and capitalize
    seen = set()
    unique = []
    for s in found_skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s.title() if len(s) > 3 else s.upper())
    
    return unique[:20]


def calculate_individual_skill_scores(resume_text, jd_skills):
    """
    Calculate per-skill match scores between a resume and JD skills.
    
    Returns:
        dict: {skill_name: score (0-100)}
    """
    resume_lower = resume_text.lower()
    skill_scores = {}
    
    for skill in jd_skills:
        skill_lower = skill.lower()
        if skill_lower in resume_lower:
            count = resume_lower.count(skill_lower)
            # Base score 65 + up to 30 for frequency, cap at 98
            score = min(65 + count * 7, 98)
            # Boost for multi-word matches (more specific)
            if ' ' in skill_lower:
                score = min(score + 5, 98)
            skill_scores[skill] = score
        else:
            skill_scores[skill] = 0
    
    return skill_scores


def identify_skills_gap(resume_text, jd_skills):
    """
    Find skills required in JD but missing from the resume.
    """
    resume_lower = resume_text.lower()
    missing = []
    
    for skill in jd_skills:
        if skill.lower() not in resume_lower:
            missing.append(skill)
    
    return missing


def calculate_experience_match(resume_text, jd_text):
    """
    Compare experience years between resume and JD.
    Returns a percentage match score.
    """
    import re
    
    # Extract years from JD
    jd_years = extract_experience_years(jd_text)
    
    # Extract years mentioned in resume
    resume_lower = resume_text.lower()
    year_patterns = [
        r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:\+)?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?',
    ]
    
    max_resume_years = 0
    for pattern in year_patterns:
        matches = re.findall(pattern, resume_lower)
        for match in matches:
            if isinstance(match, tuple):
                for m in match:
                    if m:
                        try:
                            max_resume_years = max(max_resume_years, int(m))
                        except ValueError:
                            pass
            else:
                try:
                    max_resume_years = max(max_resume_years, int(match))
                except ValueError:
                    pass
    
    # Parse JD requirement
    jd_min = 0
    jd_match = re.search(r'(\d+)', jd_years)
    if jd_match:
        jd_min = int(jd_match.group(1))
    
    if jd_min == 0:
        return 80  # Default if no requirement specified
    
    if max_resume_years >= jd_min:
        return min(75 + (max_resume_years - jd_min) * 5, 98)
    elif max_resume_years > 0:
        return max(int((max_resume_years / jd_min) * 80), 30)
    else:
        return 55  # Can't determine


def generate_detailed_report(results, jd_text):
    """
    Generate text-based analysis insights and recommendations.
    """
    if not results:
        return [], []
    
    job_role = extract_job_role(jd_text)
    insights = []
    recommendations = []
    
    # Sort by score
    sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    # Best candidate insight
    best = sorted_results[0]
    best_keywords = best.get('matched_keywords', [])[:3]
    kw_str = ', '.join(best_keywords) if best_keywords else 'relevant skills'
    insights.append(
        f"{best['resume_name']} is the best match with strong experience in {kw_str}."
    )
    
    # Second candidate
    if len(sorted_results) > 1:
        second = sorted_results[1]
        sec_kw = second.get('matched_keywords', [])[:2]
        sec_str = ' and '.join(sec_kw) if sec_kw else 'relevant areas'
        insights.append(
            f"{second['resume_name']} shows good skills in {sec_str}."
        )
    
    # Weaker candidates
    for r in sorted_results[2:]:
        if r['score'] >= 60:
            insights.append(
                f"{r['resume_name']} has relevant experience but lacks some key technical skills."
            )
        else:
            insights.append(
                f"{r['resume_name']} needs improvement in core {job_role.lower()} competencies."
            )
    
    # Recommendations
    top_count = sum(1 for r in sorted_results if r['score'] >= 70)
    recommendations.append(f"Shortlist top {max(top_count, 1)} candidate{'s' if top_count != 1 else ''}")
    recommendations.append("Consider skill gap for interview focus areas")
    
    # Find most common missing skills
    all_missing = []
    for r in sorted_results:
        all_missing.extend(r.get('missing_keywords', []))
    if all_missing:
        from collections import Counter
        common_gaps = Counter(all_missing).most_common(2)
        for skill, _ in common_gaps:
            recommendations.append(f"Focus on {skill.lower()} in interviews")
    
    recommendations.append("Verify practical experience in person")
    
    return insights, recommendations[:5]


def analyze_resume_enhanced(resume_text, jd_text, resume_name, jd_skills):
    """
    Enhanced single resume analysis with detailed metrics for dashboard.
    """
    base = analyze_single_resume(resume_text, jd_text, resume_name)
    if not base:
        return None
    
    # Calculate individual skill scores
    skill_scores = calculate_individual_skill_scores(resume_text, jd_skills)
    
    # Skills match percentage
    matched_count = sum(1 for v in skill_scores.values() if v > 0)
    skills_match = round((matched_count / len(jd_skills) * 100) if jd_skills else 0, 1)
    
    # Experience match
    experience_match = calculate_experience_match(resume_text, jd_text)
    
    # Missing skills
    missing = identify_skills_gap(resume_text, jd_skills)
    
    # Determine status
    score = base['score']
    if score >= 85:
        status = 'Best Match'
    elif score >= 70:
        status = 'Shortlisted'
    elif score >= 60:
        status = 'Review'
    elif score >= 50:
        status = 'Consider'
    else:
        status = 'Not Matched'
    
    base.update({
        'skills_match': round(skills_match, 1),
        'experience_match': experience_match,
        'skill_scores': {k: v for k, v in skill_scores.items() if v > 0},
        'missing_keywords': missing[:8],
        'status': status,
    })
    
    return base


def compare_resumes_enhanced(resumes_data, jd_text):
    """
    Enhanced multi-resume analysis returning all data needed for the dashboard.
    """
    jd_skills = get_jd_tech_skills(jd_text)
    job_role = extract_job_role(jd_text)
    experience_req = extract_experience_years(jd_text)
    
    results = []
    for resume_name, resume_text in resumes_data:
        result = analyze_resume_enhanced(resume_text, jd_text, resume_name, jd_skills)
        if result:
            results.append(result)
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Aggregate top strengths (most common matched keywords across all resumes)
    from collections import Counter
    all_keywords = []
    for r in results:
        all_keywords.extend(r.get('matched_keywords', []))
    top_strengths = [kw for kw, _ in Counter(all_keywords).most_common(6)]
    
    # Detailed report
    insights, recommendations = generate_detailed_report(results, jd_text)
    
    # Score distribution
    above_80 = sum(1 for r in results if r['score'] >= 80)
    between_60_79 = sum(1 for r in results if 60 <= r['score'] < 80)
    below_60 = sum(1 for r in results if r['score'] < 60)
    
    return {
        'success': True,
        'job_role': job_role,
        'experience_required': experience_req,
        'total_jd_skills': len(jd_skills),
        'jd_skills': jd_skills,
        'results': results,
        'total_resumes': len(results),
        'top_strengths': top_strengths,
        'insights': insights,
        'recommendations': recommendations,
        'score_distribution': {
            'above_80': above_80,
            'between_60_79': between_60_79,
            'below_60': below_60,
        }
    }

