import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getSession, 
  startSession, 
  respondToSession, 
  getSessionMessages,
  getSessionEvents 
} from '../api';
import { toast } from 'sonner';

const SessionRoom = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [events, setEvents] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [responding, setResponding] = useState(false);
  const [canRespond, setCanRespond] = useState(false);
  const [readingHint, setReadingHint] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSession = async () => {
    try {
      const [sessionRes, messagesRes, eventsRes] = await Promise.all([
        getSession(sessionId),
        getSessionMessages(sessionId).catch(() => ({ data: [] })),
        getSessionEvents(sessionId).catch(() => ({ data: [] })),
      ]);
      
      setSession(sessionRes.data);
      setMessages(messagesRes.data);
      setEvents(eventsRes.data);
      
      // Se sessão está PENDING, iniciar automaticamente
      if (sessionRes.data.status === 'PENDING') {
        handleStartSession();
      } else if (sessionRes.data.status === 'IN_PROGRESS') {
        setCanRespond(true);
      }
    } catch (error) {
      toast.error('Erro ao carregar sessão');
      navigate('/sessions');
    } finally {
      setLoading(false);
    }
  };

  const handleStartSession = async () => {
    try {
      const response = await startSession(sessionId);
      setMessages([...messages, ...response.data.messages]);
      setCanRespond(response.data.can_user_respond);
      setSession({ ...session, status: 'IN_PROGRESS' });
    } catch (error) {
      toast.error('Erro ao iniciar sessão');
    }
  };

  const handleSubmitResponse = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || !canRespond) return;

    setResponding(true);
    setCanRespond(false);

    try {
      const response = await respondToSession(sessionId, userInput);
      
      setMessages([...messages, ...response.data.messages]);
      setEvents([...events, ...response.data.events]);
      setCanRespond(response.data.can_user_respond);
      setReadingHint(response.data.reading_hint);
      
      if (response.data.session_status === 'COMPLETED') {
        setSession({ ...session, status: 'COMPLETED' });
        toast.success('Sessão concluída');
      }
      
      setUserInput('');
    } catch (error) {
      toast.error('Erro ao enviar resposta');
      setCanRespond(true);
    } finally {
      setResponding(false);
    }
  };

  const getSharkStatus = (sharkName) => {
    if (!session) return 'ATIVO';
    const shark = session.sharks.find(s => s.archetype_name === sharkName);
    return shark?.state?.is_out ? 'OUT' : 'ATIVO';
  };

  if (loading || !session || !session.pitch) {
    return (
      <div className="studio-background min-h-screen flex items-center justify-center">
        <div className="text-gray-400">Carregando sessão...</div>
      </div>
    );
  }

  return (
    <div className="studio-background vignette min-h-screen" data-testid="session-room">
      {/* Header with sharks panel */}
      <div className="border-b border-gray-800">
        <div className="container mx-auto px-6 py-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <button
                onClick={() => navigate('/sessions')}
                className="text-gray-400 hover:text-white mb-2 text-sm"
                data-testid="back-to-sessions-button"
              >
                ← Voltar
              </button>
              <h1 
                className="text-3xl font-bold"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
                data-testid="session-title"
              >
                {session.pitch.titulo}
              </h1>
            </div>
            {session.status === 'COMPLETED' && (
              <button
                onClick={() => navigate(`/sessions/${sessionId}/report`)}
                className="px-6 py-2 bg-white text-black font-semibold rounded hover:bg-gray-200"
                data-testid="view-report-button"
              >
                Ver Relatório
              </button>
            )}
          </div>

          {/* Sharks Panel */}
          <div className="grid grid-cols-4 gap-4" data-testid="sharks-panel">
            {session.sharks && session.sharks.map((shark, idx) => {
              const isOut = shark.state?.is_out || false;
              return (
                <div
                  key={idx}
                  className={`panel-seat rounded-lg p-4 text-center ${isOut ? 'out' : ''}`}
                  data-testid={`shark-panel-${shark.archetype_name.toLowerCase().replace(/\s/g, '-')}`}
                >
                  <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gray-700 flex items-center justify-center">
                    <span className="text-2xl">{shark.archetype_name.charAt(0)}</span>
                  </div>
                  <h3 className="text-white font-semibold text-sm mb-1">
                    {shark.archetype_name}
                  </h3>
                  <span 
                    className={`text-xs ${isOut ? 'text-red-400' : 'text-green-400'}`}
                    data-testid={`shark-status-${shark.archetype_name.toLowerCase().replace(/\s/g, '-')}`}
                  >
                    {isOut ? 'OUT' : 'ATIVO'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Conversation Stage */}
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Messages */}
          <div className="spotlight rounded-lg p-8 mb-6 min-h-[400px] max-h-[600px] overflow-y-auto" data-testid="messages-container">
            <div className="space-y-6">
              {messages.map((msg, idx) => {
                const isUser = msg.speaker === 'USER';
                const isInterruption = msg.message_type === 'INTERRUPTION';
                const isOut = msg.message_type === 'OUT_ANNOUNCEMENT';
                const isOffer = msg.message_type === 'OFFER';
                
                return (
                  <div
                    key={msg.id || idx}
                    className={`message-bubble ${isInterruption ? 'hard-cut' : ''}`}
                    data-testid={`message-${idx}`}
                  >
                    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
                        <div className="text-xs text-gray-500 mb-1">
                          {isUser ? 'Você' : msg.speaker}
                          {isInterruption && <span className="ml-2 text-red-400">[INTERRUPÇÃO]</span>}
                          {isOut && <span className="ml-2 text-red-400">[OUT]</span>}
                          {isOffer && <span className="ml-2 text-green-400">[OFERTA]</span>}
                        </div>
                        <div
                          className={`inline-block px-4 py-3 rounded-lg ${
                            isUser
                              ? 'bg-gray-800 text-white'
                              : isOut
                              ? 'bg-red-900/30 text-red-300 border border-red-800'
                              : isOffer
                              ? 'bg-green-900/30 text-green-300 border border-green-800'
                              : 'bg-gray-900 text-gray-200'
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Reading Hint */}
              {readingHint && session.reading_hints_enabled && (
                <div className="text-center py-4" data-testid="reading-hint">
                  <p className="text-sm text-gray-500 italic">{readingHint}</p>
                </div>
              )}

              {/* Session ended */}
              {session.status === 'COMPLETED' && (
                <div className="text-center py-6" data-testid="session-ended">
                  <p className="text-gray-400 mb-4">Sessão encerrada</p>
                  <button
                    onClick={() => navigate(`/sessions/${sessionId}/report`)}
                    className="px-6 py-2 bg-white text-black font-semibold rounded hover:bg-gray-200"
                  >
                    Ver Relatório Completo
                  </button>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* User Input */}
          {session.status === 'IN_PROGRESS' && (
            <form onSubmit={handleSubmitResponse} className="space-y-4" data-testid="user-input-form">
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={!canRespond || responding}
                placeholder={
                  responding 
                    ? 'Aguarde a resposta...' 
                    : !canRespond 
                    ? 'Aguarde sua vez...' 
                    : 'Digite sua resposta...'
                }
                className="w-full px-4 py-4 bg-black border border-gray-700 rounded text-white resize-none disabled:opacity-50"
                rows={4}
                data-testid="user-input-textarea"
              />
              <button
                type="submit"
                disabled={!canRespond || responding || !userInput.trim()}
                className="w-full px-6 py-3 bg-white text-black font-semibold rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="submit-response-button"
              >
                {responding ? 'Enviando...' : 'Enviar Resposta'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default SessionRoom;
