import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Trophy, Flame, Star, Lock, Sparkles } from 'lucide-react';

interface Badge {
  id?: number;
  badge_id?: string;
  title: string;
  description: string;
  icon: string;
  category?: string;
  earned_at?: string;
  locked?: boolean;
}

interface GamificationStats {
  level: number;
  title: string;
  icon: string;
  total_xp: number;
  xp_in_level: number;
  xp_for_next: number;
  progress_percent: number;
  next_level_xp: number;
  streak_days: number;
  longest_streak: number;
  completed_sessions: number;
  perfect_sessions: number;
  recent_badges: Badge[];
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  streak: { label: 'Rachas', color: 'bg-orange-100 text-orange-700' },
  session: { label: 'Sesiones', color: 'bg-blue-100 text-blue-700' },
  mastery: { label: 'Dominio', color: 'bg-purple-100 text-purple-700' },
  special: { label: 'Especial', color: 'bg-amber-100 text-amber-700' },
};

export default function StudentAchievements() {
  const [achievements, setAchievements] = useState<{ earned: Badge[]; available: Badge[]; total_earned: number; total_available: number } | null>(null);
  const [stats, setStats] = useState<GamificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [showNewBadge, setShowNewBadge] = useState<Badge | null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/student/achievements'),
      api.get('/api/student/gamification'),
    ]).then(([ach, gam]) => {
      setAchievements(ach);
      setStats(gam);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>
  );

  const earned = achievements?.earned || [];
  const available = achievements?.available || [];
  const allBadges = [...earned.map(b => ({ ...b, locked: false })), ...available];
  const filtered = filter === 'all' ? allBadges : allBadges.filter(b => b.category === filter);

  return (
    <div>
      {/* New Badge Animation Overlay */}
      {showNewBadge && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
             onClick={() => setShowNewBadge(null)}>
          <div className="bg-white rounded-3xl p-10 text-center max-w-sm mx-4"
               onClick={e => e.stopPropagation()}>
            <div className="text-7xl mb-4">{showNewBadge.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Logro Desbloqueado</h2>
            <h3 className="text-xl font-semibold text-indigo-600 mb-2">{showNewBadge.title}</h3>
            <p className="text-gray-500">{showNewBadge.description}</p>
            <button onClick={() => setShowNewBadge(null)}
              className="mt-6 px-6 py-2 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition">
              Cerrar
            </button>
          </div>
        </div>
      )}

      {/* Header with Level & Stats */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Trophy size={24} />
              <h1 className="text-2xl font-bold">Mis Logros</h1>
            </div>
            <p className="text-amber-100">
              {earned.length} de {achievements?.total_available || 0} badges desbloqueados
            </p>
          </div>
          {stats && (
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="flex items-center gap-1 justify-center">
                  <Flame size={18} className="text-yellow-200" />
                  <span className="text-2xl font-bold">{stats.streak_days}</span>
                </div>
                <p className="text-xs text-amber-200">Racha</p>
              </div>
              <div className="text-center">
                <div className="flex items-center gap-1 justify-center">
                  <Star size={18} className="text-yellow-200" />
                  <span className="text-2xl font-bold">{stats.completed_sessions}</span>
                </div>
                <p className="text-xs text-amber-200">Sesiones</p>
              </div>
              <div className="text-center">
                <div className="flex items-center gap-1 justify-center">
                  <Sparkles size={18} className="text-yellow-200" />
                  <span className="text-2xl font-bold">{stats.perfect_sessions}</span>
                </div>
                <p className="text-xs text-amber-200">Perfectas</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Level Progress Card */}
      {stats && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-3xl">
              {stats.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="text-sm text-gray-500">Nivel {stats.level}</span>
                  <h3 className="text-lg font-bold text-gray-900">{stats.title}</h3>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-indigo-600">{stats.total_xp} XP</span>
                  <p className="text-xs text-gray-400">{stats.xp_in_level}/{stats.xp_for_next} para nivel {stats.level + 1}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-1000"
                  style={{ width: `${stats.progress_percent}%` }}
                />
              </div>
            </div>
          </div>

          {/* Streak & Stats Row */}
          <div className="grid grid-cols-4 gap-4 mt-5 pt-5 border-t border-gray-100">
            <div className="text-center">
              <div className="text-2xl mb-1">&#x1F525;</div>
              <div className="text-lg font-bold text-gray-900">{stats.streak_days}</div>
              <div className="text-xs text-gray-500">Racha actual</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">&#x1F3C6;</div>
              <div className="text-lg font-bold text-gray-900">{stats.longest_streak}</div>
              <div className="text-xs text-gray-500">Mejor racha</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">&#x1F4DA;</div>
              <div className="text-lg font-bold text-gray-900">{stats.completed_sessions}</div>
              <div className="text-xs text-gray-500">Sesiones</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">&#x1F4AF;</div>
              <div className="text-lg font-bold text-gray-900">{stats.perfect_sessions}</div>
              <div className="text-xs text-gray-500">Perfectas</div>
            </div>
          </div>
        </div>
      )}

      {/* Category Filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition
            ${filter === 'all' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
        >
          Todos ({allBadges.length})
        </button>
        {Object.entries(CATEGORY_LABELS).map(([key, { label }]) => {
          const count = allBadges.filter(b => b.category === key).length;
          const earnedCount = earned.filter(b => b.category === key).length;
          return (
            <button key={key}
              onClick={() => setFilter(key)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition
                ${filter === key ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {label} ({earnedCount}/{count})
            </button>
          );
        })}
      </div>

      {/* Badges Grid */}
      {filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-gray-100 shadow-sm">
          <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Sin logros en esta categoria</h2>
          <p className="text-gray-500">Completa ejercicios y misiones para ganar logros.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((badge, idx) => {
            const isLocked = badge.locked;
            const catStyle = CATEGORY_LABELS[badge.category || 'special'];
            return (
              <div key={badge.badge_id || badge.id || idx}
                onClick={() => !isLocked && setShowNewBadge(badge)}
                className={`relative bg-white rounded-xl p-5 border shadow-sm text-center transition cursor-pointer
                  ${isLocked
                    ? 'border-gray-200 opacity-60 hover:opacity-80'
                    : 'border-gray-100 hover:shadow-lg hover:-translate-y-1'
                  }`}
              >
                {isLocked && (
                  <div className="absolute top-2 right-2">
                    <Lock size={14} className="text-gray-400" />
                  </div>
                )}
                <span className={`text-4xl block mb-3 ${isLocked ? 'grayscale' : ''}`}>
                  {badge.icon}
                </span>
                <h3 className={`font-semibold mb-1 text-sm ${isLocked ? 'text-gray-400' : 'text-gray-900'}`}>
                  {badge.title}
                </h3>
                <p className={`text-xs mb-2 ${isLocked ? 'text-gray-300' : 'text-gray-500'}`}>
                  {badge.description}
                </p>
                <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${catStyle?.color || 'bg-gray-100 text-gray-600'}`}>
                  {catStyle?.label || badge.category}
                </span>
                {!isLocked && badge.earned_at && (
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(badge.earned_at).toLocaleDateString('es-PA')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
