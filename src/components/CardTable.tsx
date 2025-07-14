import React, { useState, useEffect } from "react";

interface Card {
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

interface CardTableProps {
  cards: Card[];
  onCardUpdate?: (card: Card) => void;
  onCardDelete?: (id: number) => void;
}

const CardTable: React.FC<CardTableProps> = ({
  cards,
  onCardUpdate,
  onCardDelete,
}) => {
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Card | null;
    direction: "asc" | "desc";
  }>({ key: null, direction: "asc" });

  const [filteredCards, setFilteredCards] = useState<Card[]>(cards);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    let filtered = cards.filter(
      (card) =>
        card.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.expansion.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.rarity.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.number.toString().includes(searchTerm)
    );

    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const aValue = a[sortConfig.key!];
        const bValue = b[sortConfig.key!];

        if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    }

    setFilteredCards(filtered);
  }, [cards, searchTerm, sortConfig]);

  const handleSort = (key: keyof Card) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const formatCurrency = (value: number | string) => {
    if (typeof value === "number") {
      return `€${value.toFixed(2)}`;
    }
    return value;
  };

  const getRarityColor = (rarity: string) => {
    const colors: { [key: string]: string } = {
      Common: "text-muted",
      Uncommon: "text-green",
      Rare: "text-blue",
      "Ultra Rare": "text-gold",
      "Secret Rare": "text-red",
    };
    return colors[rarity] || "text-muted";
  };

  const SortIcon = ({ column }: { column: keyof Card }) => {
    if (sortConfig.key !== column) {
      return <span className="ml-1 text-muted">↕</span>;
    }
    return (
      <span className="ml-1">{sortConfig.direction === "asc" ? "↑" : "↓"}</span>
    );
  };

  return (
    <div className="card overflow-hidden">
      <div className="card-header">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold text-primary">Card Collection</h2>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Search cards..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input"
            />
            <span className="text-sm text-secondary">
              {filteredCards.length} cards
            </span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="table min-w-full">
          <thead className="table-header">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-tertiary"
                onClick={() => handleSort("name")}
              >
                Card Name <SortIcon column="name" />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-tertiary"
                onClick={() => handleSort("number")}
              >
                Number <SortIcon column="number" />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-tertiary"
                onClick={() => handleSort("rarity")}
              >
                Rarity <SortIcon column="rarity" />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-tertiary"
                onClick={() => handleSort("current_price")}
              >
                Current Price <SortIcon column="current_price" />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-tertiary"
                onClick={() => handleSort("supply")}
              >
                Supply <SortIcon column="supply" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                Expansion
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                PSA Grade
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-secondary">
            {filteredCards.map((card) => (
              <tr key={card.id} className="table-row">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium text-primary">{card.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                  #{card.number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`text-sm font-semibold ${getRarityColor(
                      card.rarity
                    )}`}
                  >
                    {card.rarity}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green">
                  {formatCurrency(card.current_price)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary text-center">
                  {card.supply}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                  {card.expansion}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gold font-medium">
                  {card.psa}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onCardUpdate?.(card)}
                      className="text-blue hover:text-blue transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onCardDelete?.(card.id)}
                      className="text-red hover:text-red transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredCards.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">No cards found</div>
          <div className="text-gray-400 text-sm mt-2">
            Try adjusting your search criteria
          </div>
        </div>
      )}
    </div>
  );
};

export default CardTable;
