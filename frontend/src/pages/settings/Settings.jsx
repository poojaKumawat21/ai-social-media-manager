import React, { useEffect, useState } from "react";
import { User, Bell, Bot, Palette, Shield, Save } from "lucide-react";
import "./Settings.css";

function Settings() {
  const [activeSection, setActiveSection] = useState("profile");

  const [settings, setSettings] = useState({
    name: "Pooja Sharma",
    email: "pooja@example.com",
    notifications: true,
    emailUpdates: true,
    aiSuggestions: true,
    autoGenerate: false,
    darkMode: true,
  });

  /* APPLY THEME */
  useEffect(() => {
    document.documentElement.classList.toggle(
      "light-theme",
      !settings.darkMode,
    );
  }, [settings.darkMode]);

  /* HANDLE SETTINGS CHANGE */
  const handleChange = (key, value) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  /* SAVE SETTINGS */
  const handleSave = () => {
    alert("Settings saved successfully.");
  };

  const sections = [
    {
      id: "profile",
      label: "Profile",
      icon: User,
    },
    {
      id: "notifications",
      label: "Notifications",
      icon: Bell,
    },
    {
      id: "ai",
      label: "AI Preferences",
      icon: Bot,
    },
    {
      id: "appearance",
      label: "Appearance",
      icon: Palette,
    },
    {
      id: "security",
      label: "Security",
      icon: Shield,
    },
    {
      id: "brand",
      label: "Brand Settings",
      icon: Palette,
    },
  ];

  return (
    <div className="settings-page">
      {/* HEADER */}
      <div className="settings-header">
        <div>
          <span className="settings-label">ACCOUNT CONTROL</span>

          <h1>Settings</h1>

          <p>Manage your profile, AI preferences and account settings.</p>
        </div>

        <button className="settings-save-button" onClick={handleSave}>
          <Save size={15} />
          Save Changes
        </button>
      </div>

      {/* SETTINGS LAYOUT */}
      <div className="settings-layout">
        {/* SIDEBAR */}
        <aside className="settings-sidebar">
          {sections.map((section) => {
            const Icon = section.icon;

            return (
              <button
                key={section.id}
                className={`settings-nav-item ${
                  activeSection === section.id ? "active" : ""
                }`}
                onClick={() => setActiveSection(section.id)}
              >
                <Icon size={16} />
                <span>{section.label}</span>
              </button>
            );
          })}
        </aside>

        {/* CONTENT */}
        <section className="settings-content">
          {/* PROFILE */}
          {activeSection === "profile" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <div>
                  <h2>Profile Settings</h2>

                  <p>Manage your basic account information.</p>
                </div>
              </div>

              <div className="settings-avatar-section">
                <div className="settings-avatar">P</div>

                <div>
                  <strong>Profile Picture</strong>

                  <p>Update your profile picture later.</p>

                  <button className="settings-secondary-button">
                    Change Avatar
                  </button>
                </div>
              </div>

              <div className="settings-form-grid">
                <div className="settings-field">
                  <label>Full Name</label>

                  <input
                    type="text"
                    value={settings.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                  />
                </div>

                <div className="settings-field">
                  <label>Email Address</label>

                  <input
                    type="email"
                    value={settings.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* NOTIFICATIONS */}
          {activeSection === "notifications" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>Notifications</h2>

                <p>Choose how you want to receive updates.</p>
              </div>

              <SettingToggle
                title="Push Notifications"
                description="Receive important updates inside the dashboard."
                enabled={settings.notifications}
                onChange={() =>
                  handleChange("notifications", !settings.notifications)
                }
              />

              <SettingToggle
                title="Email Updates"
                description="Receive account and content updates by email."
                enabled={settings.emailUpdates}
                onChange={() =>
                  handleChange("emailUpdates", !settings.emailUpdates)
                }
              />
            </div>
          )}

          {/* AI PREFERENCES */}
          {activeSection === "ai" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>AI Preferences</h2>

                <p>Control how your AI assistant works.</p>
              </div>

              <SettingToggle
                title="AI Suggestions"
                description="Allow Nova to suggest content ideas and improvements."
                enabled={settings.aiSuggestions}
                onChange={() =>
                  handleChange("aiSuggestions", !settings.aiSuggestions)
                }
              />

              <SettingToggle
                title="Automatic Content Generation"
                description="Allow AI to prepare content automatically."
                enabled={settings.autoGenerate}
                onChange={() =>
                  handleChange("autoGenerate", !settings.autoGenerate)
                }
              />
            </div>
          )}

          {/* APPEARANCE */}
          {activeSection === "appearance" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>Appearance</h2>

                <p>Customize the look of your workspace.</p>
              </div>

              <SettingToggle
                title="Dark Mode"
                description="Use the dark interface for your workspace."
                enabled={settings.darkMode}
                onChange={() => handleChange("darkMode", !settings.darkMode)}
              />
            </div>
          )}
          {activeSection === "brand" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>Brand Settings</h2>
                <p>Manage the information used for your brand content.</p>
              </div>

              <div className="settings-form-grid">
                <div className="settings-field">
                  <label>Brand Name</label>
                  <input type="text" placeholder="Enter your brand name" />
                </div>

                <div className="settings-field">
                  <label>Website</label>
                  <input type="text" placeholder="https://example.com" />
                </div>
              </div>

              <div className="settings-field" style={{ marginTop: "20px" }}>
                <label>Brand Description</label>
                <textarea placeholder="Describe your brand..." rows="5" />
              </div>
            </div>
          )}

          {/* SECURITY */}
          {activeSection === "security" && (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>Security</h2>

                <p>Manage your account security settings.</p>
              </div>

              <div className="security-row">
                <div>
                  <strong>Password</strong>

                  <p>Change your account password.</p>
                </div>

                <button
                  className="settings-secondary-button"
                  onClick={() =>
                    alert(
                      "Password change feature will be available after backend integration.",
                    )
                  }
                >
                  Change Password
                </button>
              </div>

              <div className="security-row">
                <div>
                  <strong>Two-Factor Authentication</strong>

                  <p>Add an extra layer of account security.</p>
                </div>

                <button
                  className="settings-secondary-button"
                  onClick={() =>
                    alert(
                      "Two-Factor Authentication will be available after backend integration.",
                    )
                  }
                >
                  Configure
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

/* TOGGLE COMPONENT */

function SettingToggle({ title, description, enabled, onChange }) {
  return (
    <div className="setting-toggle-row">
      <div>
        <strong>{title}</strong>

        <p>{description}</p>
      </div>

      <button
        type="button"
        className={`toggle-switch ${enabled ? "enabled" : ""}`}
        onClick={onChange}
        aria-label={title}
        aria-pressed={enabled}
      >
        <span></span>
      </button>
    </div>
  );
}

export default Settings;
