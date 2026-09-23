import React, { useEffect, useState } from "react";
import { Search, ExternalLink, Sparkles, RefreshCw } from "lucide-react";

import "./NewsTrends.css";
import api from "../services/api";

const CATEGORIES = ["All", "AI", "Technology", "Business", "Trending"];

function getCategory(title = "") {
  const text = title.toLowerCase();

  if (
    text.includes("artificial intelligence") ||
    text.includes("openai") ||
    text.includes("chatgpt") ||
    text.includes("gemini") ||
    text.includes("machine learning") ||
    text.includes("generative ai") ||
    text.includes(" ai ")
  ) {
    return "AI";
  }

  if (
    text.includes("business") ||
    text.includes("startup") ||
    text.includes("market") ||
    text.includes("investment") ||
    text.includes("economy") ||
    text.includes("company")
  ) {
    return "Business";
  }

  return "Technology";
}

function formatDate(dateString) {
  if (!dateString) {
    return "Recently published";
  }

  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return dateString;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function NewsTrends() {
  const [news, setNews] = useState([]);
  const [trends, setTrends] = useState([]);

  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchNews = async (showLoader = true) => {
    try {
      if (showLoader) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      setError("");

      const categoryMap = {
        All: "all",
        AI: "ai",
        Technology: "technology",
        Business: "business",
        Trending: "trending",
      };

      const category = categoryMap[activeCategory] || "all";

      const result = await api.get(
        `/research-news?topic=Artificial%20Intelligence&category=${category}`,
      );

      console.log("Active category:", activeCategory);
      console.log("Category sent:", category);
      console.log(
        "News API URL:",
        `/research-news?topic=Artificial%20Intelligence&category=${category}`,
      );
      console.log("GNews response:", result);
      const realNews = (result.data || [])
        .filter((item) => item && item.title)
        .map((item, index) => ({
          id: `news-${index}-${item.link || item.title}`,

          title: item.title.trim() || "Untitled news article",

          description:
            item.description?.trim() ||
            "Read the original article for complete details.",

          source: item.source?.trim() || "Unknown Source",

          publishedAt: formatDate(item.published),

          category: getCategory(item.title || ""),

          url: item.link || "#",

          image: item.image?.trim() || "",
        }));

      setNews(realNews);

      const generatedTrends = realNews.slice(0, 5).map((item, index) => ({
        id: `trend-${index}-${item.id}`,

        topic: item.title,

        category: item.category,

        activity: index === 0 ? "Latest" : "Recent coverage",
      }));

      setTrends(generatedTrends);
    } catch (error) {
      console.error("News fetch error:", error);

      setNews([]);
      setTrends([]);

      setError(
        "Unable to load latest news. Please check your backend connection.",
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews(true);

    const refreshInterval = setInterval(
      () => {
        fetchNews(false);
      },
      5 * 60 * 1000,
    );

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  const filteredNews = news.filter((item) => {
    const matchesCategory =
      activeCategory === "All" || item.category === activeCategory;

    const query = searchQuery.trim().toLowerCase();

    const matchesSearch =
      !query ||
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query) ||
      item.source.toLowerCase().includes(query);

    return matchesCategory && matchesSearch;
  });

  const handleConvertToPost = (item) => {
    console.log("Convert news to post:", item);

    alert(`"${item.title}" selected for Create Post.`);
  };

  const handleOpenSource = (url) => {
    if (!url || url === "#") {
      alert("News source link is not available.");

      return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="news-trends-page">
      {/* HEADER */}

      <div className="page-header">
        <div>
          <span className="news-label">INTELLIGENT DISCOVERY</span>

          <h1>News & Trends</h1>

          <p>
            Discover relevant news and turn fresh trends into social media
            content.
          </p>
        </div>

        <div className="news-search-box">
          <Search size={15} />

          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search news..."
          />
        </div>
      </div>

      {/* FILTERS */}

      <div className="news-filters">
        {CATEGORIES.map((category) => (
          <button
            key={category}
            className={`news-filter ${
              activeCategory === category ? "active" : ""
            }`}
            onClick={() => setActiveCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      {/* NEWS */}

      <div className="news-content">
        <div className="news-section-header">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <h3>Latest News</h3>

            <span>
              {isLoading ? "Loading..." : `${filteredNews.length} articles`}
            </span>
          </div>

          <button
            onClick={() => fetchNews(false)}
            disabled={isRefreshing}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              background: "transparent",
              border: "1px solid rgba(139, 92, 246, 0.35)",
              color: "#a78bfa",
              padding: "7px 11px",
              borderRadius: "8px",
              cursor: isRefreshing ? "default" : "pointer",
              fontSize: "12px",
            }}
          >
            <RefreshCw
              size={13}
              style={{
                animation: isRefreshing ? "spin 1s linear infinite" : "none",
              }}
            />

            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {/* LOADING */}

        {isLoading && (
          <div className="news-empty">
            <div className="news-empty-icon">✦</div>

            <h3>Loading latest news...</h3>

            <p>Fetching current news from live sources.</p>
          </div>
        )}

        {/* ERROR */}

        {!isLoading && error && (
          <div className="news-empty">
            <div className="news-empty-icon">!</div>

            <h3>Unable to load news</h3>

            <p>{error}</p>
          </div>
        )}

        {/* NEWS CARDS */}

        {!isLoading && !error && filteredNews.length > 0 && (
          <div className="news-grid">
            {filteredNews.map((item) => (
              <article className="news-card" key={item.id}>
                {/* IMAGE */}

                <div className="news-card-image">
                  {item.image ? (
                    <img
                      src={item.image}
                      alt={item.title}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";

                        e.currentTarget.parentElement.classList.add(
                          "image-load-failed",
                        );
                      }}
                    />
                  ) : (
                    <div className="news-image-fallback">
                      <Sparkles size={32} />
                    </div>
                  )}

                  <span className="news-category">{item.category}</span>
                </div>

                {/* CONTENT */}

                <div className="news-card-body">
                  <div className="news-card-source">
                    <span>{item.source}</span>

                    <span>{item.publishedAt}</span>
                  </div>

                  <h3>{item.title}</h3>

                  <p className="news-card-description">{item.description}</p>

                  {/* FOOTER */}

                  <div className="news-card-footer">
                    <button
                      className="news-source-link"
                      onClick={() => handleOpenSource(item.url)}
                    >
                      <ExternalLink size={11} />
                      Source
                    </button>

                    <button
                      className="news-to-post-button"
                      onClick={() => handleConvertToPost(item)}
                    >
                      <Sparkles size={10} />
                      Convert to Post
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}

        {/* NO RESULTS */}

        {!isLoading && !error && filteredNews.length === 0 && (
          <div className="news-empty">
            <div className="news-empty-icon">✦</div>

            <h3>No news found</h3>

            <p>Try another search or category.</p>
          </div>
        )}
      </div>

      {/* TRENDING */}

      <div className="trending-section">
        <div className="news-section-header">
          <h3>Trending Topics</h3>

          <span>Based on latest coverage</span>
        </div>

        <div className="trending-list">
          {trends.map((trend) => (
            <div className="trending-item" key={trend.id}>
              <span>{trend.category}</span>

              <strong>{trend.topic}</strong>

              <small>{trend.activity}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default NewsTrends;
