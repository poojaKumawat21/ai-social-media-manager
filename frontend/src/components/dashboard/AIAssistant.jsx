import React, { useEffect, useState } from "react";
import robotIdle from "../../assets/ai/robot-idle.png";

function AIAssistant() {
  const [isHovered, setIsHovered] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [robotAction, setRobotAction] = useState("idle");
  const actions = ["idle", "jump", "thinking", "wave", "move"];

  useEffect(() => {
    const actions = ["idle", "jump", "thinking", "wave", "move"];

    let index = 0;

    const interval = setInterval(() => {
      index = (index + 1) % actions.length;
      setRobotAction(actions[index]);
    }, 100); // Change action every 100 milliseconds

    return () => clearInterval(interval);
  }, []);

  // Send message
  const handleSendMessage = () => {
    if (!message.trim()) return;

    console.log("User message:", message);

    setMessage("");
  };

  return (
    <div
      className={`ai-assistant-card ${
        isHovered ? "assistant-hovered" : ""
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Background Glow */}
      <div className="assistant-glow"></div>

      {/* AI Chat Panel */}
      {isChatOpen && (
        <div className="ai-chat-panel">
          <div className="ai-chat-header">
            <div>
              <strong>Nova AI</strong>
              <span>Online • Ready to help</span>
            </div>

            <button
              className="ai-chat-close"
              onClick={() => setIsChatOpen(false)}
            >
              ×
            </button>
          </div>

          <div className="ai-chat-body">
            <div className="ai-message ai-message-bot">
              Hi! 👋 I'm Nova. How can I help you with your social media?
            </div>
          </div>

          <div className="ai-chat-input">
            <input
              type="text"
              placeholder="Ask Nova anything..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSendMessage();
                }
              }}
            />

            <button onClick={handleSendMessage}>→</button>
          </div>
        </div>
      )}

      {/* Assistant Header */}
      <div className="assistant-header">
        <div>
          <span className="assistant-label">YOUR AI MANAGER</span>

          <h2>
            Meet your AI Assistant
            <span className="assistant-sparkle">✦</span>
          </h2>

          <p>
            Your intelligent partner for creating, planning and managing social
            media content.
          </p>
        </div>

        <div className="assistant-status">
          <span></span>
          Online
        </div>
      </div>

      {/* Robot Area */}
      <div className="assistant-stage">
        {/* Floating Particles */}
        <span className="assistant-particle particle-one">✦</span>

        <span className="assistant-particle particle-two">✦</span>

        <span className="assistant-particle particle-three">•</span>

        {/* Nova Robot */}
        <div className={`robot-container robot-action-${robotAction}`}>
          <img
            src={robotIdle}
            alt="Nova AI Assistant"
            className="nova-robot-image"
          />
        </div>

        {/* Hover Message */}
        <div className="assistant-hover-message">
          <span>✦</span>
          AI is ready to help
        </div>
      </div>

      {/* Bottom Controls */}
      <div className="assistant-footer">
        <div className="assistant-info">
          <div className="assistant-avatar">AI</div>

          <div>
            <strong>Nova</strong>
            <span>Autonomous AI Assistant</span>
          </div>
        </div>

        {/* Talk To AI Button */}
        <button
          className="assistant-chat-button"
          onClick={() => setIsChatOpen(true)}
        >
          Talk to AI
          <span>→</span>
        </button>
      </div>
    </div>
  );
}

export default AIAssistant;