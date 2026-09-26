import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Search,
  ArrowLeft,
  LayoutDashboard,
  PenSquare,
  FileText,
  CalendarDays,
  Sparkles,
  Newspaper,
  Clock3,
  CheckCircle2,
  Link2,
  BarChart3,
  Settings,
  ArrowUpRight,
} from "lucide-react";

const searchItems = [
  {
    title: "Dashboard",
    description: "View your social media overview and activity.",
    path: "/",
    keywords: "dashboard home overview",
    icon: LayoutDashboard,
  },
  {
    title: "Create Post",
    description: "Create and generate social media posts.",
    path: "/create-post",
    keywords: "create post write content",
    icon: PenSquare,
  },
  {
    title: "Saved Drafts",
    description: "View and manage your saved post drafts.",
    path: "/saved-drafts",
    keywords: "draft drafts saved posts",
    icon: FileText,
  },
  {
    title: "Content Calendar",
    description: "Plan and organize your content schedule.",
    path: "/content-calendar",
    keywords: "calendar content schedule planning",
    icon: CalendarDays,
  },
  {
    title: "AI Ideas",
    description: "Generate fresh content ideas with AI.",
    path: "/ai-ideas",
    keywords: "ai ideas content generation",
    icon: Sparkles,
  },
  {
    title: "News & Trends",
    description: "Discover the latest news and trending topics.",
    path: "/news-trends",
    keywords: "news trends technology business ai",
    icon: Newspaper,
  },
  {
    title: "Scheduled Posts",
    description: "View posts that are scheduled for publishing.",
    path: "/scheduled-posts",
    keywords: "scheduled schedule posts",
    icon: Clock3,
  },
  {
    title: "Published Posts",
    description: "View your published social media posts.",
    path: "/published-posts",
    keywords: "published posts live",
    icon: CheckCircle2,
  },
  {
    title: "Connected Accounts",
    description: "Manage your connected social media accounts.",
    path: "/connected-accounts",
    keywords: "social accounts instagram linkedin facebook x",
    icon: Link2,
  },
  {
    title: "Analytics",
    description: "Track your social media performance.",
    path: "/analytics",
    keywords: "analytics reach engagement performance",
    icon: BarChart3,
  },
  {
    title: "Settings",
    description: "Manage your PostPilot settings.",
    path: "/settings",
    keywords: "settings profile preferences",
    icon: Settings,
  },
];

function SearchPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const query = searchParams.get("q") || "";

  const results = useMemo(() => {
    const searchText = query.trim().toLowerCase();

    if (!searchText) {
      return searchItems;
    }

    return searchItems.filter((item) => {
      const searchableText = `
        ${item.title}
        ${item.description}
        ${item.keywords}
      `.toLowerCase();

      return searchableText.includes(searchText);
    });
  }, [query]);

  return (
    <div className="search-page">
      <div className="search-page-header">
        <button
          className="search-back-button"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft size={18} />
          <span>Back</span>
        </button>

        <div className="search-page-title">
          <div className="search-title-icon">
            <Search size={22} />
          </div>

          <div>
            <h1>Search</h1>
            <p>
              Find pages and features inside PostPilot
            </p>
          </div>
        </div>
      </div>

      <div className="search-page-searchbox">
        <Search size={20} />

        <input
          value={query}
          readOnly
          placeholder="Search anything..."
        />
      </div>

      <div className="search-results-header">
        <div>
          <h2>
            {query ? `Results for "${query}"` : "All Features"}
          </h2>

          <p>
            {results.length} result{results.length !== 1 ? "s" : ""} found
          </p>
        </div>
      </div>

      {results.length > 0 ? (
        <div className="search-results-grid">
          {results.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.path}
                className="search-result-card"
                onClick={() => navigate(item.path)}
              >
                <div className="search-result-icon">
                  <Icon size={21} />
                </div>

                <div className="search-result-content">
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>

                <ArrowUpRight
                  className="search-result-arrow"
                  size={18}
                />
              </button>
            );
          })}
        </div>
      ) : (
        <div className="search-empty-state">
          <div className="search-empty-icon">
            <Search size={28} />
          </div>

          <h2>No results found</h2>

          <p>
            We couldn't find anything matching{" "}
            <strong>"{query}"</strong>.
          </p>

          <button
            onClick={() => navigate("/")}
            className="search-home-button"
          >
            Go to Dashboard
          </button>
        </div>
      )}
    </div>
  );
}

export default SearchPage;