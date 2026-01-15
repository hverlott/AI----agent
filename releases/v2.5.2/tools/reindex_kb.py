import os
import sys
import pickle
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.database import db

def load_env(tenant_id):
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / "data" / "tenants" / tenant_id / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

def load_rag_config(tenant_id):
    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "data" / "tenants" / tenant_id / "platforms" / "telegram" / "rag_config.json"
    conf = {"embedding_model_id": "text-embedding-3-small"}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("embedding_model_id"):
                    conf["embedding_model_id"] = data["embedding_model_id"]
        except:
            pass
    return conf

def get_embedding(client, text, model="text-embedding-3-small"):
    try:
        text = text.replace("\n", " ")
        if ":" in model:
            model = model.split(":", 1)[1]
        return client.embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        print(f"Error embedding text: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Reindex Knowledge Base (Generate Embeddings)")
    parser.add_argument("--tenant", required=True, help="Tenant ID")
    args = parser.parse_args()

    load_env(args.tenant)
    rag_conf = load_rag_config(args.tenant)
    embed_model = rag_conf["embedding_model_id"]
    print(f"Using embedding model: {embed_model}")
    
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL")
    
    if not api_key:
        print("Error: AI_API_KEY not found.")
        return

    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Load KB items from DB
    items = db.get_kb_items(args.tenant)
    print(f"Found {len(items)} KB items for tenant {args.tenant}")
    
    vectors = {}
    
    # Output path
    base_dir = Path(__file__).resolve().parent.parent
    chroma_dir = base_dir / "data" / "tenants" / args.tenant / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    vector_path = chroma_dir / "vectors.pkl"
    
    # Load existing if any
    if vector_path.exists():
        try:
            with open(vector_path, "rb") as f:
                vectors = pickle.load(f)
            print(f"Loaded {len(vectors)} existing vectors.")
        except:
            pass

    updated_count = 0
    for it in items:
        vid = str(it.get("id"))
        content = f"{it.get('title','')} {it.get('content','')}"
        
        if vid in vectors:
            # Skip if already exists (naive check, doesn't check for content updates)
            # Ideally we should hash content, but for now simple id check
            continue
            
        print(f"Embedding item {vid}...")
        vec = get_embedding(client, content, model=embed_model)
        if vec:
            vectors[vid] = vec
            updated_count += 1
            
    if updated_count > 0:
        with open(vector_path, "wb") as f:
            pickle.dump(vectors, f)
        print(f"Saved {len(vectors)} vectors to {vector_path}")
    else:
        print("No new items to index.")

if __name__ == "__main__":
    main()
