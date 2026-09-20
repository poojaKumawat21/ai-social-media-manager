import React, { useMemo, useState } from "react";
import {
  CheckCircle2,
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  CalendarDays,
  Clock3,
  X,
} from "lucide-react";
import "./PublishedPosts.css";

const initialPosts = [
  {
    id: 1,
    title: "The Future of Generative AI",
    content:
      "Generative AI is transforming the way businesses create, communicate and grow.",
    platform: "Instagram",
    date: "Sep 18, 2026",
    time: "10:30 AM",
    status: "Published",
    reach: "12.4K",
    engagement: "8.6%",
  },
  {
    id: 2,
    title: "5 AI Trends to Watch",
    content:
      "Here are five AI trends that creators and businesses should keep an eye on.",
    platform: "LinkedIn",
    date: "Sep 17, 2026",
    time: "09:00 AM",
    status: "Published",
    reach: "8.7K",
    engagement: "7.2%",
  },
  {
    id: 3,
    title: "Build Smarter With AI",
    content:
      "AI tools can help you save time and focus more on creative work.",
    platform: "Facebook",
    date: "Sep 16, 2026",
    time: "06:30 PM",
    status: "Published",
    reach: "6.9K",
    engagement: "6.8%",
  },
  {
    id: 4,
    title: "AI Productivity Tips",
    content:
      "Simple ways to use AI to improve your daily productivity and workflow.",
    platform: "X",
    date: "Sep 15, 2026",
    time: "08:00 PM",
    status: "Published",
    reach: "5.6K",
    engagement: "5.9%",
  },
];

function PublishedPosts() {
  const [posts, setPosts] = useState(initialPosts);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("All");
  const [openMenu, setOpenMenu] = useState(null);

  const filteredPosts = useMemo(() => {
    return posts.filter((post) => {
      const matchesSearch =
        post.title.toLowerCase().includes(search.toLowerCase()) ||
        post.content.toLowerCase().includes(search.toLowerCase());

      const matchesPlatform =
        platformFilter === "All" ||
        post.platform === platformFilter;

      return matchesSearch && matchesPlatform;
    });
  }, [posts, search, platformFilter]);

  const handleView = (post) => {
    alert(`Viewing "${post.title}"`);
    setOpenMenu(null);
  };

  const handleDelete = (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this published post?"
    );

    if (!confirmed) return;

    setPosts((currentPosts) =>
      currentPosts.filter((post) => post.id !== id)
    );

    setOpenMenu(null);
  };

  return (
    <div className="published-page">
      <div className="published-header">
        <div className="published-title-row">
          <div className="published-title-icon">
            <CheckCircle2 size={22} />
          </div>

          <div>
            <h1>Published Posts</h1>
            <p>
              View and manage your published social media content.
            </p>
          </div>
        </div>
      </div>

      <div className="published-stats">
        <div className="published-stat-card">
          <div className="published-stat-icon purple">
            <CheckCircle2 size={18} />
          </div>

          <div>
            <span>Total Published</span>
            <strong>{posts.length}</strong>
          </div>
        </div>

        <div className="published-stat-card">
          <div className="published-stat-icon blue">
            <Eye size={18} />
          </div>

          <div>
            <span>Total Reach</span>
            <strong>33.6K</strong>
          </div>
        </div>

        <div className="published-stat-card">
          <div className="published-stat-icon green">
            <CheckCircle2 size={18} />
          </div>

          <div>
            <span>Avg. Engagement</span>
            <strong>7.1%</strong>
          </div>
        </div>
      </div>

      <div className="published-toolbar">
        <div className="published-search">
          <Search size={17} />

          <input
            type="text"
            placeholder="Search published posts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {search && (
            <button
              className="published-clear-search"
              onClick={() => setSearch("")}
            >
              <X size={15} />
            </button>
          )}
        </div>

        <div className="published-filters">
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
        </div>
      </div>

      <div className="published-card">
        <div className="published-card-header">
          <div>
            <h2>Published Content</h2>
            <p>{filteredPosts.length} posts found</p>
          </div>
        </div>

        {filteredPosts.length > 0 ? (
          <div className="published-list">
            {filteredPosts.map((post) => (
              <div
                className="published-post-row"
                key={post.id}
              >
                <div className="published-platform">
                  <div className="published-platform-icon">
                    <CheckCircle2 size={18} />
                  </div>

                  <span>{post.platform}</span>
                </div>

                <div className="published-post-content">
                  <h3>{post.title}</h3>
                  <p>{post.content}</p>
                </div>

                <div className="published-date">
                  <span>{post.date}</span>

                  <small>
                    <Clock3 size={13} />
                    {post.time}
                  </small>
                </div>

                <div className="published-reach">
                  <span>{post.reach}</span>
                  <small>Reach</small>
                </div>

                <div className="published-engagement">
                  <span>{post.engagement}</span>
                  <small>Engagement</small>
                </div>

                <div className="published-status">
                  <span>Published</span>
                </div>

                <div className="published-actions">
                  <button
                    className="published-menu-btn"
                    onClick={() =>
                      setOpenMenu(
                        openMenu === post.id ? null : post.id
                      )
                    }
                  >
                    <MoreHorizontal size={19} />
                  </button>

                  {openMenu === post.id && (
                    <div className="published-dropdown">
                      <button onClick={() => handleView(post)}>
                        <Eye size={15} />
                        View
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
          <div className="published-empty">
            <div className="published-empty-icon">
              <CheckCircle2 size={30} />
            </div>

            <h3>No published posts found</h3>

            <p>
              Try changing your search or platform filter.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PublishedPosts;