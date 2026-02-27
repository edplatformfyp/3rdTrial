import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ChevronLeft, Plus, Save, Trash2, Rocket, Loader2, GripVertical, PenLine, X, CheckCircle, Sparkles, Upload, ImagePlus, Award, Palette, Settings, FileText, Check, AlertTriangle, Key } from 'lucide-react';

const OrgCourseEditor = () => {
    const { courseId } = useParams();
    const navigate = useNavigate();

    const [course, setCourse] = useState(null);
    const [chapters, setChapters] = useState([]);
    const [selectedChapterId, setSelectedChapterId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    const [saving, setSaving] = useState(false);

    // Editor state
    const [editTitle, setEditTitle] = useState('');
    const [editContent, setEditContent] = useState('');
    const [editVideo, setEditVideo] = useState('');
    const [videoFileName, setVideoFileName] = useState('');
    const [uploading, setUploading] = useState(false);
    const [editQuiz, setEditQuiz] = useState([]);

    // Inline module title rename
    const [renamingId, setRenamingId] = useState(null);
    const [renameValue, setRenameValue] = useState('');

    // Add module modal
    const [showAddModule, setShowAddModule] = useState(false);
    const [newModuleTitle, setNewModuleTitle] = useState('');
    const [newModuleDesc, setNewModuleDesc] = useState('');

    // Cover image upload
    const [uploadingCover, setUploadingCover] = useState(false);

    // Certificate template editor
    const [showCertEditor, setShowCertEditor] = useState(false);
    const [certTemplate, setCertTemplate] = useState({
        title_text: 'Certificate of Completion',
        body_text: 'has successfully completed the course',
        signature_text: '',
        bg_color: '#0a0a1a',
        text_color: '#ffffff',
        accent_color: '#00f3ff',
        font_style: 'Orbitron',
        logo_url: null,
        custom_bg_url: null
    });
    const [savingCert, setSavingCert] = useState(false);

    const fetchCertTemplate = async () => {
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/certificate-template`);
            setCertTemplate(res.data);
        } catch (err) {
            console.error('Failed to load cert template', err);
        }
    };

    const saveCertTemplate = async () => {
        setSavingCert(true);
        try {
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/certificate-template`, certTemplate);
        } catch (err) {
            alert('Failed to save template');
        } finally {
            setSavingCert(false);
        }
    };

    const handleCertLogoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
            const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/upload/cert-logo/${courseId}`, fd);
            setCertTemplate(prev => ({ ...prev, logo_url: res.data.logo_url }));
        } catch (err) {
            alert('Failed to upload logo');
        }
    };

    const handleCertBgUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
            const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/upload/cert-template/${courseId}`, fd);
            setCertTemplate(prev => ({ ...prev, custom_bg_url: res.data.custom_bg_url }));
        } catch (err) {
            alert('Failed to upload background');
        }
    };

    // Exam Config State
    const [showExamConfig, setShowExamConfig] = useState(false);
    const [examConfig, setExamConfig] = useState({
        enabled: false,
        title: 'Final Examination',
        description: 'Proctored final exam for this course.',
        time_limit_minutes: 60,
        passing_score: 70,
        max_attempts: 1,
        questions: []
    });
    const [savingExam, setSavingExam] = useState(false);

    const fetchExamConfig = async () => {
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/exam-config`);
            setExamConfig(res.data);
        } catch (err) {
            console.error('Failed to load exam config', err);
        }
    };

    const saveExamConfig = async () => {
        setSavingExam(true);
        try {
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/exam-config`, examConfig);
            setShowExamConfig(false);
        } catch (err) {
            alert('Failed to save exam config');
        } finally {
            setSavingExam(false);
        }
    };

    // Access Keys State
    const [showKeyModal, setShowKeyModal] = useState(false);
    const [courseKeys, setCourseKeys] = useState([]);
    const [loadingKeys, setLoadingKeys] = useState(false);
    const [keyCount, setKeyCount] = useState(1);
    const [generatingKeys, setGeneratingKeys] = useState(false);

    const fetchKeys = async () => {
        setLoadingKeys(true);
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/keys`);
            setCourseKeys(res.data);
        } catch (err) {
            console.error('Failed to load keys', err);
        } finally {
            setLoadingKeys(false);
        }
    };

    const generateKeys = async () => {
        setGeneratingKeys(true);
        try {
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/keys`, { count: keyCount });
            fetchKeys();
        } catch (err) {
            alert('Failed to generate keys');
        } finally {
            setGeneratingKeys(false);
        }
    };

    useEffect(() => {
        fetchCourseDetails();
    }, [courseId]);

    const fetchCourseDetails = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/courses/${courseId}`);
            setCourse(res.data);
            setChapters(res.data.chapters || []);

            // Select first chapter if available and none selected
            if (res.data.chapters && res.data.chapters.length > 0 && !selectedChapterId) {
                const first = res.data.chapters[0];
                setSelectedChapterId(first.id);
                fetchModuleDetails(courseId, first.id);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchModuleDetails = async (cId, mId) => {
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${cId}/modules/${mId}`);
            setEditTitle(res.data.title || '');
            setEditContent(res.data.content_markdown || '');
            setEditVideo(res.data.video_url || '');
            setVideoFileName(res.data.video_url ? res.data.video_url.split('/').pop() : '');
            setEditQuiz(res.data.quiz_json || []);
        } catch (err) {
            console.error("Failed to load module details", err);
        }
    };

    const handleChapterSelect = (chapterId) => {
        setSelectedChapterId(chapterId);
        fetchModuleDetails(courseId, chapterId);
    };

    // --- AI Plan Generation ---
    const handleGeneratePlan = async () => {
        if (chapters.length > 0 && !confirm("This will overwrite existing chapters. Continue?")) return;

        setGenerating(true);
        try {
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/plan`, {
                topic: course.topic,
                grade_level: course.grade_level || "General",
                structure_type: course.structure_type || "week"
            });
            setSelectedChapterId(null);
            await fetchCourseDetails();
        } catch (err) {
            alert("Plan generation failed. Check backend logs.");
            console.error(err);
        } finally {
            setGenerating(false);
        }
    };



    // --- Add Module ---
    const handleAddModule = async () => {
        if (!newModuleTitle.trim()) return;

        try {
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules`, {
                title: newModuleTitle.trim(),
                order_index: chapters.length,
                description: newModuleDesc.trim()
            });
            setShowAddModule(false);
            setNewModuleTitle('');
            setNewModuleDesc('');
            fetchCourseDetails();
        } catch (err) {
            alert("Failed to add module");
        }
    };

    // --- Delete Module ---
    const handleDeleteModule = async (moduleId, e) => {
        e.stopPropagation();
        if (!confirm("Delete this module permanently?")) return;
        try {
            await axios.delete(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules/${moduleId}`);
            if (selectedChapterId === moduleId) {
                setSelectedChapterId(null);
                setEditContent('');
                setEditVideo('');
                setEditQuiz([]);
                setEditTitle('');
            }
            fetchCourseDetails();
        } catch (err) {
            alert("Failed to delete module");
        }
    };

    // --- Rename Module ---
    const startRename = (ch, e) => {
        e.stopPropagation();
        setRenamingId(ch.id);
        setRenameValue(ch.title);
    };

    const confirmRename = async (moduleId) => {
        if (!renameValue.trim()) return;
        try {
            await axios.put(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules/${moduleId}`, {
                content_markdown: null, // don't overwrite
                title: renameValue.trim()
            });
            setRenamingId(null);
            fetchCourseDetails();
        } catch (err) {
            alert("Failed to rename module");
        }
    };

    // --- Save Content ---
    const handleSaveContent = async () => {
        if (!selectedChapterId) return;
        setSaving(true);
        try {
            const payload = {
                content_markdown: editContent,
                video_url: editVideo,
            };
            // Include quiz if we have any
            if (editQuiz.length > 0) {
                payload.quiz = editQuiz;
            }
            await axios.put(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules/${selectedChapterId}`, payload);
            setSaving(false);
            // Brief success indicator
            alert("✅ Content saved successfully!");
        } catch (err) {
            setSaving(false);
            alert("Failed to save content");
        }
    };

    // --- Quiz Editing Helpers ---
    const updateQuizQuestion = (index, field, value) => {
        const updated = [...editQuiz];
        updated[index] = { ...updated[index], [field]: value };
        setEditQuiz(updated);
    };

    const updateQuizOption = (qIndex, oIndex, value) => {
        const updated = [...editQuiz];
        const options = [...updated[qIndex].options];
        options[oIndex] = value;
        updated[qIndex] = { ...updated[qIndex], options };
        setEditQuiz(updated);
    };

    const addQuizQuestion = () => {
        setEditQuiz([...editQuiz, {
            question: '',
            options: ['', '', '', ''],
            correct_answer: 0
        }]);
    };

    const removeQuizQuestion = (index) => {
        setEditQuiz(editQuiz.filter((_, i) => i !== index));
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center text-neon-blue font-orbitron">Loading Editor...</div>;
    if (!course) return <div className="text-center p-10 text-red-500">Course not found</div>;

    const selectedChapter = chapters.find(ch => ch.id === selectedChapterId);

    return (
        <div className="h-screen flex flex-col bg-deep-space text-white overflow-hidden">
            {/* Header */}
            <header className="h-16 border-b border-neon-blue/20 bg-deep-space/80 backdrop-blur-md flex items-center px-4 justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/org')} className="text-gray-400 hover:text-white transition-colors">
                        <ChevronLeft />
                    </button>
                    <div>
                        <h1 className="text-xl font-orbitron text-white">{course.topic}</h1>
                        <div className="flex gap-2 items-center">
                            <span className="text-xs text-neon-blue px-2 py-0.5 border border-neon-blue/30 rounded">EDITOR MODE</span>
                            <span className="text-xs text-gray-500">{chapters.length} modules</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleGeneratePlan}
                        disabled={generating}
                        className="btn-neon text-sm py-1 flex items-center gap-2 disabled:opacity-50"
                    >
                        {generating ? <Loader2 className="animate-spin" size={16} /> : <Rocket size={16} />}
                        {generating ? "Generating..." : (chapters.length === 0 ? "Generate AI Plan" : "Regenerate Plan")}
                    </button>
                    <button
                        onClick={() => { fetchCertTemplate(); setShowCertEditor(true); }}
                        className="text-sm py-1 px-3 flex items-center gap-2 rounded border border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10 transition-colors"
                    >
                        <Award size={16} /> Certificate
                    </button>
                    <button
                        onClick={() => { fetchExamConfig(); setShowExamConfig(true); }}
                        className="text-sm py-1 px-3 flex items-center gap-2 rounded border border-red-500/50 text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                        <Settings size={16} /> Exam Settings
                    </button>
                    <button
                        onClick={() => { fetchKeys(); setShowKeyModal(true); }}
                        className="text-sm py-1 px-3 flex items-center gap-2 rounded border border-purple-500/50 text-purple-400 hover:bg-purple-500/10 transition-colors"
                    >
                        <Key size={16} /> Access Keys
                    </button>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar - Module List */}
                <aside className="w-80 border-r border-white/10 flex flex-col bg-black/20 shrink-0">
                    {/* Cover Image Section */}
                    <div className="relative group border-b border-white/10">
                        {course.thumbnail_url ? (
                            <div className="h-32 overflow-hidden relative">
                                <img
                                    src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${course.thumbnail_url}`}
                                    alt="Cover"
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <label className="cursor-pointer flex items-center gap-2 text-sm text-white bg-black/60 px-3 py-1.5 rounded-lg border border-white/20 hover:bg-black/80 transition-colors">
                                        <ImagePlus size={14} />
                                        Change Cover
                                        <input
                                            type="file"
                                            accept="image/*"
                                            className="hidden"
                                            onChange={async (e) => {
                                                const file = e.target.files[0];
                                                if (!file) return;
                                                setUploadingCover(true);
                                                const fd = new FormData();
                                                fd.append('file', file);
                                                try {
                                                    await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/upload/cover/${courseId}`, fd);
                                                    fetchCourseDetails();
                                                } catch (err) {
                                                    alert('Failed to upload cover image');
                                                } finally {
                                                    setUploadingCover(false);
                                                }
                                            }}
                                        />
                                    </label>
                                </div>
                                {uploadingCover && (
                                    <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
                                        <Loader2 className="animate-spin text-neon-blue" size={24} />
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="h-24 flex items-center justify-center bg-gradient-to-br from-white/[0.02] to-white/[0.01]">
                                <label className="cursor-pointer flex flex-col items-center gap-1 text-gray-500 hover:text-neon-blue transition-colors">
                                    <ImagePlus size={24} />
                                    <span className="text-xs">{uploadingCover ? 'Uploading...' : 'Add Cover Image'}</span>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        className="hidden"
                                        disabled={uploadingCover}
                                        onChange={async (e) => {
                                            const file = e.target.files[0];
                                            if (!file) return;
                                            setUploadingCover(true);
                                            const fd = new FormData();
                                            fd.append('file', file);
                                            try {
                                                await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/upload/cover/${courseId}`, fd);
                                                fetchCourseDetails();
                                            } catch (err) {
                                                alert('Failed to upload cover image');
                                            } finally {
                                                setUploadingCover(false);
                                            }
                                        }}
                                    />
                                </label>
                            </div>
                        )}
                    </div>
                    <div className="p-4 border-b border-white/10 flex justify-between items-center">
                        <span className="font-bold text-gray-300">Modules</span>
                        <button onClick={() => setShowAddModule(true)} className="text-neon-blue hover:text-white transition-colors" title="Add Module">
                            <Plus size={20} />
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                        {chapters.map((ch, idx) => (
                            <div
                                key={ch.id}
                                onClick={() => handleChapterSelect(ch.id)}
                                className={`group p-3 rounded cursor-pointer transition-all border ${selectedChapterId === ch.id
                                    ? 'bg-neon-blue/10 border-neon-blue text-white shadow-[0_0_8px_rgba(0,243,255,0.15)]'
                                    : 'border-transparent hover:bg-white/5 text-gray-400'
                                    }`}
                            >
                                {renamingId === ch.id ? (
                                    <div className="flex items-center gap-1">
                                        <input
                                            value={renameValue}
                                            onChange={e => setRenameValue(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && confirmRename(ch.id)}
                                            className="flex-1 bg-black/40 border border-neon-blue/50 rounded px-2 py-1 text-sm text-white focus:outline-none"
                                            autoFocus
                                            onClick={e => e.stopPropagation()}
                                        />
                                        <button onClick={(e) => { e.stopPropagation(); confirmRename(ch.id); }} className="text-neon-green hover:text-white">
                                            <CheckCircle size={16} />
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setRenamingId(null); }} className="text-gray-500 hover:text-white">
                                            <X size={16} />
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 overflow-hidden">
                                            <span className="text-xs font-mono text-gray-600 w-5 text-center shrink-0">{ch.chapter_number || idx + 1}</span>
                                            <span className="text-sm font-bold truncate">{ch.title}</span>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                            <button onClick={(e) => startRename(ch, e)} className="p-1 hover:text-neon-blue" title="Rename">
                                                <PenLine size={13} />
                                            </button>
                                            <button onClick={(e) => handleDeleteModule(ch.id, e)} className="p-1 hover:text-red-400" title="Delete">
                                                <Trash2 size={13} />
                                            </button>
                                        </div>
                                    </div>
                                )}
                                {ch.content_markdown && (
                                    <div className="mt-1 text-[10px] text-neon-green/60">● Content Ready</div>
                                )}
                            </div>
                        ))}
                        {chapters.length === 0 && (
                            <div className="text-center text-gray-500 p-6 text-sm space-y-3">
                                <Rocket size={32} className="mx-auto text-gray-600" />
                                <p>No modules yet.</p>
                                <p className="text-xs">Click <strong>"Generate AI Plan"</strong> above to auto-create a roadmap, or add modules manually.</p>
                            </div>
                        )}
                    </div>
                </aside>

                {/* Main Content - Editor */}
                <main className="flex-1 flex flex-col bg-deep-space relative overflow-hidden">
                    {selectedChapterId && selectedChapter ? (
                        <div className="flex-1 flex flex-col p-6 overflow-y-auto">
                            <div className="max-w-4xl mx-auto w-full space-y-6">
                                {/* Module Header */}
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h2 className="text-2xl font-orbitron text-white">
                                            {selectedChapter.title}
                                        </h2>
                                        <p className="text-sm text-gray-500 mt-1">Module {selectedChapter.chapter_number}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={handleSaveContent}
                                            disabled={saving}
                                            className="bg-neon-blue/10 text-neon-blue border border-neon-blue/40 hover:bg-neon-blue hover:text-deep-space px-6 py-2 rounded transition-all flex items-center gap-2 font-bold text-sm disabled:opacity-50"
                                        >
                                            {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                                            Save Changes
                                        </button>
                                    </div>
                                </div>

                                {/* Video Upload */}
                                <div className="card-glass p-4">
                                    <label className="block text-sm text-gray-400 mb-2">Video File (Optional)</label>
                                    {editVideo ? (
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between bg-black/30 rounded-lg p-3 border border-white/5">
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <div className="w-8 h-8 rounded bg-neon-blue/20 flex items-center justify-center shrink-0">
                                                        <Upload size={14} className="text-neon-blue" />
                                                    </div>
                                                    <span className="text-sm text-gray-300 truncate">{videoFileName || 'Uploaded video'}</span>
                                                </div>
                                                <button
                                                    onClick={async () => {
                                                        try {
                                                            await axios.put(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules/${selectedChapterId}`, {
                                                                video_url: ''
                                                            });
                                                            setEditVideo('');
                                                            setVideoFileName('');
                                                        } catch (err) {
                                                            alert('Failed to remove video');
                                                        }
                                                    }}
                                                    className="text-gray-500 hover:text-red-400 transition-colors shrink-0 ml-2 flex items-center gap-1 text-xs"
                                                    title="Delete video"
                                                >
                                                    <Trash2 size={14} /> Delete
                                                </button>
                                            </div>
                                            <video
                                                src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${editVideo}`}
                                                controls
                                                className="w-full rounded-lg max-h-[200px] bg-black"
                                            />
                                        </div>
                                    ) : (
                                        <label className={`flex flex-col items-center justify-center h-28 rounded-lg border-2 border-dashed transition-all cursor-pointer ${uploading ? 'border-neon-blue/50 bg-neon-blue/5' : 'border-gray-700 hover:border-neon-blue/40 hover:bg-white/[0.02]'
                                            }`}>
                                            <input
                                                type="file"
                                                accept="video/mp4,video/webm,video/ogg,video/avi,video/mov"
                                                className="hidden"
                                                onChange={async (e) => {
                                                    const file = e.target.files[0];
                                                    if (!file) return;
                                                    setUploading(true);
                                                    try {
                                                        const formData = new FormData();
                                                        formData.append('file', file);
                                                        const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/upload/video`, formData, {
                                                            headers: { 'Content-Type': 'multipart/form-data' }
                                                        });
                                                        setEditVideo(res.data.video_url);
                                                        setVideoFileName(res.data.filename);
                                                        // Auto-save video to backend so it persists
                                                        await axios.put(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/org/courses/${courseId}/modules/${selectedChapterId}`, {
                                                            video_url: res.data.video_url
                                                        });
                                                    } catch (err) {
                                                        alert('Failed to upload video');
                                                        console.error(err);
                                                    } finally {
                                                        setUploading(false);
                                                    }
                                                }}
                                            />
                                            {uploading ? (
                                                <>
                                                    <Loader2 size={24} className="text-neon-blue animate-spin mb-2" />
                                                    <span className="text-sm text-neon-blue">Uploading...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Upload size={24} className="text-gray-600 mb-2" />
                                                    <span className="text-sm text-gray-500">Click to upload a video file</span>
                                                    <span className="text-xs text-gray-600 mt-1">MP4, WebM, OGG, AVI, MOV</span>
                                                </>
                                            )}
                                        </label>
                                    )}
                                </div>

                                {/* Markdown Editor */}
                                <div className="card-glass p-0 flex flex-col h-[400px]">
                                    <div className="p-3 border-b border-white/10 bg-black/20 text-gray-400 text-sm flex justify-between items-center">
                                        <span>Content (Markdown Supported)</span>
                                        <span className="text-xs text-gray-600">{editContent.length} chars</span>
                                    </div>
                                    <textarea
                                        value={editContent}
                                        onChange={(e) => setEditContent(e.target.value)}
                                        className="flex-1 bg-transparent p-4 text-gray-300 font-mono text-sm focus:outline-none resize-none"
                                        placeholder="# Chapter Introduction&#10;&#10;Write your module content here using Markdown..."
                                    />
                                </div>

                                {/* Quiz Section */}
                                <div className="card-glass p-4 space-y-4">
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-lg font-orbitron text-white">Quiz Questions</h3>
                                        <button
                                            onClick={addQuizQuestion}
                                            className="text-neon-blue text-sm flex items-center gap-1 hover:text-white transition-colors"
                                        >
                                            <Plus size={16} /> Add Question
                                        </button>
                                    </div>

                                    {editQuiz.length === 0 && (
                                        <p className="text-gray-500 text-sm text-center py-4">
                                            No quiz questions yet. Use "AI Generate Content" to auto-create them, or add manually.
                                        </p>
                                    )}

                                    {editQuiz.map((q, qIdx) => (
                                        <div key={qIdx} className="bg-black/30 rounded-lg p-4 border border-white/5 space-y-3">
                                            <div className="flex justify-between items-start gap-2">
                                                <div className="flex-1">
                                                    <label className="text-xs text-gray-500">Question {qIdx + 1}</label>
                                                    <input
                                                        value={q.question}
                                                        onChange={e => updateQuizQuestion(qIdx, 'question', e.target.value)}
                                                        className="w-full bg-transparent border-b border-gray-700 text-white py-1 focus:outline-none focus:border-neon-blue"
                                                        placeholder="Enter question..."
                                                    />
                                                </div>
                                                <button
                                                    onClick={() => removeQuizQuestion(qIdx)}
                                                    className="text-gray-600 hover:text-red-400 transition-colors mt-4"
                                                >
                                                    <X size={16} />
                                                </button>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2">
                                                {q.options.map((opt, oIdx) => (
                                                    <div key={oIdx} className="flex items-center gap-2">
                                                        <button
                                                            onClick={() => updateQuizQuestion(qIdx, 'correct_answer', oIdx)}
                                                            className={`w-5 h-5 rounded-full border-2 shrink-0 transition-all ${q.correct_answer === oIdx
                                                                ? 'border-neon-green bg-neon-green/30'
                                                                : 'border-gray-600 hover:border-gray-400'
                                                                }`}
                                                            title={q.correct_answer === oIdx ? "Correct answer" : "Set as correct"}
                                                        />
                                                        <input
                                                            value={opt}
                                                            onChange={e => updateQuizOption(qIdx, oIdx, e.target.value)}
                                                            className="flex-1 bg-transparent border-b border-gray-800 text-gray-300 text-sm py-1 focus:outline-none focus:border-neon-blue/40"
                                                            placeholder={`Option ${oIdx + 1}`}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500 space-y-4">
                            <Sparkles size={48} className="text-gray-700" />
                            <p className="text-lg">Select a module to edit its content</p>
                            <p className="text-sm text-gray-600">Or generate an AI plan to get started</p>
                        </div>
                    )}
                </main>
            </div>

            <AddModuleModal
                show={showAddModule}
                onClose={() => { setShowAddModule(false); setNewModuleTitle(''); setNewModuleDesc(''); }}
                title={newModuleTitle}
                setTitle={setNewModuleTitle}
                desc={newModuleDesc}
                setDesc={setNewModuleDesc}
                onAdd={handleAddModule}
            />

            {/* Certificate Editor Modal */}
            {showCertEditor && (
                <CertificateEditorModal
                    template={certTemplate}
                    setTemplate={setCertTemplate}
                    onSave={saveCertTemplate}
                    saving={savingCert}
                    onClose={() => setShowCertEditor(false)}
                    courseId={courseId}
                    onLogoUpload={handleCertLogoUpload}
                    onBgUpload={handleCertBgUpload}
                />
            )}

            {/* Exam Config Modal */}
            {showExamConfig && (
                <ExamConfigModal
                    config={examConfig}
                    setConfig={setExamConfig}
                    onSave={saveExamConfig}
                    saving={savingExam}
                    onClose={() => setShowExamConfig(false)}
                />
            )}

            {/* Access Keys Modal */}
            {showKeyModal && (
                <AccessKeysModal
                    keys={courseKeys}
                    loading={loadingKeys}
                    generating={generatingKeys}
                    keyCount={keyCount}
                    setKeyCount={setKeyCount}
                    onGenerate={generateKeys}
                    onClose={() => setShowKeyModal(false)}
                />
            )}
        </div>
    );
};

// --- Add Module Modal ---
const AddModuleModal = ({ show, onClose, title, setTitle, desc, setDesc, onAdd }) => {
    if (!show) return null;
    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="card-glass w-full max-w-md">
                <h3 className="text-lg font-orbitron text-white mb-5">Add New Module</h3>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Module Title <span className="text-red-400">*</span></label>
                        <input
                            type="text"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && title.trim() && onAdd()}
                            className="input-cyber"
                            placeholder="e.g. Introduction to Thermodynamics"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Description (Optional)</label>
                        <textarea
                            value={desc}
                            onChange={e => setDesc(e.target.value)}
                            className="input-cyber h-20 resize-none"
                            placeholder="Brief summary of what this module covers..."
                        />
                    </div>
                </div>

                <div className="flex gap-3 mt-6">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2 rounded border border-gray-600 text-gray-400 hover:bg-white/5 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onAdd}
                        disabled={!title.trim()}
                        className="flex-1 btn-neon disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Add Module
                    </button>
                </div>
            </div>
        </div>
    );
};

export default OrgCourseEditor;

/* ─── Certificate Template Editor Modal ─── */
const CertificateEditorModal = ({ template, setTemplate, onSave, saving, onClose, courseId, onLogoUpload, onBgUpload }) => {
    const t = template;
    const courseName = 'Sample Course Name';
    const studentName = 'John Doe';

    return (
        <div className="fixed inset-0 z-50 bg-black/90 flex backdrop-blur-sm animate-in fade-in">
            {/* Sidebar Controls */}
            <div className="w-96 bg-deep-space/95 border-r border-white/10 overflow-y-auto p-6 space-y-5 shrink-0">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-orbitron text-white flex items-center gap-2"><Award size={20} className="text-yellow-400" /> Certificate Editor</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={20} /></button>
                </div>

                <p className="text-xs text-gray-500">Customize how the certificate looks for students who complete this course.</p>

                {/* Text Fields */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Title Text</label>
                    <input
                        value={t.title_text}
                        onChange={e => setTemplate({ ...t, title_text: e.target.value })}
                        className="input-cyber text-sm"
                    />
                </div>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Body Text <span className="text-gray-600">(appears after student name)</span></label>
                    <input
                        value={t.body_text}
                        onChange={e => setTemplate({ ...t, body_text: e.target.value })}
                        className="input-cyber text-sm"
                    />
                </div>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Signature / Issued By</label>
                    <input
                        value={t.signature_text}
                        onChange={e => setTemplate({ ...t, signature_text: e.target.value })}
                        className="input-cyber text-sm"
                        placeholder="Director of Education"
                    />
                </div>

                {/* Colors */}
                <div className="grid grid-cols-3 gap-3">
                    <div>
                        <label className="block text-xs text-gray-400 mb-1">Background</label>
                        <div className="flex items-center gap-2">
                            <input type="color" value={t.bg_color} onChange={e => setTemplate({ ...t, bg_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer bg-transparent border border-white/20" />
                            <span className="text-xs text-gray-500 font-mono">{t.bg_color}</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs text-gray-400 mb-1">Text</label>
                        <div className="flex items-center gap-2">
                            <input type="color" value={t.text_color} onChange={e => setTemplate({ ...t, text_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer bg-transparent border border-white/20" />
                            <span className="text-xs text-gray-500 font-mono">{t.text_color}</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs text-gray-400 mb-1">Accent</label>
                        <div className="flex items-center gap-2">
                            <input type="color" value={t.accent_color} onChange={e => setTemplate({ ...t, accent_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer bg-transparent border border-white/20" />
                            <span className="text-xs text-gray-500 font-mono">{t.accent_color}</span>
                        </div>
                    </div>
                </div>

                {/* Font Style */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Font Style</label>
                    <select
                        value={t.font_style}
                        onChange={e => setTemplate({ ...t, font_style: e.target.value })}
                        className="input-cyber text-sm bg-deep-space"
                    >
                        <option value="Orbitron">Orbitron (Default)</option>
                        <option value="Rajdhani">Rajdhani</option>
                        <option value="serif">Classic Serif</option>
                        <option value="sans-serif">Sans Serif</option>
                        <option value="Georgia">Georgia</option>
                    </select>
                </div>

                {/* Logo Upload */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Organization Logo</label>
                    <div className="flex items-center gap-3">
                        {t.logo_url && <img src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${t.logo_url}`} alt="Logo" className="w-12 h-12 object-contain rounded border border-white/10 bg-white/5" />}
                        <label className="cursor-pointer text-xs text-neon-blue border border-neon-blue/30 rounded px-3 py-1.5 hover:bg-neon-blue/10 transition-colors flex items-center gap-1">
                            <Upload size={12} /> {t.logo_url ? 'Change' : 'Upload Logo'}
                            <input type="file" accept="image/*" className="hidden" onChange={onLogoUpload} />
                        </label>
                    </div>
                </div>

                {/* Custom Background */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Custom Background Image <span className="text-gray-600">(replaces solid color)</span></label>
                    <div className="flex items-center gap-3">
                        {t.custom_bg_url && <img src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${t.custom_bg_url}`} alt="BG" className="w-16 h-10 object-cover rounded border border-white/10" />}
                        <label className="cursor-pointer text-xs text-purple-400 border border-purple-400/30 rounded px-3 py-1.5 hover:bg-purple-400/10 transition-colors flex items-center gap-1">
                            <ImagePlus size={12} /> {t.custom_bg_url ? 'Change' : 'Upload Background'}
                            <input type="file" accept="image/*" className="hidden" onChange={onBgUpload} />
                        </label>
                        {t.custom_bg_url && (
                            <button onClick={() => setTemplate({ ...t, custom_bg_url: null })} className="text-xs text-red-400 hover:text-red-300">Remove</button>
                        )}
                    </div>
                </div>

                {/* Save Button */}
                <button
                    onClick={onSave}
                    disabled={saving}
                    className="w-full btn-neon flex items-center justify-center gap-2 disabled:opacity-50"
                >
                    {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                    {saving ? 'Saving...' : 'Save Template'}
                </button>

                <p className="text-[10px] text-gray-600 text-center">All certificates include an EduCore watermark</p>
            </div>

            {/* Live Preview */}
            <div className="flex-1 flex items-center justify-center p-8 overflow-auto">
                <div
                    style={{
                        width: 900,
                        height: 636,
                        backgroundColor: t.custom_bg_url ? 'transparent' : t.bg_color,
                        backgroundImage: t.custom_bg_url ? `url(http://localhost:8000${t.custom_bg_url})` : 'none',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        color: t.text_color,
                        fontFamily: t.font_style === 'Orbitron' ? '"Orbitron", sans-serif' : t.font_style === 'Rajdhani' ? '"Rajdhani", sans-serif' : t.font_style,
                        position: 'relative',
                        overflow: 'hidden',
                    }}
                    className="rounded-xl shadow-2xl border border-white/10"
                >
                    {/* Decorative Border */}
                    <div style={{ position: 'absolute', inset: 12, border: `2px solid ${t.accent_color}40`, borderRadius: 12 }} />
                    <div style={{ position: 'absolute', inset: 16, border: `1px solid ${t.accent_color}20`, borderRadius: 10 }} />

                    {/* EduCore Watermark */}
                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%) rotate(-30deg)',
                        fontSize: 80,
                        fontWeight: 900,
                        opacity: 0.04,
                        letterSpacing: 16,
                        whiteSpace: 'nowrap',
                        fontFamily: '"Orbitron", sans-serif',
                        pointerEvents: 'none',
                    }}>
                        EDUCORE
                    </div>

                    {/* Corner Accents */}
                    <div style={{ position: 'absolute', top: 20, left: 20, width: 40, height: 40, borderTop: `3px solid ${t.accent_color}`, borderLeft: `3px solid ${t.accent_color}` }} />
                    <div style={{ position: 'absolute', top: 20, right: 20, width: 40, height: 40, borderTop: `3px solid ${t.accent_color}`, borderRight: `3px solid ${t.accent_color}` }} />
                    <div style={{ position: 'absolute', bottom: 20, left: 20, width: 40, height: 40, borderBottom: `3px solid ${t.accent_color}`, borderLeft: `3px solid ${t.accent_color}` }} />
                    <div style={{ position: 'absolute', bottom: 20, right: 20, width: 40, height: 40, borderBottom: `3px solid ${t.accent_color}`, borderRight: `3px solid ${t.accent_color}` }} />

                    {/* Content */}
                    <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 48 }}>
                        {/* Logo */}
                        {t.logo_url && (
                            <img src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${t.logo_url}`} alt="Logo" style={{ width: 64, height: 64, objectFit: 'contain', marginBottom: 12 }} />
                        )}

                        {/* Award Icon */}
                        <div style={{ fontSize: 40, marginBottom: 8 }}>🏆</div>

                        {/* Title */}
                        <h1 style={{ fontSize: 32, fontWeight: 800, color: t.accent_color, letterSpacing: 4, textTransform: 'uppercase', marginBottom: 24, textAlign: 'center' }}>
                            {t.title_text}
                        </h1>

                        <p style={{ fontSize: 14, opacity: 0.6, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>This certifies that</p>

                        {/* Student Name */}
                        <h2 style={{ fontSize: 36, fontWeight: 700, borderBottom: `2px solid ${t.accent_color}`, paddingBottom: 8, marginBottom: 16, letterSpacing: 2 }}>
                            {studentName}
                        </h2>

                        <p style={{ fontSize: 16, opacity: 0.8, marginBottom: 8, textAlign: 'center' }}>{t.body_text}</p>

                        {/* Course Name */}
                        <h3 style={{ fontSize: 22, fontWeight: 700, color: t.accent_color, marginBottom: 32, textAlign: 'center' }}>
                            "{courseName}"
                        </h3>

                        {/* Bottom Row */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', maxWidth: 600, alignItems: 'flex-end' }}>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ width: 140, borderTop: `1px solid ${t.accent_color}60`, paddingTop: 8, fontSize: 11, opacity: 0.6 }}>Date</div>
                                <div style={{ fontSize: 12, marginTop: 4, opacity: 0.8 }}>Feb 19, 2026</div>
                            </div>
                            <div style={{ fontSize: 10, opacity: 0.3, fontFamily: 'monospace' }}>ID: EDUCORE-AB12CD34</div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ width: 140, borderTop: `1px solid ${t.accent_color}60`, paddingTop: 8, fontSize: 11, opacity: 0.6 }}>
                                    {t.signature_text || 'Authorized Signatory'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

/* ─── Exam Config Modal ─── */
const ExamConfigModal = ({ config, setConfig, onSave, saving, onClose }) => {
    const [activeTab, setActiveTab] = useState('settings'); // settings, questions

    const addQuestion = () => {
        const newQ = {
            id: Date.now().toString(),
            type: 'mcq',
            question: '',
            options: ['Option 1', 'Option 2'],
            correct_answers: [0],
            points: 1
        };
        setConfig({ ...config, questions: [...config.questions, newQ] });
    };

    const updateQuestion = (idx, field, value) => {
        const newQs = [...config.questions];
        newQs[idx] = { ...newQs[idx], [field]: value };
        setConfig({ ...config, questions: newQs });
    };

    const removeQuestion = (idx) => {
        const newQs = config.questions.filter((_, i) => i !== idx);
        setConfig({ ...config, questions: newQs });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col backdrop-blur-sm animate-in fade-in p-8">
            <div className="bg-deep-space/95 border border-white/10 rounded-xl flex flex-col w-full max-w-5xl mx-auto h-full overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-red-500/20 rounded-lg text-red-400"><FileText size={24} /></div>
                        <div>
                            <h2 className="text-xl font-orbitron text-white">Final Exam Configuration</h2>
                            <p className="text-xs text-gray-400">Configure questions and strict proctoring rules</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={onClose} className="text-gray-400 hover:text-white px-3 py-1">Cancel</button>
                        <button onClick={onSave} disabled={saving} className="btn-neon bg-red-500/20 border-red-500 text-red-400 hover:bg-red-500/30 flex items-center gap-2">
                            {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />} Save Exam
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-white/10">
                    <button onClick={() => setActiveTab('settings')} className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'settings' ? 'bg-white/5 text-white border-b-2 border-red-500' : 'text-gray-400 hover:text-white'}`}>
                        General Settings
                    </button>
                    <button onClick={() => setActiveTab('questions')} className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'questions' ? 'bg-white/5 text-white border-b-2 border-red-500' : 'text-gray-400 hover:text-white'}`}>
                        Questions ({config.questions.length})
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-black/20">
                    {activeTab === 'settings' ? (
                        <div className="max-w-2xl mx-auto space-y-6">
                            <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
                                <div>
                                    <h3 className="text-white font-medium">Enable Exam</h3>
                                    <p className="text-xs text-gray-400">Students must pass this exam to get a certificate</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={config.enabled} onChange={e => setConfig({ ...config, enabled: e.target.checked })} />
                                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-500"></div>
                                </label>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Pass Score (%)</label>
                                    <input
                                        type="number"
                                        value={config.passing_score}
                                        onChange={e => setConfig({ ...config, passing_score: parseInt(e.target.value) })}
                                        className="input-cyber w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Time Limit (mins)</label>
                                    <input
                                        type="number"
                                        value={config.time_limit_minutes}
                                        onChange={e => setConfig({ ...config, time_limit_minutes: parseInt(e.target.value) })}
                                        className="input-cyber w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Max Attempts</label>
                                    <input
                                        type="number"
                                        value={config.max_attempts}
                                        onChange={e => setConfig({ ...config, max_attempts: parseInt(e.target.value) })}
                                        className="input-cyber w-full"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Exam Title</label>
                                <input
                                    value={config.title}
                                    onChange={e => setConfig({ ...config, title: e.target.value })}
                                    className="input-cyber w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Instructions</label>
                                <textarea
                                    value={config.description}
                                    onChange={e => setConfig({ ...config, description: e.target.value })}
                                    className="input-cyber w-full h-32"
                                />
                            </div>

                            <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-3">
                                <AlertTriangle className="text-yellow-500 shrink-0" size={20} />
                                <div>
                                    <h4 className="text-yellow-500 text-sm font-bold mb-1">Strict Proctoring Enabled</h4>
                                    <p className="text-xs text-yellow-200/80">
                                        This exam will automatically enforce AI-based eye tracking, voice detection, fullscreen mode, and tab-switch prevention.
                                        Students will need a webcam and microphone to take it.
                                    </p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto space-y-6">
                            {config.questions.map((q, idx) => (
                                <div key={q.id} className="bg-white/5 border border-white/10 rounded-lg p-5 relative group">
                                    <button onClick={() => removeQuestion(idx)} className="absolute top-4 right-4 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Trash2 size={18} />
                                    </button>

                                    <div className="flex gap-4 mb-4">
                                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-gray-400 font-mono font-bold shrink-0">
                                            {idx + 1}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex gap-4 mb-3">
                                                <select
                                                    value={q.type}
                                                    onChange={e => updateQuestion(idx, 'type', e.target.value)}
                                                    className="bg-black/40 border border-white/10 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-red-500/50"
                                                >
                                                    <option value="mcq">Multiple Choice (Single)</option>
                                                    <option value="msq">Multiple Select</option>
                                                    <option value="tf">True / False</option>
                                                    <option value="text">Text Answer</option>
                                                </select>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-500">Points:</span>
                                                    <input
                                                        type="number"
                                                        value={q.points}
                                                        onChange={e => updateQuestion(idx, 'points', parseInt(e.target.value))}
                                                        className="w-16 bg-black/40 border border-white/10 rounded px-2 py-1 text-sm text-gray-300"
                                                    />
                                                </div>
                                            </div>
                                            <input
                                                value={q.question}
                                                onChange={e => updateQuestion(idx, 'question', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-700 text-lg font-medium text-white focus:outline-none focus:border-red-500/50 placeholder-gray-600 mb-4"
                                                placeholder="Enter question text..."
                                            />

                                            {/* Options Logic */}
                                            {q.type !== 'text' && (
                                                <div className="space-y-2 pl-2 border-l-2 border-white/5">
                                                    {q.type === 'tf' ? (
                                                        // True/False Options (Fixed)
                                                        ['True', 'False'].map((opt, oIdx) => (
                                                            <div key={opt} className={`flex items-center gap-3 p-2 rounded cursor-pointer ${q.correct_answers.includes(oIdx) ? 'bg-green-500/10 border border-green-500/30' : 'hover:bg-white/5 border border-transparent'}`}
                                                                onClick={() => {
                                                                    // Toggle correct
                                                                    updateQuestion(idx, 'correct_answers', [oIdx]);
                                                                }}
                                                            >
                                                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${q.correct_answers.includes(oIdx) ? 'border-green-500 bg-green-500' : 'border-gray-500'}`}>
                                                                    {q.correct_answers.includes(oIdx) && <Check size={10} className="text-black" />}
                                                                </div>
                                                                <span className="text-sm text-gray-300">{opt}</span>
                                                            </div>
                                                        ))
                                                    ) : (
                                                        // MCQ/MSQ Options (Dynamic)
                                                        <>
                                                            {q.options.map((opt, oIdx) => (
                                                                <div key={oIdx} className="flex items-center gap-3">
                                                                    <button
                                                                        onClick={() => {
                                                                            let newCorrect = [...q.correct_answers];
                                                                            if (q.type === 'mcq') {
                                                                                newCorrect = [oIdx];
                                                                            } else {
                                                                                if (newCorrect.includes(oIdx)) newCorrect = newCorrect.filter(i => i !== oIdx);
                                                                                else newCorrect.push(oIdx);
                                                                            }
                                                                            updateQuestion(idx, 'correct_answers', newCorrect);
                                                                        }}
                                                                        className={`w-5 h-5 rounded flex items-center justify-center border transition-colors ${q.correct_answers.includes(oIdx) ? 'bg-green-500 border-green-500 text-black' : 'border-gray-600 text-transparent hover:border-gray-400'}`}
                                                                    >
                                                                        <Check size={14} strokeWidth={3} />
                                                                    </button>
                                                                    <input
                                                                        value={opt}
                                                                        onChange={e => {
                                                                            const newOpts = [...q.options];
                                                                            newOpts[oIdx] = e.target.value;
                                                                            updateQuestion(idx, 'options', newOpts);
                                                                        }}
                                                                        className="flex-1 bg-black/20 border border-white/10 rounded px-3 py-1.5 text-sm text-gray-300 focus:border-red-500/30 outline-none"
                                                                        placeholder={`Option ${oIdx + 1}`}
                                                                    />
                                                                    <button onClick={() => {
                                                                        const newOpts = q.options.filter((_, i) => i !== oIdx);
                                                                        // Adjust correct answers indices if needed (complex, simplified here for MVP or just reset correct)
                                                                        updateQuestion(idx, 'options', newOpts);
                                                                        updateQuestion(idx, 'correct_answers', []); // Reset correct for safety
                                                                    }} className="text-gray-600 hover:text-red-400"><X size={14} /></button>
                                                                </div>
                                                            ))}
                                                            <button
                                                                onClick={() => updateQuestion(idx, 'options', [...q.options, `Option ${q.options.length + 1}`])}
                                                                className="text-xs text-neon-blue hover:text-white flex items-center gap-1 mt-2 ml-8"
                                                            >
                                                                <Plus size={12} /> Add Option
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}

                            <button onClick={addQuestion} className="w-full py-4 border-2 border-dashed border-gray-700 rounded-xl text-gray-500 hover:border-gray-500 hover:text-gray-300 flex items-center justify-center gap-2 transition-colors">
                                <Plus size={20} /> Add New Question
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// --- Access Keys Modal ---
const AccessKeysModal = ({ keys, loading, generating, keyCount, setKeyCount, onGenerate, onClose }) => {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="card-glass w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="p-4 border-b border-white/10 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Key className="text-purple-400" />
                        <h3 className="text-lg font-orbitron text-white">Course Access Keys</h3>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-4 border-b border-white/10 flex gap-4 bg-black/20">
                    <div className="flex-1">
                        <p className="text-sm text-gray-400 mb-2">Generate new keys for offline sales. Students use these to enroll without online payment.</p>
                        <div className="flex gap-2">
                            <input
                                type="number"
                                min="1"
                                max="100"
                                value={keyCount}
                                onChange={e => setKeyCount(parseInt(e.target.value) || 1)}
                                className="input-cyber w-24"
                                placeholder="Count"
                            />
                            <button
                                onClick={onGenerate}
                                disabled={generating}
                                className="btn-neon bg-purple-500/20 border-purple-500 text-purple-400 hover:bg-purple-500/30 flex-1 flex justify-center items-center gap-2"
                            >
                                {generating ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
                                Generate {keyCount} {keyCount === 1 ? 'Key' : 'Keys'}
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {loading ? (
                        <div className="flex justify-center p-8"><Loader2 className="animate-spin text-neon-blue" /></div>
                    ) : keys.length === 0 ? (
                        <div className="text-center p-8 text-gray-500">No keys generated yet.</div>
                    ) : (
                        keys.map(k => (
                            <div key={k.key} className="flex items-center justify-between p-3 rounded-lg border border-white/10 bg-black/40">
                                <div className="font-mono text-neon-blue tracking-wider">{k.key}</div>
                                <div className="text-right flex items-center gap-4">
                                    {k.is_used ? (
                                        <div className="flex items-center gap-1 text-xs text-red-400">
                                            <span>Used by:</span>
                                            <span className="font-bold text-white">{k.used_by_student_name}</span>
                                        </div>
                                    ) : (
                                        <span className="text-xs text-green-400 px-2 py-1 bg-green-500/10 rounded">Available</span>
                                    )}
                                    <button
                                        onClick={() => { navigator.clipboard.writeText(k.key); alert('Copied to clipboard!'); }}
                                        className="text-gray-400 hover:text-white"
                                        title="Copy Key"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

// removed duplicate export

