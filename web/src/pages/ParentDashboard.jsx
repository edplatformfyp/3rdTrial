import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Link, ClipboardList, Activity, CheckCircle, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ThemeToggle from '../components/ThemeToggle';

const ParentDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [children, setChildren] = useState([]);
    const [selectedChildId, setSelectedChildId] = useState(null);
    const [childData, setChildData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Fetch linked children
    useEffect(() => {
        const fetchChildren = async () => {
            try {
                const res = await axios.get('http://localhost:8000/parent/children');
                setChildren(res.data);
                if (res.data.length > 0) {
                    setSelectedChildId(res.data[0].id);
                }
            } catch (err) {
                console.error("Failed to load children", err);
            }
        };
        fetchChildren();
    }, []);

    // Fetch child progress when selected
    useEffect(() => {
        if (!selectedChildId) return;
        const fetchProgress = async () => {
            setLoading(true);
            try {
                const res = await axios.get(`http://localhost:8000/parent/child/${selectedChildId}/progress`);
                setChildData(res.data);
            } catch (err) {
                console.error("Failed to load progress", err);
            } finally {
                setLoading(false);
            }
        };
        fetchProgress();
    }, [selectedChildId]);

    const handleLinkChild = async () => {
        const secretId = prompt("Enter Child's Secret ID (e.g. username-1234):");
        if (!secretId) return;

        try {
            await axios.post(`http://localhost:8000/parent/link-request?secret_id=${secretId}`);
            alert("Link request sent! Ask your child to approve it.");
        } catch (err) {
            alert("Failed to send link request: " + (err.response?.data?.detail || err.message));
        }
    };

    return (
        <div className="min-h-screen bg-deep-space text-white font-rajdhani">
            <header className="h-16 border-b border-neon-purple/20 bg-deep-space/80 backdrop-blur-md flex justify-between items-center px-8 sticky top-0 z-10">
                <h1 className="text-xl font-orbitron tracking-widest text-white">
                    <span className="text-neon-purple">PARENT</span> OVERWATCH
                </h1>
                <div className="flex items-center gap-4">
                    <span className="text-neon-blue font-mono">{user?.username}</span>
                    <button onClick={() => { logout(); navigate('/login'); }}>
                        <LogOut size={20} className="text-gray-400 hover:text-red-500" />
                    </button>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <aside className="w-64 h-[calc(100vh-4rem)] border-r border-neon-purple/20 p-6">
                    <div className="mb-8">
                        <button
                            onClick={handleLinkChild}
                            className="w-full btn-neon flex items-center justify-center gap-2 border-neon-purple text-neon-purple hover:bg-neon-purple/10"
                        >
                            <Link size={16} /> Link New Child
                        </button>
                    </div>

                    <h3 className="text-gray-500 uppercase text-xs tracking-wider mb-4">My Children</h3>
                    <div className="space-y-2">
                        {children.map(child => (
                            <button
                                key={child.id}
                                onClick={() => setSelectedChildId(child.id)}
                                className={`w-full text-left p-3 rounded flex items-center gap-3 transition-colors ${selectedChildId === child.id
                                    ? 'bg-neon-purple/20 border border-neon-purple text-white'
                                    : 'text-gray-400 hover:bg-white/5'
                                    }`}
                            >
                                <User size={16} />
                                {child.username}
                            </button>
                        ))}
                    </div>

                    <div className="mt-8 pt-6 border-t border-neon-purple/20">
                        <h3 className="text-gray-500 uppercase text-xs tracking-wider mb-4">Account</h3>
                        <button
                            onClick={() => setSelectedChildId('settings')}
                            className={`w-full text-left p-3 rounded flex items-center gap-3 transition-colors ${selectedChildId === 'settings'
                                ? 'bg-neon-purple/20 border border-neon-purple text-white'
                                : 'text-gray-400 hover:bg-white/5'
                                }`}
                        >
                            <Settings size={16} />
                            Settings
                        </button>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 p-8 overflow-y-auto h-[calc(100vh-4rem)]">
                    {loading ? (
                        <div className="flex justify-center mt-20 text-neon-purple animate-pulse">Scanning Neural Patterns...</div>
                    ) : selectedChildId === 'settings' ? (
                        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <ThemeToggle />
                        </div>
                    ) : childData ? (
                        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {/* Metrics */}
                            <div className="grid grid-cols-3 gap-6">
                                <MetricCard
                                    label="Active Courses"
                                    value={childData.courses.length}
                                    icon={<ClipboardList className="text-neon-blue" size={32} />}
                                />
                                <MetricCard
                                    label="Avg Quiz Score"
                                    value={`${childData.average_score}%`}
                                    icon={<Activity className="text-green-400" size={32} />}
                                />
                                <MetricCard
                                    label="Quizzes Taken"
                                    value={childData.recent_quizzes.length}
                                    icon={<CheckCircle className="text-neon-purple" size={32} />}
                                />
                            </div>

                            {/* Recent Activity */}
                            <div className="card-glass p-8">
                                <h3 className="text-xl font-orbitron mb-6 flex items-center gap-2">
                                    <Activity className="text-neon-blue" />
                                    Recent Performance
                                </h3>

                                {childData.recent_quizzes.length === 0 ? (
                                    <p className="text-gray-500">No quizzes taken yet.</p>
                                ) : (
                                    <div className="space-y-4">
                                        {childData.recent_quizzes.map((q, i) => (
                                            <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded border border-white/5">
                                                <div>
                                                    <div className="text-white font-semibold">Quiz Result</div>
                                                    <div className="text-xs text-gray-500">{new Date(q.timestamp).toLocaleString()}</div>
                                                </div>
                                                <div className={`text-xl font-bold ${q.score / q.total > 0.7 ? 'text-green-400' : 'text-yellow-400'}`}>
                                                    {q.score}/{q.total}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Active Courses List */}
                            <div className="card-glass p-8">
                                <h3 className="text-xl font-orbitron mb-6 flex items-center gap-2">
                                    <ClipboardList className="text-neon-purple" />
                                    Active Modules
                                </h3>
                                <div className="grid grid-cols-2 gap-4">
                                    {childData.courses.map((c, i) => (
                                        <div key={i} className="p-4 bg-deep-space border border-neon-purple/30 rounded">
                                            <div className="font-bold text-lg">{c.topic}</div>
                                            <div className="text-sm text-gray-400">{c.grade_level}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Messaging Section */}
                            <MessageSection childId={selectedChildId} />

                        </div>
                    ) : (
                        <div className="text-center mt-20 text-gray-500">
                            Select a child to view their progress, or link a new account.
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

const MetricCard = ({ label, value, icon }) => (
    <div className="card-glass p-6 flex items-center justify-between">
        <div>
            <div className="text-gray-400 text-sm">{label}</div>
            <div className="text-3xl font-orbitron mt-1">{value}</div>
        </div>
        <div className="bg-white/5 p-3 rounded-full">{icon}</div>
    </div>
);

const MessageSection = ({ childId }) => {
    const [message, setMessage] = useState('');
    const [sending, setSending] = useState(false);

    const handleSendMessage = async () => {
        if (!message.trim()) return;
        setSending(true);
        try {
            const token = localStorage.getItem('token');
            await axios.post(`http://localhost:8000/parent/message?receiver_id=${childId}&content=${encodeURIComponent(message)}`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert("Message sent!");
            setMessage('');
        } catch (err) {
            alert("Failed to send message");
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="card-glass p-8">
            <h3 className="text-xl font-orbitron mb-6 flex items-center gap-2">
                <div className="text-neon-blue">Send Transmission</div>
            </h3>
            <div className="flex gap-4">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type a message to your child..."
                    className="flex-1 input-cyber rounded bg-deep-space/50 border-neon-blue/30 focus:border-neon-blue"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button
                    onClick={handleSendMessage}
                    disabled={sending}
                    className="btn-neon border-neon-blue text-neon-blue hover:bg-neon-blue/10 px-6"
                >
                    {sending ? 'Sending...' : 'SEND'}
                </button>
            </div>
        </div>
    );
};

// End of file
export default ParentDashboard;
