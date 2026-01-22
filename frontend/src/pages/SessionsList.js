import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listSessions } from '../api';
import { useAuth } from '../AuthContext';
import { toast } from 'sonner';

const SessionsList = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await listSessions();
      setSessions(response.data);
    } catch (error) {
      toast.error('Erro ao carregar sessões');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      PENDING: { text: 'Pendente', color: 'bg-gray-700 text-gray-300' },
      IN_PROGRESS: { text: 'Em Andamento', color: 'bg-yellow-900 text-yellow-200' },
      COMPLETED: { text: 'Concluída', color: 'bg-green-900 text-green-200' },
    };
    const badge = badges[status] || badges.PENDING;
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  return (
    <div className="studio-background vignette min-h-screen">
      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 
              className="text-5xl font-bold mb-2"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
              data-testid="sessions-title"
            >
              Suas Sessões
            </h1>
            <p className="text-gray-400">Histórico de simulações e relatórios</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => navigate('/sessions/new')}
              className="px-6 py-3 bg-white text-black font-semibold rounded hover:bg-gray-200"
              data-testid="new-session-button"
            >
              Nova Sessão
            </button>
            <button
              onClick={logout}
              className="px-6 py-3 bg-gray-800 text-gray-300 rounded hover:bg-gray-700"
              data-testid="logout-button"
            >
              Sair
            </button>
          </div>
        </div>

        {/* Sessions List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-400">Carregando...</div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="spotlight rounded-lg p-12 text-center" data-testid="empty-sessions">
            <p className="text-gray-400 mb-4">Nenhuma sessão ainda</p>
            <button
              onClick={() => navigate('/sessions/new')}
              className="px-6 py-2 bg-white text-black rounded hover:bg-gray-200"
            >
              Criar Primeira Sessão
            </button>
          </div>
        ) : (
          <div className="grid gap-6" data-testid="sessions-list">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="panel-seat rounded-lg p-6 cursor-pointer"
                onClick={() => navigate(`/sessions/${session.id}`)}
                data-testid={`session-item-${session.id}`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {session.pitch.titulo}
                    </h3>
                    <p className="text-gray-400 text-sm line-clamp-2">
                      {session.pitch.problema}
                    </p>
                  </div>
                  {getStatusBadge(session.status)}
                </div>

                {/* Sharks */}
                <div className="flex gap-2 mb-3">
                  {session.sharks.map((shark, idx) => (
                    <div
                      key={idx}
                      className={`px-3 py-1 rounded text-xs ${
                        shark.state.is_out
                          ? 'bg-gray-800 text-gray-500 line-through'
                          : 'bg-gray-700 text-gray-300'
                      }`}
                    >
                      {shark.archetype_name}
                    </div>
                  ))}
                </div>

                <div className="text-xs text-gray-500">
                  {new Date(session.created_at).toLocaleString('pt-BR')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionsList;