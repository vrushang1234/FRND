import "./navbar.css";

export default function Navbar({ connectionStatus = "disconnected", userCount = 0 }) {
  return (
    <header className="navbar">
      <h2 className="navbar-title">Emergency Terminal</h2>
      <div className="navbar-status">
        <span className={`navbar-dot ${connectionStatus}`} />
        <span className="navbar-status-text">
          {connectionStatus === "connected" && `Live · ${userCount} user${userCount !== 1 ? "s" : ""}`}
          {connectionStatus === "connecting" && "Connecting"}
          {connectionStatus === "disconnected" && "Offline"}
        </span>
      </div>
    </header>
  );
}
