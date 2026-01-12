import uvicorn
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
from auditor import Auditor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="AI Audit Service", description="双机拦截架构 - 审核服务")
auditor = None

class AuditRequest(BaseModel):
    user_input: str
    draft_reply: str
    history: list

@app.on_event("startup")
async def startup_event():
    global auditor
    logging.info("Initializing Auditor...")
    try:
        auditor = Auditor()
        logging.info("Auditor initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Auditor: {e}")
        raise e

@app.post("/audit")
async def audit_endpoint(request: AuditRequest, x_superadmin_key: str = Header(None)):
    expected = os.getenv("SUPERADMIN_KEY") or ""
    if not expected or x_superadmin_key != expected:
        raise HTTPException(status_code=403, detail="需superAdmin权限")
    if not auditor:
        raise HTTPException(status_code=503, detail="Auditor not initialized")
    try:
        result = await auditor.audit_content(request.user_input, request.draft_reply, request.history)
        return result.to_dict()
    except Exception as e:
        logging.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check(x_superadmin_key: str = Header(None)):
    expected = os.getenv("SUPERADMIN_KEY") or ""
    if not expected or x_superadmin_key != expected:
        raise HTTPException(status_code=403, detail="需superAdmin权限")
    return {"status": "ok", "model": auditor.model_name if auditor else "unknown"}

if __name__ == "__main__":
    port = int(os.getenv("AUDIT_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
