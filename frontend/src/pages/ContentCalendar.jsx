import React from "react";
import "./ContentCalendar.css";

function ContentCalendar() {
  return (
    <div className="content-calendar-page">

      <div className="page-header">
        <div>
          <span className="calendar-label">CONTENT MANAGEMENT</span>
          <h1>Content Calendar</h1>
          <p>
            Plan, organize and schedule your social media content.
          </p>
        </div>

        <button className="primary-btn">
          + Schedule Post
        </button>
      </div>

      <div className="calendar-card">

        <div className="calendar-top">
          <div>
            <h3>September 2026</h3>
            <p>Your scheduled and planned content</p>
          </div>

          <div className="calendar-controls">
            <button>←</button>
            <button>Today</button>
            <button>→</button>
          </div>
        </div>

        <div className="calendar-placeholder">
          <div className="calendar-icon">▣</div>

          <h3>Your content calendar</h3>

          <p>
            Scheduled posts and content plans will appear here.
          </p>
        </div>

      </div>

    </div>
  );
}

export default ContentCalendar;