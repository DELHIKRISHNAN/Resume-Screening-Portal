"""
Sample dataset generator for resume-JD matching
Creates synthetic training data for fine-tuning models
"""

import csv
import json
import random
from pathlib import Path

# Sample resume templates
RESUME_TEMPLATES = [
    # Tech roles
    {
        "skills": ["Python", "Django", "PostgreSQL", "REST API", "Docker"],
        "experience": "5 years",
        "role": "Backend Developer",
        "education": "BS Computer Science",
        "projects": ["E-commerce platform", "Payment gateway integration"]
    },
    {
        "skills": ["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
        "experience": "3 years",
        "role": "Full Stack Developer",
        "education": "BS Software Engineering",
        "projects": ["Social media dashboard", "Real-time chat application"]
    },
    {
        "skills": ["Python", "TensorFlow", "PyTorch", "scikit-learn", "Pandas"],
        "experience": "4 years",
        "role": "Machine Learning Engineer",
        "education": "MS Data Science",
        "projects": ["Recommendation system", "Image classification model"]
    },
    {
        "skills": ["Java", "Spring Boot", "MySQL", "Microservices", "Kubernetes"],
        "experience": "6 years",
        "role": "Senior Java Developer",
        "education": "BS Computer Engineering",
        "projects": ["Banking application", "Distributed system design"]
    },
    {
        "skills": ["React Native", "Flutter", "iOS", "Android", "Firebase"],
        "experience": "3 years",
        "role": "Mobile Developer",
        "education": "BS Information Technology",
        "projects": ["Fitness tracking app", "Food delivery application"]
    },
    {
        "skills": ["Tableau", "Power BI", "SQL", "Python", "Excel"],
        "experience": "2 years",
        "role": "Data Analyst",
        "education": "BS Business Analytics",
        "projects": ["Sales dashboard", "Customer segmentation analysis"]
    },
    {
        "skills": ["HTML", "CSS", "JavaScript", "Vue.js", "Figma"],
        "experience": "2 years",
        "role": "Frontend Developer",
        "education": "BS Web Design",
        "projects": ["Corporate website redesign", "Interactive portfolio"]
    },
    {
        "skills": ["AWS", "Terraform", "Jenkins", "Docker", "Kubernetes"],
        "experience": "5 years",
        "role": "DevOps Engineer",
        "education": "BS Computer Science",
        "projects": ["CI/CD pipeline automation", "Infrastructure as code"]
    }
]

# Sample job description templates
JOB_TEMPLATES = [
    {
        "title": "Backend Developer",
        "required_skills": ["Python", "Django", "PostgreSQL", "REST API"],
        "preferred_skills": ["Docker", "Redis", "Celery"],
        "experience": "3-5 years",
        "responsibilities": ["Design APIs", "Database optimization", "Code reviews"],
        "qualifications": ["BS in Computer Science or related field"]
    },
    {
        "title": "Full Stack Developer",
        "required_skills": ["JavaScript", "React", "Node.js", "MongoDB"],
        "preferred_skills": ["AWS", "TypeScript", "GraphQL"],
        "experience": "2-4 years",
        "responsibilities": ["Build web applications", "Frontend and backend development"],
        "qualifications": ["BS in Software Engineering or equivalent"]
    },
    {
        "title": "Machine Learning Engineer",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
        "preferred_skills": ["Deep Learning", "NLP", "Computer Vision"],
        "experience": "3-5 years",
        "responsibilities": ["Develop ML models", "Deploy models to production"],
        "qualifications": ["MS in Data Science or Machine Learning"]
    },
    {
        "title": "Senior Java Developer",
        "required_skills": ["Java", "Spring Boot", "MySQL", "Microservices"],
        "preferred_skills": ["Kubernetes", "AWS", "Redis"],
        "experience": "5+ years",
        "responsibilities": ["Lead development team", "Architecture design"],
        "qualifications": ["BS in Computer Engineering with 5+ years experience"]
    },
    {
        "title": "Mobile Developer",
        "required_skills": ["React Native", "iOS", "Android"],
        "preferred_skills": ["Flutter", "Firebase", "Mobile UI/UX"],
        "experience": "2-4 years",
        "responsibilities": ["Develop mobile apps", "App store deployment"],
        "qualifications": ["BS in IT or Computer Science"]
    },
    {
        "title": "Data Analyst",
        "required_skills": ["SQL", "Tableau", "Excel", "Python"],
        "preferred_skills": ["Power BI", "Statistics", "Data Visualization"],
        "experience": "1-3 years",
        "responsibilities": ["Create dashboards", "Analyze business data"],
        "qualifications": ["BS in Business Analytics or Statistics"]
    },
    {
        "title": "Frontend Developer",
        "required_skills": ["HTML", "CSS", "JavaScript", "React"],
        "preferred_skills": ["Vue.js", "TypeScript", "Responsive Design"],
        "experience": "2-3 years",
        "responsibilities": ["Build user interfaces", "Optimize web performance"],
        "qualifications": ["BS in Web Design or Computer Science"]
    },
    {
        "title": "DevOps Engineer",
        "required_skills": ["AWS", "Docker", "Kubernetes", "CI/CD"],
        "preferred_skills": ["Terraform", "Jenkins", "Monitoring tools"],
        "experience": "4-6 years",
        "responsibilities": ["Automate infrastructure", "Manage deployments"],
        "qualifications": ["BS in Computer Science with DevOps experience"]
    }
]


def generate_resume_text(template):
    """Generate resume text from template"""
    return f"""
{template['role']} Resume

SUMMARY
{template['role']} with {template['experience']} of experience in software development.

EDUCATION
{template['education']}

SKILLS
{', '.join(template['skills'])}

EXPERIENCE
{template['role']} | Tech Company | {template['experience']}
- Led development of {template['projects'][0]}
- Contributed to {template['projects'][1]}
- Collaborated with cross-functional teams
- Participated in code reviews and agile sprints

PROJECTS
{template['projects'][0]}: Built using {template['skills'][0]} and {template['skills'][1]}
{template['projects'][1]}: Implemented with {template['skills'][2]} and {template['skills'][3]}
""".strip()


def generate_jd_text(template):
    """Generate job description text from template"""
    return f"""
{template['title']} Position

ABOUT THE ROLE
We are seeking a talented {template['title']} with {template['experience']} of experience.

REQUIRED SKILLS
{', '.join(template['required_skills'])}

PREFERRED SKILLS
{', '.join(template['preferred_skills'])}

RESPONSIBILITIES
{' '.join(['- ' + r for r in template['responsibilities']])}

QUALIFICATIONS
{template['qualifications']}
Required experience: {template['experience']}
""".strip()


def calculate_match_score(resume_template, jd_template):
    """Calculate match score based on skill overlap"""
    resume_skills = set([s.lower() for s in resume_template['skills']])
    required_skills = set([s.lower() for s in jd_template['required_skills']])
    preferred_skills = set([s.lower() for s in jd_template['preferred_skills']])
    
    # Calculate overlap
    required_overlap = len(resume_skills & required_skills)
    preferred_overlap = len(resume_skills & preferred_skills)
    
    # Score calculation
    required_score = (required_overlap / len(required_skills)) * 70
    preferred_score = (preferred_overlap / len(preferred_skills)) * 30
    
    return round(required_score + preferred_score, 2)


def generate_dataset(num_positive=50, num_negative=50, output_dir='training_data'):
    """
    Generate synthetic training dataset
    
    Args:
        num_positive: Number of matching resume-JD pairs
        num_negative: Number of non-matching resume-JD pairs
        output_dir: Directory to save dataset
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    dataset = []
    
    # Generate positive examples (matching pairs)
    print(f"Generating {num_positive} positive examples...")
    for i in range(num_positive):
        # Match resume to similar JD
        resume_idx = i % len(RESUME_TEMPLATES)
        jd_idx = resume_idx  # Same or similar role
        
        resume = RESUME_TEMPLATES[resume_idx]
        jd = JOB_TEMPLATES[jd_idx]
        
        resume_text = generate_resume_text(resume)
        jd_text = generate_jd_text(jd)
        match_score = calculate_match_score(resume, jd)
        
        dataset.append({
            'id': f'pos_{i}',
            'resume_text': resume_text,
            'jd_text': jd_text,
            'score': match_score,
            'label': 1 if match_score >= 50 else 0,
            'resume_role': resume['role'],
            'jd_title': jd['title']
        })
    
    # Generate negative examples (non-matching pairs)
    print(f"Generating {num_negative} negative examples...")
    for i in range(num_negative):
        # Mismatch resume to unrelated JD
        resume_idx = random.randint(0, len(RESUME_TEMPLATES) - 1)
        jd_idx = random.randint(0, len(JOB_TEMPLATES) - 1)
        
        # Ensure they're different roles
        while abs(resume_idx - jd_idx) <= 1:
            jd_idx = random.randint(0, len(JOB_TEMPLATES) - 1)
        
        resume = RESUME_TEMPLATES[resume_idx]
        jd = JOB_TEMPLATES[jd_idx]
        
        resume_text = generate_resume_text(resume)
        jd_text = generate_jd_text(jd)
        match_score = calculate_match_score(resume, jd)
        
        dataset.append({
            'id': f'neg_{i}',
            'resume_text': resume_text,
            'jd_text': jd_text,
            'score': match_score,
            'label': 1 if match_score >= 50 else 0,
            'resume_role': resume['role'],
            'jd_title': jd['title']
        })
    
    # Shuffle dataset
    random.shuffle(dataset)
    
    # Save as JSON
    json_path = output_path / 'resume_jd_dataset.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON dataset to {json_path}")
    
    # Save as CSV
    csv_path = output_path / 'resume_jd_dataset.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'resume_text', 'jd_text', 'score', 'label', 'resume_role', 'jd_title'])
        writer.writeheader()
        writer.writerows(dataset)
    print(f"✓ Saved CSV dataset to {csv_path}")
    
    # Generate statistics
    stats = {
        'total_samples': len(dataset),
        'positive_samples': sum(1 for d in dataset if d['label'] == 1),
        'negative_samples': sum(1 for d in dataset if d['label'] == 0),
        'average_score': sum(d['score'] for d in dataset) / len(dataset),
        'unique_roles': len(set(d['resume_role'] for d in dataset)),
        'unique_jd_titles': len(set(d['jd_title'] for d in dataset))
    }
    
    stats_path = output_path / 'dataset_stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved statistics to {stats_path}")
    
    print("\n=== Dataset Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return dataset


def create_sample_files(output_dir='training_data/samples'):
    """Create sample resume and JD files for testing"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create sample resumes
    for i, template in enumerate(RESUME_TEMPLATES[:3]):
        resume_text = generate_resume_text(template)
        file_path = output_path / f"resume_{i+1}_{template['role'].replace(' ', '_').lower()}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(resume_text)
        print(f"✓ Created {file_path}")
    
    # Create sample JDs
    for i, template in enumerate(JOB_TEMPLATES[:3]):
        jd_text = generate_jd_text(template)
        file_path = output_path / f"jd_{i+1}_{template['title'].replace(' ', '_').lower()}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(jd_text)
        print(f"✓ Created {file_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic resume-JD training dataset')
    parser.add_argument('--positive', type=int, default=50, help='Number of positive examples')
    parser.add_argument('--negative', type=int, default=50, help='Number of negative examples')
    parser.add_argument('--output', type=str, default='training_data', help='Output directory')
    parser.add_argument('--samples', action='store_true', help='Also create sample files')
    
    args = parser.parse_args()
    
    # Generate dataset
    dataset = generate_dataset(
        num_positive=args.positive,
        num_negative=args.negative,
        output_dir=args.output
    )
    
    # Create sample files if requested
    if args.samples:
        print("\n=== Creating Sample Files ===")
        create_sample_files(output_dir=f"{args.output}/samples")
    
    print("\n✅ Dataset generation complete!")
