import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import EngagementChart from "../components/analytics/EngagementChart";
import AIInsightCard from "../components/dashboard/AIInsightCard";
import AIAssistant from "../components/dashboard/AIAssistant";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const [posts, setPosts] = useState([]);
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_BASE = "http://127.0.0.1:8000";

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem("access_token");

      const headers = {
        Authorization: `Bearer ${token}`,
      };

      const [postsResponse, scheduledResponse] = await Promise.all([
        fetch(`${API_BASE}/posts`, {
          headers,
        }),
        fetch(`${API_BASE}/scheduled-posts`, {
          headers,
        }),
      ]);

      if (postsResponse.ok) {
        const postsData = await postsResponse.json();
        setPosts(postsData.posts || []);
      }

      if (scheduledResponse.ok) {
        const scheduledData = await scheduledResponse.json();
        setScheduledPosts(
          scheduledData.scheduled_posts || []
        );
      }
    } catch (error) {
      console.error("Dashboard data fetch failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const publishedPosts = posts.filter(
    (post) => post.status === "published"
  );

  const draftPosts = posts.filter(
    (post) => post.status === "draft"
  );

  const activeScheduledPosts = scheduledPosts.filter(
    (post) => post.status === "scheduled"
  );

  const recentPosts = posts.slice(0, 3);

  const formatDate = (date) => {
    if (!date) return "";

    return new Date(date).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

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
          <h2>{loading ? "..." : posts.length}</h2>
          <p>
            {loading
              ? "Loading..."
              : `${publishedPosts.length} published • ${draftPosts.length} drafts`}
          </p>
        </div>

        <div className="stat-card">
          <span>Scheduled</span>
          <h2>
            {loading ? "..." : activeScheduledPosts.length}
          </h2>
          <p>
            {activeScheduledPosts.length === 1
              ? "1 upcoming post"
              : `${activeScheduledPosts.length} upcoming posts`}
          </p>
        </div>

        <div className="stat-card">
          <span>Engagement</span>
          <h2>—</h2>
          <p>Analytics coming soon</p>
        </div>

        <div className="stat-card">
          <span>Followers</span>
          <h2>—</h2>
          <p>Analytics coming soon</p>
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

          {loading ? (
            <div className="post-item">
              <div>
                <strong>Loading posts...</strong>
              </div>
            </div>
          ) : recentPosts.length === 0 ? (
            <div className="post-item">
              <div>
                <strong>No posts yet</strong>
                <p>Create your first AI post</p>
              </div>
            </div>
          ) : (
            recentPosts.map((post) => {
              const scheduledPost = scheduledPosts.find(
                (scheduled) =>
                  scheduled.post_id === post.id &&
                  scheduled.status === "scheduled"
              );

              const status = scheduledPost
                ? "Scheduled"
                : post.status
                ? post.status.charAt(0).toUpperCase() +
                  post.status.slice(1)
                : "Generated";

              return (
                <div className="post-item" key={post.id}>
                  <div>
                    <strong>
                      {post.post_idea ||
                        post.topic ||
                        "Untitled Post"}
                    </strong>

                    <p>
                      {scheduledPost?.platform
                        ? scheduledPost.platform.charAt(0).toUpperCase() +
                          scheduledPost.platform.slice(1)
                        : "LinkedIn"}{" "}
                      • {status}
                    </p>
                  </div>

                  <span>
                    {scheduledPost
                      ? formatDate(scheduledPost.scheduled_at)
                      : formatDate(post.created_at)}
                  </span>
                </div>
              );
            })
          )}
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

          <button
            className="action-btn"
            onClick={() => navigate("/ai-ideas")}
          >
            ◇ Generate Content Ideas
          </button>

          <button
            className="action-btn"
            onClick={() => navigate("/content-calendar")}
          >
            ◷ Schedule a Post
          </button>

          <button
            className="action-btn"
            onClick={() => navigate("/analytics")}
          >
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

        <button
          className="primary-btn"
          onClick={() => navigate("/create-post")}
        >
          Explore AI Tools →
        </button>
      </div>
    </div>
  );
}

export default Dashboard;