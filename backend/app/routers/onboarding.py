from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_role
from app.store import store

router = APIRouter()


@router.post("/{worker_id}/submit-document")
async def submit_verification_document(worker_id: str, document_type: str, document_file: UploadFile = File(...)):
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    document = {"type": document_type, "filename": document_file.filename}
    worker.setdefault("documents", []).append(document)
    return {"status": "submitted", "document_type": document_type, "worker": store.get_worker(worker_id)}


@router.get("/{worker_id}/verification-status")
async def get_verification_status(worker_id: str):
    worker = store.get_worker(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"worker_id": worker_id, "is_verified": worker["is_verified"], "documents": worker.get("documents", []), "created_at": worker["created_at"]}


@router.post("/{worker_id}/approve")
async def approve_worker(worker_id: str, notes: str = "", _admin=Depends(require_role("admin"))):
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker["is_verified"] = True
    worker["approval_notes"] = notes
    return {"status": "approved", "worker": store.get_worker(worker_id)}


@router.post("/{worker_id}/reject")
async def reject_worker(worker_id: str, reason: str, _admin=Depends(require_role("admin"))):
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker["is_verified"] = False
    worker["rejection_reason"] = reason
    return {"status": "rejected", "success": True}


@router.get("/pending-verifications")
async def get_pending_verifications(limit: int = 10, _admin=Depends(require_role("admin"))):
    workers = [worker for worker in store.list_workers() if not worker["is_verified"]]
    return {"count": len(workers[:limit]), "workers": workers[:limit]}


@router.put("/{worker_id}/profile")
async def update_worker_profile(worker_id: str, name: str | None = None, email: str | None = None, service_types: list | None = None):
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if name is not None:
        worker["name"] = name
    if service_types:
        worker["service_type"] = service_types[0]
    return store.get_worker(worker_id)
