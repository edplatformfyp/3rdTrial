import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Bell } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import NewModule from '../components/NewModule';
import RoadmapView from '../components/RoadmapView';
import StudentProfile from '../components/StudentProfile';
import NotesView from '../components/NotesView';
import ThemeToggle from '../components/ThemeToggle';

const StudentDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [selectedCourseId, setSelectedCourseId] = useState(null);
    const [viewMode, setViewMode] = useState('new'); // 'new', 'course'
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [pendingTokens, setPendingTokens] = useState([]);

    useEffect(() => {
        const fetchPendingTokens = async () => {
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/marketplace/tokens/pending`, { withCredentials: true });
                setPendingTokens(res.data);
            } catch (err) {
                console.error('Failed to fetch pending tokens', err);
            }
        };
        fetchPendingTokens();
    }, []);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleCourseCreated = (courseId) => {
        setSelectedCourseId(courseId);
        setViewMode('course');
    };

    return (
        <div className="flex bg-deep-space min-h-screen text-gray-100 font-rajdhani">
            {/* Sidebar */}
            <Sidebar
                selectedCourseId={selectedCourseId}
                onSelectCourse={setSelectedCourseId}
                onViewChange={setViewMode}
                onToggle={setSidebarCollapsed}
                viewMode={viewMode}
            />

            {/* Main Content */}
            <div className={`flex-1 ${sidebarCollapsed ? 'mr-20' : 'mr-64'} flex flex-col h-screen transition-all duration-300`}>
                {/* Top Navbar */}
                <header className="h-16 border-b border-neon-blue/20 bg-deep-space/80 backdrop-blur-md flex justify-between items-center px-8 sticky top-0 z-10">
                    <h1 className="text-xl font-orbitron tracking-widest text-white">
                        <span className="text-neon-blue">STUDENT</span> COMMAND CENTER
                    </h1>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 text-sm text-neon-purple font-mono border border-neon-purple/30 px-3 py-1 rounded-full bg-neon-purple/5">
                            <User size={14} />
                            <span>AGENT: {user?.username?.toUpperCase()}</span>
                        </div>

                        <button
                            onClick={handleLogout}
                            className="text-gray-400 hover:text-red-500 transition-colors"
                            title="Terminate Session"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </header>

                {/* Pending Tokens Alert */}
                {pendingTokens.length > 0 && (
                    <div className="bg-neon-purple/20 border-b border-neon-purple/50 p-4 animate-in slide-in-from-top-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Bell className="text-neon-purple animate-bounce" size={20} />
                            <h3 className="text-white font-bold tracking-wide">Action Required: Pending Course Enrollments</h3>
                        </div>
                        <div className="space-y-2">
                            {pendingTokens.map(token => (
                                <div key={token.token_value} className="flex items-center justify-between bg-black/30 p-3 rounded-lg border border-white/5">
                                    <div>
                                        <p className="font-bold text-white tracking-wide">{token.course_topic}</p>
                                        <p className="text-xs text-neon-purple/80">Expires: {new Date(token.expiry_date).toLocaleString()}</p>
                                    </div>
                                    <Link
                                        to={`/activate?token=${token.token_value}&signature=${token.signature}`}
                                        className="bg-neon-purple/20 border border-neon-purple text-neon-purple px-4 py-2 flex items-center justify-center rounded-lg text-sm font-bold hover:bg-neon-purple/30 transition-colors shadow-[0_0_10px_rgba(188,19,254,0.2)]"
                                    >
                                        Activate Now
                                    </Link>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Dashboard Body */}
                <main className="flex-1 overflow-hidden p-6 relative">
                    {viewMode === 'new' && (
                        <NewModule onCourseCreated={handleCourseCreated} />
                    )}

                    {viewMode === 'profile' && <StudentProfile />}
                    {viewMode === 'notes' && <NotesView />}
                    {viewMode === 'settings' && (
                        <div className="h-full overflow-y-auto">
                            <h2 className="text-2xl font-orbitron text-white mb-6">Platform Settings</h2>
                            <ThemeToggle />
                        </div>
                    )}

                    {viewMode === 'course' && selectedCourseId && (
                        <RoadmapView courseId={selectedCourseId} />
                    )}

                    {viewMode === 'course' && !selectedCourseId && (
                        <div className="h-full flex items-center justify-center text-gray-500">
                            Select a module from the library or initialize a new one.
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default StudentDashboard;
