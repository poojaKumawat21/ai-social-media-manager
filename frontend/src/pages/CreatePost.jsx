import React, { useEffect, useState } from "react";
import "./CreatePost.css";
import api from "../services/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function CreatePost() {
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");

  // ============================================================
  // PLATFORMS
  // ============================================================

  const [platforms, setPlatforms] = useState([]);
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);

  // ============================================================
  // AI
  // ============================================================

  const [isGenerating, setIsGenerating] = useState(false);
  const [aiPlan, setAiPlan] = useState(null);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [postId, setPostId] = useState(null);

  // ============================================================
  // PUBLISH
  // ============================================================

  const [publishingPlatform, setPublishingPlatform] = useState(null);
  const [isPublishingAll, setIsPublishingAll] = useState(false);

  // ============================================================
  // DRAFT
  // ============================================================

  const [isSavingDraft, setIsSavingDraft] = useState(false);

  // ============================================================
  // SCHEDULE
  // ============================================================

  const [scheduledAt, setScheduledAt] = useState("");
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);

  // ============================================================
  // LOCAL STORAGE KEYS
  // ============================================================

  const DRAFT_KEY = "postpilot_create_post_draft";
  const RESULT_KEY = "postpilot_create_post_result";
  const PENDING_KEY = "postpilot_create_post_pending";

  // ============================================================
  // LOAD CONNECTED ACCOUNTS
  // ============================================================

  useEffect(() => {
    const loadConnectedAccounts = async () => {
      try {
        setIsLoadingAccounts(true);

        const result = await api.get("/social-accounts");

        const accounts = result?.accounts || result || [];

        const connected = Array.isArray(accounts)
          ? accounts.filter(
              (account) =>
                account?.status === "connected" ||
                account?.connected === true
            )
          : [];

        setConnectedAccounts(connected);

        // --------------------------------------------------------
        // Keep only platforms that are actually connected.
        // If nothing is selected, select the first connected
        // platform to preserve the old default behavior.
        // --------------------------------------------------------

        setPlatforms((current) => {
          const connectedPlatformNames = connected
            .map((account) =>
              account?.platform?.toLowerCase()
            )
            .filter(Boolean);

          const validCurrent = current.filter((platform) =>
            connectedPlatformNames.includes(
              platform.toLowerCase()
            )
          );

          if (validCurrent.length > 0) {
            return validCurrent;
          }

          if (connectedPlatformNames.length > 0) {
            return [connectedPlatformNames[0]];
          }

          return [];
        });
      } catch (error) {
        console.error(
          "Failed to load connected accounts:",
          error
        );

        setConnectedAccounts([]);
        setPlatforms([]);
      } finally {
        setIsLoadingAccounts(false);
      }
    };

    loadConnectedAccounts();
  }, []);

  // ============================================================
  // RESTORE SAVED DATA
  // ============================================================

  useEffect(() => {
    try {
      const savedDraft = localStorage.getItem(DRAFT_KEY);

      if (savedDraft) {
        const draft = JSON.parse(savedDraft);

        setTopic(draft.topic || "");
        setDescription(draft.description || "");

        if (Array.isArray(draft.platforms)) {
          setPlatforms(
            draft.platforms
              .map((platform) =>
                platform?.toLowerCase()
              )
              .filter(Boolean)
          );
        } else if (draft.platform) {
          setPlatforms([
            draft.platform.toLowerCase(),
          ]);
        }
      }

      // --------------------------------------------------------
      // RESTORE GENERATED RESULT
      // --------------------------------------------------------

      const savedResult =
        localStorage.getItem(RESULT_KEY);

      if (savedResult) {
        const result = JSON.parse(savedResult);

        setAiPlan(result.aiPlan || null);

        setGeneratedImages(
          result.generatedImages || []
        );

        if (Array.isArray(result.platforms)) {
          setPlatforms(
            result.platforms
              .map((platform) =>
                platform?.toLowerCase()
              )
              .filter(Boolean)
          );
        }

        if (result.postId) {
          setPostId(result.postId);
        }
      }

      // ========================================================
      // EDIT SAVED DRAFT
      // ========================================================

      const editDraft = localStorage.getItem(
        "postpilot_edit_draft"
      );

      if (editDraft) {
        const draft = JSON.parse(editDraft);

        setPostId(draft.id || null);

        setTopic(draft.topic || "");

        setDescription(
          draft.caption || ""
        );

        if (Array.isArray(draft.platforms)) {
          setPlatforms(
            draft.platforms
              .map((platform) =>
                platform?.toLowerCase()
              )
              .filter(Boolean)
          );
        } else if (draft.platform) {
          setPlatforms([
            draft.platform.toLowerCase(),
          ]);
        }

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

          format: "single_post",
        });

        localStorage.removeItem(
          "postpilot_edit_draft"
        );
      }
    } catch (error) {
      console.error(
        "Failed to restore Create Post data:",
        error
      );
    }
  }, []);

  // ============================================================
  // SAVE DRAFT
  // ============================================================

  const handleSaveDraft = async () => {
    if (!topic.trim()) {
      alert(
        "Please enter a topic before saving the draft."
      );
      return;
    }

    if (!platforms.length) {
      alert(
        "Please select at least one connected platform."
      );
      return;
    }

    setIsSavingDraft(true);

    try {
      let result;

      if (postId) {
        result = await api.put(
          `/posts/${postId}`,
          {
            status: "draft",
            platforms,
          }
        );

        alert("Draft saved successfully!");
      } else {
        result = await api.post(
          "/posts/draft",
          {
            topic: topic.trim(),
            description: description.trim(),
            platforms,
          }
        );

        alert("Draft saved successfully!");
      }

      console.log(
        "DRAFT SAVED:",
        result
      );
    } catch (error) {
      console.error(
        "Save draft error:",
        error
      );

      alert(
        error.message ||
          "Unable to save draft."
      );
    } finally {
      setIsSavingDraft(false);
    }
  };

  // ============================================================
  // PUBLISH ONE PLATFORM
  // ============================================================

  const handlePublish = async (
    targetPlatform
  ) => {
    if (!postId) {
      alert(
        "Please generate a post first."
      );
      return;
    }

    if (!targetPlatform) {
      alert(
        "Please select a platform."
      );
      return;
    }

    const normalizedPlatform =
      targetPlatform.toLowerCase();

    setPublishingPlatform(
      normalizedPlatform
    );

    try {
      let result;

      // --------------------------------------------------------
      // LINKEDIN
      // --------------------------------------------------------

      if (
        normalizedPlatform ===
        "linkedin"
      ) {
        result = await api.post(
          `/posts/${postId}/publish/linkedin`
        );
      }

      // --------------------------------------------------------
      // INSTAGRAM
      // --------------------------------------------------------

      else if (
        normalizedPlatform ===
        "instagram"
      ) {
        result = await api.post(
          `/posts/${postId}/publish/instagram`
        );
      }

      // --------------------------------------------------------
      // OTHER PLATFORMS
      // --------------------------------------------------------

      else {
        alert(
          `Publishing for ${formatPlatformName(
            normalizedPlatform
          )} is not connected to a publisher yet.`
        );

        return;
      }

      console.log(
        `${normalizedPlatform.toUpperCase()} PUBLISH RESULT:`,
        result
      );

      alert(
        `Post published to ${formatPlatformName(
          normalizedPlatform
        )} successfully!`
      );
    } catch (error) {
      console.error(
        `${normalizedPlatform} publish error:`,
        error
      );

      alert(
        error.message ||
          `Unable to publish to ${formatPlatformName(
            normalizedPlatform
          )}.`
      );
    } finally {
      setPublishingPlatform(null);
    }
  };

  // ============================================================
  // PUBLISH TO ALL SELECTED / CONNECTED PLATFORMS
  // ============================================================

  const handlePublishAll = async () => {
    if (!postId) {
      alert(
        "Please generate a post first."
      );
      return;
    }

    if (!platforms.length) {
      alert(
        "Please select at least one connected platform."
      );
      return;
    }

    setIsPublishingAll(true);

    const results = [];

    try {
      // --------------------------------------------------------
      // Publish sequentially.
      //
      // Same post_id is used for every platform.
      //
      // Instagram -> /publish/instagram
      // LinkedIn  -> /publish/linkedin
      // --------------------------------------------------------

      for (const targetPlatform of platforms) {
        const normalizedPlatform =
          targetPlatform.toLowerCase();

        try {
          let result;

          if (
            normalizedPlatform ===
            "linkedin"
          ) {
            result = await api.post(
              `/posts/${postId}/publish/linkedin`
            );
          } else if (
            normalizedPlatform ===
            "instagram"
          ) {
            result = await api.post(
              `/posts/${postId}/publish/instagram`
            );
          } else {
            results.push({
              platform:
                normalizedPlatform,
              success: false,
              error:
                "Publisher not implemented yet.",
            });

            continue;
          }

          results.push({
            platform:
              normalizedPlatform,
            success: true,
            result,
          });
        } catch (error) {
          console.error(
            `Publish failed for ${normalizedPlatform}:`,
            error
          );

          results.push({
            platform:
              normalizedPlatform,
            success: false,
            error:
              error.message ||
              "Publishing failed.",
          });
        }
      }

      // --------------------------------------------------------
      // RESULT SUMMARY
      // --------------------------------------------------------

      console.log(
        "PUBLISH ALL RESULTS:",
        results
      );

      const successful =
        results.filter(
          (item) => item.success
        );

      const failed =
        results.filter(
          (item) => !item.success
        );

      if (failed.length === 0) {
        alert(
          `Post published to ${successful.length} platform${
            successful.length > 1
              ? "s"
              : ""
          } successfully!`
        );
      } else {
        const failedNames =
          failed
            .map((item) =>
              formatPlatformName(
                item.platform
              )
            )
            .join(", ");

        alert(
          `Published to ${successful.length} platform${
            successful.length !== 1
              ? "s"
              : ""
          }. Failed: ${failedNames}`
        );
      }
    } finally {
      setIsPublishingAll(false);
    }
  };

  // ============================================================
  // SCHEDULE
  // ============================================================

  const handleSchedulePost = async () => {
    if (!postId) {
      alert(
        "Please generate a post first."
      );
      return;
    }

    if (!platforms.length) {
      alert(
        "Please select at least one platform."
      );
      return;
    }

    if (!scheduledAt) {
      alert(
        "Please select a date and time."
      );
      return;
    }

    const selectedDate =
      new Date(scheduledAt);

    if (selectedDate <= new Date()) {
      alert(
        "Please select a future date and time."
      );
      return;
    }

    setIsScheduling(true);

    try {
      // --------------------------------------------------------
      // Currently schedule the first selected platform.
      // Publishing can still be done independently for every
      // selected platform.
      // --------------------------------------------------------

      const schedulePlatform =
        platforms[0];

      const result = await api.post(
        "/scheduled-posts",
        {
          post_id: postId,
          scheduled_at:
            selectedDate.toISOString(),
          platform:
            schedulePlatform,
        }
      );

      console.log(
        "SCHEDULED POST:",
        result
      );

      alert(
        `Post scheduled successfully for ${formatPlatformName(
          schedulePlatform
        )}!`
      );

      setScheduledAt("");
    } catch (error) {
      console.error(
        "Schedule post error:",
        error
      );

      alert(
        error.message ||
          "Unable to schedule post."
      );
    } finally {
      setIsScheduling(false);
    }
  };

  // ============================================================
  // LOCAL STORAGE - DRAFT
  // ============================================================

  useEffect(() => {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        topic,
        description,
        platforms,
      })
    );
  }, [
    topic,
    description,
    platforms,
  ]);

  // ============================================================
  // LOCAL STORAGE - RESULT
  // ============================================================

  useEffect(() => {
    if (
      !aiPlan &&
      generatedImages.length === 0
    ) {
      return;
    }

    localStorage.setItem(
      RESULT_KEY,
      JSON.stringify({
        postId,
        aiPlan,
        generatedImages,
        platforms,
      })
    );
  }, [
    postId,
    aiPlan,
    generatedImages,
    platforms,
  ]);

  // ============================================================
  // PLATFORM SELECT / TOGGLE
  // ============================================================

  const togglePlatform = (
    platformName
  ) => {
    const normalized =
      platformName.toLowerCase();

    setPlatforms((current) => {
      if (
        current.includes(normalized)
      ) {
        return current.filter(
          (item) =>
            item !== normalized
        );
      }

      return [
        ...current,
        normalized,
      ];
    });
  };

  // ============================================================
  // GENERATE AI
  // ============================================================

  const handleGenerateAI = async () => {
    if (!topic.trim()) {
      alert(
        "Please enter a topic."
      );
      return;
    }

    if (!platforms.length) {
      alert(
        "Please select at least one connected platform."
      );
      return;
    }

    setIsGenerating(true);

    setAiPlan(null);
    setGeneratedImages([]);

    localStorage.setItem(
      PENDING_KEY,
      JSON.stringify({
        topic: topic.trim(),
        platforms,
        startedAt: Date.now(),
      })
    );

    try {
      // ========================================================
      // IMPORTANT:
      //
      // ONLY ONE GENERATION REQUEST.
      //
      // Backend will run ONE AI pipeline and create ONE post_id.
      //
      // Example:
      //
      // Instagram + LinkedIn selected
      //
      // => ONE /posts/generate call
      // => ONE AI pipeline
      // => ONE post_id
      //
      // NOT:
      // Instagram generation
      // + LinkedIn generation
      // ========================================================

      const result = await api.post(
        "/posts/generate",
        {
          topic: topic.trim(),
          description:
            description.trim(),
          platforms,
        }
      );

      console.log(
        "GENERATED POST:",
        result
      );

      // --------------------------------------------------------
      // SAVE ONE POST ID
      // --------------------------------------------------------

      setPostId(
        result?.post?.id || null
      );

      // --------------------------------------------------------
      // AI RESULT
      // --------------------------------------------------------

      const aiResult =
        result?.ai_result || {};

      const planner =
        aiResult?.planner || {};

      const content =
        aiResult?.content || {};

      const combinedPlan = {
        ...planner,
        ...content,
      };

      setAiPlan(
        combinedPlan
      );

      // ========================================================
      // GET IMAGE URLS
      // ========================================================

      let mediaUrls =
        result?.post?.media_urls ||
        [];

      // --------------------------------------------------------
      // FALLBACK 1:
      // uploaded_images
      // --------------------------------------------------------

      if (!mediaUrls.length) {
        mediaUrls = (
          aiResult?.uploaded_images ||
          []
        )
          .map(
            (image) =>
              image?.storage
                ?.public_url ||
              image?.storage?.url ||
              image?.url
          )
          .filter(Boolean);
      }

      // --------------------------------------------------------
      // FALLBACK 2:
      // renderer images
      // --------------------------------------------------------

      if (!mediaUrls.length) {
        mediaUrls = (
          aiResult?.render
            ?.images || []
        )
          .map(
            (image) =>
              image?.url
          )
          .filter(Boolean);
      }

      // --------------------------------------------------------
      // NORMALIZE IMAGE URL
      // --------------------------------------------------------

      const fullImageUrls =
        mediaUrls
          .filter(Boolean)
          .map((url) => {
            if (
              /^https?:\/\//i.test(
                url
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

      console.log(
        "IMAGE URLS:",
        fullImageUrls
      );

      setGeneratedImages(
        fullImageUrls
      );

      // --------------------------------------------------------
      // SAVE RESULT
      // --------------------------------------------------------

      localStorage.setItem(
        RESULT_KEY,
        JSON.stringify({
          postId:
            result?.post?.id ||
            null,
          aiPlan:
            combinedPlan,
          generatedImages:
            fullImageUrls,
          platforms:
            result?.post?.platforms ||
            platforms,
        })
      );

      localStorage.removeItem(
        PENDING_KEY
      );

      alert(
        "AI post generated successfully!"
      );
    } catch (error) {
      console.error(
        "AI generation error:",
        error
      );

      localStorage.removeItem(
        PENDING_KEY
      );

      if (
        error?.message?.includes(
          "401"
        )
      ) {
        alert(
          "Your session has expired. Please login again."
        );

        localStorage.removeItem(
          "access_token"
        );

        localStorage.removeItem(
          "refresh_token"
        );

        localStorage.removeItem(
          "user_id"
        );

        localStorage.removeItem(
          "user_email"
        );

        return;
      }

      alert(
        error?.message ||
          "Unable to generate post. Make sure the backend is running."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // ============================================================
  // RESTORE PENDING GENERATION
  // ============================================================

  useEffect(() => {
    const pendingData =
      localStorage.getItem(
        PENDING_KEY
      );

    if (!pendingData) {
      return;
    }

    let pending;

    try {
      pending =
        JSON.parse(
          pendingData
        );
    } catch {
      localStorage.removeItem(
        PENDING_KEY
      );

      return;
    }

    let intervalId = null;
    let cancelled = false;

    const checkGeneratedPost =
      async () => {
        try {
          const result =
            await api.get(
              "/posts"
            );

          const posts =
            result?.posts || [];

          const generatedPost =
            posts.find(
              (post) => {
                const createdAt =
                  post?.created_at
                    ? new Date(
                        post.created_at
                      ).getTime()
                    : 0;

                return (
                  post?.topic ===
                    pending.topic &&
                  post?.status ===
                    "generated" &&
                  createdAt >=
                    pending.startedAt
                );
              }
            );

          if (
            !generatedPost ||
            cancelled
          ) {
            return false;
          }

          // ----------------------------------------------------
          // RESTORE ONE POST ID
          // ----------------------------------------------------

          setPostId(
            generatedPost?.id ||
              null
          );

          const restoredPlan = {
            headline:
              generatedPost?.post_idea ||
              generatedPost?.topic,

            caption:
              generatedPost?.caption ||
              "",

            hashtags:
              generatedPost?.hashtags ||
              [],

            tone:
              generatedPost?.tone ||
              "Professional",

            selected_style:
              generatedPost?.style ||
              "AI Selected",

            format:
              "single_post",
          };

          // ----------------------------------------------------
          // RESTORE IMAGES
          // ----------------------------------------------------

          const mediaUrls = (
            generatedPost?.media_urls ||
            []
          )
            .filter(Boolean)
            .map((url) => {
              if (
                /^https?:\/\//i.test(
                  url
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
            generatedPost?.topic ||
              pending.topic
          );

          // ----------------------------------------------------
          // RESTORE PLATFORMS
          // ----------------------------------------------------

          if (
            Array.isArray(
              generatedPost?.platforms
            )
          ) {
            setPlatforms(
              generatedPost.platforms
                .map((platform) =>
                  platform?.toLowerCase()
                )
                .filter(Boolean)
            );
          } else if (
            Array.isArray(
              pending?.platforms
            )
          ) {
            setPlatforms(
              pending.platforms
                .map((platform) =>
                  platform?.toLowerCase()
                )
                .filter(Boolean)
            );
          }

          setAiPlan(
            restoredPlan
          );

          setGeneratedImages(
            mediaUrls
          );

          localStorage.setItem(
            RESULT_KEY,
            JSON.stringify({
              postId:
                generatedPost?.id ||
                null,

              aiPlan:
                restoredPlan,

              generatedImages:
                mediaUrls,

              platforms:
                generatedPost?.platforms ||
                pending?.platforms ||
                [],
            })
          );

          localStorage.removeItem(
            PENDING_KEY
          );

          return true;
        } catch (error) {
          console.error(
            "Checking generated post:",
            error
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
                    intervalId
                  );

                  intervalId = null;
                }
              },
              3000
            );
        }
      };

    startChecking();

    return () => {
      cancelled = true;

      if (intervalId) {
        clearInterval(
          intervalId
        );
      }
    };
  }, []);

  // ============================================================
  // DISPLAY NAME
  // ============================================================

  const formatPlatformName = (
    platformName
  ) => {
    if (!platformName) {
      return "";
    }

    return (
      platformName
        .charAt(0)
        .toUpperCase() +
      platformName.slice(1)
    );
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="create-post-page">

      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

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

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <div className="create-post-grid">

        {/* ====================================================
            LEFT: EDITOR
        ==================================================== */}

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

          {/* ==================================================
              TOPIC
          ================================================== */}

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
                setTopic(
                  e.target.value
                )
              }
              placeholder="What do you want to post about?"
            />

          </div>

          {/* ==================================================
              DESCRIPTION
          ================================================== */}

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
                  e.target.value
                )
              }
              placeholder="Tell AI anything specific you want it to consider..."
              rows="7"
            />

            <div className="content-meta">

              <span>
                {description.length}{" "}
                characters
              </span>

              <span>
                AI decides the content
                strategy
              </span>

            </div>

          </div>

          {/* ==================================================
              CONNECTED PLATFORMS
          ================================================== */}

          <div className="form-group">

            <label>
              Platforms
            </label>

            {isLoadingAccounts ? (

              <div className="platform-loading">
                Loading connected platforms...
              </div>

            ) : connectedAccounts.length === 0 ? (

              <div className="platform-empty">

                <strong>
                  No connected platforms
                </strong>

                <span>
                  Connect a social account
                  first from Connected
                  Accounts.
                </span>

              </div>

            ) : (

              <div className="platform-select-grid">

                {connectedAccounts.map(
                  (account) => {

                    const platformName =
                      account?.platform?.toLowerCase();

                    if (!platformName) {
                      return null;
                    }

                    const isSelected =
                      platforms.includes(
                        platformName
                      );

                    return (

                      <button
                        type="button"
                        key={
                          account?.id ||
                          platformName
                        }
                        className={`platform-select-card ${
                          isSelected
                            ? "selected"
                            : ""
                        }`}
                        onClick={() =>
                          togglePlatform(
                            platformName
                          )
                        }
                      >

                        <span className="platform-checkbox">
                          {isSelected
                            ? "✓"
                            : ""}
                        </span>

                        <span className="platform-select-info">

                          <strong>
                            {formatPlatformName(
                              platformName
                            )}
                          </strong>

                          <small>
                            {account?.account_name ||
                              account?.username ||
                              "Connected"}
                          </small>

                        </span>

                      </button>

                    );
                  }
                )}

              </div>

            )}

            <small className="field-help">
              Only connected social accounts
              are available for publishing.
            </small>

            {platforms.length > 0 && (

              <div className="selected-platform-summary">

                {platforms.length}{" "}
                platform
                {platforms.length > 1
                  ? "s"
                  : ""}{" "}
                selected

              </div>

            )}

          </div>

          {/* ==================================================
              AI STRATEGY
          ================================================== */}

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
                platforms.

              </div>

            )}

          </div>

          {/* ==================================================
              AI HASHTAGS
          ================================================== */}

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

                  )
                )}

              </div>

            </div>

          )}

          {/* ==================================================
              GENERATE
          ================================================== */}

          <button
            className="generate-ai-button"
            onClick={
              handleGenerateAI
            }
            disabled={
              isGenerating ||
              isLoadingAccounts ||
              connectedAccounts.length ===
                0 ||
              platforms.length === 0
            }
          >

            {isGenerating
              ? "✦ Generating..."
              : "✦ Generate with AI"}

          </button>

          {/* ==================================================
              SAVE / SCHEDULE
          ================================================== */}

          <div className="post-actions">

            <button
              className="save-draft-button"
              onClick={
                handleSaveDraft
              }
              disabled={
                isSavingDraft
              }
            >

              {isSavingDraft
                ? "Saving..."
                : "Save Draft"}

            </button>

            <button
              className="schedule-post-button"
              onClick={() =>
                setIsScheduleOpen(
                  true
                )
              }
              disabled={
                isScheduling ||
                !postId
              }
            >

              {isScheduling
                ? "Scheduling..."
                : "Schedule Post"}

            </button>

          </div>

          {/* ==================================================
              PUBLISH ACTIONS
          ================================================== */}

          {postId &&
            platforms.length > 0 && (

              <div className="publish-actions">

                {/* --------------------------------------------
                    INDEPENDENT PUBLISH BUTTONS
                -------------------------------------------- */}

                {platforms.map(
                  (targetPlatform) => (

                    <button
                      key={
                        targetPlatform
                      }
                      type="button"
                      className="publish-platform-button"
                      onClick={() =>
                        handlePublish(
                          targetPlatform
                        )
                      }
                      disabled={
                        isPublishingAll ||
                        publishingPlatform ===
                          targetPlatform
                      }
                    >

                      {publishingPlatform ===
                      targetPlatform
                        ? `Publishing ${formatPlatformName(
                            targetPlatform
                          )}...`
                        : `Publish to ${formatPlatformName(
                            targetPlatform
                          )}`}

                    </button>

                  )
                )}

                {/* --------------------------------------------
                    PUBLISH ALL
                -------------------------------------------- */}

                {platforms.length > 1 && (

                  <button
                    type="button"
                    className="publish-all-button"
                    onClick={
                      handlePublishAll
                    }
                    disabled={
                      isPublishingAll ||
                      publishingPlatform !==
                        null
                    }
                  >

                    {isPublishingAll
                      ? "Publishing to all..."
                      : "Publish to All Connected"}

                  </button>

                )}

              </div>

            )}

        </div>

        {/* ====================================================
            RIGHT: PREVIEW
        ==================================================== */}

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

          <div className="social-preview">

            {/* ==================================================
                PROFILE
            ================================================== */}

            <div className="preview-profile">

              <div className="preview-avatar">
                AI
              </div>

              <div>

                <strong>
                  Your Brand
                </strong>

                <span>

                  {platforms.length
                    ? platforms
                        .map(
                          formatPlatformName
                        )
                        .join(" + ")
                    : "No platform selected"}

                </span>

              </div>

            </div>

            {/* ==================================================
                POST CONTENT
            ================================================== */}

            <div className="preview-content">

              {aiPlan ? (

                <>

                  <h3>
                    {aiPlan.headline ||
                      topic}
                  </h3>

                  {aiPlan.subheadline && (

                    <p>
                      {
                        aiPlan.subheadline
                      }
                    </p>

                  )}

                  {aiPlan.introduction && (

                    <p>
                      {
                        aiPlan.introduction
                      }
                    </p>

                  )}

                  {aiPlan.sections
                    ?.length > 0 && (

                    <div className="ai-sections">

                      {aiPlan.sections.map(
                        (
                          section
                        ) => (

                          <div
                            className="ai-section"
                            key={
                              section.number
                            }
                          >

                            <strong>
                              {
                                section.title
                              }
                            </strong>

                            <p>
                              {
                                section.description
                              }
                            </p>

                          </div>

                        )
                      )}

                    </div>

                  )}

                  {aiPlan.key_takeaway && (

                    <p>

                      <strong>
                        Key Takeaway:
                      </strong>{" "}

                      {
                        aiPlan.key_takeaway
                      }

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

            {/* ==================================================
                AI IMAGE
            ================================================== */}

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
                        index
                      ) => (

                        <img
                          key={
                            index
                          }
                          src={
                            imageUrl
                          }
                          alt={`AI generated visual ${
                            index + 1
                          }`}
                          className="generated-ai-image"
                        />

                      )
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

              <button
                className="generate-image-button"
                onClick={() =>
                  alert(
                    "Image generation will be connected to AI backend."
                  )
                }
              >

                ✦ Generate Visual

              </button>

            </div>

          </div>

        </div>

      </div>

      {/* ======================================================
          SCHEDULE MODAL
      ====================================================== */}

      {isScheduleOpen && (

        <div className="schedule-modal-overlay">

          <div className="schedule-modal">

            <div className="schedule-modal-header">

              <div>

                <span className="schedule-modal-label">
                  SCHEDULE
                </span>

                <h3>
                  Schedule Post
                </h3>

              </div>

              <button
                type="button"
                className="schedule-close-button"
                onClick={() =>
                  setIsScheduleOpen(
                    false
                  )
                }
              >
                ×
              </button>

            </div>

            <div className="schedule-field">

              <label>
                Select Date & Time
              </label>

              <input
                type="datetime-local"
                value={
                  scheduledAt
                }
                onChange={(e) =>
                  setScheduledAt(
                    e.target.value
                  )
                }
                min={
                  new Date()
                    .toISOString()
                    .slice(
                      0,
                      16
                    )
                }
              />

            </div>

            <div className="schedule-modal-actions">

              <button
                type="button"
                className="schedule-cancel-button"
                onClick={() =>
                  setIsScheduleOpen(
                    false
                  )
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="schedule-confirm-button"
                onClick={async () => {
                  await handleSchedulePost();

                  setIsScheduleOpen(
                    false
                  );
                }}
                disabled={
                  !scheduledAt ||
                  isScheduling
                }
              >

                {isScheduling
                  ? "Scheduling..."
                  : "Schedule"}

              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default CreatePost;