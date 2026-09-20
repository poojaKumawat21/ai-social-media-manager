import {
  Search,
  Bell,
  ChevronDown,
  Sparkles,
  ArrowUpRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  return (
    <header className="top-navbar">
      {/* Search */}
      <div className="search-box">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search anything..."
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      {/* Right Side */}
      <div className="navbar-right">

        {/* Login */}
        <button
          className="navbar-login-button"
          onClick={() => navigate("/login")}
        >
          <Sparkles size={13} />
          <span>Login</span>
        </button>

        {/* Get Started */}
        <button
          className="navbar-register-button"
          onClick={() => navigate("/register")}
        >
          <span>Get Started</span>
          <ArrowUpRight size={14} />
        </button>

        {/* Notification */}
        <button className="icon-button">
          <Bell size={20} />
          <span className="notification-dot"></span>
        </button>

        {/* Profile */}
        <div className="navbar-profile">
          <div className="profile-avatar">P</div>

          <span>Pooja Sharma</span>

          <ChevronDown size={17} />
        </div>

      </div>
    </header>
  );
}

export default Navbar;