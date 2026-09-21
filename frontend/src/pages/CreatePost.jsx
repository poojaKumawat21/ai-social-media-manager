import React, { useEffect, useState } from "react";

import "./CreatePost.css";

import api from "../services/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function CreatePost() {
  const [topic, setTopic] = useState("");

  const [description, setDescription] = useState("");

  const [platform, setPlatform] = useState("Instagram");

  const [isGenerating, setIsGenerating] = useState(false);

  const [aiPlan, setAiPlan] = useState(null);

  const [generatedImages, setGeneratedImages] = useState([]);

  const [postId, setPostId] = useState(null);

  const [isPublishing, setIsPublishing] = useState(false);

  const [isSavingDraft, setIsSavingDraft] = useState(false);

  const DRAFT_KEY = "postpilot_create_post_draft";

  const RESULT_KEY = "postpilot_create_post_result";

  const PENDING_KEY = "postpilot_create_post_pending";

  useEffect(() => {

  try {

    const savedDraft = localStorage.getItem(DRAFT_KEY);

    if (savedDraft) {

      const draft = JSON.parse(savedDraft);

      setTopic(draft.topic || "");
      setDescription(draft.description || "");
      setPlatform(draft.platform || "Instagram");

    }

    const savedResult = localStorage.getItem(RESULT_KEY);

    if (savedResult) {

      const result = JSON.parse(savedResult);

      setAiPlan(result.aiPlan || null);
      setGeneratedImages(result.generatedImages || []);

    }

    // ================= EDIT SAVED DRAFT =================

    const editDraft = localStorage.getItem(
      "postpilot_edit_draft"
    );

    if (editDraft) {

      const draft = JSON.parse(editDraft);

      setPostId(
        draft.id || null
      );

      setTopic(
        draft.topic || ""
      );

      setDescription(
        draft.caption || ""
      );

      setPlatform(
        draft.platform || "LinkedIn"
      );

      setGeneratedImages(
        (draft.media_urls || []).filter(Boolean)
      );

      setAiPlan({

        headline:
          draft.post_idea ||
          draft.topic ||
          "",

        caption:
          draft.caption ||
          "",

        hashtags:
          draft.hashtags ||
          [],

        tone:
          draft.tone ||
          "Professional",

        selected_style:
          draft.style ||
          "AI Selected",

        format:
          "single_post",

      });

      localStorage.removeItem(
        "postpilot_edit_draft"
      );

    }

  } catch (error) {

    console.error(
      "Failed to restore Create Post data:",
      error,
    );

  }

}, []);

  const handleSaveDraft = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic before saving the draft.");
      return;
    }

    setIsSavingDraft(true);

    try {
      let result;

      // If AI post already exists,
      // convert the existing generated post into a draft.
      if (postId) {
        result = await api.put(`/posts/${postId}`, {
          status: "draft",
        });

        alert("Draft saved successfully!");
      } else {
        // Otherwise create a new basic draft.
        result = await api.post("/posts/draft", {
          topic: topic.trim(),
          description: description.trim(),
        });

        alert("Draft saved successfully!");
      }

      console.log("DRAFT SAVED:", result);
    } catch (error) {
      console.error("Save draft error:", error);

      alert(
        error.message ||
          "Unable to save draft.",
      );
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handlePublish = async () => {
    if (!postId) {
      alert("Please generate a post first.");
      return;
    }

    if (platform !== "LinkedIn") {
      alert("LinkedIn publishing is currently available.");
      return;
    }

    setIsPublishing(true);

    try {
      const result = await api.post(
        `/posts/${postId}/publish/linkedin`,
      );

      console.log(
        "LINKEDIN PUBLISH RESULT:",
        result,
      );

      alert(
        "Post published to LinkedIn successfully!",
      );
    } catch (error) {
      console.error(
        "LinkedIn publish error:",
        error,
      );

      alert(
        error.message ||
          "Unable to publish post to LinkedIn.",
      );
    } finally {
      setIsPublishing(false);
    }
  };

  useEffect(() => {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        topic,
        description,
        platform,
      }),
    );
  }, [topic, description, platform]);

  useEffect(() => {
    if (!aiPlan && generatedImages.length === 0) {
      return;
    }

    localStorage.setItem(
      RESULT_KEY,
      JSON.stringify({
        aiPlan,
        generatedImages,
      }),
    );
  }, [aiPlan, generatedImages]);

  const handleGenerateAI = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic.");
      return;
    }

    setIsGenerating(true);

    setAiPlan(null);

    setGeneratedImages([]);

    localStorage.setItem(
      PENDING_KEY,
      JSON.stringify({
        topic: topic.trim(),
        startedAt: Date.now(),
      }),
    );

    try {
      const result = await api.post("/posts/generate", {
        topic: topic.trim(),
        description: description.trim(),
      });

      console.log(
        "GENERATED POST:",
        result,
      );

      setPostId(
        result.post?.id || null,
      );

      const aiResult =
        result.ai_result || {};

      const planner =
        aiResult.planner || {};

      const content =
        aiResult.content || {};

      const combinedPlan = {
        ...planner,
        ...content,
      };

      setAiPlan(combinedPlan);

      /*
       * Get image URLs.
       *
       * First preference:
       * saved post media_urls
       */

      let mediaUrls =
        result.post?.media_urls || [];

      /*
       * Fallback:
       * uploaded_images from AI pipeline
       */

      if (!mediaUrls.length) {
        mediaUrls = (
          aiResult.uploaded_images || []
        )
          .map(
            (image) =>
              image?.storage?.public_url ||
              image?.storage?.url ||
              image?.url,
          )
          .filter(Boolean);
      }

      /*
       * Final fallback:
       * renderer generated image URLs
       */

      if (!mediaUrls.length) {
        mediaUrls = (
          aiResult.render?.images || []
        )
          .map(
            (image) => image?.url,
          )
          .filter(Boolean);
      }

      const fullImageUrls =
        mediaUrls
          .filter(Boolean)
          .map((url) => {
            if (
              /^https?:\/\//i.test(url)
            ) {
              return url;
            }

            return `${API_BASE_URL}${
              url.startsWith("/")
                ? ""
                : "/"
            }${url}`;
          });

      console.log(
        "IMAGE URLS:",
        fullImageUrls,
      );

      setGeneratedImages(
        fullImageUrls,
      );

      localStorage.setItem(
        RESULT_KEY,
        JSON.stringify({
          aiPlan: combinedPlan,
          generatedImages:
            fullImageUrls,
        }),
      );

      localStorage.removeItem(
        PENDING_KEY,
      );

      alert(
        "AI post generated successfully!",
      );
    } catch (error) {
      console.error(
        "AI generation error:",
        error,
      );

      localStorage.removeItem(
        PENDING_KEY,
      );

      if (
        error.message.includes("401")
      ) {
        alert(
          "Your session has expired. Please login again.",
        );

        localStorage.removeItem(
          "access_token",
        );

        localStorage.removeItem(
          "refresh_token",
        );

        localStorage.removeItem(
          "user_id",
        );

        localStorage.removeItem(
          "user_email",
        );

        return;
      }

      alert(
        error.message ||
          "Unable to generate post. Make sure the backend is running.",
      );
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    const pendingData =
      localStorage.getItem(
        PENDING_KEY,
      );

    if (!pendingData) {
      return;
    }

    let pending;

    try {
      pending = JSON.parse(
        pendingData,
      );
    } catch {
      localStorage.removeItem(
        PENDING_KEY,
      );

      return;
    }

    let intervalId = null;

    let cancelled = false;

    const checkGeneratedPost =
      async () => {
        try {
          const result =
            await api.get("/posts");

          const posts =
            result.posts || [];

          const generatedPost =
            posts.find((post) => {
              const createdAt =
                post.created_at
                  ? new Date(
                      post.created_at,
                    ).getTime()
                  : 0;

              return (
                post.topic ===
                  pending.topic &&
                post.status ===
                  "generated" &&
                createdAt >=
                  pending.startedAt
              );
            });

          if (
            !generatedPost ||
            cancelled
          ) {
            return false;
          }

          setPostId(
            generatedPost.id ||
              null,
          );

          const restoredPlan = {
            headline:
              generatedPost.post_idea ||
              generatedPost.topic,

            caption:
              generatedPost.caption ||
              "",

            hashtags:
              generatedPost.hashtags ||
              [],

            tone:
              generatedPost.tone ||
              "Professional",

            selected_style:
              generatedPost.style ||
              "AI Selected",

            format:
              "single_post",
          };

          const mediaUrls = (
            generatedPost.media_urls ||
            []
          )
            .filter(Boolean)
            .map((url) => {
              if (
                /^https?:\/\//i.test(
                  url,
                )
              ) {
                return url;
              }

              return `${API_BASE_URL}${
                url.startsWith("/")
                  ? ""
                  : "/"
              }${url}`;
            });

          setTopic(
            generatedPost.topic ||
              pending.topic,
          );

          setAiPlan(
            restoredPlan,
          );

          setGeneratedImages(
            mediaUrls,
          );

          localStorage.setItem(
            RESULT_KEY,
            JSON.stringify({
              aiPlan:
                restoredPlan,
              generatedImages:
                mediaUrls,
            }),
          );

          localStorage.removeItem(
            PENDING_KEY,
          );

          return true;
        } catch (error) {
          console.error(
            "Checking generated post:",
            error,
          );

          return false;
        }
      };

    const startChecking =
      async () => {
        const found =
          await checkGeneratedPost();

        if (
          !found &&
          !cancelled
        ) {
          intervalId =
            setInterval(
              async () => {
                const done =
                  await checkGeneratedPost();

                if (
                  done &&
                  intervalId
                ) {
                  clearInterval(
                    intervalId,
                  );

                  intervalId = null;
                }
              },
              3000,
            );
        }
      };

    startChecking();

    return () => {
      cancelled = true;

      if (intervalId) {
        clearInterval(
          intervalId,
        );
      }
    };
  }, []);

  return (
    <div className="create-post-page">

      {/* ================= PAGE HEADER ================= */}

      <div className="create-post-header">

        <div>

          <span className="create-post-label">
            AI CONTENT STUDIO
          </span>

          <h1>
            Create Post
          </h1>

          <p>
            Tell AI what you want to post.
            AI will decide the best content
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

              <h2>
                Post Idea
              </h2>

              <p>
                Give AI your topic and
                optional instructions.
              </p>

            </div>

          </div>

          {/* TOPIC */}

          <div className="form-group">

            <label>
              Topic{" "}
              <span className="required">
                *
              </span>
            </label>

            <input
              type="text"
              value={topic}
              onChange={(e) =>
                setTopic(e.target.value)
              }
              placeholder="What do you want to post about?"
            />

          </div>

          {/* DESCRIPTION / INSTRUCTIONS */}

          <div className="form-group">

            <label>

              Description / Instructions

              <span className="optional">
                Optional
              </span>

            </label>

            <textarea
              value={description}
              onChange={(e) =>
                setDescription(
                  e.target.value,
                )
              }
              placeholder="Tell AI anything specific you want it to consider..."
              rows="7"
            />

            <div className="content-meta">

              <span>
                {description.length} characters
              </span>

              <span>
                AI decides the content strategy
              </span>

            </div>

          </div>

          {/* PLATFORM */}

          <div className="form-group">

            <label>
              Platform
            </label>

            <select
              value={platform}
              onChange={(e) =>
                setPlatform(
                  e.target.value,
                )
              }
            >

              <option value="Instagram">
                Instagram
              </option>

              <option value="LinkedIn">
                LinkedIn
              </option>

              <option value="WhatsApp">
                WhatsApp
              </option>

            </select>

            <small className="field-help">
              Available platforms will come
              from Connected Accounts.
            </small>

          </div>

          {/* AI STRATEGY */}

          <div className="ai-strategy-panel">

            <div className="ai-strategy-top">

              <div className="ai-strategy-brand">

                <div className="ai-strategy-icon">
                  ✦
                </div>

                <div>

                  <span>
                    AI INTELLIGENCE
                  </span>

                  <h3>
                    Content Strategy
                  </h3>

                </div>

              </div>

              <div className="ai-live-status">

                <i></i>

                {aiPlan
                  ? "Strategy Ready"
                  : "Waiting for AI"}

              </div>

            </div>

            <div className="ai-strategy-line"></div>

            <div className="ai-strategy-content">

              <div className="ai-strategy-main">

                <span className="ai-strategy-label">
                  AI RECOMMENDATION
                </span>

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

                  <span>
                    FORMAT
                  </span>

                  <strong>
                    {aiPlan?.format ===
                    "carousel"
                      ? "Carousel"
                      : aiPlan?.format ===
                        "single_post"
                        ? "Single Post"
                        : "Auto"}
                  </strong>

                </div>

                <div>

                  <span>
                    TONE
                  </span>

                  <strong>
                    {aiPlan?.tone ||
                      "Auto"}
                  </strong>

                </div>

                <div>

                  <span>
                    AUDIENCE
                  </span>

                  <strong>
                    {aiPlan?.audience ||
                      "AI Selected"}
                  </strong>

                </div>

                <div>

                  <span>
                    STYLE
                  </span>

                  <strong>
                    {aiPlan?.selected_style ||
                      "AI Selected"}
                  </strong>

                </div>

              </div>

            </div>

            {aiPlan && (
              <div className="ai-strategy-footer">

                <span>
                  ✦
                </span>

                AI has automatically optimized
                this strategy for your selected
                platform.

              </div>
            )}

          </div>

          {/* AI HASHTAGS */}

          {aiPlan?.hashtags?.length > 0 && (

            <div className="ai-hashtags">

              <div className="ai-hashtags-header">

                <span>
                  AI HASHTAGS
                </span>

                <small>
                  Optimized for your post
                </small>

              </div>

              <div className="ai-hashtag-list">

                {aiPlan.hashtags.map(
                  (tag, index) => (
                    <span key={index}>
                      {tag}
                    </span>
                  ),
                )}

              </div>

            </div>

          )}

          {/* AI GENERATE BUTTON */}

          <button
            className="generate-ai-button"
            onClick={handleGenerateAI}
            disabled={isGenerating}
          >
            {isGenerating
              ? "✦ Generating..."
              : "✦ Generate with AI"}
          </button>

          {/* POST ACTIONS */}

          <div className="post-actions">

            <button
              className="save-draft-button"
              onClick={handleSaveDraft}
              disabled={isSavingDraft}
            >
              {isSavingDraft
                ? "Saving..."
                : "Save Draft"}
            </button>

            <button className="schedule-post-button">
              Schedule Post
            </button>

            <button
              className="publish-post-button"
              onClick={handlePublish}
              disabled={
                isPublishing ||
                !postId
              }
            >
              {isPublishing
                ? "Publishing..."
                : "Publish"}
            </button>

          </div>

        </div>

        {/* ================= RIGHT: PREVIEW ================= */}

        <div className="post-preview-card">

          <div className="preview-header">

            <div>

              <h2>
                Preview
              </h2>

              <p>
                AI-generated content will
                appear here.
              </p>

            </div>

          </div>

          {/* SOCIAL MEDIA PREVIEW */}

          <div className="social-preview">

            {/* PROFILE */}

            <div className="preview-profile">

              <div className="preview-avatar">
                AI
              </div>

              <div>

                <strong>
                  Your Brand
                </strong>

                <span>
                  {platform}
                </span>

              </div>

            </div>

            {/* POST CONTENT */}

            <div className="preview-content">

              {aiPlan ? (
                <>

                  <h3>
                    {aiPlan.headline ||
                      topic}
                  </h3>

                  {aiPlan.subheadline && (
                    <p>
                      {aiPlan.subheadline}
                    </p>
                  )}

                  {aiPlan.introduction && (
                    <p>
                      {aiPlan.introduction}
                    </p>
                  )}

                  {aiPlan.sections?.length >
                    0 && (

                    <div className="ai-sections">

                      {aiPlan.sections.map(
                        (section) => (

                          <div
                            className="ai-section"
                            key={
                              section.number
                            }
                          >

                            <strong>
                              {section.title}
                            </strong>

                            <p>
                              {
                                section.description
                              }
                            </p>

                          </div>

                        ),
                      )}

                    </div>

                  )}

                  {aiPlan.key_takeaway && (
                    <p>

                      <strong>
                        Key Takeaway:
                      </strong>{" "}

                      {aiPlan.key_takeaway}

                    </p>
                  )}

                  {aiPlan.cta && (
                    <p>

                      <strong>
                        CTA:
                      </strong>{" "}

                      {aiPlan.cta}

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

                  <span>
                    AI VISUAL
                  </span>

                  <h3>
                    Generated Creative
                  </h3>

                </div>

                <span className="ai-image-status">
                  {aiPlan
                    ? "Ready"
                    : "Waiting"}
                </span>

              </div>

              <div className="ai-image-preview">

                {generatedImages.length >
                0 ? (

                  <div className="generated-images-container">

                    {generatedImages.map(
                      (
                        imageUrl,
                        index,
                      ) => (

                        <img
                          key={index}
                          src={imageUrl}
                          alt={`AI generated visual ${
                            index + 1
                          }`}
                          className="generated-ai-image"
                        />

                      ),
                    )}

                  </div>

                ) : (

                  <>

                    <div className="ai-image-glow"></div>

                    <div className="ai-image-content">

                      <div className="ai-image-icon">
                        ✦
                      </div>

                      <strong>

                        {aiPlan
                          ? "AI visual will be generated"
                          : "Your visual starts here"}

                      </strong>

                      <p>

                        AI will create a visual
                        based on your content
                        strategy.

                      </p>

                    </div>

                  </>

                )}

              </div>

              {/* KEEP THIS BUTTON FOR NOW */}

              <button
                className="generate-image-button"
                onClick={() =>
                  alert(
                    "Image generation will be connected to AI backend.",
                  )
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