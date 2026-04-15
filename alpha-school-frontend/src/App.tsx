import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import Layout from './components/Layout';
import RoleSwitcher from './pages/Login';

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

function RoleGuard({ children, roles }: { children: React.ReactNode; roles: string[] }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" />;
  if (!roles.includes(user.role)) return <Navigate to="/" />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <Routes>
      {/* Role switcher — landing page */}
      <Route path="/" element={user ? <Navigate to={
        user.role === 'student' ? '/student' :
        user.role === 'coach' ? '/coach' :
        user.role === 'parent' ? '/parent' : '/admin'
      } /> : <RoleSwitcher />} />

      {/* Admin routes */}
      <Route path="/admin" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><AdminDashboard /></Layout></RoleGuard>} />
      <Route path="/admin/students" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><AdminStudents /></Layout></RoleGuard>} />
      <Route path="/admin/students/:id" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><StudentDetail /></Layout></RoleGuard>} />
      <Route path="/admin/coaches" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><AdminCoaches /></Layout></RoleGuard>} />
      <Route path="/admin/parents" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><AdminParents /></Layout></RoleGuard>} />
      <Route path="/admin/curriculum" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><Curriculum /></Layout></RoleGuard>} />
      <Route path="/admin/audit" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><AuditLog /></Layout></RoleGuard>} />
      <Route path="/admin/invitations" element={<RoleGuard roles={['super_admin', 'admin']}><Layout><Invitations /></Layout></RoleGuard>} />

      {/* Student routes */}
      <Route path="/student" element={<RoleGuard roles={['student']}><Layout><StudentDashboard /></Layout></RoleGuard>} />
      <Route path="/student/placement-test" element={<RoleGuard roles={['student']}><PlacementTest /></RoleGuard>} />
      <Route path="/student/progress" element={<RoleGuard roles={['student']}><Layout><StudentProgress /></Layout></RoleGuard>} />
      <Route path="/student/skills" element={<RoleGuard roles={['student']}><Layout><StudentSkills /></Layout></RoleGuard>} />
      <Route path="/student/achievements" element={<RoleGuard roles={['student']}><Layout><StudentAchievements /></Layout></RoleGuard>} />

      {/* Coach routes */}
      <Route path="/coach" element={<RoleGuard roles={['coach']}><Layout><CoachClassroom /></Layout></RoleGuard>} />
      <Route path="/coach/student/:id" element={<RoleGuard roles={['coach']}><Layout><CoachStudentDetail /></Layout></RoleGuard>} />
      <Route path="/coach/summary" element={<RoleGuard roles={['coach']}><Layout><CoachSummary /></Layout></RoleGuard>} />
      <Route path="/coach/messages" element={<RoleGuard roles={['coach']}><Layout><CoachMessages /></Layout></RoleGuard>} />

      {/* Parent routes */}
      <Route path="/parent" element={<RoleGuard roles={['parent']}><Layout><ParentDashboard /></Layout></RoleGuard>} />
      <Route path="/parent/skills" element={<RoleGuard roles={['parent']}><Layout><ParentSkills /></Layout></RoleGuard>} />
      <Route path="/parent/messages" element={<RoleGuard roles={['parent']}><Layout><ParentMessages /></Layout></RoleGuard>} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" />} />
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
