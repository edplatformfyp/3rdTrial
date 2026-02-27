import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle, AlertTriangle, Loader2, ArrowRight } from 'lucide-react';

const ActivationPage = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const token = searchParams.get('token');
    const signature = searchParams.get('signature');

    const [status, setStatus] = useState('processing'); // 'processing', 'success', 'error'
    const [message, setMessage] = useState('Validating your secure enrollment token...');

    // Prevent double execution in React Strict Mode
    const hasActivated = useRef(false);

    useEffect(() => {
        if (!token || !signature) {
            setStatus('error');
            setMessage('Invalid activation link. Missing token or signature.');
            return;
        }

        if (hasActivated.current) return;
        hasActivated.current = true;

        const activateToken = async () => {
            try {
                const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/marketplace/activate`, {
                    token_value: token,
                    signature: signature
                }, { withCredentials: true });

                setStatus('success');
                setMessage(res.data.message || 'Token activated successfully! You are now enrolled.');
            } catch (err) {
                setStatus('error');
                setMessage(err.response?.data?.detail || 'Activation failed. The link may be expired, tampered, or already used.');
            }
        };

        activateToken();
    }, [token, signature]);

    return (
        <div className="min-h-screen bg-deep-space text-white font-rajdhani flex items-center justify-center p-4">
            <div className="card-glass max-w-md w-full p-8 text-center space-y-6 animate-in fade-in zoom-in">

                {status === 'processing' && (
                    <>
                        <div className="mx-auto w-20 h-20 flex items-center justify-center">
                            <Loader2 size={48} className="text-neon-blue animate-spin" />
                        </div>
                        <h2 className="text-2xl font-orbitron text-white">Activating Access...</h2>
                        <p className="text-gray-400">{message}</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="mx-auto w-20 h-20 bg-neon-green/20 rounded-full flex items-center justify-center text-neon-green">
                            <CheckCircle size={40} />
                        </div>
                        <h2 className="text-2xl font-orbitron text-white">Enrollment Confirmed</h2>
                        <p className="text-green-400">{message}</p>
                        <button
                            onClick={() => navigate('/student/dashboard')}
                            className="btn-neon w-full flex items-center justify-center gap-2 mt-4"
                        >
                            Open Dashboard <ArrowRight size={18} />
                        </button>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="mx-auto w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center text-red-500">
                            <AlertTriangle size={40} />
                        </div>
                        <h2 className="text-2xl font-orbitron text-white">Activation Failed</h2>
                        <p className="text-red-400">{message}</p>
                        <button
                            onClick={() => navigate('/student/marketplace')}
                            className="w-full py-3 rounded text-sm bg-white/5 hover:bg-white/10 transition-colors mt-4"
                        >
                            Return to Marketplace
                        </button>
                    </>
                )}

            </div>
        </div>
    );
};

export default ActivationPage;
