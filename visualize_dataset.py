"""
Visualize training dataset statistics and distribution
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def load_dataset(dataset_path='training_data/resume_jd_dataset.json'):
    """Load dataset from JSON"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_dataset(dataset, output_dir='training_data/visualizations'):
    """Create visualizations of the dataset"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    df = pd.DataFrame(dataset)
    
    # 1. Score Distribution
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Overall score distribution
    axes[0, 0].hist(df['score'], bins=20, edgecolor='black', alpha=0.7)
    axes[0, 0].set_xlabel('Match Score')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Score Distribution (All Samples)')
    axes[0, 0].axvline(df['score'].mean(), color='red', linestyle='--', label=f'Mean: {df["score"].mean():.2f}')
    axes[0, 0].legend()
    
    # Score by label
    positive = df[df['label'] == 1]['score']
    negative = df[df['label'] == 0]['score']
    axes[0, 1].hist([positive, negative], bins=15, label=['Positive', 'Negative'], edgecolor='black', alpha=0.7)
    axes[0, 1].set_xlabel('Match Score')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Score Distribution by Label')
    axes[0, 1].legend()
    
    # Label distribution
    label_counts = df['label'].value_counts()
    axes[1, 0].bar(['Negative (0)', 'Positive (1)'], [label_counts.get(0, 0), label_counts.get(1, 0)], 
                   color=['#ff6b6b', '#51cf66'], edgecolor='black')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].set_title('Label Distribution')
    axes[1, 0].set_ylim(0, max(label_counts.values()) * 1.1)
    
    # Role distribution
    role_counts = df['resume_role'].value_counts()
    axes[1, 1].barh(role_counts.index, role_counts.values, color='skyblue', edgecolor='black')
    axes[1, 1].set_xlabel('Count')
    axes[1, 1].set_title('Resume Role Distribution')
    
    plt.tight_layout()
    plt.savefig(output_path / 'dataset_overview.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved visualization to {output_path / 'dataset_overview.png'}")
    plt.close()
    
    # 2. Score heatmap by role matching
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create pivot table of average scores
    score_matrix = df.pivot_table(
        values='score',
        index='resume_role',
        columns='jd_title',
        aggfunc='mean'
    )
    
    sns.heatmap(score_matrix, annot=True, fmt='.1f', cmap='RdYlGn', center=50,
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Average Match Score'})
    ax.set_title('Average Match Score: Resume Role vs Job Title')
    ax.set_xlabel('Job Title')
    ax.set_ylabel('Resume Role')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    plt.savefig(output_path / 'score_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved heatmap to {output_path / 'score_heatmap.png'}")
    plt.close()
    
    # 3. Print summary statistics
    print("\n=== Dataset Summary ===")
    print(f"Total samples: {len(df)}")
    print(f"Positive samples: {len(df[df['label'] == 1])}")
    print(f"Negative samples: {len(df[df['label'] == 0])}")
    print(f"\nScore statistics:")
    print(df['score'].describe())
    print(f"\nUnique roles: {df['resume_role'].nunique()}")
    print(f"Unique job titles: {df['jd_title'].nunique()}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize training dataset')
    parser.add_argument('--dataset', type=str, default='training_data/resume_jd_dataset.json',
                        help='Path to dataset JSON file')
    parser.add_argument('--output', type=str, default='training_data/visualizations',
                        help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    print("Loading dataset...")
    dataset = load_dataset(args.dataset)
    
    print("Creating visualizations...")
    visualize_dataset(dataset, args.output)
    
    print("\n✅ Visualization complete!")


if __name__ == '__main__':
    main()
