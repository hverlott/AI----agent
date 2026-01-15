import os
import json
import time
import argparse
from typing import List, Dict

# 假设使用 OpenAI 官方库
try:
    from openai import OpenAI
except ImportError:
    print("Error: 'openai' package is required. Install with 'pip install openai'")
    exit(1)

def load_training_data(data_path: str) -> List[Dict]:
    """
    加载并验证 JSONL 格式的训练数据
    """
    dataset = []
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return []
        
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    # 简单验证格式: {"messages": [...]}
                    if "messages" in item and isinstance(item["messages"], list):
                        dataset.append(item)
    except Exception as e:
        print(f"Error loading data: {e}")
        return []
        
    print(f"Loaded {len(dataset)} valid training examples.")
    return dataset

def upload_file(client: OpenAI, file_path: str):
    print(f"Uploading file: {file_path}...")
    try:
        response = client.files.create(
            file=open(file_path, "rb"),
            purpose="fine-tune"
        )
        print(f"File uploaded successfully. ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

def start_finetuning_job(client: OpenAI, file_id: str, model: str, suffix: str = None):
    print(f"Starting fine-tuning job for model: {model}...")
    try:
        response = client.fine_tuning.jobs.create(
            training_file=file_id,
            model=model,
            suffix=suffix
        )
        print(f"Job started successfully. Job ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"Job creation failed: {e}")
        return None

def monitor_job(client: OpenAI, job_id: str):
    print(f"Monitoring job {job_id}...")
    while True:
        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            print(f"Status: {status}")
            
            if status in ["succeeded", "failed", "cancelled"]:
                if status == "succeeded":
                    print(f"Fine-tuning completed! New model: {job.fine_tuned_model}")
                else:
                    print(f"Fine-tuning failed with status: {status}")
                    if job.error:
                        print(f"Error: {job.error}")
                break
                
            time.sleep(10) # Check every 10s
        except Exception as e:
            print(f"Error checking status: {e}")
            break

def main():
    parser = argparse.ArgumentParser(description="OpenAI Fine-tuning Tool")
    parser.add_argument("--data", required=True, help="Path to training data (JSONL)")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Base model to fine-tune")
    parser.add_argument("--api_key", help="OpenAI API Key (optional, defaults to env OPENAI_API_KEY)")
    parser.add_argument("--suffix", help="Suffix for the fine-tuned model name")
    parser.add_argument("--no_wait", action="store_true", help="Don't wait for job completion")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API Key is required.")
        exit(1)
        
    client = OpenAI(api_key=api_key)
    
    # 1. Load Data
    data = load_training_data(args.data)
    if not data:
        exit(1)
        
    # 2. Upload File
    file_id = upload_file(client, args.data)
    if not file_id:
        exit(1)
        
    # 3. Start Job
    job_id = start_finetuning_job(client, file_id, args.model, args.suffix)
    if not job_id:
        exit(1)
        
    # 4. Monitor (Optional)
    if not args.no_wait:
        monitor_job(client, job_id)
    else:
        print(f"Job {job_id} is running in background. You can check status later.")

if __name__ == "__main__":
    main()
