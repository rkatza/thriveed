import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import Layout from './components/Layout';
import Login from './pages/Login';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminStudents from './pages/admin/Students';
import StudentDetail from './pages/admin/StudentDetail';
import AdminCoaches from './pages/admin/Coaches';
import AdminParents from './pages/admin/Parents';
import Curriculum from './pages/admin/Curriculum';
import AuditLog from './pages/admin/AuditLog';
import Invitations from './pages/admin/Invitations';

// Student pages
import StudentDashboard from './pages/student/Dashboard';
import PlacementTest from './pages/student/PlacementTest';
import StudentProgress from './pages/student/Progress';
import StudentSkills from './pages/student/Skills';
import StudentAchievements from './pages/student/Achievements';

// Coach pages
import CoachClassroom from './pages/coach/Classroom';
import CoachStudentDetail from './pages/coach/StudentDetail';
import CoachSummary from './pages/coach/Summary';
import CoachMessages from './pages/coach/Messages';

// Parent pages
import ParentDashboard from './pages/parent/Dashboard';
import ParentSkills from './pages/parent/Skills';
import ParentMessages from './pages/parent/Messages';

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={
        user.role === 'student' ? '/student' :
        user.role === 'coach' ? '/coach' :
        user.role === 'parent' ? '/parent' : '/admin'
      } /> : <Login />} />

      {/* Admin routes */}
      <Route path="/admin" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><AdminDashboard /></Layout></ProtectedRoute>} />
      <Route path="/admin/students" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><AdminStudents /></Layout></ProtectedRoute>} />
      <Route path="/admin/students/:id" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><StudentDetail /></Layout></ProtectedRoute>} />
      <Route path="/admin/coaches" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><AdminCoaches /></Layout></ProtectedRoute>} />
      <Route path="/admin/parents" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><AdminParents /></Layout></ProtectedRoute>} />
      <Route path="/admin/curriculum" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><Curriculum /></Layout></ProtectedRoute>} />
      <Route path="/admin/audit" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><AuditLog /></Layout></ProtectedRoute>} />
      <Route path="/admin/invitations" element={<ProtectedRoute roles={['super_admin', 'admin']}><Layout><Invitations /></Layout></ProtectedRoute>} />

      {/* Student routes */}
      <Route path="/student" element={<ProtectedRoute roles={['student']}><Layout><StudentDashboard /></Layout></ProtectedRoute>} />
      <Route path="/student/placement-test" element={<ProtectedRoute roles={['student']}><PlacementTest /></ProtectedRoute>} />
      <Route path="/student/progress" element={<ProtectedRoute roles={['student']}><Layout><StudentProgress /></Layout></ProtectedRoute>} />
      <Route path="/student/skills" element={<ProtectedRoute roles={['student']}><Layout><StudentSkills /></Layout></ProtectedRoute>} />
      <Route path="/student/achievements" element={<ProtectedRoute roles={['student']}><Layout><StudentAchievements /></Layout></ProtectedRoute>} />

      {/* Coach routes */}
      <Route path="/coach" element={<ProtectedRoute roles={['coach']}><Layout><CoachClassroom /></Layout></ProtectedRoute>} />
      <Route path="/coach/student/:id" element={<ProtectedRoute roles={['coach']}><Layout><CoachStudentDetail /></Layout></ProtectedRoute>} />
      <Route path="/coach/summary" element={<ProtectedRoute roles={['coach']}><Layout><CoachSummary /></Layout></ProtectedRoute>} />
      <Route path="/coach/messages" element={<ProtectedRoute roles={['coach']}><Layout><CoachMessages /></Layout></ProtectedRoute>} />

      {/* Parent routes */}
      <Route path="/parent" element={<ProtectedRoute roles={['parent']}><Layout><ParentDashboard /></Layout></ProtectedRoute>} />
      <Route path="/parent/skills" element={<ProtectedRoute roles={['parent']}><Layout><ParentSkills /></Layout></ProtectedRoute>} />
      <Route path="/parent/messages" element={<ProtectedRoute roles={['parent']}><Layout><ParentMessages /></Layout></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
