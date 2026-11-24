from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Car, Listing, Reservation, User
from schemas import CarCreate, CarOut, CarStatusIn, CarUpdate, NearestCarOut
from security import get_current_user, require_employee
from services.geo import haversine_km

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.get("", response_model=list[CarOut])
def list_cars(status: str | None = None, brand: str | None = None,
              db: Session = Depends(get_db), _: User = Depends(require_employee)):
    q = db.query(Car)
    if status:
        q = q.filter(Car.status == status)
    if brand:
        q = q.filter(Car.brand == brand)
    return q.order_by(Car.id).all()


@router.get("/nearest", response_model=list[NearestCarOut])
def nearest_available(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    min_seats: int | None = None,
    brand: str | None = None,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Closest available cars to the customer (Haversine formula)."""
    q = db.query(Car).filter(Car.status == "available",
                             Car.current_latitude.isnot(None), Car.current_longitude.isnot(None))
    if min_seats:
        q = q.filter(Car.seats >= min_seats)
    if brand:
        q = q.filter(Car.brand == brand)
    ranked = []
    for c in q.all():
        d = haversine_km(lat, lng, float(c.current_latitude), float(c.current_longitude))
        ranked.append(NearestCarOut(**CarOut.model_validate(c).model_dump(), distance_km=round(d, 2)))
    ranked.sort(key=lambda x: x.distance_km)
    return ranked[:limit]


@router.get("/{car_id}", response_model=CarOut)
def get_car(car_id: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    c = db.get(Car, car_id)
    if not c:
        raise HTTPException(404, "Car not found")
    return c


@router.post("", response_model=CarOut, status_code=201)
def create_car(data: CarCreate, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    if db.query(Car).filter(Car.plate == data.plate).first():
        raise HTTPException(409, "Plate already exists")
    c = Car(**data.model_dump(), registered_by=emp.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/{car_id}", response_model=CarOut)
def update_car(car_id: int, data: CarUpdate, db: Session = Depends(get_db),
               _: User = Depends(require_employee)):
    c = db.get(Car, car_id)
    if not c:
        raise HTTPException(404, "Car not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{car_id}/status", response_model=CarOut)
def set_status(car_id: int, data: CarStatusIn, db: Session = Depends(get_db),
               _: User = Depends(require_employee)):
    c = db.get(Car, car_id)
    if not c:
        raise HTTPException(404, "Car not found")
    c.status = data.status
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{car_id}", status_code=204)
def delete_car(car_id: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    c = db.get(Car, car_id)
    if not c:
        raise HTTPException(404, "Car not found")
    has_res = (db.query(Reservation).join(Listing, Listing.id == Reservation.listing_id)
               .filter(Listing.car_id == car_id).first())
    if has_res:
        raise HTTPException(409, "Car has reservations; set it to 'maintenance' instead of deleting")
    db.delete(c)
    db.commit()
