import { useState } from 'react';
import axios from 'axios';
import { Sparkles, Loader2, ArrowRight } from 'lucide-react';

const NewModule = ({ onCourseCreated }) => {
    const [topic, setTopic] = useState("Quantum Physics");
    const [grade, setGrade] = useState("Undergraduate");
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const payload = { topic, grade_level: grade };
            const res = await axios.post('http://localhost:8000/courses/generate', payload);

            // Notify parent to refresh list and select new course
            if (res.data.course_id) {
                onCourseCreated(res.data.course_id);
            }
        } catch (err) {
            alert("Failed to generate couse: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto animate-in fade-in zoom-in duration-500">
            <div className="card-glass border-neon-blue/50 p-8 md:p-12 relative overflow-hidden">
                {/* Decorative background glow */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-neon-blue/10 blur-[100px] rounded-full pointer-events-none"></div>

                <h2 className="text-3xl font-orbitron mb-6 flex items-center gap-3">
                    <Sparkles className="text-neon-blue" />
                    Initialize New Module
                </h2>

                <div className="grid md:grid-cols-3 gap-6 mb-8">
                    <div className="md:col-span-2">
                        <label className="block text-neon-blue text-sm mb-2 uppercase tracking-widest">Target Subject</label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            className="input-cyber text-lg"
                            placeholder="e.g. Neuroscience"
                        />
                    </div>

                    <div>
                        <label className="block text-neon-blue text-sm mb-2 uppercase tracking-widest">Complexity</label>
                        <select
                            value={grade}
                            onChange={(e) => setGrade(e.target.value)}
                            className="input-cyber text-lg bg-transparent"
                        >
                            <option value="Grade 8" className="bg-deep-space">Grade 8</option>
                            <option value="Grade 10" className="bg-deep-space">Grade 10</option>
                            <option value="Undergraduate" className="bg-deep-space">Undergraduate</option>
                            <option value="PhD" className="bg-deep-space">PhD</option>
                        </select>
                    </div>
                </div>

                <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="w-full btn-neon py-4 text-xl flex justify-center items-center gap-3 group"
                >
                    {loading ? (
                        <>
                            <Loader2 className="animate-spin" />
                            <span>Accessing Neural Network...</span>
                        </>
                    ) : (
                        <>
                            <span>Generate Roadmap</span>
                            <ArrowRight className="group-hover:translate-x-1 transition-transform" />
                        </>
                    )}
                </button>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mt-12">
                {/* Feature Cards / Recommendations */}
                {['Artificial Intelligence', 'Cybersecurity', 'Space Exploration'].map((item, i) => (
                    <div key={i} className="card-glass p-6 hover:border-neon-blue/50 transition-colors cursor-pointer group" onClick={() => setTopic(item)}>
                        <div className="text-2xl mb-2 opacity-50 group-hover:opacity-100 transition-opacity">
                            {i === 0 ? '🤖' : i === 1 ? '🛡️' : '🚀'}
                        </div>
                        <h3 className="text-lg font-bold text-white group-hover:text-neon-blue transition-colors">{item}</h3>
                        <div className="h-1 w-full bg-white/10 mt-4 rounded-full overflow-hidden">
                            <div className="h-full bg-neon-blue w-1/3 opacity-50"></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default NewModule;
