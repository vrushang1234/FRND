import { useState } from "react";
import Navbar from "./Components/Navbar/navbar";
import ChatBox from "./Components/ChatBox/ChatBox";
import "./App.css";

export default function App() {
  const [connectionStatus, setConnectionStatus] = useState("disconnected");

  return (
    <div className="app-container">
      <Navbar connectionStatus={connectionStatus} />
      <main className="app-main">
        <ChatBox onStatusChange={setConnectionStatus} />
      </main>
    </div>
  );
}
