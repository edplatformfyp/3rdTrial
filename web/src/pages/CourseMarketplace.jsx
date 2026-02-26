import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import {
    ArrowLeft, Search, BookOpen, Users, GraduationCap,
    ShoppingCart, CheckCircle, Loader2, Star, Filter, X, Key
} from 'lucide-react';

const CourseMarketplace = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedGrade, setSelectedGrade] = useState('All');
    const [enrollingId, setEnrollingId] = useState(null);
    const [successId, setSuccessId] = useState(null);
    const [enrollModalCourse, setEnrollModalCourse] = useState(null);
    const [accessKey, setAccessKey] = useState('');

    useEffect(() => {
        fetchMarketplaceCourses();
    }, []);

    const fetchMarketplaceCourses = async () => {
        try {
            const res = await axios.get('http://localhost:8000/marketplace/courses');
            setCourses(res.data);
        } catch (err) {
            console.error('Failed to fetch marketplace courses', err);
        } finally {
            setLoading(false);
        }
    };

    const handleEnrollClick = (course) => {
        if (course.price && course.price > 0) {
            setEnrollModalCourse(course);
            setAccessKey('');
        } else {
            executeEnroll(course.id, null);
        }
    };

    const handleOnlinePayment = async () => {
        if (!enrollModalCourse) return;
        setEnrollingId(enrollModalCourse.id);
        try {
            const res = await axios.post('http://localhost:8000/marketplace/orders/create',
                { course_id: enrollModalCourse.id },
                { withCredentials: true }
            );

            navigate(`/checkout/${res.data.payment_session_id}`, {
                state: {
                    topic: enrollModalCourse.topic,
                    amount: enrollModalCourse.price,
                    order_id: res.data.order_id
                }
            });
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to initiate mock payment.');
            setEnrollingId(null);
        }
    };

    const executeEnroll = async (courseId, key) => {
        setEnrollingId(courseId);
        try {
            const payload = { course_id: courseId };
            if (key) payload.access_key = key;
            await axios.post('http://localhost:8000/marketplace/enroll', payload);
            setSuccessId(courseId);
            setEnrollModalCourse(null);
            // Update the course list to reflect enrollment
            setCourses(prev => prev.map(c =>
                c.id === courseId ? { ...c, is_enrolled: true } : c
            ));
            setTimeout(() => setSuccessId(null), 2000);
        } catch (err) {
            const msg = err.response?.data?.detail || 'Enrollment failed';
            alert(msg);
        } finally {
            setEnrollingId(null);
        }
    };

    // Get unique grades for filter
    const grades = ['All', ...new Set(courses.map(c => c.grade_level))];

    // Filter courses
    const filtered = courses.filter(c => {
        const matchSearch = c.topic.toLowerCase().includes(search.toLowerCase()) ||
            c.org_name.toLowerCase().includes(search.toLowerCase()) ||
            c.description.toLowerCase().includes(search.toLowerCase());
        const matchGrade = selectedGrade === 'All' || c.grade_level === selectedGrade;
        return matchSearch && matchGrade;
    });

    return (
        <div className="min-h-screen bg-deep-space text-gray-100 font-rajdhani">
            {/* Hero Banner */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-neon-blue/10 via-neon-purple/5 to-transparent" />
                <div className="absolute inset-0">
                    <div className="absolute top-20 left-20 w-72 h-72 bg-neon-blue/5 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-10 right-20 w-96 h-96 bg-neon-purple/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
                </div>

                <div className="relative max-w-7xl mx-auto px-6 py-8">
                    {/* Top Bar */}
                    <div className="flex items-center justify-between mb-8">
                        <button
                            onClick={() => navigate('/student')}
                            className="flex items-center gap-2 text-gray-400 hover:text-neon-blue transition-colors group"
                        >
                            <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                            <span className="text-sm">Back to Dashboard</span>
                        </button>
                        <div className="flex items-center gap-2 text-sm text-neon-purple font-mono border border-neon-purple/30 px-3 py-1 rounded-full bg-neon-purple/5">
                            <GraduationCap size={14} />
                            <span>{user?.username?.toUpperCase()}</span>
                        </div>
                    </div>

                    {/* Hero Content */}
                    <div className="text-center space-y-4 mb-10">
                        <h1 className="text-4xl md:text-5xl font-orbitron tracking-wider">
                            <span className="text-neon-blue">COURSE</span>{' '}
                            <span className="text-white">MARKETPLACE</span>
                        </h1>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            Explore premium courses from top organizations. Enroll and start learning today.
                        </p>
                    </div>

                    {/* Search & Filters */}
                    <div className="max-w-3xl mx-auto space-y-4">
                        <div className="relative">
                            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                            <input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Search courses, organizations..."
                                className="w-full pl-12 pr-10 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-neon-blue/50 backdrop-blur-sm transition-colors"
                            />
                            {search && (
                                <button
                                    onClick={() => setSearch('')}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                                >
                                    <X size={16} />
                                </button>
                            )}
                        </div>

                        <div className="flex items-center gap-2 flex-wrap">
                            <Filter size={14} className="text-gray-500" />
                            {grades.map(g => (
                                <button
                                    key={g}
                                    onClick={() => setSelectedGrade(g)}
                                    className={`px-3 py-1 rounded-full text-xs font-mono transition-all ${selectedGrade === g
                                        ? 'bg-neon-blue text-deep-space font-bold'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-white/10'
                                        }`}
                                >
                                    {g}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Course Grid */}
            <div className="max-w-7xl mx-auto px-6 pb-12">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 size={32} className="animate-spin text-neon-blue" />
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center py-20 space-y-3">
                        <BookOpen size={48} className="mx-auto text-gray-700" />
                        <p className="text-gray-500 text-lg">
                            {search || selectedGrade !== 'All'
                                ? 'No courses match your filters'
                                : 'No courses available yet'}
                        </p>
                        {(search || selectedGrade !== 'All') && (
                            <button
                                onClick={() => { setSearch(''); setSelectedGrade('All'); }}
                                className="text-neon-blue text-sm hover:underline"
                            >
                                Clear filters
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        <p className="text-sm text-gray-500 mb-6">
                            {filtered.length} course{filtered.length !== 1 ? 's' : ''} available
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filtered.map(course => (
                                <CourseCard
                                    key={course.id}
                                    course={course}
                                    onEnroll={handleEnrollClick}
                                    enrolling={enrollingId === course.id}
                                    justEnrolled={successId === course.id}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Access Key Modal for Paid Courses */}
            {enrollModalCourse && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
                    <div className="card-glass w-full max-w-md p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center gap-3">
                                <div className="p-3 bg-neon-purple/20 rounded-xl text-neon-purple">
                                    <ShoppingCart size={24} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-orbitron text-white">Enroll in Course</h3>
                                    <p className="text-xs text-gray-400">Payment required</p>
                                </div>
                            </div>
                            <button onClick={() => setEnrollModalCourse(null)} className="text-gray-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="mb-6 space-y-2 text-center bg-black/30 p-4 rounded-lg">
                            <p className="text-sm text-gray-300">
                                You are enrolling in <strong>{enrollModalCourse.topic}</strong>
                            </p>
                            <div className="text-3xl font-orbitron text-neon-green mt-2">
                                ₹{enrollModalCourse.price}
                            </div>
                        </div>

                        <div className="space-y-6">
                            {/* Option 1: Online Mock Payment */}
                            <div>
                                <button
                                    onClick={handleOnlinePayment}
                                    disabled={enrollingId === enrollModalCourse.id}
                                    className="w-full py-4 rounded-lg font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 bg-gradient-to-r from-neon-blue to-neon-purple text-white shadow-[0_0_15px_rgba(0,243,255,0.2)] hover:shadow-[0_0_25px_rgba(188,19,254,0.4)]"
                                >
                                    {enrollingId === enrollModalCourse.id ? <Loader2 className="animate-spin" size={20} /> : <ShoppingCart size={20} />}
                                    Pay Online Now
                                </button>
                            </div>

                            <div className="relative flex py-2 items-center">
                                <div className="flex-grow border-t border-white/10"></div>
                                <span className="flex-shrink-0 mx-4 text-gray-500 text-xs uppercase tracking-widest">Or</span>
                                <div className="flex-grow border-t border-white/10"></div>
                            </div>

                            {/* Option 2: Access Key Redemption */}
                            <div className="space-y-3">
                                <label className="text-xs text-neon-blue/80 px-1">Have an offline Access Key?</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={accessKey}
                                        onChange={e => setAccessKey(e.target.value)}
                                        placeholder="EDU-1234-ABCD"
                                        className="input-cyber uppercase font-mono tracking-wider flex-1"
                                        onKeyDown={e => e.key === 'Enter' && accessKey.trim() && executeEnroll(enrollModalCourse.id, accessKey)}
                                    />
                                    <button
                                        onClick={() => executeEnroll(enrollModalCourse.id, accessKey)}
                                        disabled={!accessKey.trim() || enrollingId === enrollModalCourse.id}
                                        className="px-4 py-2 rounded-lg bg-neon-purple/20 border border-neon-purple text-neon-purple hover:bg-neon-purple/30 flex justify-center items-center gap-2 disabled:opacity-50 transition-colors"
                                    >
                                        {enrollingId === enrollModalCourse.id ? <Loader2 className="animate-spin" size={16} /> : <Key size={16} />}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const CourseCard = ({ course, onEnroll, enrolling, justEnrolled }) => {
    const isFree = !course.price || course.price === 0;

    return (
        <div className="group relative bg-gradient-to-br from-white/[0.04] to-white/[0.01] border border-white/10 rounded-xl overflow-hidden hover:border-neon-blue/30 transition-all duration-300 hover:shadow-[0_0_30px_rgba(0,243,255,0.05)]">
            {/* Thumbnail / Gradient Header */}
            <div className="h-36 relative overflow-hidden">
                {course.thumbnail_url ? (
                    <img
                        src={`http://localhost:8000${course.thumbnail_url}`}
                        alt={course.topic}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-neon-blue/20 via-neon-purple/10 to-deep-space flex items-center justify-center">
                        <BookOpen size={40} className="text-neon-blue/30" />
                    </div>
                )}
                {/* Price Badge */}
                <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md ${isFree
                    ? 'bg-neon-green/20 text-neon-green border border-neon-green/30'
                    : 'bg-neon-purple/20 text-neon-purple border border-neon-purple/30'
                    }`}>
                    {isFree ? 'FREE' : `₹${course.price}`}
                </div>
                {/* Grade Badge */}
                <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/50 backdrop-blur-md text-xs text-gray-300 border border-white/10">
                    {course.grade_level}
                </div>
            </div>

            {/* Content */}
            <div className="p-5 space-y-3">
                <h3 className="text-lg font-bold text-white font-orbitron leading-tight line-clamp-2 group-hover:text-neon-blue transition-colors">
                    {course.topic}
                </h3>

                <p className="text-sm text-gray-400 line-clamp-2 leading-relaxed min-h-[2.5rem]">
                    {course.description || 'Explore this course to learn more.'}
                </p>

                {/* Meta */}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                        <Users size={12} />
                        <span>{course.org_name}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <BookOpen size={12} />
                        <span>{course.module_count} module{course.module_count !== 1 ? 's' : ''}</span>
                    </div>
                </div>

                {/* Action Button */}
                <div className="pt-2">
                    {course.is_enrolled ? (
                        <div className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-neon-green/10 text-neon-green border border-neon-green/20 text-sm font-bold">
                            <CheckCircle size={16} />
                            Enrolled
                        </div>
                    ) : justEnrolled ? (
                        <div className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-neon-green/20 text-neon-green text-sm font-bold animate-pulse">
                            <CheckCircle size={16} />
                            Successfully Enrolled!
                        </div>
                    ) : (
                        <button
                            onClick={() => onEnroll(course)}
                            disabled={enrolling}
                            className="w-full py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 bg-gradient-to-r from-neon-blue/20 to-neon-purple/20 text-white border border-neon-blue/30 hover:from-neon-blue/30 hover:to-neon-purple/30 hover:border-neon-blue/50 hover:shadow-[0_0_20px_rgba(0,243,255,0.1)]"
                        >
                            {enrolling ? (
                                <Loader2 size={16} className="animate-spin" />
                            ) : (
                                <ShoppingCart size={16} />
                            )}
                            {enrolling ? 'Enrolling...' : (isFree ? 'Enroll Free' : `Buy for ₹${course.price}`)}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CourseMarketplace;
