"""SQLAlchemy models: exact mirror of schema.sql (UML diagram)."""
import datetime as dt

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger,
    String, Text, Time, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))  # bcrypt hash

    address: Mapped["Address | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan")
    customer: Mapped["Customer | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan")
    employee: Mapped["Employee | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def role(self) -> str:
        if self.employee is not None:
            return "admin" if self.employee.admin is not None else "employee"
        return "customer"


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint("user_id", name="uq_addresses_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    country: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    street: Mapped[str] = mapped_column(String(150))
    house_nbr: Mapped[str] = mapped_column(String(20))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))

    user: Mapped[User] = relationship(back_populates="address")


class Customer(Base):
    __tablename__ = "customers"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    birthdate: Mapped[dt.date] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="customer")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="customer")


class Employee(Base):
    __tablename__ = "employees"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    user: Mapped[User] = relationship(back_populates="employee")
    admin: Mapped["Admin | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan")


class Admin(Base):
    __tablename__ = "admins"

    user_id: Mapped[int] = mapped_column(ForeignKey("employees.user_id", ondelete="CASCADE"), primary_key=True)

    employee: Mapped[Employee] = relationship(back_populates="admin")


class Car(Base):
    __tablename__ = "cars"
    __table_args__ = (UniqueConstraint("plate", name="uq_cars_plate"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    registered_by: Mapped[int] = mapped_column(ForeignKey("employees.user_id"))
    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(SmallInteger)
    seats: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(30), default="available")  # available|rented|maintenance
    plate: Mapped[str] = mapped_column(String(30))
    kilometer: Mapped[int] = mapped_column(Integer, default=0)
    current_latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    current_longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))

    listings: Mapped[list["Listing"]] = relationship(back_populates="car", cascade="all, delete-orphan")
    maintenances: Mapped[list["Maintenance"]] = relationship(back_populates="car", cascade="all, delete-orphan")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"))
    created_by: Mapped[int] = mapped_column(ForeignKey("employees.user_id"))
    price: Mapped[float] = mapped_column(Numeric(10, 2))  # price per day
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")  # draft|published|unpublished

    car: Mapped[Car] = relationship(back_populates="listings")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="listing")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="chk_reservations_dates"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.user_id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    start_date: Mapped[dt.date] = mapped_column(Date)
    end_date: Mapped[dt.date] = mapped_column(Date)
    # pending|confirmed|rejected|picked_up|completed|cancelled
    status: Mapped[str] = mapped_column(String(30), default="pending")
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    pickup_location: Mapped[str | None] = mapped_column(String(255))
    return_location: Mapped[str | None] = mapped_column(String(255))
    pickup_time: Mapped[dt.time | None] = mapped_column(Time)
    return_time: Mapped[dt.time | None] = mapped_column(Time)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    deposit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    customer: Mapped[Customer] = relationship(back_populates="reservations")
    listing: Mapped[Listing] = relationship(back_populates="reservations")
    payments: Mapped[list["Payment"]] = relationship(back_populates="reservation")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="reservation", uselist=False)
    return_report: Mapped["ReturnReport | None"] = relationship(back_populates="reservation", uselist=False)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"))
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|paid|failed|refunded
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    method: Mapped[str] = mapped_column(String(30))
    date: Mapped[dt.date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    provider: Mapped[str | None] = mapped_column(String(50))
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    failure_reason: Mapped[str | None] = mapped_column(String(500))

    reservation: Mapped[Reservation] = relationship(back_populates="payments")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", name="uq_invoices_number"),
        UniqueConstraint("reservation_id", name="uq_invoices_reservation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"))
    invoice_number: Mapped[str] = mapped_column(String(50))
    issue_date: Mapped[dt.date] = mapped_column(Date)
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    extra_fees: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    pdf_path: Mapped[str | None] = mapped_column(String(500))

    reservation: Mapped[Reservation] = relationship(back_populates="invoice")


class ReturnReport(Base):
    __tablename__ = "return_reports"
    __table_args__ = (UniqueConstraint("reservation_id", name="uq_return_reports_reservation"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"))
    returned_at: Mapped[dt.datetime] = mapped_column(DateTime)
    kilometer_at_return: Mapped[int] = mapped_column(Integer)
    fuel_full: Mapped[bool] = mapped_column(Boolean, default=True)
    damage_description: Mapped[str | None] = mapped_column(Text)
    damage_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    reservation: Mapped[Reservation] = relationship(back_populates="return_report")


class Maintenance(Base):
    __tablename__ = "maintenances"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"))
    maintenance_date: Mapped[dt.date] = mapped_column(Date)
    next_maintenance: Mapped[dt.date | None] = mapped_column(Date)
    maintenance_type: Mapped[str] = mapped_column(String(50))  # routine|inspection|repair

    car: Mapped[Car] = relationship(back_populates="maintenances")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.user_id", ondelete="CASCADE"))
    maintenance_id: Mapped[int | None] = mapped_column(ForeignKey("maintenances.id", ondelete="SET NULL"))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(Text)
    date: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    status: Mapped[str] = mapped_column(String(30), default="unread")  # unread|read
