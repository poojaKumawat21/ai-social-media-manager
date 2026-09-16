import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import CreatePost from "./pages/CreatePost";
import AIIdeas from "./pages/AIIdeas";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<MainLayout />}>

          {/* Dashboard */}
          <Route index element={<Dashboard />} />

          {/* Create Post */}
          <Route path="create-post" element={<CreatePost />} />
          <Route path="ai-ideas" element={<AIIdeas />} />

        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;