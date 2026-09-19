from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.models import AuditLog


def write_audit_log(
    db: Session,
    action: str,
    entity: str,
    entity_id: str,
    actor_id: str | None = None,
) -> None:
    audit_log = AuditLog(
        id=str(uuid4()),
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
    )

    db.add(audit_log)
    # raise RuntimeError("TEST: force audit failure")