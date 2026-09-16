import { Search, Bell, ChevronDown } from "lucide-react";

function Navbar() {
  return (
    <header className="top-navbar">

      {/* Search */}
      <div className="search-box">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search anything..."
        />

        <span className="search-shortcut">
          ⌘ K
        </span>
      </div>

      {/* Right Side */}
      <div className="navbar-right">

        {/* Notification */}
        <button className="icon-button">
          <Bell size={20} />
          <span className="notification-dot"></span>
        </button>

        {/* Profile */}
        <div className="navbar-profile">
          <div className="profile-avatar">
            P
          </div>

          <span>Pooja Sharma</span>

          <ChevronDown size={17} />
        </div>

      </div>

    </header>
  );
}

export default Navbar;