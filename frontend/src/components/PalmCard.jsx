import { Link } from 'react-router-dom';

const PalmCard = ({ palm }) => (
  <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition">
    <div className="flex gap-4 items-start">
      {palm.images?.[0] ? (
        <img src={palm.images[0]} alt={palm.palm_code} className="h-16 w-16 rounded object-cover flex-shrink-0" />
      ) : (
        <div className="h-16 w-16 rounded bg-gray-200 flex items-center justify-center text-xs text-gray-500 flex-shrink-0">
          No img
        </div>
      )}
      <div className="flex justify-between items-start flex-1">
        <div>
          <h3 className="font-semibold text-lg">{palm.palm_code}</h3>
          <p className="text-gray-600 text-sm">ID: {palm.palm_id}</p>
          {palm.donner_name && (
            <p className="text-gray-600 text-sm mt-1">Donner: {palm.donner_name}</p>
          )}
          {palm.area && (
            <p className="text-gray-500 text-sm">{palm.area} - {palm.section}</p>
          )}
        </div>
        <Link
          to={`/palm/${palm.id}`}
          className="text-palm-600 hover:text-palm-800 text-sm font-medium"
        >
          View →
        </Link>
      </div>
    </div>
  </div>
);

export default PalmCard;
