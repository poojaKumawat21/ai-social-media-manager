import {
  Bell,
  ChevronDown,
  Sparkles,
  ArrowUpRight,
  User,
  Settings,
  LogOut,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Navbar.css";

import api from "../../services/api";

function Navbar() {
  const navigate = useNavigate();

  const [profileName, setProfileName] = useState("User");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const result = await api.get("/profile");

        if (result.profile?.name) {
          setProfileName(result.profile.name);
        }

        if (result.profile?.avatar_url) {
          setAvatarUrl(result.profile.avatar_url);
        }
      } catch (error) {
        console.error("Profile load error:", error);
      }
    };

    loadProfile();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_email");

    navigate("/login", { replace: true });
  };

  const firstLetter = profileName.charAt(0).toUpperCase();

  return (
    <header className="top-navbar">
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
        <div className="navbar-profile-wrapper">
          <button
            className="navbar-profile"
            onClick={() => setIsProfileOpen((prev) => !prev)}
          >
            <div className="profile-avatar">
              {avatarUrl ? (
                <img src={avatarUrl} alt={profileName} />
              ) : (
                firstLetter
              )}
            </div>

            <span>{profileName}</span>

            <ChevronDown size={17} />
          </button>

          {/* Profile Dropdown */}
          {isProfileOpen && (
            <div className="profile-dropdown">
              <button
                onClick={() => {
                  setIsProfileOpen(false);
                  navigate("/settings");
                }}
              >
                <User size={16} />
                <span>Profile Settings</span>
              </button>

              <button
                onClick={() => {
                  setIsProfileOpen(false);
                  navigate("/settings");
                }}
              >
                <Settings size={16} />
                <span>Settings</span>
              </button>

              <div className="profile-dropdown-divider"></div>

              <button className="logout-button" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Navbar;