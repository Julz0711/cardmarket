import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import type { PortfolioSummary } from "../../types/assets";

// Material Icons
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import BarChartIcon from "@mui/icons-material/BarChart";
import PercentIcon from "@mui/icons-material/Percent";

interface PortfolioSummaryProps {
  summary: PortfolioSummary;
}

const PortfolioSummaryComponent: React.FC<PortfolioSummaryProps> = ({
  summary,
}) => {
  const formatCurrency = (value: number) => `€${value.toFixed(2)}`;
  const formatPercentage = (value: number) => `${value.toFixed(2)}%`;

  const getProfitLossColor = (value: number) => {
    if (value > 0) return "text-green";
    if (value < 0) return "text-red";
    return "text-primary";
  };

  // Prepare data for pie chart
  const pieChartData = Object.entries(summary.asset_breakdown || {})
    .filter(
      ([, breakdown]) => breakdown && breakdown.count > 0 && breakdown.value > 0
    )
    .map(([type, breakdown]) => ({
      name: type.charAt(0).toUpperCase() + type.slice(1),
      value: breakdown.value,
      percentage: breakdown.percentage,
      count: breakdown.count,
    }));

  // Color scheme for different asset types
  const COLORS = {
    Cards: "#3B82F6", // Blue
    Stocks: "#10B981", // Green
    Etfs: "#8B5CF6", // Purple
    Crypto: "#F59E0B", // Amber
    Steam: "#EF4444", // Red
  };

  const getColorForAsset = (name: string) => {
    return COLORS[name as keyof typeof COLORS] || "#6B7280";
  };

  return (
    <div className="mb-8">
      <div className="card">
        <div className="card-header">
          <h2 className="text-2xl font-bold text-primary">Portfolio Summary</h2>
        </div>

        <div className="card-body">
          {/* Main Portfolio Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="stats-card">
              <div className="flex items-center">
                <div className="stats-icon-blue rounded-md p-3">
                  <AttachMoneyIcon className="w-6 h-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-secondary">
                    Portfolio Value
                  </p>
                  <p className="text-2xl font-semibold text-primary">
                    {formatCurrency(summary.total_portfolio_value)}
                  </p>
                </div>
              </div>
            </div>

            <div className="stats-card">
              <div className="flex items-center">
                <div className="stats-icon-gold rounded-md p-3">
                  <TrendingUpIcon className="w-6 h-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-secondary">
                    Total Investment
                  </p>
                  <p className="text-2xl font-semibold text-primary">
                    {formatCurrency(summary.total_investment)}
                  </p>
                </div>
              </div>
            </div>

            <div className="stats-card">
              <div className="flex items-center">
                <div
                  className={`${
                    summary.total_profit_loss >= 0
                      ? "stats-icon-green"
                      : "stats-icon-red"
                  } rounded-md p-3`}
                >
                  <BarChartIcon className="w-6 h-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-secondary">
                    Profit/Loss
                  </p>
                  <p
                    className={`text-2xl font-semibold ${getProfitLossColor(
                      summary.total_profit_loss
                    )}`}
                  >
                    {formatCurrency(summary.total_profit_loss)}
                  </p>
                </div>
              </div>
            </div>

            <div className="stats-card">
              <div className="flex items-center">
                <div
                  className={`${
                    summary.total_profit_loss_percentage >= 0
                      ? "stats-icon-green"
                      : "stats-icon-red"
                  } rounded-md p-3`}
                >
                  <PercentIcon className="w-6 h-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-secondary">Return %</p>
                  <p
                    className={`text-2xl font-semibold ${getProfitLossColor(
                      summary.total_profit_loss_percentage
                    )}`}
                  >
                    {formatPercentage(summary.total_profit_loss_percentage)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Asset Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-primary mb-4">
                Asset Allocation
              </h3>
              {pieChartData.length > 0 ? (
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percentage }) =>
                          `${name} ${percentage.toFixed(1)}%`
                        }
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pieChartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={getColorForAsset(entry.name)}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => [
                          formatCurrency(value),
                          "Value",
                        ]}
                        labelFormatter={(label) => `${label}`}
                      />
                      <Legend
                        verticalAlign="bottom"
                        height={36}
                        formatter={(value) => {
                          const dataEntry = pieChartData.find(
                            (item) => item.name === value
                          );
                          return `${value}: ${dataEntry?.count || 0} item${
                            dataEntry?.count !== 1 ? "s" : ""
                          }`;
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-80 w-full flex items-center justify-center text-center">
                  <div>
                    <p className="text-secondary text-lg mb-2">
                      No Assets Found
                    </p>
                    <p className="text-muted">
                      Start by adding some cards or other assets to see your
                      allocation.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div>
              <h3 className="text-lg font-semibold text-primary mb-4">
                Performance
              </h3>
              <div className="space-y-4">
                {summary.top_performers.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-secondary mb-2">
                      Top Performers
                    </h4>
                    <div className="space-y-2">
                      {summary.top_performers.slice(0, 3).map((asset) => (
                        <div
                          key={asset.id}
                          className="flex items-center justify-between p-2 bg-tertiary rounded"
                        >
                          <span className="text-sm text-primary">
                            {asset.name}
                          </span>
                          <span className="text-sm text-green">
                            +
                            {formatPercentage(
                              ((asset.current_price - asset.price_bought) /
                                asset.price_bought) *
                                100
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {summary.worst_performers.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-secondary mb-2">
                      Underperformers
                    </h4>
                    <div className="space-y-2">
                      {summary.worst_performers.slice(0, 3).map((asset) => (
                        <div
                          key={asset.id}
                          className="flex items-center justify-between p-2 bg-tertiary rounded"
                        >
                          <span className="text-sm text-primary">
                            {asset.name}
                          </span>
                          <span className="text-sm text-red">
                            {formatPercentage(
                              ((asset.current_price - asset.price_bought) /
                                asset.price_bought) *
                                100
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryComponent;
