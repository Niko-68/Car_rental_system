import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Car, Listing, Payment, Reservation, ReturnReport, User
from schemas import (
    CancelIn, PayIn, ReservationCreate, ReservationOut, ReservationUpdate, ReturnIn,
)
from security import get_current_user, require_customer, require_employee
from services.invoice import build_invoice_pdf, upsert_invoice

router = APIRouter(prefix="/reservations", tags=["Reservations"])

BLOCKING = ("confirmed", "picked_up")


def _q(db: Session):
    return db.query(Reservation).options(
        joinedload(Reservation.listing).joinedload(Listing.car),
        joinedload(Reservation.customer),
        joinedload(Reservation.payments),
        joinedload(Reservation.invoice),
        joinedload(Reservation.return_report),
    )


def _days(start: dt.date, end: dt.date) -> int:
    return max((end - start).days, 1)


def _check_dates(start: dt.date, end: dt.date):
    if end <= start:
        raise HTTPException(400, "end_date must be after start_date")
    if start < dt.date.today():
        raise HTTPException(400, "start_date cannot be in the past")


def _overlap(db: Session, car_id: int, start: dt.date, end: dt.date, exclude: int | None = None) -> bool:
    q = (db.query(Reservation).join(Listing, Listing.id == Reservation.listing_id)
         .filter(Listing.car_id == car_id, Reservation.status.in_(BLOCKING),
                 Reservation.start_date < end, Reservation.end_date > start))
    if exclude:
        q = q.filter(Reservation.id != exclude)
    return q.first() is not None


def _get(db: Session, rid: int, user: User) -> Reservation:
    r = _q(db).filter(Reservation.id == rid).first()
    if not r:
        raise HTTPException(404, "Reservation not found")
    if user.role == "customer" and r.customer_id != user.id:
        raise HTTPException(403, "Not your reservation")
    return r


def _is_paid(r: Reservation) -> bool:
    return any(p.status == "paid" for p in r.payments)


# ---------- Customer ----------
@router.post("", response_model=ReservationOut, status_code=201)
def create(data: ReservationCreate, db: Session = Depends(get_db), cust: User = Depends(require_customer)):
    _check_dates(data.start_date, data.end_date)
    l = db.get(Listing, data.listing_id)
    if not l or l.status != "published":
        raise HTTPException(404, "Listing not found")
    if l.car.status == "maintenance":
        raise HTTPException(409, "Car is under maintenance")
    if _overlap(db, l.car_id, data.start_date, data.end_date):
        raise HTTPException(409, "Car already booked for these dates")
    r = Reservation(
        **data.model_dump(), customer_id=cust.id,
        total_price=Decimal(str(l.price)) * _days(data.start_date, data.end_date),
    )
    db.add(r)
    db.commit()
    return _get(db, r.id, cust)


@router.get("", response_model=list[ReservationOut])
def list_reservations(status: str | None = None, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    q = _q(db)
    if user.role == "customer":
        q = q.filter(Reservation.customer_id == user.id)
    if status:
        q = q.filter(Reservation.status == status)
    return q.order_by(Reservation.created_at.desc()).all()


@router.get("/{rid}", response_model=ReservationOut)
def get_reservation(rid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get(db, rid, user)


@router.put("/{rid}", response_model=ReservationOut)
def modify(rid: int, data: ReservationUpdate, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    r = _get(db, rid, user)
    if r.status != "pending":
        raise HTTPException(409, "Only pending reservations can be modified")
    payload = data.model_dump(exclude_unset=True)
    start = payload.get("start_date", r.start_date)
    end = payload.get("end_date", r.end_date)
    _check_dates(start, end)
    if _overlap(db, r.listing.car_id, start, end, exclude=r.id):
        raise HTTPException(409, "Car already booked for these dates")
    for k, v in payload.items():
        setattr(r, k, v)
    r.total_price = Decimal(str(r.listing.price)) * _days(start, end)
    db.commit()
    return _get(db, r.id, user)


@router.post("/{rid}/cancel", response_model=ReservationOut)
def cancel(rid: int, data: CancelIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = _get(db, rid, user)
    if r.status not in ("pending", "confirmed"):
        raise HTTPException(409, f"Cannot cancel a reservation in status {r.status}")
    r.status = "cancelled"
    r.cancellation_reason = data.reason
    for p in r.payments:
        if p.status == "paid":
            p.status = "refunded"
    db.commit()
    return _get(db, r.id, user)


# ---------- Payment & invoice ----------
@router.post("/{rid}/pay", response_model=ReservationOut)
def pay(rid: int, data: PayIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Simulated payment: replace with Stripe/PayPal. Generates the invoice."""
    r = _get(db, rid, user)
    if r.status != "confirmed":
        raise HTTPException(409, "Reservation must be confirmed by an employee before payment")
    if _is_paid(r):
        raise HTTPException(409, "Already paid")
    inv = upsert_invoice(db, r)
    now = dt.datetime.utcnow()
    db.add(Payment(reservation_id=r.id, status="paid", amount=inv.total_amount, method=data.method,
                   date=now.date(), currency="EUR", provider=data.provider, processed_at=now))
    db.commit()
    return _get(db, r.id, user)


@router.get("/{rid}/invoice")
def invoice_pdf(rid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = _get(db, rid, user)
    if r.invoice is None:
        raise HTTPException(409, "No invoice yet: the reservation must be paid first")
    return Response(
        content=build_invoice_pdf(r), media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{r.invoice.invoice_number}.pdf"'},
    )


# ---------- Employees ----------
@router.post("/{rid}/approve", response_model=ReservationOut)
def approve(rid: int, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    r = _get(db, rid, emp)
    if r.status != "pending":
        raise HTTPException(409, "Only pending reservations can be approved")
    if r.listing.car.status == "maintenance":
        raise HTTPException(409, "Car is under maintenance")
    if _overlap(db, r.listing.car_id, r.start_date, r.end_date, exclude=r.id):
        raise HTTPException(409, "Car already booked for these dates")
    r.status = "confirmed"
    db.commit()
    return _get(db, r.id, emp)


@router.post("/{rid}/reject", response_model=ReservationOut)
def reject(rid: int, data: CancelIn, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    r = _get(db, rid, emp)
    if r.status != "pending":
        raise HTTPException(409, "Only pending reservations can be rejected")
    r.status = "rejected"
    r.cancellation_reason = data.reason
    db.commit()
    return _get(db, r.id, emp)


@router.post("/{rid}/pickup", response_model=ReservationOut)
def pickup(rid: int, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    r = _get(db, rid, emp)
    if r.status != "confirmed":
        raise HTTPException(409, "Reservation must be confirmed before pickup")
    if not _is_paid(r):
        raise HTTPException(409, "Reservation must be paid before pickup")
    car: Car = r.listing.car
    if car.status == "maintenance":
        raise HTTPException(409, "Car is under maintenance")
    r.status = "picked_up"
    car.status = "rented"
    db.commit()
    return _get(db, r.id, emp)


@router.post("/{rid}/return", response_model=ReservationOut)
def return_car(rid: int, data: ReturnIn, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    """Record the return (return_reports) and update the invoice with extra fees."""
    r = _get(db, rid, emp)
    if r.status != "picked_up":
        raise HTTPException(409, "Car has not been picked up")
    now = dt.datetime.utcnow()
    late_days = max((now.date() - r.end_date).days, 0)
    late_fee = Decimal(str(r.listing.price)) * late_days
    r.return_report = ReturnReport(
        returned_at=now, kilometer_at_return=data.kilometer_at_return, fuel_full=data.fuel_full,
        damage_description=data.damage_description, damage_fee=data.damage_fee,
    )
    r.status = "completed"
    car = r.listing.car
    car.kilometer = data.kilometer_at_return
    car.status = "available"
    if r.invoice is not None:
        upsert_invoice(db, r, extra_fees=data.damage_fee + late_fee)
    db.commit()
    return _get(db, r.id, emp)
