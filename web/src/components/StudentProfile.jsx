import { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Shield, MessageSquare, Check, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const StudentProfile = () => {
    const { user } = useAuth();
    const [requests, setRequests] = useState([]);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            const [reqRes, msgRes] = await Promise.all([
                axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/student/requests`, { headers }),
                axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/student/messages`, { headers })
            ]);

            setRequests(reqRes.data);
            setMessages(msgRes.data);
        } catch (err) {
            console.error("Failed to load profile data", err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (parentId) => {
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/student/approve-request?parent_id=${parentId}`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert("Parent linked successfully!");
            setRequests(requests.filter(r => r.id !== parentId));
        } catch (err) {
            alert("Failed to approve request");
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Identity Card */}
            <div className="card-glass p-8 flex items-center gap-6">
                <div className="bg-neon-blue/20 p-4 rounded-full border border-neon-blue">
                    <User size={48} className="text-neon-blue" />
                </div>
                <div>
                    <h2 className="text-2xl font-orbitron text-white">{user?.username}</h2>
                    <p className="text-gray-400">{user?.email}</p>
                    <div className="mt-4 flex items-center gap-2 bg-deep-space/50 px-4 py-2 rounded border border-neon-purple/30">
                        <Shield size={16} className="text-neon-purple" />
                        <span className="text-gray-400 text-sm">SECRET ID:</span>
                        <span className="font-mono text-neon-purple tracking-wider select-all">{user?.secret_id || 'Generating...'}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Share this ID with your parent to link accounts.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Link Requests */}
                <div className="card-glass p-6">
                    <h3 className="text-xl font-orbitron mb-4 flex items-center gap-2">
                        <Clock className="text-yellow-400" /> Pending Requests
                    </h3>
                    {requests.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">No pending link requests.</p>
                    ) : (
                        <div className="space-y-4">
                            {requests.map(req => (
                                <div key={req.id} className="flex items-center justify-between p-3 bg-white/5 rounded border border-white/10">
                                    <div>
                                        <div className="font-semibold text-white">{req.username}</div>
                                        <div className="text-xs text-gray-400">{req.email}</div>
                                    </div>
                                    <button
                                        onClick={() => handleApprove(req.id)}
                                        className="btn-neon px-3 py-1 text-xs border-green-400 text-green-400 hover:bg-green-400/10 flex items-center gap-1"
                                    >
                                        <Check size={12} /> Approve
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Messages */}
                <div className="card-glass p-6">
                    <h3 className="text-xl font-orbitron mb-4 flex items-center gap-2">
                        <MessageSquare className="text-neon-blue" /> Comms Log
                    </h3>
                    {messages.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">No incoming transmissions.</p>
                    ) : (
                        <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
                            {messages.map(msg => (
                                <div key={msg.id} className="p-3 bg-deep-space/50 rounded border-l-2 border-neon-blue">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-neon-blue font-bold text-sm">{msg.sender}</span>
                                        <span className="text-[10px] text-gray-500">{new Date(msg.timestamp).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-gray-300 text-sm leading-relaxed">{msg.content}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default StudentProfile;
