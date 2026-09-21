import React, { useState } from "react";
import "./BrandSettings.css";

function BrandSettings() {
  const [brandName, setBrandName] = useState("Your Brand");
  const [description, setDescription] = useState("");
  const [website, setWebsite] = useState("");

  const handleSave = () => {
    alert("Brand settings saved successfully.");
  };

  return (
    <div className="brand-settings-page">
      <div className="brand-settings-header">
        <div>
          <span className="settings-label">BRAND CONTROL</span>
          <h1>Brand Settings</h1>
          <p>
            Manage your brand information used for social media content.
          </p>
        </div>

        <button
          className="settings-save-button"
          onClick={handleSave}
        >
          Save Changes
        </button>
      </div>

      <div className="brand-settings-card">
        <div className="brand-settings-card-header">
          <h2>Brand Information</h2>
          <p>Set the basic information about your brand.</p>
        </div>

        <div className="brand-settings-form">
          <div className="brand-settings-field">
            <label>Brand Name</label>
            <input
              type="text"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="Enter brand name"
            />
          </div>

          <div className="brand-settings-field">
            <label>Website</label>
            <input
              type="text"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://example.com"
            />
          </div>

          <div className="brand-settings-field full-width">
            <label>Brand Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your brand..."
              rows="5"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default BrandSettings;