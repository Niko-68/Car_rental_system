"""Demo data. Usage:  python seed.py
Accounts (password: password123): admin@rental.com, agent@rental.com, client@rental.com
"""
import datetime as dt

from database import Base, SessionLocal, engine
from models import Address, Admin, Car, Customer, Employee, Listing, User
from security import hash_password


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(User).first():
        print("The database already contains users: seed skipped.")
        return
    pw = hash_password("password123")

    admin = User(name="Alice", last_name="Boss", email="admin@rental.com", password=pw)
    admin.employee = Employee()
    admin.employee.admin = Admin()
    agent = User(name="Marc", last_name="Agent", email="agent@rental.com", password=pw)
    agent.employee = Employee()
    client = User(name="Manon", last_name="Colard", email="client@rental.com", password=pw)
    client.customer = Customer(birthdate=dt.date(2000, 5, 17))
    client.address = Address(country="France", city="Paris", street="Rue de Rivoli", house_nbr="10",
                             latitude=48.8566, longitude=2.3522)
    db.add_all([admin, agent, client])
    db.flush()

    cars = [
        Car(registered_by=agent.id, brand="Toyota", model="Corolla", year=2021, seats=5, plate="ABC-123",
            kilometer=32000, current_latitude=48.8566, current_longitude=2.3522),
        Car(registered_by=agent.id, brand="Toyota", model="RAV4", year=2022, seats=5, plate="DEF-456",
            kilometer=18000, current_latitude=48.9, current_longitude=2.4),
        Car(registered_by=agent.id, brand="BMW", model="X3", year=2020, seats=5, plate="GHI-789",
            kilometer=52000, current_latitude=45.764, current_longitude=4.8357),
        Car(registered_by=agent.id, brand="Renault", model="Trafic", year=2019, seats=9, plate="JKL-012",
            kilometer=64000, current_latitude=43.2965, current_longitude=5.3698),
    ]
    db.add_all(cars)
    db.flush()
    prices = [45, 70, 95, 110]
    for c, p in zip(cars, prices):
        db.add(Listing(car_id=c.id, created_by=agent.id, price=p, status="published",
                       description=f"{c.brand} {c.model} {c.year}, {c.seats} seats."))
    db.commit()
    print("Seed completed.")


if __name__ == "__main__":
    run()
