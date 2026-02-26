import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const role = await login(username, password);
            // Redirect based on role
            if (role === 'student') navigate('/student');
            else if (role === 'parent') navigate('/parent');
            else if (role === 'organization') navigate('/org');
            else navigate('/student'); // Default
        } catch (err) {
            setError('Invalid credentials');
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
                <p className="text-center text-gray-400 mb-8">Access Neural Interface</p>

                {error && (
                    <div className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-neon-blue text-sm mb-2">IDENTITY</label>
                        <input
                            type="text"
                            className="input-cyber"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-neon-blue text-sm mb-2">ACCESS_KEY</label>
                        <input
                            type="password"
                            className="input-cyber"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full btn-neon flex justify-center items-center gap-2"
                        disabled={loading}
                    >
                        {loading ? <Loader2 className="animate-spin" /> : 'INITIALIZE SESSION'}
                    </button>
                </form>

                <p className="text-center mt-6 text-sm text-gray-500">
                    No ID? <a href="/signup" className="text-neon-purple hover:text-white transition-colors">Request Access</a>
                </p>
            </div>
        </div>
    );
};

export default Login;
