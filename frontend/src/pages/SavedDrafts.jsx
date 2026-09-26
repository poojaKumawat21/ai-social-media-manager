import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../services/api";
import "./SavedDrafts.css";

function SavedDrafts() {
  const navigate = useNavigate();

  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [publishingId, setPublishingId] = useState(null);

  const loadDrafts = async () => {
    try {
      setLoading(true);

      const response = await api.get("/posts");

      const allPosts = response.posts || [];

      const savedDrafts = allPosts.filter(
        (post) => post.status === "draft"
      );

      setDrafts(savedDrafts);
    } catch (error) {
      console.error("Failed to load drafts:", error);

      alert(
        error.message || "Unable to load saved drafts."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, []);

  // ================= EDIT =================

  const handleEdit = (draft) => {
    localStorage.setItem(
      "postpilot_edit_draft",
      JSON.stringify(draft)
    );

    navigate("/create-post");
  };

  // ================= DELETE =================

  const handleDelete = async (draftId) => {
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
        error.message ||
          "Unable to delete draft."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ================= PUBLISH =================

  const handlePublish = async (draft) => {
    if (!draft?.id) {
      return;
    }

    const confirmed = window.confirm(
      "Publish this draft to LinkedIn?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setPublishingId(draft.id);

      const result = await api.post(
        `/posts/${draft.id}/publish/linkedin`
      );

      console.log(
        "Draft publish result:",
        result
      );

      setDrafts((currentDrafts) =>
        currentDrafts.filter(
          (item) => item.id !== draft.id
        )
      );

      alert(
        "Draft published to LinkedIn successfully."
      );
    } catch (error) {
      console.error(
        "Publish draft error:",
        error
      );

      alert(
        error.message ||
          "Unable to publish draft to LinkedIn."
      );
    } finally {
      setPublishingId(null);
    }
  };

  return (
    <div className="saved-drafts-page">

      {/* ================= HEADER ================= */}

      <div className="saved-drafts-header">

        <div>

          <span className="create-post-label">
            CONTENT LIBRARY
          </span>

          <h1>Saved Drafts</h1>

          <p>
            Continue working on your saved posts.
          </p>

        </div>

        <button
          className="create-new-draft-button"
          onClick={() =>
            navigate("/create-post")
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
              onClick={() =>
                navigate("/create-post")
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

                {/* IMAGE */}

                {draft.media_urls?.length > 0 ? (

                  <div className="draft-image">

                    <img
                      src={draft.media_urls[0]}
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

                {/* DETAILS */}

                <div className="draft-card-body">

                  <div className="draft-card-top">

                    <span className="draft-status">
                      DRAFT
                    </span>

                    <span className="draft-platform">
                      LinkedIn
                    </span>

                  </div>

                  <h3>
                    {draft.topic ||
                      "Untitled Draft"}
                  </h3>

                  <p>
                    {draft.caption ||
                      "No description added yet."}
                  </p>

                  {/* FOOTER */}

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
                        className="draft-edit-button"
                        onClick={() =>
                          handleEdit(draft)
                        }
                      >
                        Edit
                      </button>

                      {/* PUBLISH */}

                      <button
                        className="draft-publish-button"
                        onClick={() =>
                          handlePublish(draft)
                        }
                        disabled={
                          publishingId ===
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
                        className="draft-delete-button"
                        onClick={() =>
                          handleDelete(
                            draft.id
                          )
                        }
                        disabled={
                          deletingId ===
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