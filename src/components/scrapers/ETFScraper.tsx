import React, { useState } from "react";
import { apiClient } from "../../api/client";

// Material Icons
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";

interface ETFScraperProps {
  onScrapingComplete: () => void;
}

export const ETFScraper: React.FC<ETFScraperProps> = ({
  onScrapingComplete,
}) => {
  const [formData, setFormData] = useState({
    symbols: "",
    dataSource: "yahoo",
    includeExpenseRatio: true,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleScrape = async () => {
    if (!formData.symbols.trim()) {
      setError("Please enter at least one ETF symbol");
      return;
    }

    const symbols = formData.symbols
      .split(",")
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0);

    if (symbols.length === 0) {
      setError("Please enter valid ETF symbols");
      return;
    }

    setIsLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await apiClient.scrapeETFs({
        symbols,
      });

      setMessage(`Successfully scraped ${response.scraped_etfs.length} ETFs!`);
      onScrapingComplete();

      // Reset form
      setFormData({
        symbols: "",
        dataSource: "yahoo",
        includeExpenseRatio: true,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to scrape ETF data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 stats-icon-red rounded-lg flex items-center justify-center">
            <AccountBalanceIcon fontSize="small" className="text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-primary">ETF Scraper</h2>
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
                htmlFor="dataSource"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Data Source
              </label>
              <select
                id="dataSource"
                name="dataSource"
                value={formData.dataSource}
                onChange={handleInputChange}
                className="select w-full"
              >
                <option value="yahoo">Yahoo Finance</option>
                <option value="morningstar">Morningstar</option>
                <option value="ishares">iShares</option>
                <option value="vanguard">Vanguard</option>
                <option value="schwab">Charles Schwab</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="includeExpenseRatio"
                name="includeExpenseRatio"
                checked={formData.includeExpenseRatio}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue focus:ring-blue border-primary bg-tertiary rounded"
              />
              <label
                htmlFor="includeExpenseRatio"
                className="ml-2 block text-sm text-secondary"
              >
                Include expense ratios and fund details
              </label>
            </div>
          </div>

          <div>
            <label
              htmlFor="symbols"
              className="block text-sm font-medium text-secondary mb-1"
            >
              ETF Symbols (comma-separated)
            </label>
            <input
              type="text"
              id="symbols"
              name="symbols"
              value={formData.symbols}
              onChange={handleInputChange}
              className="input w-full"
              placeholder="e.g., SPY, VTI, QQQ, IVV, VXUS"
            />
            <p className="text-xs text-muted mt-1">
              Enter ETF symbols separated by commas. Examples: SPY (S&P 500),
              VTI (Total Stock Market), QQQ (NASDAQ-100)
            </p>
          </div>

          {/* Popular ETF Quick Add */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-2">
              Popular ETFs (click to add)
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { symbol: "SPY", name: "S&P 500" },
                { symbol: "VTI", name: "Total Stock Market" },
                { symbol: "QQQ", name: "NASDAQ-100" },
                { symbol: "IVV", name: "Core S&P 500" },
                { symbol: "VXUS", name: "International" },
                { symbol: "BND", name: "Total Bond Market" },
                { symbol: "VYM", name: "High Dividend Yield" },
                { symbol: "SCHD", name: "Dividend Appreciation" },
              ].map((etf) => (
                <button
                  key={etf.symbol}
                  type="button"
                  onClick={() => {
                    const currentSymbols = formData.symbols
                      ? formData.symbols + ", "
                      : "";
                    setFormData((prev) => ({
                      ...prev,
                      symbols: currentSymbols + etf.symbol,
                    }));
                  }}
                  className="px-3 py-1 text-xs bg-tertiary text-secondary rounded-md hover:bg-primary hover:text-primary transition-colors"
                >
                  {etf.symbol} - {etf.name}
                </button>
              ))}
            </div>
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
              Scraping ETF Data...
            </div>
          ) : (
            "Start Scraping ETFs"
          )}
        </button>

        <div className="mt-4 text-sm text-muted">
          <p>
            <strong>Note:</strong> ETF data will include current prices, expense
            ratios, and fund categories. Some data sources may require API keys.
          </p>
        </div>
      </div>
    </div>
  );
};
