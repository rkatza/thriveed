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
      <Route path="/admin" element={<Layout><AdminDashboard /></Layout>} />
      <Route path="/admin/students" element={<Layout><AdminStudents /></Layout>} />
      <Route path="/admin/students/:id" element={<Layout><StudentDetail /></Layout>} />
      <Route path="/admin/coaches" element={<Layout><AdminCoaches /></Layout>} />
      <Route path="/admin/parents" element={<Layout><AdminParents /></Layout>} />
      <Route path="/admin/curriculum" element={<Layout><Curriculum /></Layout>} />
      <Route path="/admin/audit" element={<Layout><AuditLog /></Layout>} />
      <Route path="/admin/invitations" element={<Layout><Invitations /></Layout>} />

      {/* Student routes */}
      <Route path="/student" element={<Layout><StudentDashboard /></Layout>} />
      <Route path="/student/placement-test" element={<PlacementTest />} />
      <Route path="/student/progress" element={<Layout><StudentProgress /></Layout>} />
      <Route path="/student/skills" element={<Layout><StudentSkills /></Layout>} />
      <Route path="/student/achievements" element={<Layout><StudentAchievements /></Layout>} />

      {/* Coach routes */}
      <Route path="/coach" element={<Layout><CoachClassroom /></Layout>} />
      <Route path="/coach/student/:id" element={<Layout><CoachStudentDetail /></Layout>} />
      <Route path="/coach/summary" element={<Layout><CoachSummary /></Layout>} />
      <Route path="/coach/messages" element={<Layout><CoachMessages /></Layout>} />

      {/* Parent routes */}
      <Route path="/parent" element={<Layout><ParentDashboard /></Layout>} />
      <Route path="/parent/skills" element={<Layout><ParentSkills /></Layout>} />
      <Route path="/parent/messages" element={<Layout><ParentMessages /></Layout>} />

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
