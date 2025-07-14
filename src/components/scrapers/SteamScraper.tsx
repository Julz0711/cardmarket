import React, { useState } from "react";
import { apiClient } from "../../api/client";

// Material Icons
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";

interface SteamScraperProps {
  onScrapingComplete: () => void;
}

export const SteamScraper: React.FC<SteamScraperProps> = ({
  onScrapingComplete,
}) => {
  const [formData, setFormData] = useState({
    steamId: "",
    appId: "",
    includeFloats: true,
    priceSource: "csfloat",
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
    if (!formData.steamId.trim()) {
      setError("Please enter your Steam ID");
      return;
    }

    setIsLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await apiClient.scrapeSteam({
        steamId: formData.steamId,
        appId: formData.appId || undefined,
      });

      setMessage(
        `Successfully scraped ${response.scraped_items.length} Steam items!`
      );
      onScrapingComplete();

      // Reset form
      setFormData({
        steamId: "",
        appId: "",
        includeFloats: true,
        priceSource: "csfloat",
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to scrape Steam inventory"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 stats-icon-green rounded-lg flex items-center justify-center">
            <SportsEsportsIcon fontSize="small" className="text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-primary">
            Steam Inventory Scraper
          </h2>
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
                htmlFor="steamId"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Steam ID / Profile URL
              </label>
              <input
                type="text"
                id="steamId"
                name="steamId"
                value={formData.steamId}
                onChange={handleInputChange}
                className="input w-full"
                placeholder="e.g., 76561198000000000 or steamcommunity.com/id/username"
              />
              <p className="text-xs text-muted mt-1">
                Enter your Steam ID or profile URL. Your inventory must be
                public.
              </p>
            </div>

            <div>
              <label
                htmlFor="appId"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Game App ID (Optional)
              </label>
              <select
                id="appId"
                name="appId"
                value={formData.appId}
                onChange={handleInputChange}
                className="select w-full"
              >
                <option value="">All Games</option>
                <option value="730">Counter-Strike 2</option>
                <option value="570">Dota 2</option>
                <option value="440">Team Fortress 2</option>
                <option value="252490">Rust</option>
                <option value="304930">Unturned</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="priceSource"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Price Data Source
              </label>
              <select
                id="priceSource"
                name="priceSource"
                value={formData.priceSource}
                onChange={handleInputChange}
                className="select w-full"
              >
                <option value="csfloat">CSFloat</option>
                <option value="steammarket">Steam Community Market</option>
                <option value="buff163">Buff163</option>
                <option value="skinport">Skinport</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="includeFloats"
                name="includeFloats"
                checked={formData.includeFloats}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue focus:ring-blue border-primary bg-tertiary rounded"
              />
              <label
                htmlFor="includeFloats"
                className="ml-2 block text-sm text-secondary"
              >
                Include float values and pattern info (CS2 skins)
              </label>
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
              Scraping Steam Inventory...
            </div>
          ) : (
            "Start Scraping Steam Inventory"
          )}
        </button>

        <div className="mt-4 text-sm text-muted">
          <p>
            <strong>Note:</strong> Your Steam inventory must be set to public
            for this to work. Prices will be fetched from your selected source.
            CS2 items will include float values when available.
          </p>
        </div>
      </div>
    </div>
  );
};
