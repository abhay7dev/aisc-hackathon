const ACTION_STYLES = {
  RECYCLE: "bg-green-100 border-green-500 text-green-800",
  TRASH: "bg-red-100 border-red-500 text-red-800",
  COMPOST: "bg-amber-100 border-amber-500 text-amber-800",
  SPECIAL: "bg-purple-100 border-purple-500 text-purple-800",
  NOT_DISPOSABLE: "bg-blue-100 border-blue-500 text-blue-800",
};

const ACTION_LABELS = {
  SPECIAL: "SPECIAL DISPOSAL",
  NOT_DISPOSABLE: "NOT DISPOSABLE",
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
