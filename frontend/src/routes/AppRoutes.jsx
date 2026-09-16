import React from "react";
import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/Dashboard";
import CreatePost from "../pages/CreatePost";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/create-post" element={<CreatePost />} />
    </Routes>
  );
}

export default AppRoutes;