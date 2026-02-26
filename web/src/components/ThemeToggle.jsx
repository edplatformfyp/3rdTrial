import { useTheme } from '../context/ThemeContext';
import { Monitor, Sun, Moon } from 'lucide-react';

const ThemeToggle = () => {
    const { theme, setTheme } = useTheme();

    const themes = [
        { id: 'theme-original', name: 'Original Cyberpunk', icon: <Monitor size={18} /> },
        { id: 'theme-light', name: 'Standard Light', icon: <Sun size={18} /> },
        { id: 'theme-dark', name: 'Standard Dark', icon: <Moon size={18} /> },
    ];

    return (
        <div className="card-glass p-6 max-w-xl animate-in fade-in">
            <h3 className="text-xl font-orbitron text-white mb-6">Interface Theme</h3>
            <p className="text-gray-400 text-sm mb-6 pb-4 border-b border-white/10">
                Customize your visual experience across the platform. Your choice is automatically saved.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {themes.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setTheme(t.id)}
                        className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all duration-300 ${theme === t.id
                                ? 'bg-neon-blue/20 border-neon-blue text-neon-blue shadow-[0_0_15px_rgba(0,243,255,0.2)]'
                                : 'bg-black/20 border-white/5 text-gray-400 hover:bg-white/5 hover:text-white'
                            }`}
                    >
                        <div className="mb-3">{t.icon}</div>
                        <span className="font-bold text-sm text-center">{t.name}</span>
                    </button>
                ))}
            </div>

            <div className="mt-8 p-4 bg-black/40 rounded-lg border border-white/5 text-sm">
                <p className="text-white font-bold mb-1">Theme Preview</p>
                <p className="text-gray-400">Notice how the backgrounds, glowing highlights, and primary text colors immediately adapt to your selected theme preference.</p>
            </div>
        </div>
    );
};

export default ThemeToggle;
