import React from "react";
import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/Dashboard";
import CreatePost from "../pages/CreatePost";
import SavedDrafts from "../pages/SavedDrafts";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />

      <Route path="/create-post" element={<CreatePost />} />

      {/* Saved Drafts */}
      <Route
        path="/saved-drafts"
        element={<SavedDrafts />}
      />
    </Routes>
  );
}

export default AppRoutes;