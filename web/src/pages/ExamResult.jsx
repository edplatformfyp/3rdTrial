
import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle, XCircle, AlertTriangle, ShieldCheck, ShieldAlert, ChevronLeft, Award } from 'lucide-react';

const ExamResult = () => {
    const { state } = useLocation();
    const { courseId } = useParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(state?.result || null);
    const [loading, setLoading] = useState(!state?.result);

    useEffect(() => {
        if (!result) {
            // Fetch last result if not passed in state
            const fetchResult = async () => {
                try {
                    const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/courses/${courseId}/exam/result`);
                    setResult(res.data);
                } catch (err) {
                    // Redirect if no result
                    navigate('/student');
                } finally {
                    setLoading(false);
                }
            };
            fetchResult();
        }
    }, [courseId, navigate, result]);

    if (loading) return <div className="min-h-screen bg-black text-white flex items-center justify-center">Loading result...</div>;
    if (!result) return null;

    return (
        <div className="min-h-screen bg-black text-white p-8 font-sans">
            <div className="max-w-4xl mx-auto space-y-8">
                <button onClick={() => navigate('/student')} className="flex items-center gap-2 text-gray-400 hover:text-white mb-4">
                    <ChevronLeft size={20} /> Back to Course
                </button>

                {/* Score Card */}
                <div className={`p-8 rounded-2xl border ${result.passed ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'} flex items-center justify-between`}>
                    <div>
                        <h1 className="text-4xl font-orbitron mb-2">{result.passed ? 'Exam Passed' : 'Exam Failed'}</h1>
                        <p className="text-gray-300">You have {result.passed ? 'successfully completed' : 'not passed'} the final examination.</p>
                    </div>
                    <div className="text-center">
                        <div className={`text-6xl font-bold font-mono mb-2 ${result.passed ? 'text-green-400' : 'text-red-400'}`}>
                            {result.percentage.toFixed(0)}%
                        </div>
                        <div className="text-sm text-gray-400">Score: {result.score} / {result.total_points}</div>
                    </div>
                </div>

                {/* Credibility Score */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="col-span-2 bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 className="text-xl font-orbitron mb-4 flex items-center gap-2">
                            <ShieldCheck className="text-neon-blue" /> Credibility Analysis
                        </h3>
                        <div className="flex items-center gap-6">
                            <div className="relative w-32 h-32 flex items-center justify-center">
                                <svg className="w-full h-full rotate-[-90deg]">
                                    <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-gray-800" />
                                    <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="8" fill="transparent"
                                        strokeDasharray={351}
                                        strokeDashoffset={351 - (351 * result.credibility_score) / 100}
                                        className={`${result.credibility_score > 80 ? 'text-green-500' : result.credibility_score > 50 ? 'text-yellow-500' : 'text-red-500'} transition-all duration-1000`}
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-3xl font-bold">{result.credibility_score}</span>
                                    <span className="text-[10px] uppercase text-gray-500">Trust Score</span>
                                </div>
                            </div>
                            <div className="flex-1 space-y-3">
                                <div className="flex justify-between text-sm border-b border-white/10 pb-2">
                                    <span className="text-gray-400">Malpractice Events Detected</span>
                                    <span className="font-mono text-red-400">{result.malpractice_count}</span>
                                </div>
                                <div className="flex justify-between text-sm border-b border-white/10 pb-2">
                                    <span className="text-gray-400">Window Focus Lost</span>
                                    <span className="font-mono">{result.malpractice_count > 0 ? 'Yes' : 'No'}</span>
                                </div>
                                <div className="text-xs text-gray-500 mt-2">
                                    Based on AI proctoring logs (gaze tracking, audio levels, tab switching).
                                    {result.malpractice_count > 3 ? " High risk detected. Review required." : " Standard exam behavior."}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white/5 border border-white/10 rounded-xl p-6 flex flex-col justify-center">
                        <div className="text-center space-y-2">
                            <div className="text-gray-400 text-sm">Attempt Number</div>
                            <div className="text-4xl font-bold text-white">{result.attempts}</div>
                            {result.passed && (
                                <div className="mt-4 pt-4 border-t border-white/10">
                                    <Award className="mx-auto text-yellow-500 mb-2" size={32} />
                                    <div className="text-xs text-yellow-500">You are now eligible for certification!</div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Detailed Analysis */}
                <div className="space-y-4">
                    <h3 className="text-xl font-orbitron mb-2">Question Analysis</h3>
                    {result.analysis.map((item, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border ${item.correct ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
                            <div className="flex items-start gap-3">
                                {item.correct ? <CheckCircle className="text-green-500 shrink-0 mt-1" size={20} /> : <XCircle className="text-red-500 shrink-0 mt-1" size={20} />}
                                <div className="flex-1">
                                    <div className="text-sm text-gray-400 mb-1">Question {idx + 1}</div>
                                    <div className="font-medium text-lg mb-2">{item.question}</div>
                                    <div className="flex flex-col gap-1 text-sm">
                                        <div className="flex gap-2">
                                            <span className="text-gray-500">Your Answer:</span>
                                            <span className={item.correct ? 'text-green-400' : 'text-red-400'}>
                                                {formatAnswer(item.user_answer) || 'No Answer'}
                                            </span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1 uppercase font-bold tracking-wider">{item.feedback}</div>
                                    </div>
                                </div>
                                {!item.correct && (
                                    <div className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded">0 pts</div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const formatAnswer = (ans) => {
    if (ans === undefined || ans === null) return '';
    if (Array.isArray(ans)) return ans.map(i => `Option ${i + 1}`).join(', '); // Indices to "Option X"
    if (typeof ans === 'number') return `Option ${ans + 1}`; // Index to "Option X"
    return ans.toString();
};

export default ExamResult;
