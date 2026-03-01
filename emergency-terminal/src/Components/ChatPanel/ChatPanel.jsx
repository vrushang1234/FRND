import { useEffect, useRef, useState } from "react";
import "./ChatPanel.css";

export default function ChatPanel({ selectedUserId, selectedUser, messages, onSendMessage, wsStatus }) {
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Clear input when switching users
  useEffect(() => {
    setInputMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [selectedUserId]);

  const sendMessage = () => {
    const text = inputMessage.trim();
    if (!text || wsStatus !== "connected" || !selectedUserId) return;
    onSendMessage(selectedUserId, text);
    setInputMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInput = (e) => {
    setInputMessage(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 100) + "px";
    }
  };

  if (!selectedUserId) {
    return (
      <div className="chatpanel">
        <div className="chatpanel-placeholder">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
          </svg>
          <p>Select a user to begin</p>
        </div>
      </div>
    );
  }

  const canSend = wsStatus === "connected" && selectedUser?.online;

  return (
    <div className="chatpanel">
      {/* Header */}
      <div className="chatpanel-header">
        <div className="chatpanel-user-info">
          <span className={`chatpanel-status-dot ${selectedUser?.online ? "online" : "offline"}`} />
          <span className="chatpanel-username">{selectedUser?.label}</span>
          <span className="chatpanel-user-status">
            {selectedUser?.online ? "Online" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="chatpanel-messages">
        {messages.length === 0 && (
          <div className="chatpanel-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <p>No messages yet</p>
          </div>
        )}
        {messages.map((msg) =>
          msg.type === "system" ? (
            <div key={msg.id} className="chatpanel-system-msg">
              — {msg.content} —
            </div>
          ) : (
            <div key={msg.id} className={`chatpanel-message ${msg.type}`}>
              <div className="chatpanel-bubble">
                <span className="chatpanel-text">{msg.content}</span>
                <span className="chatpanel-time">{msg.timestamp}</span>
              </div>
            </div>
          )
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chatpanel-input-area">
        <textarea
          ref={textareaRef}
          className="chatpanel-input"
          value={inputMessage}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            !canSend
              ? selectedUser?.online
                ? "Not connected to server"
                : "User is offline"
              : "Type a message… (Enter to send)"
          }
          disabled={!canSend}
          rows={1}
        />
        <button
          className="chatpanel-send-btn"
          onClick={sendMessage}
          disabled={!canSend || !inputMessage.trim()}
          aria-label="Send"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
