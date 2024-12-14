# AI Job Market Analysis

A data-driven tool for analyzing AI job market trends and identifying startup opportunities using natural language processing and machine learning.

## Project Structure

```
project_2025/
├── data/
│   ├── raw/           # Raw job posting data
│   └── processed/     # Processed and cleaned data
├── src/
│   ├── analysis/      # Analysis modules
│   │   ├── cluster_analysis.py
│   │   └── llm_analysis.py
│   ├── data/          # Data handling modules
│   │   └── embeddings.py
│   └── parser/        # Text parsing modules
│       └── job_parser.py
├── vector_db/         # Vector database storage
├── requirements.txt   # Project dependencies
└── README.md
```

## Features

- Job posting text analysis and metric extraction
- Industry and use case pattern recognition
- Vector embeddings using OpenAI's embedding model
- Clustering analysis for identifying job market segments
- Cross-cluster statistical analysis
- LLM-powered insights generation

## Requirements

- Python 3.9+
- OpenAI API key
- Dependencies listed in requirements.txt

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd project_2025
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export OPENAI_API_KEY='your-api-key'  # On Windows: set OPENAI_API_KEY=your-api-key
```

## Usage

1. Place your job postings data in `data/raw/job_descriptions.txt`
2. Run the analysis:
```python
from src.parser.job_parser import load_job_posts
from src.data.embeddings import setup_vector_db, embed_and_store_jobs, get_embeddings_data
from src.analysis.cluster_analysis import cluster_jobs_function, calculate_cluster_statistics

# Load and process job postings
jobs = load_job_posts('data/raw/job_descriptions.txt')

# Setup vector database and embed jobs
collection = setup_vector_db()
embed_and_store_jobs(jobs, collection)

# Get embeddings and perform clustering
data = get_embeddings_data(collection)
clusters, documents = cluster_jobs_function(data['embeddings'], data['documents'])

# Calculate statistics
stats = calculate_cluster_statistics(clusters)
```

## Components

### Parser Module
- `job_parser.py`: Handles loading and parsing job postings, extracting key metrics like industries and use cases.

### Data Module
- `embeddings.py`: Manages vector embeddings using OpenAI's API and ChromaDB for storage.

### Analysis Module
- `cluster_analysis.py`: Implements clustering and statistical analysis of job postings.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the embedding model
- ChromaDB for vector storage
- scikit-learn for clustering algorithms 