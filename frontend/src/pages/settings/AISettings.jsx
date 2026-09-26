import React, { useState } from "react";
import "./AISettings.css";

function AISettings() {
  const [suggestions, setSuggestions] = useState(true);
  const [autoGenerate, setAutoGenerate] = useState(false);
  const [tone, setTone] = useState("Professional");
  const [language, setLanguage] = useState("English");

  const handleSave = () => {
    alert("AI settings saved successfully.");
  };

  return (
    <div className="ai-settings-page">
      <div className="ai-settings-header">
        <div>
          <span className="settings-label">AI CONTROL</span>
          <h1>AI Settings</h1>
          <p>Customize how AI creates and improves your content.</p>
        </div>

        <button className="settings-save-button" onClick={handleSave}>
          Save Changes
        </button>
      </div>

      <div className="ai-settings-card">
        <div className="ai-settings-card-header">
          <h2>AI Preferences</h2>
          <p>Control the behaviour and style of your AI assistant.</p>
        </div>

        <div className="ai-setting-row">
          <div>
            <strong>AI Suggestions</strong>
            <p>Get AI-powered content ideas and improvements.</p>
          </div>

          <button
            className={`ai-toggle ${suggestions ? "enabled" : ""}`}
            onClick={() => setSuggestions(!suggestions)}
          >
            <span></span>
          </button>
        </div>

        <div className="ai-setting-row">
          <div>
            <strong>Automatic Content Generation</strong>
            <p>Allow AI to prepare content automatically.</p>
          </div>

          <button
            className={`ai-toggle ${autoGenerate ? "enabled" : ""}`}
            onClick={() => setAutoGenerate(!autoGenerate)}
          >
            <span></span>
          </button>
        </div>

        <div className="ai-settings-form">
          <div className="ai-settings-field">
            <label>Content Tone</label>
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              <option>Professional</option>
              <option>Friendly</option>
              <option>Creative</option>
              <option>Educational</option>
            </select>
          </div>

          <div className="ai-settings-field">
            <label>Content Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option>English</option>
              <option>Hindi</option>
              <option>Hinglish</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AISettings;