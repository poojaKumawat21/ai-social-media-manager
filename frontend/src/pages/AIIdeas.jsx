import React, { useState } from "react";
import "./AIIdeas.css";
import api from "../services/api";

function AIIdeas() {
  const [topic, setTopic] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [ideas, setIdeas] = useState([]);

  const handleGenerateIdeas = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic or niche.");
      return;
    }

    setIsGenerating(true);
    setIdeas([]);

    try {
      const result = await api.post("/ai/ideas", {
        topic: topic.trim(),
      });

      setIdeas(result.ideas || []);
    } catch (error) {
      console.error("AI ideas generation error:", error);

      if (error.status === 401) {
        alert("Your session has expired. Please login again.");
      } else {
        alert("Failed to generate AI ideas. Please try again.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="ai-ideas-page">
      <div className="page-header">
        <div>
          <h1>AI Content Ideas</h1>
          <p>Let AI discover fresh content ideas for your social media.</p>
        </div>

        <button
          className="primary-btn"
          onClick={handleGenerateIdeas}
          disabled={isGenerating}
        >
          {isGenerating ? "✦ Generating..." : "✦ Generate Ideas"}
        </button>
      </div>

      <div className="ai-ideas-card">
        <h3>AI Idea Generator</h3>

        <p>Tell AI what kind of content you want ideas for.</p>

        <div className="idea-input-group">
          <label>Topic or niche</label>

          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. AI, technology, fitness, business..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleGenerateIdeas();
              }
            }}
          />

          <small>
            AI will analyze your topic and suggest relevant content ideas.
          </small>
        </div>

        <div className="ai-ideas-results">
          <div className="results-header">
            <div>
              <span>AI GENERATED</span>
              <h3>Content Ideas</h3>
            </div>

            <small>
              {ideas.length > 0
                ? `${ideas.length} AI recommendations`
                : "AI recommendations"}
            </small>
          </div>

          {ideas.length > 0 && (
            <div className="idea-results-grid">
              {ideas.map((idea, index) => (
                <div className="idea-result-card" key={index}>
                  <span className="idea-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <h4>{idea.title}</h4>

                  <p>{idea.description}</p>

                  <div className="idea-tags">
                    {(idea.tags || []).map((tag, tagIndex) => (
                      <span key={tagIndex}>{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isGenerating && ideas.length === 0 && (
            <div className="empty-ideas-state">
              <p>Enter a topic and let AI generate fresh content ideas.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIIdeas;