const ACTION_STYLES = {
  RECYCLE: "bg-green-900/50 border-green-500 text-green-300",
  TRASH: "bg-red-900/50 border-red-500 text-red-300",
  COMPOST: "bg-amber-900/50 border-amber-500 text-amber-300",
  SPECIAL: "bg-purple-900/50 border-purple-500 text-purple-300",
};

const ACTION_LABELS = {
  SPECIAL: "SPECIAL DISPOSAL",
};

export default function ResultCard({ item, action, reason, confidence, city }) {
  const style = ACTION_STYLES[action] || ACTION_STYLES.TRASH;

  return (
    <div className={`border-2 rounded-lg p-4 mt-4 ${style}`}>
      <div className="text-2xl font-bold mb-2">{ACTION_LABELS[action] || action}</div>
      <div className="mb-1">{reason}</div>
      <div className="text-sm opacity-75">
        Confidence: {confidence} &middot; City: {city}
      </div>
    </div>
  );
}

const OVERLAY_STYLES = {
  RECYCLE: "bg-green-900/80 border-green-400",
  TRASH: "bg-red-900/80 border-red-400",
  COMPOST: "bg-amber-900/80 border-amber-400",
  SPECIAL: "bg-purple-900/80 border-purple-400",
};

export function ResultOverlay({ item, action, reason, confidence, city, onDismiss }) {
  const style = OVERLAY_STYLES[action] || OVERLAY_STYLES.TRASH;

  return (
    <div
      className={`absolute bottom-6 left-4 right-4 z-20 border-2 rounded-xl p-4 backdrop-blur-sm text-white cursor-pointer ${style}`}
      onClick={onDismiss}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xl font-bold">{ACTION_LABELS[action] || action}</span>
        <span className="text-xs opacity-60 uppercase">{confidence} confidence</span>
      </div>
      {item && <div className="text-sm font-medium opacity-80 mb-1">{item}</div>}
      <div className="text-sm">{reason}</div>
      <div className="text-xs opacity-50 mt-2">{city} &middot; tap to dismiss</div>
    </div>
  );
}
