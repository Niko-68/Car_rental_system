// Rental orders (Reservation in the class diagram). Fake data until the backend exists.

export type ReservationStatus = "Confirmed" | "Active" | "Returned" | "Closed" | "Cancelled";

export type Reservation = {
  id: number;
  userId: number; // the customer who made the order
  carLabel: string; // ex: "Renault Clio (AB-123-CD)"
  start: string; // YYYY-MM-DD
  end: string; // YYYY-MM-DD
  totalPrice: number;
  status: ReservationStatus;
};

let reservations: Reservation[] = [
  { id: 1001, userId: 1, carLabel: "Renault Clio (AB-123-CD)", start: "2026-09-02", end: "2026-09-05", totalPrice: 135, status: "Closed" },
  { id: 1002, userId: 1, carLabel: "Toyota Yaris (MN-012-OP)", start: "2026-11-08", end: "2026-11-12", totalPrice: 180, status: "Active" },
  { id: 1003, userId: 2, carLabel: "Peugeot 208 (EF-456-GH)", start: "2026-10-10", end: "2026-10-12", totalPrice: 96, status: "Closed" },
  { id: 1004, userId: 3, carLabel: "Volkswagen Golf (QR-345-ST)", start: "2026-11-05", end: "2026-11-08", totalPrice: 165, status: "Returned" },
  { id: 1005, userId: 3, carLabel: "Citroën C3 (IJ-789-KL)", start: "2026-11-20", end: "2026-11-23", totalPrice: 126, status: "Confirmed" },
  { id: 1006, userId: 3, carLabel: "Renault Clio (AB-123-CD)", start: "2026-08-14", end: "2026-08-16", totalPrice: 90, status: "Cancelled" },
];

// An order is still "open" while the car is booked, rented or waiting for the final invoice
export const OPEN_STATUSES: ReservationStatus[] = ["Confirmed", "Active", "Returned"];

export const getReservations = (): Reservation[] => reservations;

export const saveReservations = (list: Reservation[]) => {
  reservations = list;
};
