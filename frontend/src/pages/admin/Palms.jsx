import { useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import AdminNavbar from '../../components/AdminNavbar';

import LoadingSpinner from '../../components/LoadingSpinner';

import {

  adminAddPalm,

  adminDeletePalm,

  adminUpdatePalm,

  fetchAdminPalms,

} from '../../services/api';



const emptyForm = {

  palm_id: '',

  palm_code: '',

  plant_date: '',

  donner_name: '',

  donner_phone_number: '',

  harvest_amount: '',

  last_harvest: '',

  age: '',

  area: '',

  section: '',

  images: [],

};



const emptyFilters = {

  palm_code: '',

  donner_name: '',

  donner_phone: '',

  area: '',

  section: '',

};



const Palms = () => {

  const navigate = useNavigate();

  const [palms, setPalms] = useState([]);

  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState(emptyForm);

  const [filters, setFilters] = useState(emptyFilters);

  const [appliedFilters, setAppliedFilters] = useState(emptyFilters);

  const [editingId, setEditingId] = useState(null);

  const [existingImages, setExistingImages] = useState([]);

  const [error, setError] = useState('');

  const [page, setPage] = useState(1);

  const [totalPages, setTotalPages] = useState(1);

  const [total, setTotal] = useState(0);



  const loadPalms = () => {

    setLoading(true);

    const params = { page, ...appliedFilters };

    Object.keys(params).forEach((key) => {

      if (!params[key]) delete params[key];

    });



    fetchAdminPalms(params)

      .then((data) => {

        setPalms(data.palms);

        setTotalPages(data.pages);

        setTotal(data.total);

      })

      .catch((err) => {

        if (err.response?.status === 403) navigate('/admin/login');

      })

      .finally(() => setLoading(false));

  };



  useEffect(() => {

    loadPalms();

  }, [page, appliedFilters]);



  const handleChange = (e) => {

    const { name, value, files } = e.target;

    if (name === 'images') {

      setForm({ ...form, images: Array.from(files) });

    } else {

      setForm({ ...form, [name]: value });

    }

  };



  const handleFilterChange = (e) => {

    setFilters({ ...filters, [e.target.name]: e.target.value });

  };



  const handleSearch = (e) => {

    e.preventDefault();

    setPage(1);

    setAppliedFilters({ ...filters });

  };



  const handleClearFilters = () => {

    setFilters(emptyFilters);

    setAppliedFilters(emptyFilters);

    setPage(1);

  };



  const handleSubmit = async (e) => {

    e.preventDefault();

    setError('');

    try {

      if (editingId) {

        await adminUpdatePalm(editingId, form);

      } else {

        await adminAddPalm(form);

      }

      setForm(emptyForm);

      setExistingImages([]);

      setEditingId(null);

      setShowForm(false);

      loadPalms();

    } catch (err) {

      setError(err.response?.data?.error || 'Operation failed');

    }

  };



  const handleEdit = (palm) => {

    setEditingId(palm.id);

    setExistingImages(palm.images || []);

    setForm({

      palm_id: palm.palm_id,

      palm_code: palm.palm_code,

      plant_date: palm.plant_date?.split('T')[0] || '',

      donner_name: palm.donner_name || '',

      donner_phone_number: palm.donner_phone_number || '',

      harvest_amount: palm.harvest_amount || '',

      last_harvest: palm.last_harvest?.split('T')[0] || '',

      age: palm.age || '',

      area: palm.area || '',

      section: palm.section || '',

      images: [],

    });

    setShowForm(true);

    window.scrollTo({ top: 0, behavior: 'smooth' });

  };



  const handleDelete = async (id) => {

    if (!window.confirm('Delete this palm profile?')) return;

    try {

      await adminDeletePalm(id);

      loadPalms();

    } catch (err) {

      setError(err.response?.data?.error || 'Delete failed');

    }

  };



  return (

    <div className="min-h-screen bg-gray-50">

      <AdminNavbar />

      <main className="container mx-auto px-4 py-8">

        <div className="flex justify-between items-center mb-6">

          <h1 className="text-2xl font-bold">Palm Management</h1>

          <button

            onClick={() => {

              setShowForm(!showForm);

              setEditingId(null);

              setExistingImages([]);

              setForm(emptyForm);

            }}

            className="bg-palm-600 hover:bg-palm-700 text-white px-4 py-2 rounded"

          >

            {showForm ? 'Cancel' : 'Add Palm'}

          </button>

        </div>



        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-4 mb-6 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">

          <input

            name="palm_code"

            placeholder="Palm code"

            value={filters.palm_code}

            onChange={handleFilterChange}

            className="border rounded px-3 py-2"

          />

          <input

            name="donner_name"

            placeholder="Donner name"

            value={filters.donner_name}

            onChange={handleFilterChange}

            className="border rounded px-3 py-2"

          />

          <input

            name="donner_phone"

            placeholder="Donner phone"

            value={filters.donner_phone}

            onChange={handleFilterChange}

            className="border rounded px-3 py-2"

          />

          <input

            name="area"

            placeholder="Area"

            value={filters.area}

            onChange={handleFilterChange}

            className="border rounded px-3 py-2"

          />

          <input

            name="section"

            placeholder="Section"

            value={filters.section}

            onChange={handleFilterChange}

            className="border rounded px-3 py-2"

          />

          <div className="flex gap-2">

            <button type="submit" className="flex-1 bg-palm-600 text-white rounded px-3 py-2">Search</button>

            <button type="button" onClick={handleClearFilters} className="px-3 py-2 border rounded">Clear</button>

          </div>

        </form>



        {showForm && (

          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">

            <h2 className="md:col-span-2 text-lg font-semibold">

              {editingId ? 'Edit Palm' : 'Add New Palm'}

            </h2>

            {['palm_id', 'palm_code', 'plant_date', 'donner_name', 'donner_phone_number',

              'harvest_amount', 'last_harvest', 'age', 'area', 'section'].map((field) => (

              <div key={field}>

                <label className="block text-sm font-medium capitalize mb-1">

                  {field.replace(/_/g, ' ')}

                </label>

                <input

                  name={field}

                  type={field.includes('date') ? 'date' : field === 'age' || field === 'harvest_amount' ? 'number' : 'text'}

                  value={form[field]}

                  onChange={handleChange}

                  required={['palm_id', 'palm_code', 'plant_date'].includes(field)}

                  className="w-full border rounded px-3 py-2"

                />

              </div>

            ))}

            <div className="md:col-span-2">

              <label className="block text-sm font-medium mb-1">

                {editingId ? 'Add Images' : 'Images'}

              </label>

              <input name="images" type="file" multiple accept="image/*" onChange={handleChange} />

              <p className="text-xs text-gray-500 mt-1">

                Uses S3 when configured, otherwise stores images locally.

              </p>

            </div>

            {existingImages.length > 0 && (

              <div className="md:col-span-2">

                <p className="text-sm font-medium mb-2">Current Images</p>

                <div className="flex flex-wrap gap-2">

                  {existingImages.map((url) => (

                    <img

                      key={url}

                      src={url}

                      alt="Palm"

                      className="h-20 w-20 object-cover rounded border"

                    />

                  ))}

                </div>

              </div>

            )}

            {error && <p className="text-red-600 md:col-span-2">{error}</p>}

            <button type="submit" className="md:col-span-2 bg-palm-600 text-white py-2 rounded">

              {editingId ? 'Update Palm' : 'Create Palm'}

            </button>

          </form>

        )}



        <p className="text-sm text-gray-600 mb-3">{total} palm(s) found</p>



        {loading ? (

          <LoadingSpinner />

        ) : (

          <div className="bg-white rounded-lg shadow overflow-x-auto">

            <table className="w-full text-sm">

              <thead className="bg-gray-50">

                <tr>

                  <th className="text-left p-3">Image</th>

                  <th className="text-left p-3">Code</th>

                  <th className="text-left p-3">Donner</th>

                  <th className="text-left p-3">Phone</th>

                  <th className="text-left p-3">Area</th>

                  <th className="text-left p-3">Section</th>

                  <th className="text-left p-3">Age</th>

                  <th className="text-left p-3">Actions</th>

                </tr>

              </thead>

              <tbody>

                {palms.map((palm) => (

                  <tr key={palm.id} className="border-t">

                    <td className="p-3">

                      {palm.images?.[0] ? (

                        <img src={palm.images[0]} alt={palm.palm_code} className="h-12 w-12 object-cover rounded" />

                      ) : (

                        <span className="text-gray-400 text-xs">No image</span>

                      )}

                    </td>

                    <td className="p-3 font-medium">{palm.palm_code}</td>

                    <td className="p-3">{palm.donner_name}</td>

                    <td className="p-3">{palm.donner_phone_number}</td>

                    <td className="p-3">{palm.area}</td>

                    <td className="p-3">{palm.section}</td>

                    <td className="p-3">{palm.age}</td>

                    <td className="p-3 space-x-2">

                      <button onClick={() => handleEdit(palm)} className="text-blue-600 hover:underline">Edit</button>

                      <button onClick={() => handleDelete(palm.id)} className="text-red-600 hover:underline">Delete</button>

                    </td>

                  </tr>

                ))}

                {palms.length === 0 && (

                  <tr>

                    <td colSpan={8} className="p-6 text-center text-gray-500">No palms match your search.</td>

                  </tr>

                )}

              </tbody>

            </table>

            {totalPages > 1 && (

              <div className="flex justify-center gap-2 p-4">

                <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded disabled:opacity-50">Prev</button>

                <span>Page {page} of {totalPages}</span>

                <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded disabled:opacity-50">Next</button>

              </div>

            )}

          </div>

        )}

      </main>

    </div>

  );

};



export default Palms;


