import React, { useState } from "react";
import { apiClient } from "../api/client";

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
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          }
        />

        <StatsCard
          title="Total Value"
          value={formatCurrency(stats.total_value)}
          color="green"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
              />
            </svg>
          }
        />

        <StatsCard
          title="Average Price"
          value={formatCurrency(stats.average_price)}
          color="purple"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          }
        />

        <StatsCard
          title="Expansions"
          value={stats.expansions.length}
          color="yellow"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          }
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
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
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
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
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
