import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminNavbar from '../../components/AdminNavbar';
import StatsCards from '../../components/StatsCards';
import LoadingSpinner from '../../components/LoadingSpinner';
import { fetchAdminDashboard } from '../../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAdminDashboard()
      .then(setData)
      .catch((err) => {
        if (err.response?.status === 403) {
          navigate('/admin/login');
        } else {
          setError('Failed to load dashboard');
        }
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminNavbar />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

        {loading && <LoadingSpinner />}
        {error && <p className="text-red-600">{error}</p>}

        {data && (
          <>
            <StatsCards stats={data.stats} />

            <div className="mt-8 bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h2 className="font-semibold">Recent Site Visits</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3">Page</th>
                      <th className="text-left p-3">IP</th>
                      <th className="text-left p-3">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_visits?.map((visit) => (
                      <tr key={visit.id} className="border-t">
                        <td className="p-3">{visit.page_visited}</td>
                        <td className="p-3">{visit.ip_address}</td>
                        <td className="p-3">
                          {visit.visited_at ? new Date(visit.visited_at).toLocaleString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                    {data.recent_visits?.length === 0 && (
                      <tr>
                        <td colSpan={3} className="p-3 text-center text-gray-500">No visits yet</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
