import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ACTION_COLORS = {
  RECYCLE: "text-blue-400",
  TRASH: "text-red-400",
  COMPOST: "text-green-400",
  SPECIAL: "text-purple-400",
};

export default function History({ refreshKey }) {
  const [scans, setScans] = useState([]);

  useEffect(() => {
    axios
      .get(`${API_URL}/history`)
      .then((res) => setScans(res.data.scans))
      .catch(() => {});
  }, [refreshKey]);

  if (scans.length === 0) return null;

  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold mb-3 text-blue-400">Recent Scans</h2>
      <ul className="space-y-2">
        {scans.map((s, i) => (
          <li key={i} className="border border-blue-900/50 bg-gray-900 rounded p-2 flex items-center gap-3">
            <span className={`font-bold ${ACTION_COLORS[s.action] || ""}`}>
              {s.action}
            </span>
            <span className="text-sm truncate flex-1 text-gray-300">{s.reason}</span>
            <span className="text-gray-500 text-sm">{s.city}</span>
            <span className="text-gray-500 text-sm ml-auto">
              {new Date(s.timestamp).toLocaleTimeString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
