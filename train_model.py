"""
Training script for fine-tuning Sentence-BERT model on resume-JD matching
Uses the generated synthetic dataset
"""

import json
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import logging
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_dataset(dataset_path='training_data/resume_jd_dataset.json'):
    """Load training dataset from JSON file"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    logger.info(f"Loaded {len(dataset)} samples from {dataset_path}")
    return dataset


def prepare_training_data(dataset, split_ratio=0.8):
    """
    Prepare training and validation data
    
    Args:
        dataset: List of samples with resume_text, jd_text, and score
        split_ratio: Train/validation split ratio
    
    Returns:
        train_examples, val_examples
    """
    # Convert to InputExample format for Sentence-BERT
    examples = []
    for sample in dataset:
        # Normalize score to 0-1 range
        normalized_score = sample['score'] / 100.0
        examples.append(InputExample(
            texts=[sample['resume_text'], sample['jd_text']],
            label=float(normalized_score)
        ))
    
    # Split into train and validation
    split_idx = int(len(examples) * split_ratio)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]
    
    logger.info(f"Training samples: {len(train_examples)}")
    logger.info(f"Validation samples: {len(val_examples)}")
    
    return train_examples, val_examples


def train_model(
    train_examples,
    val_examples,
    model_name='sentence-transformers/all-mpnet-base-v2',
    output_path='output/job_bert_finetuned',
    epochs=4,
    batch_size=16,
    warmup_steps=100
):
    """
    Fine-tune Sentence-BERT model
    
    Args:
        train_examples: Training data
        val_examples: Validation data
        model_name: Base model to fine-tune
        output_path: Where to save fine-tuned model
        epochs: Number of training epochs
        batch_size: Training batch size
        warmup_steps: Warmup steps for learning rate
    """
    # Load base model
    logger.info(f"Loading base model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Create data loader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    
    # Use CosineSimilarityLoss for regression on similarity scores
    train_loss = losses.CosineSimilarityLoss(model)
    
    # Prepare validation evaluator
    val_sentences1 = [example.texts[0] for example in val_examples]
    val_sentences2 = [example.texts[1] for example in val_examples]
    val_scores = [example.label for example in val_examples]
    
    evaluator = EmbeddingSimilarityEvaluator(
        val_sentences1,
        val_sentences2,
        val_scores,
        name='resume-jd-validation'
    )
    
    # Training configuration
    logger.info("Starting training...")
    logger.info(f"Epochs: {epochs}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Warmup steps: {warmup_steps}")
    
    # Train the model
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=epochs,
        warmup_steps=warmup_steps,
        output_path=output_path,
        evaluation_steps=500,
        save_best_model=True,
        show_progress_bar=True
    )
    
    logger.info(f"✓ Training complete! Model saved to {output_path}")
    
    return model


def evaluate_model(model, test_examples):
    """
    Evaluate model performance on test set
    
    Args:
        model: Trained SentenceTransformer model
        test_examples: Test data
    
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info("Evaluating model...")
    
    predictions = []
    actuals = []
    
    for example in test_examples:
        # Encode texts
        embeddings = model.encode(example.texts, convert_to_tensor=True)
        
        # Calculate cosine similarity
        cos_sim = torch.nn.functional.cosine_similarity(
            embeddings[0].unsqueeze(0),
            embeddings[1].unsqueeze(0)
        ).item()
        
        predictions.append(cos_sim)
        actuals.append(example.label)
    
    # Calculate metrics
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    mse = np.mean((predictions - actuals) ** 2)
    mae = np.mean(np.abs(predictions - actuals))
    pearson_corr = np.corrcoef(predictions, actuals)[0, 1]
    
    metrics = {
        'mse': float(mse),
        'mae': float(mae),
        'pearson_correlation': float(pearson_corr),
        'num_samples': len(test_examples)
    }
    
    logger.info(f"MSE: {mse:.4f}")
    logger.info(f"MAE: {mae:.4f}")
    logger.info(f"Pearson Correlation: {pearson_corr:.4f}")
    
    return metrics


def main():
    """Main training pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train resume-JD matching model')
    parser.add_argument('--dataset', type=str, default='training_data/resume_jd_dataset.json',
                        help='Path to training dataset')
    parser.add_argument('--model', type=str, default='sentence-transformers/all-mpnet-base-v2',
                        help='Base model to fine-tune')
    parser.add_argument('--output', type=str, default='output/job_bert_finetuned',
                        help='Output directory for fine-tuned model')
    parser.add_argument('--epochs', type=int, default=4,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Training batch size')
    parser.add_argument('--split', type=float, default=0.8,
                        help='Train/validation split ratio')
    
    args = parser.parse_args()
    
    # Load dataset
    dataset = load_dataset(args.dataset)
    
    # Prepare data
    train_examples, val_examples = prepare_training_data(dataset, args.split)
    
    # Train model
    model = train_model(
        train_examples,
        val_examples,
        model_name=args.model,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    # Evaluate on validation set
    logger.info("\n=== Final Evaluation ===")
    metrics = evaluate_model(model, val_examples)
    
    # Save metrics
    metrics_path = Path(args.output) / 'evaluation_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"✓ Metrics saved to {metrics_path}")
    
    logger.info("\n✅ Training pipeline complete!")


if __name__ == '__main__':
    main()
