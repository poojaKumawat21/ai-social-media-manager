import React, { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  Clock3,
  X,
} from "lucide-react";
import "./PublishedPosts.css";
import api from "../services/api";

function PublishedPosts() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("All");
  const [openMenu, setOpenMenu] = useState(null);

  // =========================================================
  // LOAD PUBLISHED POSTS
  // =========================================================

  useEffect(() => {
    const loadPublishedPosts = async () => {
      try {
        setLoading(true);
        setError("");

        const result = await api.get("/posts");

        const allPosts = result?.posts || [];

        console.log("ALL POSTS FROM BACKEND:", allPosts);

        /*
         * A single DB post can contain multiple platforms.
         *
         * Example:
         *
         * platforms:
         * ["instagram", "linkedin", "x"]
         *
         * platform_status:
         * {
         *   instagram: "published",
         *   linkedin: "published",
         *   x: "pending"
         * }
         *
         * We only show the platforms whose status is
         * actually "published".
         */

        const publishedRows = [];

        allPosts.forEach((post) => {
          const platformStatuses = post?.platform_status || {};
          const platformVariants = post?.platform_variants || {};

          Object.entries(platformStatuses).forEach(
            ([platform, status]) => {
              if (status !== "published") {
                return;
              }

              const variant =
                platformVariants?.[platform] || {};

              /*
               * platform_post_id is saved by the backend
               * when publishing.
               */
              const platformPostId =
                variant?.platform_post_id ||
                null;

              publishedRows.push({
                id: `${post.id}-${platform}`,

                parentPostId: post.id,

                platform,

                platformPostId,

                topic:
                  post.topic ||
                  variant.topic ||
                  "Untitled post",

                title:
                  post.topic ||
                  variant.topic ||
                  "Untitled post",

                content:
                  variant.caption ||
                  post.caption ||
                  "",

                hashtags:
                  variant.hashtags ||
                  post.hashtags ||
                  [],

                mediaUrls:
                  variant.media_urls ||
                  post.media_urls ||
                  [],

                createdAt: post.created_at,

                status: "Published",

                /*
                 * Analytics will populate these later.
                 */
                reach: "--",

                engagement: "--",
              });
            },
          );
        });

        console.log(
          "PUBLISHED PLATFORM ROWS:",
          publishedRows,
        );

        setPosts(publishedRows);
      } catch (err) {
        console.error(
          "Published posts load error:",
          err,
        );

        setError(
          "Failed to load published posts.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadPublishedPosts();
  }, []);

  // =========================================================
  // FORMAT PLATFORM NAME
  // =========================================================

  const formatPlatform = (platform) => {
    if (!platform) {
      return "";
    }

    if (platform.toLowerCase() === "x") {
      return "X";
    }

    return (
      platform.charAt(0).toUpperCase() +
      platform.slice(1)
    );
  };

  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (dateValue) => {
    if (!dateValue) {
      return "--";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
      return "--";
    }

    return date.toLocaleDateString(
      "en-US",
      {
        month: "short",
        day: "numeric",
        year: "numeric",
      },
    );
  };

  // =========================================================
  // FORMAT TIME
  // =========================================================

  const formatTime = (dateValue) => {
    if (!dateValue) {
      return "--";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
      return "--";
    }

    return date.toLocaleTimeString(
      "en-US",
      {
        hour: "2-digit",
        minute: "2-digit",
      },
    );
  };

  // =========================================================
  // FILTER POSTS
  // =========================================================

  const filteredPosts = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase();

    return posts.filter((post) => {
      const searchableText = [
        post.title,
        post.content,
        post.topic,
        post.platform,
        ...(post.hashtags || []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !normalizedSearch ||
        searchableText.includes(
          normalizedSearch,
        );

      const matchesPlatform =
        platformFilter === "All" ||
        formatPlatform(post.platform) ===
          platformFilter;

      return (
        matchesSearch &&
        matchesPlatform
      );
    });
  }, [
    posts,
    search,
    platformFilter,
  ]);

  // =========================================================
  // VIEW POST
  // =========================================================

  const handleView = (post) => {
    const hashtags =
      post.hashtags?.length
        ? `\n\nHashtags: ${post.hashtags.join(" ")}`
        : "";

    const platformId =
      post.platformPostId
        ? `\n\nPlatform Post ID: ${post.platformPostId}`
        : "";

    alert(
      `${formatPlatform(post.platform)}\n\n` +
        `${post.content || post.title}` +
        `${hashtags}` +
        `${platformId}`,
    );

    setOpenMenu(null);
  };

  // =========================================================
  // DELETE POST
  // =========================================================

  const handleDelete = async (post) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this published post?",
    );

    if (!confirmed) {
      return;
    }

    try {
      /*
       * IMPORTANT:
       *
       * We delete the parent post from backend.
       *
       * The database post can contain multiple platforms,
       * so deleting the parent removes the whole generated post.
       */
      await api.delete(
        `/posts/${post.parentPostId}`,
      );

      setPosts((currentPosts) =>
        currentPosts.filter(
          (item) =>
            item.parentPostId !==
            post.parentPostId,
        ),
      );

      setOpenMenu(null);
    } catch (err) {
      console.error(
        "Delete published post error:",
        err,
      );

      alert(
        "Failed to delete the post.",
      );
    }
  };

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
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
                View and manage your published
                social media content.
              </p>
            </div>
          </div>
        </div>

        <div className="published-card">
          <div className="published-empty">
            <div className="published-empty-icon">
              <CheckCircle2 size={30} />
            </div>

            <h3>Loading published posts...</h3>

            <p>
              Fetching your published content.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================
  // MAIN UI
  // =========================================================

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
              View and manage your published
              social media content.
            </p>
          </div>
        </div>
      </div>

      {/* =====================================================
          STATS
      ===================================================== */}

      <div className="published-stats">
        <div className="published-stat-card">
          <div className="published-stat-icon purple">
            <CheckCircle2 size={18} />
          </div>

          <div>
            <span>Total Published</span>
            <strong>
              {posts.length}
            </strong>
          </div>
        </div>

        <div className="published-stat-card">
          <div className="published-stat-icon blue">
            <Eye size={18} />
          </div>

          <div>
            <span>Total Reach</span>
            <strong>--</strong>
          </div>
        </div>

        <div className="published-stat-card">
          <div className="published-stat-icon green">
            <CheckCircle2 size={18} />
          </div>

          <div>
            <span>Avg. Engagement</span>
            <strong>--</strong>
          </div>
        </div>
      </div>

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div
          style={{
            marginBottom: "18px",
            padding: "12px 14px",
            borderRadius: "9px",
            border:
              "1px solid rgba(239, 68, 68, 0.15)",
            background:
              "rgba(239, 68, 68, 0.06)",
            color: "#f28b8b",
            fontSize: "11px",
          }}
        >
          {error}
        </div>
      )}

      {/* =====================================================
          TOOLBAR
      ===================================================== */}

      <div className="published-toolbar">
        <div className="published-search">
          <Search size={17} />

          <input
            type="text"
            placeholder="Search published posts..."
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
          />

          {search && (
            <button
              className="published-clear-search"
              onClick={() =>
                setSearch("")
              }
            >
              <X size={15} />
            </button>
          )}
        </div>

        <div className="published-filters">
          <select
            value={platformFilter}
            onChange={(e) =>
              setPlatformFilter(
                e.target.value,
              )
            }
          >
            <option value="All">
              All Platforms
            </option>

            <option value="Instagram">
              Instagram
            </option>

            <option value="Facebook">
              Facebook
            </option>

            <option value="LinkedIn">
              LinkedIn
            </option>

            <option value="X">
              X
            </option>
          </select>
        </div>
      </div>

      {/* =====================================================
          CONTENT CARD
      ===================================================== */}

      <div className="published-card">
        <div className="published-card-header">
          <div>
            <h2>
              Published Content
            </h2>

            <p>
              {filteredPosts.length} posts found
            </p>
          </div>
        </div>

        {filteredPosts.length > 0 ? (
          <div className="published-list">
            {filteredPosts.map(
              (post) => (
                <div
                  className="published-post-row"
                  key={post.id}
                >
                  {/* =========================================
                      PLATFORM
                  ========================================= */}

                  <div className="published-platform">
                    <div className="published-platform-icon">
                      <CheckCircle2 size={18} />
                    </div>

                    <span>
                      {formatPlatform(
                        post.platform,
                      )}
                    </span>
                  </div>

                  {/* =========================================
                      CONTENT
                  ========================================= */}

                  <div className="published-post-content">
                    <h3>
                      {post.title}
                    </h3>

                    <p>
                      {post.content ||
                        "No caption available."}
                    </p>
                  </div>

                  {/* =========================================
                      DATE
                  ========================================= */}

                  <div className="published-date">
                    <span>
                      {formatDate(
                        post.createdAt,
                      )}
                    </span>

                    <small>
                      <Clock3 size={13} />

                      {formatTime(
                        post.createdAt,
                      )}
                    </small>
                  </div>

                  {/* =========================================
                      REACH
                  ========================================= */}

                  <div className="published-reach">
                    <span>
                      {post.reach}
                    </span>

                    <small>
                      Reach
                    </small>
                  </div>

                  {/* =========================================
                      ENGAGEMENT
                  ========================================= */}

                  <div className="published-engagement">
                    <span>
                      {post.engagement}
                    </span>

                    <small>
                      Engagement
                    </small>
                  </div>

                  {/* =========================================
                      STATUS
                  ========================================= */}

                  <div className="published-status">
                    <span>
                      Published
                    </span>
                  </div>

                  {/* =========================================
                      ACTIONS
                  ========================================= */}

                  <div className="published-actions">
                    <button
                      className="published-menu-btn"
                      onClick={() =>
                        setOpenMenu(
                          openMenu ===
                            post.id
                            ? null
                            : post.id,
                        )
                      }
                    >
                      <MoreHorizontal
                        size={19}
                      />
                    </button>

                    {openMenu ===
                      post.id && (
                      <div className="published-dropdown">
                        <button
                          onClick={() =>
                            handleView(
                              post,
                            )
                          }
                        >
                          <Eye size={15} />
                          View
                        </button>

                        <button
                          className="delete-action"
                          onClick={() =>
                            handleDelete(
                              post,
                            )
                          }
                        >
                          <Trash2
                            size={15}
                          />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ),
            )}
          </div>
        ) : (
          <div className="published-empty">
            <div className="published-empty-icon">
              <CheckCircle2 size={30} />
            </div>

            <h3>
              {search ||
              platformFilter !== "All"
                ? "No published posts found"
                : "No published posts yet"}
            </h3>

            <p>
              {search ||
              platformFilter !== "All"
                ? "Try changing your search or platform filter."
                : "Posts will appear here after they are published."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PublishedPosts;
