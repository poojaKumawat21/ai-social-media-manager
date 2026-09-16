import React, { useState } from "react";
import "./CreatePost.css";

function CreatePost() {
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [platform, setPlatform] = useState("Instagram");
  const [isGenerating, setIsGenerating] = useState(false);
  const [aiPlan, setAiPlan] = useState(null);

  // Temporary frontend-only AI generation
  // Backend integration will be connected in the next step.
  const handleGenerateAI = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic.");
      return;
    }

    setIsGenerating(true);

    try {
      const params = new URLSearchParams({
        topic: topic.trim(),
        description: description.trim(),
      });

      const response = await fetch(
        `http://127.0.0.1:8000/plan-post?${params.toString()}`,
        {
          method: "POST",
        },
      );

      if (!response.ok) {
        throw new Error("Failed to generate post plan.");
      }

      const result = await response.json();

      console.log("AI PLAN:", result);
      setAiPlan(result.data);

      alert("AI planning completed successfully!");
    } catch (error) {
      console.error("AI generation error:", error);
      alert(
        "Unable to connect with AI backend. Make sure the backend is running.",
      );
    } finally {
      setIsGenerating(false);
    }
  };
  return (
    <div className="create-post-page">
      {/* ================= PAGE HEADER ================= */}
      <div className="create-post-header">
        <div>
          <span className="create-post-label">AI CONTENT STUDIO</span>

          <h1>Create Post</h1>

          <p>
            Tell AI what you want to post. AI will decide the best content
            strategy.
          </p>
        </div>

        <div className="create-post-status">
          <span></span>
          AI Ready
        </div>
      </div>

      {/* ================= MAIN CONTENT ================= */}
      <div className="create-post-grid">
        {/* ================= LEFT: EDITOR ================= */}
        <div className="post-editor-card">
          <div className="card-title">
            <div>
              <h2>Post Idea</h2>

              <p>Give AI your topic and optional instructions.</p>
            </div>
          </div>

          {/* TOPIC */}
          <div className="form-group">
            <label>
              Topic <span className="required">*</span>
            </label>

            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What do you want to post about?"
            />
          </div>

          {/* DESCRIPTION / INSTRUCTIONS */}
          <div className="form-group">
            <label>
              Description / Instructions
              <span className="optional">Optional</span>
            </label>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tell AI anything specific you want it to consider..."
              rows="7"
            />

            <div className="content-meta">
              <span>{description.length} characters</span>

              <span>AI decides the content strategy</span>
            </div>
          </div>

          {/* PLATFORM */}
          <div className="form-group">
            <label>Platform</label>

            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              <option value="Instagram">Instagram</option>
              <option value="LinkedIn">LinkedIn</option>
              <option value="WhatsApp">WhatsApp</option>
            </select>

            <small className="field-help">
              Available platforms will come from Connected Accounts.
            </small>
          </div>
          {/* AI STRATEGY */}

          <div className="ai-strategy-panel">
            <div className="ai-strategy-top">
              <div className="ai-strategy-brand">
                <div className="ai-strategy-icon">✦</div>

                <div>
                  <span>AI INTELLIGENCE</span>
                  <h3>Content Strategy</h3>
                </div>
              </div>

              <div className="ai-live-status">
                <i></i>
                {aiPlan ? "Strategy Ready" : "Waiting for AI"}
              </div>
            </div>

            <div className="ai-strategy-line"></div>

            <div className="ai-strategy-content">
              <div className="ai-strategy-main">
                <span className="ai-strategy-label">AI RECOMMENDATION</span>

                <h4>
                  {aiPlan?.post_type ||
                    "AI will determine the best content approach"}
                </h4>

                <p>
                  {aiPlan?.reasoning ||
                    "AI will analyze your topic, understand the audience and automatically build the most effective content strategy."}
                </p>
              </div>

              <div className="ai-strategy-data">
                <div>
                  <span>FORMAT</span>
                  <strong>
                    {aiPlan?.format === "carousel"
                      ? "Carousel"
                      : aiPlan?.format === "single_post"
                        ? "Single Post"
                        : "Auto"}
                  </strong>
                </div>

                <div>
                  <span>TONE</span>
                  <strong>{aiPlan?.tone || "Auto"}</strong>
                </div>

                <div>
                  <span>AUDIENCE</span>
                  <strong>{aiPlan?.audience || "AI Selected"}</strong>
                </div>

                <div>
                  <span>STYLE</span>
                  <strong>{aiPlan?.selected_style || "AI Selected"}</strong>
                </div>
              </div>
            </div>

            {aiPlan && (
              <div className="ai-strategy-footer">
                <span>✦</span>
                AI has automatically optimized this strategy for your selected
                platform.
              </div>
            )}
          </div>
          {aiPlan?.hashtags?.length > 0 && (
            <div className="ai-hashtags">
              <div className="ai-hashtags-header">
                <span>AI HASHTAGS</span>
                <small>Optimized for your post</small>
              </div>

              <div className="ai-hashtag-list">
                {aiPlan.hashtags.map((tag, index) => (
                  <span key={index}>{tag}</span>
                ))}
              </div>
            </div>
          )}

          {/* AI GENERATE BUTTON */}
          <button
            className="generate-ai-button"
            onClick={handleGenerateAI}
            disabled={isGenerating}
          >
            {isGenerating ? "✦ Generating..." : "✦ Generate with AI"}
          </button>

          {/* POST ACTIONS */}
          <div className="post-actions">
            <button className="save-draft-button">Save Draft</button>

            <button className="schedule-post-button">Schedule Post</button>

            <button className="publish-post-button">Publish</button>
          </div>
        </div>

        {/* ================= RIGHT: PREVIEW ================= */}
        <div className="post-preview-card">
          <div className="preview-header">
            <div>
              <h2>Preview</h2>

              <p>AI-generated content will appear here.</p>
            </div>
          </div>

          {/* SOCIAL MEDIA PREVIEW */}
          <div className="social-preview">
            {/* PROFILE */}
            <div className="preview-profile">
              <div className="preview-avatar">AI</div>

              <div>
                <strong>Your Brand</strong>

                <span>{platform}</span>
              </div>
            </div>

            {/* POST CONTENT */}
            <div className="preview-content">
              {aiPlan ? (
                <>
                  <h3>{aiPlan.headline || topic}</h3>

                  {aiPlan.subheadline && <p>{aiPlan.subheadline}</p>}

                  {aiPlan.introduction && <p>{aiPlan.introduction}</p>}

                  {aiPlan.sections?.length > 0 && (
                    <div className="ai-sections">
                      {aiPlan.sections.map((section) => (
                        <div className="ai-section" key={section.number}>
                          <strong>{section.title}</strong>
                          <p>{section.description}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {aiPlan.key_takeaway && (
                    <p>
                      <strong>Key Takeaway:</strong> {aiPlan.key_takeaway}
                    </p>
                  )}

                  {aiPlan.cta && (
                    <p>
                      <strong>CTA:</strong> {aiPlan.cta}
                    </p>
                  )}
                </>
              ) : topic ? (
                topic
              ) : (
                "Your AI-generated post preview will appear here..."
              )}
            </div>

            {/* AI IMAGE */}
            <div className="ai-image-section">
              <div className="ai-image-header">
                <div>
                  <span>AI VISUAL</span>
                  <h3>Generated Creative</h3>
                </div>

                <span className="ai-image-status">
                  {aiPlan ? "Ready" : "Waiting"}
                </span>
              </div>

              <div className="ai-image-preview">
                <div className="ai-image-glow"></div>

                <div className="ai-image-content">
                  <div className="ai-image-icon">✦</div>

                  <strong>
                    {aiPlan
                      ? "AI visual will be generated"
                      : "Your visual starts here"}
                  </strong>

                  <p>AI will create a visual based on your content strategy.</p>
                </div>
              </div>

              <button
                className="generate-image-button"
                onClick={() =>
                  alert("Image generation will be connected to AI backend.")
                }
              >
                ✦ Generate Visual
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CreatePost;
