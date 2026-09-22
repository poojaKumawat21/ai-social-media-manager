import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../../services/api";

function Sidebar() {
  const [profileName, setProfileName] = useState("User");
  const [profileEmail, setProfileEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const result = await api.get("/profile");

        if (result.profile?.name) {
          setProfileName(result.profile.name);
        }

        if (result.profile?.email) {
          setProfileEmail(result.profile.email);
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

  const firstLetter = profileName.charAt(0).toUpperCase();

  return (
    <aside className={`sidebar ${isCollapsed ? "sidebar-collapsed" : ""}`}>
      
      {/* Toggle Button */}
      <button
        className="sidebar-toggle"
        onClick={() => setIsCollapsed((prev) => !prev)}
        title={isCollapsed ? "Open sidebar" : "Close sidebar"}
        aria-label={isCollapsed ? "Open sidebar" : "Close sidebar"}
      >
        <span>{isCollapsed ? "→" : "←"}</span>
      </button>

      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">
          <img src="/logo.jpeg" alt="PostPilot Logo" />
        </div>

        <div className="sidebar-logo-text">
          <h2>PostPilot</h2>
          <span>AI Social Media</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <p className="nav-section">MAIN</p>

        <Link to="/">
          <span className="nav-icon">⌂</span>
          <span className="nav-text">Dashboard</span>
        </Link>

        <Link to="/create-post">
          <span className="nav-icon">✎</span>
          <span className="nav-text">Create Post</span>
        </Link>

        <Link to="/saved-drafts">
          <span className="nav-icon">▤</span>
          <span className="nav-text">Saved Drafts</span>
        </Link>

        <Link to="/content-calendar">
          <span className="nav-icon">▣</span>
          <span className="nav-text">Content Calendar</span>
        </Link>

        <Link to="/ai-ideas">
          <span className="nav-icon">✦</span>
          <span className="nav-text">AI Ideas</span>
        </Link>

        <Link to="/news-trends">
          <span className="nav-icon">◈</span>
          <span className="nav-text">News & Trends</span>
        </Link>

        <Link to="/scheduled-posts">
          <span className="nav-icon">◷</span>
          <span className="nav-text">Scheduled Posts</span>
        </Link>

        <Link to="/published-posts">
          <span className="nav-icon">✓</span>
          <span className="nav-text">Published Posts</span>
        </Link>

        <Link to="/connected-accounts">
          <span className="nav-icon">◎</span>
          <span className="nav-text">Connected Accounts</span>
        </Link>

        <Link to="/analytics">
          <span className="nav-icon">▥</span>
          <span className="nav-text">Analytics</span>
        </Link>

        <Link to="/brand-settings">
          <span className="nav-icon">⚙</span>
          <span className="nav-text">Brand Settings</span>
        </Link>

        <Link to="/ai-settings">
          <span className="nav-icon">✦</span>
          <span className="nav-text">AI Settings</span>
        </Link>

        <Link to="/security">
          <span className="nav-icon">♢</span>
          <span className="nav-text">Security</span>
        </Link>
      </nav>

      {/* AI Promo */}
      <div className="ai-promo">
        <div className="ai-promo-content">
          <h3>
            Let AI handle
            <br />
            your social media
          </h3>

          <p>Smart content. Better engagement. More growth.</p>

          <button>Upgrade to Pro →</button>
        </div>
      </div>

      {/* User */}
      <div className="sidebar-user">
        <div className="user-avatar">
          {avatarUrl ? (
            <img src={avatarUrl} alt={profileName} />
          ) : (
            firstLetter
          )}
        </div>

        <div className="sidebar-user-info">
          <strong>{profileName}</strong>
          <small>{profileEmail}</small>
        </div>
      </div>

      {/* Bottom */}
      <div className="sidebar-bottom">
        <Link to="/settings">
          <span className="nav-icon">⚙</span>
          <span className="nav-text">Settings</span>
        </Link>

        <Link to="/logout">
          <span className="nav-icon">↪</span>
          <span className="nav-text">Logout</span>
        </Link>
      </div>
    </aside>
  );
}

export default Sidebar;