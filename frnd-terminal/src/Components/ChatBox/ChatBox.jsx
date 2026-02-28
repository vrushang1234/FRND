import { useState, useEffect, useRef, useCallback } from "react";
import "./ChatBox.css";

const WS_URL = "ws://localhost:8080";

export default function ChatBox({ onStatusChange }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [status, setStatus] = useState("disconnected");
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const updateStatus = (s) => {
    setStatus(s);
    onStatusChange?.(s);
  };

  const addSystemMessage = (content) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), type: "system", content, timestamp: new Date().toLocaleTimeString() },
    ]);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    updateStatus("connecting");

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      updateStatus("connected");
      addSystemMessage("Connected");
    };

    ws.onmessage = (event) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + Math.random(),
          type: "received",
          content: event.data,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    };

    ws.onclose = () => {
      updateStatus("disconnected");
      addSystemMessage("Disconnected from server");
    };

    ws.onerror = () => {
      updateStatus("disconnected");
      addSystemMessage("Connection error");
    };

    wsRef.current = ws;
  }, []);

  const disconnect = () => {
    wsRef.current?.close();
    wsRef.current = null;
  };

  const sendMessage = () => {
    const text = inputMessage.trim();
    if (!text || wsRef.current?.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(text);
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        type: "sent",
        content: text,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
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

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div className="chatbox">
      {/* Status bar */}
      <div className="chatbox-status-bar">
        <div className="chatbox-status-dot-wrap">
          <span className={`chatbox-status-dot ${status}`} />
          <span className="chatbox-status-label">
            {status === "connected" && "Connected"}
            {status === "connecting" && "Connecting…"}
            {status === "disconnected" && "Disconnected"}
          </span>
        </div>
        {status === "disconnected" && (
          <button className="chatbox-reconnect-btn" onClick={connect}>
            Reconnect
          </button>
        )}
        {status === "connected" && (
          <button className="chatbox-disconnect-btn" onClick={disconnect}>
            Disconnect
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="chatbox-messages">
        {messages.length === 0 && (
          <div className="chatbox-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <p>Waiting for connection…</p>
          </div>
        )}
        {messages.map((msg) =>
          msg.type === "system" ? (
            <div key={msg.id} className="chatbox-system-msg">
              — {msg.content} —
            </div>
          ) : (
            <div key={msg.id} className={`chatbox-message ${msg.type}`}>
              <div className="chatbox-bubble">
                <span className="chatbox-text">{msg.content}</span>
                <span className="chatbox-time">{msg.timestamp}</span>
              </div>
            </div>
          )
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chatbox-input-area">
        <textarea
          ref={textareaRef}
          className="chatbox-input"
          value={inputMessage}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={status === "connected" ? "Type a message… (Enter to send)" : "Not connected"}
          disabled={status !== "connected"}
          rows={1}
        />
        <button
          className="chatbox-send-btn"
          onClick={sendMessage}
          disabled={status !== "connected" || !inputMessage.trim()}
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
