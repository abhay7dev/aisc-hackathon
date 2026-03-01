const CITIES = [
  { value: "seattle", label: "Seattle" },
  { value: "nyc", label: "NYC" },
  { value: "la", label: "Los Angeles" },
  { value: "chicago", label: "Chicago" },
];

export default function CitySelector({ value, onChange }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-black/60 backdrop-blur-sm text-white border border-white/30 rounded-full px-3 py-1.5 text-sm focus:border-white/60 focus:outline-none appearance-none cursor-pointer"
    >
      {CITIES.map((c) => (
        <option key={c.value} value={c.value}>
          {c.label}
        </option>
      ))}
    </select>
  );
}
