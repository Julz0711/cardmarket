// src/routes.tsx
import { Routes, Route } from "react-router-dom";
import PortfolioSummary from "./components/portfolio/PortfolioSummary";
import AssetTable from "./components/common/AssetTable";
import FinancialAssetTable from "./components/common/FinancialAssetTable";
import { SteamInventory } from "./components/SteamInventory";
import UserManagement from "./components/admin/UserManagement";

// You can add more imports as needed

export function AppRoutes(props: any) {
  const { portfolioSummary, assets, loadData } = props;

  return (
    <Routes>
      <Route
        path="/"
        element={<PortfolioSummary summary={portfolioSummary} />}
      />
      <Route
        path="/portfolio"
        element={<PortfolioSummary summary={portfolioSummary} />}
      />
      <Route
        path="/cards"
        element={
          <AssetTable
            assets={assets.cards}
            assetType="cards"
            onDataUpdate={loadData}
            onSetBuyPrice={async (id: number, buyPrice: number) => {
              await props.api.updateCardBuyPrice(id, buyPrice);
              await loadData();
            }}
          />
        }
      />
      <Route
        path="/stocks"
        element={
          <FinancialAssetTable
            assets={assets.stocks}
            assetType="stocks"
            onDataUpdate={loadData}
          />
        }
      />
      <Route
        path="/etfs"
        element={
          <FinancialAssetTable
            assets={assets.etfs}
            assetType="etfs"
            onDataUpdate={loadData}
          />
        }
      />
      <Route
        path="/crypto"
        element={
          <FinancialAssetTable
            assets={assets.crypto}
            assetType="crypto"
            onDataUpdate={loadData}
          />
        }
      />
      <Route path="/steam" element={<SteamInventory />} />
      <Route path="/users" element={<UserManagement />} />
    </Routes>
  );
}
