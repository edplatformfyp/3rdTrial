import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Signup from './pages/Signup';
import StudentDashboard from './pages/StudentDashboard';
import ParentDashboard from './pages/ParentDashboard';
import OrgDashboard from './pages/OrgDashboard';
import OrgCourseEditor from './pages/OrgCourseEditor';
import AdminDashboard from './pages/AdminDashboard';
import CourseMarketplace from './pages/CourseMarketplace';
import ExamView from './pages/ExamView';
import ExamResult from './pages/ExamResult';
import MockPayment from './pages/MockPayment';
import ActivationPage from './pages/ActivationPage';
import CertificateVerification from './pages/CertificateVerification';
import { ThemeProvider } from './context/ThemeContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div className="min-h-screen flex items-center justify-center text-neon-blue">LOADING SYSTEM...</div>;

  if (!user) return <Navigate to="/login" />;

  return children;
};

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/student" element={
              <ProtectedRoute>
                <StudentDashboard />
              </ProtectedRoute>
            } />
            <Route path="/parent" element={
              <ProtectedRoute>
                <ParentDashboard />
              </ProtectedRoute>
            } />
            <Route path="/org" element={
              <ProtectedRoute>
                <OrgDashboard />
              </ProtectedRoute>
            } />
            <Route path="/org/course/:courseId" element={
              <ProtectedRoute>
                <OrgCourseEditor />
              </ProtectedRoute>
            } />
            <Route path="/admin" element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/marketplace" element={
              <ProtectedRoute>
                <CourseMarketplace />
              </ProtectedRoute>
            } />
            <Route path="/course/:courseId/exam" element={
              <ProtectedRoute>
                <ExamView />
              </ProtectedRoute>
            } />
            <Route path="/course/:courseId/exam/result" element={
              <ProtectedRoute>
                <ExamResult />
              </ProtectedRoute>
            } />
            <Route path="/checkout/:sessionId" element={
              <ProtectedRoute>
                <MockPayment />
              </ProtectedRoute>
            } />
            <Route path="/activate" element={
              <ProtectedRoute>
                <ActivationPage />
              </ProtectedRoute>
            } />
            <Route path="/verify/:certId" element={<CertificateVerification />} />
            <Route path="/" element={<Navigate to="/student" />} />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
