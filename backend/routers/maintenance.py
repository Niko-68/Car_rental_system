import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Car, Employee, Maintenance, Notification, User
from schemas import MaintenanceCreate, MaintenanceOut, NotificationOut
from security import require_employee

router = APIRouter(tags=["Maintenance"])

DUE_SOON_DAYS = 14


def _q(db: Session):
    return db.query(Maintenance).options(joinedload(Maintenance.car))


def _notify_all(db: Session, maintenance: Maintenance | None, subject: str, message: str):
    """One notification per employee, without duplicates (same subject + same maintenance)."""
    for emp in db.query(Employee).all():
        exists = db.query(Notification).filter(
            Notification.employee_id == emp.user_id, Notification.subject == subject,
            Notification.maintenance_id == (maintenance.id if maintenance else None)).first()
        if not exists:
            db.add(Notification(employee_id=emp.user_id, maintenance_id=maintenance.id if maintenance else None,
                                subject=subject, message=message))


# ---------- Maintenances ----------
@router.get("/maintenances", response_model=list[MaintenanceOut])
def list_maintenances(car_id: int | None = None, db: Session = Depends(get_db),
                      _: User = Depends(require_employee)):
    q = _q(db)
    if car_id:
        q = q.filter(Maintenance.car_id == car_id)
    return q.order_by(Maintenance.maintenance_date.desc()).all()


@router.post("/maintenances", response_model=MaintenanceOut, status_code=201)
def create_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db),
                       _: User = Depends(require_employee)):
    """Record a maintenance. If it takes place today or earlier, the car is set to
    'maintenance' (so it is excluded from listings) until PATCH /cars/{id}/status -> available."""
    car = db.get(Car, data.car_id)
    if not car:
        raise HTTPException(404, "Car not found")
    if data.maintenance_date <= dt.date.today() and car.status == "rented":
        raise HTTPException(409, "Car is currently rented")
    m = Maintenance(**data.model_dump())
    db.add(m)
    db.flush()
    if data.maintenance_date <= dt.date.today():
        car.status = "maintenance"
    _notify_all(db, m, f"Maintenance: {car.brand} {car.model} ({car.plate})",
                f"{data.maintenance_type} scheduled on {data.maintenance_date}")
    db.commit()
    return _q(db).filter(Maintenance.id == m.id).one()


@router.delete("/maintenances/{mid}", status_code=204)
def delete_maintenance(mid: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    m = db.get(Maintenance, mid)
    if not m:
        raise HTTPException(404, "Maintenance not found")
    db.delete(m)
    db.commit()


@router.get("/maintenances/due", response_model=list[MaintenanceOut])
def due(db: Session = Depends(get_db), _: User = Depends(require_employee)):
    """Maintenances whose next service is overdue or coming up. Creates notifications."""
    limit = dt.date.today() + dt.timedelta(days=DUE_SOON_DAYS)
    rows = _q(db).filter(Maintenance.next_maintenance.isnot(None),
                         Maintenance.next_maintenance <= limit).all()
    # keep only the latest maintenance of each car
    latest = {}
    for m in db.query(Maintenance).order_by(Maintenance.maintenance_date, Maintenance.id).all():
        latest[m.car_id] = m.id
    rows = [m for m in rows if latest.get(m.car_id) == m.id]
    for m in rows:
        late = m.next_maintenance < dt.date.today()
        _notify_all(db, m, f"Service {'overdue' if late else 'due soon'}: {m.car.brand} {m.car.model}",
                    f"Next maintenance planned on {m.next_maintenance} (plate {m.car.plate})")
    db.commit()
    return rows


# ---------- Notifications ----------
@router.get("/notifications", response_model=list[NotificationOut])
def my_notifications(unread_only: bool = False, db: Session = Depends(get_db),
                     emp: User = Depends(require_employee)):
    q = db.query(Notification).filter(Notification.employee_id == emp.id)
    if unread_only:
        q = q.filter(Notification.status == "unread")
    return q.order_by(Notification.date.desc()).all()


@router.patch("/notifications/{nid}/read", response_model=NotificationOut)
def mark_read(nid: int, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    n = db.get(Notification, nid)
    if not n or n.employee_id != emp.id:
        raise HTTPException(404, "Notification not found")
    n.status = "read"
    db.commit()
    db.refresh(n)
    return n
