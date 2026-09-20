import React, { useState } from "react";
import { Search, ExternalLink, Sparkles } from "lucide-react";
import "./NewsTrends.css";

const CATEGORIES = [
  "All",
  "AI",
  "Technology",
  "Business",
  "Trending",
];

const INITIAL_NEWS = [
  {
    id: "news-001",
    title: "The Future of Generative AI",
    description:
      "Explore how generative AI is changing the way people create, work and communicate.",
    source: "Tech Daily",
    publishedAt: "2 hours ago",
    category: "AI",
    url: "#",
  },
  {
    id: "news-002",
    title: "AI Tools Are Transforming Content Creation",
    description:
      "New AI tools are helping creators plan, write and produce content faster.",
    source: "Digital World",
    publishedAt: "5 hours ago",
    category: "Technology",
    url: "#",
  },
  {
    id: "news-003",
    title: "Social Media Trends Creators Should Watch",
    description:
      "Discover emerging content formats and trends that are shaping social media.",
    source: "Creator News",
    publishedAt: "8 hours ago",
    category: "Trending",
    url: "#",
  },
  {
    id: "news-004",
    title: "AI Startups Driving the Next Wave of Innovation",
    description:
      "A look at how new AI startups are building products around real-world problems.",
    source: "Startup Today",
    publishedAt: "1 day ago",
    category: "Business",
    url: "#",
  },
  {
    id: "news-005",
    title: "What's Next for AI Assistants?",
    description:
      "AI assistants are becoming more capable of planning, reasoning and completing tasks.",
    source: "Future Tech",
    publishedAt: "1 day ago",
    category: "AI",
    url: "#",
  },
  {
    id: "news-006",
    title: "The Rise of Agentic AI",
    description:
      "Agentic AI systems are moving beyond simple responses toward autonomous workflows.",
    source: "AI Insider",
    publishedAt: "2 days ago",
    category: "Technology",
    url: "#",
  },
];

const INITIAL_TRENDS = [
  {
    id: "trend-001",
    topic: "Generative AI",
    category: "AI",
    activity: "High interest",
  },
  {
    id: "trend-002",
    topic: "AI Agents",
    category: "Technology",
    activity: "Growing fast",
  },
  {
    id: "trend-003",
    topic: "Creator Economy",
    category: "Business",
    activity: "Trending",
  },
];

function NewsTrends() {
  const [news] = useState(INITIAL_NEWS);
  const [trends] = useState(INITIAL_TRENDS);

  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredNews = news.filter((item) => {
    const matchesCategory =
      activeCategory === "All" ||
      item.category === activeCategory;

    const query = searchQuery.trim().toLowerCase();

    const matchesSearch =
      !query ||
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query);

    return matchesCategory && matchesSearch;
  });

  const handleConvertToPost = (item) => {
    console.log("Convert news to post:", item);

    alert(
      `"${item.title}" will be connected to Create Post later.`
    );
  };

  const handleOpenSource = (url) => {
    if (!url || url === "#") {
      alert("News source link will be connected later.");
      return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="news-trends-page">

      {/* =========================
          PAGE HEADER
      ========================= */}

      <div className="page-header">

        <div>
          <span className="news-label">
            INTELLIGENT DISCOVERY
          </span>

          <h1>News & Trends</h1>

          <p>
            Discover relevant news and turn fresh trends into social
            media content.
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


      {/* =========================
          CATEGORY FILTERS
      ========================= */}

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


      {/* =========================
          NEWS SECTION
      ========================= */}

      <div className="news-content">

        <div className="news-section-header">
          <h3>Latest News</h3>

          <span>
            {filteredNews.length} articles
          </span>
        </div>


        {filteredNews.length > 0 ? (

          <div className="news-grid">

            {filteredNews.map((item) => (

              <article
                className="news-card"
                key={item.id}
              >

                {/* IMAGE AREA */}

                <div className="news-card-image">

                  <span className="news-category">
                    {item.category}
                  </span>

                </div>


                {/* CARD CONTENT */}

                <div className="news-card-body">

                  <div className="news-card-source">

                    <span>
                      {item.source}
                    </span>

                    <span>
                      {item.publishedAt}
                    </span>

                  </div>


                  <h3>
                    {item.title}
                  </h3>


                  <p className="news-card-description">
                    {item.description}
                  </p>


                  {/* CARD ACTIONS */}

                  <div className="news-card-footer">

                    <button
                      className="news-source-link"
                      onClick={() =>
                        handleOpenSource(item.url)
                      }
                    >
                      <ExternalLink size={11} />
                      Source
                    </button>


                    <button
                      className="news-to-post-button"
                      onClick={() =>
                        handleConvertToPost(item)
                      }
                    >
                      <Sparkles size={10} />
                      Convert to Post
                    </button>

                  </div>

                </div>

              </article>

            ))}

          </div>

        ) : (

          <div className="news-empty">

            <div className="news-empty-icon">
              ✦
            </div>

            <h3>
              No news found
            </h3>

            <p>
              Try another search or category.
            </p>

          </div>

        )}

      </div>


      {/* =========================
          TRENDING SECTION
      ========================= */}

      <div className="trending-section">

        <div className="news-section-header">

          <h3>
            Trending Topics
          </h3>

          <span>
            AI discovered
          </span>

        </div>


        <div className="trending-list">

          {trends.map((trend) => (

            <div
              className="trending-item"
              key={trend.id}
            >

              <span>
                {trend.category}
              </span>

              <strong>
                {trend.topic}
              </strong>

              <small>
                {trend.activity}
              </small>

            </div>

          ))}

        </div>

      </div>

    </div>
  );
}

export default NewsTrends;