
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import * as tf from '@tensorflow/tfjs';
import * as blazeface from '@tensorflow-models/blazeface';
import axios from 'axios';
import { AlertTriangle, Clock, Eye, EyeOff, Shield, ShieldAlert, CheckCircle, Loader2 } from 'lucide-react';

const ExamView = () => {
    const { courseId } = useParams();
    const navigate = useNavigate();

    // State
    const [loading, setLoading] = useState(true);
    const [examData, setExamData] = useState(null);
    const [started, setStarted] = useState(false);
    const [timeLeft, setTimeLeft] = useState(0);
    const [answers, setAnswers] = useState({});
    const [currentQ, setCurrentQ] = useState(0);
    const [submitting, setSubmitting] = useState(false);

    // Proctoring State
    const [warnings, setWarnings] = useState(0);
    const [proctorLogs, setProctorLogs] = useState([]);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const webcamRef = useRef(null);
    const modelRef = useRef(null);
    const [modelLoaded, setModelLoaded] = useState(false);
    const [cameraPermission, setCameraPermission] = useState(null); // null, granted, denied

    // --- Actions ---

    const handleSubmit = async (force = false) => {
        if (submitting) return;
        setSubmitting(true);
        if (document.fullscreenElement) document.exitFullscreen().catch(() => { });

        const payload = {
            items: answers,
            proctor_logs: proctorLogs,
            malpractice_count: warnings,
            time_taken_seconds: (examData?.time_limit_minutes * 60) - timeLeft
        };

        try {
            const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/courses/${courseId}/exam/submit`, payload, {
                withCredentials: true
            });
            navigate(`/course/${courseId}/exam/result`, { state: { result: res.data } });
        } catch (err) {
            alert("Submission failed. Please try again or contact support.");
            setSubmitting(false);
        }
    };

    const addWarning = (reason) => {
        if (warnings >= 5) return;
        const msg = `Warning ${warnings + 1}/5: ${reason}`;

        // Use functional update to check fresh state if needed, but here we trigger side effects
        setWarnings(prev => {
            const newCount = prev + 1;
            if (newCount >= 6 && !submitting) {
                // Defer alert to avoid state update conflict
                setTimeout(() => {
                    alert("Too many violations. Auto-submitting exam.");
                    handleSubmit(true);
                }, 100);
            }
            return newCount;
        });
        setProctorLogs(prev => [...prev, msg]);
    };

    const startExam = async () => {
        if (!modelLoaded) {
            alert("Please wait for AI Proctoring to initialize.");
            return;
        }
        try {
            await document.documentElement.requestFullscreen();
            setStarted(true);
        } catch (err) {
            alert("Fullscreen is required to start the exam.");
        }
    };

    // --- Effects ---

    // Load Exam Data
    useEffect(() => {
        const fetchExam = async () => {
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/courses/${courseId}/exam`, {
                    withCredentials: true
                });
                setExamData(res.data);
                setTimeLeft(res.data.time_limit_minutes * 60);
            } catch (err) {
                alert(err.response?.data?.detail || 'Failed to load exam');
                navigate(`/course/${courseId}`);
            } finally {
                setLoading(false);
            }
        };
        fetchExam();
    }, [courseId, navigate]);

    // Load AI Model
    useEffect(() => {
        const loadModel = async () => {
            await tf.ready();
            const model = await blazeface.load();
            modelRef.current = model;
            setModelLoaded(true);
        };
        loadModel();
    }, []);

    // Fullscreen Listener
    useEffect(() => {
        const handleFullscreen = () => {
            const isFull = !!document.fullscreenElement;
            setIsFullscreen(isFull);
            if (started && !isFull) {
                addWarning("Exited fullscreen mode");
            }
        };
        document.addEventListener('fullscreenchange', handleFullscreen);
        return () => document.removeEventListener('fullscreenchange', handleFullscreen);
    }, [started]); // AddWarning is stable enough or we ignore dep warning

    // Visibility Listener (Tab Switch)
    useEffect(() => {
        const handleVisibility = () => {
            if (document.hidden && started) {
                addWarning("Switched tabs or minimized window");
            }
        };
        document.addEventListener('visibilitychange', handleVisibility);
        return () => document.removeEventListener('visibilitychange', handleVisibility);
    }, [started]);

    // Audio Monitoring
    useEffect(() => {
        let audioContext;
        let analyser;
        let microphone;
        let javascriptNode;

        const setupAudio = async () => {
            if (!started) return;
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

                analyser.smoothingTimeConstant = 0.8;
                analyser.fftSize = 1024;

                microphone.connect(analyser);
                analyser.connect(javascriptNode);
                javascriptNode.connect(audioContext.destination);

                javascriptNode.onaudioprocess = () => {
                    const array = new Uint8Array(analyser.frequencyBinCount);
                    analyser.getByteFrequencyData(array);
                    let values = 0;
                    const length = array.length;
                    for (let i = 0; i < length; i++) {
                        values += array[i];
                    }
                    const average = values / length;

                    if (average > 40) { // Threshold
                        addWarning("High background noise detected!");
                    }
                };
            } catch (err) {
                console.error("Audio setup failed", err);
            }
        };

        if (started) setupAudio();

        return () => {
            if (audioContext && audioContext.state !== 'closed') audioContext.close();
            if (microphone) microphone.disconnect();
            if (javascriptNode) javascriptNode.disconnect();
        }
    }, [started]);

    // Gaze/Face Tracking Loop
    useEffect(() => {
        let interval;
        if (started && modelRef.current && webcamRef.current) {
            interval = setInterval(async () => {
                if (webcamRef.current.video.readyState === 4) {
                    const video = webcamRef.current.video;
                    const predictions = await modelRef.current.estimateFaces(video, false);

                    if (predictions.length === 0) {
                        addWarning("No face detected! Please stay in frame.");
                    } else if (predictions.length > 1) {
                        addWarning("Multiple faces detected!");
                    }
                }
            }, 4000);
        }
        return () => clearInterval(interval);
    }, [started]);

    // Timer
    useEffect(() => {
        if (!started || timeLeft <= 0) return;
        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    handleSubmit();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [started, timeLeft]);

    if (loading) return <div className="min-h-screen bg-black text-white flex items-center justify-center"><Loader2 className="animate-spin" size={48} /></div>;

    if (!started) {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8 font-sans">
                <div className="max-w-2xl w-full bg-deep-space border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-purple-600"></div>

                    <h1 className="text-3xl font-orbitron mb-2">{examData.title}</h1>
                    <p className="text-gray-400 mb-8">{examData.description}</p>

                    <div className="grid grid-cols-2 gap-4 mb-8">
                        <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                            <Clock className="text-neon-blue mb-2" />
                            <div className="text-xl font-bold">{examData.time_limit_minutes} Mins</div>
                            <div className="text-xs text-gray-400">Time Limit</div>
                        </div>
                        <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                            <ShieldAlert className="text-red-500 mb-2" />
                            <div className="text-xl font-bold">Strict</div>
                            <div className="text-xs text-gray-400">Proctoring Level</div>
                        </div>
                    </div>

                    <div className="space-y-4 mb-8">
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <CheckCircle size={16} className="text-green-500" /> Fullscreen Mode Required
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <CheckCircle size={16} className="text-green-500" /> Webcam & Mic Access Required
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <CheckCircle size={16} className="text-green-500" /> No Tab Switching Allowed
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <CheckCircle size={16} className="text-green-500" /> AI Face Tracking Enabled
                        </div>
                    </div>

                    {/* Camera Preview */}
                    <div className="mb-8 relative rounded-lg overflow-hidden border border-white/20 bg-black aspect-video flex items-center justify-center">
                        <Webcam
                            audio={false}
                            ref={webcamRef}
                            screenshotFormat="image/jpeg"
                            className="w-full h-full object-cover"
                            onUserMedia={() => setCameraPermission('granted')}
                            onUserMediaError={() => setCameraPermission('denied')}
                        />
                        {!cameraPermission && <div className="absolute inset-0 bg-black/80 flex items-center justify-center text-gray-400">Requesting Camera Access...</div>}
                        {cameraPermission === 'denied' && <div className="absolute inset-0 bg-red-900/80 flex items-center justify-center text-white font-bold">Camera Access Denied</div>}
                    </div>

                    <button
                        onClick={startExam}
                        disabled={cameraPermission !== 'granted' || !modelLoaded}
                        className="w-full py-4 bg-red-600 hover:bg-red-700 disabled:bg-gray-800 disabled:text-gray-500 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                    >
                        {modelLoaded ? <><Shield size={20} /> Start Proctored Exam</> : <><Loader2 className="animate-spin" /> Loading AI Models...</>}
                    </button>
                    {!modelLoaded && <p className="text-xs text-center text-gray-500 mt-2">Downloading proctoring resources (~5MB)...</p>}
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white flex flex-col relative" style={{ userSelect: 'none' }} onContextMenu={e => e.preventDefault()}>
            {/* Proctor Overlay (Webcam) */}
            <div className="fixed bottom-4 right-4 w-48 h-36 border-2 border-red-500/50 rounded-lg overflow-hidden bg-black z-50 shadow-2xl">
                <Webcam audio={false} ref={webcamRef} className="w-full h-full object-cover opacity-80" />
                <div className="absolute top-1 left-1 flex items-center gap-1 bg-black/60 px-2 py-0.5 rounded text-[10px] text-red-400 font-mono">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> REC
                </div>
            </div>

            {/* Warnings Overlay */}
            {warnings > 0 && (
                <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-red-500/90 text-white px-6 py-2 rounded-full font-bold shadow-[0_0_20px_rgba(239,68,68,0.6)] animate-pulse z-50 flex items-center gap-2">
                    <AlertTriangle size={20} /> {warnings}/3 Warnings
                </div>
            )}

            {/* Header */}
            <header className="h-16 border-b border-white/10 bg-deep-space/50 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-40">
                <div className="font-orbitron font-bold text-xl">{examData.title}</div>
                <div className="flex items-center gap-6">
                    <div className="font-mono text-xl text-neon-blue flex items-center gap-2">
                        <Clock size={20} />
                        {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                    </div>
                    <button onClick={() => handleSubmit()} className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded text-sm transition-colors">
                        Submit Exam
                    </button>
                </div>
            </header>

            {/* Questions */}
            <main className="flex-1 max-w-4xl mx-auto w-full p-8 pb-32">
                <div className="space-y-8">
                    {examData.questions.map((q, idx) => (
                        <div key={q.id} className="bg-white/5 border border-white/10 rounded-xl p-6">
                            <div className="flex gap-4">
                                <span className="text-gray-500 font-mono text-lg">{idx + 1}.</span>
                                <div className="flex-1">
                                    <h3 className="text-lg font-medium mb-4">{q.question}</h3>

                                    {/* Question Types */}
                                    {q.type === 'text' ? (
                                        <textarea
                                            value={answers[q.id] || ''}
                                            onChange={e => setAnswers({ ...answers, [q.id]: e.target.value })}
                                            className="w-full bg-black/40 border border-white/20 rounded-lg p-3 text-white focus:border-neon-blue outline-none h-32"
                                            placeholder="Type your answer here..."
                                        />
                                    ) : (
                                        <div className="space-y-2">
                                            {q.type === 'tf' ? ['True', 'False'].map((opt, oIdx) => (
                                                <label key={opt} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${answers[q.id] === oIdx ? 'bg-neon-blue/20 border-neon-blue' : 'bg-black/20 border-white/10 hover:border-white/30'}`}>
                                                    <input
                                                        type="radio"
                                                        name={q.id}
                                                        checked={answers[q.id] === oIdx}
                                                        onChange={() => setAnswers({ ...answers, [q.id]: oIdx })}
                                                        className="hidden"
                                                    />
                                                    <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${answers[q.id] === oIdx ? 'border-neon-blue' : 'border-gray-500'}`}>
                                                        {answers[q.id] === oIdx && <div className="w-2.5 h-2.5 rounded-full bg-neon-blue" />}
                                                    </div>
                                                    <span>{opt}</span>
                                                </label>
                                            )) : (q.options && q.options.length > 0) ? q.options.map((opt, oIdx) => (
                                                <label key={oIdx} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${q.type === 'msq'
                                                    ? (answers[q.id]?.includes(oIdx) ? 'bg-neon-blue/20 border-neon-blue' : 'bg-black/20 border-white/10 hover:border-white/30')
                                                    : (answers[q.id] === oIdx ? 'bg-neon-blue/20 border-neon-blue' : 'bg-black/20 border-white/10 hover:border-white/30')
                                                    }`}>
                                                    <input
                                                        type={q.type === 'msq' ? 'checkbox' : 'radio'}
                                                        name={q.id}
                                                        checked={q.type === 'msq' ? (answers[q.id] || []).includes(oIdx) : answers[q.id] === oIdx}
                                                        onChange={() => {
                                                            if (q.type === 'msq') {
                                                                const curr = answers[q.id] || [];
                                                                if (curr.includes(oIdx)) setAnswers({ ...answers, [q.id]: curr.filter(i => i !== oIdx) });
                                                                else setAnswers({ ...answers, [q.id]: [...curr, oIdx] });
                                                            } else {
                                                                setAnswers({ ...answers, [q.id]: oIdx });
                                                            }
                                                        }}
                                                        className="hidden"
                                                    />
                                                    <div className={`w-5 h-5 ${q.type === 'msq' ? 'rounded' : 'rounded-full'} border flex items-center justify-center ${(q.type === 'msq' ? (answers[q.id] || []).includes(oIdx) : answers[q.id] === oIdx) ? 'border-neon-blue bg-neon-blue/20' : 'border-gray-500'
                                                        }`}>
                                                        {(q.type === 'msq' ? (answers[q.id] || []).includes(oIdx) : answers[q.id] === oIdx) && <div className={`w-2.5 h-2.5 ${q.type === 'msq' ? 'rounded-sm' : 'rounded-full'} bg-neon-blue`} />}
                                                    </div>
                                                    <span>{opt}</span>
                                                </label>
                                            )) : <span className="text-gray-500">No options available</span>}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default ExamView;
