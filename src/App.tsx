import { useState, useEffect, useCallback } from "react";
import AssetTable from "./components/common/AssetTable";
import FinancialAssetTable from "./components/common/FinancialAssetTable";
import PortfolioSummary from "./components/portfolio/PortfolioSummary";
import UserManagement from "./components/admin/UserManagement";
import { SteamInventory } from "./components/SteamInventory";
import { api, type Asset, type AssetType, type Card } from "./api/client";
import type { PortfolioSummary as PortfolioSummaryType } from "./types/assets";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AuthButton } from "./components/Auth/AuthButton";

// Material Icons
import DashboardIcon from "@mui/icons-material/Dashboard";
import StyleIcon from "@mui/icons-material/Style";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import CurrencyBitcoinIcon from "@mui/icons-material/CurrencyBitcoin";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";

function App() {
  const [portfolioSummary, setPortfolioSummary] =
    useState<PortfolioSummaryType>({
      total_portfolio_value: 0,
      total_investment: 0,
      total_profit_loss: 0,
      total_profit_loss_percentage: 0,
      asset_breakdown: {
        cards: { value: 0, percentage: 0, count: 0 },
        stocks: { value: 0, percentage: 0, count: 0 },
        etfs: { value: 0, percentage: 0, count: 0 },
        crypto: { value: 0, percentage: 0, count: 0 },
        steam: { value: 0, percentage: 0, count: 0 },
      },
      top_performers: [],
      worst_performers: [],
    });

  const [assets, setAssets] = useState<{
    cards: Card[];
    stocks: Asset[];
    etfs: Asset[];
    crypto: Asset[];
    steam: Asset[];
  }>({
    cards: [],
    stocks: [],
    etfs: [],
    crypto: [],
    steam: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to load portfolio summary from backend
      try {
        const summary = await api.getPortfolioSummary();
        setPortfolioSummary(summary);
      } catch (apiError) {
        console.warn("Failed to get portfolio summary from backend:", apiError);
        // Initialize with empty summary if API fails
        setPortfolioSummary({
          total_portfolio_value: 0,
          total_investment: 0,
          total_profit_loss: 0,
          total_profit_loss_percentage: 0,
          asset_breakdown: {
            cards: { value: 0, percentage: 0, count: 0 },
            stocks: { value: 0, percentage: 0, count: 0 },
            etfs: { value: 0, percentage: 0, count: 0 },
            crypto: { value: 0, percentage: 0, count: 0 },
            steam: { value: 0, percentage: 0, count: 0 },
          },
          top_performers: [],
          worst_performers: [],
        });
      }

      // Load cards directly without using the callback to avoid dependency loop
      try {
        const cardsResponse = await api.getCards();
        setAssets((prev) => ({
          ...prev,
          cards: cardsResponse.items || [],
        }));
      } catch (cardsError) {
        console.warn("Failed to load cards:", cardsError);
        setAssets((prev) => ({
          ...prev,
          cards: [],
        }));
      }

      // Load steam inventory items
      try {
        const steamResponse = await api.getSteamItems(1, 1000);
        setAssets((prev) => ({
          ...prev,
          steam: steamResponse.items || [],
        }));
      } catch (steamError) {
        console.warn("Failed to load steam items:", steamError);
        setAssets((prev) => ({
          ...prev,
          steam: [],
        }));
      }

      // Load financial assets (stocks, ETFs, crypto)
      try {
        const [stocksResponse, etfsResponse, cryptoResponse] =
          await Promise.allSettled([
            api.getFinancialAssets("stocks"),
            api.getFinancialAssets("etfs"),
            api.getFinancialAssets("crypto"),
          ]);

        setAssets((prev) => ({
          ...prev,
          stocks:
            stocksResponse.status === "fulfilled"
              ? stocksResponse.value.items || []
              : [],
          etfs:
            etfsResponse.status === "fulfilled"
              ? etfsResponse.value.items || []
              : [],
          crypto:
            cryptoResponse.status === "fulfilled"
              ? cryptoResponse.value.items || []
              : [],
        }));
      } catch (financialError) {
        console.warn("Failed to load financial assets:", financialError);
        setAssets((prev) => ({
          ...prev,
          stocks: [],
          etfs: [],
          crypto: [],
        }));
      }
    } catch (error) {
      console.error("Failed to load portfolio data:", error);
      setError("Failed to load portfolio data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []); // Remove dependency to prevent infinite loop

  return (
    <AuthProvider onAuthChange={loadData}>
      <AppContent
        portfolioSummary={portfolioSummary}
        assets={assets}
        loading={loading}
        error={error}
        loadData={loadData}
        setError={setError}
      />
    </AuthProvider>
  );
}

function AppContent({
  portfolioSummary,
  assets,
  loading,
  error,
  loadData,
  setError,
}: {
  portfolioSummary: PortfolioSummaryType;
  assets: {
    cards: Card[];
    stocks: Asset[];
    etfs: Asset[];
    crypto: Asset[];
    steam: Asset[];
  };
  loading: boolean;
  error: string | null;
  loadData: () => Promise<void>;
  setError: (error: string | null) => void;
}) {
  const { isLoading } = useAuth();

  const [activeSection, setActiveSection] = useState<
    AssetType | "dashboard" | "scrapers" | "users"
  >("dashboard");

  // Load initial data only after authentication is ready
  useEffect(() => {
    if (!isLoading) {
      loadData();
    }
  }, [isLoading]); // Remove loadData dependency to prevent infinite loop

  // Show loading spinner while authentication is initializing OR while loading data
  if (isLoading || loading) {
    return (
      <div className="min-h-screen min-w-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse mx-auto mb-4" />
          <p className="text-muted">
            {isLoading ? "Initializing..." : "Loading data..."}
          </p>
        </div>
      </div>
    );
  }

  const handleSetBuyPrice = async (id: number, buyPrice: number) => {
    try {
      await api.updateCardBuyPrice(id, buyPrice);
      // Refresh data after updating buy price
      await loadData();
    } catch (error) {
      console.error("Failed to update buy price:", error);
      setError(
        error instanceof Error ? error.message : "Failed to update buy price"
      );
    }
  };

  const renderSectionContent = () => {
    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4">
                <button
                  onClick={loadData}
                  className="primary-btn btn-red text-sm"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    switch (activeSection) {
      case "dashboard":
        return (
          <PortfolioSummary
            summary={portfolioSummary}
            onSectionChange={setActiveSection}
          />
        );
      case "cards":
        return (
          <AssetTable
            assets={assets.cards}
            assetType="cards"
            onDataUpdate={loadData}
            onSetBuyPrice={handleSetBuyPrice}
          />
        );
      case "stocks":
        return (
          <FinancialAssetTable
            assets={assets.stocks}
            assetType="stocks"
            onDataUpdate={loadData}
          />
        );
      case "etfs":
        return (
          <FinancialAssetTable
            assets={assets.etfs}
            assetType="etfs"
            onDataUpdate={loadData}
          />
        );
      case "crypto":
        return (
          <FinancialAssetTable
            assets={assets.crypto}
            assetType="crypto"
            onDataUpdate={loadData}
          />
        );
      case "steam":
        return <SteamInventory />;
      case "users":
        return <UserManagement />;
      default:
        return <PortfolioSummary summary={portfolioSummary} />;
    }
  };

  return (
    <div className="min-h-screen min-w-screen bg-background">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-primary">
              Portfolio Manager
            </h1>
            <p className="text-muted mt-1">
              Track your investments across multiple asset classes
            </p>
          </div>
          <AuthButton onUserManagementClick={() => setActiveSection("users")} />
        </div>

        {/* Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-4">
            {[
              { key: "dashboard", label: "Dashboard", icon: DashboardIcon },
              { key: "cards", label: "Trading Cards", icon: StyleIcon },
              { key: "stocks", label: "Stocks", icon: TrendingUpIcon },
              { key: "etfs", label: "ETFs", icon: AccountBalanceIcon },
              { key: "crypto", label: "Crypto", icon: CurrencyBitcoinIcon },
              {
                key: "steam",
                label: "Steam Inventory",
                icon: SportsEsportsIcon,
              },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() =>
                  setActiveSection(
                    key as AssetType | "dashboard" | "scrapers" | "users"
                  )
                }
                className={`nav-primary ${
                  activeSection === key ? "active" : ""
                }`}
              >
                <Icon className="nav-icon" />
                {label}
                {/* Add notification badge for asset counts */}
                {["cards", "stocks", "etfs", "crypto", "steam"].includes(key) &&
                  assets[key as AssetType].length > 0 && (
                    <span className="nav-badge">
                      {assets[key as AssetType].length > 99
                        ? "99+"
                        : assets[key as AssetType].length}
                    </span>
                  )}
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="bg-card rounded-lg shadow-sm">
          <div>{renderSectionContent()}</div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-muted text-sm">
          <p>Portfolio Manager - by Julz & Gaggles</p>
          <p className="mt-1 flex items-center justify-center gap-1">
            Backend API:{" "}
            <span className="inline-flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              Connected
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
