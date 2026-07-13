import { Link } from 'react-router-dom';
import { adminLogout } from '../services/api';

const AdminNavbar = () => {
  const handleLogout = async () => {
    try {
      await adminLogout();
    } finally {
      window.location.href = '/admin/login';
    }
  };

  return (
    <header className="bg-gray-800 text-white shadow">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/admin" className="text-xl font-bold hover:text-gray-300">
          Admin Panel
        </Link>
        <nav className="flex gap-4 items-center">
          <Link to="/admin" className="hover:text-gray-300">Dashboard</Link>
          <Link to="/admin/palms" className="hover:text-gray-300">Palms</Link>
          <Link to="/admin/reports" className="hover:text-gray-300">Reports</Link>
          <Link to="/" className="hover:text-gray-300">Public Site</Link>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
          >
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
};

export default AdminNavbar;
