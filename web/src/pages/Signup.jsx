import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const Signup = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('student');
    const [orgCode, setOrgCode] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const payload = {
                username,
                email,
                password,
                role,
                organization_code: orgCode || null
            };
            await register(payload);
            setSuccess('Registration successful! Redirecting to login...');
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
            {/* Background Rings */}
            <div className="absolute w-[500px] h-[500px] rounded-full border border-neon-blue/20 animate-spin-slow"></div>
            <div className="absolute w-[700px] h-[700px] rounded-full border border-neon-purple/20 animate-reverse-spin"></div>

            <div className="card-glass w-full max-w-md z-10 p-8">
                <h1 className="text-4xl text-center mb-2 bg-gradient-to-r from-white to-neon-blue bg-clip-text text-transparent">EduCore</h1>
                <p className="text-center text-gray-400 mb-8">Create Neural Identity</p>

                {error && (
                    <div className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded mb-4">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="bg-green-500/20 border border-green-500 text-green-200 p-3 rounded mb-4">
                        {success}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-neon-blue text-sm mb-2">USERNAME</label>
                        <input
                            type="text"
                            required
                            className="input-cyber"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-neon-blue text-sm mb-2">EMAIL</label>
                        <input
                            type="email"
                            required
                            className="input-cyber"
                            placeholder="Email Address"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-neon-blue text-sm mb-2">PASSWORD</label>
                        <input
                            type="password"
                            required
                            className="input-cyber"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-neon-blue text-sm mb-2">ROLE</label>
                        <select
                            className="input-cyber bg-deep-space w-full"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                        >
                            <option value="student">Student</option>
                            <option value="parent">Parent</option>
                            <option value="organization">Organization</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>

                    {role === 'student' && (
                        <div>
                            <label className="block text-neon-blue text-sm mb-2">ORG CODE (OPTIONAL)</label>
                            <input
                                type="text"
                                className="input-cyber"
                                placeholder="Organization Code"
                                value={orgCode}
                                onChange={(e) => setOrgCode(e.target.value)}
                            />
                        </div>
                    )}

                    <button
                        type="submit"
                        className="w-full btn-neon flex justify-center items-center gap-2"
                        disabled={loading}
                    >
                        {loading ? <Loader2 className="animate-spin" /> : 'REGISTER IDENTITY'}
                    </button>
                </form>

                <p className="text-center mt-6 text-sm text-gray-500">
                    Already have an ID? <Link to="/login" className="text-neon-purple hover:text-white transition-colors">Login</Link>
                </p>
            </div>
        </div>
    );
};

export default Signup;
