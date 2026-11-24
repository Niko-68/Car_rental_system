from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Car, Listing, User
from schemas import ListingCreate, ListingOut, ListingUpdate
from security import optional_user, require_employee
from services.recommendation import rank_listings

router = APIRouter(prefix="/listings", tags=["Listings"])


def _q(db: Session):
    return db.query(Listing).options(joinedload(Listing.car))


@router.get("", response_model=list[ListingOut])
def browse(
    brand: str | None = None,
    min_year: int | None = None,
    min_seats: int | None = None,
    max_price: float | None = None,
    personalized: bool = True,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    """Public catalog: published listings whose car is not under maintenance.
    For a logged-in customer, results are sorted by similarity with past rentals."""
    q = _q(db).join(Car, Car.id == Listing.car_id).filter(
        Listing.status == "published", Car.status != "maintenance")
    if brand:
        q = q.filter(Car.brand == brand)
    if min_year:
        q = q.filter(Car.year >= min_year)
    if min_seats:
        q = q.filter(Car.seats >= min_seats)
    if max_price is not None:
        q = q.filter(Listing.price <= max_price)
    items = q.order_by(Listing.id.desc()).all()
    if personalized and user and user.role == "customer":
        items = rank_listings(db, items, user.id)
    return items


@router.get("/manage", response_model=list[ListingOut])
def manage(db: Session = Depends(get_db), _: User = Depends(require_employee)):
    return _q(db).order_by(Listing.id.desc()).all()


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    l = _q(db).filter(Listing.id == listing_id).first()
    is_staff = user is not None and user.role in ("employee", "admin")
    if not l or (l.status != "published" and not is_staff):
        raise HTTPException(404, "Listing not found")
    return l


@router.post("", response_model=ListingOut, status_code=201)
def create_listing(data: ListingCreate, db: Session = Depends(get_db), emp: User = Depends(require_employee)):
    if not db.get(Car, data.car_id):
        raise HTTPException(404, "Car not found")
    l = Listing(**data.model_dump(), created_by=emp.id)
    db.add(l)
    db.commit()
    return _q(db).filter(Listing.id == l.id).one()


@router.put("/{listing_id}", response_model=ListingOut)
def update_listing(listing_id: int, data: ListingUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_employee)):
    l = db.get(Listing, listing_id)
    if not l:
        raise HTTPException(404, "Listing not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(l, k, v)
    db.commit()
    return _q(db).filter(Listing.id == l.id).one()


@router.patch("/{listing_id}/status", response_model=ListingOut)
def set_status(listing_id: int, status: str, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    """Publish / unpublish: status = draft | published | unpublished."""
    if status not in ("draft", "published", "unpublished"):
        raise HTTPException(422, "status must be draft, published or unpublished")
    l = db.get(Listing, listing_id)
    if not l:
        raise HTTPException(404, "Listing not found")
    l.status = status
    db.commit()
    return _q(db).filter(Listing.id == l.id).one()


@router.delete("/{listing_id}", status_code=204)
def delete_listing(listing_id: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    l = db.get(Listing, listing_id)
    if not l:
        raise HTTPException(404, "Listing not found")
    if l.reservations:
        raise HTTPException(409, "Listing has reservations; unpublish it instead")
    db.delete(l)
    db.commit()
