import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
    return useContext(ThemeContext);
};

export const ThemeProvider = ({ children }) => {
    // Check localStorage or default to 'theme-original'
    const [theme, setTheme] = useState(() => {
        const savedTheme = localStorage.getItem('educore-theme');
        return savedTheme || 'theme-original';
    });

    useEffect(() => {
        // Remove old theme classes
        document.documentElement.classList.remove('theme-original', 'theme-light', 'theme-dark');

        // Apply the new theme class to the HTML root
        document.documentElement.classList.add(theme);

        // Persist
        localStorage.setItem('educore-theme', theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};
