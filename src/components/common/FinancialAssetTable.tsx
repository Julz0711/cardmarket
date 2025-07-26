import React, { useState, memo } from "react";
import type { Asset } from "../../types/assets";
import { apiClient } from "../../api/client";

// Material Icons
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import RefreshIcon from "@mui/icons-material/Refresh";

// --- Types for buy/sell transactions ---
type TransactionType = "buy" | "sell";
type Purchase = {
  quantity: number;
  price: number;
  date?: string;
  type: TransactionType;
};
interface AddFormData {
  ticker: string;
  quantity: number;
  purchases: Purchase[];
  tempQuantity: string;
  tempPrice: string;
  type: TransactionType;
}
interface EditFormData {
  purchases: Purchase[];
  tempQuantity: string;
  tempPrice: string;
  type: TransactionType;
}

interface FinancialAssetTableProps {
  assets: Asset[];
  assetType: "stocks" | "etfs" | "crypto";
  onDataUpdate?: () => void;
}

const FinancialAssetTable: React.FC<FinancialAssetTableProps> = ({
  assets,
  assetType,
  onDataUpdate,
}) => {
  const [filterText, setFilterText] = useState("");
  // Sorting filter state
  const [sortFilter, setSortFilter] = useState<string>("value");

  // ...existing code...

  // Add new asset modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addMessage, setAddMessage] = useState<string>("");
  const [addError, setAddError] = useState<string>("");
  // Types moved to top-level below imports
  const [addFormData, setAddFormData] = useState<AddFormData>({
    ticker: "",
    quantity: 1,
    purchases: [],
    tempQuantity: "",
    tempPrice: "",
    type: "buy",
  });

  // Edit modal states
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  // Types moved to top-level below imports
  const [editFormData, setEditFormData] = useState<EditFormData>({
    purchases: [],
    tempQuantity: "",
    tempPrice: "",
    type: "buy",
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string>("");

  // Delete states
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string>("");
  const [deleteError, setDeleteError] = useState<string>("");

  // Update prices states
  const [isUpdatingPrices, setIsUpdatingPrices] = useState(false);
  const [updatePricesMessage, setUpdatePricesMessage] = useState<string>("");
  const [updatePricesError, setUpdatePricesError] = useState<string>("");

  // Format as EUR (all prices from backend are now in EUR)
  const formatCurrency = (value: number) => {
    return `€${value.toFixed(2)}`;
  };
  const formatPercentage = (value: number) =>
    `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;

  const getProfitLossColor = (profitLoss: number) => {
    if (profitLoss > 0) return "text-green-600";
    if (profitLoss < 0) return "text-red-600";
    return "text-gray-600";
  };

  const getProfitLossSymbol = (profitLoss: number) => {
    if (profitLoss > 0) return "+";
    return "";
  };

  const getTotalItems = () => assets.length;

  const getTotalValue = () => {
    return assets.reduce((total, asset) => {
      return total + asset.current_price * asset.quantity;
    }, 0);
  };

  const getTotalInvestment = () => {
    return assets.reduce((total, asset) => {
      return total + asset.price_bought * asset.quantity;
    }, 0);
  };

  const getTotalProfitLoss = () => {
    return getTotalValue() - getTotalInvestment();
  };

  const getTotalProfitLossPercentage = () => {
    const investment = getTotalInvestment();
    if (investment === 0) return 0;
    return (getTotalProfitLoss() / investment) * 100;
  };

  const handleAddNew = () => {
    setShowAddModal(true);
    setAddMessage("");
    setAddError("");
    setAddFormData({
      ticker: "",
      quantity: 1,
      purchases: [],
      tempQuantity: "",
      tempPrice: "",
      type: "buy",
    });
  };

  const handleAddInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setAddFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Purchase step functions for stocks/ETFs
  const handleAddPurchase = () => {
    const quantity = parseFloat(
      (addFormData.tempQuantity + "").replace(",", ".")
    );
    const price = parseFloat((addFormData.tempPrice + "").replace(",", "."));
    if (isNaN(quantity) || quantity <= 0 || isNaN(price) || price <= 0) {
      setAddError("Please enter valid quantity and price");
      return;
    }
    const newPurchase: Purchase = {
      quantity,
      price,
      date: new Date().toISOString().split("T")[0],
      type: addFormData.type,
    };
    setAddFormData((prev) => ({
      ...prev,
      purchases: [...prev.purchases, newPurchase],
      tempQuantity: "",
      tempPrice: "",
    }));
    setAddError("");
  };

  const handleRemovePurchase = (index: number) => {
    setAddFormData((prev) => ({
      ...prev,
      purchases: prev.purchases.filter((_, i) => i !== index),
    }));
  };

  const getTotalQuantity = (type: TransactionType = addFormData.type) => {
    return addFormData.purchases
      .filter((p) => p.type === type)
      .reduce((total, purchase) => total + purchase.quantity, 0);
  };
  const getAveragePrice = (type: TransactionType = addFormData.type) => {
    const filtered = addFormData.purchases.filter((p) => p.type === type);
    if (filtered.length === 0) return 0;
    const totalValue = filtered.reduce(
      (total, purchase) => total + purchase.quantity * purchase.price,
      0
    );
    const totalQuantity = getTotalQuantity(type);
    return totalQuantity > 0 ? totalValue / totalQuantity : 0;
  };

  const handleAddSubmit = async () => {
    setIsAdding(true);
    setAddError("");

    try {
      if (!addFormData.ticker.trim()) {
        setAddError("Please enter a ticker symbol");
        setIsAdding(false);
        return;
      }

      // Ensure we have purchase history for all asset types
      if (addFormData.purchases.length === 0) {
        setAddError("Please add at least one purchase entry");
        setIsAdding(false);
        return;
      }

      // Use total quantity from purchase history for all asset types
      const quantity = getTotalQuantity();
      const averagePrice = getAveragePrice();

      // Call API to add new financial asset with weighted average price
      await apiClient.addFinancialAsset({
        assetType,
        ticker: addFormData.ticker.toUpperCase(),
        quantity: quantity,
        price_bought: averagePrice > 0 ? averagePrice : undefined,
      });

      setAddMessage(
        `Successfully added ${addFormData.ticker.toUpperCase()} to ${assetType}!`
      );
      setShowAddModal(false);

      // Reset form on success
      setAddFormData({
        ticker: "",
        quantity: 1,
        purchases: [],
        tempQuantity: "",
        tempPrice: "",
        type: "buy",
      }); // Refresh the data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setAddError(
        error instanceof Error ? error.message : `Failed to add ${assetType}`
      );
    } finally {
      setIsAdding(false);
    }
  };

  const handleEditAsset = (asset: Asset) => {
    setEditingAsset(asset);
    // Default to buy tab, and create a single buy entry for now
    const singlePurchase: Purchase = {
      quantity: asset.quantity,
      price: asset.price_bought,
      date: new Date().toISOString().split("T")[0],
      type: "buy",
    };
    setEditFormData({
      purchases: [singlePurchase],
      tempQuantity: "",
      tempPrice: "",
      type: "buy",
    });
    setShowEditModal(true);
    setUpdateError("");
  };

  const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Edit purchase history functions
  const handleEditAddPurchase = () => {
    const quantity = parseFloat(
      (editFormData.tempQuantity + "").replace(",", ".")
    );
    const price = parseFloat((editFormData.tempPrice + "").replace(",", "."));
    if (isNaN(quantity) || quantity <= 0 || isNaN(price) || price <= 0) {
      setUpdateError("Please enter valid quantity and price");
      return;
    }
    const newPurchase: Purchase = {
      quantity,
      price,
      date: new Date().toISOString().split("T")[0],
      type: editFormData.type,
    };
    setEditFormData((prev) => ({
      ...prev,
      purchases: [...prev.purchases, newPurchase],
      tempQuantity: "",
      tempPrice: "",
    }));
    setUpdateError("");
  };

  const handleEditRemovePurchase = (index: number) => {
    setEditFormData((prev) => ({
      ...prev,
      purchases: prev.purchases.filter((_, i) => i !== index),
    }));
  };

  const getEditTotalQuantity = (type: TransactionType = editFormData.type) => {
    return editFormData.purchases
      .filter((p) => p.type === type)
      .reduce((total, purchase) => total + purchase.quantity, 0);
  };
  const getEditAveragePrice = (type: TransactionType = editFormData.type) => {
    const filtered = editFormData.purchases.filter((p) => p.type === type);
    if (filtered.length === 0) return 0;
    const totalValue = filtered.reduce(
      (total, purchase) => total + purchase.quantity * purchase.price,
      0
    );
    const totalQuantity = getEditTotalQuantity(type);
    return totalQuantity > 0 ? totalValue / totalQuantity : 0;
  };

  const handleEditSubmit = async () => {
    if (!editingAsset) return;

    setIsUpdating(true);
    setUpdateError("");

    try {
      if (editFormData.purchases.length === 0) {
        setUpdateError("Please add at least one purchase entry");
        setIsUpdating(false);
        return;
      }

      const newQuantity = getEditTotalQuantity();
      const newAveragePrice = getEditAveragePrice();

      // Update quantity if changed
      if (newQuantity !== editingAsset.quantity) {
        await apiClient.updateFinancialAssetQuantity(
          assetType,
          editingAsset.id,
          newQuantity
        );
      }

      // Update bought price if changed
      if (newAveragePrice !== editingAsset.price_bought) {
        await apiClient.updateFinancialAssetBoughtPrice(
          assetType,
          editingAsset.id,
          newAveragePrice
        );
      }

      setShowEditModal(false);
      setEditingAsset(null);

      // Refresh the data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setUpdateError(
        error instanceof Error ? error.message : "Failed to update asset"
      );
    } finally {
      setIsUpdating(false);
    }
  };

  const getAssetLogo = (asset: Asset) => {
    const symbol = "symbol" in asset ? asset.symbol : "";

    let logoSymbol = symbol;
    if (assetType === "crypto") {
      logoSymbol = symbol.replace(/-usd|-eur/i, "").toLowerCase();
    } else {
      logoSymbol = symbol.toUpperCase();
    }
    if (!logoSymbol) {
      logoSymbol = asset.name.replace(/\s+/g, "").toLowerCase();
    }
    return `https://api.elbstream.com/logos/symbol/${logoSymbol}`;
  };

  const getPortfolioPercentage = (asset: Asset) => {
    const totalPortfolioValue = getTotalValue();
    if (totalPortfolioValue === 0) return 0;
    const assetValue = asset.current_price * asset.quantity;
    return (assetValue / totalPortfolioValue) * 100;
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
      await apiClient.deleteFinancialAsset(assetType, id);
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
      await apiClient.deleteAllFinancialAssets(assetType);
      setDeleteMessage(`Successfully deleted all ${assetType}`);

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

  const handleUpdatePrices = async () => {
    setIsUpdatingPrices(true);
    setUpdatePricesMessage("");
    setUpdatePricesError("");

    try {
      const result = await apiClient.refreshFinancialAssetPrices(assetType);
      setUpdatePricesMessage(
        `Successfully updated prices for ${
          result.updated_count || assets.length
        } ${assetType}`
      );

      // Refresh the data
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      setUpdatePricesError(
        error instanceof Error ? error.message : "Failed to update prices"
      );
    } finally {
      setIsUpdatingPrices(false);
    }
  };

  const filteredAssets = assets.filter(
    (asset) =>
      asset.name.toLowerCase().includes(filterText.toLowerCase()) ||
      ("symbol" in asset &&
        asset.symbol.toLowerCase().includes(filterText.toLowerCase()))
  );

  const sortedAssets = [...filteredAssets].sort((a, b) => {
    const totalValueA = a.current_price * a.quantity;
    const totalValueB = b.current_price * b.quantity;
    const profitA = totalValueA - a.price_bought * a.quantity;
    const profitB = totalValueB - b.price_bought * b.quantity;
    switch (sortFilter) {
      case "value":
        return totalValueB - totalValueA; // Descending total value
      case "profit":
        return profitB - profitA; // Descending profit
      case "loss":
        return profitA - profitB; // Descending loss (most negative first)
      case "name":
      default: {
        const aSymbol = "symbol" in a ? a.symbol : a.name;
        const bSymbol = "symbol" in b ? b.symbol : b.name;
        return aSymbol.localeCompare(bSymbol);
      }
    }
  });

  const getAssetTypeLabel = () => {
    switch (assetType) {
      case "stocks":
        return "Stocks";
      case "etfs":
        return "ETFs";
      case "crypto":
        return "Cryptos";
      default:
        return assetType;
    }
  };

  return (
    <div className="space-y-6">
      {/* Total Summary Section */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-primary">
              {getAssetTypeLabel()} Summary
            </h3>
            <button
              onClick={handleDeleteAll}
              disabled={isDeleting || assets.length === 0}
              className="primary-btn btn-red disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              {isDeleting ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <DeleteIcon fontSize="inherit" />
              )}
              Delete All
            </button>
          </div>
        </div>

        <div className="card-body">
          {/* Status messages */}
          {addMessage && (
            <div className="mb-4 p-4 bg-green-800 border border-green-600 text-green-200 rounded">
              {addMessage}
            </div>
          )}
          {addError && (
            <div className="mb-4 p-4 bg-red-800 border border-red-600 text-red-200 rounded">
              {addError}
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
          {updatePricesMessage && (
            <div className="mb-4 p-4 bg-green-800 border border-green-600 text-green-200 rounded">
              {updatePricesMessage}
            </div>
          )}
          {updatePricesError && (
            <div className="mb-4 p-4 bg-red-800 border border-red-600 text-red-200 rounded">
              {updatePricesError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">Total Items</div>
              <div className="text-2xl font-bold text-primary">
                {getTotalItems()}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">Total Value</div>
              <div className="text-2xl font-bold text-primary">
                {formatCurrency(getTotalValue())}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">
                Total Investment
              </div>
              <div className="text-2xl font-bold text-primary">
                {formatCurrency(getTotalInvestment())}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-xs font-bold text-muted">Total P&L</div>
              <div
                className={`text-2xl font-bold ${getProfitLossColor(
                  getTotalProfitLoss()
                )}`}
              >
                {getProfitLossSymbol(getTotalProfitLoss())}
                {formatCurrency(Math.abs(getTotalProfitLoss()))}
                <div className="text-sm font-normal">
                  ({formatPercentage(getTotalProfitLossPercentage())})
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modern Asset Pills */}
      <div className="card">
        <div className="card-header">
          <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-2 md:gap-0">
            <h3 className="text-lg font-medium text-primary">
              {getAssetTypeLabel()} ({assets.length})
            </h3>
            <div className="flex space-x-3">
              <button
                onClick={handleAddNew}
                className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
              >
                <AddIcon fontSize="inherit" />
                Add New {getAssetTypeLabel().slice(0, -1)}
              </button>
              <button
                onClick={handleUpdatePrices}
                disabled={isUpdatingPrices || assets.length === 0}
                className="primary-btn btn-black disabled:bg-gray-600 disabled:cursor-not-allowed"
              >
                {isUpdatingPrices ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <RefreshIcon fontSize="inherit" />
                )}
                {isUpdatingPrices ? "Updating..." : "Update Prices"}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4 p-4">
          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Asset Name
            </label>
            <input
              type="text"
              placeholder={`Filter ${assetType}...`}
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Sort By
            </label>
            <select
              value={sortFilter}
              onChange={(e) => setSortFilter(e.target.value)}
              className="select w-full"
              aria-label="Sort assets"
            >
              <option value="name">Name</option>
              <option value="value">Value</option>
              <option value="profit">Profit</option>
              <option value="loss">Loss</option>
            </select>
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
            <div className="space-y-4">
              {sortedAssets.map((asset) => {
                const price = asset.current_price;
                const totalValue = price * asset.quantity;
                const invPrice = asset.price_bought;
                const totalInvestment = invPrice * asset.quantity;
                const profitLoss = totalValue - totalInvestment;
                const profitLossPercentage =
                  totalInvestment > 0
                    ? (profitLoss / totalInvestment) * 100
                    : 0;
                const change24h =
                  "change_24h" in asset ? (asset as any).change_24h : 0;
                const portfolioPercentage = getPortfolioPercentage(asset);
                const symbol = "symbol" in asset ? asset.symbol : "";

                // Determine background gradient based on 24h change
                const gradientClass =
                  change24h >= 0
                    ? "bg-gradient-to-r from-40% from-dark to-green/40"
                    : "bg-gradient-to-r from-40% from-dark to-red/40";

                return (
                  <div
                    key={asset.id}
                    className="flex items-center justify-center space-x-4"
                  >
                    <div
                      className={`flex items-center justify-between inset-shadow-md shadow-lg ${gradientClass} border border-primary rounded-xl px-4 py-3 flex-1`}
                    >
                      {/* Left Section: Logo & Asset Info */}
                      <div className="flex items-center space-x-4 flex-1">
                        {/* Asset Logo */}
                        <div className="w-10 h-10 bg-white border border-primary rounded-full flex items-center justify-center overflow-hidden">
                          <img
                            src={getAssetLogo(asset)}
                            alt={symbol}
                            className="w-10 h-10 rounded-full object-cover"
                            onError={(e) => {
                              // Fallback to first 3 letters if image fails to load
                              const target = e.target as HTMLImageElement;
                              target.style.display = "none";
                              target.parentElement!.innerHTML = `<span class="text-sm font-bold text-black">${symbol
                                .slice(0, 3)
                                .toUpperCase()}</span>`;
                            }}
                          />
                        </div>

                        {/* Asset Details */}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            {/* Ticker Symbol (smaller) and Full Name */}
                            <div className="flex flex-row items-center gap-2">
                              <span
                                className="text-md font-semibold text-white max-w-48 truncate"
                                title={asset.name}
                              >
                                {asset.name}
                              </span>
                              <span className="text-sm font-semibold text-muted tracking-wide uppercase leading-tight">
                                ({symbol})
                              </span>
                            </div>

                            {/* Current Price */}
                            <div className="text-sm font-semibold text-gold">
                              {formatCurrency(asset.current_price)}
                              {asset.currency && (
                                <span className="text-sm text-muted ml-1">
                                  ({asset.currency})
                                </span>
                              )}
                            </div>

                            {/* 24h Change */}
                            <div
                              className={`text-[8px] font-medium px-1.5 py-0.5 rounded-full ${
                                change24h >= 0
                                  ? "bg-green/30 text-green-400"
                                  : "bg-red/30 text-red-400"
                              }`}
                            >
                              {formatPercentage(change24h)}
                            </div>
                          </div>

                          {/* Portfolio Percentage Bar - Made smaller, with amount holding */}
                          <div className="flex items-center mt-1 space-x-2">
                            <div className="w-48 bg-tertiary rounded-full h-1.5 overflow-hidden">
                              <div
                                className="h-full bg-white/10"
                                style={{
                                  width: `${Math.min(
                                    portfolioPercentage,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                            <div className="text-xs text-muted">
                              {portfolioPercentage.toFixed(1)}%
                            </div>
                            <div className="text-xs text-muted">
                              <span className="text-muted">
                                ({Number(asset.quantity).toFixed(2)}{" "}
                                {assetType === "crypto" ? "units" : "shares"})
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Right Section: Total Value */}
                      <div className="text-right">
                        <div className="text-xl font-bold text-white">
                          {formatCurrency(totalValue)}
                        </div>
                        <div
                          className={`text-sm ${getProfitLossColor(
                            profitLoss
                          )}`}
                        >
                          {getProfitLossSymbol(profitLoss)}
                          {formatCurrency(Math.abs(profitLoss))}
                          <span className="text-xs ml-1">
                            ({formatPercentage(profitLossPercentage)})
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Edit Button - Outside the pill */}
                    <button
                      onClick={() => handleEditAsset(asset)}
                      className="primary-btn btn-black"
                    >
                      Edit
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Edit Asset Modal */}
      {showEditModal && editingAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-10 flex items-center justify-center z-50">
          <div className="bg-primary rounded-lg p-6 w-full max-w-md mx-4 border border-primary">
            <h3 className="text-lg font-semibold text-white mb-4">
              Edit{" "}
              {"symbol" in editingAsset
                ? editingAsset.symbol
                : editingAsset.name}
            </h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleEditSubmit();
              }}
            >
              <div className="space-y-4">
                {/* Add Transaction Section */}
                <div className="bg-primary p-4 rounded-md border border-primary">
                  {/* Buy/Sell Tabs */}
                  <div className="flex space-x-2 bg-tertiary p-[2px] rounded-lg mb-2">
                    {(["buy", "sell"] as TransactionType[]).map((type) => (
                      <button
                        key={type}
                        type="button"
                        className={`px-4 py-1 text-[10px] w-full rounded-md font-medium focus:outline-none transition-colors cursor-pointer hover:bg-primary/50 ${
                          editFormData.type === type
                            ? "bg-primary text-white"
                            : "text-muted hover:text-white"
                        }`}
                        onClick={() => setEditFormData((f) => ({ ...f, type }))}
                      >
                        {type === "buy" ? "Buy" : "Sell"}
                      </button>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-2">
                        {assetType === "crypto" ? "Quantity" : "Shares"}
                      </label>
                      <input
                        type="text"
                        name="tempQuantity"
                        value={editFormData.tempQuantity || ""}
                        onChange={handleEditInputChange}
                        placeholder={assetType === "crypto" ? "0.001" : "10"}
                        className="w-full input"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-2">
                        {assetType === "crypto"
                          ? "Price per Unit (€)"
                          : "Price per Share (€)"}
                      </label>
                      <input
                        type="text"
                        name="tempPrice"
                        value={editFormData.tempPrice || ""}
                        onChange={handleEditInputChange}
                        placeholder={
                          assetType === "crypto" ? "50000.00" : "150.00"
                        }
                        className="w-full input"
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleEditAddPurchase}
                    className="primary-btn btn-blue"
                  >
                    Add Transaction
                  </button>

                  {editFormData.purchases.filter(
                    (p) => p.type === editFormData.type
                  ).length > 0 && (
                    <div className="space-y-2 mt-8">
                      <div className="text-xs font-semibold text-muted">
                        {editFormData.type === "buy" ? "Buy" : "Sell"}{" "}
                        Transactions (
                        {
                          editFormData.purchases.filter(
                            (p) => p.type === editFormData.type
                          ).length
                        }
                        )
                      </div>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {editFormData.purchases
                          .filter((p) => p.type === editFormData.type)
                          .map((purchase, index) => (
                            <div
                              key={index}
                              className="bg-tertiary p-2 rounded-md text-xs flex justify-between items-center"
                            >
                              <div className="text-gray-300">
                                <span className="font-bold">
                                  {purchase.quantity}
                                </span>{" "}
                                {assetType === "crypto" ? "units" : "shares"} @{" "}
                                <span className="font-bold">
                                  {purchase.price.toFixed(2)}€
                                </span>
                                {purchase.date && (
                                  <span className="text-gray-400 ml-2">
                                    ({purchase.date})
                                  </span>
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => handleEditRemovePurchase(index)}
                                className="bg-red-600 hover:bg-red-700 text-white rounded-md p-1 flex items-center justify-center transition-colors"
                              >
                                <CloseIcon fontSize="inherit" />
                              </button>
                            </div>
                          ))}
                      </div>
                      {/* Summary for selected tab */}
                      <div className="bg-tertiary p-2 rounded-md text-xs text-gray-300">
                        <div>
                          Total Quantity:{" "}
                          <span className="font-bold">
                            {getEditTotalQuantity(editFormData.type)}
                          </span>
                        </div>
                        <div>
                          Average Price:{" "}
                          <span className="font-bold">
                            {getEditAveragePrice(editFormData.type).toFixed(2)}€
                          </span>
                        </div>
                        <div>
                          Total Investment:{" "}
                          <span className="font-bold">
                            {(
                              getEditTotalQuantity(editFormData.type) *
                              getEditAveragePrice(editFormData.type)
                            ).toFixed(2)}
                            €
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                {/* Transaction History List for selected tab */}
              </div>

              {updateError && (
                <div className="mt-4 p-3 bg-red-800 border border-red-600 text-red-200 rounded text-sm">
                  {updateError}
                </div>
              )}

              <div className="flex justify-between items-center mt-6">
                <button
                  type="button"
                  onClick={() => {
                    if (
                      editingAsset &&
                      window.confirm(
                        `Are you sure you want to delete "${editingAsset.name}"? This action cannot be undone.`
                      )
                    ) {
                      handleDeleteAsset(editingAsset.id, editingAsset.name);
                      setShowEditModal(false);
                      setEditingAsset(null);
                    }
                  }}
                  className="primary-btn btn-red"
                >
                  <DeleteIcon className="mr-2" fontSize="small" />
                  Delete Asset
                </button>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingAsset(null);
                      setUpdateError("");
                    }}
                    className="primary-btn btn-black"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isUpdating}
                    className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                  >
                    {isUpdating ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-primary rounded-lg p-6 w-full max-w-lg mx-4 border border-primary">
            <h3 className="text-lg font-semibold text-white mb-4">
              Add New {getAssetTypeLabel().slice(0, -1)}
            </h3>
            {/* Info box for symbol lookup */}
            <div className="mb-4 p-3 bg-blue/20 border border-blue/60 text-blue-100 rounded-lg text-xs">
              <strong>Tip:</strong> To find the correct symbol, search for your
              asset on{" "}
              <a
                href="https://de.finance.yahoo.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline text-gold hover:text-gray-200"
              >
                Yahoo Finance
              </a>
              .<br />
              For example, the S&P 500 ETF is{" "}
              <span className="font-semibold bg-blue/60 px-1 rounded">SPY</span>
              , Apple is{" "}
              <span className="font-semibold bg-blue/60 px-1 rounded">
                AAPL
              </span>
              , and Bitcoin is{" "}
              <span className="font-semibold bg-blue/60 px-1 rounded">
                BTC-USD
              </span>
              .<br />
              Use the symbol exactly as shown on Yahoo Finance for accurate
              price data.
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAddSubmit();
              }}
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ticker Symbol
                  </label>
                  <input
                    type="text"
                    name="ticker"
                    value={addFormData.ticker}
                    onChange={handleAddInputChange}
                    placeholder={
                      assetType === "stocks"
                        ? "e.g., NVDA, AAPL"
                        : assetType === "etfs"
                        ? "e.g., SPY, QQQ"
                        : "e.g., BTC-USD, ETH-USD"
                    }
                    autoComplete="off"
                    className="w-full input"
                  />
                </div>

                {assetType === "crypto" ? (
                  // Simple quantity input for crypto
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-gray-300">
                      Purchase History
                    </div>

                    {/* Add new purchase section */}
                    <div className="bg-primary p-4 rounded-md border border-primary">
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-400 mb-2">
                            Quantity
                          </label>
                          <input
                            type="text"
                            name="tempQuantity"
                            value={addFormData.tempQuantity || ""}
                            onChange={handleAddInputChange}
                            placeholder="0.001"
                            className="w-full input"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-400 mb-2">
                            Price per Unit (€)
                          </label>
                          <input
                            type="text"
                            name="tempPrice"
                            value={addFormData.tempPrice || ""}
                            onChange={handleAddInputChange}
                            placeholder="50000.00"
                            className="w-full input"
                          />
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleAddPurchase}
                        className="primary-btn btn-blue"
                      >
                        Add Purchase
                      </button>
                    </div>

                    {/* Purchase history list */}
                    {addFormData.purchases.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-medium text-gray-400">
                          Purchase Entries ({addFormData.purchases.length})
                        </div>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {addFormData.purchases.map((purchase, index) => (
                            <div
                              key={index}
                              className="bg-secondary p-2 rounded text-xs flex justify-between items-center"
                            >
                              <div className="text-gray-300">
                                <span className="font-bold">
                                  {purchase.quantity}
                                </span>{" "}
                                units @{" "}
                                <span className="font-bold">
                                  {purchase.price.toFixed(2)}€
                                </span>
                                {purchase.date && (
                                  <span className="text-muted ml-2">
                                    ({purchase.date})
                                  </span>
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => handleRemovePurchase(index)}
                                className="bg-red border-2 border-red text-white rounded-md p-1 flex items-center justify-center hover:bg-black hover:text-red transition-colors"
                              >
                                <CloseIcon fontSize="inherit" />
                              </button>
                            </div>
                          ))}
                        </div>

                        {/* Summary */}
                        <div className="bg-primary p-2 rounded text-xs text-gray-300">
                          <div>
                            Total Quantity:{" "}
                            <span className="font-bold">
                              {getTotalQuantity()}
                            </span>
                          </div>
                          <div>
                            Average Price:{" "}
                            <span className="font-bold">
                              {getAveragePrice().toFixed(2)}€
                            </span>
                          </div>
                          <div>
                            Total Investment:{" "}
                            <span className="font-bold">
                              {(getTotalQuantity() * getAveragePrice()).toFixed(
                                2
                              )}
                              €
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  // Purchase history system for stocks/ETFs
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-gray-300">
                      Purchase History
                    </div>

                    {/* Add new purchase section */}
                    <div className="bg-tertiary p-4 rounded-md border border-primary">
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-400 mb-2">
                            Quantity
                          </label>
                          <input
                            type="text"
                            name="tempQuantity"
                            value={addFormData.tempQuantity || ""}
                            onChange={handleAddInputChange}
                            placeholder="10"
                            className="input w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-400 mb-2">
                            Price per Share (€)
                          </label>
                          <input
                            type="text"
                            name="tempPrice"
                            value={addFormData.tempPrice || ""}
                            onChange={handleAddInputChange}
                            placeholder="150.00"
                            className="w-full input"
                          />
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleAddPurchase}
                        className="primary-btn btn-blue"
                      >
                        Add Purchase
                      </button>
                    </div>

                    {/* Purchase history list */}
                    {addFormData.purchases.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-medium text-gray-400">
                          Purchase Entries ({addFormData.purchases.length})
                        </div>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {addFormData.purchases.map((purchase, index) => (
                            <div
                              key={index}
                              className="bg-secondary p-2 rounded text-xs flex justify-between items-center"
                            >
                              <div className="text-gray-300">
                                <span className="font-bold">
                                  {purchase.quantity}
                                </span>{" "}
                                shares @{" "}
                                <span className="font-bold">
                                  {purchase.price.toFixed(2)}€
                                </span>
                                {purchase.date && (
                                  <span className="text-muted ml-2">
                                    ({purchase.date})
                                  </span>
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => handleRemovePurchase(index)}
                                className="bg-red border-2 border-red text-white rounded-md p-1 flex items-center justify-center hover:bg-black hover:text-red transition-colors"
                              >
                                <CloseIcon fontSize="inherit" />
                              </button>
                            </div>
                          ))}
                        </div>

                        {/* Summary */}
                        <div className="bg-primary p-2 rounded text-xs text-gray-300">
                          <div>
                            Total Quantity:{" "}
                            <span className="font-bold">
                              {getTotalQuantity()}
                            </span>
                          </div>
                          <div>
                            Average Price:{" "}
                            <span className="font-bold">
                              {getAveragePrice().toFixed(2)}€
                            </span>
                          </div>
                          <div>
                            Total Investment:{" "}
                            <span className="font-bold">
                              {(getTotalQuantity() * getAveragePrice()).toFixed(
                                2
                              )}
                              €
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {addError && (
                <div className="mt-4 p-3 bg-red-800 border border-red text-red-200 rounded text-sm">
                  {addError}
                </div>
              )}

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setAddError("");
                  }}
                  className="primary-btn btn-black"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAdding}
                  className="primary-btn btn-green disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  {isAdding
                    ? "Adding..."
                    : `Add ${getAssetTypeLabel().slice(0, -1)}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(FinancialAssetTable);
