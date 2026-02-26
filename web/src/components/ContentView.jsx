import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, BookOpen, Video, PenTool, ChevronLeft, ChevronRight } from 'lucide-react';
import ChapterNotes from './ChapterNotes';

const ContentView = ({ courseId, chapterId, chapter }) => {
    const [content, setContent] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('read'); // read, video, quiz
    const [slideIndex, setSlideIndex] = useState(0);

    // When chapter changes, reset state
    useEffect(() => {
        setContent(null);
        setLoading(false);
        setActiveTab('read');
        setSlideIndex(0);

        // Check if content already exists in chapter object passed from parent
        if (chapter.content_markdown) {
            // We have content, but the backend structure for 'content' in generate response includes quiz_json too.
            // The RoadmapView passes 'chapter' from get_course_details which has content_markdown.
            // Ideally we should use that, but we might need quiz data which is not in the simple chapter list response?
            // Let's check main.py: get_course_details returns chapters with content_markdown. Quiz is NOT in the list response.

            // So we might need to fetch full chapter details or just hit generate again (which returns existing if present)
            // Hitting generate is safer to get quiz data.
            fetchContent();
        } else {
            // No content, fetch it
            fetchContent();
        }
    }, [chapterId]);

    const fetchContent = async () => {
        setLoading(true);
        try {
            const res = await axios.post(`http://localhost:8000/courses/${courseId}/chapters/${chapterId}/generate`);
            setContent(res.data);
        } catch (err) {
            console.error("Failed to load content", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-neon-blue">
                <Loader2 size={48} className="animate-spin mb-4" />
                <p className="text-xl font-orbitron animate-pulse">Agents Generating Content...</p>
                <p className="text-sm text-gray-500 mt-2">Accessing Knowledge Base • Synthesizing • Formatting</p>
            </div>
        );
    }

    if (!content) return null;

    // Render Logic
    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-black/20">
                <div>
                    <div className="text-neon-blue text-xs uppercase tracking-widest mb-1">Chapter {chapter.chapter_number}</div>
                    <h2 className="text-2xl font-orbitron text-white">{chapter.title}</h2>
                </div>

                {/* Tabs */}
                <div className="flex bg-deep-space/50 p-1 rounded-lg border border-white/10">
                    <button
                        onClick={() => setActiveTab('read')}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-semibold transition-all ${activeTab === 'read' ? 'bg-neon-blue text-deep-space shadow-glow' : 'text-gray-400 hover:text-white'}`}
                    >
                        <BookOpen size={16} /> Read
                    </button>
                    <button
                        onClick={() => setActiveTab('video')}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-semibold transition-all ${activeTab === 'video' ? 'bg-neon-purple text-white shadow-glow' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Video size={16} /> Watch
                    </button>
                    <button
                        onClick={() => setActiveTab('quiz')}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-semibold transition-all ${activeTab === 'quiz' ? 'bg-green-400 text-deep-space shadow-glow' : 'text-gray-400 hover:text-white'}`}
                    >
                        <PenTool size={16} /> Quiz
                    </button>
                </div>
            </div>

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-transparent to-black/20">

                {activeTab === 'read' && (
                    <SlideDeck content={content.content_markdown} index={slideIndex} setIndex={setSlideIndex} />
                )}

                {activeTab === 'video' && (
                    <VideoPlayer topic={chapter.title} content={content.content_markdown} />
                )}

                {activeTab === 'quiz' && (
                    <QuizInterface
                        courseId={courseId}
                        chapterId={chapterId}
                        quizData={content.quiz}
                    />
                )}

                {/* Chapter Notes Section */}
                <ChapterNotes courseId={courseId} chapterId={chapterId} />

            </div>
        </div>
    );
};

// Sub-components

const SlideDeck = ({ content, index, setIndex }) => {
    // Parse markdown into slides by '## '
    const slides = content.split('## ').filter(s => s.trim().length > 0).map(s => {
        const lines = s.trim().split('\n');
        return {
            title: lines[0],
            body: lines.slice(1).join('\n')
        };
    });

    const currentSlide = slides[index] || { title: "Intro", body: content };

    return (
        <div className="h-full flex flex-col max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-4">
                <button
                    disabled={index === 0}
                    onClick={() => setIndex(i => i - 1)}
                    className="p-2 rounded-full border border-white/20 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <ChevronLeft size={24} />
                </button>
                <span className="text-gray-400 text-sm">Slide {index + 1} / {slides.length}</span>
                <button
                    disabled={index === slides.length - 1}
                    onClick={() => setIndex(i => i + 1)}
                    className="p-2 rounded-full border border-white/20 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <ChevronRight size={24} />
                </button>
            </div>

            {/* Slide Card */}
            <div className="flex-1 bg-deep-space border border-neon-blue/20 rounded-xl p-8 md:p-12 shadow-2xl relative overflow-hidden flex flex-col justify-center min-h-[500px]">
                {/* Decorative */}
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-neon-blue to-neon-purple"></div>

                <h2 className="text-3xl md:text-4xl font-orbitron text-neon-blue mb-8 text-center">{currentSlide.title}</h2>

                <div className="prose prose-invert prose-lg max-w-none text-gray-200 leading-relaxed whitespace-pre-wrap">
                    {currentSlide.body}
                </div>
            </div>
        </div>
    );
};

const VideoPlayer = ({ topic, content }) => {
    const [videoUrl, setVideoUrl] = useState(null);
    const [generating, setGenerating] = useState(false);

    const generateVideo = async () => {
        setGenerating(true);
        try {
            const res = await axios.post('http://localhost:8000/generate/video', {
                topic,
                content_markdown: content, // sending full markdown
                chapter_title: topic
            });
            setVideoUrl("http://localhost:8000" + res.data.video_url);
        } catch (err) {
            alert("Video generation failed");
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-full">
            {videoUrl ? (
                <div className="w-full max-w-4xl aspect-video bg-black rounded-lg overflow-hidden border border-neon-purple shadow-[0_0_30px_rgba(188,19,254,0.3)]">
                    <video src={videoUrl} controls className="w-full h-full" autoPlay />
                </div>
            ) : (
                <div className="text-center p-12 border border-dashed border-white/20 rounded-xl bg-white/5">
                    <Video size={48} className="mx-auto text-neon-purple mb-4" />
                    <h3 className="text-xl mb-2">Video Lecture Unavailable</h3>
                    <p className="text-gray-400 mb-6">Generate an AI-narrated video summary of this chapter.</p>
                    <button
                        onClick={generateVideo}
                        disabled={generating}
                        className="btn-neon"
                    >
                        {generating ? "Synthesizing Video..." : "Generate Video Agent"}
                    </button>
                </div>
            )}
        </div>
    );
};

const QuizInterface = ({ courseId, chapterId, quizData }) => {
    const [answers, setAnswers] = useState({}); // { 0: "Option A" }
    const [submitted, setSubmitted] = useState(false);
    const [score, setScore] = useState(null);
    const [loading, setLoading] = useState(false);

    // Check existing result
    useEffect(() => {
        const fetchResult = async () => {
            try {
                const res = await axios.get(`http://localhost:8000/quizzes/${chapterId}/result`);
                if (res.data) {
                    setScore(res.data.score);
                    setSubmitted(true);
                }
            } catch (err) {
                // Ignore 404
            }
        };
        fetchResult();
    }, [chapterId]);

    const handleSubmit = async () => {
        if (Object.keys(answers).length < quizData.length) {
            alert("Please answer all questions");
            return;
        }

        setLoading(true);
        try {
            const payload = {
                chapter_id: chapterId,
                course_id: courseId,
                answers: answers
            };
            const res = await axios.post('http://localhost:8000/quizzes/submit', payload);
            setScore(res.data.score);
            setSubmitted(true);
        } catch (err) {
            alert(err.response?.data?.detail || "Submission failed");
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="flex flex-col items-center justify-center h-full">
                <div className="card-glass p-12 text-center border-neon-green">
                    <h2 className="text-3xl font-orbitron text-green-400 mb-2">Quiz Complete! 🏆</h2>
                    <div className="text-6xl font-bold my-6">{score} <span className="text-2xl text-gray-400">/ {quizData.length}</span></div>
                    <p className="text-gray-400">Score recorded on blockchain (simulated).</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-8 pb-12">
            {quizData.map((q, i) => (
                <div key={i} className="card-glass p-6">
                    <h3 className="text-lg font-semibold mb-4 text-white">
                        <span className="text-neon-blue mr-2">Q{i + 1}.</span>
                        {q.question}
                    </h3>
                    <div className="space-y-3">
                        {q.options.map((opt, optIdx) => (
                            <label
                                key={optIdx}
                                className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${answers[i] === opt
                                    ? 'bg-neon-blue/20 border-neon-blue text-white'
                                    : 'bg-black/20 border-white/5 hover:bg-white/5'
                                    }`}
                            >
                                <input
                                    type="radio"
                                    name={`q-${i}`}
                                    className="hidden"
                                    checked={answers[i] === opt}
                                    onChange={() => setAnswers(prev => ({ ...prev, [i]: opt }))}
                                />
                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${answers[i] === opt ? 'border-neon-blue' : 'border-gray-500'
                                    }`}>
                                    {answers[i] === opt && <div className="w-2 h-2 bg-neon-blue rounded-full"></div>}
                                </div>
                                <span className={answers[i] === opt ? 'text-neon-blue' : 'text-gray-300'}>{opt}</span>
                            </label>
                        ))}
                    </div>
                </div>
            ))}

            <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full btn-neon py-4 text-xl"
            >
                {loading ? "Submitting..." : "Submit Assessment"}
            </button>
        </div>
    );
};

export default ContentView;
