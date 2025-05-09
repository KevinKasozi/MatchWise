import * as Tabs from "@radix-ui/react-tabs";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip,
  Legend,
);

// Mock data for charts
const modelPerformanceData = {
  labels: ["Accuracy", "Precision", "Recall", "F1"],
  datasets: [
    {
      label: "Model",
      data: [0.82, 0.79, 0.77, 0.78],
      backgroundColor: "#2563eb",
      borderRadius: 8,
    },
  ],
};

const teamTrendsData = {
  labels: ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5", "Match 6"],
  datasets: [
    {
      label: "xG (Arsenal)",
      data: [1.2, 2.1, 1.8, 2.5, 1.9, 2.2],
      borderColor: "#22c55e",
      backgroundColor: "rgba(34,197,94,0.2)",
      tension: 0.4,
      fill: true,
    },
    {
      label: "xG (Man City)",
      data: [1.5, 1.7, 2.0, 2.3, 2.1, 2.4],
      borderColor: "#2563eb",
      backgroundColor: "rgba(37,99,235,0.2)",
      tension: 0.4,
      fill: true,
    },
  ],
};

const featureImportanceData = {
  labels: [
    "Recent Form",
    "Goals Scored",
    "Win Rate",
    "Possession",
    "Shots on Target",
  ],
  datasets: [
    {
      label: "Importance",
      data: [0.32, 0.25, 0.18, 0.15, 0.1],
      backgroundColor: ["#2563eb", "#22c55e", "#f59e42", "#e11d48", "#a21caf"],
      borderWidth: 0,
    },
  ],
};

export default function Insights() {
  return (
    <div className="w-full px-4 md:px-8 py-8 max-w-screen-lg mx-auto grid gap-8">
      <h1 className="text-2xl font-bold text-primary mb-4">
        Insights & Analytics
      </h1>
      <Tabs.Root defaultValue="model" className="w-full">
        <Tabs.List className="flex gap-2 mb-4">
          <Tabs.Trigger
            value="model"
            className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition"
          >
            Model Performance
          </Tabs.Trigger>
          <Tabs.Trigger
            value="trends"
            className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition"
          >
            Team Trends
          </Tabs.Trigger>
          <Tabs.Trigger
            value="features"
            className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition"
          >
            Feature Importance
          </Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="model">
          <div className="bg-white/90 rounded-2xl shadow-lg p-8 border border-slate-100">
            <h2 className="text-lg font-bold mb-2">Model Performance</h2>
            <Bar
              data={modelPerformanceData}
              options={{
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { min: 0, max: 1, ticks: { stepSize: 0.2 } } },
              }}
            />
          </div>
        </Tabs.Content>
        <Tabs.Content value="trends">
          <div className="bg-white/90 rounded-2xl shadow-lg p-8 border border-slate-100">
            <h2 className="text-lg font-bold mb-2">Team Trends (xG)</h2>
            <Line
              data={teamTrendsData}
              options={{
                responsive: true,
                plugins: { legend: { position: "top" } },
                scales: { y: { min: 0, max: 3, ticks: { stepSize: 0.5 } } },
              }}
            />
          </div>
        </Tabs.Content>
        <Tabs.Content value="features">
          <div className="bg-white/90 rounded-2xl shadow-lg p-8 border border-slate-100">
            <h2 className="text-lg font-bold mb-2">Feature Importance</h2>
            <Doughnut
              data={featureImportanceData}
              options={{
                responsive: true,
                plugins: { legend: { position: "bottom" } },
              }}
            />
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
