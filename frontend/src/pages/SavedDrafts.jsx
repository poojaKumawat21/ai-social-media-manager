import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../services/api";
import "./SavedDrafts.css";

const USER_ID_KEY = "user_id";

const getUserScopedKey = (baseKey, userId) => {
  if (!userId) {
    return null;
  }

  return `${baseKey}_${userId}`;
};

function SavedDrafts() {
  const navigate = useNavigate();

  const [currentUserId, setCurrentUserId] = useState(() =>
    localStorage.getItem(USER_ID_KEY)
  );

  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [publishingId, setPublishingId] = useState(null);

  // =========================================================
  // USER-SCOPED STORAGE
  // =========================================================

  const EDIT_DRAFT_KEY = getUserScopedKey(
    "postpilot_edit_draft",
    currentUserId
  );

  // =========================================================
  // AUTH / USER SYNC
  // =========================================================

  useEffect(() => {
    const syncCurrentUser = () => {
      setCurrentUserId(localStorage.getItem(USER_ID_KEY));
    };

    window.addEventListener("storage", syncCurrentUser);

    return () => {
      window.removeEventListener("storage", syncCurrentUser);
    };
  }, []);

  // =========================================================
  // LOAD DRAFTS
  // =========================================================

  const loadDrafts = async () => {
    try {
      setLoading(true);

      const response = await api.get("/posts");

      // Support both:
      // { posts: [...] }
      // and direct [...]
      const allPosts = Array.isArray(response)
        ? response
        : Array.isArray(response?.posts)
        ? response.posts
        : [];

      const savedDrafts = allPosts.filter(
        (post) => post?.status === "draft"
      );

      setDrafts(savedDrafts);
    } catch (error) {
      console.error("Failed to load drafts:", error);

      alert(
        error?.message ||
          "Unable to load saved drafts."
      );

      setDrafts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentUserId) {
      setDrafts([]);
      setLoading(false);
      return;
    }

    loadDrafts();
  }, [currentUserId]);

  // =========================================================
  // PLATFORM HELPERS
  // =========================================================

  const getPlatforms = (draft) => {
    if (!draft) {
      return [];
    }

    if (Array.isArray(draft.platforms)) {
      return draft.platforms
        .map((platform) =>
          String(platform).toLowerCase().trim()
        )
        .filter(Boolean);
    }

    if (draft.platform) {
      return [
        String(draft.platform)
          .toLowerCase()
          .trim(),
      ];
    }

    return [];
  };

  const getPlatformLabel = (platform) => {
    switch (String(platform).toLowerCase()) {
      case "instagram":
        return "Instagram";

      case "linkedin":
        return "LinkedIn";

      case "facebook":
        return "Facebook";

      case "x":
        return "X";

      default:
        return "Social Media";
    }
  };

  const getDraftPlatformLabel = (draft) => {
    const platforms = getPlatforms(draft);

    if (platforms.length === 0) {
      return "No platform";
    }

    if (platforms.length === 1) {
      return getPlatformLabel(platforms[0]);
    }

    return platforms
      .map((platform) =>
        getPlatformLabel(platform)
      )
      .join(" • ");
  };

  // =========================================================
  // EDIT
  // =========================================================

  const handleEdit = (draft) => {
    if (!draft?.id) {
      alert("Unable to edit this draft.");
      return;
    }

    if (!currentUserId || !EDIT_DRAFT_KEY) {
      alert(
        "Your session could not be identified. Please log in again."
      );
      return;
    }

    try {
      localStorage.setItem(
        EDIT_DRAFT_KEY,
        JSON.stringify(draft)
      );

      navigate("/create-post");
    } catch (error) {
      console.error(
        "Save edit draft error:",
        error
      );

      alert(
        "Unable to open this draft for editing."
      );
    }
  };

  // =========================================================
  // DELETE
  // =========================================================

  const handleDelete = async (draftId) => {
    if (!draftId) {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete this draft?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(draftId);

      await api.delete(`/posts/${draftId}`);

      setDrafts((currentDrafts) =>
        currentDrafts.filter(
          (draft) => draft.id !== draftId
        )
      );

      alert("Draft deleted successfully.");
    } catch (error) {
      console.error(
        "Delete draft error:",
        error
      );

      alert(
        error?.message ||
          "Unable to delete draft."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // =========================================================
  // PUBLISH ONE PLATFORM
  // =========================================================

  const publishToPlatform = async (
    draft,
    platform
  ) => {
    if (!draft?.id) {
      throw new Error(
        "Draft ID is missing."
      );
    }

    const normalizedPlatform = String(
      platform
    )
      .toLowerCase()
      .trim();

    // -------------------------
    // LINKEDIN
    // -------------------------

    if (
      normalizedPlatform === "linkedin"
    ) {
      return api.post(
        `/posts/${draft.id}/publish/linkedin`
      );
    }

    // -------------------------
    // INSTAGRAM
    // -------------------------

    if (
      normalizedPlatform === "instagram"
    ) {
      return api.post(
        `/posts/${draft.id}/publish/instagram`
      );
    }

    // -------------------------
    // X
    // -------------------------

    if (normalizedPlatform === "x") {
      const includeImage =
        Array.isArray(draft.media_urls) &&
        draft.media_urls.length > 0;

      return api.post(
        `/posts/${draft.id}/publish/x`,
        {
          include_image: includeImage,
        }
      );
    }

    throw new Error(
      `${getPlatformLabel(
        normalizedPlatform
      )} publishing is not available yet.`
    );
  };

  // =========================================================
  // PUBLISH
  // =========================================================

  const handlePublish = async (draft) => {
    if (!draft?.id) {
      return;
    }

    const platforms = getPlatforms(draft);

    if (platforms.length === 0) {
      alert(
        "No platform is selected for this draft."
      );
      return;
    }

    // Only platforms that currently have
    // backend publish endpoints.
    const publishablePlatforms =
      platforms.filter((platform) =>
        [
          "linkedin",
          "instagram",
          "x",
        ].includes(platform)
      );

    if (
      publishablePlatforms.length === 0
    ) {
      alert(
        "This draft does not have a supported publishing platform."
      );
      return;
    }

    let selectedPlatform =
      publishablePlatforms[0];

    // If the draft has multiple platforms,
    // let the user choose where to publish.
    if (publishablePlatforms.length > 1) {
      const platformText =
        publishablePlatforms
          .map(
            (platform, index) =>
              `${index + 1}. ${getPlatformLabel(
                platform
              )}`
          )
          .join("\n");

      const selection = window.prompt(
        `Which platform do you want to publish this draft to?\n\n${platformText}\n\nEnter the number:`,
        "1"
      );

      if (selection === null) {
        return;
      }

      const selectedIndex =
        Number(selection) - 1;

      if (
        !Number.isInteger(
          selectedIndex
        ) ||
        !publishablePlatforms[
          selectedIndex
        ]
      ) {
        alert(
          "Invalid platform selection."
        );
        return;
      }

      selectedPlatform =
        publishablePlatforms[
          selectedIndex
        ];
    }

    const platformLabel =
      getPlatformLabel(selectedPlatform);

    // X has a 280-character limit.
    if (selectedPlatform === "x") {
      const xVariant =
        draft?.platform_variants?.x ||
        {};

      const xText =
        xVariant.text ||
        draft.caption ||
        draft.content ||
        draft.text ||
        "";

      const hashtags = Array.isArray(
        xVariant.hashtags
      )
        ? xVariant.hashtags
        : [];

      const hashtagText =
        hashtags.length > 0
          ? ` ${hashtags.join(" ")}`
          : "";

      const finalXText =
        `${xText}${hashtagText}`.trim();

      if (finalXText.length > 280) {
        alert(
          `This X post is ${finalXText.length}/280 characters. Please edit the draft before publishing.`
        );
        return;
      }
    }

    const confirmed = window.confirm(
      `Publish this draft to ${platformLabel}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setPublishingId(draft.id);

      const result =
        await publishToPlatform(
          draft,
          selectedPlatform
        );

      console.log(
        "Draft publish result:",
        result
      );

      // Remove from saved drafts after successful publish.
      setDrafts((currentDrafts) =>
        currentDrafts.filter(
          (item) =>
            item.id !== draft.id
        )
      );

      alert(
        `Draft published to ${platformLabel} successfully.`
      );
    } catch (error) {
      console.error(
        "Publish draft error:",
        error
      );

      alert(
        error?.message ||
          `Unable to publish draft to ${platformLabel}.`
      );
    } finally {
      setPublishingId(null);
    }
  };

  // =========================================================
  // CREATE NEW POST
  // =========================================================

  const handleCreateNewPost = () => {
    if (EDIT_DRAFT_KEY) {
      localStorage.removeItem(
        EDIT_DRAFT_KEY
      );
    }

    navigate("/create-post");
  };

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="saved-drafts-page">

      {/* ================= HEADER ================= */}

      <div className="saved-drafts-header">

        <div>

          <span className="create-post-label">
            CONTENT LIBRARY
          </span>

          <h1>
            Saved Drafts
          </h1>

          <p>
            Continue working on your saved
            posts.
          </p>

        </div>

        <button
          className="create-new-draft-button"
          onClick={
            handleCreateNewPost
          }
        >
          + Create New Post
        </button>

      </div>

      {/* ================= CONTENT ================= */}

      <div className="saved-drafts-content">

        {loading ? (

          <div className="drafts-empty-state">

            <div className="drafts-empty-icon">
              ⏳
            </div>

            <h2>
              Loading drafts...
            </h2>

            <p>
              Fetching your saved drafts.
            </p>

          </div>

        ) : drafts.length === 0 ? (

          <div className="drafts-empty-state">

            <div className="drafts-empty-icon">
              ▤
            </div>

            <h2>
              No saved drafts
            </h2>

            <p>
              Posts that you save as drafts
              will appear here.
            </p>

            <button
              onClick={
                handleCreateNewPost
              }
            >
              Create Your First Post
            </button>

          </div>

        ) : (

          <div className="drafts-grid">

            {drafts.map((draft) => (

              <div
                className="draft-card"
                key={draft.id}
              >

                {/* ================= IMAGE ================= */}

                {draft.media_urls?.length >
                0 ? (

                  <div className="draft-image">

                    <img
                      src={
                        draft.media_urls[0]
                      }
                      alt={
                        draft.topic ||
                        "Draft"
                      }
                    />

                  </div>

                ) : (

                  <div className="draft-image draft-image-placeholder">

                    <span>
                      ✦
                    </span>

                  </div>

                )}

                {/* ================= DETAILS ================= */}

                <div className="draft-card-body">

                  <div className="draft-card-top">

                    <span className="draft-status">
                      DRAFT
                    </span>

                    <span className="draft-platform">
                      {getDraftPlatformLabel(
                        draft
                      )}
                    </span>

                  </div>

                  <h3>
                    {draft.topic ||
                      "Untitled Draft"}
                  </h3>

                  <p>
                    {draft.caption ||
                      draft.content ||
                      draft.text ||
                      "No description added yet."}
                  </p>

                  {/* ================= FOOTER ================= */}

                  <div className="draft-card-footer">

                    <small>
                      {draft.created_at
                        ? new Date(
                            draft.created_at
                          ).toLocaleDateString()
                        : ""}
                    </small>

                    <div className="draft-actions">

                      {/* EDIT */}

                      <button
                        type="button"
                        className="draft-edit-button"
                        onClick={() =>
                          handleEdit(
                            draft
                          )
                        }
                        disabled={
                          deletingId ===
                            draft.id ||
                          publishingId ===
                            draft.id
                        }
                      >
                        Edit
                      </button>

                      {/* PUBLISH */}

                      <button
                        type="button"
                        className="draft-publish-button"
                        onClick={() =>
                          handlePublish(
                            draft
                          )
                        }
                        disabled={
                          publishingId ===
                            draft.id ||
                          deletingId ===
                            draft.id
                        }
                      >
                        {publishingId ===
                        draft.id
                          ? "Publishing..."
                          : "Publish"}
                      </button>

                      {/* DELETE */}

                      <button
                        type="button"
                        className="draft-delete-button"
                        onClick={() =>
                          handleDelete(
                            draft.id
                          )
                        }
                        disabled={
                          deletingId ===
                            draft.id ||
                          publishingId ===
                            draft.id
                        }
                      >
                        {deletingId ===
                        draft.id
                          ? "Deleting..."
                          : "Delete"}
                      </button>

                    </div>

                  </div>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>

    </div>
  );
}

export default SavedDrafts;