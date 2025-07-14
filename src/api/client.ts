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

  async getSteamItems(): Promise<ApiResponse<SteamItem[]>> {
    return this.getAssetsByType("steam") as Promise<ApiResponse<SteamItem[]>>;
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

  // Scraping endpoints - Cards
  async scrapeCards(data: {
    tcg: string;
    expansion: string;
    numbers: number[];
    headless?: boolean;
  }): Promise<{
    message: string;
    scraped_cards: Card[];
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

  // Scraping endpoints - Steam (placeholder)
  async scrapeSteam(data: { steamId: string; appId?: string }): Promise<{
    message: string;
    scraped_items: SteamItem[];
  }> {
    return this.request("/scrape/steam", {
      method: "POST",
      body: JSON.stringify(data),
    });
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
}

export const apiClient = new ApiClient();
export const api = new ApiClient();
