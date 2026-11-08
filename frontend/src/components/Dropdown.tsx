import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

export type MenuItem = { label: string; to: string };

export default function Dropdown({ label, items }: { label: string; items: MenuItem[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // shut the dropdown when clicking outside of it
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className="dropdown" ref={ref}>
      <button className="btn" onClick={() => setOpen(!open)}>
        {label} ▾
      </button>
      {open && (
        <ul className="dropdown-menu">
          {items.map((item) => (
            <li key={item.to}>
              <Link to={item.to} onClick={() => setOpen(false)}>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}