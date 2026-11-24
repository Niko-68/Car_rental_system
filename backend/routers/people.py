"""User management: customers (employees) and employees/admins (admin)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import Address, Admin, Customer, Employee, Reservation, User
from schemas import CustomerOut, EmployeeCreate, ReservationOut, UserOut
from security import hash_password, require_admin, require_employee
from routers.reservations import _q as reservation_query

router = APIRouter(tags=["Users"])


# ---------- Customers ----------
@router.get("/customers", response_model=list[CustomerOut])
def list_customers(search: str | None = None, db: Session = Depends(get_db),
                   _: User = Depends(require_employee)):
    q = db.query(Customer).join(User, User.id == Customer.user_id)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(User.name.like(like), User.last_name.like(like), User.email.like(like)))
    return q.order_by(Customer.user_id).all()


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    c = db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, "Customer not found")
    return c


@router.get("/customers/{customer_id}/reservations", response_model=list[ReservationOut])
def customer_history(customer_id: int, db: Session = Depends(get_db), _: User = Depends(require_employee)):
    return (reservation_query(db).filter(Reservation.customer_id == customer_id)
            .order_by(Reservation.created_at.desc()).all())


# ---------- Employees / Admins ----------
@router.get("/employees", response_model=list[UserOut])
def list_employees(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).join(Employee, Employee.user_id == User.id).order_by(User.id).all()


@router.post("/employees", response_model=UserOut, status_code=201)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    u = User(name=data.name, last_name=data.last_name, email=data.email,
             password=hash_password(data.password))
    u.employee = Employee()
    if data.is_admin:
        u.employee.admin = Admin()
    if data.address:
        u.address = Address(**data.address.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/employees/{user_id}/admin", response_model=UserOut)
def set_admin(user_id: int, is_admin: bool, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    emp = db.get(Employee, user_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    if user_id == me.id:
        raise HTTPException(400, "You cannot change your own role")
    if is_admin and emp.admin is None:
        emp.admin = Admin()
    elif not is_admin and emp.admin is not None:
        db.delete(emp.admin)
    db.commit()
    db.refresh(emp.user)
    return emp.user


@router.delete("/employees/{user_id}", status_code=204)
def delete_employee(user_id: int, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    emp = db.get(Employee, user_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    if user_id == me.id:
        raise HTTPException(400, "You cannot delete yourself")
    try:
        db.delete(emp.user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Employee is referenced by cars/listings and cannot be deleted")
