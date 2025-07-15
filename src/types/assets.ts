// Common asset types and interfaces
export type AssetType = "cards" | "stocks" | "etfs" | "crypto" | "steam";

export interface BaseAsset {
  id: number;
  type: AssetType;
  name: string;
  current_price: number;
  price_bought: number;
  quantity: number;
  last_updated: string;
}

// Trading Cards
export interface Card extends BaseAsset {
  type: "cards";
  tcg: string;
  expansion: string;
  number: number;
  rarity: string;
  supply: number;
  psa: string;
}

// Stocks
export interface Stock extends BaseAsset {
  type: "stocks";
  symbol: string;
  company: string;
  sector: string;
  market: string;
  dividend_yield?: number;
}

// ETFs
export interface ETF extends BaseAsset {
  type: "etfs";
  symbol: string;
  fund_name: string;
  expense_ratio: number;
  dividend_yield?: number;
  category: string;
}

// Cryptocurrency
export interface Crypto extends BaseAsset {
  type: "crypto";
  symbol: string;
  market_cap?: number;
  volume_24h?: number;
  change_24h?: number;
}

// Steam Items
export interface SteamItem extends BaseAsset {
  _id?: string;
  type: "steam";
  name: string;
  game: string;
  rarity: string;
  condition?: string;
  float_value?: number;
  asset_id: string;
  image_url?: string;
  market_hash_name?: string;
  steam_id?: string;
}

// Union type for all assets
export type Asset = Card | Stock | ETF | Crypto | SteamItem;

// Statistics interfaces
export interface BaseStats {
  total_items: number;
  total_value: number;
  total_cost: number;
  profit_loss: number;
  profit_loss_percentage: number;
  average_price: number;
}

export interface CardStats extends BaseStats {
  type: "cards";
  expansions: string[];
  rarities: string[];
  tcgs: string[];
}

export interface StockStats extends BaseStats {
  type: "stocks";
  sectors: string[];
  markets: string[];
  total_dividend: number;
}

export interface ETFStats extends BaseStats {
  type: "etfs";
  categories: string[];
  average_expense_ratio: number;
  total_dividend: number;
}

export interface CryptoStats extends BaseStats {
  type: "crypto";
  total_market_cap: number;
  top_performers: string[];
  worst_performers: string[];
}

export interface SteamStats extends BaseStats {
  type: "steam";
  games: string[];
  qualities: string[];
  average_float: number;
}

export type AssetStats =
  | CardStats
  | StockStats
  | ETFStats
  | CryptoStats
  | SteamStats;

// Portfolio summary
export interface PortfolioSummary {
  total_portfolio_value: number;
  total_investment: number;
  total_profit_loss: number;
  total_profit_loss_percentage: number;
  asset_breakdown: {
    [K in AssetType]: {
      value: number;
      percentage: number;
      count: number;
    };
  };
  top_performers: Asset[];
  worst_performers: Asset[];
}
