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
      className="border border-blue-800 bg-gray-900 text-gray-100 rounded px-3 py-2 text-base focus:border-blue-500 focus:outline-none"
    >
      {CITIES.map((c) => (
        <option key={c.value} value={c.value}>
          {c.label}
        </option>
      ))}
    </select>
  );
}
