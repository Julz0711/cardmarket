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
import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";

export const SteamInventory: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState<SteamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteAllConfirm, setDeleteAllConfirm] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);
  const [updatingPrices, setUpdatingPrices] = useState(false);

  // Edit price states
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState("");

  // Add Profile states
  const [addingProfile, setAddingProfile] = useState(false);
  const [addProfileNote, setAddProfileNote] = useState("");
  const [showImportModal, setShowImportModal] = useState(false);
  const [steamIdInput, setSteamIdInput] = useState("");

  // Filter states
  const [nameFilter, setNameFilter] = useState("");
  const [rarityFilter, setRarityFilter] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  // Sort states
  // Default: sort by current price, descending (high to low)
  const [sortBy, setSortBy] = useState<"name" | "rarity" | "price" | "profit">("price");
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
    setAddProfileNote("Importing Steam inventory and scraping prices. This may take a minute...");
    setError("");
    setShowImportModal(false);
    try {
      // Use the correct scraping endpoint that saves to database
      const scrapeResponse = await apiClient.scrapeSteam({
        steam_id: steamIdInput,
        headless: true,
        include_floats: true
      });
      
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
    } catch (err: any) {
      if (err?.message?.includes('401') || err?.status === 401) {
        setError("Authentication required. Please log in to view your Steam inventory.");
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

  const handleCancelEdit = () => {
    setEditingItem(null);
    setEditPrice("");
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
      if (response.status === "warning" || response.details.updated.length === 0) {
        setError("No prices could be updated. SkinSearch may be down or blocking requests.");
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
            Common: 1,
            Uncommon: 2,
            Immortal: 7,
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
      // Agent rarities - NEW proper names (after rescraping)
      "Master Agent": "#eb4b4b", // Master Agent (red)
      "Superior Agent": "#d32ce6", // Superior Agent (pink)
      "Exceptional Agent": "#8847ff", // Exceptional Agent (purple)
      "Distinguished Agent": "#4b69ff", // Distinguished Agent (blue)
      // Agent rarities - OLD format (before rescraping) - TEMPORARY FIXES
      Master: "#eb4b4b", // Will show as Master Agent after rescraping
      Superior: "#d32ce6", // Will show as Superior Agent after rescraping
      Exceptional: "#8847ff", // Will show as Exceptional Agent after rescraping
      Distinguished: "#4b69ff", // Will show as Distinguished Agent after rescraping
      // Legacy agent rarities mapped incorrectly - FIXES for current data
      Legendary: "#eb4b4b", // Actually Master Agent (red) - WRONG in current data
      Mythical: "#8847ff", // Actually Exceptional Agent (purple) - WRONG in current data
      Rare: "#4b69ff", // Actually Distinguished Agent (blue) - WRONG in current data
      Immortal: "#e4ae39",
      // CS2 Agent rarity variations
      "★": "#ffd700", // Special symbol for some agents
      "★ Master Agent": "#eb4b4b",
      "★ Superior Agent": "#d32ce6",
      "★ Exceptional Agent": "#8847ff",
      "★ Distinguished Agent": "#4b69ff",
      // Quality levels
      Normal: "#b0b0b0",
      Genuine: "#4b69ff",
      Vintage: "#476291",
      Unusual: "#8650ac",
      Unique: "#ffd700",
      Strange: "#cf6a32",
      Haunted: "#38f3ab",
      "Collector's": "#aa0000",
      Decorated: "#ffd700",
    };

    // Debug log to see what rarity values we're getting
    if (!colors[rarity]) {
      console.log(`Unknown rarity: "${rarity}"`);
    }

    return colors[rarity] || "#b0b0b0";
  };

  const getConditionColor = (condition: string) => {
    const colors: Record<string, string> = {
      FN: "text-gray-200",
      MW: "text-gray-200",
      FT: "text-gray-200",
      WW: "text-gray-200",
      BS: "text-gray-200",
    };
    return colors[condition] || "text-gray-500";
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
              <h2 className="text-xl font-semibold text-primary">Steam Inventory</h2>
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
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 stats-icon-green rounded-lg flex items-center justify-center">
              <SportsEsportsIcon fontSize="small" className="text-primary" />
            </div>
            <h2 className="text-xl font-semibold text-primary">
              Steam Inventory Summary
            </h2>
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
            {addProfileNote && (
              <span className="ml-4 text-xs text-muted">{addProfileNote}</span>
            )}
      {/* Import Steam Inventory Modal */}
      {showImportModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-secondary rounded-lg p-6 max-w-md w-full mx-4 border border-primary">
            <h3 className="text-xl font-semibold text-primary mb-4">Import Steam Inventory</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-muted mb-2">Steam ID</label>
              <input
                type="text"
                value={steamIdInput}
                onChange={(e) => setSteamIdInput(e.target.value)}
                placeholder="Enter your Steam ID..."
                className="w-full px-3 py-2 border border-primary/20 rounded bg-tertiary text-primary"
              />
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
              <div className="text-sm font-medium text-secondary">
                Total Items
              </div>
              <div className="text-2xl font-bold text-primary">
                {filteredItems.length}
              </div>
            </div>

            {/* Total Value */}
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Value
              </div>
              <div className="text-2xl font-bold text-primary">
                €
                {filteredItems
                  .reduce((sum, item) => sum + (item.current_price || 0), 0)
                  .toFixed(2)}
              </div>
            </div>

            {/* Total Invested */}
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
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
                  <div className="text-sm font-medium text-secondary">
                    Total P&L
                  </div>
                  <div
                    className={`text-2xl font-bold ${
                      profitLoss >= 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {profitLoss >= 0 ? "+" : ""}€
                    {Math.abs(profitLoss).toFixed(2)}
                    <div className="text-sm font-normal">
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
                  className="primary-btn btn-blue text-sm px-3 py-1 flex items-center"
                  disabled={updatingPrices}
                >
                  {updatingPrices ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <SearchIcon fontSize="small" className="mr-1" />
                  )}
                  {updatingPrices ? "Updating..." : "Update Prices"}
                </button>
              )}

              {/* Delete All Button */}
              {items.length > 0 && (
                <button
                  onClick={() => setDeleteAllConfirm(true)}
                  className="primary-btn btn-red text-sm px-3 py-1 flex items-center"
                  disabled={deletingAll}
                >
                  {deletingAll ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <DeleteIcon fontSize="small" className="mr-1" />
                  )}
                  Clear Inventory
                </button>
              )}

              {/* Filter Toggle Button */}
              <button
                onClick={clearFilters}
                className="primary-btn btn-secondary text-sm px-3 py-1"
                disabled={
                  !nameFilter &&
                  !rarityFilter &&
                  !minPrice &&
                  !maxPrice &&
                  sortBy === "name" &&
                  sortOrder === "asc"
                }
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="border-b border-primary/20 bg-secondary/30">
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
                  className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary placeholder-muted"
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
                  className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary"
                >
                  <option value="">All Rarities</option>
                  {uniqueRarities.map((rarity) => (
                    <option key={rarity} value={rarity}>
                      {rarity}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Price Filter */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Min Price (€)
                </label>
                <input
                  type="number"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary placeholder-muted"
                />
              </div>

              {/* Max Price Filter */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Max Price (€)
                </label>
                <input
                  type="number"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  placeholder="999.99"
                  step="0.01"
                  min="0"
                  className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary placeholder-muted"
                />
              </div>
            </div>

            {/* Sort Controls */}
            <div className="border-t border-primary/20 pt-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                    className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary"
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
                    className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary"
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
            </div>

            {/* Active Filters Display */}
            {(nameFilter ||
              rarityFilter ||
              minPrice ||
              maxPrice ||
              sortBy !== "name" ||
              sortOrder !== "asc") && (
              <div className="mt-3 pt-3 border-t border-primary/20">
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-muted">Active filters:</span>
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
                  {minPrice && (
                    <span className="px-2 py-1 bg-green/20 text-green text-xs rounded">
                      Min: €{minPrice}
                    </span>
                  )}
                  {maxPrice && (
                    <span className="px-2 py-1 bg-green/20 text-green text-xs rounded">
                      Max: €{maxPrice}
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
                    className="bg-tertiary rounded-lg border-[1px] border-[var(--border-primary)] overflow-hidden hover:border-primary/40 transition-colors"
                  >
                    {/* Item Image with Gradient Background */}
                    <div
                      className="bg-secondary/50 flex items-center justify-center pt-8 pb-2 relative"
                      style={{
                        background: `linear-gradient(to top, ${rarityColor}40 0%, transparent 60%), var(--bg-secondary)`,
                      }}
                    >
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

                    {/* Item Details */}
                    <div className="p-3">
                      {/* Rarity & Condition */}
                      <div className="flex justify-between items-center mb-4">
                        <span
                          className="text-sm font-medium"
                          style={{ color: rarityColor }}
                        >
                          {item.rarity}
                        </span>
                        {item.condition && item.condition !== "N/A" && (
                          <span
                            className={`text-sm font-medium ${getConditionColor(
                              item.condition
                            )}`}
                          >
                            {item.condition}
                          </span>
                        )}
                      </div>

                      {/* Float Value - Show for items that can have float */}
                      {item.float_value && item.float_value > 0 ? (
                        <div className="text-xs text-muted mb-2">
                          Float: {item.float_value.toFixed(6)}
                        </div>
                      ) : null}

                      {/* Prices */}
                      <div className="space-y-1 mb-3">
                        <div className="flex justify-between items-end text-xs">
                          <span className="text-muted">Current:</span>
                          <span className="text-white font-medium text-2xl">
                            €{item.current_price?.toFixed(2) || "0.00"}
                          </span>
                        </div>

                        {/* Bought Price - Editable */}
                        <div className="flex justify-between text-xs">
                          <span className="text-muted">Bought:</span>
                          {editingItem === itemId ? (
                            <div className="flex items-center gap-1">
                              <input
                                type="number"
                                value={editPrice}
                                onChange={(e) => setEditPrice(e.target.value)}
                                className="w-16 h-5 text-xs px-1 border border-primary/20 rounded bg-tertiary text-primary"
                                step="0.01"
                                min="0"
                              />
                              <button
                                onClick={() => handleSavePrice(itemId)}
                                className="p-1 text-green hover:bg-green/20 rounded"
                              >
                                <SaveIcon fontSize="inherit" />
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="p-1 text-red hover:bg-red/20 rounded"
                              >
                                <CancelIcon fontSize="inherit" />
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

                        {/* Profit/Loss */}
                        {(() => {
                          const currentPrice = item.current_price || 0;
                          const boughtPrice = item.price_bought || 0;
                          const profitLoss = currentPrice - boughtPrice;

                          return (
                            <div className="flex justify-between text-xs">
                              <span className="text-muted">P/L:</span>
                              <span
                                className={
                                  profitLoss >= 0
                                    ? "text-green font-medium"
                                    : "text-red font-medium"
                                }
                              >
                                {profitLoss >= 0 ? "+" : ""}€
                                {profitLoss.toFixed(2)}
                              </span>
                            </div>
                          );
                        })()}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-between gap-1">
                        <button
                          onClick={() => handleEditPrice(item)}
                          className="primary-btn btn-black text-xs px-2 py-1 flex-1"
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
                          className="primary-btn btn-black text-xs px-2 py-1 flex-1"
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
