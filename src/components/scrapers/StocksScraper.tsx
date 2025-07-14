import React, { useState } from "react";
import { apiClient } from "../../api/client";

// Material Icons
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

interface StocksScraperProps {
  onScrapingComplete: () => void;
}

export const StocksScraper: React.FC<StocksScraperProps> = ({
  onScrapingComplete,
}) => {
  const [formData, setFormData] = useState({
    symbols: "",
    market: "NYSE",
    exchange: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleScrape = async () => {
    if (!formData.symbols.trim()) {
      setError("Please enter at least one stock symbol");
      return;
    }

    const symbols = formData.symbols
      .split(",")
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0);

    if (symbols.length === 0) {
      setError("Please enter valid stock symbols");
      return;
    }

    setIsLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await apiClient.scrapeStocks({
        symbols,
        market: formData.market,
      });

      setMessage(
        `Successfully scraped ${response.scraped_stocks.length} stocks!`
      );
      onScrapingComplete();

      // Reset form
      setFormData({
        symbols: "",
        market: "NYSE",
        exchange: "",
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to scrape stock data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 stats-icon-blue rounded-lg flex items-center justify-center">
            <TrendingUpIcon fontSize="small" className="text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-primary">Stocks Scraper</h2>
        </div>
      </div>

      <div className="card-body">
        {/* Status Messages */}
        {message && <div className="mb-4 alert-success">{message}</div>}

        {error && <div className="mb-4 alert-error">{error}</div>}

        {/* Scraping Form */}
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="market"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Market/Exchange
              </label>
              <select
                id="market"
                name="market"
                value={formData.market}
                onChange={handleInputChange}
                className="select w-full"
              >
                <option value="NYSE">NYSE</option>
                <option value="NASDAQ">NASDAQ</option>
                <option value="LSE">London Stock Exchange</option>
                <option value="XETRA">XETRA (Germany)</option>
                <option value="TSE">Tokyo Stock Exchange</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="exchange"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Data Source
              </label>
              <select
                id="exchange"
                name="exchange"
                value={formData.exchange}
                onChange={handleInputChange}
                className="select w-full"
              >
                <option value="">Auto-detect</option>
                <option value="yahoo">Yahoo Finance</option>
                <option value="alphavantage">Alpha Vantage</option>
                <option value="finnhub">Finnhub</option>
              </select>
            </div>
          </div>

          <div>
            <label
              htmlFor="symbols"
              className="block text-sm font-medium text-secondary mb-1"
            >
              Stock Symbols (comma-separated)
            </label>
            <input
              type="text"
              id="symbols"
              name="symbols"
              value={formData.symbols}
              onChange={handleInputChange}
              className="input w-full"
              placeholder="e.g., AAPL, MSFT, GOOGL, TSLA"
            />
            <p className="text-xs text-muted mt-1">
              Enter stock symbols separated by commas. Examples: AAPL, MSFT,
              GOOGL
            </p>
          </div>
        </div>

        {/* Scrape Button */}
        <button
          onClick={handleScrape}
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-md font-medium transition-colors ${
            isLoading
              ? "btn-secondary cursor-not-allowed opacity-50"
              : "btn-primary"
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              Scraping Stock Data...
            </div>
          ) : (
            "Start Scraping Stocks"
          )}
        </button>

        <div className="mt-4 text-sm text-muted">
          <p>
            <strong>Note:</strong> Stock data will be fetched from financial
            APIs. Make sure you have proper API keys configured for your chosen
            data source.
          </p>
        </div>
      </div>
    </div>
  );
};
