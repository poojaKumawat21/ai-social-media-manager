import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

function MainLayout() {
  return (
    <div className="app-layout">

      {/* Left Sidebar */}
      <Sidebar />

      {/* Right Application Area */}
      <div className="main-area">

        {/* Top Navbar */}
        <Navbar />

        {/* Page Content */}
        <main className="main-content">
          <Outlet />
        </main>

      </div>

    </div>
  );
}

export default MainLayout;