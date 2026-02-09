import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
};

function SeverityChart({ data }) {
  const chartData = data || [
    { name: 'Critical', value: 0, color: COLORS.critical },
    { name: 'High', value: 0, color: COLORS.high },
    { name: 'Medium', value: 0, color: COLORS.medium },
    { name: 'Low', value: 0, color: COLORS.low },
    { name: 'Info', value: 0, color: COLORS.info },
  ];

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="severity-chart">
      <h3>Findings by Severity</h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        {total === 0 && (
          <div className="no-data">No findings yet</div>
        )}
      </div>
      <div className="severity-stats">
        {chartData.map((item) => (
          <div key={item.name} className="stat-item">
            <span className="stat-color" style={{ backgroundColor: item.color }} />
            <span className="stat-name">{item.name}</span>
            <span className="stat-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SeverityChart;
