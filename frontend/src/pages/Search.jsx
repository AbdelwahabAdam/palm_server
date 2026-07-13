import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import SearchBar from '../components/SearchBar';
import PalmCard from '../components/PalmCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { searchPalms } from '../services/api';

const Search = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);

  const palmCode = searchParams.get('palm_code') || '';
  const donnerName = searchParams.get('donner_name') || '';
  const donnerPhone = searchParams.get('donner_phone') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  useEffect(() => {
    setLoading(true);
    searchPalms({ palm_code: palmCode, donner_name: donnerName, donner_phone: donnerPhone, page })
      .then(setResults)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [palmCode, donnerName, donnerPhone, page]);

  const goToPage = (newPage) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', String(newPage));
    setSearchParams(params);
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Search Results</h1>
        <SearchBar initialValues={{ palm_code: palmCode, donner_name: donnerName, donner_phone: donnerPhone }} />

        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            <p className="text-gray-600 mb-4">
              Found {results?.total || 0} palm{results?.total !== 1 ? 's' : ''}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results?.palms?.map((palm) => (
                <PalmCard key={palm.id} palm={palm} />
              ))}
            </div>
            {results?.palms?.length === 0 && (
              <p className="text-center text-gray-500 py-8">No palms found matching your criteria.</p>
            )}
            {results?.pages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <button
                  disabled={page <= 1}
                  onClick={() => goToPage(page - 1)}
                  className="px-4 py-2 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2">Page {page} of {results.pages}</span>
                <button
                  disabled={page >= results.pages}
                  onClick={() => goToPage(page + 1)}
                  className="px-4 py-2 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default Search;
