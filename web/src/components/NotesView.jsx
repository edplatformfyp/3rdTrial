import { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, Plus, StickyNote } from 'lucide-react';
import CanvasEditor from './CanvasEditor';

const NotesView = () => {
    const [notes, setNotes] = useState([]);
    const [newNote, setNewNote] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchNotes();
    }, []);

    const fetchNotes = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notes`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNotes(res.data);
        } catch (err) {
            console.error("Failed to fetch notes", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateNote = async () => {
        if (!newNote.trim()) return;

        try {
            const token = localStorage.getItem('token');
            // Course ID is optional, sending generic note for now
            await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notes`,
                {
                    title: "Quick Note",
                    content: newNote,
                    course_id: null,
                    note_type: 'text'
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewNote('');
            fetchNotes(); // Refresh list
        } catch (err) {
            console.error("Failed to create note", err);
            alert("Failed to save note");
        }
    };

    const handleDeleteNote = async (noteId) => {
        if (!confirm("Delete this note?")) return;
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

    const [selectedSketch, setSelectedSketch] = useState(null);

    return (
        <div className="h-full flex flex-col p-6 animate-in fade-in duration-500">
            <h2 className="text-2xl font-orbitron text-neon-blue mb-6 flex items-center gap-2">
                <StickyNote /> My Notes
            </h2>

            {/* Create Note (Quick Text) */}
            <div className="mb-8 p-4 border border-neon-blue/20 rounded-lg bg-deep-space/30">
                <div className="mb-2 text-sm text-gray-400">Quick Memo</div>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Type a new note..."
                        className="flex-1 input-cyber rounded bg-deep-space/50 border-neon-blue/30 focus:border-neon-blue"
                        onKeyPress={(e) => e.key === 'Enter' && handleCreateNote()}
                    />
                    <button
                        onClick={handleCreateNote}
                        className="btn-neon border-neon-blue text-neon-blue hover:bg-neon-blue/10 px-4"
                    >
                        <Plus size={20} />
                    </button>
                </div>
            </div>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {loading ? (
                    <div className="text-center text-neon-blue animate-pulse">Loading neural storage...</div>
                ) : notes.length === 0 ? (
                    <div className="text-center text-gray-500 mt-10">No notes recorded yet.</div>
                ) : (
                    notes.map(note => (
                        <div key={note.id} className="card-glass p-4 group relative hover:border-neon-blue/40 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <h4 className="font-bold text-white text-lg">{note.title || "Untitled Note"}</h4>
                                    {(note.topic || note.chapter_title) && (
                                        <div className="text-xs text-neon-purple mt-0.5 flex items-center gap-2">
                                            {note.topic && <span className="bg-neon-purple/10 px-1.5 py-0.5 rounded">{note.topic}</span>}
                                            {note.topic && note.chapter_title && <span>/</span>}
                                            {note.chapter_title && <span className="text-gray-400">{note.chapter_title}</span>}
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${note.note_type === 'sketch' ? 'border-neon-green text-neon-green' : 'border-gray-600 text-gray-400'}`}>
                                        {note.note_type || 'TEXT'}
                                    </span>
                                    <button
                                        onClick={() => handleDeleteNote(note.id)}
                                        className="text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            {note.note_type === 'sketch' ? (
                                <div className="mt-2">
                                    <button
                                        onClick={() => setSelectedSketch(note.metadata?.snapshot)}
                                        className="w-full h-24 bg-gray-900/50 rounded border border-dashed border-gray-700 flex items-center justify-center text-gray-500 hover:text-neon-blue hover:border-neon-blue/50 transition-all font-mono text-sm group-inner"
                                    >
                                        <span className="group-inner-hover:scale-105 transition-transform">Click to View Sketch</span>
                                    </button>
                                </div>
                            ) : (
                                <p className="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed">{note.content}</p>
                            )}

                            <div className="mt-3 pt-2 border-t border-white/5 text-xs text-gray-500 flex justify-between">
                                <span>{new Date(note.created_at).toLocaleString()}</span>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Sketch Viewer Modal */}
            {selectedSketch && (
                <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8 backdrop-blur-sm animate-in fade-in">
                    <div className="w-full h-full max-w-6xl bg-deep-space rounded-xl border border-neon-blue/30 flex flex-col overflow-hidden shadow-2xl">
                        <div className="h-12 border-b border-white/10 flex justify-between items-center px-4 bg-black/20">
                            <h3 className="text-white font-orbitron">Sketch Viewer</h3>
                            <button onClick={() => setSelectedSketch(null)} className="text-gray-400 hover:text-white">
                                <Trash2 className="hidden" /> {/* Dummy to keep import valid if needed, utilizing X instead */}
                                <span className="text-2xl">&times;</span>
                            </button>
                        </div>
                        <div className="flex-1 relative bg-white">
                            {/* Reusing CanvasEditor in read-only mode or just passing initialData. 
                                 Since CanvasEditor is an editor, we can just use it and maybe hide the save button 
                                 or just let them edit (but save won't update unless we wire it up).
                                 For now, let's lazily import CanvasEditor here or assuming it is imported.
                             */}
                            <CanvasEditor
                                initialData={selectedSketch}
                                onClose={() => setSelectedSketch(null)}
                                onSave={() => { alert("Updates from this view are not supported yet."); }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotesView;
