import React from "react";
import "./Dashboard.css";
import EngagementChart from "../components/analytics/EngagementChart";
import AIInsightCard from "../components/dashboard/AIInsightCard";
import AIAssistant from "../components/dashboard/AIAssistant";
import { useNavigate } from "react-router-dom";


function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Manage and monitor your social media content</p>
        </div>

        <button
          className="primary-btn"
          onClick={() => navigate("/create-post")}
        >
          + Create Post
        </button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Posts</span>
          <h2>128</h2>
          <p>↑ 12% this month</p>
        </div>

        <div className="stat-card">
          <span>Scheduled</span>
          <h2>24</h2>
          <p>8 posts this week</p>
        </div>

        <div className="stat-card">
          <span>Engagement</span>
          <h2>8.4K</h2>
          <p>↑ 18.5%</p>
        </div>

        <div className="stat-card">
          <span>Followers</span>
          <h2>24.8K</h2>
          <p>↑ 6.2%</p>
        </div>
      </div>

      {/* Main Cards */}
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-header">
            <h3>Recent Posts</h3>
            <span
              className="view-all-link"
              onClick={() => navigate("/published-posts")}
            >
              View all →
            </span>
          </div>

          <div className="post-item">
            <div>
              <strong>AI Trends in 2026</strong>
              <p>Instagram • Published</p>
            </div>
            <span>2.4K views</span>
          </div>

          <div className="post-item">
            <div>
              <strong>5 AI Tools Every Creator Needs</strong>
              <p>LinkedIn • Published</p>
            </div>
            <span>1.8K views</span>
          </div>

          <div className="post-item">
            <div>
              <strong>Future of Social Media</strong>
              <p>Twitter • Scheduled</p>
            </div>
            <span>Tomorrow</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <h3>Quick Actions</h3>
          </div>

          <button
            className="action-btn"
            onClick={() => navigate("/create-post")}
          >
            ✦ Generate AI Post
          </button>

          <button className="action-btn" onClick={() => navigate("/ai-ideas")}>
            ◇ Generate Content Ideas
          </button>

          <button
            className="action-btn"
            onClick={() => navigate("/content-calendar")}
          >
            ◷ Schedule a Post
          </button>

          <button className="action-btn" onClick={() => navigate("/analytics")}>
            ▣ View Analytics
          </button>
        </div>
      </div>

      <EngagementChart />
      <AIInsightCard />
      <AIAssistant />

      {/* AI Section */}
      <div className="ai-banner">
        <div>
          <h2>✦ Let AI handle your social media</h2>
          <p>
            Generate smarter content, discover trends and grow your audience.
          </p>
        </div>

        <button className="primary-btn">Explore AI Tools →</button>
      </div>
    </div>
  );
}

export default Dashboard;
