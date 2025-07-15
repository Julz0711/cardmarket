import React, { useState } from "react";
import { apiClient } from "../../api/client";

// Material Icons
import StyleIcon from "@mui/icons-material/Style";

interface ScrapingFormData {
  tcg: string;
  expansion: string;
  numbers: string;
  headless: boolean;
}

interface CardsScraperProps {
  onScrapingComplete: () => void;
}

export const CardsScraper: React.FC<CardsScraperProps> = ({
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
        setError("Please enter valid card numbers");
        return;
      }

      const response = await apiClient.scrapeCards({
        tcg: formData.tcg,
        expansion: formData.expansion,
        numbers: numbers,
        headless: formData.headless,
      });

      // Create detailed success message
      let successMessage = response.message;

      if (response.skipped_cards && response.skipped_cards.length > 0) {
        const skippedNumbers = response.skipped_cards
          .map((card: any) => `#${card.number}`)
          .join(", ");
        successMessage += `\n\nSkipped existing cards: ${skippedNumbers}`;
      }

      setMessage(successMessage);

      // Call the callback to refresh data
      onScrapingComplete();

      // Reset form on success
      setFormData({
        tcg: "Pokemon",
        expansion: "",
        numbers: "",
        headless: true,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during scraping"
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
            <StyleIcon fontSize="small" className="text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-primary">
            Trading Cards Scraper
          </h2>
        </div>
      </div>

      <div className="card-body">
        {/* Status Messages */}
        {message && (
          <div className="mb-4 alert-success whitespace-pre-line">
            {message}
          </div>
        )}

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
                className="select w-full"
              >
                <option value="Pokemon">Pokemon</option>
                <option value="Magic">Magic: The Gathering</option>
                <option value="YuGiOh">Yu-Gi-Oh!</option>
                <option value="DragonBall">Dragon Ball Super</option>
                <option value="OnePiece">One Piece</option>
                <option value="Digimon">Digimon</option>
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
            <p className="text-xs text-muted mt-1">
              Enter card numbers separated by commas. Example: 170, 135, 152
            </p>
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
          className={`w-full transition-colors ${
            isLoading ? "btn-xl cursor-not-allowed" : "btn-xl"
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <div role="status">
                <svg
                  aria-hidden="true"
                  className="w-4 h-4 text-gray-200 animate-spin dark:text-gray-600 fill-blue-500"
                  viewBox="0 0 100 101"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                    fill="currentColor"
                  />
                  <path
                    d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                    fill="currentFill"
                  />
                </svg>
                <span className="sr-only">Loading...</span>
              </div>
              Scraping CardMarket...
            </div>
          ) : (
            "Start Scraping Cards"
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
