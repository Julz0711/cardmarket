import React, { useEffect, useState } from "react";

interface ScraperStatus {
  name: string;
  running: boolean;
  [key: string]: any;
}

export const ScraperStatusIndicator: React.FC = () => {
  const [scrapers, setScrapers] = useState<ScraperStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const res = await fetch("/api/scrapers/status", {
          credentials: "include",
        });
        const data = await res.json();
        if (isMounted && data.scrapers) {
          // Convert object to array for consistent frontend usage
          const scrapersArray = Array.isArray(data.scrapers)
            ? data.scrapers
            : Object.values(data.scrapers);
          setScrapers(scrapersArray);
        }
      } catch {
        // handle error if needed
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const runningScrapers = scrapers.filter((s) => s.running);

  return (
    <div className="flex items-center ml-2">
      {loading ? (
        <span className="animate-spin mr-1 w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full"></span>
      ) : runningScrapers.length > 0 ? (
        <>
          <span className="w-3 h-3 bg-green-500 rounded-full mr-1"></span>
          <span className="text-xs text-green-700 font-semibold">
            {runningScrapers.map((s) => s.name).join(", ")}
          </span>
        </>
      ) : (
        <>
          <span className="w-3 h-3 bg-gray-400 rounded-full mr-1"></span>
          <span className="text-xs text-gray-500">Idle</span>
        </>
      )}
    </div>
  );
};
