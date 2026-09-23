import React, { useEffect, useState } from "react";

import "./CreatePost.css";
import api from "../services/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const USER_ID_KEY = "user_id";

function CreatePost() {
  // ============================================================
  // CURRENT USER
  // ============================================================

  const [currentUserId, setCurrentUserId] = useState(
    () => localStorage.getItem(USER_ID_KEY)
  );

  // ============================================================
  // USER-SCOPED STORAGE KEYS
  // ============================================================

  const getUserStorageKey = (baseKey) => {
    if (!currentUserId) {
      return null;
    }

    return `${baseKey}_${currentUserId}`;
  };

  const DRAFT_KEY = getUserStorageKey(
    "postpilot_create_post_draft"
  );

  const RESULT_KEY = getUserStorageKey(
    "postpilot_create_post_result"
  );

  const PENDING_KEY = getUserStorageKey(
    "postpilot_create_post_pending"
  );

  const EDIT_DRAFT_KEY = getUserStorageKey(
    "postpilot_edit_draft"
  );

  // ============================================================
  // FORM
  // ============================================================

  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");

  // ============================================================
  // PLATFORMS
  // ============================================================

  const [platforms, setPlatforms] = useState([]);
  const [connectedAccounts, setConnectedAccounts] =
    useState([]);
  const [isLoadingAccounts, setIsLoadingAccounts] =
    useState(true);

  // ============================================================
  // AI
  // ============================================================

  const [isGenerating, setIsGenerating] =
    useState(false);

  const [aiPlan, setAiPlan] = useState(null);

  const [generatedImages, setGeneratedImages] =
    useState([]);

  const [postId, setPostId] = useState(null);

  // ============================================================
  // PUBLISH
  // ============================================================

  const [publishingPlatform, setPublishingPlatform] =
    useState(null);

  const [isPublishingAll, setIsPublishingAll] =
    useState(false);

  // false = Text + Hashtags
  // true = Image + Text + Hashtags
  const [xIncludeImage, setXIncludeImage] =
    useState(false);

  // ============================================================
  // DRAFT
  // ============================================================

  const [isSavingDraft, setIsSavingDraft] =
    useState(false);

  // ============================================================
  // SCHEDULE
  // ============================================================

  const [scheduledAt, setScheduledAt] = useState("");
  const [isScheduleOpen, setIsScheduleOpen] =
    useState(false);
  const [isScheduling, setIsScheduling] =
    useState(false);

  // ============================================================
  // SYNC CURRENT USER
  // ============================================================

  useEffect(() => {
    const syncCurrentUser = () => {
      const loggedInUserId =
        localStorage.getItem(USER_ID_KEY);

      setCurrentUserId(loggedInUserId);
    };

    syncCurrentUser();

    window.addEventListener(
      "storage",
      syncCurrentUser
    );

    return () => {
      window.removeEventListener(
        "storage",
        syncCurrentUser
      );
    };
  }, []);

  // ============================================================
  // LOAD CONNECTED ACCOUNTS
  // ============================================================

  useEffect(() => {
    if (!currentUserId) {
      setConnectedAccounts([]);
      setPlatforms([]);
      setIsLoadingAccounts(false);
      return;
    }

    let cancelled = false;

    const loadConnectedAccounts = async () => {
      try {
        setIsLoadingAccounts(true);

        const result = await api.get(
          "/social-accounts"
        );

        if (cancelled) {
          return;
        }

        const accounts =
          result?.accounts ||
          result?.data?.accounts ||
          result?.data ||
          result ||
          [];

        const connected = Array.isArray(accounts)
          ? accounts.filter(
              (account) =>
                account?.status === "connected" ||
                account?.connected === true
            )
          : [];

        setConnectedAccounts(connected);

        setPlatforms((current) => {
          const connectedPlatformNames =
            connected
              .map((account) =>
                account?.platform?.toLowerCase()
              )
              .filter(Boolean);

          const validCurrent = current.filter(
            (platform) =>
              connectedPlatformNames.includes(
                platform.toLowerCase()
              )
          );

          if (validCurrent.length > 0) {
            return validCurrent;
          }

          if (
            connectedPlatformNames.length > 0
          ) {
            return [
              connectedPlatformNames[0],
            ];
          }

          return [];
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        console.error(
          "Failed to load connected accounts:",
          error
        );

        setConnectedAccounts([]);
        setPlatforms([]);
      } finally {
        if (!cancelled) {
          setIsLoadingAccounts(false);
        }
      }
    };

    loadConnectedAccounts();

    return () => {
      cancelled = true;
    };
  }, [currentUserId]);

  // ============================================================
  // RESTORE USER-SCOPED SAVED DATA
  // ============================================================

  useEffect(() => {
    if (!currentUserId) {
      return;
    }

    try {
      // --------------------------------------------------------
      // RESTORE DRAFT
      // --------------------------------------------------------

      const savedDraft = DRAFT_KEY
        ? localStorage.getItem(DRAFT_KEY)
        : null;

      if (savedDraft) {
        const draft = JSON.parse(savedDraft);

        setTopic(draft.topic || "");
        setDescription(
          draft.description || ""
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
      }

      // --------------------------------------------------------
      // RESTORE GENERATED RESULT
      // --------------------------------------------------------

      const savedResult = RESULT_KEY
        ? localStorage.getItem(RESULT_KEY)
        : null;

      if (savedResult) {
        const result = JSON.parse(savedResult);

        setAiPlan(
          result.aiPlan || null
        );

        setGeneratedImages(
          Array.isArray(
            result.generatedImages
          )
            ? result.generatedImages
            : []
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

      // --------------------------------------------------------
      // RESTORE EDIT DRAFT
      // --------------------------------------------------------

      const editDraft = EDIT_DRAFT_KEY
        ? localStorage.getItem(
            EDIT_DRAFT_KEY
          )
        : null;

      if (editDraft) {
        const draft = JSON.parse(
          editDraft
        );

        setPostId(draft.id || null);

        setTopic(
          draft.topic || ""
        );

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
          Array.isArray(
            draft.media_urls
          )
            ? draft.media_urls.filter(
                Boolean
              )
            : []
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
          EDIT_DRAFT_KEY
        );
      }
    } catch (error) {
      console.error(
        "Failed to restore Create Post data:",
        error
      );
    }
  }, [
    currentUserId,
    DRAFT_KEY,
    RESULT_KEY,
    EDIT_DRAFT_KEY,
  ]);

  // ============================================================
  // X POST TEXT
  // ============================================================

  const getXPostText = () => {
    const caption =
      aiPlan?.caption ||
      aiPlan?.description ||
      "";

    const hashtags = Array.isArray(
      aiPlan?.hashtags
    )
      ? aiPlan.hashtags
      : [];

    const hashtagText = hashtags.length
      ? hashtags
          .map((hashtag) => {
            const value =
              String(hashtag).trim();

            if (!value) {
              return "";
            }

            return value.startsWith("#")
              ? value
              : `#${value}`;
          })
          .filter(Boolean)
          .join(" ")
      : "";

    return [caption.trim(), hashtagText]
      .filter(Boolean)
      .join("\n\n");
  };

  const xPostText = getXPostText();

  const xCharacterCount =
    xPostText.length;

  const isXOverLimit =
    xCharacterCount > 280;

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

        alert(
          "Draft saved successfully!"
        );
      } else {
        result = await api.post(
          "/posts/draft",
          {
            topic: topic.trim(),
            description:
              description.trim(),
            platforms,
          }
        );

        alert(
          "Draft saved successfully!"
        );
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
    targetPlatform,
    includeImage = false
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
      // X
      // --------------------------------------------------------

      else if (
        normalizedPlatform === "x"
      ) {
        if (isXOverLimit) {
          alert(
            `X post is ${xCharacterCount} characters. Maximum allowed is 280.`
          );
          return;
        }

        if (
          includeImage &&
          generatedImages.length === 0
        ) {
          alert(
            "Image publishing is selected, but no generated image is available."
          );
          return;
        }

        result = await api.post(
          `/posts/${postId}/publish/x`,
          {
            include_image:
              includeImage,
          }
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
  // PUBLISH ALL
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
      for (const targetPlatform of platforms) {
        const normalizedPlatform =
          targetPlatform.toLowerCase();

        try {
          let result;

          // ----------------------------------------------------
          // LINKEDIN
          // ----------------------------------------------------

          if (
            normalizedPlatform ===
            "linkedin"
          ) {
            result = await api.post(
              `/posts/${postId}/publish/linkedin`
            );
          }

          // ----------------------------------------------------
          // INSTAGRAM
          // ----------------------------------------------------

          else if (
            normalizedPlatform ===
            "instagram"
          ) {
            result = await api.post(
              `/posts/${postId}/publish/instagram`
            );
          }

          // ----------------------------------------------------
          // X
          // ----------------------------------------------------

          else if (
            normalizedPlatform === "x"
          ) {
            if (isXOverLimit) {
              results.push({
                platform:
                  normalizedPlatform,
                success: false,
                error: `X post exceeds 280 characters (${xCharacterCount}).`,
              });

              continue;
            }

            if (
              xIncludeImage &&
              generatedImages.length === 0
            ) {
              results.push({
                platform:
                  normalizedPlatform,
                success: false,
                error:
                  "X image publishing was selected but no image is available.",
              });

              continue;
            }

            result = await api.post(
              `/posts/${postId}/publish/x`,
              {
                include_image:
                  xIncludeImage,
              }
            );
          }

          // ----------------------------------------------------
          // UNSUPPORTED
          // ----------------------------------------------------

          else {
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
      alert("Please generate a post first.");
      return false;
    }

    if (!platforms.length) {
      alert("Please select at least one platform.");
      return false;
    }

    if (!scheduledAt) {
      alert("Please select a date and time.");
      return false;
    }

    const selectedDate = new Date(scheduledAt);

    if (Number.isNaN(selectedDate.getTime())) {
      alert("Invalid date and time selected.");
      return false;
    }

    if (selectedDate <= new Date()) {
      alert("Please select a future date and time.");
      return false;
    }

    setIsScheduling(true);

    try {
      const results = [];

      for (const targetPlatform of platforms) {
        const normalizedPlatform = String(targetPlatform).toLowerCase().trim();

        try {
          const result = await api.post("/scheduled-posts", {
            post_id: postId,
            scheduled_at: selectedDate.toISOString(),
            platform: normalizedPlatform,
          });

          console.log(`SCHEDULED ${normalizedPlatform.toUpperCase()}:`, result);

          results.push({
            platform: normalizedPlatform,
            success: true,
            result,
          });
        } catch (error) {
          console.error(`Scheduling failed for ${normalizedPlatform}:`, error);

          results.push({
            platform: normalizedPlatform,
            success: false,
            error: error?.message || "Scheduling failed.",
          });
        }
      }

      const successful = results.filter((item) => item.success);
      const failed = results.filter((item) => !item.success);

      if (successful.length > 0 && failed.length === 0) {
        const scheduledNames = successful
          .map((item) => formatPlatformName(item.platform))
          .join(", \ ");

        alert(`Post scheduled successfully for ${scheduledNames}!`);
        setScheduledAt("");
        setIsScheduleOpen(false);
        return true;
      }

      if (successful.length > 0 && failed.length > 0) {
        const successfulNames = successful
          .map((item) => formatPlatformName(item.platform))
          .join(", \ ");
        const failedNames = failed
          .map((item) => formatPlatformName(item.platform))
          .join(", \ ");

        alert(`Scheduled for: ${successfulNames}. Failed: ${failedNames}.`);
        return true;
      }

      alert("Unable to schedule the post for the selected platforms.");
      return false;
    } finally {
      setIsScheduling(false);
    }
  };

  // ============================================================
  // SAVE USER-SCOPED DRAFT TO LOCAL STORAGE
  // ============================================================

  useEffect(() => {
    if (!currentUserId || !DRAFT_KEY) {
      return;
    }

    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        topic,
        description,
        platforms,
      })
    );
  }, [
    currentUserId,
    DRAFT_KEY,
    topic,
    description,
    platforms,
  ]);

  // ============================================================
  // SAVE USER-SCOPED GENERATED RESULT
  // ============================================================

  useEffect(() => {
    if (!currentUserId || !RESULT_KEY) {
      return;
    }

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
    currentUserId,
    RESULT_KEY,
    postId,
    aiPlan,
    generatedImages,
    platforms,
  ]);

  // ============================================================
  // PLATFORM TOGGLE
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
    if (!currentUserId) {
      alert(
        "Your session is not ready. Please login again."
      );
      return;
    }

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
    setPostId(null);

    // ----------------------------------------------------------
    // USER-SCOPED PENDING STATE
    // ----------------------------------------------------------

    if (PENDING_KEY) {
      localStorage.setItem(
        PENDING_KEY,
        JSON.stringify({
          topic: topic.trim(),
          platforms,
          startedAt: Date.now(),
        })
      );
    }

    try {
      // ========================================================
      // ONE GENERATION REQUEST ONLY
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
      // ONE POST ID
      // --------------------------------------------------------

      const generatedPostId =
        result?.post?.id ||
        null;

      setPostId(
        generatedPostId
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

      // --------------------------------------------------------
      // IMAGE URLS
      // --------------------------------------------------------

      let mediaUrls =
        Array.isArray(
          result?.post?.media_urls
        )
          ? result.post.media_urls
          : [];

      // --------------------------------------------------------
      // FALLBACK 1: UPLOADED IMAGES
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
      // FALLBACK 2: RENDER IMAGES
      // --------------------------------------------------------

      if (!mediaUrls.length) {
        mediaUrls = (
          aiResult?.render?.images ||
          []
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
      // SAVE USER-SCOPED RESULT
      // --------------------------------------------------------

      if (RESULT_KEY) {
        localStorage.setItem(
          RESULT_KEY,
          JSON.stringify({
            postId:
              generatedPostId,

            aiPlan:
              combinedPlan,

            generatedImages:
              fullImageUrls,

            platforms:
              result?.post
                ?.platforms ||
              platforms,
          })
        );
      }

      // --------------------------------------------------------
      // REMOVE PENDING
      // --------------------------------------------------------

      if (PENDING_KEY) {
        localStorage.removeItem(
          PENDING_KEY
        );
      }

      alert(
        "AI post generated successfully!"
      );
    } catch (error) {
      console.error(
        "AI generation error:",
        error
      );

      if (PENDING_KEY) {
        localStorage.removeItem(
          PENDING_KEY
        );
      }

      // --------------------------------------------------------
      // SESSION EXPIRED
      // --------------------------------------------------------

      if (
        error?.message?.includes("401")
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

        setCurrentUserId(null);

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
    if (
      !currentUserId ||
      !PENDING_KEY
    ) {
      return;
    }

    const pendingData =
      localStorage.getItem(
        PENDING_KEY
      );

    if (!pendingData) {
      return;
    }

    let pending;

    try {
      pending = JSON.parse(
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
          // RESTORE POST ID
          // ----------------------------------------------------

          setPostId(
            generatedPost?.id ||
              null
          );

          // ----------------------------------------------------
          // RESTORE PLAN
          // ----------------------------------------------------

          const restoredPlan = {
            headline:
              generatedPost?.post_idea ||
              generatedPost?.topic ||
              "",

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

          // ----------------------------------------------------
          // RESTORE TOPIC
          // ----------------------------------------------------

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

          // ----------------------------------------------------
          // SAVE RESTORED RESULT
          // ----------------------------------------------------

          if (RESULT_KEY) {
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
          }

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
  }, [
    currentUserId,
    PENDING_KEY,
    RESULT_KEY,
  ]);

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
            ) : connectedAccounts.length ===
              0 ? (
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
              type="button"
              className="schedule-post-button"
              onClick={() => {
                if (!postId) {
                  alert("Please generate a post first.");
                  return;
                }
                if (!platforms.length) {
                  alert("Please select at least one connected platform.");
                  return;
                }
                setScheduledAt("");
                setIsScheduleOpen(true);
              }}
              disabled={
                isScheduling ||
                !postId ||
                platforms.length === 0
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

                {/* X OPTIONS */}

                {platforms.includes(
                  "x"
                ) && (
                  <div className="x-publish-options">

                    <div className="x-publish-title">
                      X Publishing Options
                    </div>

                    <label className="x-publish-option">
                      <input
                        type="radio"
                        name="xPublishMode"
                        checked={
                          !xIncludeImage
                        }
                        onChange={() =>
                          setXIncludeImage(
                            false
                          )
                        }
                      />

                      <span>
                        Text + Hashtags only
                      </span>
                    </label>

                    <label className="x-publish-option">
                      <input
                        type="radio"
                        name="xPublishMode"
                        checked={
                          xIncludeImage
                        }
                        onChange={() =>
                          setXIncludeImage(
                            true
                          )
                        }
                      />

                      <span>
                        Image + Text + Hashtags
                      </span>
                    </label>

                    <div className="x-character-count">
                      {xCharacterCount} / 280
                      {" "}
                      characters
                    </div>

                    {xIncludeImage &&
                      generatedImages.length ===
                        0 && (
                        <div className="x-character-error">
                          Image publishing is selected,
                          but no generated image is
                          available for this post.
                        </div>
                      )}

                    {isXOverLimit && (
                      <div className="x-character-error">
                        X post exceeds the 280
                        character limit.
                      </div>
                    )}

                  </div>
                )}

                {/* INDEPENDENT PUBLISH BUTTONS */}

                {platforms.map(
                  (targetPlatform) => {
                    const normalizedPlatform =
                      targetPlatform.toLowerCase();

                    const isX =
                      normalizedPlatform ===
                      "x";

                    return (
                      <button
                        key={
                          targetPlatform
                        }
                        type="button"
                        className="publish-platform-button"
                        onClick={() =>
                          handlePublish(
                            targetPlatform,
                            isX
                              ? xIncludeImage
                              : false
                          )
                        }
                        disabled={
                          isPublishingAll ||
                          publishingPlatform ===
                            normalizedPlatform ||
                          (isX &&
                            isXOverLimit) ||
                          (isX &&
                            xIncludeImage &&
                            generatedImages.length ===
                              0)
                        }
                      >
                        {publishingPlatform ===
                        normalizedPlatform
                          ? `Publishing ${formatPlatformName(
                              targetPlatform
                            )}...`
                          : `Publish to ${formatPlatformName(
                              targetPlatform
                            )}`}
                      </button>
                    );
                  }
                )}

                {/* PUBLISH ALL */}

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
                        null ||
                      (platforms.includes(
                        "x"
                      ) &&
                        isXOverLimit) ||
                      (platforms.includes(
                        "x"
                      ) &&
                        xIncludeImage &&
                        generatedImages.length ===
                          0)
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
                        (section) => (
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
                Platforms
              </label>

              <div className="schedule-platform-summary">
                {platforms.map((platform) => (
                  <span
                    key={platform}
                    className="schedule-platform-chip"
                  >
                    {formatPlatformName(platform)}
                  </span>
                ))}
              </div>

              <small className="field-help">
                The same generated post will be scheduled for each selected platform.
              </small>

            </div>

            <div className="schedule-field">

              <label>
                Select Date & Time
              </label>

              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) =>
                  setScheduledAt(e.target.value)
                }
                min={new Date()
                  .toISOString()
                  .slice(0, 16)}
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
                onClick={handleSchedulePost}
                disabled={
                  !scheduledAt ||
                  isScheduling ||
                  !platforms.length
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