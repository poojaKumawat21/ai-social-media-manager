import React, { useState } from "react";
import "./SecuritySettings.css";

function SecuritySettings() {
  const [twoFactor, setTwoFactor] = useState(false);

  const handleSave = () => {
    alert("Security settings saved successfully.");
  };

  return (
    <div className="security-settings-page">
      <div className="security-settings-header">
        <div>
          <span className="settings-label">ACCOUNT SECURITY</span>
          <h1>Security</h1>
          <p>Manage your password and account security.</p>
        </div>

        <button className="settings-save-button" onClick={handleSave}>
          Save Changes
        </button>
      </div>

      <div className="security-settings-card">
        <div className="security-settings-card-header">
          <h2>Password</h2>
          <p>Keep your account protected with a strong password.</p>
        </div>

        <div className="security-action-row">
          <div>
            <strong>Change Password</strong>
            <p>Update your account password.</p>
          </div>

          <button
            className="settings-secondary-button"
            onClick={() =>
              alert("Password change will be available after backend integration.")
            }
          >
            Change Password
          </button>
        </div>

        <div className="security-settings-card-header security-two-factor-header">
          <h2>Two-Factor Authentication</h2>
          <p>Add an extra layer of protection to your account.</p>
        </div>

        <div className="security-action-row">
          <div>
            <strong>Enable 2FA</strong>
            <p>
              Require an additional verification step when signing in.
            </p>
          </div>

          <button
            className={`security-toggle ${twoFactor ? "enabled" : ""}`}
            onClick={() => setTwoFactor(!twoFactor)}
          >
            <span></span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default SecuritySettings;