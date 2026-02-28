import "./navbar.css";

export default function Navbar({ connectionStatus = "disconnected" }) {
  return (
    <header className="navbar">
      <h2 className="navbar-title">Field Relay Neighboring Datapoints</h2>
      <div className="navbar-status">
        <span className={`navbar-dot ${connectionStatus}`} />
        <span className="navbar-status-text">
          {connectionStatus === "connected" && "Live"}
          {connectionStatus === "connecting" && "Connecting"}
          {connectionStatus === "disconnected" && "Offline"}
        </span>
      </div>
    </header>
  );
}
