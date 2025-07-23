
import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Sector,
} from "recharts";
import type { AssetType, PortfolioSummary } from "../../types/assets";

// Material Icons
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import BarChartIcon from "@mui/icons-material/BarChart";
import PercentIcon from "@mui/icons-material/Percent";

interface PortfolioSummaryProps {
  summary: PortfolioSummary;
  onSectionChange?: (
    section: AssetType | "dashboard" | "scrapers" | "users"
  ) => void;
}

const PortfolioSummaryComponent: React.FC<PortfolioSummaryProps> = ({
  summary,
  onSectionChange,
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
      ([, breakdown]) =>
        breakdown && (breakdown.count > 0 || breakdown.value > 0)
    )
    .map(([type, breakdown]) => ({
      name: type.charAt(0).toUpperCase() + type.slice(1),
      value: breakdown.value,
      percentage: breakdown.percentage,
      count: breakdown.count,
    }));

  console.log("Portfolio Summary Data:", summary);

  // Custom active sector renderer
  const renderActiveShape = (props: any) => {
    const {
      cx,
      cy,
      midAngle,
      innerRadius,
      outerRadius,
      startAngle,
      endAngle,
      fill,
      payload,
      percent,
      value,
    } = props;
    const RADIAN = Math.PI / 180;
    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? "start" : "end";
    return (
      <g>
        <text
          x={cx}
          y={cy}
          dy={8}
          textAnchor="middle"
          fill={fill}
          fontWeight="bold"
        >
          {payload.name}
        </text>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
        />
        <Sector
          cx={cx}
          cy={cy}
          startAngle={startAngle}
          endAngle={endAngle}
          innerRadius={outerRadius + 6}
          outerRadius={outerRadius + 10}
          fill={fill}
          stroke="none"
        />
        <path
          d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`}
          stroke={fill}
          fill="none"
        />
        <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
        <text
          x={ex + (cos >= 0 ? 1 : -1) * 12}
          y={ey}
          dy={-8}
          textAnchor={textAnchor}
          fill="#f8f8f8"
        >{`Value €${value.toFixed(2)}`}</text>
        <text
          x={ex + (cos >= 0 ? 1 : -1) * 12}
          y={ey}
          dy={16}
          textAnchor={textAnchor}
          fill="#8e9297"
        >
          {`(${(percent * 100).toFixed(2)}%)`}
        </text>
      </g>
    );
  };

  // Get theme colors once for performance
  const themeColors = React.useMemo(() => {
    const getThemeColor = (variable: string) =>
      getComputedStyle(document.documentElement)
        .getPropertyValue(variable)
        .trim() || "#6B7280";
    return {
      Cards: getThemeColor("--color-gold"),
      Stocks: getThemeColor("--color-green"),
      Etfs: getThemeColor("--color-red"),
      Crypto: getThemeColor("--color-white"),
      Steam: getThemeColor("--color-blue"),
    };
  }, []);

  const getColorForAsset = (name: string) => {
    return themeColors[name as keyof typeof themeColors] || "#6B7280";
  };

  const handlePieClick = (index: number) => {
    if (!onSectionChange) return;
    const assetTypes = ["cards", "stocks", "etfs", "crypto", "steam"];
    const section = assetTypes[index];
    if (section) {
      onSectionChange(section as AssetType);
    }
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
                  <p className="text-xs font-bold text-muted">
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
                  <p className="text-xs font-bold text-muted">
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
                  <p className="text-xs font-bold text-muted">Profit/Loss</p>
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
                  <p className="text-xs font-bold text-muted">Return %</p>
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
          <div className="grid">
            <div>
              <h3 className="text-lg font-semibold text-primary mb-4">
                Asset Allocation
              </h3>
              {pieChartData.length > 0 ? (
                <div className="h-128 w-full bg-primary border border-primary rounded-lg focus:outline-0">
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                    className="focus:outline-0"
                  >
                    <PieChart>
                      <Pie
                        activeShape={renderActiveShape}
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        fill="#8884d8"
                        stroke="none"
                        dataKey="value"
                        onClick={handlePieClick}
                        className="focus:outline-0 cursor-pointer"
                      >
                        {pieChartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={getColorForAsset(entry.name)}
                            className="focus:outline-0 cursor-pointer"
                          />
                        ))}
                      </Pie>
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
            {/*
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
                          <div className="flex flex-col">
                            <span className="text-sm text-primary">
                              {asset.name}
                            </span>
                            <span className="text-xs text-muted capitalize">
                              {asset.asset_type}
                            </span>
                          </div>
                          <span className="text-sm text-green">
                            +{formatPercentage(asset.profit_loss_percentage)}
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
                          <div className="flex flex-col">
                            <span className="text-sm text-primary">
                              {asset.name}
                            </span>
                            <span className="text-xs text-muted capitalize">
                              {asset.asset_type}
                            </span>
                          </div>
                          <span className="text-sm text-red">
                            {formatPercentage(asset.profit_loss_percentage)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryComponent;
