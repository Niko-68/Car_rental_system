import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Users / Auth ----------
class AddressIn(BaseModel):
    country: str
    city: str
    street: str
    house_nbr: str
    latitude: float | None = None
    longitude: float | None = None


class AddressOut(ORM, AddressIn):
    id: int


class RegisterIn(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    birthdate: dt.date
    address: AddressIn | None = None


class EmployeeCreate(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    is_admin: bool = False
    address: AddressIn | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: int
    name: str
    last_name: str
    email: EmailStr
    role: str
    address: AddressOut | None = None


class UserBrief(ORM):
    id: int
    name: str
    last_name: str
    email: EmailStr


class UserUpdate(BaseModel):
    name: str | None = None
    last_name: str | None = None
    address: AddressIn | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CustomerOut(ORM):
    user_id: int
    birthdate: dt.date
    created_at: dt.datetime
    user: UserBrief


# ---------- Cars ----------
class CarBase(BaseModel):
    brand: str
    model: str
    year: int
    seats: int = Field(gt=0)
    plate: str
    kilometer: int = 0
    current_latitude: float | None = None
    current_longitude: float | None = None


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    seats: int | None = None
    plate: str | None = None
    kilometer: int | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None


class CarStatusIn(BaseModel):
    status: str = Field(pattern="^(available|rented|maintenance)$")


class CarOut(ORM, CarBase):
    id: int
    status: str
    registered_by: int


class NearestCarOut(CarOut):
    distance_km: float


# ---------- Listings ----------
class ListingCreate(BaseModel):
    car_id: int
    price: Decimal = Field(gt=0)
    description: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|unpublished)$")


class ListingUpdate(BaseModel):
    price: Decimal | None = Field(default=None, gt=0)
    description: str | None = None


class ListingOut(ORM):
    id: int
    car_id: int
    created_by: int
    price: Decimal
    description: str | None
    status: str
    car: CarOut


# ---------- Reservations ----------
class ReservationCreate(BaseModel):
    listing_id: int
    start_date: dt.date
    end_date: dt.date
    pickup_location: str | None = None
    return_location: str | None = None
    pickup_time: dt.time | None = None
    return_time: dt.time | None = None
    deposit_price: Decimal = Decimal("0")
    notes: str | None = None


class ReservationUpdate(BaseModel):
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    pickup_location: str | None = None
    return_location: str | None = None
    pickup_time: dt.time | None = None
    return_time: dt.time | None = None
    notes: str | None = None


class CancelIn(BaseModel):
    reason: str | None = None


class ReturnIn(BaseModel):
    kilometer_at_return: int
    fuel_full: bool = True
    damage_description: str | None = None
    damage_fee: Decimal = Decimal("0")


class PayIn(BaseModel):
    method: str = "card"
    provider: str | None = "simulated"


class PaymentOut(ORM):
    id: int
    status: str
    amount: Decimal
    method: str
    date: dt.date
    currency: str
    provider: str | None
    processed_at: dt.datetime | None
    failure_reason: str | None


class InvoiceOut(ORM):
    id: int
    invoice_number: str
    issue_date: dt.date
    base_amount: Decimal
    extra_fees: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class ReturnReportOut(ORM):
    returned_at: dt.datetime
    kilometer_at_return: int
    fuel_full: bool
    damage_description: str | None
    damage_fee: Decimal


class ReservationOut(ORM):
    id: int
    customer_id: int
    listing_id: int
    start_date: dt.date
    end_date: dt.date
    status: str
    total_price: Decimal
    created_at: dt.datetime
    pickup_location: str | None
    return_location: str | None
    pickup_time: dt.time | None
    return_time: dt.time | None
    cancellation_reason: str | None
    notes: str | None
    deposit_price: Decimal
    listing: ListingOut
    customer: CustomerOut
    payments: list[PaymentOut] = []
    invoice: InvoiceOut | None = None
    return_report: ReturnReportOut | None = None


# ---------- Maintenance / Notifications ----------
class MaintenanceCreate(BaseModel):
    car_id: int
    maintenance_date: dt.date
    next_maintenance: dt.date | None = None
    maintenance_type: str = Field(pattern="^(routine|inspection|repair)$")


class MaintenanceOut(ORM):
    id: int
    car_id: int
    maintenance_date: dt.date
    next_maintenance: dt.date | None
    maintenance_type: str
    car: CarOut


class NotificationOut(ORM):
    id: int
    employee_id: int
    maintenance_id: int | None
    subject: str
    message: str | None
    date: dt.datetime
    status: str
