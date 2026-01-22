import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register, login } from '../api';
import { useAuth } from '../AuthContext';
import { toast } from 'sonner';

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuthToken } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = isLogin 
        ? await login(email, password)
        : await register(email, password);
      
      await setAuthToken(response.data.access_token);
      toast.success(isLogin ? 'Login realizado' : 'Cadastro realizado');
      
      // Aguardar um pouco para garantir que o estado foi atualizado
      setTimeout(() => {
        navigate('/sessions');
      }, 100);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao autenticar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="studio-background vignette min-h-screen flex items-center justify-center px-6">
      <div className="spotlight rounded-lg p-8 w-full max-w-md">
        <h2 
          className="text-3xl font-bold mb-2 text-center"
          style={{ fontFamily: "'Cormorant Garamond', serif" }}
          data-testid="auth-title"
        >
          {isLogin ? 'Entrar' : 'Criar Conta'}
        </h2>
        <p className="text-gray-400 text-center mb-8 text-sm">
          {isLogin ? 'Acesse sua conta' : 'Comece a treinar seu pitch'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4" data-testid="auth-form">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
              required
              data-testid="email-input"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
              required
              minLength={6}
              data-testid="password-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-white text-black font-semibold rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="auth-submit-button"
          >
            {loading ? 'Processando...' : (isLogin ? 'Entrar' : 'Criar Conta')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-gray-400 hover:text-white text-sm"
            data-testid="toggle-auth-mode"
          >
            {isLogin ? 'Não tem conta? Criar conta' : 'Já tem conta? Entrar'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;