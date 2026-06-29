import { BarChart3, BrainCircuit, Code2, FileText, LayoutDashboard, LogOut, PlayCircle } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { logout } from "../auth/api";
import { clearTokens } from "../auth/authStore";
import styles from "./AppShell.module.css";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/interview/setup", label: "New Interview", icon: PlayCircle },
  { to: "/coding", label: "Coding Round", icon: Code2 },
  { to: "/reports", label: "Reports", icon: FileText },
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
          <span className={styles.brandIcon}>IL</span>
          <div>
            <div className={styles.brandName}>InterviewLoop</div>
            <div className={styles.brandTagline}>AI Mock Interviews</div>
          </div>
        </NavLink>

        <hr className={styles.divider} />
        <span className={styles.navSection}>Navigation</span>

        <nav aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                className={({ isActive }) => (isActive ? styles.activeLink : styles.navLink)}
                end={item.end}
                key={item.to}
                to={item.to}
              >
                <Icon aria-hidden="true" className={styles.navIcon} size={16} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <hr className={styles.divider} />
        <span className={styles.navSection}>Analytics</span>
        <NavLink
          className={({ isActive }) => (isActive ? styles.activeLink : styles.navLink)}
          to="/"
          end
        >
          <BarChart3 aria-hidden="true" className={styles.navIcon} size={16} />
          Performance
        </NavLink>

        <button className={styles.logout} onClick={handleLogout} type="button">
          <LogOut aria-hidden="true" size={16} />
          Sign out
        </button>
      </aside>

      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
}
