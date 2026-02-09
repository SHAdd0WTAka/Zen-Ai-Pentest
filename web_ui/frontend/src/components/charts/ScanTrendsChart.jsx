import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { format, parseISO } from 'date-fns';

function ScanTrendsChart({ data }) {
  const formattedData = data?.map(item => ({
    ...item,
    date: format(parseISO(item.date), 'MMM dd'),
  })) || [];

  return (
    <div className="scan-trends-chart">
      <h3>Scan Trends (30 Days)</h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={formattedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="completed" 
              stroke="#22c55e" 
              name="Completed"
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="findings" 
              stroke="#ef4444" 
              name="Findings"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
        {formattedData.length === 0 && (
          <div className="no-data">No scan data available</div>
        )}
      </div>
    </div>
  );
}

export default ScanTrendsChart;
