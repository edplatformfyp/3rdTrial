import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Map, CheckCircle, Circle, PlayCircle, ChevronLeft, Award, Download, Loader2, X, FileText } from 'lucide-react';
import ContentView from './ContentView';
import html2canvas from 'html2canvas';

const RoadmapView = ({ courseId }) => {
    const navigate = useNavigate();
    const [course, setCourse] = useState(null);
    const [selectedChapterId, setSelectedChapterId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    // Certificate state
    const [certEligible, setCertEligible] = useState(false);
    const [certProgress, setCertProgress] = useState({ completed: 0, total: 0 });
    const [examStatus, setExamStatus] = useState({ required: false, passed: false });
    const [showCert, setShowCert] = useState(false);
    const [certData, setCertData] = useState(null);
    const [loadingCert, setLoadingCert] = useState(false);
    const certRef = useRef(null);

    useEffect(() => {
        if (!courseId) return;

        const fetchCourse = async () => {
            setLoading(true);
            try {
                const res = await axios.get(`http://localhost:8000/courses/${courseId}`);
                setCourse(res.data);
                // Default select first chapter if none selected
                if (res.data.chapters && res.data.chapters.length > 0) {
                    setSelectedChapterId(res.data.chapters[0].id);
                }
            } catch (err) {
                console.error("Failed to load course", err);
            } finally {
                setLoading(false);
            }
        };

        fetchCourse();
    }, [courseId]);

    // Check certificate eligibility
    useEffect(() => {
        if (!courseId) return;
        const checkCert = async () => {
            try {
                const res = await axios.get(`http://localhost:8000/courses/${courseId}/certificate/check`);
                setCertEligible(res.data.eligible);
                setCertProgress({ completed: res.data.completed, total: res.data.total });
                setExamStatus({ required: res.data.exam_required, passed: res.data.exam_passed });
            } catch (err) {
                console.error('Cert check failed', err);
            }
        };
        checkCert();
    }, [courseId]);

    const handleViewCertificate = async () => {
        setLoadingCert(true);
        try {
            const res = await axios.get(`http://localhost:8000/courses/${courseId}/certificate`);
            setCertData(res.data);
            setShowCert(true);
        } catch (err) {
            alert(err.response?.data?.detail || 'Cannot get certificate');
        } finally {
            setLoadingCert(false);
        }
    };

    const handleDownloadCert = async () => {
        if (!certRef.current) return;
        try {
            const canvas = await html2canvas(certRef.current, { scale: 2, useCORS: true, backgroundColor: null });
            const link = document.createElement('a');
            link.download = `certificate_${certData?.certificate_id || 'educore'}.png`;
            link.href = canvas.toDataURL();
            link.click();
        } catch (err) {
            alert('Download failed');
        }
    };

    if (loading) return <div className="text-neon-blue animate-pulse">Loading Blueprint...</div>;
    if (!course) return null;

    return (
        <div className="h-full flex flex-col md:flex-row gap-6 overflow-hidden">
            {/* Chapter List (Mini Sidebar) */}
            <div className={`flex-shrink-0 flex flex-col gap-3 overflow-y-auto transition-all duration-300 ease-in-out border-r border-white/5 bg-black/20
                ${isSidebarOpen ? 'w-full md:w-80 p-4' : 'w-20 py-4 items-center'}
            `}>
                <div className={`flex items-center justify-between mb-6 sticky top-0 z-10 ${isSidebarOpen ? 'px-2' : 'flex-col gap-4'}`}>
                    {isSidebarOpen ? (
                        <div>
                            <h2 className="text-lg font-orbitron text-white glitch-text" data-text={course.topic}>{course.topic}</h2>
                            <div className="flex items-center gap-2 text-xs text-neon-blue uppercase tracking-widest mt-1">
                                <Map size={12} /> PATH
                            </div>
                        </div>
                    ) : (
                        <div className="w-10 h-10 rounded-full bg-neon-blue/10 flex items-center justify-center text-neon-blue border border-neon-blue/30 shadow-[0_0_10px_rgba(0,243,255,0.2)]">
                            <Map size={20} />
                        </div>
                    )}

                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className={`text-gray-400 hover:text-white transition-colors p-1 rounded-md hover:bg-white/5 ${!isSidebarOpen && 'mt-2'}`}
                        title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                    >
                        <ChevronLeft size={20} className={`transition-transform duration-300 ${!isSidebarOpen ? 'rotate-180 text-neon-blue' : ''}`} />
                    </button>
                </div>

                <div className={`flex flex-col gap-3 ${!isSidebarOpen && 'items-center w-full px-2'}`}>
                    {course.chapters.map((chapter, index) => {
                        const isSelected = selectedChapterId === chapter.id;
                        return (
                            <div
                                key={chapter.id}
                                onClick={() => setSelectedChapterId(chapter.id)}
                                className={`
                                    relative cursor-pointer transition-all duration-300 rounded-lg border group
                                    ${isSelected
                                        ? 'bg-neon-blue/10 border-neon-blue shadow-[0_0_15px_rgba(0,243,255,0.15)]'
                                        : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20'
                                    }
                                    ${isSidebarOpen ? 'p-4' : 'w-12 h-12 flex items-center justify-center'}
                                `}
                                title={!isSidebarOpen ? chapter.title : ""}
                            >
                                {isSidebarOpen ? (
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 ${isSelected ? 'text-neon-blue' : 'text-gray-500 group-hover:text-gray-300'}`}>
                                            {isSelected ? <PlayCircle size={20} /> : <Circle size={20} />}
                                        </div>
                                        <div>
                                            <h4 className={`font-semibold text-sm ${isSelected ? 'text-white' : 'text-gray-300 group-hover:text-white'}`}>
                                                {chapter.chapter_number}. {chapter.title}
                                            </h4>
                                        </div>
                                    </div>
                                ) : (
                                    <span className={`font-mono font-bold text-lg ${isSelected ? 'text-neon-blue' : 'text-gray-500 group-hover:text-gray-300'}`}>
                                        {chapter.chapter_number}
                                    </span>
                                )}

                                {/* Active Indicator Bar for Collapsed State */}
                                {!isSidebarOpen && isSelected && (
                                    <div className="absolute -right-[1px] top-2 bottom-2 w-[2px] bg-neon-blue rounded-l" />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Certificate Button */}
                {certProgress.total > 0 && (
                    <div className={`p-3 border-t border-white/10 ${isSidebarOpen ? '' : 'flex justify-center'}`}>
                        {certEligible ? (
                            <button
                                onClick={handleViewCertificate}
                                disabled={loadingCert}
                                className={`${isSidebarOpen ? 'w-full' : 'w-12 h-12'} flex items-center justify-center gap-2 rounded-lg py-2 bg-gradient-to-r from-yellow-600/30 to-amber-600/30 border border-yellow-500/40 text-yellow-300 hover:from-yellow-600/40 hover:to-amber-600/40 transition-all shadow-[0_0_15px_rgba(234,179,8,0.15)]`}
                            >
                                {loadingCert ? <Loader2 size={18} className="animate-spin" /> : <Award size={18} />}
                                {isSidebarOpen && (loadingCert ? 'Loading...' : '🎓 View Certificate')}
                            </button>
                        ) : (
                            isSidebarOpen && (
                                <div className="text-xs text-center">
                                    {certProgress.completed >= certProgress.total && certProgress.total > 0 && examStatus.required && !examStatus.passed ? (
                                        <div className="space-y-2">
                                            <div className="text-green-400 font-bold">All Quizzes Completed!</div>
                                            <button
                                                onClick={() => navigate(`/course/${courseId}/exam`)}
                                                className="w-full flex items-center justify-center gap-2 rounded-lg py-2 bg-red-500/20 border border-red-500/40 text-red-400 hover:bg-red-500/30 transition-all shadow-[0_0_10px_rgba(239,68,68,0.2)] animate-pulse"
                                            >
                                                <FileText size={16} /> Take Final Exam
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="mb-1 text-gray-500">Complete all quizzes {examStatus.required ? '& exam' : ''} for certificate</div>
                                            <div className="w-full bg-gray-800 rounded-full h-1.5">
                                                <div className="h-1.5 rounded-full bg-neon-blue/60 transition-all" style={{ width: `${(certProgress.completed / Math.max(certProgress.total, 1)) * 100}%` }} />
                                            </div>
                                            <div className="mt-1 text-gray-600">{certProgress.completed}/{certProgress.total} quizzes completed</div>
                                        </>
                                    )}
                                </div>
                            )
                        )}
                    </div>
                )}
            </div>

            {/* Main Content Area */}
            <div className="flex-1 card-glass overflow-hidden flex flex-col">
                {selectedChapterId && (
                    <ContentView
                        courseId={courseId}
                        chapterId={selectedChapterId}
                        chapter={course.chapters.find(c => c.id === selectedChapterId)}
                    />
                )}
            </div>

            {/* Certificate Modal */}
            {showCert && certData && (
                <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="flex flex-col items-center gap-4 max-w-[960px]">
                        <div className="flex items-center gap-4">
                            <h2 className="text-xl font-orbitron text-yellow-400 flex items-center gap-2"><Award size={24} /> Your Certificate</h2>
                            <button onClick={handleDownloadCert} className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-neon-blue/20 border border-neon-blue/40 text-neon-blue hover:bg-neon-blue/30 transition-colors">
                                <Download size={16} /> Download PNG
                            </button>
                            <button onClick={() => setShowCert(false)} className="text-gray-400 hover:text-white ml-4"><X size={20} /></button>
                        </div>

                        {/* Certificate Render */}
                        <div ref={certRef}
                            style={{
                                width: 900,
                                height: 636,
                                backgroundColor: certData.template.custom_bg_url ? 'transparent' : certData.template.bg_color,
                                backgroundImage: certData.template.custom_bg_url ? `url(http://localhost:8000${certData.template.custom_bg_url})` : 'none',
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                color: certData.template.text_color,
                                fontFamily: certData.template.font_style === 'Orbitron' ? '"Orbitron", sans-serif' : certData.template.font_style === 'Rajdhani' ? '"Rajdhani", sans-serif' : certData.template.font_style,
                                position: 'relative',
                                overflow: 'hidden',
                            }}
                            className="rounded-xl shadow-2xl border border-white/10"
                        >
                            {/* Decorative Borders */}
                            <div style={{ position: 'absolute', inset: 12, border: `2px solid ${certData.template.accent_color}40`, borderRadius: 12 }} />
                            <div style={{ position: 'absolute', inset: 16, border: `1px solid ${certData.template.accent_color}20`, borderRadius: 10 }} />

                            {/* EduCore Watermark */}
                            <div style={{
                                position: 'absolute', top: '50%', left: '50%',
                                transform: 'translate(-50%, -50%) rotate(-30deg)',
                                fontSize: 80, fontWeight: 900, opacity: 0.04, letterSpacing: 16,
                                whiteSpace: 'nowrap', fontFamily: '"Orbitron", sans-serif', pointerEvents: 'none',
                            }}>EDUCORE</div>

                            {/* Corner Accents */}
                            <div style={{ position: 'absolute', top: 20, left: 20, width: 40, height: 40, borderTop: `3px solid ${certData.template.accent_color}`, borderLeft: `3px solid ${certData.template.accent_color}` }} />
                            <div style={{ position: 'absolute', top: 20, right: 20, width: 40, height: 40, borderTop: `3px solid ${certData.template.accent_color}`, borderRight: `3px solid ${certData.template.accent_color}` }} />
                            <div style={{ position: 'absolute', bottom: 20, left: 20, width: 40, height: 40, borderBottom: `3px solid ${certData.template.accent_color}`, borderLeft: `3px solid ${certData.template.accent_color}` }} />
                            <div style={{ position: 'absolute', bottom: 20, right: 20, width: 40, height: 40, borderBottom: `3px solid ${certData.template.accent_color}`, borderRight: `3px solid ${certData.template.accent_color}` }} />

                            {/* Content */}
                            <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 48 }}>
                                {certData.template.logo_url && (
                                    <img src={`http://localhost:8000${certData.template.logo_url}`} alt="Logo" style={{ width: 64, height: 64, objectFit: 'contain', marginBottom: 12 }} />
                                )}
                                <div style={{ fontSize: 40, marginBottom: 8 }}>🏆</div>
                                <h1 style={{ fontSize: 32, fontWeight: 800, color: certData.template.accent_color, letterSpacing: 4, textTransform: 'uppercase', marginBottom: 24, textAlign: 'center' }}>
                                    {certData.template.title_text}
                                </h1>
                                <p style={{ fontSize: 14, opacity: 0.6, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>This certifies that</p>
                                <h2 style={{ fontSize: 36, fontWeight: 700, borderBottom: `2px solid ${certData.template.accent_color}`, paddingBottom: 8, marginBottom: 16, letterSpacing: 2 }}>
                                    {certData.student_name}
                                </h2>
                                <p style={{ fontSize: 16, opacity: 0.8, marginBottom: 8, textAlign: 'center' }}>{certData.template.body_text}</p>
                                <h3 style={{ fontSize: 22, fontWeight: 700, color: certData.template.accent_color, marginBottom: 32, textAlign: 'center' }}>
                                    "{certData.course_name}"
                                </h3>
                                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', maxWidth: 600, alignItems: 'flex-end' }}>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ width: 140, borderTop: `1px solid ${certData.template.accent_color}60`, paddingTop: 8, fontSize: 11, opacity: 0.6 }}>Date</div>
                                        <div style={{ fontSize: 12, marginTop: 4, opacity: 0.8 }}>{new Date(certData.issued_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                                    </div>
                                    <div style={{ fontSize: 10, opacity: 0.3, fontFamily: 'monospace' }}>ID: {certData.certificate_id}</div>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ width: 140, borderTop: `1px solid ${certData.template.accent_color}60`, paddingTop: 8, fontSize: 11, opacity: 0.6 }}>
                                            {certData.template.signature_text || 'Authorized Signatory'}
                                        </div>
                                        <div style={{ fontSize: 12, marginTop: 4, opacity: 0.8 }}>{certData.org_name}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoadmapView;
