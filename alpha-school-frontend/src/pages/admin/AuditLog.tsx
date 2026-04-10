import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Shield } from 'lucide-react';

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/admin/audit-log').then(setLogs).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Shield size={24} className="text-gray-400" />
        <h1 className="text-2xl font-bold text-gray-900">Registro de Auditoría</h1>
      </div>
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Fecha</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Usuario</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Acción</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Entidad</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Detalles</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-sm text-gray-600">{new Date(log.created_at).toLocaleString('es-PA')}</td>
                <td className="px-5 py-3 text-sm text-gray-900">{log.user_email || `User #${log.user_id}`}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                    log.action.includes('create') ? 'bg-green-100 text-green-700' :
                    log.action.includes('delete') ? 'bg-red-100 text-red-700' :
                    log.action.includes('update') ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>{log.action}</span>
                </td>
                <td className="px-5 py-3 text-sm text-gray-600">{log.entity_type} #{log.entity_id}</td>
                <td className="px-5 py-3 text-sm text-gray-500 max-w-xs truncate">{log.details || '—'}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-gray-400">No hay registros de auditoría</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
