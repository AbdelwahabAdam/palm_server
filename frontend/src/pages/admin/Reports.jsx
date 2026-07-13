import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminNavbar from '../../components/AdminNavbar';
import LoadingSpinner from '../../components/LoadingSpinner';
import { fetchAdminReports } from '../../services/api';

const Reports = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ start_date: '', end_date: '', section: '' });
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadReport = (params = filters) => {
    setLoading(true);
    fetchAdminReports(params)
      .then(setReport)
      .catch((err) => {
        if (err.response?.status === 403) navigate('/admin/login');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadReport();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    loadReport(filters);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminNavbar />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Reports</h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 mb-6 flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              className="border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              className="border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Section</label>
            <select
              value={filters.section}
              onChange={(e) => setFilters({ ...filters, section: e.target.value })}
              className="border rounded px-3 py-2"
            >
              <option value="">All</option>
              <option value="North">North</option>
              <option value="South">South</option>
              <option value="East">East</option>
              <option value="West">West</option>
            </select>
          </div>
          <button type="submit" className="bg-palm-600 text-white px-4 py-2 rounded">Generate</button>
        </form>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3">Section</th>
                  <th className="text-left p-3">Palm Count</th>
                  <th className="text-left p-3">Total Harvest (kg)</th>
                </tr>
              </thead>
              <tbody>
                {report?.report_data?.map((row) => (
                  <tr key={row.section} className="border-t">
                    <td className="p-3 font-medium">{row.section}</td>
                    <td className="p-3">{row.count}</td>
                    <td className="p-3">{row.total_harvest?.toFixed(2)}</td>
                  </tr>
                ))}
                {report?.report_data?.length === 0 && (
                  <tr>
                    <td colSpan={3} className="p-3 text-center text-gray-500">No data for selected filters</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default Reports;
