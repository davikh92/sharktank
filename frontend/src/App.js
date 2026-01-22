import React from 'react';
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from 'sonner';
import { AuthProvider } from './AuthContext';
import { ProtectedRoute } from './ProtectedRoute';

// Pages
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import SessionsList from './pages/SessionsList';
import NewSession from './pages/NewSession';
import SessionRoom from './pages/SessionRoom';
import Report from './pages/Report';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/auth" element={<Auth />} />
            <Route
              path="/sessions"
              element={
                <ProtectedRoute>
                  <SessionsList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sessions/new"
              element={
                <ProtectedRoute>
                  <NewSession />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sessions/:sessionId"
              element={
                <ProtectedRoute>
                  <SessionRoom />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sessions/:sessionId/report"
              element={
                <ProtectedRoute>
                  <Report />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" theme="dark" />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
