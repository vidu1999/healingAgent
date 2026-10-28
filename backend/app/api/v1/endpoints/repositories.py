"""Repository endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.models.all import Repository, WorkflowRun
from app.services.github_adapter import GitHubAdapter
from app.schemas.github import RepositoryRegister
from app.schemas.incidents import RepositoryOut, WorkflowRunOut
from app.services.audit_service import record_audit

router = APIRouter()


@router.get("", response_model=list[RepositoryOut])
def list_repositories(current_user: object = Depends(get_current_user), db=Depends(get_db)):
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


@router.post("", response_model=RepositoryOut, status_code=status.HTTP_201_CREATED)
def register_repository(payload: RepositoryRegister, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    adapter = GitHubAdapter()
    if not adapter.is_configured():
        # Still allow registration but mark read-only; real metadata fetch skipped.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub integration not configured")
    if not adapter.is_allowed(payload.full_name):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Repository not on allowlist")
    try:
        meta = adapter.get_repository(payload.full_name)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    finally:
        adapter.close()
    repo = db.query(Repository).filter(Repository.full_name == payload.full_name).first()
    if repo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Repository already registered")
    repo = Repository(
        name=payload.full_name.split("/")[-1],
        full_name=payload.full_name,
        owner=payload.full_name.split("/")[0],
        default_branch=meta.get("default_branch", "main"),
        html_url=meta.get("html_url"),
        clone_url=payload.clone_url or meta.get("clone_url"),
        allow_write=bool(payload.allow_write and not settings.GITHUB_READ_ONLY),
    )
    db.add(repo)
    db.flush()
    record_audit(db, action="repository.register", resource=f"repository:{repo.id}", decision="success", result="registered", actor_user=current_user if hasattr(current_user, 'id') else None)
    return repo


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(repository_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    db.delete(repo)
    db.flush()
    return None


@router.get("/{repository_id}/workflows", response_model=list[WorkflowRunOut])
def repository_workflows(repository_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return db.query(WorkflowRun).filter(WorkflowRun.repository_id == repository_id).order_by(WorkflowRun.created_at.desc()).all()
