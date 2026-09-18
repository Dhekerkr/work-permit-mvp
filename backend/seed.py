from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import AuditLog, Permit, User

USERS = [
    ("Ahmed Ben Salah", "PROD001", "production@agil.tn", "PRODUCTION"),
    ("Leïla Trabelsi", "HSE001", "hse@agil.tn", "HSE"),
    ("Sami Gharbi", "PREST001", "prestataire@agil.tn", "PRESTATAIRE"),
    ("Administrateur AGIL", "ADMIN001", "admin@agil.tn", "ADMIN"),
]
WORK_TYPES = ["HOT_WORK", "WELDING", "CUTTING", "GRINDING", "MECHANICAL", "ELECTRICAL", "HEIGHT", "CONFINED_SPACE", "OTHER"]

def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.scalar(select(User).limit(1)):
            for name, matricule, email, role in USERS:
                db.add(User(name=name, matricule=matricule, email=email, role=role, password_hash=hash_password("Demo123!")))
            db.commit()
        users = {u.role: u for u in db.scalars(select(User))}
        if not db.scalar(select(Permit).limit(1)):
            now = datetime.now(timezone.utc)
            samples = [
                ("DRAFT", "Maintenance vanne GPL", ["MECHANICAL"]),
                ("PENDING_APPROVAL", "Soudage support métallique", ["WELDING"]),
                ("ACTIVE", "Contrôle armoire électrique", ["ELECTRICAL"]),
                ("SUSPENDED", "Découpe tuyauterie hors service", ["CUTTING"]),
                ("REJECTED", "Intervention en hauteur", ["HEIGHT"]),
                ("COMPLETED", "Remplacement joint de pompe", ["MECHANICAL"]),
                ("CLOSED", "Meulage d'un support", ["GRINDING"]),
            ]
            for i, (status, description, types) in enumerate(samples, 1):
                creator = users["PRODUCTION"]
                p = Permit(permit_number=f"PT-{now.year}-{i:04d}", permit_date=date.today() - timedelta(days=i-1), site="AGIL Gaz Radès", work_location="Zone " + chr(64+i), contractor="SOTUMEC Services", responsible_person="Nabil Mansour", work_description=description, work_types=types, safety_checks=[{"code": f"S{n}", "checked": status != "DRAFT", "comment": ""} for n in range(1,10)], gas_measurement={"applicable": i % 2 == 0, "measuredAt": now.isoformat(), "o2": 20.8, "lel": 0.0, "performedBy": "Leïla Trabelsi", "comment": "Valeurs consignées sans décision automatique"} if i % 2 == 0 else {"applicable": False}, hot_work_checks=[{"code": f"H{n}", "checked": True, "comment": ""} for n in range(1,7)] if types[0] in {"WELDING","CUTTING","GRINDING","HOT_WORK"} else [], planned_start_at=now - timedelta(hours=1), expires_at=now + timedelta(hours=7), status=status, rejection_reason="Zone non libérée pour l'intervention" if status == "REJECTED" else None, closure_checks=[{"code": f"C{n}", "checked": True} for n in range(1,6)] if status in {"COMPLETED","CLOSED"} else [], created_by_id=creator.id)
                db.add(p); db.flush()
                db.add(AuditLog(permit_id=p.id, user_id=creator.id, user_name=creator.name, action="PERMIT_CREATED", details="Donnée de démonstration", new_status=status))
            db.commit()
        print("Seed terminé. Mot de passe commun: Demo123!")
    finally:
        db.close()

if __name__ == "__main__": seed()

