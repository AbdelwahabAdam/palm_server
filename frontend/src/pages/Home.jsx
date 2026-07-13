import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import SearchBar from '../components/SearchBar';
import StatsCards from '../components/StatsCards';
import LoadingSpinner from '../components/LoadingSpinner';
import { fetchStatistics } from '../services/api';

const Home = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatistics()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-palm-800">Palm Management System</h1>
          <p className="text-gray-600 mt-2">Track and manage palm profiles across all areas</p>
        </div>

        <SearchBar />

        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            <StatsCards stats={stats} />
            {stats?.areas?.length > 0 && (
              <div className="mt-8 bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Palms by Area</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {stats.areas.map((area) => (
                    <div key={area.name} className="text-center p-4 bg-gray-50 rounded">
                      <p className="text-2xl font-bold text-palm-700">{area.count}</p>
                      <p className="text-gray-600 text-sm">{area.name}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default Home;
