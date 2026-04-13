import { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminParents() {
  const [parents, setParents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/admin/parents').then(setParents).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Padres de Familia</h1>
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
        <table className="w-full min-w-[500px]">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Padre/Madre</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Teléfono</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Hijos</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {parents.map(p => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-sm font-medium text-gray-900">{p.first_name} {p.last_name}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{p.email}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{p.phone || '—'}</td>
                <td className="px-5 py-3">
                  <div className="flex gap-1 flex-wrap">
                    {p.children?.map((c: any) => (
                      <span key={c.id} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs">{c.first_name} {c.last_name}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
