import React, { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import type { SteamItem } from "../types/assets";

// Material Icons
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import DeleteIcon from "@mui/icons-material/Delete";
import WarningIcon from "@mui/icons-material/Warning";
import SearchIcon from "@mui/icons-material/Search";
import EditIcon from "@mui/icons-material/Edit";
import RefreshIcon from "@mui/icons-material/Refresh";
import CheckIcon from "@mui/icons-material/Check";

export const SteamInventory: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState<SteamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteAllConfirm, setDeleteAllConfirm] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);
  const [updatingPrices, setUpdatingPrices] = useState(false);
  const [updatingFloats, setUpdatingFloats] = useState(false);
  const [rescraping, setRescraping] = useState(false);
  const [rescrapeMessage, setRescrapeMessage] = useState("");

  // Rescrape inventory handler
  const handleRescrapeInventory = async () => {
    setRescraping(true);
    setRescrapeMessage("");
    setError("");
    try {
      // Call backend endpoint to rescrape inventory and update DB
      const response = await apiClient.rescrapeSteamInventory({
        steam_id: profileId,
      });
      // Reload items after rescrape
      await loadSteamItems();
      setRescrapeMessage(response.message || "Rescrape completed.");
    } catch (err) {
      setError("Failed to rescrape Steam inventory");
      setRescrapeMessage("");
      console.error(err);
    } finally {
      setRescraping(false);
    }
  };

  // Edit price states
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState("");
  // Overpay states
  const [editingOverpayItem, setEditingOverpayItem] = useState<string | null>(
    null
  );
  const [editOverpay, setEditOverpay] = useState("");

  // Add Profile states
  const [addingProfile, setAddingProfile] = useState(false);
  const [addProfileNote, setAddProfileNote] = useState("");
  const [showImportModal, setShowImportModal] = useState(false);
  const [steamIdInput, setSteamIdInput] = useState("");
  // Profile ID state
  const [profileId, setProfileId] = useState<string>("");

  // Import options
  const [includePrices, setIncludePrices] = useState(false);
  const [includeFloats, setIncludeFloats] = useState(false);

  // Filter states
  const [nameFilter, setNameFilter] = useState("");
  const [rarityFilter, setRarityFilter] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  // Sort states
  // Default: sort by current price, descending (high to low)
  const [sortBy, setSortBy] = useState<"name" | "rarity" | "price" | "profit">(
    "price"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    // Only load Steam items if user is authenticated
    if (isAuthenticated) {
      loadSteamItems();
    } else {
      // Clear items if not authenticated
      setItems([]);
      setLoading(false);
    }
  }, [isAuthenticated]); // Re-run when authentication status changes

  // Add Profile handler (uses modal input)
  const handleAddProfile = async () => {
    setShowImportModal(true);
  };

  const handleImportConfirm = async () => {
    setAddingProfile(true);
    setAddProfileNote("Importing Steam inventory. This may take a minute...");
    setError("");
    setShowImportModal(false);
    try {
      // Use the correct scraping endpoint that saves to database
      const scrapeResponse = await apiClient.scrapeSteam({
        steam_id: steamIdInput,
        headless: true,
        include_floats: includeFloats,
        include_prices: includePrices,
      });

      // Set profileId to the imported Steam ID
      setProfileId(steamIdInput);

      // Reload items from database to get the saved items
      await loadSteamItems();

      // Handle response format from backend
      const totalScraped = scrapeResponse.data.total_scraped;
      setAddProfileNote(`Successfully imported ${totalScraped} Steam items.`);
    } catch (err) {
      setError("Failed to import Steam inventory");
      setAddProfileNote("");
      console.error(err);
    } finally {
      setAddingProfile(false);
      setSteamIdInput("");
      setIncludePrices(false);
      setIncludeFloats(false);
    }
  };

  const loadSteamItems = async () => {
    if (!isAuthenticated) {
      setError("Please log in to view your Steam inventory");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(""); // Clear any previous errors
      const response = await apiClient.getSteamItems(1, 1000);
      setItems(response.items || []);
      // If items exist, set profileId from the first item's steam_id
      if (response.items && response.items.length > 0) {
        const firstSteamId = response.items[0].steam_id;
        if (firstSteamId) setProfileId(firstSteamId);
      }
    } catch (err: any) {
      if (err?.message?.includes("401") || err?.status === 401) {
        setError(
          "Authentication required. Please log in to view your Steam inventory."
        );
      } else {
        setError("Failed to load Steam inventory");
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditPrice = (item: SteamItem) => {
    setEditingItem(item._id || item.id?.toString() || "");
    setEditPrice(item.price_bought?.toString() || "0");
    setEditingOverpayItem(null);
    setEditOverpay("");
  };

  const handleSavePrice = async (itemId: string) => {
    try {
      const price = parseFloat(editPrice) || 0;
      await apiClient.updateSteamItem(itemId, { price_bought: price });

      // Update local state
      setItems(
        items.map((item) =>
          (item._id || item.id?.toString()) === itemId
            ? { ...item, price_bought: price }
            : item
        )
      );

      setEditingItem(null);
      setEditPrice("");
    } catch (err) {
      setError("Failed to update bought price");
      console.error(err);
    }
  };

  // Overpay edit/save handlers
  const handleEditOverpay = (item: SteamItem) => {
    setEditingOverpayItem(item._id || item.id?.toString() || "");
    setEditOverpay((item.overpay ?? "").toString());
    setEditingItem(null);
    setEditPrice("");
  };

  const handleSaveOverpay = async (itemId: string) => {
    try {
      let overpay = Math.abs(parseFloat(editOverpay) || 0); // Only positive
      await apiClient.updateSteamItem(itemId, { overpay });
      setItems(
        items.map((item) =>
          (item._id || item.id?.toString()) === itemId
            ? { ...item, overpay }
            : item
        )
      );
      setEditingOverpayItem(null);
      setEditOverpay("");
    } catch (err) {
      setError("Failed to update overpay");
      console.error(err);
    }
  };

  const handleDeleteAllItems = async () => {
    try {
      setDeletingAll(true);

      // Delete all items one by one
      for (const item of items) {
        const itemId = item._id || item.id?.toString() || "";
        if (itemId) {
          await apiClient.deleteSteamItem(itemId);
        }
      }

      // Clear local state
      setItems([]);
      setDeleteAllConfirm(false);
    } catch (err) {
      setError("Failed to delete all items from inventory");
      console.error(err);
    } finally {
      setDeletingAll(false);
    }
  };

  const handleUpdatePrices = async () => {
    try {
      setUpdatingPrices(true);
      setError("");

      const response = await apiClient.updateSteamPrices({
        headless: true,
      });

      // Update local state with new prices
      if (response.details.updated.length > 0) {
        setItems((prevItems) =>
          prevItems.map((item) => {
            const updatedItem = response.details.updated.find(
              (updated) => updated.name === item.name
            );
            if (updatedItem) {
              return { ...item, current_price: updatedItem.price };
            }
            return item;
          })
        );
      }

      // Show success or warning message
      if (
        response.status === "warning" ||
        response.details.updated.length === 0
      ) {
        setError(
          "No prices could be updated. SkinSearch may be down or blocking requests."
        );
      } else {
        setError("");
      }
      console.log(`Price update completed: ${response.message}`);
    } catch (err) {
      setError("Failed to update prices from SkinSearch");
      console.error(err);
    } finally {
      setUpdatingPrices(false);
    }
  };

  const handleUpdateFloats = async () => {
    try {
      setUpdatingFloats(true);
      setError("");

      const response = await apiClient.updateSteamFloats({
        headless: true,
      });

      // Update local state with new float data
      if (response.details.updated.length > 0) {
        setItems((prevItems) =>
          prevItems.map((item) => {
            const updatedItem = response.details.updated.find(
              (updated) => updated.name === item.name
            );
            if (updatedItem) {
              return {
                ...item,
                float_value: updatedItem.float_value ?? undefined,
                paint_seed: updatedItem.paint_seed ?? undefined,
              };
            }
            return item;
          })
        );
      }

      // Show success or warning message
      if (
        response.status === "warning" ||
        response.details.updated.length === 0
      ) {
        setError(
          "No float values could be updated. CSFloat may be down or items may not have inspect links."
        );
      } else {
        setError("");
      }
      console.log(`Float update completed: ${response.message}`);
    } catch (err) {
      setError("Failed to update float values from CSFloat");
      console.error(err);
    } finally {
      setUpdatingFloats(false);
    }
  };

  // Filter items based on current filter criteria
  const filteredItems = items
    .filter((item) => {
      // Name filter
      if (
        nameFilter &&
        !item.name.toLowerCase().includes(nameFilter.toLowerCase())
      ) {
        return false;
      }

      // Rarity filter
      if (rarityFilter && item.rarity !== rarityFilter) {
        return false;
      }

      // Price filter
      const currentPrice = item.current_price || 0;
      if (minPrice && currentPrice < parseFloat(minPrice)) {
        return false;
      }
      if (maxPrice && currentPrice > parseFloat(maxPrice)) {
        return false;
      }

      return true;
    })
    .sort((a, b) => {
      let compareValue = 0;

      switch (sortBy) {
        case "name":
          compareValue = a.name.localeCompare(b.name);
          break;
        case "rarity":
          // Define rarity order for proper sorting
          const rarityOrder = {
            Consumer: 1,
            Industrial: 2,
            "Mil-Spec": 3,
            Restricted: 4,
            Classified: 5,
            Covert: 6,
            Contraband: 7,
            Extraordinary: 7,
            Distinguished: 2,
            Exceptional: 4,
            Superior: 5,
            Master: 6,
            Common: 0,
            Uncommon: 2,
            Immortal: 7,
            "Master Agent": 6,
            "Superior Agent": 5,
            "Exceptional Agent": 4,
            "Distinguished Agent": 3,
            Rare: 3,
          };
          const aRarity =
            rarityOrder[a.rarity as keyof typeof rarityOrder] || 0;
          const bRarity =
            rarityOrder[b.rarity as keyof typeof rarityOrder] || 0;
          compareValue = aRarity - bRarity;
          break;
        case "price":
          compareValue = (a.current_price || 0) - (b.current_price || 0);
          break;
        case "profit":
          const aProfit = (a.current_price || 0) - (a.price_bought || 0);
          const bProfit = (b.current_price || 0) - (b.price_bought || 0);
          compareValue = aProfit - bProfit;
          break;
      }

      return sortOrder === "desc" ? -compareValue : compareValue;
    });

  // Get unique rarities for filter dropdown
  const uniqueRarities = [...new Set(items.map((item) => item.rarity))].sort();

  const clearFilters = () => {
    setNameFilter("");
    setRarityFilter("");
    setMinPrice("");
    setMaxPrice("");
    setSortBy("name");
    setSortOrder("asc");
  };

  const getRarityColor = (rarity: string) => {
    const colors: Record<string, string> = {
      Consumer: "#b0c3d9",
      Industrial: "#5e98d9",
      "Mil-Spec": "#4b69ff",
      Restricted: "#8847ff",
      Classified: "#d32ce6",
      Covert: "#eb4b4b",
      Contraband: "#e4ae39",
      Extraordinary: "#eb4b4b",
      Uncommon: "#5e98d9",
      Common: "#b0b0b0",
      Stock: "#b0b0b0",
      Rare: "#4b69ff",
      // Agent rarities - NEW proper names (after rescraping)
      "Master Agent": "#eb4b4b",
      "Superior Agent": "#d32ce6",
      "Exceptional Agent": "#8847ff",
      "Distinguished Agent": "#4b69ff",
      // Legacy agent rarities mapped incorrectly - FIXES for current data
      Legendary: "#eb4b4b",
      Mythical: "#8847ff",
    };

    // Debug log to see what rarity values we're getting
    if (!colors[rarity]) {
      console.log(`Unknown rarity: "${rarity}"`);
    }

    return colors[rarity] || "#b0b0b0";
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue"></div>
            <span className="ml-2 text-secondary">
              Loading Steam inventory...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="alert-error">{error}</div>
        </div>
      </div>
    );
  }

  // Show authentication message if not logged in
  if (!isAuthenticated) {
    return (
      <div className="space-y-6">
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 stats-icon-green rounded-lg flex items-center justify-center">
                <SportsEsportsIcon fontSize="small" className="text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-primary">
                Steam Inventory
              </h2>
            </div>
          </div>
          <div className="card-body text-center py-12">
            <WarningIcon className="text-6xl text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Authentication Required
            </h3>
            <p className="text-muted">
              Please log in to view your Steam inventory.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Steam Inventory Summary Section */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between gap-3">
            <div className=" flex items-center justify-center gap-4">
              <div className="w-8 h-8 stats-icon-blue rounded-lg flex items-center justify-center">
                <SportsEsportsIcon fontSize="small" className="text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-primary">
                Steam Inventory Summary
              </h2>
            </div>

            {rescrapeMessage && (
              <span className="ml-4 text-xs text-blue-400">
                {rescrapeMessage}
              </span>
            )}

            {/* Steam Profile Actions */}
            <div className="flex items-center gap-3">
              {profileId ? (
                <span className="ml-4 text-muted font-semibold text-sm">
                  Current Profile: {profileId}
                </span>
              ) : (
                <button
                  onClick={handleAddProfile}
                  className="primary-btn btn-green ml-4 flex items-center"
                  disabled={addingProfile}
                >
                  {addingProfile ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : null}
                  {addingProfile ? "Importing..." : "Add Profile"}
                </button>
              )}
              {/* Rescrape Inventory Button */}
              {profileId && (
                <button
                  onClick={handleRescrapeInventory}
                  className="primary-btn btn-blue"
                  disabled={rescraping}
                  title="Rescrape your Steam inventory to update items"
                >
                  {rescraping ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <RefreshIcon fontSize="inherit" />
                  )}
                  {rescraping ? "Rescraping..." : "Rescrape Inventory"}
                </button>
              )}

              {/* Delete Inventory */}
              {items.length > 0 && (
                <button
                  onClick={() => setDeleteAllConfirm(true)}
                  className="primary-btn btn-red"
                  disabled={deletingAll}
                >
                  {deletingAll ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <DeleteIcon fontSize="inherit" />
                  )}
                  Clear Inventory
                </button>
              )}
              {addProfileNote && (
                <span className="ml-4 text-xs text-muted">
                  {addProfileNote}
                </span>
              )}
            </div>
            {/* Import Steam Inventory Modal */}
            {showImportModal && (
              <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
                <div className="bg-secondary rounded-lg p-6 max-w-md w-full mx-4 border border-primary">
                  <h3 className="text-xl font-semibold text-primary mb-4">
                    Import Steam Inventory
                  </h3>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-muted mb-2">
                      Steam ID
                    </label>
                    <input
                      type="text"
                      value={steamIdInput}
                      onChange={(e) => setSteamIdInput(e.target.value)}
                      placeholder="Enter your Steam ID..."
                      className="input"
                    />
                  </div>

                  {/* Import Options */}
                  <div className="mb-4 space-y-3">
                    <h4 className="text-sm font-medium text-muted">
                      Import Options
                    </h4>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={includePrices}
                        onChange={(e) => setIncludePrices(e.target.checked)}
                        className="w-4 h-4 text-blue bg-tertiary border-primary/20 rounded focus:ring-blue"
                      />
                      <div className="flex flex-col">
                        <span className="text-sm text-primary">
                          Include Prices
                        </span>
                        <span className="text-xs text-muted">
                          Scrape current market prices (can be updated later)
                        </span>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={includeFloats}
                        onChange={(e) => setIncludeFloats(e.target.checked)}
                        className="w-4 h-4 text-blue bg-tertiary border-primary/20 rounded focus:ring-blue"
                      />
                      <div className="flex flex-col">
                        <span className="text-sm text-primary">
                          Include Float & Pattern
                        </span>
                        <span className="text-xs text-muted">
                          Fetch float values and paint seeds from CSFloat (can
                          be updated later)
                        </span>
                      </div>
                    </label>
                  </div>
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setShowImportModal(false)}
                      className="px-4 py-2 text-sm rounded bg-gray-700 text-white hover:bg-gray-600"
                      disabled={addingProfile}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleImportConfirm}
                      className="px-4 py-2 text-sm bg-green-600 rounded text-white hover:bg-green-500 flex items-center"
                      disabled={addingProfile || !steamIdInput}
                    >
                      {addingProfile && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      )}
                      Import
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Total Items */}
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">Total Items</div>
              <div className="text-2xl font-bold text-primary">
                {filteredItems.length}
              </div>
            </div>

            {/* Total Value */}
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">Total Value</div>
              <div className="text-2xl font-bold text-primary">
                €
                {filteredItems
                  .reduce((sum, item) => sum + (item.current_price || 0), 0)
                  .toFixed(2)}
              </div>
            </div>

            {/* Total Invested */}
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">
                Total Investment
              </div>
              <div className="text-2xl font-bold text-primary">
                €
                {filteredItems
                  .reduce((sum, item) => sum + (item.price_bought || 0), 0)
                  .toFixed(2)}
              </div>
            </div>

            {/* Profit/Loss Summary */}
            {(() => {
              const totalValue = filteredItems.reduce(
                (sum, item) => sum + (item.current_price || 0),
                0
              );
              const totalInvested = filteredItems.reduce(
                (sum, item) => sum + (item.price_bought || 0),
                0
              );
              const profitLoss = totalValue - totalInvested;
              const profitLossPercentage =
                totalInvested > 0 ? (profitLoss / totalInvested) * 100 : 0;

              return (
                <div className="stats-card">
                  <div className="text-xs font-bold text-muted">Total P&L</div>
                  <div
                    className={`text-2xl font-bold ${
                      profitLoss >= 0 ? "text-green" : "text-red"
                    }`}
                  >
                    {profitLoss >= 0 ? "+" : ""}€
                    {Math.abs(profitLoss).toFixed(2)}
                    <div className="text-xs font-normal">
                      ({profitLossPercentage >= 0 ? "+" : ""}
                      {profitLossPercentage.toFixed(2)}%)
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      </div>

      {/* Steam Items Section */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-primary">
              Steam Items ({filteredItems.length})
            </h2>

            <div className="flex gap-2">
              {/* Update Prices Button */}
              {items.length > 0 && (
                <button
                  onClick={handleUpdatePrices}
                  className="primary-btn btn-black"
                  disabled={updatingPrices || updatingFloats}
                >
                  {updatingPrices ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <RefreshIcon fontSize="inherit" />
                  )}
                  {updatingPrices ? "Updating..." : "Update Prices"}
                </button>
              )}

              {/* Update Floats Button */}
              {items.length > 0 && (
                <button
                  onClick={handleUpdateFloats}
                  className="primary-btn btn-black"
                  disabled={updatingFloats || updatingPrices}
                >
                  {updatingFloats ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <RefreshIcon fontSize="inherit" />
                  )}
                  {updatingFloats ? "Updating..." : "Update Float & Pattern"}
                </button>
              )}

              {/* Filter Toggle Button */}
              <button
                onClick={clearFilters}
                className="primary-btn btn-black"
                disabled={
                  !nameFilter &&
                  !rarityFilter &&
                  !minPrice &&
                  !maxPrice &&
                  sortBy === "name" &&
                  sortOrder === "asc"
                }
              >
                <DeleteIcon fontSize="inherit" />
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="">
          <div className="p-4">
            {/* Filter Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
              {/* Name Filter */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Item Name
                </label>
                <input
                  type="text"
                  value={nameFilter}
                  onChange={(e) => setNameFilter(e.target.value)}
                  placeholder="Filter by name..."
                  className="input w-full"
                />
              </div>

              {/* Rarity Filter */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Rarity
                </label>
                <select
                  value={rarityFilter}
                  onChange={(e) => setRarityFilter(e.target.value)}
                  className="select w-full"
                >
                  <option value="">All Rarities</option>
                  {uniqueRarities.map((rarity) => (
                    <option key={rarity} value={rarity}>
                      {rarity}
                    </option>
                  ))}
                </select>
              </div>
              {/* Sort By */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) =>
                    setSortBy(
                      e.target.value as "name" | "rarity" | "price" | "profit"
                    )
                  }
                  className="select w-full"
                >
                  <option value="name">Name</option>
                  <option value="rarity">Rarity</option>
                  <option value="price">Current Price</option>
                  <option value="profit">Profit/Loss</option>
                </select>
              </div>

              {/* Sort Order */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Sort Order
                </label>
                <select
                  value={sortOrder}
                  onChange={(e) =>
                    setSortOrder(e.target.value as "asc" | "desc")
                  }
                  className="select w-full"
                >
                  <option value="asc">
                    {sortBy === "name"
                      ? "A → Z"
                      : sortBy === "rarity"
                      ? "Low → High"
                      : sortBy === "price"
                      ? "Low → High"
                      : "Loss → Profit"}
                  </option>
                  <option value="desc">
                    {sortBy === "name"
                      ? "Z → A"
                      : sortBy === "rarity"
                      ? "High → Low"
                      : sortBy === "price"
                      ? "High → Low"
                      : "Profit → Loss"}
                  </option>
                </select>
              </div>
            </div>

            {/* Active Filters Display */}
            {(nameFilter ||
              rarityFilter ||
              sortBy !== "name" ||
              sortOrder !== "asc") && (
              <div className="mt-3 pt-3 border-t border-primary/20">
                <div className="flex flex-wrap gap-2">
                  <span className="text-sm font-bold text-muted">
                    Active filters:
                  </span>
                  {nameFilter && (
                    <span className="px-2 py-1 bg-blue/20 text-blue text-xs rounded">
                      Name: "{nameFilter}"
                    </span>
                  )}
                  {rarityFilter && (
                    <span className="px-2 py-1 bg-purple/20 text-purple text-xs rounded">
                      Rarity: {rarityFilter}
                    </span>
                  )}
                  {(sortBy !== "name" || sortOrder !== "asc") && (
                    <span className="px-2 py-1 bg-orange/20 text-orange text-xs rounded">
                      Sort: {sortBy} ({sortOrder === "asc" ? "↑" : "↓"})
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="card-body">
          {filteredItems.length === 0 ? (
            <div className="text-center py-8">
              <SportsEsportsIcon className="w-16 h-16 text-muted mx-auto mb-4" />
              {items.length === 0 ? (
                <>
                  <p className="text-secondary">No Steam items found</p>
                  <p className="text-muted text-sm">
                    Use the Steam scraper to import your inventory
                  </p>
                </>
              ) : (
                <>
                  <p className="text-secondary">No items match your filters</p>
                  <p className="text-muted text-sm">
                    Try adjusting your filter criteria
                  </p>
                </>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {filteredItems.map((item) => {
                const itemId = item._id || item.id?.toString() || "";
                const rarityColor = getRarityColor(item.rarity);

                return (
                  <div
                    key={itemId}
                    className="bg-tertiary shadow-lg inset-shadow-md rounded-lg border overflow-hidden transition-colors flex flex-col h-full"
                    style={{
                      background: `linear-gradient(to bottom, ${rarityColor}40 0%, transparent 60%), var(--bg-secondary)`,
                      borderColor: `${rarityColor}75`,
                    }}
                  >
                    {/* Item Image with Gradient Background */}
                    <div className="flex items-center justify-center pt-10 pb-0 relative">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-2/3 h-2/3 aspect-square object-contain"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <SportsEsportsIcon className="w-8 h-8 text-muted" />
                      )}

                      {/* Item Name at Top */}
                      <div className="absolute top-2 left-2 right-2">
                        <h3 className="font-semibold text-sm text-primary rounded px-2 py-1 line-clamp-2">
                          {item.name}
                        </h3>
                      </div>
                    </div>

                    {/* Item Details and Actions - flex-grow to push actions to bottom */}
                    <div className="flex flex-col flex-grow p-4">
                      <div className="flex items-center w-full my-1">
                        <span className="flex-grow border-t border-muted/30" />
                        <span className="px-2 text-[8px] text-muted/30 font-medium whitespace-nowrap">
                          Prices
                        </span>
                        <span className="flex-grow border-t border-muted/30" />
                      </div>

                      {/* Prices */}
                      <div className="space-y-2 mb-3">
                        <div className="flex justify-between items-end text-xs">
                          <span className="text-muted font-medium">
                            Current:
                          </span>
                          <span className="font-medium">
                            €{item.current_price?.toFixed(2) || "0.00"}
                          </span>
                        </div>

                        {/* Bought Price - Editable */}
                        <div className="flex justify-between text-xs">
                          <span className="text-muted font-medium">
                            Bought:
                          </span>
                          {editingItem === itemId ? (
                            <div className="flex items-center justify-center">
                              <input
                                type="number"
                                value={editPrice}
                                onChange={(e) => setEditPrice(e.target.value)}
                                className="max-w-12 h-5 text-xs text-right px-1 border border-primary rounded bg-secondary text-primary mr-1"
                                step="0.01"
                                min="0"
                              />
                              <button
                                onClick={() => handleSavePrice(itemId)}
                                className="flex justify-center items-center duration-200 w-5 h-5 hover:text-green hover:bg-green/20 bg-secondary border border-primary rounded"
                              >
                                <CheckIcon fontSize="inherit" />
                              </button>
                            </div>
                          ) : (
                            <span
                              className="text-secondary font-medium"
                              onClick={() => handleEditPrice(item)}
                            >
                              €{item.price_bought?.toFixed(2) || "0.00"}
                            </span>
                          )}
                        </div>

                        {/* Overpay - Editable */}
                        <div className="flex justify-between text-xs">
                          <span className="text-muted font-medium">
                            Overpay:
                          </span>
                          {editingOverpayItem === itemId ? (
                            <div className="flex items-center justify-center">
                              <input
                                type="number"
                                value={editOverpay}
                                onChange={(e) => setEditOverpay(e.target.value)}
                                className="max-w-12 h-5 text-xs text-right px-1 border border-primary rounded bg-secondary text-primary mr-1"
                                step="0.01"
                                min="0"
                              />
                              <button
                                onClick={() => handleSaveOverpay(itemId)}
                                className="flex justify-center items-center duration-200 w-5 h-5 hover:text-green hover:bg-green/20 bg-secondary border border-primary rounded"
                              >
                                <CheckIcon fontSize="inherit" />
                              </button>
                            </div>
                          ) : (
                            <span
                              className="text-secondary font-medium"
                              onClick={() => handleEditOverpay(item)}
                            >
                              €{item.overpay?.toFixed(2) || "0.00"}
                            </span>
                          )}
                        </div>

                        {/* Profit/Loss */}
                        {(() => {
                          const currentPrice = item.current_price || 0;
                          const boughtPrice = item.price_bought || 0;
                          const overpay = item.overpay || 0;
                          const profitLoss =
                            currentPrice - boughtPrice + overpay;

                          return (
                            <div className="flex justify-between text-xs">
                              <span className="text-muted font-medium">
                                P/L:
                              </span>
                              <span
                                className={
                                  profitLoss >= 0
                                    ? "text-green-500 font-medium"
                                    : "text-red-500 font-medium"
                                }
                              >
                                {profitLoss >= 0 ? "+" : ""}€
                                {profitLoss.toFixed(2)}
                              </span>
                            </div>
                          );
                        })()}

                        <div className="flex items-center w-full my-1">
                          <span className="flex-grow border-t border-muted/30" />
                          <span className="px-2 text-[8px] text-muted/30 font-medium whitespace-nowrap">
                            Item Infos
                          </span>
                          <span className="flex-grow border-t border-muted/30" />
                        </div>
                        <div className="flex justify-between items-end text-xs">
                          <span className="text-muted font-medium">
                            Rarity:
                          </span>
                          <span
                            className="font-medium"
                            style={{ color: rarityColor }}
                          >
                            {item.rarity}
                          </span>
                        </div>

                        <div className="flex justify-between items-end text-xs">
                          <span className="text-muted font-medium">
                            Condition:
                          </span>
                          <span className="font-medium">
                            {item.condition && item.condition !== "N/A" ? (
                              <>{item.condition}</>
                            ) : (
                              <>-</>
                            )}
                          </span>
                        </div>

                        {/* Float Value - Show for items that can have float */}
                        {item.float_value && item.float_value > 0 ? (
                          <div className="text-xs text-muted mb-2">
                            Float: {item.float_value.toFixed(6)}
                          </div>
                        ) : null}

                        {/* Paint Seed - Show for items that have pattern */}
                        {item.paint_seed && item.paint_seed > 0 ? (
                          <div className="text-xs text-muted mb-2">
                            Pattern: {item.paint_seed}
                          </div>
                        ) : null}
                      </div>

                      {/* Spacer to push actions to bottom */}
                      <div className="flex-grow" />

                      {/* Action Buttons */}
                      <div className="flex justify-between gap-2 mt-1">
                        <button
                          onClick={() => handleEditPrice(item)}
                          className="primary-btn btn-black flex-1"
                          disabled={editingItem === itemId}
                        >
                          <EditIcon fontSize="inherit" className="mr-1" />
                          Edit
                        </button>

                        {/* Inspect In-Game Button */}
                        <button
                          onClick={() =>
                            window.open(
                              `steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S${
                                item.steam_id || ""
                              }A${item.asset_id || ""}D7334057344902390015`,
                              "_blank"
                            )
                          }
                          className="primary-btn btn-black flex-1"
                          title="Inspect in CS2"
                        >
                          <SearchIcon fontSize="inherit" className="mr-1" />
                          Inspect
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Delete All Confirmation Dialog */}
      {deleteAllConfirm && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-secondary rounded-lg p-6 max-w-md w-full mx-4 border border-primary">
            <div className="flex items-center mb-4">
              <WarningIcon className="w-8 h-8 text-red-500 mr-3" />
              <h3 className="text-xl font-semibold text-primary">
                Clear Steam Inventory
              </h3>
            </div>
            <div className="space-y-3 mb-6">
              <p className="text-secondary">
                Are you sure you want to delete{" "}
                <strong>ALL {items.length} items</strong> from your Steam
                inventory?
              </p>
              <div className="bg-red/10 border border-red/20 rounded p-3">
                <p className="text-red text-sm font-medium">
                  ⚠️ This action cannot be undone!
                </p>
                <p className="text-red text-sm">
                  All Steam items will be permanently removed.
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteAllConfirm(false)}
                className="px-4 py-2 text-sm rounded bg-gray-700 text-white hover:bg-gray-600 disabled:opacity-50"
                disabled={deletingAll}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAllItems}
                className="px-4 py-2 text-sm bg-red-600 rounded text-white hover:bg-red-500 flex items-center disabled:opacity-50"
                disabled={deletingAll}
              >
                {deletingAll && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                )}
                {deletingAll ? "Deleting..." : "Clear All Items"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
