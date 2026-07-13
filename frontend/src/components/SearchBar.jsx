import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SearchBar = ({ initialValues = {} }) => {
  const navigate = useNavigate();
  const [palmCode, setPalmCode] = useState(initialValues.palm_code || '');
  const [donnerName, setDonnerName] = useState(initialValues.donner_name || '');
  const [donnerPhone, setDonnerPhone] = useState(initialValues.donner_phone || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (palmCode) params.set('palm_code', palmCode);
    if (donnerName) params.set('donner_name', donnerName);
    if (donnerPhone) params.set('donner_phone', donnerPhone);
    navigate(`/search?${params.toString()}`);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 mb-8">
      <h2 className="text-lg font-semibold mb-4">Search Palms</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="Palm Code"
          value={palmCode}
          onChange={(e) => setPalmCode(e.target.value)}
          className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-palm-500"
        />
        <input
          type="text"
          placeholder="Donner Name"
          value={donnerName}
          onChange={(e) => setDonnerName(e.target.value)}
          className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-palm-500"
        />
        <input
          type="text"
          placeholder="Donner Phone"
          value={donnerPhone}
          onChange={(e) => setDonnerPhone(e.target.value)}
          className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-palm-500"
        />
      </div>
      <button
        type="submit"
        className="mt-4 bg-palm-600 hover:bg-palm-700 text-white px-6 py-2 rounded"
      >
        Search
      </button>
    </form>
  );
};

export default SearchBar;
