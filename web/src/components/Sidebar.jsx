import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { BookOpen, PlusCircle, Trash2, ChevronRight, Loader2, User, StickyNote, ShoppingBag, Settings } from 'lucide-react';

const Sidebar = ({ onSelectCourse, selectedCourseId, onViewChange, onToggle, viewMode }) => {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [collapsed, setCollapsed] = useState(false);
    const navigate = useNavigate();

    const fetchCourses = async () => {
        try {
            const res = await axios.get('http://localhost:8000/courses');
            setCourses(res.data);
        } catch (err) {
            console.error("Failed to fetch courses", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCourses();
    }, []);

    const toggleSidebar = () => {
        const newState = !collapsed;
        setCollapsed(newState);
        onToggle(newState);
    };

    const handleDelete = async (e, courseId) => {
        e.stopPropagation();
        if (!window.confirm("Delete this course?")) return;

        try {
            await axios.delete(`http://localhost:8000/courses/${courseId}`);
            // Refresh list
            fetchCourses();
            // If selected was deleted, clear selection
            if (selectedCourseId === courseId) {
                onSelectCourse(null);
                onViewChange('new');
            }
        } catch (err) {
            alert("Failed to delete course");
        }
    };

    return (
        <aside className={`${collapsed ? 'w-20' : 'w-64'} bg-deep-space/95 border-l border-neon-blue/30 backdrop-blur-xl h-screen fixed right-0 top-0 overflow-y-auto z-20 transition-all duration-300 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]`}>

            {/* Toggle Button */}
            <button
                onClick={toggleSidebar}
                className="absolute left-0 top-8 -translate-x-full bg-deep-space border border-neon-blue/50 border-r-0 rounded-l-lg p-2 text-neon-blue hover:text-white hover:bg-neon-blue/20 transition-colors shadow-[-5px_0_15px_rgba(0,243,255,0.2)]"
            >
                <ChevronRight size={20} className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
            </button>

            <div className={`h-20 flex items-center border-b border-neon-blue/30 ${collapsed ? 'justify-center' : 'px-6'}`}>
                <div className="flex items-center gap-3">
                    <BookOpen className="text-neon-blue shrink-0" size={24} />
                    <span className={`text-xl font-orbitron text-white whitespace-nowrap overflow-hidden transition-all duration-300 ${collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
                        LIBRARY
                    </span>
                </div>
            </div>

            <nav className="p-3 space-y-3">
                <MenuButton
                    icon={<PlusCircle size={22} />}
                    label="New Module"
                    collapsed={collapsed}
                    active={!selectedCourseId && viewMode === 'new'}
                    onClick={() => { onSelectCourse(null); onViewChange('new'); }}
                />

                <MenuButton
                    icon={<User size={22} />}
                    label="My Profile"
                    collapsed={collapsed}
                    active={viewMode === 'profile'}
                    onClick={() => { onSelectCourse(null); onViewChange('profile'); }}
                />

                <MenuButton
                    icon={<StickyNote size={22} />}
                    label="My Notes"
                    collapsed={collapsed}
                    active={viewMode === 'notes'}
                    onClick={() => { onSelectCourse(null); onViewChange('notes'); }}
                />

                <MenuButton
                    icon={<Settings size={22} />}
                    label="Settings"
                    collapsed={collapsed}
                    active={viewMode === 'settings'}
                    onClick={() => { onSelectCourse(null); onViewChange('settings'); }}
                />

                <MenuButton
                    icon={<ShoppingBag size={22} />}
                    label="Browse Courses"
                    collapsed={collapsed}
                    active={false}
                    onClick={() => navigate('/marketplace')}
                />

                <div className="py-4">
                    {collapsed ? (
                        <div className="h-[1px] w-8 bg-gray-700 mx-auto" />
                    ) : (
                        <div className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                            My Courses
                        </div>
                    )}
                </div>

                {loading ? (
                    <div className="flex justify-center p-4"><Loader2 className="animate-spin text-neon-purple" /></div>
                ) : (
                    courses.map(course => (
                        <div
                            key={course.id}
                            onClick={() => { onSelectCourse(course.id); onViewChange('course'); }}
                            className={`group relative w-full flex flex-col cursor-pointer transition-all duration-200 rounded-md mb-2
                                ${selectedCourseId === course.id
                                    ? 'bg-neon-purple/20 text-white border border-neon-purple/50 shadow-[0_0_10px_rgba(168,85,247,0.2)]'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                                }
                                ${collapsed ? 'justify-center p-3 items-center' : 'p-3'}
                            `}
                            title={collapsed ? `${course.topic} (${course.progress}%)` : ""}
                        >
                            <div className="flex items-center justify-between w-full mb-1">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    {collapsed ? (
                                        <div className="relative">
                                            {/* Circular Progress for Collapsed State */}
                                            <svg className="w-8 h-8 transform -rotate-90">
                                                <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="3" fill="transparent" className="text-gray-700" />
                                                <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="3" fill="transparent"
                                                    className={`${selectedCourseId === course.id ? 'text-neon-purple' : 'text-neon-blue'}`}
                                                    strokeDasharray={2 * Math.PI * 14}
                                                    strokeDashoffset={2 * Math.PI * 14 * (1 - (course.progress || 0) / 100)}
                                                />
                                            </svg>
                                            <div className={`absolute inset-0 m-auto w-2 h-2 rounded-full ${selectedCourseId === course.id ? 'bg-neon-purple' : 'bg-transparent'}`} />
                                        </div>
                                    ) : (
                                        <>
                                            <ChevronRight size={14} className={`transition-transform duration-200 ${selectedCourseId === course.id ? 'text-neon-purple translate-x-1' : 'opacity-0'}`} />
                                            <span className="truncate font-medium">{course.topic}</span>
                                        </>
                                    )}
                                </div>

                                {!collapsed && (
                                    <button
                                        onClick={(e) => handleDelete(e, course.id)}
                                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                )}
                            </div>

                            {/* Progress Bar (Expanded State) */}
                            {!collapsed && (
                                <div className="w-full mt-2 pl-6 pr-1">
                                    <div className="flex justify-between items-center text-[10px] text-gray-500 mb-1">
                                        <span>Progress</span>
                                        <span className={course.progress === 100 ? 'text-neon-green' : 'text-neon-blue'}>{course.progress || 0}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                        <div
                                            className={`h-full rounded-full transition-all duration-500 ${course.progress === 100 ? 'bg-neon-green shadow-[0_0_10px_#4ade80]' : 'bg-neon-blue shadow-[0_0_8px_#00f3ff]'}`}
                                            style={{ width: `${course.progress || 0}%` }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </nav>
        </aside>
    );
};

const MenuButton = ({ icon, label, collapsed, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center transition-all duration-200 rounded-md group
            ${active
                ? 'bg-neon-blue/20 text-white border border-neon-blue/50 shadow-[0_0_10px_rgba(0,243,255,0.2)]'
                : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
            }
            ${collapsed ? 'justify-center p-3' : 'p-3 gap-3'}
        `}
        title={collapsed ? label : ""}
    >
        <span className={`${active ? 'text-neon-blue' : 'text-gray-400 group-hover:text-white'}`}>{icon}</span>
        <span className={`whitespace-nowrap overflow-hidden transition-all duration-300 ${collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
            {label}
        </span>
    </button>
);

export default Sidebar;
