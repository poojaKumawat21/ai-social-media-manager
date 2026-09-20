import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import "./Login.css";
import api from "../../services/api";

function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

const handleLogin = async (e) => {
  e.preventDefault();

  if (!formData.email.trim() || !formData.password.trim()) {
    alert("Please enter your email and password.");
    return;
  }

  setIsLoading(true);

  try {
    const result = await api.post("/auth/login", {
      email: formData.email.trim(),
      password: formData.password,
    });

    if (!result.access_token) {
      throw new Error("Access token was not received.");
    }

    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("user_id", result.user_id);
    localStorage.setItem("user_email", result.email);

    if (result.refresh_token) {
      localStorage.setItem("refresh_token", result.refresh_token);
    }

    // alert("Login successful!");

    try {
  await api.get("/profile");
  navigate("/");
} catch (error) {
  if (error.status === 404) {
    navigate("/profile-setup");
  } else {
    throw error;
  }
}
  } catch (error) {
    console.error("Login error:", error);

    alert(
      error.message ||
        "Unable to login. Please check your email and password.",
    );
  } finally {
    setIsLoading(false);
  }
};

  return (
    <div className="auth-page">

      {/* LEFT BRAND SECTION */}
      <div className="auth-brand-section">

        <div className="auth-brand-content">

          <div className="auth-logo">
            <div className="auth-logo-icon">
              <Sparkles size={18} />
            </div>

            <div>
              <strong>POSTPILOT</strong>
              <span>AI SOCIAL MEDIA MANAGER</span>
            </div>
          </div>

          <div className="auth-hero-text">
            <span className="auth-small-label">
              INTELLIGENT CONTENT MANAGEMENT
            </span>

            <h1>
              Create.
              <br />
              <span>Automate.</span>
              <br />
              Grow.
            </h1>

            <p>
              Your AI-powered social media manager for creating,
              planning and managing content across platforms.
            </p>
          </div>

          <div className="auth-feature-list">
            <div className="auth-feature">
              <span>✦</span>
              <div>
                <strong>AI Content Creation</strong>
                <p>Generate platform-ready content in seconds.</p>
              </div>
            </div>

            <div className="auth-feature">
              <span>✦</span>
              <div>
                <strong>Smart Automation</strong>
                <p>Plan and schedule your social media workflow.</p>
              </div>
            </div>

            <div className="auth-feature">
              <span>✦</span>
              <div>
                <strong>Performance Insights</strong>
                <p>Understand what is working for your audience.</p>
              </div>
            </div>
          </div>

        </div>

        <div className="auth-brand-glow"></div>
      </div>

      {/* RIGHT LOGIN SECTION */}
      <div className="auth-form-section">

        <div className="login-card">

          <div className="login-header">
            <span className="login-label">WELCOME BACK</span>

            <h2>Sign in to your account</h2>

            <p>
              Continue managing your social media with AI.
            </p>
          </div>

          <form onSubmit={handleLogin}>

            {/* EMAIL */}
            <div className="auth-field">

              <label htmlFor="email">
                Email Address
              </label>

              <div className="auth-input-wrapper">

                <Mail size={16} />

                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  autoComplete="email"
                />

              </div>
            </div>

            {/* PASSWORD */}
            <div className="auth-field">

              <div className="auth-field-label-row">
                <label htmlFor="password">
                  Password
                </label>

                <Link to="/forgot-password">
                  Forgot password?
                </Link>
              </div>

              <div className="auth-input-wrapper">

                <Lock size={16} />

                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword((prev) => !prev)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? (
                    <EyeOff size={15} />
                  ) : (
                    <Eye size={15} />
                  )}
                </button>

              </div>
            </div>

            {/* REMEMBER ME */}
            <div className="login-options">

              <label className="remember-me">

                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) =>
                    setRememberMe(e.target.checked)
                  }
                />

                <span className="custom-checkbox"></span>

                <span>Remember me</span>

              </label>

            </div>

            {/* LOGIN BUTTON */}
            <button
              type="submit"
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="login-spinner"></span>
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight size={15} />
                </>
              )}
            </button>

          </form>

          {/* DIVIDER */}
          <div className="auth-divider">
            <span>OR CONTINUE WITH</span>
          </div>

          {/* SOCIAL LOGIN */}
          <div className="social-login-buttons">

            <button
              type="button"
              className="social-login-button"
              onClick={() =>
                alert("Google login will be connected later.")
              }
            >
              <span className="social-icon google-icon">G</span>
              Google
            </button>

            <button
              type="button"
              className="social-login-button"
              onClick={() =>
                alert("GitHub login will be connected later.")
              }
            >
              <span className="social-icon github-icon">GH</span>
              GitHub
            </button>

          </div>

          {/* REGISTER */}
          <div className="register-link">

            <span>Don't have an account?</span>

            <Link to="/register">
              Create an account
              <ArrowRight size={12} />
            </Link>

          </div>

          {/* FOOTER */}
          <div className="auth-security-note">
            <Lock size={11} />
            <span>Your account is protected with secure authentication.</span>
          </div>

        </div>

      </div>

    </div>
  );
}

export default Login;