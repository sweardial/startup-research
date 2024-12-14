# Project 2025: AI Job Market Analysis Suite

A comprehensive suite for collecting and analyzing AI job market data to identify startup opportunities.

## Components

### 1. Chrome Extension (`/chrome_extension`)
A browser extension for automatically collecting job postings data from various job boards.

Features:
- Automatic job posting detection
- Data extraction from job descriptions
- Local server for data storage
- Easy-to-use popup interface

[Learn more about the Chrome Extension](./chrome_extension/README.md)

### 2. Market Analyzer (`/job_market_analyzer`)
A Python-based analysis tool that processes collected job data to identify market trends and opportunities.

Features:
- Text analysis and metric extraction
- Vector embeddings and clustering
- Industry pattern recognition
- LLM-powered insights generation

[Learn more about the Market Analyzer](./job_market_analyzer/README.md)

## Workflow

1. Use the Chrome Extension to collect job postings data
2. Data is saved to a local file
3. Run the Market Analyzer to process the data
4. Review generated insights and visualizations

## Getting Started

1. Set up the Chrome Extension:
```bash
cd chrome_extension
npm install
```

2. Set up the Market Analyzer:
```bash
cd job_market_analyzer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your OpenAI API key in `job_market_analyzer/.env`

## License

This project is licensed under the MIT License - see the LICENSE file for details.