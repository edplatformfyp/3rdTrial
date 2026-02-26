import { useAuth } from '../context/AuthContext';
import { LogOut, ShieldCheck, Database, Cpu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const AdminDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-deep-space text-white font-rajdhani p-8">
            <header className="flex justify-between items-center mb-12 border-b border-neon-blue/20 pb-4">
                <h1 className="text-3xl font-orbitron"><span className="text-red-500">ADMIN</span> ROOT ACCESS</h1>
                <button onClick={() => { logout(); navigate('/login'); }} className="btn-neon border-red-500 text-red-500 hover:bg-red-500/10">
                    <LogOut size={18} />
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
                <div className="card-glass p-6 border-green-500/50">
                    <div className="flex items-center gap-4 mb-4">
                        <ShieldCheck size={32} className="text-green-500" />
                        <h3 className="text-xl font-bold">System Status</h3>
                    </div>
                    <div className="text-4xl font-orbitron text-green-400">ONLINE</div>
                    <p className="text-gray-400 mt-2">All subsystems operational.</p>
                </div>

                <div className="card-glass p-6 border-blue-500/50">
                    <div className="flex items-center gap-4 mb-4">
                        <Database size={32} className="text-blue-500" />
                        <h3 className="text-xl font-bold">Database</h3>
                    </div>
                    <div className="text-4xl font-orbitron text-blue-400">CONNECTED</div>
                    <p className="text-gray-400 mt-2">MongoDB Cluster Active.</p>
                </div>

                <div className="card-glass p-6 border-purple-500/50">
                    <div className="flex items-center gap-4 mb-4">
                        <Cpu size={32} className="text-purple-500" />
                        <h3 className="text-xl font-bold">AI Agents</h3>
                    </div>
                    <div className="text-4xl font-orbitron text-purple-400">READY</div>
                    <p className="text-gray-400 mt-2">Planner & Content Agents Standing By.</p>
                </div>
            </div>

            <div className="max-w-6xl mx-auto mt-12">
                <ThemeToggle />
            </div>
        </div>
    );
};

export default AdminDashboard;
