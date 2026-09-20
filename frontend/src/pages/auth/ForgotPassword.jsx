import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, ArrowRight, Sparkles, CheckCircle } from "lucide-react";
import "./ForgotPassword.css";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!email.trim()) return;

    // Backend password-reset API will be connected later
    setSubmitted(true);
  };

  return (
    <div className="forgot-page">

      {/* BRAND */}
      <div className="forgot-brand">

        <div className="forgot-logo">
          <div className="forgot-logo-icon">
            <Sparkles size={22} />
          </div>

          <div>
            <h2>PostPilot AI</h2>
            <span>AI Social Media Manager</span>
          </div>
        </div>

        <div className="forgot-brand-content">
          <span className="forgot-badge">
            <Sparkles size={14} />
            Secure Account Recovery
          </span>

          <h1>
            Get back to
            <br />
            <span>creating.</span>
          </h1>

          <p>
            Don't worry. We'll help you get back into your
            PostPilot AI account securely.
          </p>
        </div>

        <div className="forgot-glow"></div>

      </div>


      {/* FORM */}
      <div className="forgot-form-section">

        <div className="forgot-form-container">

          {!submitted ? (
            <>
              <div className="forgot-heading">
                <h1>Forgot your password?</h1>

                <p>
                  Enter your email address and we'll send you
                  instructions to reset your password.
                </p>
              </div>

              <form onSubmit={handleSubmit}>

                <div className="forgot-input-group">
                  <label>Email Address</label>

                  <div className="forgot-input">
                    <Mail size={17} />

                    <input
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="forgot-submit"
                >
                  <span>Send Reset Link</span>
                  <ArrowRight size={17} />
                </button>

              </form>

              <div className="forgot-login">
                Remember your password?
                <Link to="/login">Login</Link>
              </div>
            </>
          ) : (
            <div className="forgot-success">

              <div className="forgot-success-icon">
                <CheckCircle size={30} />
              </div>

              <h1>Check your email</h1>

              <p>
                If an account exists for{" "}
                <strong>{email}</strong>, you'll receive
                password reset instructions.
              </p>

              <Link
                to="/login"
                className="forgot-back-login"
              >
                Back to Login
              </Link>

            </div>
          )}

        </div>

      </div>

    </div>
  );
}

export default ForgotPassword;