import { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hello! 👋 I'm your customer service assistant. How can I help you today?",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const text = input.trim();

    if (!text || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
  session_id: "frontend-session",
  message: text,
}),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.response,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "Sorry, I couldn't connect to the server.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  const setQuickMessage = (message) => {
    setInput(message);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">AI</div>

          <div>
            <h1>Customer Support</h1>

            <span>
              <span className="status-dot"></span>
              Online
            </span>
          </div>
        </div>
      </header>

      {/* Main Chat */}
      <main className="chat-container">
        {/* Welcome */}
        <div className="welcome">
          <div className="bot-avatar">AI</div>

          <h2>How can we help?</h2>

          <p>
            Ask about your order, products, payments, delivery, or any other
            support issue.
          </p>
        </div>

        {/* Messages */}
        <div className="messages">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message-row ${
                message.role === "user" ? "user-row" : "bot-row"
              }`}
            >
              {message.role === "bot" && (
                <div className="small-avatar">AI</div>
              )}

              <div
                className={`message ${
                  message.role === "user"
                    ? "user-message"
                    : "bot-message"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}

          {/* Loading */}
          {loading && (
            <div className="message-row bot-row">
              <div className="small-avatar">AI</div>

              <div className="message bot-message">Checking...</div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <button
            onClick={() => setQuickMessage("Where is my order?")}
          >
            📦 Track my order
          </button>

          <button
            onClick={() =>
              setQuickMessage("I have a payment problem")
            }
          >
            💳 Payment issue
          </button>

          <button
            onClick={() =>
              setQuickMessage("I want to return a product")
            }
          >
            🔄 Return a product
          </button>
        </div>

        {/* Input */}
        <div className="input-area">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          <button
            className="send-button"
            onClick={sendMessage}
            disabled={loading}
          >
            {loading ? "..." : "Send"}
          </button>
        </div>

        {/* Disclaimer */}
        <p className="disclaimer">
          AI assistant • Please don't share passwords or payment details.
        </p>
      </main>
    </div>
  );
}

export default App;