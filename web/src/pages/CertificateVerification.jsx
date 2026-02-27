import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Award, CheckCircle, ShieldCheck, User, BookOpen, BarChart3, Loader2, XCircle } from 'lucide-react';

const CertificateVerification = () => {
    const { certId } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchVerification = async () => {
            setLoading(true);
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/certificates/verify/${certId}`);
                setData(res.data);
            } catch (err) {
                setError(err.response?.data?.detail || "Invalid or unrecognized Certificate ID");
            } finally {
                setLoading(false);
            }
        };

        if (certId) {
            fetchVerification();
        }
    }, [certId]);

    if (loading) {
        return (
            <div className="min-h-screen bg-deep-space text-white flex flex-col items-center justify-center p-6 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-neon-purple/20 via-deep-space to-deep-space">
                <Loader2 size={48} className="animate-spin text-neon-blue mb-4" />
                <h2 className="text-xl font-orbitron tracking-widest text-neon-blue animate-pulse">VERIFYING RECORD...</h2>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-deep-space text-white flex flex-col items-center justify-center p-6 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-red-900/20 via-deep-space to-deep-space">
                <div className="w-full max-w-lg card-glass p-8 border border-red-500/30 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-red-500" />
                    <XCircle size={64} className="text-red-500 mx-auto mb-6" />
                    <h1 className="text-3xl font-orbitron text-white mb-2 font-bold tracking-wider">VERIFICATION FAILED</h1>
                    <p className="text-red-400 font-mono tracking-widest bg-red-500/10 inline-block px-4 py-2 rounded mb-6">ID: {certId}</p>
                    <p className="text-gray-400 mb-8 max-w-sm mx-auto">{error}</p>

                    <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white font-medium transition-all">
                        Return Home
                    </Link>
                </div>
            </div>
        );
    }

    const { certificate, course, performance, exam } = data;

    return (
        <div className="min-h-screen bg-deep-space text-white p-4 md:p-8 lg:p-12 relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-neon-blue/10 via-deep-space to-deep-space">

            {/* Background Accents */}
            <div className="absolute top-[20%] right-[10%] w-[500px] h-[500px] bg-neon-purple/5 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-[20%] left-[10%] w-[600px] h-[600px] bg-neon-blue/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="max-w-4xl mx-auto relative z-10 w-full">

                {/* Header Section */}
                <header className="mb-10 text-center">
                    <div className="inline-flex items-center justify-center gap-3 bg-neon-blue/10 border border-neon-blue/30 text-neon-blue px-6 py-2 rounded-full mb-6 max-w-full">
                        <ShieldCheck size={20} className="shrink-0" />
                        <span className="font-orbitron font-bold tracking-widest text-sm sm:text-base truncate">OFFICIAL RECORD VERIFIED</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-orbitron font-black text-transparent bg-clip-text bg-gradient-to-r from-neon-blue via-white to-neon-purple leading-tight pb-2">
                        Certificate Verification
                    </h1>
                </header>

                {/* Main Card */}
                <div className="card-glass border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden">

                    {/* Top Accent Bar */}
                    <div className="h-1.5 w-full bg-gradient-to-r from-neon-blue via-neon-purple to-pink-500" />

                    <div className="p-6 md:p-10">
                        {/* Certificate Core Information */}
                        <div className="flex flex-col md:flex-row gap-8 items-start mb-12">
                            <div className="flex-1 space-y-6 w-full">
                                <div>
                                    <h2 className="text-sm font-mono text-gray-400 mb-1 uppercase tracking-widest">Recipient</h2>
                                    <div className="text-3xl font-bold flex items-center gap-3 border-l-4 border-neon-blue pl-4 py-1">
                                        {certificate.student_name}
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full">
                                    <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                        <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Issue Date</div>
                                        <div className="text-lg font-medium">{new Date(certificate.issued_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-xl border border-white/5 flex flex-col items-start min-w-[200px]">
                                        <div className="text-xs text-gray-500 uppercase tracking-widest mb-1 shrink-0">Certificate ID</div>
                                        <div className="text-sm font-mono text-neon-blue truncate max-w-full" title={certificate.id}>{certificate.id}</div>
                                    </div>
                                </div>
                            </div>

                            <div className="hidden md:flex flex-col items-center justify-center p-6 bg-gradient-to-br from-yellow-500/10 to-amber-600/10 border border-yellow-500/20 rounded-2xl min-w-[160px]">
                                <Award size={64} className="text-yellow-500 mb-3 drop-shadow-[0_0_15px_rgba(234,179,8,0.3)]" />
                                <div className="text-xs font-orbitron tracking-widest text-yellow-600 font-bold">VALIDATED</div>
                            </div>
                        </div>

                        {/* Divider */}
                        <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent mb-12" />

                        {/* Details Grid */}
                        <div className="grid md:grid-cols-2 gap-8 md:gap-12">

                            {/* Course Context */}
                            <section>
                                <div className="flex items-center gap-2 mb-6">
                                    <BookOpen className="text-neon-purple" size={24} />
                                    <h3 className="text-xl font-orbitron font-bold text-white tracking-wide">Course Details</h3>
                                </div>

                                <div className="space-y-5">
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Course Title</div>
                                        <div className="text-xl font-semibold text-gray-200 leading-snug">{course.title}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Description</div>
                                        <div className="text-sm text-gray-400 line-clamp-3">{course.description}</div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Provider</div>
                                            <div className="text-sm font-medium">{course.org_name}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Format</div>
                                            <div className="text-sm font-medium">{course.module_count} Modules</div>
                                        </div>
                                    </div>
                                </div>
                            </section>

                            {/* Performance Matrix */}
                            <section>
                                <div className="flex items-center gap-2 mb-6">
                                    <BarChart3 className="text-neon-blue" size={24} />
                                    <h3 className="text-xl font-orbitron font-bold text-white tracking-wide">Performance Matrix</h3>
                                </div>

                                <div className="space-y-4">
                                    {/* Final Exam Highlight */}
                                    {exam ? (
                                        <div className="bg-gradient-to-br from-neon-blue/10 to-transparent border border-neon-blue/30 p-5 rounded-xl relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                                <Award size={64} />
                                            </div>
                                            <div className="text-xs text-neon-blue uppercase tracking-widest mb-2 font-bold flex items-center gap-2">
                                                <CheckCircle size={14} /> Final Exam Mastery
                                            </div>
                                            <div className="flex items-end gap-2">
                                                <div className="text-4xl font-black text-white">{exam.percentage}%</div>
                                                <div className="text-sm text-gray-400 mb-1">({exam.score}/{exam.total_points} pts)</div>
                                            </div>

                                            {/* Integrity Score */}
                                            {exam.credibility_score !== undefined && (
                                                <div className="mt-4 pt-4 border-t border-white/10 flex justify-between items-center">
                                                    <span className="text-xs text-gray-400">Proctoring Integrity Score:</span>
                                                    <span className={`text-sm font-mono font-bold px-2 py-0.5 rounded ${exam.credibility_score >= 90 ? 'bg-green-500/20 text-green-400' : exam.credibility_score >= 70 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {exam.credibility_score}/100
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="bg-white/5 border border-white/10 p-5 rounded-xl text-center">
                                            <div className="text-gray-400 text-sm">No Final Exam Required</div>
                                        </div>
                                    )}

                                    {/* Quiz Averages */}
                                    <div className="flex items-center justify-between bg-white/5 border border-white/10 p-4 rounded-xl">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-neon-purple/20 flex items-center justify-center text-neon-purple">
                                                <BookOpen size={18} />
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-white">Module Quizzes</div>
                                                <div className="text-xs text-gray-400">{performance.quizzes_completed} completed</div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xl font-bold text-white">{performance.avg_quiz_score}%</div>
                                            <div className="text-[10px] text-gray-500 uppercase tracking-widest">Average</div>
                                        </div>
                                    </div>
                                </div>
                            </section>

                        </div>
                    </div>

                    {/* Security Footer */}
                    <div className="bg-black/50 p-4 flex flex-col md:flex-row items-center justify-between gap-4 border-t border-white/5 text-xs text-gray-500 font-mono">
                        <div className="flex items-center gap-2 max-w-full">
                            <ShieldCheck size={14} className="text-green-500 shrink-0" />
                            <span className="truncate">This record is cryptographically tied to the EduCore database.</span>
                        </div>
                        <div className="shrink-0">
                            Requested: {new Date().toLocaleDateString()}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default CertificateVerification;
