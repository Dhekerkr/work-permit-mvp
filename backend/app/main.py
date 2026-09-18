from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from .auth import create_token, current_user, require_roles, verify_password
from .database import Base, engine, get_db
from .models import AuditLog, Permit, User
from .schemas import CommentIn, CompletionIn, LoginIn, PermitCreate, PermitOut, PermitUpdate, TokenOut, UserOut
from .workflow import transition, validate_submission

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="Permis de Travail API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def audit(db: Session, permit: Permit, user: User, action: str, details: str | None = None, previous: str | None = None, new: str | None = None):
    db.add(AuditLog(permit_id=permit.id, user_id=user.id, user_name=user.name, action=action, details=details, previous_status=previous, new_status=new))

def query_permit(db: Session, permit_id: int) -> Permit:
    permit = db.scalar(select(Permit).options(selectinload(Permit.creator), selectinload(Permit.audit_logs)).where(Permit.id == permit_id))
    if not permit: raise HTTPException(404, "Permis introuvable")
    return permit

def permit_number(db: Session) -> str:
    year = datetime.now().year
    latest = db.scalar(select(func.max(Permit.id))) or 0
    return f"PT-{year}-{latest + 1:04d}"

@app.get("/api/health")
def health(): return {"status": "ok"}

@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(or_(User.email == data.identifier, User.matricule == data.identifier)))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": create_token(user), "user": user}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@app.get("/api/permits", response_model=list[PermitOut])
def list_permits(status: Optional[str] = None, search: Optional[str] = None, work_type: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = select(Permit).options(selectinload(Permit.creator), selectinload(Permit.audit_logs)).order_by(Permit.created_at.desc())
    if status: q = q.where(Permit.status == status)
    if search:
        term = f"%{search}%"
        q = q.where(or_(Permit.permit_number.ilike(term), Permit.contractor.ilike(term), Permit.responsible_person.ilike(term), Permit.work_description.ilike(term)))
    if work_type: q = q.where(Permit.work_types.contains(work_type))
    if date_from: q = q.where(Permit.permit_date >= date_from)
    if date_to: q = q.where(Permit.permit_date <= date_to)
    return list(db.scalars(q).unique())

@app.post("/api/permits", response_model=PermitOut)
def create_permit(data: PermitCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("PRODUCTION", "HSE", "PRESTATAIRE", "ADMIN"))):
    values = data.model_dump(exclude_none=True)
    values.setdefault("permit_date", date.today())
    permit = Permit(**values, permit_number=permit_number(db), created_by_id=user.id)
    db.add(permit); db.flush()
    audit(db, permit, user, "PERMIT_CREATED", "Brouillon créé", None, "DRAFT")
    db.commit()
    return query_permit(db, permit.id)

@app.get("/api/permits/{permit_id}", response_model=PermitOut)
def get_permit(permit_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return query_permit(db, permit_id)

@app.patch("/api/permits/{permit_id}", response_model=PermitOut)
def update_permit(permit_id: int, data: PermitUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    permit = query_permit(db, permit_id)
    if permit.status != "DRAFT": raise HTTPException(409, "Seul un brouillon peut être modifié")
    if permit.created_by_id != user.id and user.role != "ADMIN": raise HTTPException(403, "Vous ne pouvez pas modifier ce brouillon")
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(permit, key, value)
    audit(db, permit, user, "DRAFT_UPDATED", "Brouillon enregistré")
    db.commit(); return query_permit(db, permit.id)

def set_status(db: Session, permit: Permit, user: User, action: str, label: str, details: str | None = None):
    old = permit.status; permit.status = transition(old, action)
    audit(db, permit, user, label, details, old, permit.status)

@app.post("/api/permits/{permit_id}/submit", response_model=PermitOut)
def submit(permit_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("PRODUCTION", "HSE", "PRESTATAIRE", "ADMIN"))):
    permit = query_permit(db, permit_id)
    if permit.created_by_id != user.id and user.role != "ADMIN": raise HTTPException(403, "Seul le créateur peut soumettre ce permis")
    validate_submission(permit); set_status(db, permit, user, "submit", "PERMIT_SUBMITTED", "Envoyé pour validation HSE")
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/approve", response_model=PermitOut)
def approve(permit_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("HSE", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "approve", "PERMIT_APPROVED", "Validation humaine explicite")
    permit.approval = {"by": user.name, "byId": user.id, "decidedAt": datetime.now(timezone.utc).isoformat(), "decision": "APPROVED"}
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/activate", response_model=PermitOut)
def activate(permit_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("PRODUCTION", "HSE", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "activate", "PERMIT_ACTIVATED", "Activation explicite")
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/reject", response_model=PermitOut)
def reject(permit_id: int, data: CommentIn, db: Session = Depends(get_db), user: User = Depends(require_roles("HSE", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "reject", "PERMIT_REJECTED", data.comment)
    permit.rejection_reason = data.comment; permit.approval = {"by": user.name, "decision": "REJECTED", "comment": data.comment, "decidedAt": datetime.now(timezone.utc).isoformat()}
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/suspend", response_model=PermitOut)
def suspend(permit_id: int, data: CommentIn, db: Session = Depends(get_db), user: User = Depends(require_roles("HSE", "PRODUCTION", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "suspend", "PERMIT_SUSPENDED", data.comment)
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/resume", response_model=PermitOut)
def resume(permit_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("HSE", "PRODUCTION", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "resume", "PERMIT_RESUMED")
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/complete", response_model=PermitOut)
def complete(permit_id: int, data: CompletionIn, db: Session = Depends(get_db), user: User = Depends(require_roles("PRODUCTION", "PRESTATAIRE", "HSE", "ADMIN"))):
    permit = query_permit(db, permit_id)
    if not data.checks or not all(x.get("checked") for x in data.checks): raise HTTPException(422, "Toutes les vérifications de fin de travaux doivent être confirmées")
    set_status(db, permit, user, "complete", "WORK_COMPLETED"); permit.closure_checks = data.checks; permit.completed_at = datetime.now(timezone.utc)
    db.commit(); return query_permit(db, permit.id)

@app.post("/api/permits/{permit_id}/close", response_model=PermitOut)
def close(permit_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("HSE", "PRODUCTION", "ADMIN"))):
    permit = query_permit(db, permit_id); set_status(db, permit, user, "close", "PERMIT_CLOSED", "Clôture finale validée")
    permit.closed_at = datetime.now(timezone.utc); db.commit(); return query_permit(db, permit.id)

@app.get("/api/dashboard/stats")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    counts = dict(db.execute(select(Permit.status, func.count(Permit.id)).group_by(Permit.status)).all())
    today = db.scalar(select(func.count(Permit.id)).where(Permit.permit_date == date.today())) or 0
    recent = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(8)))
    return {"counts": counts, "today": today, "recentActivity": [{"id": x.id, "permitId": x.permit_id, "user": x.user_name, "action": x.action, "details": x.details, "createdAt": x.created_at} for x in recent]}

