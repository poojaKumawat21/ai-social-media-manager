import React from "react";
import "./Analytics.css";

function Analytics() {
  const stats = [
    {
      label: "TOTAL POSTS",
      value: "128",
      change: "+12.5%",
    },
    {
      label: "TOTAL REACH",
      value: "48.6K",
      change: "+18.2%",
    },
    {
      label: "ENGAGEMENT",
      value: "7.8%",
      change: "+2.4%",
    },
    {
      label: "FOLLOWERS",
      value: "12.4K",
      change: "+8.7%",
    },
  ];

  return (
    <div className="analytics-page">

      {/* HEADER */}
      <div className="page-header">
        <div>
          <span className="analytics-label">PERFORMANCE</span>

          <h1>Analytics</h1>

          <p>
            Track your social media performance and audience growth.
          </p>
        </div>

        <button className="analytics-date-button">
          Last 30 Days ▾
        </button>
      </div>

      {/* STATS */}
      <div className="analytics-stats-grid">
        {stats.map((stat) => (
          <div className="analytics-stat-card" key={stat.label}>
            <span>{stat.label}</span>

            <div className="analytics-stat-bottom">
              <strong>{stat.value}</strong>

              <small>{stat.change}</small>
            </div>
          </div>
        ))}
      </div>

      {/* MAIN ANALYTICS GRID */}
      <div className="analytics-main-grid">

        {/* ENGAGEMENT */}
        <div className="analytics-card engagement-card">
          <div className="analytics-card-header">
            <div>
              <span>ENGAGEMENT</span>
              <h3>Engagement Overview</h3>
            </div>

            <span className="analytics-period">
              30 days
            </span>
          </div>

          <div className="chart-placeholder">
            <div className="chart-line">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div className="chart-labels">
              <span>Week 1</span>
              <span>Week 2</span>
              <span>Week 3</span>
              <span>Week 4</span>
            </div>
          </div>
        </div>

        {/* PLATFORM */}
        <div className="analytics-card platform-card">
          <div className="analytics-card-header">
            <div>
              <span>PLATFORMS</span>
              <h3>Platform Performance</h3>
            </div>
          </div>

          <div className="platform-list">

            <div className="platform-row">
              <div>
                <strong>Instagram</strong>
                <span>42% engagement</span>
              </div>

              <div className="platform-progress">
                <span style={{ width: "82%" }}></span>
              </div>
            </div>

            <div className="platform-row">
              <div>
                <strong>LinkedIn</strong>
                <span>31% engagement</span>
              </div>

              <div className="platform-progress">
                <span style={{ width: "65%" }}></span>
              </div>
            </div>

            <div className="platform-row">
              <div>
                <strong>Facebook</strong>
                <span>18% engagement</span>
              </div>

              <div className="platform-progress">
                <span style={{ width: "48%" }}></span>
              </div>
            </div>

            <div className="platform-row">
              <div>
                <strong>X</strong>
                <span>12% engagement</span>
              </div>

              <div className="platform-progress">
                <span style={{ width: "32%" }}></span>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* BOTTOM GRID */}
      <div className="analytics-bottom-grid">

        {/* BEST POSTS */}
        <div className="analytics-card best-posts-card">
          <div className="analytics-card-header">
            <div>
              <span>TOP CONTENT</span>
              <h3>Best Performing Posts</h3>
            </div>
          </div>

          <div className="best-post-list">

            <div className="best-post">
              <div className="post-rank">01</div>

              <div className="best-post-info">
                <strong>How AI is changing the future</strong>
                <span>Instagram • 2 days ago</span>
              </div>

              <div className="post-engagement">
                <strong>8.9K</strong>
                <span>engagement</span>
              </div>
            </div>

            <div className="best-post">
              <div className="post-rank">02</div>

              <div className="best-post-info">
                <strong>5 AI tools every creator needs</strong>
                <span>LinkedIn • 5 days ago</span>
              </div>

              <div className="post-engagement">
                <strong>6.4K</strong>
                <span>engagement</span>
              </div>
            </div>

            <div className="best-post">
              <div className="post-rank">03</div>

              <div className="best-post-info">
                <strong>Future of social media</strong>
                <span>Facebook • 8 days ago</span>
              </div>

              <div className="post-engagement">
                <strong>4.8K</strong>
                <span>engagement</span>
              </div>
            </div>

          </div>
        </div>

        {/* AI INSIGHTS */}
        <div className="analytics-card ai-insights-card">
          <div className="analytics-card-header">
            <div>
              <span>AI ANALYSIS</span>
              <h3>AI Insights</h3>
            </div>

            <div className="ai-insight-icon">✦</div>
          </div>

          <div className="ai-insight-content">
            <h4>Your content is performing well.</h4>

            <p>
              Educational AI content is currently generating higher
              engagement. Consider creating more posts around practical
              AI tips and trends.
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}

export default Analytics;