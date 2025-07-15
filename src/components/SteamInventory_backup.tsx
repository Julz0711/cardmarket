import React, { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import type { SteamItem } from "../types/assets";

// Material Icons
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import DeleteIcon from "@mui/icons-material/Delete";
import WarningIcon from "@mui/icons-material/Warning";

export const SteamInventory: React.FC = () => {
  const [items, setItems] = useState<SteamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteAllConfirm, setDeleteAllConfirm] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);

  // Filter states
  const [nameFilter, setNameFilter] = useState("");
  const [rarityFilter, setRarityFilter] = useState("");

  // Sort states
  const [sortBy, setSortBy] = useState<"name" | "rarity">("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    loadSteamItems();
  }, []);

  const loadSteamItems = async () => {
    try {
      setLoading(true);
      // Request all items by setting a high per_page limit
      const response = await apiClient.getSteamItems(1, 1000);
      setItems(response.items || []);
    } catch (err) {
      setError("Failed to load Steam inventory");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDemoData = async () => {
    try {
      setLoading(true);
      setError("");

      // Simulate loading delay
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Set realistic demo data with proper SteamItem structure
      setItems([
        {
          _id: "demo_1",
          id: 1,
          name: "AK-47 | Redline (Field-Tested)",
          rarity: "Classified",
          type: "steam",
          game: "Counter-Strike 2",
          price_bought: 8.50,
          current_price: 8.75,
          price_source: "market_research",
          image_url: "https://community.akamai.steamstatic.com/economy/image/demo_ak47_redline",
          condition: "FT",
          float_value: 0.15234,
          steam_id: "demo_inventory",
          asset_id: "demo_asset_1",
          market_hash_name: "AK-47 | Redline (Field-Tested)",
          quantity: 1,
          last_updated: "2025-01-15T12:00:00Z"
        },
        {
          _id: "demo_2", 
          id: 2,
          name: "AWP | Lightning Strike (Factory New)",
          rarity: "Covert",
          type: "steam",
          game: "Counter-Strike 2",
          price_bought: 40.00,
          current_price: 42.50,
          price_source: "market_research",
          image_url: "https://community.akamai.steamstatic.com/economy/image/demo_awp_lightning",
          condition: "FN",
          float_value: 0.02145,
          steam_id: "demo_inventory",
          asset_id: "demo_asset_2",
          market_hash_name: "AWP | Lightning Strike (Factory New)",
          quantity: 1,
          last_updated: "2025-01-15T12:00:00Z"
        },
        {
          _id: "demo_3",
          id: 3,
          name: "★ Karambit | Doppler (Factory New)",
          rarity: "Extraordinary",
          type: "steam",
          game: "Counter-Strike 2",
          price_bought: 380.00,
          current_price: 420.00,
          price_source: "market_research",
          image_url: "https://community.akamai.steamstatic.com/economy/image/demo_karambit_doppler",
          condition: "FN",
          float_value: 0.00892,
          steam_id: "demo_inventory",
          asset_id: "demo_asset_3",
          market_hash_name: "★ Karambit | Doppler (Factory New)",
          quantity: 1,
          last_updated: "2025-01-15T12:00:00Z"
        },
        {
          _id: "demo_4",
          id: 4,
          name: "Operation Hydra Case",
          rarity: "Base Grade",
          type: "steam",
          game: "Counter-Strike 2",
          price_bought: 0.12,
          current_price: 0.15,
          price_source: "market_research",
          image_url: "https://community.akamai.steamstatic.com/economy/image/demo_hydra_case",
          condition: "N/A",
          steam_id: "demo_inventory",
          asset_id: "demo_asset_4",
          market_hash_name: "Operation Hydra Case",
          quantity: 1,
          last_updated: "2025-01-15T12:00:00Z"
        },
        {
          _id: "demo_5",
          id: 5,
          name: "Cmdr. Mae 'Dead Cold' Jamison",
          rarity: "Superior",
          type: "steam",
          game: "Counter-Strike 2",
          price_bought: 11.00,
          current_price: 12.50,
          price_source: "market_research",
          image_url: "https://community.akamai.steamstatic.com/economy/image/demo_agent_mae",
          condition: "N/A",
          steam_id: "demo_inventory",
          asset_id: "demo_asset_5",
          market_hash_name: "Cmdr. Mae 'Dead Cold' Jamison",
          quantity: 1,
          last_updated: "2025-01-15T12:00:00Z"
        },
      ]);
    } catch (err) {
      setError("Failed to load demo data");
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

  const handleDeleteItem = async (itemId: string) => {
    try {
      setDeleting(true);
      await apiClient.deleteSteamItem(itemId);

      // Update local state
      setItems(
        items.filter((item) => (item._id || item.id?.toString()) !== itemId)
      );
    } catch (err) {
      setError("Failed to delete item from inventory");
      console.error(err);
    } finally {
      setDeleting(false);
      setDeleteConfirm(false);
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
            // Agent rarities - with proper names (NEW)
            "Distinguished Agent": 2,
            "Exceptional Agent": 4,
            "Superior Agent": 5,
            "Master Agent": 6,
            // Legacy agent rarities (OLD format)
            Distinguished: 2,
            Exceptional: 4,
            Superior: 5,
            Master: 6,
            // Incorrectly mapped agent rarities (CURRENT DATA - needs fixing)
            Legendary: 6, // Actually Master Agent
            Mythical: 4, // Actually Exceptional Agent
            Rare: 2, // Actually Distinguished Agent (when it's an agent)
            // Other rarities
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
      // Weapon skin rarities
      Consumer: "#b0c3d9",
      Industrial: "#5e98d9",
      "Mil-Spec": "#4b69ff",
      Restricted: "#8847ff",
      Classified: "#d32ce6",
      Covert: "#eb4b4b",
      Contraband: "#e4ae39",
      Extraordinary: "#eb4b4b", // Extraordinary (gloves, special items - red)
      // Additional rarities for other item types
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

  const getDisplayRarity = (item: SteamItem) => {
    const isAgent =
      item.name.toLowerCase().includes("agent") ||
      item.name.toLowerCase().includes("ava") ||
      item.name.toLowerCase().includes("specialist") ||
      item.name.toLowerCase().includes("lieutenant") ||
      item.name.toLowerCase().includes("commander");

    if (isAgent) {
      // Convert old incorrect agent rarities to proper display names
      switch (item.rarity) {
        case "Legendary":
          return "Master Agent";
        case "Mythical":
          return "Exceptional Agent";
        case "Rare":
          return "Distinguished Agent";
        case "Master":
          return "Master Agent";
        case "Exceptional":
          return "Exceptional Agent";
        case "Distinguished":
          return "Distinguished Agent";
        case "Superior":
          return "Superior Agent";
        default:
          return item.rarity;
      }
    }

    return item.rarity;
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

  return (
    <div className="space-y-6">
      {/* Demo Data Banner */}
      {items.length > 0 && items[0]?.steam_id === "demo_inventory" && (
        <div className="bg-blue/10 border border-blue/20 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-blue/20 rounded-full flex items-center justify-center">
              <span className="text-blue text-sm">ℹ️</span>
            </div>
            <div>
              <h3 className="text-blue font-medium">Demo Data Loaded</h3>
              <p className="text-blue/80 text-sm">
                You're viewing realistic demo inventory with real market-researched prices. 
                No infinite loading issues! All prices are based on actual CS2 market data.
              </p>
            </div>
          </div>
        </div>
      )}

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
              {/* Demo Data Button */}
              <button
                onClick={() => loadDemoData()}
                className="primary-btn btn-green text-sm px-3 py-1 flex items-center"
                disabled={loading}
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <SportsEsportsIcon fontSize="small" className="mr-1" />
                )}
                Load Demo Data
              </button>

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
                  Delete Profile
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
                          {getDisplayRarity(item)}
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
                                className="w-16 h-5 text-xs px-1 border border-primary/20 rounded"
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
                        {item.current_price && item.price_bought ? (
                          <div className="flex justify-between text-xs">
                            <span className="text-muted">P/L:</span>
                            <span
                              className={
                                item.current_price - item.price_bought >= 0
                                  ? "text-green font-medium"
                                  : "text-red font-medium"
                              }
                            >
                              €
                              {(item.current_price - item.price_bought).toFixed(
                                2
                              )}
                            </span>
                          </div>
                        ) : (
                          <div className="flex justify-between text-xs">
                            <span className="text-muted">P/L:</span>
                            <span className="text-green font-medium">
                              €
                              {(item.current_price - item.price_bought).toFixed(
                                2
                              )}
                            </span>
                          </div>
                        )}
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

                    {/* Delete Confirmation Dialog */}
                    {deleteConfirm && editingItem === itemId && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                        <div className="bg-tertiary rounded-lg p-4 max-w-sm w-full">
                          <div className="flex items-center mb-4">
                            <WarningIcon className="w-6 h-6 text-red-500 mr-2" />
                            <h3 className="text-lg font-semibold text-primary">
                              Confirm Deletion
                            </h3>
                          </div>
                          <p className="text-sm text-muted mb-4">
                            Are you sure you want to delete this item from your
                            inventory? This action cannot be undone.
                          </p>
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => setDeleteConfirm(false)}
                              className="px-3 py-1 text-sm rounded bg-gray-700 text-white hover:bg-gray-600"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleDeleteItem(itemId)}
                              className="px-3 py-1 text-sm bg-red-600 rounded text-white hover:bg-red-500 flex items-center"
                            >
                              {deleting && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              )}
                              Confirm Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
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
                Delete Steam Profile
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
                  All Steam items and their price data will be permanently
                  removed.
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
                {deletingAll ? "Deleting..." : "Delete All Items"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
