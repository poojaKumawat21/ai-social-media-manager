import React, { useState } from "react";
import "./AIIdeas.css";


function AIIdeas() {
    const [topic, setTopic] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [ideas, setIdeas] = useState([]);

    const handleGenerateIdeas = () => {
        if (!topic.trim()) {
            alert("Please enter a topic or niche.");
            return;
        }

        setIsGenerating(true);

        // Backend integration will be connected later.
        setTimeout(() => {
            setIdeas([
                {
                    title: "AI-Powered Content Creation",
                    description:
                        "Explore how AI is changing the way creators plan, write and publish social media content.",
                    tags: ["Educational", "AI"],
                },
                {
                    title: "Future of Social Media",
                    description:
                        "Create a thought-provoking post about upcoming trends and the future of digital content.",
                    tags: ["Trending", "Engagement"],
                },
                {
                    title: "Common Creator Mistakes",
                    description:
                        "Share practical mistakes creators make and how they can improve their social media strategy.",
                    tags: ["Tips", "Practical"],
                },
            ]);

            setIsGenerating(false);
        }, 800);
    };
    // Backend integration will be connected later.
    setTimeout(() => {
        setIsGenerating(false);
        alert("AI Ideas generation will be connected with backend.");
    }, 800);
};

return (
    <div className="ai-ideas-page">
        <div className="page-header">
            <div>
                <h1>AI Content Ideas</h1>
                <p>Let AI discover fresh content ideas for your social media.</p>
            </div>

            <button
                className="primary-btn"
                onClick={handleGenerateIdeas}
                disabled={isGenerating}
            >
                {isGenerating ? "✦ Generating..." : "✦ Generate Ideas"}
            </button>
        </div>

        <div className="ai-ideas-card">
            <h3>AI Idea Generator</h3>

            <p>Tell AI what kind of content you want ideas for.</p>

            <div className="idea-input-group">
                <label>Topic or niche</label>

                <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. AI, technology, fitness, business..."
                />

                <small>
                    AI will analyze your topic and suggest relevant content ideas.
                </small>
            </div>

            <div className="ai-ideas-results">
                <div className="results-header">
                    <div>
                        <span>AI GENERATED</span>
                        <h3>Content Ideas</h3>
                    </div>

                    <small>AI recommendations</small>
                </div>

                {ideas.length > 0 && (
                    <div className="idea-results-grid">
                        {ideas.map((idea, index) => (
                            <div className="idea-result-card" key={index}>
                                <span className="idea-number">
                                    {String(index + 1).padStart(2, "0")}
                                </span>

                                <h4>{idea.title}</h4>

                                <p>{idea.description}</p>

                                <div className="idea-tags">
                                    {idea.tags.map((tag, tagIndex) => (
                                        <span key={tagIndex}>{tag}</span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                <div className="idea-result-card">
                    <span className="idea-number">02</span>

                    <h4>Future of Social Media</h4>

                    <p>
                        Create a thought-provoking post about upcoming trends and the
                        future of digital content.
                    </p>

                    <div className="idea-tags">
                        <span>Trending</span>
                        <span>Engagement</span>
                    </div>
                </div>

                <div className="idea-result-card">
                    <span className="idea-number">03</span>

                    <h4>Common Creator Mistakes</h4>

                    <p>
                        Share practical mistakes creators make and how they can improve
                        their social media strategy.
                    </p>

                    <div className="idea-tags">
                        <span>Tips</span>
                        <span>Practical</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
  );


export default AIIdeas;
