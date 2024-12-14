import json
import os
import time
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, TypedDict

import chromadb
import dotenv
import numpy as np
from chromadb.utils import embedding_functions
from openai import OpenAI
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

dotenv.load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

class JobMetrics(TypedDict):
    industries: Counter
    use_cases: Counter

INDUSTRY_KEYWORDS = {
    'healthcare': ['healthcare', 'medical', 'hospital', 'clinical', 'health'],
    'finance': ['finance', 'banking', 'insurance', 'fintech', 'trading'],
    'retail': ['retail', 'e-commerce', 'shopping', 'marketplace'],
    'real_estate': ['real estate', 'property', 'housing', 'rental'],
    'education': ['education', 'learning', 'teaching', 'academic'],
    'manufacturing': ['manufacturing', 'industrial', 'factory', 'production'],
    'agriculture': ['agriculture', 'farming', 'crop', 'agricultural'],
}

def setup_vector_db():
    """Setup ChromaDB with OpenAI embeddings."""
    client = chromadb.PersistentClient(path="./vector_db")
    try:
        collection = client.get_collection("job_postings", embedding_function=openai_ef)
    except:
        collection = client.create_collection("job_postings", embedding_function=openai_ef)
    return collection

def embed_and_store_jobs(jobs: List[str], collection) -> List[str]:
    """Embed and store job postings in vector DB."""
    try:
        existing_count = collection.count()
        if existing_count > 0:
            print(f"Found {existing_count} existing embeddings, skipping embedding step...")
            return [f"job_{i}" for i in range(existing_count)]
    except Exception as e:
        print(f"Error checking existing embeddings: {str(e)}")
    
    ids = [f"job_{i}" for i in range(len(jobs))]
    
    batch_size = 100
    for i in tqdm(range(0, len(jobs), batch_size), desc="Embedding jobs"):
        batch_ids = ids[i:i + batch_size]
        batch_jobs = jobs[i:i + batch_size]
        collection.add(
            documents=batch_jobs,
            ids=batch_ids
        )
    
    return ids

def get_embeddings_data(collection):
    """Get all embeddings and documents from collection."""
    try:
        all_ids = [f"job_{i}" for i in range(collection.count())]
        
        data = collection.get(
            ids=all_ids,
            include=["embeddings", "documents"]
        )
        
        if len(data["embeddings"]) == 0:
            raise ValueError("No embeddings found in collection")
            
        print(f"Retrieved {len(data['embeddings'])} embeddings and {len(data['documents'])} documents")
        return data
    except Exception as e:
        print(f"Error retrieving embeddings: {str(e)}")
        raise

def cluster_jobs_function(collection, n_clusters: int = 10):
    """Cluster job postings based on their embeddings."""
    try:
        all_data = get_embeddings_data(collection)
        embeddings = np.array(all_data["embeddings"])
        documents = all_data["documents"]
        
        if len(documents) == 0:
            raise ValueError("No documents found in collection")
            
        print(f"Clustering {len(documents)} documents into {n_clusters} clusters...")
        
        scaler = StandardScaler()
        normalized_embeddings = scaler.fit_transform(embeddings)
        
        kmeans = KMeans(n_clusters=min(n_clusters, len(documents)), random_state=42)
        clusters = kmeans.fit_predict(normalized_embeddings)
        
        return clusters, documents
    except Exception as e:
        print(f"Error in clustering: {str(e)}")
        raise

def extract_job_metrics(text: str) -> JobMetrics:
    metrics = JobMetrics(
        platforms=Counter(),
        industries=Counter(),
        use_cases=Counter(),
    )
    
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(keyword in text.lower() for keyword in keywords):
            metrics['industries'][industry] += 1
    
    use_case_patterns = [
        r'(?:to|for) (automate|improve|enhance|optimize|streamline) ([\w\s]+)',
        r'(?:building|developing|creating) (?:an?|the) ([\w\s]+) (?:system|solution|platform|tool)',
        r'(?:help|assist|enable) (?:us|clients|customers) (?:to|with) ([\w\s]+)'
    ]
    for pattern in use_case_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            metrics['use_cases'][match.group(0).strip().lower()] += 1
    
    
    return metrics

def calculate_cluster_statistics(cluster_analyses: List[Dict]) -> Dict:
    stats = {
        "industry_distribution": defaultdict(lambda: defaultdict(int)),
        "cluster_sizes": [],
        "technology_dominance": [],
        "industry_dominance": [],
        "cross_cluster_patterns": []
    }
    
    if not cluster_analyses:
        return stats
    
    try:
        total_jobs = sum(analysis.get("metrics", {}).get("total_jobs", 0) for analysis in cluster_analyses)
        
        for cluster_idx, analysis in enumerate(cluster_analyses):
            metrics = analysis.get("metrics", {})
            cluster_size = metrics.get("total_jobs", 0)
            stats["cluster_sizes"].append({
                "cluster_id": cluster_idx,
                "size": cluster_size,
                "percentage": (cluster_size / total_jobs) * 100 if total_jobs > 0 else 0
            })
            
            for industry, count in metrics.get("top_industries", {}).items():
                stats["industry_distribution"][industry][cluster_idx] = count
    
        for industry, cluster_counts in stats["industry_distribution"].items():
            if cluster_counts:
                max_cluster = max(cluster_counts.items(), key=lambda x: x[1])
                cluster_size = next((size["size"] for size in stats["cluster_sizes"] if size["cluster_id"] == max_cluster[0]), 0)
                stats["industry_dominance"].append({
                    "industry": industry,
                    "dominant_cluster": max_cluster[0],
                    "count": max_cluster[1],
                    "percentage": (max_cluster[1] / cluster_size) * 100 if cluster_size > 0 else 0
                })
    except Exception as e:
        print(f"Error in calculate_cluster_statistics: {str(e)}")
        return stats
    
    return stats

def ensure_valid_json(response_text: str) -> Dict:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        return {
            "error": "Failed to parse GPT response as JSON",
            "raw_response": response_text,
            "fallback_analysis": {
                "primary_opportunity": {
                    "name": "Error in analysis",
                    "description": "Failed to parse model response",
                    "target_market": "Unknown",
                    "required_technologies": [],
                    "competitive_advantage": "Unknown"
                },
                "market_validation": {
                    "demand_signals": [],
                    "skill_requirements": [],
                    "target_industries": []
                }
            }
        }

def log_openai_interaction(filename: str, messages: List[Dict[str, str]], response: str):
    """Append the request messages and response to a log file."""
    entry = {
        "request": messages,
        "response": response
    }
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n\n")

def analyze_cluster_with_metrics(jobs: List[str], total_jobs: int) -> Dict:
    cluster_metrics = JobMetrics(
        industries=Counter(),
        use_cases=Counter(),
    )
    
    for job in jobs:
        metrics = extract_job_metrics(job)
        for key in cluster_metrics.keys():
            cluster_metrics[key].update(metrics[key])
    
    metrics_summary = {
        "total_jobs": len(jobs),
        "top_industries": dict(cluster_metrics["industries"].most_common(3)),
        "top_use_cases": dict(cluster_metrics["use_cases"].most_common(5)),
    }
    
    metrics_summary["percentages"] = {
        "cluster_size": (len(jobs) / total_jobs) * 100 if total_jobs > 0 else 0,
        "industry_share": {
            industry: (count / len(jobs)) * 100 if len(jobs) > 0 else 0
            for industry, count in metrics_summary["top_industries"].items()
        },
    }
    
    top_industry = list(metrics_summary['top_industries'].items())
    top_industry_name = top_industry[0][0] if top_industry else "No dominant industry"
    top_industry_share = list(metrics_summary['percentages']['industry_share'].values())[0] if metrics_summary['percentages']['industry_share'] else 0

    initial_prompt = f"""Analyze this cluster of {len(jobs)} job postings (representing {metrics_summary['percentages']['cluster_size']:.1f}% of total dataset) based on the following metrics:

Cluster Statistics:
{json.dumps(metrics_summary, indent=2)}

Key Observations:
- Dominant industry: {top_industry_name} ({top_industry_share:.1f}% of cluster jobs)

Based on these specific metrics, identify:
1. The most promising and concrete business opportunity
2. Specific pain points that aren't well-addressed by existing solutions
3. Technical requirements and implementation approach
4. Target market and user personas
5. Potential competitive advantages

Focus on being extremely specific. Reference actual technologies, skills, and use cases from the data.
Include specific percentages and numbers in your analysis.

Respond in JSON format:
{{
    "primary_opportunity": {{
        "description": "Detailed description referencing specific use cases",
        "target_market": "Specific industry/user segment based on the data",
        "competitive_advantage": "Specific advantage based on market gaps in the data"
    }},
    "market_validation": {{
        "target_industries": ["List specific industries showing interest"]
    }}
}}"""

    try:
        initial_messages = [
            {"role": "system", "content": "You are a startup advisor with deep technical expertise. Focus on concrete, actionable insights based solely on the provided data. IMPORTANT: Your response must be valid JSON."},
            {"role": "user", "content": initial_prompt}
        ]
        initial_prompt_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=initial_messages,
            temperature=0.2,
        )
        
        # Log request/initial_prompt_response
        log_openai_interaction('openai_initial_analysis.log', initial_messages, initial_prompt_response.choices[0].message.content)        
        
        
        time.sleep(5)
        validation_prompt = f"""Review this initial analysis and validate it against the data:

Initial Analysis:
{initial_prompt_response.choices[0].message.content}

Cluster Metrics:
{json.dumps(metrics_summary, indent=2)}

Identify any gaps or inconsistencies. Make the analysis more specific by:
1. Ensuring every claim is supported by the metrics
2. Adding specific numbers and percentages
3. Tying recommendations to actual job requirements
4. Identifying unique patterns in the data

Return a refined version of the analysis with additional validation metrics.
IMPORTANT: Your response must be valid JSON."""

        validation_messages = [
            {"role": "system", "content": "You are a data analyst validating startup opportunities. Be critical and ensure all insights are supported by data. IMPORTANT: Your response must be valid JSON."},
            {"role": "user", "content": validation_prompt}
        ]
        validation_prompt_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=validation_messages,
            temperature=0.1,
        )
        
        time.sleep(5000)
        # Log request/validation_prompt_response
        log_openai_interaction('openai_validation.log', validation_messages, validation_prompt_response.choices[0].message.content)

        validated_analysis = ensure_valid_json(validation_prompt_response.choices[0].message.content)
        
        return {
            "metrics": metrics_summary,
            "analysis": validated_analysis,
            "raw_metrics": {k: dict(v) for k, v in cluster_metrics.items()}
        }
    except Exception as e:
        print(f"Error in cluster analysis: {str(e)}")
        
        return {
            "metrics": metrics_summary,
            "analysis": {
                "error": f"Analysis failed: {str(e)}",
                "fallback_analysis": {
                    "primary_opportunity": {
                        "name": "Error in analysis",
                        "description": f"Analysis failed: {str(e)}",
                        "target_market": "Unknown",
                        "required_technologies": [],
                        "competitive_advantage": "Unknown"
                    }
                }
            },
            "raw_metrics": {k: dict(v) for k, v in cluster_metrics.items()}
        }

def perform_global_analysis(collection) -> Dict:
    try:
        print("Performing clustering...")
        cluster_results = cluster_jobs_function(collection)
        clusters, jobs = cluster_results
        cluster_analyses = []
        
        for i in tqdm(range(max(clusters) + 1), desc="Analyzing clusters"):
            cluster_jobs = [job for job, cluster in zip(jobs, clusters) if cluster == i]
            if cluster_jobs:
                analysis = analyze_cluster_with_metrics(cluster_jobs, len(jobs))
                analysis["cluster_id"] = i
                analysis["job_count"] = len(cluster_jobs)
                cluster_analyses.append(analysis)
        
        cross_cluster_stats = calculate_cluster_statistics(cluster_analyses)
        
        # Convert cross_cluster_stats and cluster_analyses to JSON-serializable format
        cross_cluster_stats_json = json.loads(json.dumps(cross_cluster_stats))
        cluster_analyses_json = json.loads(json.dumps(cluster_analyses))
        
        # Take first half of the data
        half_stats = json.dumps(cross_cluster_stats_json, indent=2)
        half_analyses = json.dumps(cluster_analyses_json, indent=2)
        
        synthesis_prompt = f"""Based on these cluster analyses and cross-cluster statistics, provide global insights about AI startup opportunities.

Cross-Cluster Statistics:
{half_stats}

Cluster Analyses:
{half_analyses}

Focus on:
1. Major market trends (with specific percentages and numbers)
2. Cross-cluster opportunities (especially where technologies/industries overlap)
3. Most promising startup directions (based on concrete demand signals)
4. Implementation strategies (referencing specific technology stacks)

Highlight:
- Industries with strong presence across multiple clusters
- Unique patterns in different market segments

Respond in JSON format:
{{
    "market_trends": [
        {{
            "trend": "Trend description",
            "supporting_data": "Specific numbers and percentages",
            "cluster_distribution": "Where this trend appears strongest"
        }}
    ],
    "cross_cluster_opportunities": [
        {{
            "description": "Description with specific metrics",
            "evidence": "Specific data points supporting this opportunity"
        }}
    ]
}}"""

        synthesis_messages = [
            {"role": "system", "content": "You are an expert at market analysis and startup opportunities. IMPORTANT: Your response must be valid JSON."},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        # Save synthesis prompt
        with open('openai_global_synthesis_prompt.json', 'w') as f:
            json.dump(synthesis_messages, f, indent=2)
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=synthesis_messages,
            temperature=0.2,
        )
        
        # Save response immediately
        with open('openai_global_synthesis_response.json', 'w') as f:
            json.dump(response.model_dump(), f, indent=2)
        
        global_insights = ensure_valid_json(response.choices[0].message.content)
        global_insights["cluster_analyses"] = cluster_analyses
        
        return global_insights
    except Exception as e:
        raise e


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    file_path = 'output/job_descriptions.txt'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    separator = '_____________\n'
    job_posts = [post.strip() for post in content.split(separator) if post.strip()]
    unique_jobs = list(set(job_posts))
    
    print(f"\nFound {len(unique_jobs)} unique job postings")
    
    print("\nSetting up vector database...")
    collection = setup_vector_db()
    
    print("\nPerforming global analysis...")
    global_analysis = perform_global_analysis(collection)
    
    with open('vector_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(global_analysis, f, indent=2, ensure_ascii=False)
    
    print("\nCreating visualizations...")
    
    print("\nAnalysis complete! Check 'vector_analysis_results.json' for results and the log files for request-response records.")

if __name__ == "__main__":
    main()
