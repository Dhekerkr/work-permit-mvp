from fastapi import HTTPException

TRANSITIONS = {
    "submit": ({"DRAFT"}, "PENDING_APPROVAL"),
    "approve": ({"PENDING_APPROVAL"}, "ACTIVE"),
    "reject": ({"PENDING_APPROVAL"}, "REJECTED"),
    "activate": ({"PENDING_APPROVAL"}, "ACTIVE"),
    "suspend": ({"ACTIVE"}, "SUSPENDED"),
    "resume": ({"SUSPENDED"}, "ACTIVE"),
    "complete": ({"ACTIVE"}, "COMPLETED"),
    "close": ({"COMPLETED"}, "CLOSED"),
}

def transition(status: str, action: str) -> str:
    allowed, target = TRANSITIONS[action]
    if status not in allowed:
        raise HTTPException(409, f"Transition impossible: {status} → {action}")
    return target

def validate_submission(permit):
    missing = []
    for attr, label in [("contractor", "entreprise"), ("responsible_person", "responsable"), ("work_description", "description")]:
        if not getattr(permit, attr): missing.append(label)
    if not permit.work_types: missing.append("type de travaux")
    if not permit.planned_start_at: missing.append("début prévu")
    if not permit.expires_at: missing.append("fin de validité")
    if missing:
        raise HTTPException(422, "Champs requis: " + ", ".join(missing))
    if permit.expires_at <= permit.planned_start_at:
        raise HTTPException(422, "La fin de validité doit suivre le début prévu")

