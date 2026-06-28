import { BarChart3, Code2, FileText, Fingerprint, LogOut, MessagesSquare, PlayCircle } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { clearTokens } from "../auth/authStore";
import { logout } from "../auth/api";
import styles from "./AppShell.module.css";

const navItems = [
  { to: "/", label: "Dashboard", icon: BarChart3 },
  { to: "/interview/setup", label: "Setup", icon: PlayCircle },
  { to: "/interview/demo-session", label: "Interview", icon: MessagesSquare },
  { to: "/coding", label: "Coding", icon: Code2 },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/enrollment", label: "Enrollment", icon: Fingerprint },
];

export function AppShell() {
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Token cleanup should still happen when the server is unreachable.
    } finally {
      clearTokens();
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <NavLink className={styles.brand} to="/">
          <span>IL</span>
          <strong>InterviewLoop</strong>
        </NavLink>
        <nav className={styles.nav} aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink className={({ isActive }) => (isActive ? styles.activeLink : styles.navLink)} key={item.to} to={item.to}>
                <Icon aria-hidden="true" size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <button className={styles.logout} onClick={handleLogout} type="button">
          <LogOut aria-hidden="true" size={18} />
          Logout
        </button>
      </aside>
      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
}
