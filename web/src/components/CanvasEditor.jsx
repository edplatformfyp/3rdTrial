import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'
import { useState } from 'react'
import { Save } from 'lucide-react'

// CanvasEditor component
// Props:
// - initialData: object (optional) - Initial snapshot of the canvas
// - onSave: function(snapshot) - Callback when save is clicked
// - onClose: function() - Callback when close/cancel is clicked
// - readOnly: boolean (optional) - If true, the canvas will be in read-only mode

const CanvasEditor = ({ initialData, onSave, onClose, readOnly = false }) => {
    const [editor, setEditor] = useState(null)

    const handleMount = (editorInstance) => {
        setEditor(editorInstance)

        // Load initial data if provided
        if (initialData) {
            try {
                editorInstance.loadSnapshot(initialData)
            } catch (e) {
                console.error("Failed to load snapshot", e)
            }
        }

        // Set dark mode to match theme
        editorInstance.user.updateUserPreferences({ isDarkMode: true })

        // Set Read Only if requested
        if (readOnly) {
            editorInstance.updateInstanceState({ isReadonly: true })
        }
    }

    const handleSave = () => {
        if (editor && !readOnly) {
            const snapshot = editor.getSnapshot()
            onSave(snapshot)
        }
    }

    return (
        <div className="fixed inset-0 z-50 bg-deep-space flex flex-col animate-in fade-in duration-300">
            {/* Toolbar */}
            <div className="h-16 border-b border-neon-blue/30 flex justify-between items-center px-6 bg-deep-space/90 backdrop-blur-md">
                <h2 className="text-xl font-orbitron text-white">
                    <span className="text-neon-purple">{readOnly ? 'VIEW' : 'NEURAL'}</span> SKETCHPAD
                </h2>
                <div className="flex gap-4">
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        {readOnly ? 'CLOSE' : 'CANCEL'}
                    </button>
                    {!readOnly && (
                        <button
                            onClick={handleSave}
                            className="btn-neon flex items-center gap-2 px-6"
                        >
                            <Save size={18} />
                            SAVE NOTE
                        </button>
                    )}
                </div>
            </div>

            {/* Editor Area */}
            <div className="flex-1 relative">
                <Tldraw
                    onMount={handleMount}
                    persistenceKey={readOnly ? null : "educore-sketch"} // Disable persistence for read-only
                    hideUi={readOnly}
                />
            </div>
        </div>
    )
}

export default CanvasEditor
