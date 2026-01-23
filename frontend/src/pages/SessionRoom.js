import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getSession, 
  startSession, 
  respondToSession, 
  getSessionMessages,
  getSessionEvents,
  founderAction,
  getSessionOffers
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
  
  // Estados de negociação
  const [activeOffers, setActiveOffers] = useState([]);
  const [awaitingFounderAction, setAwaitingFounderAction] = useState(false);
  const [sessionPhase, setSessionPhase] = useState('PITCHING');
  const [ending, setEnding] = useState(null);
  
  // Contra-proposta
  const [showCounterForm, setShowCounterForm] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [counterValor, setCounterValor] = useState('');
  const [counterEquity, setCounterEquity] = useState('');
  const [counterMessage, setCounterMessage] = useState('');

  // Calcular quais sharks estão OUT baseado nos eventos
  const sharksOutSet = useMemo(() => {
    const outSet = new Set();
    events.forEach(event => {
      if (event.event_type === 'SHARK_OUT') {
        outSet.add(event.actor);
      }
    });
    return outSet;
  }, [events]);

  useEffect(() => {
    loadSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      
      // Carregar ofertas ativas
      try {
        const offersRes = await getSessionOffers(sessionId);
        setActiveOffers(offersRes.data || []);
        if (offersRes.data && offersRes.data.length > 0) {
          setAwaitingFounderAction(true);
          setSessionPhase('NEGOTIATION_WINDOW');
        }
      } catch (e) {
        // Ignorar se endpoint não existe
      }
      
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
      
      // Atualizar estado de negociação
      if (response.data.active_offers) {
        setActiveOffers(response.data.active_offers);
      }
      if (response.data.awaiting_founder_action !== undefined) {
        setAwaitingFounderAction(response.data.awaiting_founder_action);
      }
      if (response.data.session_phase) {
        setSessionPhase(response.data.session_phase);
      }
      if (response.data.ending) {
        setEnding(response.data.ending);
      }
      
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

  // === AÇÕES DO FOUNDER ===
  
  const handleFounderAction = async (action, offerId, counterOffer = null) => {
    setResponding(true);
    
    try {
      const payload = {
        action: action,
        offer_id: offerId,
        counter_offer: counterOffer
      };
      
      const response = await founderAction(sessionId, payload);
      
      setMessages([...messages, ...response.data.messages]);
      setEvents([...events, ...response.data.events]);
      setCanRespond(response.data.can_user_respond);
      
      // Atualizar estado de negociação
      setActiveOffers(response.data.active_offers || []);
      setAwaitingFounderAction(response.data.awaiting_founder_action || false);
      setSessionPhase(response.data.session_phase || 'PITCHING');
      
      if (response.data.ending) {
        setEnding(response.data.ending);
      }
      
      if (response.data.session_status === 'COMPLETED') {
        setSession({ ...session, status: 'COMPLETED' });
      }
      
      // Resetar form de contra-proposta
      setShowCounterForm(false);
      setSelectedOffer(null);
      setCounterValor('');
      setCounterEquity('');
      setCounterMessage('');
      
    } catch (error) {
      toast.error('Erro ao processar ação');
    } finally {
      setResponding(false);
    }
  };
  
  const handleAccept = (offerId) => {
    handleFounderAction('ACCEPT', offerId);
  };
  
  const handleReject = (offerId) => {
    handleFounderAction('REJECT', offerId);
  };
  
  const handleWait = (offerId) => {
    handleFounderAction('WAIT', offerId);
  };
  
  const handleCounter = (offer) => {
    setSelectedOffer(offer);
    setCounterValor(offer.valor);
    setCounterEquity(offer.equity.replace('%', ''));
    setShowCounterForm(true);
  };
  
  const submitCounter = () => {
    if (!counterValor || !counterEquity) {
      toast.error('Preencha valor e equity');
      return;
    }
    
    const counterOffer = {
      offer_id: selectedOffer.id,
      valor: counterValor,
      equity: counterEquity.includes('%') ? counterEquity : counterEquity + '%',
      message: counterMessage || null
    };
    
    handleFounderAction('COUNTER', selectedOffer.id, counterOffer);
  };

  const getOfferTypeLabel = (type) => {
    switch(type) {
      case 'ALIGNED': return 'Alinhada';
      case 'AGGRESSIVE': return 'Agressiva';
      case 'CREATIVE': return 'Criativa';
      default: return type;
    }
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
                Voltar
              </button>
              <h1 
                className="text-3xl font-bold"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
                data-testid="session-title"
              >
                {session.pitch.titulo}
              </h1>
              {/* Phase indicator */}
              <div className="mt-2 flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  sessionPhase === 'NEGOTIATION_WINDOW' 
                    ? 'bg-green-900/50 text-green-400 border border-green-700' 
                    : 'bg-gray-800 text-gray-400'
                }`}>
                  {sessionPhase === 'PITCHING' ? 'Fase de Perguntas' : 
                   sessionPhase === 'NEGOTIATION_WINDOW' ? 'Negociacao em Andamento' :
                   'Encerramento'}
                </span>
              </div>
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

          {/* Sharks Panel - Estados Granulares */}
          <div className="grid grid-cols-4 gap-4" data-testid="sharks-panel">
            {session.sharks && session.sharks.map((shark, idx) => {
              // Verificar se shark está OUT baseado nos eventos (fonte primária de verdade)
              const isOut = sharksOutSet.has(shark.archetype_name) || shark.state?.is_out || false;
              const hasOffer = activeOffers.some(o => o.shark_name === shark.archetype_name);
              const interest = shark.state?.interest || 50;
              const patience = shark.state?.patience || 50;
              const inRecovery = shark.state?.in_recovery_window || false;
              
              // Determinar estado de exibição granular
              const getDisplayState = () => {
                if (isOut) return { state: 'OUT', icon: '✗', color: 'text-red-400', bg: 'bg-red-900/50' };
                if (inRecovery) return { state: 'ÚLTIMA CHANCE', icon: '⏱️', color: 'text-yellow-400', bg: 'bg-yellow-900/50' };
                if (hasOffer) {
                  if (sessionPhase === 'NEGOTIATION_WINDOW') {
                    return { state: 'NEGOCIANDO', icon: '🤝', color: 'text-blue-400', bg: 'bg-blue-900/50' };
                  }
                  return { state: 'OFERTA', icon: '💰', color: 'text-green-400', bg: 'bg-green-900' };
                }
                if (patience < 25) return { state: 'IMPACIENTE', icon: '⚠️', color: 'text-orange-400', bg: 'bg-orange-900/30' };
                if (interest < 35) return { state: 'CÉTICO', icon: '🤨', color: 'text-gray-400', bg: 'bg-gray-700' };
                if (interest >= 70) return { state: 'INTERESSADO', icon: '👀', color: 'text-green-400', bg: 'bg-green-900/30' };
                return { state: 'ATIVO', icon: '●', color: 'text-gray-400', bg: 'bg-gray-700' };
              };
              
              const displayState = getDisplayState();
              
              return (
                <div
                  key={idx}
                  className={`panel-seat rounded-lg p-4 text-center transition-all duration-500 ${
                    isOut 
                      ? 'opacity-40 bg-red-900/20 border border-red-900/50' 
                      : inRecovery
                        ? 'bg-yellow-900/20 border border-yellow-700/50 animate-pulse'
                        : hasOffer 
                          ? 'ring-2 ring-green-500' 
                          : displayState.state === 'IMPACIENTE'
                            ? 'border border-orange-700/50'
                            : displayState.state === 'INTERESSADO'
                              ? 'border border-green-700/30'
                              : ''
                  }`}
                  data-testid={`shark-panel-${shark.archetype_name.toLowerCase().replace(/\s/g, '-')}`}
                >
                  <div className={`w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center transition-colors ${displayState.bg}`}>
                    <span className={`text-2xl ${isOut ? 'opacity-50' : ''}`}>
                      {displayState.icon !== '●' && displayState.icon !== '✗' ? displayState.icon : shark.archetype_name.charAt(0)}
                    </span>
                  </div>
                  <h3 className={`font-semibold text-sm mb-1 ${isOut ? 'text-gray-500 line-through' : 'text-white'}`}>
                    {shark.archetype_name}
                  </h3>
                  <span 
                    className={`text-xs font-bold ${displayState.color}`}
                    data-testid={`shark-status-${shark.archetype_name.toLowerCase().replace(/\s/g, '-')}`}
                  >
                    {displayState.icon} {displayState.state}
                  </span>
                  {/* Barra de interesse (sutil) */}
                  {!isOut && (
                    <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${
                          interest > 70 ? 'bg-green-500' : 
                          interest > 50 ? 'bg-gray-500' : 
                          interest > 30 ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${interest}%` }}
                      />
                    </div>
                  )}
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
                const isUser = msg.speaker === 'USER' || msg.speaker === 'FOUNDER';
                const isInterruption = msg.message_type === 'INTERRUPTION';
                const isOut = msg.message_type === 'OUT_ANNOUNCEMENT';
                const isOffer = msg.message_type === 'OFFER';
                const isOfferPressure = msg.message_type === 'OFFER_PRESSURE';
                const isOfferWithdrawn = msg.message_type === 'OFFER_WITHDRAWN';
                const isDeal = msg.message_type === 'DEAL_ANNOUNCEMENT';
                const isNarration = msg.message_type === 'NARRATION';
                const isSharkReaction = msg.message_type === 'SHARK_REACTION';
                const isConflict = msg.message_type === 'SHARK_CONFLICT';
                const isCounter = msg.message_type === 'COUNTER_OFFER';
                
                return (
                  <div
                    key={msg.id || idx}
                    className={`message-bubble ${isInterruption ? 'hard-cut' : ''}`}
                    data-testid={`message-${idx}`}
                  >
                    {isNarration ? (
                      <div className="text-center py-6 px-8 bg-gradient-to-b from-gray-900 to-black rounded-lg border border-gray-700">
                        <p className="text-lg text-gray-300 italic leading-relaxed">
                          {msg.content}
                        </p>
                      </div>
                    ) : (
                      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
                          <div className="text-xs text-gray-500 mb-1">
                            {isUser ? 'Voce' : msg.speaker}
                            {isInterruption && <span className="ml-2 text-red-400">[INTERRUPCAO]</span>}
                            {isOut && <span className="ml-2 text-red-400">[OUT]</span>}
                            {isOffer && <span className="ml-2 text-green-400">[OFERTA]</span>}
                            {isOfferPressure && <span className="ml-2 text-yellow-400">[PRESSAO]</span>}
                            {isOfferWithdrawn && <span className="ml-2 text-red-400">[RETIRADA]</span>}
                            {isDeal && <span className="ml-2 text-green-400 font-bold">[DEAL!]</span>}
                            {isSharkReaction && <span className="ml-2 text-blue-400">[REACAO]</span>}
                            {isConflict && <span className="ml-2 text-purple-400">[CONFLITO]</span>}
                            {isCounter && <span className="ml-2 text-cyan-400">[CONTRA-PROPOSTA]</span>}
                          </div>
                          <div
                            className={`inline-block px-4 py-3 rounded-lg ${
                              isUser
                                ? 'bg-gray-800 text-white'
                                : isOut || isOfferWithdrawn
                                ? 'bg-red-900/30 text-red-300 border border-red-800'
                                : isOffer || isDeal
                                ? 'bg-green-900/30 text-green-300 border border-green-800'
                                : isOfferPressure
                                ? 'bg-yellow-900/30 text-yellow-300 border border-yellow-800'
                                : isConflict
                                ? 'bg-purple-900/30 text-purple-300 border border-purple-800'
                                : 'bg-gray-900 text-gray-200'
                            }`}
                          >
                            {msg.content}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Reading Hint */}
              {readingHint && (
                <div className="text-center py-4" data-testid="reading-hint">
                  <p className="text-sm text-gray-500 italic">{readingHint}</p>
                </div>
              )}

              {/* Ending display */}
              {ending && (
                <div className="text-center py-6" data-testid="session-ended">
                  <div className={`inline-block px-6 py-4 rounded-lg ${
                    ending.type === 'DEAL_CLOSED' ? 'bg-green-900/30 border border-green-700' :
                    ending.type === 'DEAL_BITTER' ? 'bg-yellow-900/30 border border-yellow-700' :
                    ending.type === 'TABLE_BROKEN' ? 'bg-red-900/30 border border-red-700' :
                    'bg-gray-900/50 border border-gray-700'
                  }`}>
                    <p className="text-2xl mb-2">
                      {ending.type === 'DEAL_CLOSED' ? 'Acordo Fechado' :
                       ending.type === 'DEAL_BITTER' ? 'Acordo Amargo' :
                       ending.type === 'TABLE_BROKEN' ? 'Mesa Quebrada' : 'Sem Investimento'}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate(`/sessions/${sessionId}/report`)}
                    className="mt-4 px-6 py-2 bg-white text-black font-semibold rounded hover:bg-gray-200"
                  >
                    Ver Relatório Completo
                  </button>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Active Offers Panel */}
          {activeOffers.length > 0 && session.status === 'IN_PROGRESS' && (
            <div className="mb-6 p-6 bg-gradient-to-r from-green-900/30 to-gray-900 rounded-lg border border-green-800" data-testid="offers-panel">
              <h3 className="text-lg font-bold text-green-400 mb-4">Ofertas na Mesa</h3>
              <div className="space-y-4">
                {activeOffers.map((offer, idx) => (
                  <div key={offer.id || idx} className="bg-black/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="text-white font-semibold">{offer.shark_name}</p>
                        <p className="text-xs text-gray-500">{getOfferTypeLabel(offer.offer_type)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-green-400 font-bold">{offer.valor}</p>
                        <p className="text-green-300">por {offer.equity}</p>
                      </div>
                    </div>
                    {offer.conditions && (
                      <p className="text-xs text-gray-400 mb-3 italic">&ldquo;{offer.conditions}&rdquo;</p>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-yellow-500">
                        {offer.turns_remaining} turno(s) restante(s)
                      </span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAccept(offer.id)}
                          disabled={responding}
                          className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                          data-testid={`accept-offer-${idx}`}
                        >
                          Aceitar
                        </button>
                        <button
                          onClick={() => handleCounter(offer)}
                          disabled={responding}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                          data-testid={`counter-offer-${idx}`}
                        >
                          Contra
                        </button>
                        <button
                          onClick={() => handleWait(offer.id)}
                          disabled={responding}
                          className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50"
                          data-testid={`wait-offer-${idx}`}
                        >
                          Esperar
                        </button>
                        <button
                          onClick={() => handleReject(offer.id)}
                          disabled={responding}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                          data-testid={`reject-offer-${idx}`}
                        >
                          Recusar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Counter Offer Form Modal */}
          {showCounterForm && selectedOffer && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" data-testid="counter-modal">
              <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
                <h3 className="text-lg font-bold text-white mb-4">Contra-Proposta para {selectedOffer.shark_name}</h3>
                <p className="text-sm text-gray-400 mb-4">
                  Oferta original: {selectedOffer.valor} por {selectedOffer.equity}
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Valor (ex: R$ 400.000)</label>
                    <input
                      type="text"
                      value={counterValor}
                      onChange={(e) => setCounterValor(e.target.value)}
                      className="w-full px-3 py-2 bg-black border border-gray-700 rounded text-white"
                      placeholder="R$ 400.000"
                      data-testid="counter-valor-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Equity (%)</label>
                    <input
                      type="text"
                      value={counterEquity}
                      onChange={(e) => setCounterEquity(e.target.value)}
                      className="w-full px-3 py-2 bg-black border border-gray-700 rounded text-white"
                      placeholder="10"
                      data-testid="counter-equity-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Mensagem (opcional)</label>
                    <textarea
                      value={counterMessage}
                      onChange={(e) => setCounterMessage(e.target.value)}
                      className="w-full px-3 py-2 bg-black border border-gray-700 rounded text-white resize-none"
                      rows={2}
                      placeholder="Argumento para sua contra-proposta..."
                      data-testid="counter-message-input"
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowCounterForm(false)}
                    className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                    data-testid="cancel-counter-button"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={submitCounter}
                    disabled={responding}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    data-testid="submit-counter-button"
                  >
                    Enviar Contra-Proposta
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* User Input */}
          {session.status === 'IN_PROGRESS' && !awaitingFounderAction && (
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

          {/* Message when awaiting action */}
          {session.status === 'IN_PROGRESS' && awaitingFounderAction && activeOffers.length > 0 && (
            <div className="text-center py-4 text-yellow-400" data-testid="awaiting-action-message">
              Ha oferta(s) na mesa. Escolha uma acao acima antes de continuar.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SessionRoom;
