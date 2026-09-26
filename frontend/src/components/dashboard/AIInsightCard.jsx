import React from "react";

const insights = [
  {
    type: "TRENDING",
    title: "AI Agents are trending",
    description:
      "AI Agent content is getting strong attention across professional audiences.",
    action: "Create Post",
    icon: "✦",
    accent: "purple",
  },
  {
    type: "BEST TIME",
    title: "6:00 PM looks promising",
    description:
      "Your audience is most active around the evening posting window.",
    action: "Schedule Post",
    icon: "◷",
    accent: "cyan",
  },
  {
    type: "NEWS",
    title: "New AI model released",
    description:
      "This news matches your niche and could become a timely social post.",
    action: "Generate Post",
    icon: "↗",
    accent: "blue",
  },
  {
    type: "PERFORMANCE",
    title: "Educational posts perform better",
    description:
      "Educational content is currently one of your strongest content formats.",
    action: "View Analytics",
    icon: "↗",
    accent: "green",
  },
];

function AIInsightCard() {
  return (
    <section className="ai-insights-section">

      <div className="ai-section-heading">
        <div>
          <div className="ai-title-row">
            <span className="ai-sparkle">✦</span>
            <h2>AI Recommendations</h2>
          </div>

          <p>
            Your AI manager found these opportunities for your brand.
          </p>
        </div>

        <span className="ai-status">
          <span className="status-dot"></span>
          AI Active
        </span>
      </div>

      <div className="ai-insights-grid">
        {insights.map((insight) => (
          <div
            className={`ai-insight-card ${insight.accent}`}
            key={insight.type}
          >

            <div className="insight-top">
              <span className="insight-type">
                {insight.type}
              </span>

              <div className="insight-icon">
                {insight.icon}
              </div>
            </div>

            <h3>{insight.title}</h3>

            <p>{insight.description}</p>

            <button className="insight-action">
              {insight.action}
              <span>→</span>
            </button>

          </div>
        ))}
      </div>

    </section>
  );
}

export default AIInsightCard;