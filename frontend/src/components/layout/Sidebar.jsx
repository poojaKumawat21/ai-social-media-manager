import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">✦</div>

        <div>
          <h2>AI Social Media</h2>
          <span>Manager</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <p className="nav-section">MAIN</p>

        <Link to="/">⌂ Dashboard</Link>

        <Link to="/create-post">
          ✎ Create Post
        </Link>

        {/* Saved Drafts */}
        <Link to="/saved-drafts">
          ▤ Saved Drafts
        </Link>

        <Link to="/content-calendar">
          ▣ Content Calendar
        </Link>

        <Link to="/ai-ideas">
          ✦ AI Ideas
        </Link>

        <Link to="/news-trends">
          ◈ News & Trends
        </Link>

        <Link to="/scheduled-posts">
          ◷ Scheduled Posts
        </Link>

        <Link to="/published-posts">
          ✓ Published Posts
        </Link>

        <Link to="/connected-accounts">
          ◎ Connected Accounts
        </Link>

        <Link to="/analytics">
          ▥ Analytics
        </Link>

        <Link to="/brand-settings">
          ⚙ Brand Settings
        </Link>

        <Link to="/ai-settings">
          ✦ AI Settings
        </Link>

        <Link to="/security">
          ♢ Security
        </Link>
      </nav>

      {/* AI Promo */}
      <div className="ai-promo">
        <h3>
          Let AI handle
          <br />
          your social media
        </h3>

        <p>
          Smart content. Better engagement. More growth.
        </p>

        <button>
          Upgrade to Pro →
        </button>
      </div>

      {/* User */}
      <div className="sidebar-user">
        <div className="user-avatar">
          P
        </div>

        <div>
          <strong>xxxxx</strong>
          <small>xxxx@email.com</small>
        </div>
      </div>

      {/* Bottom */}
      <div className="sidebar-bottom">
        <Link to="/settings">
          ⚙ Settings
        </Link>

        <Link to="/logout">
          ↪ Logout
        </Link>
      </div>
    </aside>
  );
}

export default Sidebar;

