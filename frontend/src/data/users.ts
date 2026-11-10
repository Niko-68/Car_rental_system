// Users of the system (fake data until the backend exists).
// The list is kept here, outside the pages, so every user page sees the same people:
// if the list page creates a user or the details page removes one, the other page sees it too.
// The changes are lost when the browser reloads (there is no database yet).

export type Role = "Customer" | "Employee" | "Admin";

export type User = {
  id: number;
  name: string;
  lastName: string;
  email: string;
  phone: string;
  role: Role;
};

// What the user form edits: everything except the id (the system assigns it)
export type UserFormValues = Omit<User, "id">;

let users: User[] = [
  { id: 1, name: "Austėja", lastName: "Petrauskienė", email: "austeja@example.com", phone: "+370 612 34567", role: "Customer" },
  { id: 2, name: "Lukas", lastName: "Jonaitis", email: "lukas@example.com", phone: "+370 623 45678", role: "Customer" },
  { id: 3, name: "Marie", lastName: "Dubois", email: "marie@example.com", phone: "+33 6 12 34 56 78", role: "Customer" },
  { id: 4, name: "Mantas", lastName: "Kazlauskas", email: "mantas@carrental.lt", phone: "+370 634 56789", role: "Employee" },
  { id: 5, name: "Eglė", lastName: "Vaitkutė", email: "egle@carrental.lt", phone: "+370 645 67890", role: "Employee" },
  { id: 6, name: "Rasa", lastName: "Navickienė", email: "rasa@carrental.lt", phone: "+370 656 78901", role: "Admin" },
];

// Read the current list of users
export const getUsers = (): User[] => users;

// Replace the list of users (after creating, editing or removing one)
export const saveUsers = (list: User[]) => {
  users = list;
};
