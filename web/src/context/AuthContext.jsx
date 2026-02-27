import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    // Configure Axios default header
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            localStorage.setItem('token', token);
        } else {
            delete axios.defaults.headers.common['Authorization'];
            localStorage.removeItem('token');
            setUser(null);
        }
    }, [token]);

    // Fetch User Profile on load
    useEffect(() => {
        const fetchUser = async () => {
            if (!token) {
                setLoading(false);
                return;
            }
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/users/me`);
                setUser(res.data);
            } catch (error) {
                console.error("Auth check failed:", error);
                setToken(null);
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, [token]);

    const login = async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/token`, formData);
        const { access_token, role } = res.data;

        // Immediately configure axios headers for the subsequent request
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        localStorage.setItem('token', access_token);
        setToken(access_token);

        // Fetch User directly so ProtectedRoute doesn't redirect before useEffect fires
        try {
            const userRes = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/users/me`);
            setUser(userRes.data);
        } catch (error) {
            console.error("Auth check failed during login:", error);
        }

        return role;
    };

    const register = async (userData) => {
        const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/register`, userData);
        return res.data;
    };

    const logout = () => {
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
