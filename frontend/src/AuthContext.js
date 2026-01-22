import React, { createContext, useContext, useState, useEffect } from 'react';
import { getMe, setAuthToken as setApiAuthToken, getAuthToken } from './api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('auth_token');
          setApiAuthToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const setAuthToken = async (token) => {
    setApiAuthToken(token);
    if (token) {
      try {
        const res = await getMe();
        setUser(res.data);
        return true;
      } catch (error) {
        localStorage.removeItem('auth_token');
        setApiAuthToken(null);
        return false;
      }
    } else {
      setUser(null);
      return true;
    }
  };

  const logout = () => {
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, setAuthToken, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};