import React, { useState } from "react";
import { apiClient } from "../api/client";

interface ScrapingFormData {
  tcg: string;
  expansion: string;
  numbers: string;
  headless: boolean;
}

interface CardMarketScraperProps {
  onScrapingComplete: () => void;
}

export const CardMarketScraper: React.FC<CardMarketScraperProps> = ({
  onScrapingComplete,
}) => {
  const [formData, setFormData] = useState<ScrapingFormData>({
    tcg: "Pokemon",
    expansion: "Black Bolt JP",
    numbers: "170, 135, 152, 108, 146, 104",
    headless: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleScrape = async () => {
    setIsLoading(true);
    setMessage("");
    setError("");

    try {
      // Parse numbers from string
      const numbers = formData.numbers
        .split(",")
        .map((n) => parseInt(n.trim()))
        .filter((n) => !isNaN(n));

      if (numbers.length === 0) {
        throw new Error("Please enter valid card numbers");
      }

      const response = await apiClient.scrapeCards({
        tcg: formData.tcg,
        expansion: formData.expansion,
        numbers: numbers,
        headless: formData.headless,
      });

      setMessage(
        `✅ Successfully scraped ${response.scraped_cards.length} cards!`
      );
      onScrapingComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to scrape cards");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 stats-icon-blue rounded-lg flex items-center justify-center">
            <span className="text-primary font-semibold text-sm">🤖</span>
          </div>
          <h2 className="text-xl font-semibold text-primary">
            CardMarket Scraper
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
                htmlFor="tcg"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Trading Card Game
              </label>
              <select
                id="tcg"
                name="tcg"
                value={formData.tcg}
                onChange={handleInputChange}
                className="select"
              >
                <option value="Pokemon">Pokemon</option>
                <option value="Magic">Magic: The Gathering</option>
                <option value="YuGiOh">Yu-Gi-Oh!</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="expansion"
                className="block text-sm font-medium text-secondary mb-1"
              >
                Expansion/Set
              </label>
              <input
                type="text"
                id="expansion"
                name="expansion"
                value={formData.expansion}
                onChange={handleInputChange}
                className="input w-full"
                placeholder="e.g., Black Bolt JP"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="numbers"
              className="block text-sm font-medium text-secondary mb-1"
            >
              Card Numbers (comma-separated)
            </label>
            <input
              type="text"
              id="numbers"
              name="numbers"
              value={formData.numbers}
              onChange={handleInputChange}
              className="input w-full"
              placeholder="e.g., 170, 135, 152, 108"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="headless"
              name="headless"
              checked={formData.headless}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue focus:ring-blue border-primary bg-tertiary rounded"
            />
            <label
              htmlFor="headless"
              className="ml-2 block text-sm text-secondary"
            >
              Run in headless mode (browser hidden)
            </label>
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
              Scraping CardMarket...
            </div>
          ) : (
            "Start Scraping"
          )}
        </button>

        <div className="mt-4 text-sm text-muted">
          <p>
            <strong>Note:</strong> Scraping may take a few minutes depending on
            the number of cards. The browser will automatically navigate
            CardMarket to gather real-time data.
          </p>
        </div>
      </div>
    </div>
  );
};
