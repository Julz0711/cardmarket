import type {
  Asset,
  AssetType,
  Card,
  Stock,
  ETF,
  Crypto,
  SteamItem,
  AssetStats,
  PortfolioSummary,
  CardStats,
} from "../types/assets";
import { authService } from "../services/auth";

const API_BASE_URL = "http://localhost:5000/api";

export interface ApiResponse<T> {
  data?: T;
  items?: T[];
  total?: number;
  timestamp?: string;
  message?: string;
  error?: string;
}

// Re-export types for backward compatibility
export type {
  Asset,
  AssetType,
  Card,
  Stock,
  ETF,
  Crypto,
  SteamItem,
  CardStats,
};

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  // Cards endpoints
  async getCards(filters?: {
    expansion?: string;
    rarity?: string;
    min_price?: number;
    max_price?: number;
    search?: string;
  }): Promise<ApiResponse<Card>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== "") {
          params.append(key, value.toString());
        }
      });
    }

    const query = params.toString();
    return this.request<ApiResponse<Card>>(`/cards${query ? `?${query}` : ""}`);
  }

  async getCard(id: number): Promise<Card> {
    return this.request<Card>(`/cards/${id}`);
  }

  async addCard(
    card: Omit<Card, "id" | "last_updated">
  ): Promise<ApiResponse<Card>> {
    return this.request<ApiResponse<Card>>("/cards", {
      method: "POST",
      body: JSON.stringify(card),
    });
  }

  async updateCard(
    id: number,
    card: Partial<Card>
  ): Promise<ApiResponse<Card>> {
    return this.request<ApiResponse<Card>>(`/cards/${id}`, {
      method: "PUT",
      body: JSON.stringify(card),
    });
  }

  async updateCardBuyPrice(
    id: number,
    buyPrice: number
  ): Promise<ApiResponse<Card>> {
    return this.request<ApiResponse<Card>>(`/cards/${id}/buy-price`, {
      method: "PUT",
      body: JSON.stringify({ buy_price: buyPrice }),
    });
  }

  async deleteCard(id: number): Promise<ApiResponse<Card>> {
    return this.request<ApiResponse<Card>>(`/cards/${id}`, {
      method: "DELETE",
    });
  }

  async deleteAllCards(): Promise<{
    message: string;
    deleted_count: number;
    total_cards: number;
  }> {
    return this.request("/cards", {
      method: "DELETE",
    });
  }

  // Stats endpoint
  async getStats(): Promise<CardStats> {
    return this.request<CardStats>("/stats");
  }

  // Portfolio endpoints
  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.request<PortfolioSummary>("/portfolio/summary");
  }

  async getAssetsByType(type: AssetType): Promise<ApiResponse<Asset[]>> {
    return this.request<ApiResponse<Asset[]>>(`/assets/${type}`);
  }

  async getAssetStats(type: AssetType): Promise<AssetStats> {
    return this.request<AssetStats>(`/assets/${type}/stats`);
  }

  async deleteAllAssets(type: AssetType): Promise<ApiResponse<any>> {
    return this.request<ApiResponse<any>>(`/assets/${type}`, {
      method: "DELETE",
    });
  }

  // Asset-specific endpoints
  async getStocks(): Promise<ApiResponse<Stock[]>> {
    return this.getAssetsByType("stocks") as Promise<ApiResponse<Stock[]>>;
  }

  async getETFs(): Promise<ApiResponse<ETF[]>> {
    return this.getAssetsByType("etfs") as Promise<ApiResponse<ETF[]>>;
  }

  async getCrypto(): Promise<ApiResponse<Crypto[]>> {
    return this.getAssetsByType("crypto") as Promise<ApiResponse<Crypto[]>>;
  }

  // Steam Inventory Management - Updated
  async getSteamItems(
    page = 1,
    perPage = 50
  ): Promise<{
    status: string;
    items: SteamItem[];
    page: number;
    per_page: number;
    total: number;
  }> {
    return this.request(`/steam/items?page=${page}&per_page=${perPage}`);
  }

  // Import Steam Inventory
  async importSteamInventory(steamId: string): Promise<{
    status: string;
    items: SteamItem[];
    message?: string;
    total?: number;
  }> {
    return this.request("/steam/import", {
      method: "POST",
      body: JSON.stringify({ steam_id: steamId }),
    });
  }

  // Import from pandas
  async importFromPandas(cards: any[]): Promise<ApiResponse<any>> {
    return this.request<ApiResponse<any>>("/import/pandas", {
      method: "POST",
      body: JSON.stringify({ cards }),
    });
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    version: string;
  }> {
    return this.request("/health");
  }

  // User management
  async getAllUsers(): Promise<{
    users: Array<{
      id: string;
      username: string;
      email: string;
      created_at: string;
      last_login?: string;
    }>;
    total: number;
  }> {
    return this.request("/auth/users");
  }

  // Scraping endpoints - Cards
  async scrapeCards(data: {
    tcg: string;
    expansion: string;
    numbers: number[];
    language: string;
    headless?: boolean;
  }): Promise<{
    message: string;
    scraped_cards: Card[];
    skipped_cards?: Array<{
      number: number;
      name: string;
      message: string;
    }>;
    total_cards: number;
  }> {
    return this.request("/scrape/cards", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async scrapeNewCard(url: string): Promise<{
    success: boolean;
    message: string;
    added: boolean;
    card?: Card;
  }> {
    return this.request("/cards/scrape-single", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  }

  // Scraping endpoints - Stocks (placeholder)
  async scrapeStocks(data: { symbols: string[]; market?: string }): Promise<{
    message: string;
    scraped_stocks: Stock[];
  }> {
    return this.request("/scrape/stocks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Scraping endpoints - ETFs (placeholder)
  async scrapeETFs(data: { symbols: string[] }): Promise<{
    message: string;
    scraped_etfs: ETF[];
  }> {
    return this.request("/scrape/etfs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Scraping endpoints - Crypto (placeholder)
  async scrapeCrypto(data: { symbols: string[] }): Promise<{
    message: string;
    scraped_crypto: Crypto[];
  }> {
    return this.request("/scrape/crypto", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Steam Inventory Management
  async updateSteamItem(
    itemId: string,
    data: {
      price_bought?: number;
      [key: string]: any;
    }
  ): Promise<{
    status: string;
    message: string;
    item: SteamItem;
  }> {
    return this.request(`/steam/items/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteSteamItem(itemId: string): Promise<{
    status: string;
    message: string;
  }> {
    return this.request(`/steam/items/${itemId}`, {
      method: "DELETE",
    });
  }

  async getSteamStats(): Promise<{
    status: string;
    stats: {
      total_items: number;
      total_value: number;
      total_bought: number;
      avg_value: number;
      rarity_distribution: Record<string, { count: number; value: number }>;
    };
  }> {
    return this.request("/steam/stats");
  }

  // Scraping endpoints - Steam
  async scrapeSteam(data: {
    steam_id: string;
    app_id?: string;
    include_floats?: boolean;
    include_prices?: boolean; // NEW: Include pricing data
    enable_pricing?: boolean; // NEW: Enable pricing service
    headless?: boolean;
  }): Promise<{
    status: string;
    message: string;
    data: {
      scraped_items: SteamItem[];
      skipped_items?: Array<{
        name: string;
        asset_id: string;
        message: string;
      }>;
      failed_items?: Array<{
        name: string;
        asset_id: string;
        error: string;
      }>;
      total_scraped: number;
      total_skipped: number;
      total_failed: number;
    };
  }> {
    // Steam scraping can take a long time with float values, so use a longer timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

    try {
      const result = await this.request<{
        status: string;
        message: string;
        data: {
          scraped_items: SteamItem[];
          skipped_items?: Array<{
            name: string;
            asset_id: string;
            message: string;
          }>;
          failed_items?: Array<{
            name: string;
            asset_id: string;
            error: string;
          }>;
          total_scraped: number;
          total_skipped: number;
          total_failed: number;
        };
      }>("/scrape/steam", {
        method: "POST",
        body: JSON.stringify(data),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async addCustomCard(card: {
    tcg: string;
    expansion: string;
    number: number;
    name: string;
    rarity: string;
    supply: number;
    current_price: number;
    price_bought?: string;
    psa?: string;
  }): Promise<{
    message: string;
    card: Card;
    total_cards: number;
  }> {
    return this.request("/scrape/custom", {
      method: "POST",
      body: JSON.stringify(card),
    });
  }

  async getScraperStatus(): Promise<{
    status: string;
    selenium_available: boolean;
    beautifulsoup_available: boolean;
    message: string;
  }> {
    return this.request("/scrape/status");
  }

  async rescrapeCardPrices(): Promise<{
    status: string;
    message: string;
    updated_cards: Card[];
    errors: string[];
    total_updated: number;
    total_errors: number;
  }> {
    return this.request("/cards/rescrape", {
      method: "POST",
    });
  }

  async updateSteamPrices(data: {
    item_ids?: string[];
    headless?: boolean;
  }): Promise<{
    status: string;
    message: string;
    updated_items: number;
    skipped_items: number;
    failed_items: number;
    details: {
      updated: Array<{ name: string; price: number }>;
      skipped: Array<{ name: string; reason: string }>;
      failed: Array<{ name: string; error: string }>;
    };
  }> {
    // Price updating can take a long time, so use a longer timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minute timeout

    try {
      const result = await this.request<{
        status: string;
        message: string;
        updated_items: number;
        skipped_items: number;
        failed_items: number;
        details: {
          updated: Array<{ name: string; price: number }>;
          skipped: Array<{ name: string; reason: string }>;
          failed: Array<{ name: string; error: string }>;
        };
      }>("/steam/update-prices", {
        method: "POST",
        body: JSON.stringify(data),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async updateSteamFloats(data: {
    item_ids?: string[];
    headless?: boolean;
  }): Promise<{
    status: string;
    message: string;
    updated_items: number;
    skipped_items: number;
    failed_items: number;
    details: {
      updated: Array<{
        name: string;
        float_value: number | null;
        paint_seed: number | null;
      }>;
      skipped: Array<{ name: string; reason: string }>;
      failed: Array<{ name: string; error: string }>;
    };
  }> {
    // Float updating can take a long time, so use a longer timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minute timeout

    try {
      const result = await this.request<{
        status: string;
        message: string;
        updated_items: number;
        skipped_items: number;
        failed_items: number;
        details: {
          updated: Array<{
            name: string;
            float_value: number | null;
            paint_seed: number | null;
          }>;
          skipped: Array<{ name: string; reason: string }>;
          failed: Array<{ name: string; error: string }>;
        };
      }>("/steam/update-floats", {
        method: "POST",
        body: JSON.stringify(data),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // Financial Assets (Stocks, ETFs, Crypto) - YFinance Integration
  async addFinancialAsset(data: {
    assetType: "stocks" | "etfs" | "crypto";
    ticker: string;
    quantity: number;
    price_bought?: number;
  }): Promise<{
    status: string;
    message: string;
    asset: Asset;
  }> {
    const body: any = {
      ticker: data.ticker,
      quantity: data.quantity,
    };
    if (
      typeof data.price_bought === "number" &&
      !isNaN(data.price_bought) &&
      data.price_bought > 0
    ) {
      body.price_bought = data.price_bought;
    }
    return this.request(`/financial/${data.assetType}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async updateFinancialAssetBoughtPrice(
    assetType: "stocks" | "etfs" | "crypto",
    id: number,
    boughtPrice: number
  ): Promise<{
    status: string;
    message: string;
    asset: Asset;
  }> {
    return this.request(`/financial/${assetType}/${id}/bought-price`, {
      method: "PUT",
      body: JSON.stringify({ price_bought: boughtPrice }),
    });
  }

  async updateFinancialAssetQuantity(
    assetType: "stocks" | "etfs" | "crypto",
    id: number,
    quantity: number
  ): Promise<{
    status: string;
    message: string;
    asset: Asset;
  }> {
    return this.request(`/financial/${assetType}/${id}/quantity`, {
      method: "PUT",
      body: JSON.stringify({ quantity }),
    });
  }

  async deleteFinancialAsset(
    assetType: "stocks" | "etfs" | "crypto",
    id: number
  ): Promise<{
    status: string;
    message: string;
  }> {
    return this.request(`/financial/${assetType}/${id}`, {
      method: "DELETE",
    });
  }

  async deleteAllFinancialAssets(
    assetType: "stocks" | "etfs" | "crypto"
  ): Promise<{
    status: string;
    message: string;
    deleted_count: number;
  }> {
    return this.request(`/financial/${assetType}`, {
      method: "DELETE",
    });
  }

  async getFinancialAssets(
    assetType: "stocks" | "etfs" | "crypto"
  ): Promise<ApiResponse<Asset>> {
    return this.request<ApiResponse<Asset>>(`/financial/${assetType}`);
  }

  async refreshFinancialAssetPrices(
    assetType: "stocks" | "etfs" | "crypto",
    assetIds?: number[]
  ): Promise<{
    status: string;
    message: string;
    updated_count: number;
    failed_count: number;
    details: {
      updated: Array<{
        id: number;
        name: string;
        old_price: number;
        new_price: number;
      }>;
      failed: Array<{ id: number; name: string; error: string }>;
    };
  }> {
    return this.request(`/financial/${assetType}/refresh-prices`, {
      method: "POST",
      body: JSON.stringify({ asset_ids: assetIds }),
    });
  }
}

export const apiClient = new ApiClient();
export const api = new ApiClient();
