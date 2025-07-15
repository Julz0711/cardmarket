import { useState, useEffect } from "react";
import AssetTable from "./components/common/AssetTable";
import PortfolioSummary from "./components/portfolio/PortfolioSummary";
import { CardsScraper } from "./components/scrapers/CardsScraper";
import { StocksScraper } from "./components/scrapers/StocksScraper";
import { CryptoScraper } from "./components/scrapers/CryptoScraper";
import { ETFScraper } from "./components/scrapers/ETFScraper";
import { SteamScraper } from "./components/scrapers/SteamScraper";
import { api, type Asset, type AssetType, type Card } from "./api/client";
import type { PortfolioSummary as PortfolioSummaryType } from "./types/assets";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AuthButton } from "./components/Auth/AuthButton";

// Material Icons
import DashboardIcon from "@mui/icons-material/Dashboard";
import DataObjectIcon from "@mui/icons-material/DataObject";
import StyleIcon from "@mui/icons-material/Style";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import CurrencyBitcoinIcon from "@mui/icons-material/CurrencyBitcoin";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import BusinessCenterIcon from "@mui/icons-material/BusinessCenter";

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

function AppContent() {
  const { isLoading } = useAuth();
  
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
  const [activeSection, setActiveSection] = useState<
    AssetType | "dashboard" | "scrapers"
  >("dashboard");
  const [activeScraperTab, setActiveScraperTab] = useState<AssetType>("cards");

  // Load initial data only after authentication is ready
  useEffect(() => {
    if (!isLoading) {
      loadData();
    }
  }, [isLoading]);

  // Show loading spinner while authentication is initializing
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse mx-auto mb-4" />
          <p className="text-muted">Loading...</p>
        </div>
      </div>
    );
  }
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
  const [activeSection, setActiveSection] = useState<
    AssetType | "dashboard" | "scrapers"
  >("dashboard");
  const [activeScraperTab, setActiveScraperTab] = useState<AssetType>("cards");

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadCards = async () => {
    try {
      console.log("Loading stored cards from backend...");
      const cardsResponse = await api.getCards();
      console.log("Cards loaded:", cardsResponse);
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
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log("Starting to load portfolio data...");

      // Try to load portfolio summary from backend
      console.log("Calling api.getPortfolioSummary()...");
      try {
        const summary = await api.getPortfolioSummary();
        console.log("Portfolio summary received:", summary);
        setPortfolioSummary(summary);
      } catch (apiError) {
        console.warn(
          "Portfolio API call failed, using empty summary:",
          apiError
        );
        // Use empty portfolio if API fails
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

      // Note: Load stored cards from backend
      console.log("Loading stored cards from backend...");
      try {
        const cardsResponse = await api.getCards();
        console.log("Cards loaded:", cardsResponse);
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

      console.log("Data loading completed successfully");
    } catch (err) {
      console.error("Error in loadData:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSetBuyPrice = async (id: number, buyPrice: number) => {
    try {
      await api.updateCardBuyPrice(id, buyPrice);
      // Refresh the cards to show updated data
      await loadCards();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update buy price"
      );
    }
  };

  const handleAssetDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this item?")) {
      return;
    }

    try {
      // Note: New backend doesn't store data, so deletion is just removing from local state
      // In a real implementation, this would delete from a database
      console.log("Delete asset with id:", id);
      setError("Deletion not implemented in scraper-only mode");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete item");
    }
  };

  const getSectionIcon = (section: AssetType | "dashboard" | "scrapers") => {
    switch (section) {
      case "dashboard":
        return <DashboardIcon fontSize="small" />;
      case "scrapers":
        return <DataObjectIcon fontSize="small" />;
      case "cards":
        return <StyleIcon fontSize="small" />;
      case "stocks":
        return <TrendingUpIcon fontSize="small" />;
      case "etfs":
        return <AccountBalanceIcon fontSize="small" />;
      case "crypto":
        return <CurrencyBitcoinIcon fontSize="small" />;
      case "steam":
        return <SportsEsportsIcon fontSize="small" />;
      default:
        return <DashboardIcon fontSize="small" />;
    }
  };

  const renderScraperContent = () => {
    switch (activeScraperTab) {
      case "cards":
        return <CardsScraper onScrapingComplete={loadCards} />;
      case "stocks":
        return <StocksScraper onScrapingComplete={loadData} />;
      case "etfs":
        return <ETFScraper onScrapingComplete={loadData} />;
      case "crypto":
        return <CryptoScraper onScrapingComplete={loadData} />;
      case "steam":
        return <SteamScraper onScrapingComplete={loadData} />;
      default:
        return <CardsScraper onScrapingComplete={loadCards} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-screen bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto loading-spinner"></div>
          <p className="mt-4 text-secondary">Loading Portfolio data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen min-w-screen bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="alert-error mb-4">
            <p className="font-bold">Error loading data</p>
            <p>{error}</p>
          </div>
          <button
            onClick={loadData}
            className="btn-primary font-bold py-2 px-4 rounded"
          >
            Retry
          </button>
          <div className="mt-4 text-sm text-muted">
            <p>Make sure the backend server is running on localhost:5000</p>
            <p>
              You can start it by running:{" "}
              <code className="bg-tertiary px-1 py-0.5 rounded text-primary">
                python backend/app.py
              </code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AuthProvider>
      <div className="min-h-screen min-w-screen flex justify-center bg-primary">
        <div className="container px-6 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-4xl font-bold text-primary mb-2 flex items-center gap-3">
                  Portfolio Manager
                </h1>
                <p className="text-secondary">
                  Manage and track your investment portfolio across multiple
                  asset classes
                </p>
              </div>
              <div className="pt-2">
                <AuthButton />
              </div>
            </div>
          </div>

          {/* Main Navigation */}
          <div className="mb-6">
            <nav className="-mb-px flex space-x-4">
              <button
                onClick={() => setActiveSection("dashboard")}
                className={`py-2 px-1 font-medium text-sm flex items-center gap-2 ${
                  activeSection === "dashboard" ? "tab-active" : "tab-inactive"
                }`}
              >
                {getSectionIcon("dashboard")} Dashboard
              </button>
              <button
                onClick={() => setActiveSection("scrapers")}
                className={`py-2 px-1 font-medium text-sm flex items-center gap-2 ${
                  activeSection === "scrapers" ? "tab-active" : "tab-inactive"
                }`}
              >
                {getSectionIcon("scrapers")} Scrapers
              </button>
              {(
                ["cards", "stocks", "etfs", "crypto", "steam"] as AssetType[]
              ).map((assetType) => (
                <button
                  key={assetType}
                  onClick={() => setActiveSection(assetType)}
                  className={`py-2 px-1 font-medium text-sm flex items-center gap-2 capitalize relative ${
                    activeSection === assetType ? "tab-active" : "tab-inactive"
                  }`}
                >
                  {getSectionIcon(assetType)} {assetType}
                  {assets[assetType].length > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium min-w-[20px]">
                      {assets[assetType].length > 99
                        ? "99+"
                        : assets[assetType].length}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          {activeSection === "dashboard" ? (
            <>
              {/* Portfolio Summary */}
              <PortfolioSummary summary={portfolioSummary} />

              {/* Quick Asset Overview */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {(
                  ["cards", "stocks", "etfs", "crypto", "steam"] as AssetType[]
                ).map(
                  (assetType) =>
                    assets[assetType].length > 0 && (
                      <div key={assetType} className="card">
                        <div className="card-header">
                          <h3 className="text-lg font-semibold text-primary capitalize flex items-center gap-2">
                            {getSectionIcon(assetType)} {assetType}
                          </h3>
                        </div>
                        <div className="card-body">
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-secondary">Items:</span>
                              <span className="text-primary font-medium">
                                {assets[assetType].length}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-secondary">Value:</span>
                              <span className="text-primary font-medium">
                                €
                                {portfolioSummary.asset_breakdown[
                                  assetType
                                ].value.toFixed(2)}
                              </span>
                            </div>
                            <button
                              onClick={() => setActiveSection(assetType)}
                              className="w-full mt-3 btn-secondary text-sm py-2"
                            >
                              View Details
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                )}
              </div>
            </>
          ) : activeSection === "scrapers" ? (
            <>
              {/* Scraper Tab Navigation */}
              <div className="mb-6">
                <div className="">
                  <nav className="-mb-px flex space-x-8">
                    {(
                      [
                        "cards",
                        "stocks",
                        "etfs",
                        "crypto",
                        "steam",
                      ] as AssetType[]
                    ).map((assetType) => (
                      <button
                        key={assetType}
                        onClick={() => setActiveScraperTab(assetType)}
                        className={`py-2 px-1 font-medium text-sm flex items-center gap-2 capitalize relative ${
                          activeScraperTab === assetType
                            ? "tab-active"
                            : "tab-inactive"
                        }`}
                      >
                        {getSectionIcon(assetType)} {assetType}
                        {assets[assetType].length > 0 && (
                          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium min-w-[20px]">
                            {assets[assetType].length > 99
                              ? "99+"
                              : assets[assetType].length}
                          </span>
                        )}
                      </button>
                    ))}
                  </nav>
                </div>
              </div>

              {/* Scraper Content */}
              {renderScraperContent()}
            </>
          ) : (
            <>
              {/* Individual Asset Section */}
              <AssetTable
                assets={assets[activeSection as AssetType]}
                assetType={activeSection as AssetType}
                onAssetDelete={handleAssetDelete}
                onSetBuyPrice={handleSetBuyPrice}
                onDataUpdate={loadData}
              />
            </>
          )}

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
    </AuthProvider>
  );
}

export default App;
