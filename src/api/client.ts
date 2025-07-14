const API_BASE_URL = "http://localhost:5000/api";

export interface Card {
  id: number;
  tcg: string;
  expansion: string;
  number: number;
  name: string;
  rarity: string;
  supply: number;
  current_price: number;
  price_bought: number | string;
  psa: string;
  last_updated: string;
}

export interface Stats {
  total_cards: number;
  total_value: number;
  average_price: number;
  expansions: string[];
  rarities: string[];
}

export interface ApiResponse<T> {
  cards?: T[];
  total?: number;
  timestamp?: string;
  message?: string;
  error?: string;
}

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
  async getStats(): Promise<Stats> {
    return this.request<Stats>("/stats");
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

  // Scraping endpoints
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
    return this.request("/scrape", {
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
}

export const apiClient = new ApiClient();
export const api = new ApiClient();
