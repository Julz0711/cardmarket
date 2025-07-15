import React, { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import type { SteamItem } from "../types/assets";

// Material Icons
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import DeleteIcon from "@mui/icons-material/Delete";
import WarningIcon from "@mui/icons-material/Warning";
import SearchIcon from "@mui/icons-material/Search";

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
      const response = await apiClient.getSteamItems(1, 1000);
      setItems(response.items || []);
    } catch (err) {
      setError("Failed to load Steam inventory");
      console.error(err);
    } finally {
      setLoading(false);
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
            Rare: 3,
            Mythical: 4,
            Legendary: 5,
            Immortal: 7,
          };
          const aRarity =
            rarityOrder[a.rarity as keyof typeof rarityOrder] || 0;
          const bRarity =
            rarityOrder[b.rarity as keyof typeof rarityOrder] || 0;
          compareValue = aRarity - bRarity;
          break;
      }

      return sortOrder === "desc" ? -compareValue : compareValue;
    });

  // Get unique rarities for filter dropdown
  const uniqueRarities = [...new Set(items.map((item) => item.rarity))].sort();

  const clearFilters = () => {
    setNameFilter("");
    setRarityFilter("");
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
      Distinguished: "#4b69ff",
      Exceptional: "#8847ff",
      Superior: "#d32ce6",
      Master: "#eb4b4b",
      Rare: "#8847ff",
      Mythical: "#d32ce6",
      Legendary: "#eb4b4b",
      Immortal: "#e4ae39",
    };

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
              Steam Inventory
            </h2>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Total Items */}
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Items
              </div>
              <div className="text-2xl font-bold text-primary">
                {filteredItems.length}
              </div>
            </div>

            {/* Unique Items */}
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Unique Items
              </div>
              <div className="text-2xl font-bold text-primary">
                {new Set(filteredItems.map(item => item.name)).size}
              </div>
            </div>
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

              {/* Sort By */}
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) =>
                    setSortBy(e.target.value as "name" | "rarity")
                  }
                  className="w-full px-2 py-1 text-sm border border-primary/20 rounded bg-tertiary text-primary"
                >
                  <option value="name">Name</option>
                  <option value="rarity">Rarity</option>
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
                    {sortBy === "name" ? "A → Z" : "Low → High"}
                  </option>
                  <option value="desc">
                    {sortBy === "name" ? "Z → A" : "High → Low"}
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
                      {item.float_value && item.float_value > 0 && (
                        <div className="text-xs text-muted mb-2">
                          Float: {item.float_value.toFixed(6)}
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex justify-center">
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
                          className="primary-btn btn-black text-xs px-2 py-1 flex items-center"
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
