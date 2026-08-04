# 🎓 Training Quick Reference

## One-Line Commands

```bash
# Generate dataset
python generate_dataset.py --positive 100 --negative 100 --samples

# Visualize dataset (requires matplotlib, seaborn)
python visualize_dataset.py

# Train model
python train_model.py --epochs 4 --batch-size 16

# Run demo
python demo_training.py
```

## Files Created

### Dataset Generation
- `training_data/resume_jd_dataset.json` - Main dataset
- `training_data/resume_jd_dataset.csv` - CSV format
- `training_data/dataset_stats.json` - Statistics
- `training_data/samples/*.txt` - Sample files (if --samples used)

### Training
- `output/job_bert_finetuned/` - Fine-tuned model
- `output/job_bert_finetuned/evaluation_metrics.json` - Performance metrics

### Visualization
- `training_data/visualizations/dataset_overview.png`
- `training_data/visualizations/score_heatmap.png`

## Common Workflows

### 1. Quick Test (Small Dataset)
```bash
python generate_dataset.py --positive 20 --negative 20
python train_model.py --epochs 2
```

### 2. Production Training (Large Dataset)
```bash
python generate_dataset.py --positive 200 --negative 200
python train_model.py --epochs 10 --batch-size 32
```

### 3. Visualization Workflow
```bash
pip install matplotlib seaborn
python generate_dataset.py --positive 50 --negative 50
python visualize_dataset.py
# Check: training_data/visualizations/
```

## Integration

After training, update `analysis/services.py`:

```python
# Line 27 - Change from:
sbert_model = SentenceTransformer('output/job_bert')

# To:
sbert_model = SentenceTransformer('output/job_bert_finetuned')
```

Then restart Django:
```bash
python manage.py runserver
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Out of memory | Reduce `--batch-size` to 8 or 4 |
| Slow training | Reduce dataset size or epochs |
| Model not found | Check path in services.py |
| Import errors | `pip install -r requirements-training.txt` |

## Expected Performance

| Metric | Before Training | After Training |
|--------|----------------|----------------|
| Pearson Correlation | 0.65-0.75 | 0.80-0.90 |
| MAE | 0.15-0.20 | 0.08-0.12 |

## Parameters Reference

### generate_dataset.py
- `--positive N` - Number of matching pairs (default: 50)
- `--negative N` - Number of non-matching pairs (default: 50)
- `--output DIR` - Output directory (default: training_data)
- `--samples` - Create sample text files

### train_model.py
- `--dataset PATH` - Dataset JSON path
- `--model NAME` - Base model name
- `--output PATH` - Model output path
- `--epochs N` - Training epochs (default: 4)
- `--batch-size N` - Batch size (default: 16)
- `--split RATIO` - Train/val split (default: 0.8)

## Sample Dataset

8 roles included:
1. Backend Developer (Python, Django)
2. Full Stack Developer (JavaScript, React)
3. Machine Learning Engineer (Python, TensorFlow)
4. Senior Java Developer (Java, Spring Boot)
5. Mobile Developer (React Native, Flutter)
6. Data Analyst (Tableau, SQL)
7. Frontend Developer (HTML, CSS, React)
8. DevOps Engineer (AWS, Docker)

## Next Steps

1. ✅ Generate synthetic data
2. ✅ Train initial model
3. ⬜ Test on real resumes
4. ⬜ Fine-tune with real data
5. ⬜ Deploy to production

See [TRAINING_GUIDE.md](TRAINING_GUIDE.md) for complete documentation.
