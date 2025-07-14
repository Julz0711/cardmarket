import React, { useState } from "react";
import { apiClient } from "../../api/client";

// Material Icons
import CurrencyBitcoinIcon from "@mui/icons-material/CurrencyBitcoin";

interface CryptoScraperProps {
  onScrapingComplete: () => void;
}

export const CryptoScraper: React.FC<CryptoScraperProps> = ({
  onScrapingComplete,
}) => {
  const [formData, setFormData] = useState({
    symbols: "",
    exchange: "coinmarketcap",
    includeMetrics: true,
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
      setError("Please enter at least one cryptocurrency symbol");
      return;
    }

    const symbols = formData.symbols
      .split(",")
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0);

    if (symbols.length === 0) {
      setError("Please enter valid cryptocurrency symbols");
      return;
    }

    setIsLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await apiClient.scrapeCrypto({
        symbols,
      });

      setMessage(
        `Successfully scraped ${response.scraped_crypto.length} cryptocurrencies!`
      );
      onScrapingComplete();

      // Reset form
      setFormData({
        symbols: "",
        exchange: "coinmarketcap",
        includeMetrics: true,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to scrape crypto data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 stats-icon-gold rounded-lg flex items-center justify-center">
            <CurrencyBitcoinIcon fontSize="small" className="text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-primary">Crypto Scraper</h2>
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
                <option value="coinmarketcap">CoinMarketCap</option>
                <option value="coingecko">CoinGecko</option>
                <option value="binance">Binance</option>
                <option value="coinbase">Coinbase</option>
                <option value="kraken">Kraken</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="includeMetrics"
                name="includeMetrics"
                checked={formData.includeMetrics}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue focus:ring-blue border-primary bg-tertiary rounded"
              />
              <label
                htmlFor="includeMetrics"
                className="ml-2 block text-sm text-secondary"
              >
                Include market metrics (market cap, volume, etc.)
              </label>
            </div>
          </div>

          <div>
            <label
              htmlFor="symbols"
              className="block text-sm font-medium text-secondary mb-1"
            >
              Cryptocurrency Symbols (comma-separated)
            </label>
            <input
              type="text"
              id="symbols"
              name="symbols"
              value={formData.symbols}
              onChange={handleInputChange}
              className="input w-full"
              placeholder="e.g., BTC, ETH, ADA, DOT, SOL"
            />
            <p className="text-xs text-muted mt-1">
              Enter crypto symbols separated by commas. Examples: BTC, ETH, ADA,
              MATIC
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
              Scraping Crypto Data...
            </div>
          ) : (
            "Start Scraping Crypto"
          )}
        </button>

        <div className="mt-4 text-sm text-muted">
          <p>
            <strong>Note:</strong> Cryptocurrency data will be fetched from your
            selected exchange API. Rate limits may apply depending on the data
            source.
          </p>
        </div>
      </div>
    </div>
  );
};
