# Training Data and Model Fine-tuning

## Overview

This directory contains tools for generating synthetic training data and fine-tuning the resume-JD matching model.

## Quick Start

### 1. Generate Training Dataset

```bash
# Generate default dataset (50 positive + 50 negative examples)
python generate_dataset.py

# Generate larger dataset
python generate_dataset.py --positive 200 --negative 200

# Generate with sample files
python generate_dataset.py --samples

# Custom output directory
python generate_dataset.py --output my_training_data
```

### 2. Train the Model

```bash
# Train with default settings
python train_model.py

# Train with custom parameters
python train_model.py --epochs 10 --batch-size 32

# Use custom dataset
python train_model.py --dataset my_training_data/resume_jd_dataset.json

# Fine-tune different base model
python train_model.py --model sentence-transformers/all-MiniLM-L6-v2
```

---

## Dataset Structure

### Generated Files

```
training_data/
├── resume_jd_dataset.json      # Main training dataset
├── resume_jd_dataset.csv       # CSV version
├── dataset_stats.json          # Dataset statistics
└── samples/                    # Sample files (optional)
    ├── resume_1_backend_developer.txt
    ├── resume_2_full_stack_developer.txt
    ├── jd_1_backend_developer.txt
    └── jd_2_full_stack_developer.txt
```

### Data Format

Each sample contains:
```json
{
  "id": "pos_0",
  "resume_text": "Backend Developer Resume\nSUMMARY...",
  "jd_text": "Backend Developer Position\nABOUT THE ROLE...",
  "score": 85.5,
  "label": 1,
  "resume_role": "Backend Developer",
  "jd_title": "Backend Developer"
}
```

Fields:
- `id`: Unique identifier (pos_* for matches, neg_* for non-matches)
- `resume_text`: Full resume text
- `jd_text`: Full job description text
- `score`: Calculated match score (0-100)
- `label`: Binary label (1 = match, 0 = no match)
- `resume_role`: Role from resume
- `jd_title`: Job title from JD

---

## Sample Data Templates

### Resume Roles Included
1. Backend Developer (Python, Django, PostgreSQL)
2. Full Stack Developer (JavaScript, React, Node.js)
3. Machine Learning Engineer (Python, TensorFlow, PyTorch)
4. Senior Java Developer (Java, Spring Boot, MySQL)
5. Mobile Developer (React Native, Flutter)
6. Data Analyst (Tableau, Power BI, SQL)
7. Frontend Developer (HTML, CSS, React)
8. DevOps Engineer (AWS, Docker, Kubernetes)

### Job Description Types
- 8 different job roles matching the resume types
- Required and preferred skills
- Experience requirements
- Responsibilities and qualifications

---

## Training Pipeline

### Step 1: Data Generation
```bash
python generate_dataset.py --positive 100 --negative 100
```

**Output:**
- 100 matching resume-JD pairs (high similarity)
- 100 non-matching pairs (low similarity)
- Balanced dataset for training

### Step 2: Model Training
```bash
python train_model.py --epochs 4 --batch-size 16
```

**Process:**
1. Load pre-trained Sentence-BERT model
2. Fine-tune on resume-JD pairs
3. Use CosineSimilarityLoss
4. Validate during training
5. Save best model

### Step 3: Evaluation
Model automatically evaluates on validation set:
- **MSE** (Mean Squared Error)
- **MAE** (Mean Absolute Error)
- **Pearson Correlation**

---

## Training Parameters

### Dataset Generation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--positive` | 50 | Number of matching pairs |
| `--negative` | 50 | Number of non-matching pairs |
| `--output` | training_data | Output directory |
| `--samples` | False | Create sample text files |

### Model Training

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--dataset` | training_data/resume_jd_dataset.json | Training data path |
| `--model` | all-mpnet-base-v2 | Base model name |
| `--output` | output/job_bert_finetuned | Model output path |
| `--epochs` | 4 | Training epochs |
| `--batch-size` | 16 | Batch size |
| `--split` | 0.8 | Train/validation split |

---

## Using the Fine-tuned Model

### Update services.py

Replace the model loading line:

```python
# Before
sbert_model = SentenceTransformer('output/job_bert')

# After (using fine-tuned model)
sbert_model = SentenceTransformer('output/job_bert_finetuned')
```

### Restart Django Server

```bash
python manage.py runserver
```

---

## Advanced Usage

### Custom Dataset

Create your own dataset in JSON format:

```python
[
  {
    "resume_text": "Your resume text...",
    "jd_text": "Your JD text...",
    "score": 75.5,
    "label": 1
  }
]
```

Train with custom dataset:
```bash
python train_model.py --dataset path/to/your/dataset.json
```

### Real Data Collection

To use real data instead of synthetic:

1. Collect resume-JD pairs from actual hiring data
2. Have recruiters score matches (0-100)
3. Format data according to schema
4. Train model on real data

### Hyperparameter Tuning

```bash
# Experiment with different settings
python train_model.py --epochs 10 --batch-size 32
python train_model.py --epochs 5 --batch-size 8

# Try different base models
python train_model.py --model sentence-transformers/all-MiniLM-L6-v2
python train_model.py --model sentence-transformers/paraphrase-mpnet-base-v2
```

---

## Expected Results

### Baseline Model (No Fine-tuning)
- Pearson Correlation: ~0.65-0.75
- MAE: ~0.15-0.20

### Fine-tuned Model (After Training)
- Pearson Correlation: ~0.80-0.90
- MAE: ~0.08-0.12
- Better domain-specific understanding

---

## Troubleshooting

### Out of Memory Error
```bash
# Reduce batch size
python train_model.py --batch-size 8
```

### Slow Training
```bash
# Reduce dataset size
python generate_dataset.py --positive 30 --negative 30

# Reduce epochs
python train_model.py --epochs 2
```

### Model Not Improving
- Generate more diverse training data
- Increase training epochs
- Try different base models
- Check data quality and balance

---

## Dataset Statistics

After generation, check `dataset_stats.json`:

```json
{
  "total_samples": 100,
  "positive_samples": 50,
  "negative_samples": 50,
  "average_score": 45.2,
  "unique_roles": 8,
  "unique_jd_titles": 8
}
```

---

## Best Practices

1. **Balanced Dataset**: Equal positive and negative examples
2. **Diverse Roles**: Cover multiple job categories
3. **Quality Over Quantity**: Better to have 100 good examples than 1000 poor ones
4. **Regular Re-training**: Update model as new data becomes available
5. **Validation**: Always evaluate on held-out test set

---

## Integration with Main App

After training, update the model path in [services.py](analysis/services.py):

```python
# Load the fine-tuned model
sbert_model = SentenceTransformer('output/job_bert_finetuned')
```

The rest of the application will automatically use the improved model!

---

## Next Steps

1. ✅ Generate synthetic dataset
2. ✅ Train initial model
3. ⬜ Collect real resume-JD pairs
4. ⬜ Fine-tune on real data
5. ⬜ Evaluate on production data
6. ⬜ Deploy improved model

---

## Resources

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [Training Custom Models](https://www.sbert.net/docs/training/overview.html)
- [Loss Functions](https://www.sbert.net/docs/package_reference/losses.html)
