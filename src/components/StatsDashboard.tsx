import React, { useState } from "react";
import { apiClient } from "../api/client";

// Material Icons
import StyleIcon from "@mui/icons-material/Style";
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import BarChartIcon from "@mui/icons-material/BarChart";
import CategoryIcon from "@mui/icons-material/Category";
import DeleteIcon from "@mui/icons-material/Delete";
import CircularProgress from "@mui/material/CircularProgress";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color = "blue",
}) => {
  const colorClasses =
    {
      blue: "stats-icon-blue",
      green: "stats-icon-green",
      purple: "stats-icon-gold", // Using gold instead of purple
      yellow: "stats-icon-red", // Using red for variety
    }[color] || "stats-icon-blue";

  return (
    <div className="stats-card">
      <div className="flex items-center">
        <div className={`${colorClasses} rounded-md p-3 text-primary`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-secondary">{title}</p>
          <p className="text-2xl font-semibold text-primary">{value}</p>
        </div>
      </div>
    </div>
  );
};

interface Stats {
  total_cards: number;
  total_value: number;
  average_price: number;
  expansions: string[];
  rarities: string[];
}

interface StatsDashboardProps {
  stats: Stats;
  onRefresh: () => void;
}

const StatsDashboard: React.FC<StatsDashboardProps> = ({
  stats,
  onRefresh,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const formatCurrency = (value: number) => `€${value.toFixed(2)}`;

  const handleDeleteAll = async () => {
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setIsDeleting(true);
    try {
      await apiClient.deleteAllCards();
      onRefresh(); // Refresh the data after deletion
      setShowConfirm(false);
    } catch (error) {
      console.error("Error deleting all cards:", error);
      alert("Failed to delete all cards. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setShowConfirm(false);
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatsCard
          title="Total Cards"
          value={stats.total_cards}
          color="blue"
          icon={<StyleIcon className="w-6 h-6" />}
        />

        <StatsCard
          title="Total Value"
          value={formatCurrency(stats.total_value)}
          color="green"
          icon={<AttachMoneyIcon className="w-6 h-6" />}
        />

        <StatsCard
          title="Average Price"
          value={formatCurrency(stats.average_price)}
          color="purple"
          icon={<BarChartIcon className="w-6 h-6" />}
        />

        <StatsCard
          title="Expansions"
          value={stats.expansions.length}
          color="yellow"
          icon={<CategoryIcon className="w-6 h-6" />}
        />
      </div>

      {/* Delete All Button */}
      {stats.total_cards > 0 && (
        <div className="flex justify-end">
          <div className="flex items-center space-x-3">
            {showConfirm ? (
              <>
                <span className="text-secondary text-sm">
                  Are you sure? This will delete all {stats.total_cards} cards.
                </span>
                <button
                  onClick={cancelDelete}
                  className="btn-secondary px-4 py-2 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAll}
                  disabled={isDeleting}
                  className="btn-danger px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isDeleting ? (
                    <>
                      <CircularProgress size={16} color="inherit" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <span>Confirm Delete All</span>
                  )}
                </button>
              </>
            ) : (
              <button
                onClick={handleDeleteAll}
                className="btn-danger px-4 py-2 rounded-lg flex items-center space-x-2"
              >
                <DeleteIcon className="w-4 h-4" />
                <span>Delete All Cards</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsDashboard;
