import { useEffect, useState } from 'react';

import { Link, useParams } from 'react-router-dom';

import Navbar from '../components/Navbar';

import LoadingSpinner from '../components/LoadingSpinner';

import { getPalmDetail } from '../services/api';



const PalmDetail = () => {

  const { id } = useParams();

  const [palm, setPalm] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [activeImage, setActiveImage] = useState(0);



  useEffect(() => {

    getPalmDetail(id)

      .then((data) => {

        setPalm(data);

        setActiveImage(0);

      })

      .catch(() => setError('Palm not found'))

      .finally(() => setLoading(false));

  }, [id]);



  const formatDate = (dateStr) => {

    if (!dateStr) return 'N/A';

    return new Date(dateStr).toLocaleDateString();

  };



  const images = palm?.images || [];



  return (

    <div className="min-h-screen">

      <Navbar />

      <main className="container mx-auto px-4 py-8">

        <Link to="/search" className="text-palm-600 hover:underline mb-4 inline-block">

          ← Back to Search

        </Link>



        {loading && <LoadingSpinner />}

        {error && <p className="text-red-600">{error}</p>}



        {palm && (

          <div className="bg-white rounded-lg shadow overflow-hidden">

            <div className="p-4 bg-gray-50">

              {images.length > 0 ? (

                <>

                  <img

                    src={images[activeImage]}

                    alt={`Palm ${palm.palm_code}`}

                    className="rounded object-cover w-full max-h-96 mb-3"

                  />

                  {images.length > 1 && (

                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">

                      {images.map((url, i) => (

                        <button

                          key={url}

                          type="button"

                          onClick={() => setActiveImage(i)}

                          className={`rounded overflow-hidden border-2 ${

                            activeImage === i ? 'border-palm-600' : 'border-transparent'

                          }`}

                        >

                          <img src={url} alt={`${palm.palm_code} ${i + 1}`} className="h-20 w-full object-cover" />

                        </button>

                      ))}

                    </div>

                  )}

                  <p className="text-sm text-gray-500 mt-2">{images.length} image(s)</p>

                </>

              ) : (

                <div className="h-48 flex items-center justify-center bg-gray-200 rounded text-gray-500">

                  No images available

                </div>

              )}

            </div>

            <div className="p-6">

              <h1 className="text-3xl font-bold text-palm-800">{palm.palm_code}</h1>

              <p className="text-gray-500">Palm ID: {palm.palm_id}</p>



              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">

                <div>

                  <h2 className="font-semibold text-gray-700 mb-2">Donner Information</h2>

                  <p><span className="text-gray-500">Name:</span> {palm.donner_name || 'N/A'}</p>

                  <p><span className="text-gray-500">Phone:</span> {palm.donner_phone_number || 'N/A'}</p>

                </div>

                <div>

                  <h2 className="font-semibold text-gray-700 mb-2">Location</h2>

                  <p><span className="text-gray-500">Area:</span> {palm.area || 'N/A'}</p>

                  <p><span className="text-gray-500">Section:</span> {palm.section || 'N/A'}</p>

                </div>

                <div>

                  <h2 className="font-semibold text-gray-700 mb-2">Growth</h2>

                  <p><span className="text-gray-500">Plant Date:</span> {formatDate(palm.plant_date)}</p>

                  <p><span className="text-gray-500">Age:</span> {palm.age ?? 'N/A'} years</p>

                </div>

                <div>

                  <h2 className="font-semibold text-gray-700 mb-2">Harvest</h2>

                  <p><span className="text-gray-500">Amount:</span> {palm.harvest_amount ?? 'N/A'} kg</p>

                  <p><span className="text-gray-500">Last Harvest:</span> {formatDate(palm.last_harvest)}</p>

                </div>

              </div>

            </div>

          </div>

        )}

      </main>

    </div>

  );

};



export default PalmDetail;


