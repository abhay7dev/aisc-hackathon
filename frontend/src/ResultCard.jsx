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
  RECYCLE: "bg-green-900/85 border-green-400",
  TRASH: "bg-red-900/85 border-red-400",
  COMPOST: "bg-amber-900/85 border-amber-400",
  SPECIAL: "bg-purple-900/85 border-purple-400",
};

export function ResultOverlay({ item, action, reason, confidence, city, onDismiss }) {
  const style = OVERLAY_STYLES[action] || OVERLAY_STYLES.TRASH;

  return (
    <div
      className={`absolute bottom-0 left-0 right-0 z-20 border-t-2 rounded-t-3xl px-8 pt-6 pb-10 backdrop-blur-md text-white cursor-pointer ${style}`}
      onClick={onDismiss}
    >
      <div className="w-12 h-1.5 bg-white/30 rounded-full mx-auto mb-6" />
      <div className="flex items-baseline justify-between mb-4">
        <span className="text-6xl font-black tracking-tight">{ACTION_LABELS[action] || action}</span>
        <span className="text-base opacity-60 uppercase font-semibold">{confidence}</span>
      </div>
      {item && <div className="text-2xl font-semibold opacity-85 mb-3">{item}</div>}
      <div className="text-xl leading-relaxed">{reason}</div>
      <div className="text-base opacity-50 mt-5">{city} &middot; tap to dismiss</div>
    </div>
  );
}
