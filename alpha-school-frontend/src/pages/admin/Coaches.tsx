import { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminCoaches() {
  const [coaches, setCoaches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/admin/coaches').then(setCoaches).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Coaches</h1>
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Coach</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Salón</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Especialización</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {coaches.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center text-teal-700 font-medium text-sm">
                      {c.first_name?.[0]}{c.last_name?.[0]}
                    </div>
                    <span className="text-sm font-medium text-gray-900">{c.first_name} {c.last_name}</span>
                  </div>
                </td>
                <td className="px-5 py-3 text-sm text-gray-600">{c.email}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{c.classroom_name || '—'}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{c.specialization || '—'}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {c.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
