import React, { useState, memo } from "react";
import type { Asset, AssetType } from "../../types/assets";
import { apiClient } from "../../api/client";

// Material Icons
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";

interface AssetTableProps {
  assets: Asset[];
  assetType: AssetType;
  onAssetDelete?: (id: number) => void;
  onSetBuyPrice?: (id: number, buyPrice: number) => void;
  onDataUpdate?: () => void;
}

const AssetTable: React.FC<AssetTableProps> = ({
  assets,
  assetType,
  onSetBuyPrice,
  onDataUpdate,
}) => {
  const [sortField, setSortField] = useState<keyof Asset>("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [filterText, setFilterText] = useState("");
  const [isRescraping, setIsRescraping] = useState(false);
  const [rescrapeMessage, setRescrapeMessage] = useState<string>("");
  const [rescrapeError, setRescrapeError] = useState<string>("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string>("");
  const [deleteError, setDeleteError] = useState<string>("");
  const [isAddingCard, setIsAddingCard] = useState(false);
  const [showAddCardModal, setShowAddCardModal] = useState(false);
  const [addCardMessage, setAddCardMessage] = useState<string>("");
  const [addCardError, setAddCardError] = useState<string>("");
  const [addCardFormData, setAddCardFormData] = useState({
    tcg: "Pokemon",
    expansion: "",
    numbers: "",
    headless: true,
  });

  const formatCurrency = (value: number) => `€${value.toFixed(2)}`;

  const getProfitLossColor = (profitLoss: number) => {
    if (profitLoss > 0) return "text-green-600";
    if (profitLoss < 0) return "text-red-600";
    return "text-gray-600";
  };

  const getProfitLossSymbol = (profitLoss: number) => {
    if (profitLoss > 0) return "+";
    return "-";
  };

  const getProfitLossPercentage = (asset: Asset) => {
    if (asset.price_bought === 0) return 0;
    return (
      ((asset.current_price - asset.price_bought) / asset.price_bought) * 100
    );
  };

  const getTotalItems = () => assets.length;

  const getTotalValue = () => {
    return assets.reduce(
      (total, asset) => total + asset.current_price * asset.quantity,
      0
    );
  };

  const getTotalInvestment = () => {
    return assets.reduce(
      (total, asset) => total + asset.price_bought * asset.quantity,
      0
    );
  };

  const getTotalProfitLoss = () => {
    return getTotalValue() - getTotalInvestment();
  };

  const getTotalProfitLossPercentage = () => {
    const investment = getTotalInvestment();
    if (investment === 0) return 0;
    return (getTotalProfitLoss() / investment) * 100;
  };

  const handleAddNewCard = () => {
    setShowAddCardModal(true);
    setAddCardMessage("");
    setAddCardError("");
    // Reset form to ensure clean state
    setAddCardFormData({
      tcg: "Pokemon",
      expansion: "",
      numbers: "",
      headless: true,
    });
  };

  const handleAddCardInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const newValue =
      type === "checkbox" ? (e.target as HTMLInputElement).checked : value;

    setAddCardFormData((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleAddCardSubmit = async () => {
    setIsAddingCard(true);
    setAddCardError("");

    try {
      // Parse numbers from string
      const numbers = addCardFormData.numbers
        .split(",")
        .map((n) => parseInt(n.trim()))
        .filter((n) => !isNaN(n));

      if (numbers.length === 0) {
        setAddCardError("Please enter valid card numbers");
        setIsAddingCard(false);
        return;
      }

      if (!addCardFormData.expansion.trim()) {
        setAddCardError("Please enter an expansion name");
        setIsAddingCard(false);
        return;
      }

      const result = await apiClient.scrapeCards({
        tcg: addCardFormData.tcg,
        expansion: addCardFormData.expansion,
        numbers: numbers,
        headless: addCardFormData.headless,
      });

      setAddCardMessage(
        `Successfully scraped ${result.scraped_cards.length} cards from ${addCardFormData.tcg} - ${addCardFormData.expansion}!`
      );
      setShowAddCardModal(false);

      // Reset form on success
      setAddCardFormData({
        tcg: "Pokemon",
        expansion: "",
        numbers: "",
        headless: true,
      });

      // Refresh the data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setAddCardError(
        error instanceof Error ? error.message : "Failed to add cards"
      );
    } finally {
      setIsAddingCard(false);
    }
  };

  const handleRescrape = async () => {
    setIsRescraping(true);
    setRescrapeMessage("");
    setRescrapeError("");

    try {
      const result = await apiClient.rescrapeCardPrices();
      setRescrapeMessage(
        `Successfully updated ${result.total_updated} cards. ${result.total_errors} errors.`
      );

      // Call parent component to refresh data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setRescrapeError(
        error instanceof Error ? error.message : "Failed to rescrape prices"
      );
    } finally {
      setIsRescraping(false);
    }
  };

  const handleDeleteAsset = async (id: number, assetName: string) => {
    if (
      !window.confirm(
        `Are you sure you want to delete "${assetName}"? This action cannot be undone.`
      )
    ) {
      return;
    }

    try {
      if (assetType === "cards") {
        await apiClient.deleteCard(id);
      } else {
        // For other asset types, we'd need specific delete endpoints
        // For now, show an error
        throw new Error(
          `Individual deletion not yet implemented for ${assetType}`
        );
      }

      // Refresh the data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : `Failed to delete ${assetName}`;
      setDeleteError(errorMessage);
    }
  };

  const handleDeleteAll = async () => {
    if (
      !window.confirm(
        `Are you sure you want to delete all ${assets.length} ${assetType}? This action cannot be undone.`
      )
    ) {
      return;
    }

    setIsDeleting(true);
    setDeleteMessage("");
    setDeleteError("");

    try {
      if (assetType === "cards") {
        // Use the specific cards DELETE endpoint
        const result = await apiClient.deleteAllCards();
        setDeleteMessage(
          `Successfully deleted ${result.deleted_count} out of ${result.total_cards} cards`
        );
      } else {
        // Use the generic assets DELETE endpoint for other types
        await apiClient.deleteAllAssets(assetType);
        setDeleteMessage(`Successfully deleted all ${assetType}`);
      }

      // Call parent component to refresh data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : "Failed to delete all assets"
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSort = (field: keyof Asset) => {
    if (field === sortField) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const filteredAssets = assets.filter(
    (asset) =>
      asset.name.toLowerCase().includes(filterText.toLowerCase()) ||
      (asset.type === "cards" &&
        "tcg" in asset &&
        asset.tcg.toLowerCase().includes(filterText.toLowerCase())) ||
      (asset.type === "cards" &&
        "expansion" in asset &&
        asset.expansion.toLowerCase().includes(filterText.toLowerCase())) ||
      (asset.type === "stocks" &&
        "symbol" in asset &&
        asset.symbol.toLowerCase().includes(filterText.toLowerCase())) ||
      (asset.type === "etfs" &&
        "symbol" in asset &&
        asset.symbol.toLowerCase().includes(filterText.toLowerCase()))
  );

  const sortedAssets = [...filteredAssets].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
    }

    return 0;
  });

  const getSortIcon = (field: keyof Asset) => {
    if (sortField !== field) return <UnfoldMoreIcon fontSize="small" />;
    return sortDirection === "asc" ? (
      <KeyboardArrowUpIcon fontSize="small" />
    ) : (
      <KeyboardArrowDownIcon fontSize="small" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Total Summary Section */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-primary">
              {assetType.charAt(0).toUpperCase() + assetType.slice(1)} Summary
            </h3>
            <div className="flex space-x-3">
              {/* Add New button for each asset type */}
              {assetType === "cards" && (
                <button
                  onClick={handleAddNewCard}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  Add New Card
                </button>
              )}
              {assetType === "stocks" && (
                <button
                  onClick={() => alert("Add New Stock (not implemented)")}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  Add New Stock
                </button>
              )}
              {assetType === "etfs" && (
                <button
                  onClick={() => alert("Add New ETF (not implemented)")}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  Add New ETF
                </button>
              )}
              {assetType === "crypto" && (
                <button
                  onClick={() => alert("Add New Crypto (not implemented)")}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  Add New Crypto
                </button>
              )}
              {/* Rescrape/refresh and delete all remain for all types */}
              {assetType === "cards" && (
                <button
                  onClick={handleRescrape}
                  disabled={isRescraping || assets.length === 0}
                  className="primary-btn disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  {isRescraping ? "Rescraping..." : "Rescrape Prices"}
                </button>
              )}
              <button
                onClick={handleDeleteAll}
                disabled={isDeleting || assets.length === 0}
                className="primary-btn btn-red disabled:bg-gray-600 disabled:cursor-not-allowed"
              >
                {isDeleting ? "Deleting..." : "Delete All"}
              </button>
            </div>
          </div>
        </div>

        <div className="card-body">
          {/* Status messages */}
          {rescrapeMessage && (
            <div className="mb-4 p-4 bg-green-800 border border-green-600 text-green-200 rounded">
              {rescrapeMessage}
            </div>
          )}
          {rescrapeError && (
            <div className="mb-4 p-4 bg-red-800 border border-red-600 text-red-200 rounded">
              {rescrapeError}
            </div>
          )}
          {addCardMessage && (
            <div className="mb-4 p-4 bg-green-800 border border-green-600 text-green-200 rounded">
              {addCardMessage}
            </div>
          )}
          {addCardError && (
            <div className="mb-4 p-4 bg-red-800 border border-red-600 text-red-200 rounded">
              {addCardError}
            </div>
          )}
          {deleteMessage && (
            <div className="mb-4 p-4 bg-green-800 border border-green-600 text-green-200 rounded">
              {deleteMessage}
            </div>
          )}
          {deleteError && (
            <div className="mb-4 p-4 bg-red-800 border border-red-600 text-red-200 rounded">
              {deleteError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Items
              </div>
              <div className="text-2xl font-bold text-primary">
                {getTotalItems()}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Value
              </div>
              <div className="text-2xl font-bold text-primary">
                {formatCurrency(getTotalValue())}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Investment
              </div>
              <div className="text-2xl font-bold text-primary">
                {formatCurrency(getTotalInvestment())}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total P&L
              </div>
              <div
                className={`text-2xl font-bold ${getProfitLossColor(
                  getTotalProfitLoss()
                )}`}
              >
                {getProfitLossSymbol(getTotalProfitLoss())}
                {formatCurrency(Math.abs(getTotalProfitLoss()))}
                <div className="text-sm font-normal">
                  ({getProfitLossSymbol(getTotalProfitLossPercentage())}
                  {getTotalProfitLossPercentage().toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Table */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-primary">
              {assetType.charAt(0).toUpperCase() + assetType.slice(1)} (
              {assets.length})
            </h3>
            <input
              type="text"
              placeholder={`Filter ${assetType}...`}
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="border border-gray-600 bg-tertiary text-primary rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-secondary"
            />
          </div>
        </div>

        <div className="card-body">
          {sortedAssets.length === 0 ? (
            <div className="px-6 py-8 text-center text-secondary">
              {filterText
                ? `No ${assetType} found matching "${filterText}"`
                : `No ${assetType} found`}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-600">
                <thead className="bg-tertiary">
                  <tr>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                      onClick={() => handleSort("name")}
                    >
                      Name {getSortIcon("name")}
                    </th>
                    {assetType === "cards" && (
                      <th
                        className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort("tcg" as keyof Asset)}
                      >
                        TCG {getSortIcon("tcg" as keyof Asset)}
                      </th>
                    )}
                    {assetType === "cards" && (
                      <th
                        className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort("expansion" as keyof Asset)}
                      >
                        Expansion {getSortIcon("expansion" as keyof Asset)}
                      </th>
                    )}
                    {(assetType === "stocks" || assetType === "etfs") && (
                      <th
                        className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort("symbol" as keyof Asset)}
                      >
                        Symbol {getSortIcon("symbol" as keyof Asset)}
                      </th>
                    )}
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                      onClick={() => handleSort("quantity")}
                    >
                      Quantity {getSortIcon("quantity")}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                      onClick={() => handleSort("current_price")}
                    >
                      Current Price {getSortIcon("current_price")}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                      onClick={() => handleSort("price_bought")}
                    >
                      Buy Price {getSortIcon("price_bought")}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      Total Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      P&L
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-secondary divide-y divide-gray-600">
                  {sortedAssets.map((asset) => {
                    const totalValue = asset.current_price * asset.quantity;
                    const totalInvestment = asset.price_bought * asset.quantity;
                    const profitLoss = totalValue - totalInvestment;
                    const profitLossPercentage = getProfitLossPercentage(asset);

                    return (
                      <tr key={asset.id} className="hover:bg-tertiary">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-primary">
                            {asset.name}
                          </div>
                        </td>
                        {assetType === "cards" && "tcg" in asset && (
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-secondary">
                              {asset.tcg}
                            </div>
                          </td>
                        )}
                        {assetType === "cards" && "expansion" in asset && (
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-secondary">
                              {asset.expansion}
                            </div>
                          </td>
                        )}
                        {(assetType === "stocks" || assetType === "etfs") &&
                          "symbol" in asset && (
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-secondary">
                                {asset.symbol}
                              </div>
                            </td>
                          )}
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-secondary">
                            {asset.quantity}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-secondary">
                            {formatCurrency(asset.current_price)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-secondary">
                            {formatCurrency(asset.price_bought)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-primary">
                            {formatCurrency(totalValue)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div
                            className={`text-sm font-medium ${getProfitLossColor(
                              profitLoss
                            )}`}
                          >
                            {getProfitLossSymbol(profitLoss)}
                            {formatCurrency(Math.abs(profitLoss))}
                          </div>
                          <div
                            className={`text-xs ${getProfitLossColor(
                              profitLoss
                            )}`}
                          >
                            ({getProfitLossSymbol(profitLossPercentage)}
                            {profitLossPercentage.toFixed(2)}%)
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                          {onSetBuyPrice && (
                            <button
                              onClick={() => {
                                const buyPrice = prompt(
                                  `Set buy price for ${asset.name}:`,
                                  asset.price_bought.toString()
                                );
                                if (
                                  buyPrice !== null &&
                                  !isNaN(parseFloat(buyPrice))
                                ) {
                                  onSetBuyPrice(asset.id, parseFloat(buyPrice));
                                }
                              }}
                              className="text-green-400 hover:text-green-300 transition-colors"
                            >
                              Set Price
                            </button>
                          )}
                          <button
                            onClick={() =>
                              handleDeleteAsset(asset.id, asset.name)
                            }
                            className="text-red-400 hover:text-red-300 transition-colors"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add Card Modal */}
      {showAddCardModal && (
        <div
          key="add-card-modal"
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4 border border-gray-600">
            <h3 className="text-lg font-semibold text-white mb-4">
              Add New Cards
            </h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAddCardSubmit();
              }}
            >
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="add-tcg"
                    className="block text-sm font-medium text-gray-300 mb-2"
                  >
                    Trading Card Game
                  </label>
                  <select
                    id="add-tcg"
                    name="tcg"
                    value={addCardFormData.tcg}
                    onChange={handleAddCardInputChange}
                    className="w-full border border-gray-600 bg-gray-700 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    htmlFor="add-expansion"
                    className="block text-sm font-medium text-gray-300 mb-2"
                  >
                    Expansion/Set
                  </label>
                  <input
                    type="text"
                    id="add-expansion"
                    name="expansion"
                    value={addCardFormData.expansion}
                    onChange={handleAddCardInputChange}
                    placeholder="e.g., Stellar Crown"
                    autoComplete="off"
                    className="w-full border border-gray-600 bg-gray-700 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                    key="expansion-input"
                  />
                </div>

                <div>
                  <label
                    htmlFor="add-numbers"
                    className="block text-sm font-medium text-gray-300 mb-2"
                  >
                    Card Numbers (comma-separated)
                  </label>
                  <input
                    type="text"
                    id="add-numbers"
                    name="numbers"
                    value={addCardFormData.numbers}
                    onChange={handleAddCardInputChange}
                    placeholder="e.g., 170, 135, 152, 108"
                    autoComplete="off"
                    className="w-full border border-gray-600 bg-gray-700 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                    key="numbers-input"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Enter card numbers separated by commas. Example: 170, 135,
                    152
                  </p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="add-headless"
                    name="headless"
                    checked={addCardFormData.headless}
                    onChange={handleAddCardInputChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 bg-gray-700 rounded"
                  />
                  <label
                    htmlFor="add-headless"
                    className="ml-2 block text-sm text-gray-300"
                  >
                    Run in headless mode (browser hidden)
                  </label>
                </div>
              </div>

              {addCardError && (
                <div className="mt-4 p-3 bg-red-800 border border-red-600 text-red-200 rounded text-sm">
                  {addCardError}
                </div>
              )}

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddCardModal(false);
                    setAddCardError("");
                  }}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAddingCard}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  {isAddingCard ? "Scraping..." : "Add Cards"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(AssetTable);
