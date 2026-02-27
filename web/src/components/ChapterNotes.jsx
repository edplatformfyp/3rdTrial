import { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, StickyNote, PenTool, Type, Trash2, X, Loader2 } from 'lucide-react';
import CanvasEditor from './CanvasEditor';

const ChapterNotes = ({ courseId, chapterId }) => {
    const [notes, setNotes] = useState([]);
    const [isCreating, setIsCreating] = useState(false);
    const [noteType, setNoteType] = useState('text'); // 'text' | 'sketch'
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [sketchData, setSketchData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showSketchEditor, setShowSketchEditor] = useState(false);

    useEffect(() => {
        if (chapterId) {
            fetchNotes();
        }
    }, [chapterId]);

    const fetchNotes = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notes?chapter_id=${chapterId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNotes(res.data);
        } catch (err) {
            console.error("Failed to fetch notes", err);
        }
    };

    const handleSaveNote = async () => {
        if (!title.trim()) {
            alert("Please enter a title for your note.");
            return;
        }

        if (noteType === 'text' && !content.trim()) {
            alert("Please enter some content.");
            return;
        }

        if (noteType === 'sketch' && !sketchData) {
            alert("Please create a sketch.");
            return;
        }

        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const payload = {
                title,
                content: noteType === 'text' ? content : "Sketch Note",
                course_id: courseId,
                chapter_id: chapterId,
                note_type: noteType,
                metadata: noteType === 'sketch' ? { snapshot: sketchData } : null
            };

            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notes`, payload, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Reset Form
            setIsCreating(false);
            setTitle('');
            setContent('');
            setSketchData(null);
            setNoteType('text');
            fetchNotes(); // Refresh list

        } catch (err) {
            console.error("Failed to save note", err);
            alert("Failed to save note. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteNote = async (noteId) => {
        if (!confirm("Are you sure you want to delete this note?")) return;

        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notes/${noteId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNotes(notes.filter(n => n.id !== noteId));
        } catch (err) {
            console.error("Failed to delete note", err);
        }
    };

    return (
        <div className="mt-8 border-t border-neon-blue/20 pt-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-orbitron text-white flex items-center gap-2">
                    <StickyNote className="text-neon-purple" />
                    Chapter Notes
                </h3>

                {!isCreating && (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="btn-neon text-sm px-4 py-2 flex items-center gap-2"
                    >
                        <Plus size={16} />
                        Add Note
                    </button>
                )}
            </div>

            {/* Creation Form */}
            {isCreating && (
                <div className="card-glass p-6 mb-8 border border-neon-blue/50 animate-in slide-in-from-top-4 duration-300">
                    <div className="flex justify-between items-start mb-4">
                        <h4 className="text-lg font-bold text-neon-blue">New Note</h4>
                        <button onClick={() => setIsCreating(false)} className="text-gray-400 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Title</label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full input-cyber bg-deep-space/50"
                                placeholder="Concept Summary..."
                            />
                        </div>

                        {/* Type Toggle */}
                        <div className="flex gap-4 border-b border-gray-700 pb-2">
                            <button
                                onClick={() => setNoteType('text')}
                                className={`flex items-center gap-2 pb-2 px-2 transition-colors border-b-2 ${noteType === 'text' ? 'border-neon-blue text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
                            >
                                <Type size={16} /> Text
                            </button>
                            <button
                                onClick={() => setNoteType('sketch')}
                                className={`flex items-center gap-2 pb-2 px-2 transition-colors border-b-2 ${noteType === 'sketch' ? 'border-neon-purple text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
                            >
                                <PenTool size={16} /> Sketch
                            </button>
                        </div>

                        {/* Content Input */}
                        {noteType === 'text' ? (
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                className="w-full h-32 input-cyber bg-deep-space/50 resize-none"
                                placeholder="Write your notes here..."
                            />
                        ) : (
                            <div className="h-32 bg-deep-space/30 border border-dashed border-gray-600 rounded-lg flex flex-col items-center justify-center gap-3">
                                {sketchData ? (
                                    <div className="text-green-400 flex items-center gap-2">
                                        <div className="w-3 h-3 bg-green-500 rounded-full" />
                                        Sketch Ready
                                    </div>
                                ) : (
                                    <span className="text-gray-500">No sketch created yet</span>
                                )}
                                <button
                                    onClick={() => setShowSketchEditor(true)}
                                    className="btn-neon border-neon-purple text-neon-purple hover:bg-neon-purple/10 text-sm"
                                >
                                    {sketchData ? 'Edit Sketch' : 'Open Canvas'}
                                </button>
                            </div>
                        )}

                        <div className="flex justify-end gap-3 pt-4">
                            <button
                                onClick={() => setIsCreating(false)}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveNote}
                                disabled={loading}
                                className="btn-neon px-6 py-2 flex items-center gap-2"
                            >
                                {loading ? <Loader2 className="animate-spin" size={16} /> : <SaveIcon />}
                                Save Note
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Notes List */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {notes.length === 0 && !isCreating ? (
                    <div className="col-span-2 text-center py-8 text-gray-500 border border-dashed border-gray-700 rounded-lg">
                        No notes for this chapter yet. Click "Add Note" to start.
                    </div>
                ) : (
                    notes.map(note => (
                        <div key={note.id} className="card-glass p-4 group hover:border-neon-blue/50 transition-all">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="font-bold text-white truncate pr-4">{note.title || "Untitled Note"}</h4>
                                <div className="flex gap-2">
                                    <span className={`text-xs px-2 py-0.5 rounded-full border ${note.note_type === 'sketch' ? 'border-neon-purple/30 text-neon-purple bg-neon-purple/5' : 'border-neon-blue/30 text-neon-blue bg-neon-blue/5'}`}>
                                        {note.note_type === 'sketch' ? 'SKETCH' : 'TEXT'}
                                    </span>
                                    <button
                                        onClick={() => handleDeleteNote(note.id)}
                                        className="text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            {note.note_type === 'text' ? (
                                <p className="text-sm text-gray-400 line-clamp-3 mb-2">{note.content}</p>
                            ) : (
                                <div className="h-20 bg-gray-900/50 rounded flex items-center justify-center mb-2 border border-gray-800">
                                    <span className="text-xs text-gray-500 italic">Sketch Data</span>
                                </div>
                            )}

                            <div className="text-xs text-gray-600 mt-2 pt-2 border-t border-gray-800">
                                {new Date(note.created_at).toLocaleDateString()}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Sketch Editor Modal */}
            {showSketchEditor && (
                <CanvasEditor
                    initialData={sketchData}
                    onSave={(data) => {
                        setSketchData(data);
                        setShowSketchEditor(false);
                    }}
                    onClose={() => setShowSketchEditor(false)}
                />
            )}
        </div>
    );
};

const SaveIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" /></svg>
);

export default ChapterNotes;
