import { useState, useEffect, useRef, useCallback } from "react";
import Navbar from "./Components/Navbar/navbar";
import UserList from "./Components/UserList/UserList";
import ChatPanel from "./Components/ChatPanel/ChatPanel";
import "./App.css";

const WS_URL = `ws://${window.location.hostname}:8080`;

function makeId() {
  return Date.now() + Math.random();
}

function timestamp() {
  return new Date().toLocaleTimeString();
}

export default function App() {
  const [wsStatus, setWsStatus] = useState("disconnected");
  // users: { [id]: { label, online, lastMessage } }
  const [users, setUsers] = useState({});
  // messages: { [userId]: Array<{ id, type, content, timestamp }> }
  const [messages, setMessages] = useState({});
  const [selectedUserId, setSelectedUserId] = useState(null);
  // unread counts for users not currently selected
  const [unreadCounts, setUnreadCounts] = useState({});

  const wsRef = useRef(null);
  const selectedUserIdRef = useRef(selectedUserId);
  // Tracks which users get LLM auto-replies (avoids stale-closure issues)
  const llmHandledRef = useRef(new Set());

  useEffect(() => {
    selectedUserIdRef.current = selectedUserId;
    // Clear unread for selected user
    if (selectedUserId) {
      setUnreadCounts((prev) => ({ ...prev, [selectedUserId]: 0 }));
    }
  }, [selectedUserId]);

  const addMessageForUser = useCallback((userId, msg) => {
    setMessages((prev) => ({
      ...prev,
      [userId]: [...(prev[userId] || []), msg],
    }));
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setWsStatus("connecting");

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setWsStatus("connected");
      // Identify as admin to the server
      ws.send(JSON.stringify({ type: "identify", role: "admin" }));
    };

    ws.onmessage = (event) => {
      let parsed;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        // Ignore non-JSON messages
        return;
      }

      const { type, id, ip, content, from } = parsed;

      if (type === "user_connected") {
        const userId = id || ip;
        const label = ip || id;
        if (parsed.llm_handled) llmHandledRef.current.add(userId);
        setUsers((prev) => ({
          ...prev,
          [userId]: {
            label,
            online: true,
            llmHandled: parsed.llm_handled ?? false,
            lastMessage: prev[userId]?.lastMessage || null,
          },
        }));
        setMessages((prev) => ({
          ...prev,
          [userId]: [
            ...(prev[userId] || []),
            {
              id: makeId(),
              type: "system",
              content: "User connected",
              timestamp: timestamp(),
            },
          ],
        }));
      } else if (type === "user_disconnected") {
        const userId = id || ip;
        llmHandledRef.current.delete(userId);
        setUsers((prev) =>
          prev[userId]
            ? { ...prev, [userId]: { ...prev[userId], online: false } }
            : prev,
        );
        setMessages((prev) => ({
          ...prev,
          [userId]: [
            ...(prev[userId] || []),
            {
              id: makeId(),
              type: "system",
              content: "User disconnected",
              timestamp: timestamp(),
            },
          ],
        }));
      } else if (type === "llm_status_changed") {
        const userId = parsed.id;
        const llmHandled = parsed.llm_handled;
        if (llmHandled) {
          llmHandledRef.current.add(userId);
        } else {
          llmHandledRef.current.delete(userId);
        }
        setUsers((prev) =>
          prev[userId]
            ? { ...prev, [userId]: { ...prev[userId], llmHandled } }
            : prev,
        );
      } else if (type === "message") {
        const userId = from;
        if (!userId) return;

        const newMsg = {
          id: makeId(),
          type: "received",
          content,
          timestamp: timestamp(),
        };

        setMessages((prev) => ({
          ...prev,
          [userId]: [...(prev[userId] || []), newMsg],
        }));

        setUsers((prev) =>
          prev[userId]
            ? { ...prev, [userId]: { ...prev[userId], lastMessage: content } }
            : {
                ...prev,
                [userId]: { label: userId, online: true, lastMessage: content },
              },
        );

        if (selectedUserIdRef.current !== userId) {
          setUnreadCounts((prev) => ({
            ...prev,
            [userId]: (prev[userId] || 0) + 1,
          }));
        }

        // Auto-reply via local LLM for overflow users
        if (llmHandledRef.current.has(userId)) {
          fetch("http://localhost:3001/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: content }),
          })
            .then((r) => r.json())
            .then(({ response }) => {
              if (ws.readyState !== WebSocket.OPEN) return;
              ws.send(JSON.stringify({ type: "message", to: userId, content: response }));
              setMessages((prev) => ({
                ...prev,
                [userId]: [
                  ...(prev[userId] || []),
                  {
                    id: makeId(),
                    type: "sent",
                    content: response,
                    timestamp: timestamp(),
                  },
                ],
              }));
            })
            .catch(() => {
              // LLM service unreachable — do nothing, admin can reply manually
            });
        }
      }
    };

    ws.onclose = () => {
      setWsStatus("disconnected");
    };

    ws.onerror = () => {
      setWsStatus("disconnected");
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, []);

  const handleSendMessage = useCallback((userId, text) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({ type: "message", to: userId, content: text }),
    );

    const newMsg = {
      id: makeId(),
      type: "sent",
      content: text,
      timestamp: timestamp(),
    };

    setMessages((prev) => ({
      ...prev,
      [userId]: [...(prev[userId] || []), newMsg],
    }));
  }, []);

  const handleSelectUser = (userId) => {
    setSelectedUserId(userId);
    setUnreadCounts((prev) => ({ ...prev, [userId]: 0 }));
  };

  const onlineCount = Object.values(users).filter((u) => u.online).length;

  return (
    <div className="app-container">
      <Navbar connectionStatus={wsStatus} userCount={onlineCount} />
      <main className="app-main">
        <UserList
          users={users}
          selectedUserId={selectedUserId}
          onSelectUser={handleSelectUser}
          unreadCounts={unreadCounts}
        />
        <ChatPanel
          selectedUserId={selectedUserId}
          selectedUser={selectedUserId ? users[selectedUserId] : null}
          messages={selectedUserId ? messages[selectedUserId] || [] : []}
          onSendMessage={handleSendMessage}
          wsStatus={wsStatus}
        />
      </main>
    </div>
  );
}
