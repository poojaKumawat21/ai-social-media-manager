import React, { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import {
  CalendarClock,
  Search,
  MoreHorizontal,
  Edit3,
  Trash2,
  Clock3,
  Plus,
  X,
} from "lucide-react";
import "./ScheduledPosts.css";

// const initialPosts = [
//   {
//     id: 1,
//     title: "The Future of Generative AI",
//     content:
//       "Generative AI is transforming the way businesses create, communicate and grow.",
//     platform: "Instagram",
//     date: "Sep 22, 2026",
//     time: "10:30 AM",
//     status: "Scheduled",
//   },
//   {
//     id: 2,
//     title: "5 AI Trends to Watch",
//     content:
//       "Here are five AI trends that creators and businesses should keep an eye on.",
//     platform: "LinkedIn",
//     date: "Sep 23, 2026",
//     time: "09:00 AM",
//     status: "Scheduled",
//   },
//   {
//     id: 3,
//     title: "Build Smarter With AI",
//     content:
//       "AI tools can help you save time and focus more on creative work.",
//     platform: "Facebook",
//     date: "Sep 24, 2026",
//     time: "06:30 PM",
//     status: "Scheduled",
//   },
//   {
//     id: 4,
//     title: "AI Productivity Tips",
//     content:
//       "Simple ways to use AI to improve your daily productivity and workflow.",
//     platform: "X",
//     date: "Sep 25, 2026",
//     time: "08:00 PM",
//     status: "Scheduled",
//   },
// ];

function ScheduledPosts() {
  // const [posts, setPosts] = useState(initialPosts);
  const [posts, setPosts] = useState([]);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [openMenu, setOpenMenu] = useState(null);

  const filteredPosts = useMemo(() => {
    return posts.filter((post) => {
      const matchesSearch =
        post.title.toLowerCase().includes(search.toLowerCase()) ||
        post.content.toLowerCase().includes(search.toLowerCase());

      const matchesPlatform =
        platformFilter === "All" || post.platform === platformFilter;

      const matchesStatus =
        statusFilter === "All" || post.status === statusFilter;

      return matchesSearch && matchesPlatform && matchesStatus;
    });
  }, [posts, search, platformFilter, statusFilter]);

  const getPlatformIcon = () => {
    return <CalendarClock size={18} />;
  };

  const handleDelete = async (id) => {
  const confirmed = window.confirm(
    "Are you sure you want to cancel this scheduled post?"
  );

  if (!confirmed) return;

  try {
    await api.delete(`/scheduled-posts/${id}`);

    setPosts((currentPosts) =>
      currentPosts.filter((post) => post.id !== id)
    );

    setOpenMenu(null);

    alert("Scheduled post cancelled successfully.");
  } catch (error) {
    console.error(
      "Cancel scheduled post error:",
      error
    );

    alert(
      error.message ||
        "Unable to cancel scheduled post."
    );
  }
};
  const handleEdit = (post) => {
    alert(`Edit "${post.title}"`);
    setOpenMenu(null);
  };

  const handleSchedule = () => {
    alert("Schedule Post feature will be connected later.");
  };
useEffect(() => {
  const fetchScheduledPosts = async () => {
    try {
      const scheduledResult = await api.get("/scheduled-posts");
      const postsResult = await api.get("/posts");

      const allPosts = postsResult.posts || [];

      const postMap = new Map(
        allPosts.map((post) => [post.id, post])
      );

      const formattedPosts = (
        scheduledResult.scheduled_posts || []
      ).map((scheduledPost) => {
        const post = postMap.get(scheduledPost.post_id) || {};

        const scheduledDate = new Date(
          scheduledPost.scheduled_at
        );

        return {
          id: scheduledPost.id,
          postId: scheduledPost.post_id,

          title:
            post.post_idea ||
            post.topic ||
            "Scheduled Post",

          content: post.caption || "",

          platform:
            scheduledPost.platform === "linkedin"
              ? "LinkedIn"
              : scheduledPost.platform,

          date: scheduledDate.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          }),

          time: scheduledDate.toLocaleTimeString("en-US", {
            hour: "numeric",
            minute: "2-digit",
          }),

          status:
            scheduledPost.status === "scheduled"
              ? "Scheduled"
              : scheduledPost.status,
        };
      });

      setPosts(formattedPosts);
    } catch (error) {
      console.error(
        "Failed to fetch scheduled posts:",
        error
      );
    }
  };

    fetchScheduledPosts();

  const refreshInterval = setInterval(
    fetchScheduledPosts,
    10000
  );

  return () => {
    clearInterval(refreshInterval);
  };
}, []);
  return (
    <div className="scheduled-page">
      {/* HEADER */}
      <div className="scheduled-header">
        <div>
          <div className="scheduled-title-row">
            <div className="scheduled-title-icon">
              <CalendarClock size={22} />
            </div>

            <div>
              <h1>Scheduled Posts</h1>
              <p>
                Manage and monitor your upcoming social media posts.
              </p>
            </div>
          </div>
        </div>

        <button
          className="scheduled-primary-btn"
          onClick={handleSchedule}
        >
          <Plus size={17} />
          Schedule Post
        </button>
      </div>

      {/* STATS */}
      <div className="scheduled-stats">
        <div className="scheduled-stat-card">
          <div className="scheduled-stat-icon purple">
            <CalendarClock size={18} />
          </div>

          <div>
            <span>Total Scheduled</span>
            <strong>{posts.length}</strong>
          </div>
        </div>

        <div className="scheduled-stat-card">
          <div className="scheduled-stat-icon blue">
            <Clock3 size={18} />
          </div>

          <div>
            <span>Upcoming</span>
            <strong>
              {posts.filter((p) => p.status === "Scheduled").length}
            </strong>
          </div>
        </div>

        <div className="scheduled-stat-card">
          <div className="scheduled-stat-icon green">
            <CalendarClock size={18} />
          </div>

          <div>
            <span>Platforms</span>
            <strong>
              {new Set(posts.map((p) => p.platform)).size}
            </strong>
          </div>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="scheduled-toolbar">
        <div className="scheduled-search">
          <Search size={17} />

          <input
            type="text"
            placeholder="Search scheduled posts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {search && (
            <button
              className="scheduled-clear-search"
              onClick={() => setSearch("")}
            >
              <X size={15} />
            </button>
          )}
        </div>

        <div className="scheduled-filters">
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
          >
            <option value="All">All Platforms</option>
            <option value="Instagram">Instagram</option>
            <option value="Facebook">Facebook</option>
            <option value="LinkedIn">LinkedIn</option>
            <option value="X">X</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Status</option>
            <option value="Scheduled">Scheduled</option>
          </select>
        </div>
      </div>

      {/* POSTS */}
      <div className="scheduled-card">
        <div className="scheduled-card-header">
          <div>
            <h2>Upcoming Posts</h2>
            <p>{filteredPosts.length} posts found</p>
          </div>
        </div>

        {filteredPosts.length > 0 ? (
          <div className="scheduled-list">
            {filteredPosts.map((post) => (
              <div
                className="scheduled-post-row"
                key={post.id}
              >
                <div className="scheduled-platform">
                  <div
                    className={`platform-icon ${post.platform.toLowerCase()}`}
                  >
                    {getPlatformIcon()}
                  </div>

                  <span>{post.platform}</span>
                </div>

                <div className="scheduled-post-content">
                  <h3>{post.title}</h3>
                  <p>{post.content}</p>
                </div>

                <div className="scheduled-date">
                  <span>{post.date}</span>

                  <small>
                    <Clock3 size={13} />
                    {post.time}
                  </small>
                </div>

                <div className="scheduled-status">
                  <span>{post.status}</span>
                </div>

                <div className="scheduled-actions">
                  <button
                    className="scheduled-menu-btn"
                    onClick={() =>
                      setOpenMenu(
                        openMenu === post.id ? null : post.id
                      )
                    }
                  >
                    <MoreHorizontal size={19} />
                  </button>

                  {openMenu === post.id && (
                    <div className="scheduled-dropdown">
                      <button
                        onClick={() => handleEdit(post)}
                      >
                        <Edit3 size={15} />
                        Edit
                      </button>

                      <button
                        className="delete-action"
                        onClick={() => handleDelete(post.id)}
                      >
                        <Trash2 size={15} />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="scheduled-empty">
            <div className="scheduled-empty-icon">
              <CalendarClock size={30} />
            </div>

            <h3>No scheduled posts found</h3>

            <p>
              Try changing your filters or schedule a new post.
            </p>

            <button
              className="scheduled-primary-btn"
              onClick={handleSchedule}
            >
              <Plus size={16} />
              Schedule Post
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScheduledPosts;