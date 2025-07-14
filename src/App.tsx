import { useState, useEffect } from "react";
import CardTable from "./components/CardTable";
import StatsDashboard from "./components/StatsDashboard";
import { CardMarketScraper } from "./components/CardMarketScraper";
import { api, type Card, type Stats } from "./api/client";

function App() {
  const [cards, setCards] = useState<Card[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_cards: 0,
    total_value: 0,
    average_price: 0,
    expansions: [],
    rarities: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "scraper">(
    "dashboard"
  );

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [cardsResponse, statsResponse] = await Promise.all([
        api.getCards(),
        api.getStats(),
      ]);

      setCards(cardsResponse.cards || []);
      setStats(statsResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCardUpdate = async (card: Card) => {
    // For now, just log - you can implement edit modal here
    console.log("Update card:", card);
    // TODO: Implement edit modal
  };

  const handleCardDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this card?")) {
      return;
    }

    try {
      await api.deleteCard(id);
      setCards(cards.filter((card) => card.id !== id));
      loadData(); // Reload stats
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete card");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-screen bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto loading-spinner"></div>
          <p className="mt-4 text-secondary">Loading CardMarket data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen min-w-screen bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="alert-error mb-4">
            <p className="font-bold">Error loading data</p>
            <p>{error}</p>
          </div>
          <button
            onClick={loadData}
            className="btn-primary font-bold py-2 px-4 rounded"
          >
            Retry
          </button>
          <div className="mt-4 text-sm text-muted">
            <p>Make sure the backend server is running on localhost:5000</p>
            <p>
              You can start it by running:{" "}
              <code className="bg-tertiary px-1 py-0.5 rounded text-primary">
                python backend/app.py
              </code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen min-w-screen flex justify-center bg-primary">
      <div className="container px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">
            🎴 CardMarket Dashboard
          </h1>
          <p className="text-secondary">
            Manage and track your trading card collection
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`py-2 px-1 font-medium text-sm ${
                  activeTab === "dashboard" ? "tab-active" : "tab-inactive"
                }`}
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => setActiveTab("scraper")}
                className={`py-2 px-1 font-medium text-sm ${
                  activeTab === "scraper" ? "tab-active" : "tab-inactive"
                }`}
              >
                🤖 CardMarket Scraper
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "dashboard" ? (
          <>
            {/* Stats Dashboard */}
            <StatsDashboard stats={stats} onRefresh={loadData} />

            {/* Cards Table */}
            <CardTable
              cards={cards}
              onCardUpdate={handleCardUpdate}
              onCardDelete={handleCardDelete}
            />
          </>
        ) : (
          <>
            {/* Scraper Component */}
            <CardMarketScraper onScrapingComplete={loadData} />
          </>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-muted text-sm">
          <p>CardMarket Dashboard - Built with React + Vite + Tailwind CSS</p>
          <p className="mt-1">
            Backend API:{" "}
            <span className="inline-flex items-center">
              <span className="w-2 h-2 bg-green rounded-full mr-1"></span>
              Connected
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
