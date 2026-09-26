import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../services/api";


import {
  Sparkles,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  ArrowRight,
} from "lucide-react";
import "./Register.css";

function Register() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

const handleSubmit = async (e) => {
  e.preventDefault();

  if (formData.password !== formData.confirmPassword) {
    alert("Passwords do not match.");
    return;
  }

  try {
    const result = await api.post("/auth/register", {
      email: formData.email.trim(),
      password: formData.password,
    });

    console.log("Registration successful:", result);

    alert(
      "Registration successful! Please check your email for confirmation."
    );

    navigate("/login");
  } catch (error) {
    console.error("Registration error:", error);

    alert(
      error.message ||
        "Unable to create account. Please try again."
    );
  }
};

  return (
    <div className="register-page">

      {/* LEFT BRAND SECTION */}
      <div className="register-brand">

        <div className="register-logo">
          <div className="register-logo-icon">
            <Sparkles size={22} />
          </div>

          <div>
            <h2>PostPilot AI</h2>
            <span>AI Social Media Manager</span>
          </div>
        </div>

        <div className="register-brand-content">
          <span className="register-badge">
            <Sparkles size={14} />
            AI-Powered Social Media
          </span>

          <h1>
            Create content.
            <br />
            <span>Grow smarter.</span>
          </h1>

          <p>
            Build, automate and manage your social media
            presence with the power of AI.
          </p>
        </div>

        <div className="register-glow"></div>
      </div>


      {/* RIGHT FORM SECTION */}
      <div className="register-form-section">

        <div className="register-form-container">

          <div className="register-heading">
            <h1>Create your account</h1>
            <p>
              Start managing your social media with AI.
            </p>
          </div>


          <form onSubmit={handleSubmit}>

            {/* NAME */}
            <div className="register-input-group">
              <label>Full Name</label>

              <div className="register-input">
                <User size={17} />

                <input
                  type="text"
                  name="name"
                  placeholder="Enter your name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>


            {/* EMAIL */}
            <div className="register-input-group">
              <label>Email Address</label>

              <div className="register-input">
                <Mail size={17} />

                <input
                  type="email"
                  name="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>


            {/* PASSWORD */}
            <div className="register-input-group">
              <label>Password</label>

              <div className="register-input">
                <Lock size={17} />

                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                >
                  {showPassword ? (
                    <EyeOff size={17} />
                  ) : (
                    <Eye size={17} />
                  )}
                </button>
              </div>
            </div>


            {/* CONFIRM PASSWORD */}
            <div className="register-input-group">
              <label>Confirm Password</label>

              <div className="register-input">
                <Lock size={17} />

                <input
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirmPassword"
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowConfirmPassword(
                      !showConfirmPassword
                    )
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOff size={17} />
                  ) : (
                    <Eye size={17} />
                  )}
                </button>
              </div>
            </div>


            {/* TERMS */}
            <label className="register-terms">
              <input type="checkbox" required />
              <span>
                I agree to the Terms of Service and Privacy Policy.
              </span>
            </label>


            {/* BUTTON */}
            <button
              type="submit"
              className="register-submit"
            >
              <span>Create Account</span>
              <ArrowRight size={17} />
            </button>

          </form>


          {/* LOGIN LINK */}
          <div className="register-login-link">
            Already have an account?
            <Link to="/login">Login</Link>
          </div>


          {/* BACK */}
          <button
            className="register-back"
            onClick={() => navigate("/")}
          >
            ← Back to Dashboard
          </button>

        </div>

      </div>
    </div>
  );
}

export default Register;