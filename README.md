# 🤖 AI Resume Matcher

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green)](https://www.djangoproject.com/)

> **Resume screening with AI-powered semantic similarity**

A Django web application that analyzes resumes against job descriptions using Sentence-BERT for intelligent candidate ranking.

---

## ✨ Features

- 📄 **Resume Upload** - Support for PDF, DOCX, and TXT files
- 🤖 **AI-Powered Matching** - Uses Sentence-BERT for semantic similarity
- 📊 **Smart Scoring** - Bidirectional similarity between resume and job description
- 🔍 **Keyword Extraction** - Identifies matching skills and qualifications
- 📈 **Ranking System** - Compare multiple resumes and rank them

### File Support
- **PDF** - Text extraction with PyMuPDF
- **DOCX** - Word document support
- **TXT** - Plain text files

### AI Model
- **Sentence-BERT** (all-mpnet-base-v2) - 768-dimensional embeddings for semantic similarity

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip
- 2GB RAM minimum

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-resume-matcher.git
   cd ai-resume-matcher
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your SECRET_KEY
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Open your browser**
   ```
   http://localhost:8000
   ```

---

## 📖 How It Works

### Workflow
1. **Upload** - Upload resumes (PDF/DOCX/TXT) and job description
2. **Extract** - Text extracted from documents
3. **Analyze** - Sentence-BERT calculates semantic similarity
4. **Score** - Bidirectional similarity score (0-100%)
5. **Rank** - Resumes ranked by match percentage

### Scoring Algorithm
```python
# Extract text from documents
resume_text = extract_text(resume_file)
jd_text = extract_text(jd_file)

# Calculate bidirectional similarity
resume_to_jd = cosine_similarity(resume_sentences, jd_sentences)
jd_to_resume = cosine_similarity(jd_sentences, resume_sentences)

# Final score
score = (resume_to_jd + jd_to_resume) / 2
```

---

## 🛠️ Tech Stack

- **Django 4.2** - Web framework
- **Sentence-Transformers** - SBERT for semantic similarity
- **spaCy** - NLP and sentence segmentation
- **NLTK** - Keyword extraction
- **PyMuPDF** - PDF text extraction
- **python-docx** - DOCX file support
- **SQLite** - Database

---

## 🔧 Configuration

Create a `.env` file:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 🔗 API Endpoints

### Compare Resumes
```http
POST /analysis/compare-resumes/
Content-Type: multipart/form-data

Parameters:
- jd_file: Job description file
- resume1-5: Up to 5 resume files

Response:
{
  "status": "success",
  "results": [
    {
      "resume_name": "candidate.pdf",
      "score": 85.5,
      "matched_keywords": ["python", "django"],
      "match_report": [...]
    }
  ]
}
```

---

## 🚨 Troubleshooting

### Model Download Issues
- Ensure stable internet connection
- First run takes ~2 minutes to download SBERT model

### NLTK Data Missing
```bash
python -m nltk.downloader stopwords punkt averaged_perceptron_tagger
```

### File Upload Issues
- Ensure file is PDF, DOCX, or TXT
- Check file size (<10MB)

---

## 📁 Project Structure

```
resume_analyzer/
├── analysis/              # Main app
│   ├── views.py          # Core logic
│   ├── urls.py           # Routes
│   └── templates/        # HTML
├── resume_analyzer/       # Settings
│   └── settings.py       # Config
├── output/job_bert/       # SBERT model
├── manage.py
└── requirements.txt
```

---

## 🚀 Future Enhancements

- User authentication
- Database storage for history
- Batch resume processing
- Export results to PDF/CSV
- Advanced filtering options

---

## 📝 License

MIT License

---

**Day 1  AI Resume Matcher**

*Built with Django and Sentence-BERT*
