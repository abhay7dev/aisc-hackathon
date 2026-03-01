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
