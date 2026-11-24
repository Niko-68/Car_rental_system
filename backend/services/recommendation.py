"""Sort listings by similarity to the cars the customer has already rented.

Criteria available in the UML model: brand, model year, number of seats.
(The diagram has no colour or car type: see README to add them.)
"""
from collections import Counter

from sqlalchemy.orm import Session

from models import Car, Listing, Reservation

W_BRAND, W_YEAR, W_SEATS = 3.0, 2.0, 2.0
PAST = ("confirmed", "picked_up", "completed")


def _history(db: Session, customer_id: int) -> list[Car]:
    rows = (
        db.query(Reservation)
        .filter(Reservation.customer_id == customer_id, Reservation.status.in_(PAST))
        .all()
    )
    return [r.listing.car for r in rows]


def score(car: Car, history: list[Car]) -> float:
    n = len(history)
    brands = Counter(h.brand.lower() for h in history)
    seats = Counter(h.seats for h in history)
    avg_year = sum(h.year for h in history) / n
    s = W_BRAND * brands.get(car.brand.lower(), 0) / n
    s += W_SEATS * seats.get(car.seats, 0) / n
    s += W_YEAR * max(0.0, 1 - abs(car.year - avg_year) / 10)
    return s


def rank_listings(db: Session, listings: list[Listing], user_id: int | None) -> list[Listing]:
    if user_id is None:
        return listings
    history = _history(db, user_id)
    if not history:
        return listings
    return sorted(listings, key=lambda l: score(l.car, history), reverse=True)
