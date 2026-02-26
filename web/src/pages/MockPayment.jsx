import { useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CreditCard, ShieldCheck, Loader2, ArrowLeft, Clock } from 'lucide-react';

const MockPayment = () => {
    const { sessionId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(null);

    // We expect course topic and amount to be passed via React Router state
    const orderData = location.state || { topic: 'Course Enrollment', amount: 0 };

    const handlePayment = async () => {
        setLoading(true);
        setError(null);
        try {
            await axios.post(`http://localhost:8000/marketplace/orders/${sessionId}/pay`, {}, { withCredentials: true });
            setSuccess(true);
        } catch (err) {
            setError(err.response?.data?.detail || 'Payment simulation failed.');
            setSuccess(false);
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-deep-space text-white font-rajdhani flex items-center justify-center p-4">
                <div className="card-glass max-w-md w-full p-8 text-center space-y-6 animate-in fade-in zoom-in">
                    <div className="mx-auto w-20 h-20 bg-neon-purple/20 rounded-full flex items-center justify-center text-neon-purple">
                        <Clock size={40} />
                    </div>
                    <h2 className="text-2xl font-orbitron text-white">Payment Submitted</h2>
                    <p className="text-gray-400">
                        Your payment reference has been recorded. This transaction is currently
                        <strong className="text-neon-purple"> Awaiting Organization Verification</strong>.
                    </p>
                    <p className="text-sm text-gray-500 bg-black/30 p-4 rounded-lg">
                        Once the organization confirms receipt of funds, you will receive an active Enrollment Token link to instantly unlock your course.
                    </p>
                    <button
                        onClick={() => navigate('/student/dashboard')}
                        className="btn-neon w-full flex items-center justify-center gap-2 mt-4"
                    >
                        <ArrowLeft size={18} /> Return to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-deep-space text-white font-rajdhani flex flex-col items-center justify-center p-4">
            <div className="mb-8 text-center animate-in slide-in-from-top-4">
                <h1 className="text-3xl font-orbitron text-neon-blue flex items-center justify-center gap-3">
                    <ShieldCheck size={32} /> Secure Checkout (Mock)
                </h1>
                <p className="text-gray-400 mt-2 tracking-widest uppercase text-sm">Testing Environment</p>
            </div>

            <div className="card-glass max-w-md w-full p-8 space-y-8 animate-in fade-in zoom-in">
                <div className="space-y-4">
                    <div className="flex justify-between items-center pb-4 border-b border-white/10">
                        <span className="text-gray-400">Order Topic</span>
                        <span className="font-bold text-white text-right max-w-[200px] truncate">{orderData.topic}</span>
                    </div>
                    <div className="flex justify-between items-center pb-4 border-b border-white/10">
                        <span className="text-gray-400">Session ID</span>
                        <span className="font-mono text-xs text-gray-500 truncate max-w-[200px]">{sessionId}</span>
                    </div>
                    <div className="flex justify-between items-center text-lg">
                        <span className="text-neon-blue font-orbitron">Total Amount</span>
                        <span className="font-bold text-2xl text-neon-green">₹{orderData.amount}</span>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg text-sm text-center">
                        {error}
                    </div>
                )}

                <div className="space-y-4 pt-4">
                    <p className="text-xs text-gray-500 text-center">
                        This is a simulated payment gateway. No real charges will be made. Clicking the button below simulates a successful third-party transaction.
                    </p>
                    <button
                        onClick={handlePayment}
                        disabled={loading}
                        className="w-full py-4 rounded-lg text-lg font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 bg-gradient-to-r from-neon-blue to-neon-purple text-white shadow-[0_0_20px_rgba(0,243,255,0.3)] hover:shadow-[0_0_30px_rgba(188,19,254,0.5)]"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : <CreditCard />}
                        Simulate Payment of ₹{orderData.amount}
                    </button>

                    <button
                        onClick={() => navigate(-1)}
                        className="w-full py-3 rounded-lg text-sm text-gray-400 hover:text-white transition-colors"
                    >
                        Cancel and Return
                    </button>
                </div>
            </div>
        </div>
    );
};

export default MockPayment;
