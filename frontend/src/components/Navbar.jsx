import { Link } from 'react-router-dom';

const Navbar = () => (
  <header className="bg-palm-700 text-white shadow">
    <div className="container mx-auto px-4 py-4 flex items-center justify-between">
      <Link to="/" className="text-2xl font-bold hover:text-palm-100">
        🌴 Palm Management
      </Link>
      <nav className="flex gap-4">
        <Link to="/" className="hover:text-palm-100">Home</Link>
        <Link to="/search" className="hover:text-palm-100">Search</Link>
        <Link to="/admin/login" className="hover:text-palm-100">Admin</Link>
      </nav>
    </div>
  </header>
);

export default Navbar;
