import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Plus, Trash2, Edit, Globe, EyeOff, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ThemeToggle from '../components/ThemeToggle';

const OrgDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('overview'); // overview, courses, students, verifications
    const [analytics, setAnalytics] = useState(null);
    const [loadingAnalytics, setLoadingAnalytics] = useState(true);

    const fetchAnalytics = async () => {
        setLoadingAnalytics(true);
        try {
            const res = await axios.get('http://localhost:8000/org/analytics');
            setAnalytics(res.data);
        } catch (err) {
            console.error('Failed to fetch analytics', err);
        } finally {
            setLoadingAnalytics(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, []);

    return (
        <div className="min-h-screen bg-deep-space text-white font-rajdhani flex flex-col">
            <header className="h-16 border-b border-neon-blue/20 bg-deep-space/80 backdrop-blur-md flex justify-between items-center px-8 sticky top-0 z-10">
                <h1 className="text-xl font-orbitron tracking-widest text-white">
                    <span className="text-neon-blue">ORGANIZATION</span> PORTAL
                </h1>
                <div className="flex items-center gap-6">
                    <nav className="flex gap-1 bg-white/5 p-1 rounded-lg">
                        <button onClick={() => setActiveTab('overview')} className={`px-4 py-1 rounded transition-colors ${activeTab === 'overview' ? 'bg-neon-blue text-deep-space font-bold' : 'hover:bg-white/5'}`}>Overview</button>
                        <button onClick={() => setActiveTab('courses')} className={`px-4 py-1 rounded transition-colors ${activeTab === 'courses' ? 'bg-neon-blue text-deep-space font-bold' : 'hover:bg-white/5'}`}>Courses</button>
                        <button onClick={() => setActiveTab('students')} className={`px-4 py-1 rounded transition-colors ${activeTab === 'students' ? 'bg-neon-blue text-deep-space font-bold' : 'hover:bg-white/5'}`}>Students</button>
                        <button onClick={() => setActiveTab('verifications')} className={`px-4 py-1 rounded transition-colors ${activeTab === 'verifications' ? 'bg-neon-blue text-deep-space font-bold' : 'hover:bg-white/5'}`}>Verifications</button>
                        <button onClick={() => setActiveTab('settings')} className={`px-4 py-1 rounded transition-colors ${activeTab === 'settings' ? 'bg-neon-blue text-deep-space font-bold' : 'hover:bg-white/5'}`}>Settings</button>
                    </nav>

                    <div className="flex items-center gap-4">
                        <span className="text-gray-400 font-mono">{user?.username}</span>
                        <button onClick={() => { logout(); navigate('/login'); }}>
                            <LogOut size={20} className="text-gray-400 hover:text-red-500" />
                        </button>
                    </div>
                </div>
            </header>

            <main className="flex-1 p-8 overflow-y-auto">
                {activeTab === 'overview' && <OverviewTab analytics={analytics} loading={loadingAnalytics} />}
                {activeTab === 'courses' && <CoursesTab />}
                {activeTab === 'students' && <StudentsTab analytics={analytics} loading={loadingAnalytics} />}
                {activeTab === 'verifications' && <VerificationsTab />}
                {activeTab === 'settings' && (
                    <div className="max-w-6xl mx-auto">
                        <h2 className="text-2xl font-orbitron text-white mb-6">Platform Settings</h2>
                        <ThemeToggle />
                    </div>
                )}
            </main>
        </div>
    );
};

const OverviewTab = ({ analytics, loading }) => {
    if (loading) return <div className="text-center p-12 text-neon-blue">Loading Analytics...</div>;
    if (!analytics) return <div className="text-center p-12 text-red-500">Failed to load analytics</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in zoom-in duration-300">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card-glass p-6">
                    <div className="text-gray-400 mb-1">Total Students</div>
                    <div className="text-4xl font-orbitron text-neon-blue">{analytics.total_students}</div>
                    <div className="text-sm text-green-400 mt-2">Enrolled across all courses</div>
                </div>
                <div className="card-glass p-6">
                    <div className="text-gray-400 mb-1">Active Courses</div>
                    <div className="text-4xl font-orbitron text-neon-purple">{analytics.active_courses}</div>
                    <div className="text-sm text-green-400 mt-2">Currently published</div>
                </div>
                <div className="card-glass p-6">
                    <div className="text-gray-400 mb-1">Avg. Completion</div>
                    <div className="text-4xl font-orbitron text-white">{analytics.avg_completion.toFixed(1)}%</div>
                    <div className="text-sm text-green-400 mt-2">Overall across all courses</div>
                </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500 text-blue-200 p-4 rounded flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                System Notification: New AI model available for course generation.
            </div>

            <div className="card-glass p-6 mt-8">
                <h3 className="text-xl font-orbitron text-white mb-6">Course Performance</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/10 text-gray-400 text-sm">
                                <th className="pb-3 font-medium">Course Title</th>
                                <th className="pb-3 font-medium text-center">Enrolled Students</th>
                                <th className="pb-3 font-medium text-center">Avg. Progress</th>
                                <th className="pb-3 font-medium text-center">Avg. Score</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {analytics.course_stats.map(cs => (
                                <tr key={cs.course_id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="py-4 text-white font-medium">{cs.topic}</td>
                                    <td className="py-4 text-neon-blue text-center">{cs.enrolled_students}</td>
                                    <td className="py-4 text-neon-green text-center">{cs.avg_progress.toFixed(1)}%</td>
                                    <td className="py-4 text-neon-purple text-center">{cs.avg_score.toFixed(1)}%</td>
                                </tr>
                            ))}
                            {analytics.course_stats.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="py-8 text-center text-gray-500">No course data available yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const CoursesTab = () => {
    const navigate = useNavigate();
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchCourses = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/org/courses');
            setCourses(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchCourses(); }, []);

    const handleDelete = async (id) => {
        if (!confirm("Delete course completely?")) return;
        try {
            await axios.delete(`http://localhost:8000/courses/${id}`);
            fetchCourses();
        } catch (err) {
            alert("Delete failed");
        }
    };

    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newCourseData, setNewCourseData] = useState({
        title: '',
        grade_level: '',
        description: '',
        structure_type: 'week',
        price: 0
    });

    const handlePublish = async (courseId) => {
        try {
            await axios.put(`http://localhost:8000/org/courses/${courseId}/publish`);
            fetchCourses();
        } catch (err) {
            alert('Failed to toggle publish status');
        }
    };

    const handleCreateCourse = async () => {
        if (!newCourseData.title || !newCourseData.grade_level) {
            alert("Title and Grade Level are required");
            return;
        }

        try {
            await axios.post('http://localhost:8000/org/courses/create', newCourseData);
            setShowCreateModal(false);
            setNewCourseData({ title: '', grade_level: '', description: '', structure_type: 'week', price: 0 });
            fetchCourses();
        } catch (err) {
            alert("Failed to create course");
            console.error(err);
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-orbitron">Course Management</h2>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-neon flex items-center gap-2"
                >
                    <Plus size={18} /> Launch New Course
                </button>
            </div>

            {loading ? <div className="text-center p-12">Loading...</div> : (
                <div className="grid gap-4">
                    {courses.map(c => (
                        <div key={c.id} className="card-glass p-4 flex items-center justify-between hover:border-neon-blue/40 transition-colors">
                            <div>
                                <div className="flex items-center gap-2">
                                    <h3 className="text-xl font-bold text-white">{c.topic}</h3>
                                    {c.is_published && (
                                        <span className="text-xs bg-neon-green/20 text-neon-green px-2 py-0.5 rounded-full border border-neon-green/30">Published</span>
                                    )}
                                </div>
                                <div className="flex gap-4 text-sm text-gray-400 mt-1">
                                    <span>{c.grade_level}</span>
                                    <span>•</span>
                                    <span>{c.structure_type} structure</span>
                                    {c.price > 0 && (
                                        <><span>•</span><span>₹{c.price}</span></>
                                    )}
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handlePublish(c.id)}
                                    className={`p-2 hover:bg-white/10 rounded ${c.is_published ? 'text-neon-green' : 'text-gray-500'}`}
                                    title={c.is_published ? 'Unpublish' : 'Publish to Marketplace'}
                                >
                                    {c.is_published ? <Globe size={18} /> : <EyeOff size={18} />}
                                </button>
                                <button
                                    onClick={() => navigate(`/org/course/${c.id}`)}
                                    className="p-2 hover:bg-white/10 rounded text-neon-blue"
                                    title="Edit"
                                >
                                    <Edit size={18} />
                                </button>
                                <button onClick={() => handleDelete(c.id)} className="p-2 hover:bg-white/10 rounded text-red-500" title="Delete">
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                    ))}
                    {courses.length === 0 && <div className="text-center text-gray-500 p-8">No active courses.</div>}
                </div>
            )}

            {/* Create Course Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in">
                    <div className="card-glass w-full max-w-md space-y-4">
                        <h3 className="text-xl font-orbitron text-white mb-4">Launch New Course</h3>

                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Course Title</label>
                            <input
                                type="text"
                                value={newCourseData.title}
                                onChange={e => setNewCourseData({ ...newCourseData, title: e.target.value })}
                                className="input-cyber"
                                placeholder="e.g. Advanced Physics"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Grade Level / Target Audience</label>
                            <input
                                type="text"
                                value={newCourseData.grade_level}
                                onChange={e => setNewCourseData({ ...newCourseData, grade_level: e.target.value })}
                                className="input-cyber"
                                placeholder="e.g. Undergraduate, Grade 10"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Description</label>
                            <textarea
                                value={newCourseData.description}
                                onChange={e => setNewCourseData({ ...newCourseData, description: e.target.value })}
                                className="input-cyber h-24"
                                placeholder="Brief overview of the course content..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Structure Type</label>
                            <select
                                value={newCourseData.structure_type}
                                onChange={e => setNewCourseData({ ...newCourseData, structure_type: e.target.value })}
                                className="input-cyber bg-deep-space"
                            >
                                <option value="week">Weekly Structure</option>
                                <option value="day">Daily Structure</option>
                                <option value="module">Modular Structure</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Price (₹) — 0 for free</label>
                            <input
                                type="number"
                                min="0"
                                value={newCourseData.price}
                                onChange={e => setNewCourseData({ ...newCourseData, price: parseFloat(e.target.value) || 0 })}
                                className="input-cyber"
                                placeholder="0"
                            />
                        </div>

                        <div className="flex gap-4 mt-6">
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="flex-1 py-2 rounded border border-gray-600 text-gray-400 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateCourse}
                                className="flex-1 btn-neon"
                            >
                                Create Course
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const StudentsTab = ({ analytics, loading }) => {
    if (loading) return <div className="text-center p-12 text-neon-blue">Loading Student Data...</div>;
    if (!analytics) return <div className="text-center p-12 text-red-500">Failed to load student data</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in">
            <h2 className="text-2xl font-orbitron text-white mb-6">Student Analytics</h2>
            <div className="card-glass p-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/10 text-gray-400 text-sm">
                                <th className="pb-3 font-medium">Student Name</th>
                                <th className="pb-3 font-medium text-center">Enrolled Courses</th>
                                <th className="pb-3 font-medium text-center">Overall Progress</th>
                                <th className="pb-3 font-medium text-center">Avg. Score</th>
                                <th className="pb-3 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {analytics.student_stats.map(ss => (
                                <tr key={ss.student_id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="py-4 text-white font-medium flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-neon-blue/20 flex items-center justify-center text-neon-blue font-bold">
                                            {ss.student_name.charAt(0).toUpperCase()}
                                        </div>
                                        {ss.student_name}
                                    </td>
                                    <td className="py-4 text-gray-300 text-center">{ss.enrolled_courses}</td>
                                    <td className="py-4">
                                        <div className="flex items-center justify-center gap-2">
                                            <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                                                <div className="h-full bg-neon-green" style={{ width: `${ss.avg_progress}%` }}></div>
                                            </div>
                                            <span className="text-neon-green font-mono text-xs">{ss.avg_progress.toFixed(1)}%</span>
                                        </div>
                                    </td>
                                    <td className="py-4 text-neon-purple text-center tracking-wider">{ss.avg_score.toFixed(1)}%</td>
                                    <td className="py-4">
                                        {ss.avg_progress >= 100 ? (
                                            <span className="bg-neon-green/10 text-neon-green px-2 py-1 rounded text-xs border border-neon-green/20">Graduated</span>
                                        ) : ss.avg_progress > 0 ? (
                                            <span className="bg-neon-blue/10 text-neon-blue px-2 py-1 rounded text-xs border border-neon-blue/20">Active</span>
                                        ) : (
                                            <span className="bg-gray-700/50 text-gray-400 px-2 py-1 rounded text-xs border border-gray-600">Enrolled</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {analytics.student_stats.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="py-8 text-center text-gray-500 font-mono">No students enrolled yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const VerificationsTab = () => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState(null);

    const fetchOrders = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/org/orders', { withCredentials: true });
            setOrders(res.data);
        } catch (err) {
            console.error('Failed to fetch orders', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrders();
    }, []);

    const handleVerification = async (orderId, action) => {
        setProcessingId(orderId);
        try {
            const res = await axios.post(`http://localhost:8000/org/orders/${orderId}/verify`, { action }, { withCredentials: true });
            if (action === 'approve') {
                alert(`Approved! Activation link generated:\n\nhttp://localhost:5173${res.data.activation_link}`);
            } else {
                alert('Order Rejected.');
            }
            fetchOrders();
        } catch (err) {
            alert(err.response?.data?.detail || 'Verification action failed');
        } finally {
            setProcessingId(null);
        }
    };

    if (loading) return <div className="text-center p-12 text-neon-blue">Loading Orders...</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in">
            <h2 className="text-2xl font-orbitron text-white mb-6">Payment Verifications</h2>
            <div className="card-glass p-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/10 text-gray-400 text-sm">
                                <th className="pb-3 font-medium">Order ID</th>
                                <th className="pb-3 font-medium">Student Name</th>
                                <th className="pb-3 font-medium">Course Topic</th>
                                <th className="pb-3 font-medium">Amount</th>
                                <th className="pb-3 font-medium">Status</th>
                                <th className="pb-3 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {orders.map(o => (
                                <tr key={o.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="py-4 font-mono text-gray-400">{o.order_id}</td>
                                    <td className="py-4 text-white">{o.username}</td>
                                    <td className="py-4 text-gray-300">{o.course_topic}</td>
                                    <td className="py-4 font-bold text-neon-green">₹{o.amount}</td>
                                    <td className="py-4">
                                        <span className={`px-2 py-1 rounded text-xs border ${o.status === 'paid' ? 'bg-neon-green/10 text-neon-green border-neon-green/20' :
                                            o.status === 'payment_submitted' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' :
                                                o.status === 'rejected' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                                                    'bg-gray-700/50 text-gray-400 border-gray-600'
                                            }`}>
                                            {o.status.replace('_', ' ').toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="py-4 text-right">
                                        {o.status === 'payment_submitted' && (
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => handleVerification(o.order_id, 'approve')}
                                                    disabled={processingId === o.order_id}
                                                    className="px-3 py-1 bg-neon-green/20 text-neon-green hover:bg-neon-green/30 border border-neon-green/30 rounded flex items-center gap-1 disabled:opacity-50"
                                                >
                                                    {processingId === o.order_id ? '...' : 'Approve'}
                                                </button>
                                                <button
                                                    onClick={() => handleVerification(o.order_id, 'reject')}
                                                    disabled={processingId === o.order_id}
                                                    className="px-3 py-1 bg-red-500/20 text-red-500 hover:bg-red-500/30 border border-red-500/30 rounded flex items-center gap-1 disabled:opacity-50"
                                                >
                                                    {processingId === o.order_id ? '...' : 'Reject'}
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {orders.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500 font-mono">No order records found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default OrgDashboard;
