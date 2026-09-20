import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  User,
  Calendar,
  Briefcase,
  Languages,
  MessageCircle,
  ArrowRight,
} from "lucide-react";
import api from "../services/api";
import "./ProfileSetup.css";

function ProfileSetup() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    dob: "",
    niche: "",
    language: "English",
    tone: "Professional",
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (
      !formData.name.trim() ||
      !formData.dob ||
      !formData.niche.trim()
    ) {
      alert("Please fill in all required fields.");
      return;
    }

    setIsSaving(true);

    try {
      const result = await api.post("/profile", {
        name: formData.name.trim(),
        dob: formData.dob,
        niche: formData.niche.trim(),
        language: formData.language,
        tone: formData.tone,
      });

      console.log("Profile created:", result);

      navigate("/");
    } catch (error) {
      console.error("Profile setup error:", error);

      alert(
        error.message ||
          "Unable to save your profile. Please try again.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="profile-setup-page">
      {/* LEFT BRAND SECTION */}
      <div className="profile-setup-brand">
        <div className="profile-setup-logo">
          <div className="profile-setup-logo-icon">
            <Sparkles size={22} />
          </div>

          <div>
            <h2>PostPilot AI</h2>
            <span>AI Social Media Manager</span>
          </div>
        </div>

        <div className="profile-setup-brand-content">
          <span className="profile-setup-badge">
            <Sparkles size={14} />
            AI-Powered Social Media
          </span>

          <h1>
            Let AI understand
            <br />
            <span>your brand.</span>
          </h1>

          <p>
            Tell PostPilot a little about yourself so your AI-generated
            content can match your field, audience and communication style.
          </p>
        </div>

        <div className="profile-setup-glow"></div>
      </div>

      {/* RIGHT FORM SECTION */}
      <div className="profile-setup-form-section">
        <div className="profile-setup-form-container">
          <div className="profile-setup-heading">
            <h1>Set up your profile</h1>
            <p>
              Complete your profile before creating AI-powered content.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            {/* NAME */}
            <div className="profile-setup-input-group">
              <label>Full Name</label>

              <div className="profile-setup-input">
                <User size={17} />

                <input
                  type="text"
                  name="name"
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* DOB */}
            <div className="profile-setup-input-group">
              <label>Date of Birth</label>

              <div className="profile-setup-input">
                <Calendar size={17} />

                <input
                  type="date"
                  name="dob"
                  value={formData.dob}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* NICHE */}
            <div className="profile-setup-input-group">
              <label>Your Field / Niche</label>

              <div className="profile-setup-input">
                <Briefcase size={17} />

                <input
                  type="text"
                  name="niche"
                  placeholder="e.g. Digital Marketing, Fashion, Education"
                  value={formData.niche}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* LANGUAGE */}
            <div className="profile-setup-input-group">
              <label>Content Language</label>

              <div className="profile-setup-input">
                <Languages size={17} />

                <select
                  name="language"
                  value={formData.language}
                  onChange={handleChange}
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi</option>
                  <option value="Hinglish">Hinglish</option>
                </select>
              </div>
            </div>

            {/* TONE */}
            <div className="profile-setup-input-group">
              <label>Preferred Tone</label>

              <div className="profile-setup-input">
                <MessageCircle size={17} />

                <select
                  name="tone"
                  value={formData.tone}
                  onChange={handleChange}
                >
                  <option value="Professional">Professional</option>
                  <option value="Friendly">Friendly</option>
                  <option value="Funny">Funny</option>
                  <option value="Educational">Educational</option>
                  <option value="Inspirational">Inspirational</option>
                  <option value="Casual">Casual</option>
                </select>
              </div>
            </div>

            {/* BUTTON */}
            <button
              type="submit"
              className="profile-setup-submit"
              disabled={isSaving}
            >
              <span>
                {isSaving ? "Saving Profile..." : "Continue to Dashboard"}
              </span>

              {!isSaving && <ArrowRight size={17} />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ProfileSetup;