-- =====================================================================
--  Car Rental : schéma MySQL 8 (généré à partir du diagramme UML)
--  Usage :  mysql -u root -p < schema.sql
-- =====================================================================

CREATE DATABASE IF NOT EXISTS car_rental
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE car_rental;

-- ---------------------------------------------------------------------
--  Héritage User -> Customer / Employee -> Admin (une table par classe)
-- ---------------------------------------------------------------------
CREATE TABLE users (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name        VARCHAR(100) NOT NULL,
  last_name   VARCHAR(100) NOT NULL,
  email       VARCHAR(255) NOT NULL,
  password    VARCHAR(255) NOT NULL COMMENT 'hash du mot de passe (bcrypt), jamais en clair',
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- User 1 --- 1 Address ("has")
CREATE TABLE addresses (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED NOT NULL,
  country     VARCHAR(100) NOT NULL,
  city        VARCHAR(100) NOT NULL,
  street      VARCHAR(150) NOT NULL,
  house_nbr   VARCHAR(20)  NOT NULL,
  latitude    DECIMAL(9,6) NULL,
  longitude   DECIMAL(9,6) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_addresses_user (user_id),
  CONSTRAINT fk_addresses_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE customers (
  user_id     INT UNSIGNED NOT NULL,
  birthdate   DATE NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_customers_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE employees (
  user_id     INT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_employees_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE admins (
  user_id     INT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_admins_employee FOREIGN KEY (user_id)
    REFERENCES employees (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Car  (Employee 1 --- 0..* Car : "Register vehicle")
-- ---------------------------------------------------------------------
CREATE TABLE cars (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT,
  registered_by      INT UNSIGNED NOT NULL,
  brand              VARCHAR(100) NOT NULL,
  model              VARCHAR(100) NOT NULL,
  year               SMALLINT UNSIGNED NOT NULL,
  seats              TINYINT UNSIGNED NOT NULL,
  status             VARCHAR(30) NOT NULL DEFAULT 'available'
                     COMMENT 'ex: available, rented, maintenance',
  plate              VARCHAR(30) NOT NULL,
  kilometer          INT UNSIGNED NOT NULL DEFAULT 0,
  current_latitude   DECIMAL(9,6) NULL,
  current_longitude  DECIMAL(9,6) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cars_plate (plate),
  KEY idx_cars_status (status),
  CONSTRAINT fk_cars_employee FOREIGN KEY (registered_by)
    REFERENCES employees (user_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Listing (Employee 1 --- 0..* Listing : "Create listing")
--           (Car 1 --- 0..* Listing : "is enlisted")
-- ---------------------------------------------------------------------
CREATE TABLE listings (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  car_id       INT UNSIGNED NOT NULL,
  created_by   INT UNSIGNED NOT NULL,
  price        DECIMAL(10,2) NOT NULL COMMENT 'prix par jour',
  description  TEXT NULL,
  status       VARCHAR(30) NOT NULL DEFAULT 'draft'
               COMMENT 'ex: draft, published, unpublished',
  PRIMARY KEY (id),
  KEY idx_listings_status (status),
  CONSTRAINT fk_listings_car FOREIGN KEY (car_id)
    REFERENCES cars (id) ON DELETE CASCADE,
  CONSTRAINT fk_listings_employee FOREIGN KEY (created_by)
    REFERENCES employees (user_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Reservation (Customer 1 --- 0..* Reservation : "creates reservations")
--               (Listing 1 --- 0..* Reservation : "used for reservations")
-- ---------------------------------------------------------------------
CREATE TABLE reservations (
  id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id          INT UNSIGNED NOT NULL,
  listing_id           INT UNSIGNED NOT NULL,
  start_date           DATE NOT NULL,
  end_date             DATE NOT NULL,
  status               VARCHAR(30) NOT NULL DEFAULT 'pending'
                       COMMENT 'ex: pending, confirmed, rejected, picked_up, completed, cancelled',
  total_price          DECIMAL(10,2) NOT NULL,
  created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pickup_location      VARCHAR(255) NULL,
  return_location      VARCHAR(255) NULL,
  pickup_time          TIME NULL,
  return_time          TIME NULL,
  cancellation_reason  VARCHAR(500) NULL,
  notes                TEXT NULL,
  deposit_price        DECIMAL(10,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_reservations_dates (listing_id, start_date, end_date),
  KEY idx_reservations_status (status),
  CONSTRAINT fk_reservations_customer FOREIGN KEY (customer_id)
    REFERENCES customers (user_id),
  CONSTRAINT fk_reservations_listing FOREIGN KEY (listing_id)
    REFERENCES listings (id),
  CONSTRAINT chk_reservations_dates CHECK (end_date >= start_date)
) ENGINE=InnoDB;

-- Reservation 1 --- 0..* Payment ("has payments")
CREATE TABLE payments (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reservation_id  INT UNSIGNED NOT NULL,
  status          VARCHAR(30) NOT NULL DEFAULT 'pending'
                  COMMENT 'ex: pending, paid, failed, refunded',
  amount          DECIMAL(10,2) NOT NULL,
  method          VARCHAR(30) NOT NULL COMMENT 'ex: card, cash, transfer',
  date            DATE NOT NULL,
  currency        CHAR(3) NOT NULL DEFAULT 'EUR',
  provider        VARCHAR(50) NULL COMMENT 'ex: stripe, paypal',
  processed_at    DATETIME NULL,
  failure_reason  VARCHAR(500) NULL,
  PRIMARY KEY (id),
  KEY idx_payments_reservation (reservation_id),
  CONSTRAINT fk_payments_reservation FOREIGN KEY (reservation_id)
    REFERENCES reservations (id)
) ENGINE=InnoDB;

-- Reservation 1 --- 0..1 Invoice ("generates")
CREATE TABLE invoices (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reservation_id  INT UNSIGNED NOT NULL,
  invoice_number  VARCHAR(50) NOT NULL,
  issue_date      DATE NOT NULL,
  base_amount     DECIMAL(10,2) NOT NULL,
  extra_fees      DECIMAL(10,2) NOT NULL DEFAULT 0,
  tax_amount      DECIMAL(10,2) NOT NULL DEFAULT 0,
  total_amount    DECIMAL(10,2) NOT NULL,
  pdf_path        VARCHAR(500) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_invoices_number (invoice_number),
  UNIQUE KEY uq_invoices_reservation (reservation_id),
  CONSTRAINT fk_invoices_reservation FOREIGN KEY (reservation_id)
    REFERENCES reservations (id)
) ENGINE=InnoDB;

-- Reservation 1 --- 0..1 ReturnReport ("has")
CREATE TABLE return_reports (
  id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reservation_id       INT UNSIGNED NOT NULL,
  returned_at          DATETIME NOT NULL,
  kilometer_at_return  INT UNSIGNED NOT NULL,
  fuel_full            BOOLEAN NOT NULL DEFAULT TRUE,
  damage_description   TEXT NULL,
  damage_fee           DECIMAL(10,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_return_reports_reservation (reservation_id),
  CONSTRAINT fk_return_reports_reservation FOREIGN KEY (reservation_id)
    REFERENCES reservations (id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Maintenance (Car 1 --- 0..* Maintenance : "has")
-- ---------------------------------------------------------------------
CREATE TABLE maintenances (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  car_id              INT UNSIGNED NOT NULL,
  maintenance_date    DATE NOT NULL,
  next_maintenance    DATE NULL,
  maintenance_type    VARCHAR(50) NOT NULL COMMENT 'ex: routine, inspection, repair',
  PRIMARY KEY (id),
  KEY idx_maintenances_next (next_maintenance),
  CONSTRAINT fk_maintenances_car FOREIGN KEY (car_id)
    REFERENCES cars (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Notification (Maintenance 1 --- 0..* Notification : "generate")
--                (Notification 0..* --- Employee : "is send to")
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  employee_id     INT UNSIGNED NOT NULL,
  maintenance_id  INT UNSIGNED NULL,
  subject         VARCHAR(200) NOT NULL,
  message         TEXT NULL,
  date            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status          VARCHAR(30) NOT NULL DEFAULT 'unread' COMMENT 'ex: unread, read',
  PRIMARY KEY (id),
  KEY idx_notifications_employee_status (employee_id, status),
  CONSTRAINT fk_notifications_employee FOREIGN KEY (employee_id)
    REFERENCES employees (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_notifications_maintenance FOREIGN KEY (maintenance_id)
    REFERENCES maintenances (id) ON DELETE SET NULL
) ENGINE=InnoDB;