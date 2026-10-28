"""Notification service. Sending external notifications containing incident
data requires approval; this service persists notifications and exposes a send
interface that callers gate on approval.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.all import Notification, User


def create_notification(
    db: Session,
    *,
    user_id: Optional[str],
    type: str,
    title: str,
    message: str,
) -> Notification:
    note = Notification(user_id=user_id, type=type, title=title, message=message)
    db.add(note)
    db.flush()
    return note


def mark_read(db: Session, notification_id: str) -> Optional[Notification]:
    note = db.get(Notification, notification_id)
    if not note:
        return None
    note.is_read = True
    db.add(note)
    db.flush()
    return note
