import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import CreatePost from "./pages/CreatePost";
import AIIdeas from "./pages/AIIdeas";
import ContentCalendar from "./pages/ContentCalendar";
import Analytics from "./pages/Analytics";
import NewsTrends from "./pages/NewsTrends";
import Settings from "./pages/settings/Settings";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ScheduledPosts from "./pages/ScheduledPosts";
import PublishedPosts from "./pages/PublishedPosts";
import ConnectedAccounts from "./pages/ConnectedAccounts";
import ProfileSetup from "./pages/ProfileSetup";


import "./App.css";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Protected App */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="create-post" element={<CreatePost />} />
          <Route path="ai-ideas" element={<AIIdeas />} />
          <Route path="content-calendar" element={<ContentCalendar />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="news-trends" element={<NewsTrends />} />
          <Route path="settings" element={<Settings />} />
          <Route path="scheduled-posts" element={<ScheduledPosts />} />
          <Route path="published-posts" element={<PublishedPosts />} />
          <Route path="connected-accounts" element={<ConnectedAccounts />} />
        </Route>

        {/* Public Auth / Onboarding Pages */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/profile-setup" element={<ProfileSetup />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
