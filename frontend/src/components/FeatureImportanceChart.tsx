import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

function prettifyFeatureName(name: string): string {
  let s = name;
  s = s.replace(/^t1_/, "Team 1: ");
  s = s.replace(/^t2_/, "Team 2: ");
  s = s.replace(/form_/g, "form ");
  s = s.replace(/_win_rate/g, " win rate");
  s = s.replace(/_/g, " ");
  return s
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

interface FeatureImportanceChartProps {
  features: { feature: string; importance: number }[];
}

export function FeatureImportanceChart({ features }: FeatureImportanceChartProps) {
  const data = features
    .slice(0, 10)
    .map((f) => ({
      name: prettifyFeatureName(f.feature),
      importance: f.importance,
    }))
    .sort((a, b) => a.importance - b.importance);

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis
            dataKey="name"
            type="category"
            width={180}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value) => [
              typeof value === "number" ? value.toFixed(5) : value,
              "Importance",
            ]}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill="rgba(59, 130, 246, 0.6)" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
