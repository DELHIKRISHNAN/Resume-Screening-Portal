"""
Quick demo of the training pipeline
Demonstrates dataset generation and model evaluation
"""

from pathlib import Path
import json


def demo_dataset_generation():
    """Demo: Generate a small dataset"""
    print("=" * 60)
    print("DEMO 1: Dataset Generation")
    print("=" * 60)
    
    from generate_dataset import generate_dataset, create_sample_files
    
    print("\nGenerating small demo dataset (10 positive, 10 negative)...")
    dataset = generate_dataset(num_positive=10, num_negative=10, output_dir='demo_data')
    
    print("\n✓ Dataset generated successfully!")
    print(f"Total samples: {len(dataset)}")
    
    # Show a sample
    print("\n--- Sample Entry ---")
    sample = dataset[0]
    print(f"ID: {sample['id']}")
    print(f"Resume Role: {sample['resume_role']}")
    print(f"JD Title: {sample['jd_title']}")
    print(f"Score: {sample['score']}")
    print(f"Label: {sample['label']}")
    print(f"Resume Text (first 100 chars): {sample['resume_text'][:100]}...")
    
    return dataset


def demo_model_evaluation():
    """Demo: Evaluate existing model on sample data"""
    print("\n" + "=" * 60)
    print("DEMO 2: Model Evaluation")
    print("=" * 60)
    
    try:
        from sentence_transformers import SentenceTransformer, util
        import torch
        
        print("\nLoading pre-trained model...")
        model = SentenceTransformer('output/job_bert')
        print("✓ Model loaded successfully!")
        
        # Test on sample pair
        print("\n--- Testing Model ---")
        resume_text = "Python developer with 5 years experience in Django and PostgreSQL"
        jd_text = "Seeking Python developer with Django experience for backend development"
        
        print(f"Resume: {resume_text}")
        print(f"JD: {jd_text}")
        
        # Calculate similarity
        embeddings = model.encode([resume_text, jd_text], convert_to_tensor=True)
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        
        print(f"\nSimilarity Score: {similarity:.4f} ({similarity*100:.2f}%)")
        
        if similarity > 0.7:
            print("✓ Strong match!")
        elif similarity > 0.5:
            print("~ Moderate match")
        else:
            print("✗ Weak match")
        
        return similarity
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Note: Make sure the model is available in output/job_bert/")
        return None


def demo_statistics():
    """Demo: Show dataset statistics"""
    print("\n" + "=" * 60)
    print("DEMO 3: Dataset Statistics")
    print("=" * 60)
    
    try:
        with open('demo_data/dataset_stats.json', 'r') as f:
            stats = json.load(f)
        
        print("\n--- Statistics ---")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
            
    except FileNotFoundError:
        print("✗ Stats file not found. Generate dataset first.")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("🎓 TRAINING PIPELINE DEMO")
    print("=" * 60)
    print("\nThis demo will:")
    print("1. Generate a small training dataset")
    print("2. Evaluate the existing model")
    print("3. Show dataset statistics")
    print("\nPress Enter to continue...")
    input()
    
    # Demo 1: Dataset generation
    dataset = demo_dataset_generation()
    
    # Demo 2: Model evaluation
    demo_model_evaluation()
    
    # Demo 3: Statistics
    demo_statistics()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Generate larger dataset: python generate_dataset.py --positive 100 --negative 100")
    print("2. Visualize data: python visualize_dataset.py")
    print("3. Train model: python train_model.py")
    print("4. See TRAINING_GUIDE.md for detailed instructions")


if __name__ == '__main__':
    main()
