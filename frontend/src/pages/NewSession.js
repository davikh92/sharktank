import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSharks, createSession } from '../api';
import { toast } from 'sonner';

const NewSession = () => {
  const [sharks, setSharks] = useState([]);
  const [selectedSharks, setSelectedSharks] = useState([]);
  const [useRandom, setUseRandom] = useState(true);
  const [readingHints, setReadingHints] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [pitch, setPitch] = useState({
    titulo: '',
    problema: '',
    solucao: '',
    mercado: '',
    modelo_negocio: '',
    tracao: '',
    pedido_valor: '',
    pedido_equity: '',
  });

  useEffect(() => {
    loadSharks();
  }, []);

  const loadSharks = async () => {
    try {
      const response = await getSharks();
      setSharks(response.data.sharks);
    } catch (error) {
      toast.error('Erro ao carregar sharks');
    }
  };

  const toggleShark = (sharkName) => {
    if (selectedSharks.includes(sharkName)) {
      setSelectedSharks(selectedSharks.filter((s) => s !== sharkName));
    } else {
      if (selectedSharks.length < 4) {
        setSelectedSharks([...selectedSharks, sharkName]);
      } else {
        toast.error('Máximo de 4 sharks');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!useRandom && selectedSharks.length !== 4) {
      toast.error('Selecione exatamente 4 sharks');
      return;
    }

    setLoading(true);
    try {
      const sessionData = {
        pitch,
        panel_selection: useRandom ? null : selectedSharks,
        reading_hints_enabled: readingHints,
      };

      const response = await createSession(sessionData);
      toast.success('Sessão criada');
      navigate(`/sessions/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar sessão');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="studio-background vignette min-h-screen">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <button
              onClick={() => navigate('/sessions')}
              className="text-gray-400 hover:text-white mb-4 flex items-center gap-2"
              data-testid="back-button"
            >
              ← Voltar
            </button>
            <h1 
              className="text-5xl font-bold mb-2"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
              data-testid="new-session-title"
            >
              Nova Sessão
            </h1>
            <p className="text-gray-400">Configure seu pitch e painel de investidores</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8" data-testid="new-session-form">
            {/* Pitch Data */}
            <div className="spotlight rounded-lg p-8 space-y-6">
              <h2 className="text-2xl font-semibold mb-4">Dados do Pitch</h2>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Título do Pitch *</label>
                <input
                  type="text"
                  value={pitch.titulo}
                  onChange={(e) => setPitch({ ...pitch, titulo: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  required
                  data-testid="pitch-title-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Problema *</label>
                <textarea
                  value={pitch.problema}
                  onChange={(e) => setPitch({ ...pitch, problema: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  rows={3}
                  required
                  data-testid="pitch-problem-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Solução *</label>
                <textarea
                  value={pitch.solucao}
                  onChange={(e) => setPitch({ ...pitch, solucao: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  rows={3}
                  required
                  data-testid="pitch-solution-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Mercado *</label>
                <textarea
                  value={pitch.mercado}
                  onChange={(e) => setPitch({ ...pitch, mercado: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  rows={3}
                  required
                  data-testid="pitch-market-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Modelo de Negócio *</label>
                <textarea
                  value={pitch.modelo_negocio}
                  onChange={(e) => setPitch({ ...pitch, modelo_negocio: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  rows={3}
                  required
                  data-testid="pitch-business-model-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Tração *</label>
                <textarea
                  value={pitch.tracao}
                  onChange={(e) => setPitch({ ...pitch, tracao: e.target.value })}
                  className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                  rows={3}
                  required
                  data-testid="pitch-traction-input"
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Valor do Pedido</label>
                  <input
                    type="text"
                    value={pitch.pedido_valor}
                    onChange={(e) => setPitch({ ...pitch, pedido_valor: e.target.value })}
                    className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                    placeholder="Ex: R$ 500.000"
                    data-testid="pitch-investment-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">% Equity</label>
                  <input
                    type="text"
                    value={pitch.pedido_equity}
                    onChange={(e) => setPitch({ ...pitch, pedido_equity: e.target.value })}
                    className="w-full px-4 py-3 bg-black border border-gray-700 rounded text-white"
                    placeholder="Ex: 10%"
                    data-testid="pitch-equity-input"
                  />
                </div>
              </div>
            </div>

            {/* Panel Selection */}
            <div className="spotlight rounded-lg p-8 space-y-6">
              <h2 className="text-2xl font-semibold mb-4">Painel de Investidores</h2>

              <div className="flex items-center gap-4 mb-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={useRandom}
                    onChange={() => setUseRandom(true)}
                    className="w-4 h-4"
                    data-testid="random-panel-radio"
                  />
                  <span className="text-gray-300">Todos os 4 sharks (padrão)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={!useRandom}
                    onChange={() => setUseRandom(false)}
                    className="w-4 h-4"
                    data-testid="custom-panel-radio"
                  />
                  <span className="text-gray-300">Selecionar 4 sharks</span>
                </label>
              </div>

              {!useRandom && (
                <div className="grid md:grid-cols-2 gap-4">
                  {sharks.map((shark) => (
                    <div
                      key={shark.id}
                      onClick={() => toggleShark(shark.name)}
                      className={`panel-seat rounded-lg p-4 cursor-pointer ${
                        selectedSharks.includes(shark.name) ? 'border-white' : ''
                      }`}
                      data-testid={`shark-option-${shark.id}`}
                    >
                      <h3 className="text-white font-semibold mb-1">{shark.name}</h3>
                      <p className="text-xs text-gray-400">{shark.tese}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Options */}
            <div className="spotlight rounded-lg p-8">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={readingHints}
                  onChange={(e) => setReadingHints(e.target.checked)}
                  className="w-5 h-5"
                  data-testid="reading-hints-checkbox"
                />
                <div>
                  <span className="text-white font-medium">Dicas de leitura de mesa</span>
                  <p className="text-xs text-gray-400 mt-1">
                    Pistas curtas de temperamento/engajamento (opcional)
                  </p>
                </div>
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-4 bg-white text-black font-semibold rounded hover:bg-gray-200 disabled:opacity-50"
              data-testid="create-session-button"
            >
              {loading ? 'Criando...' : 'Criar Sessão'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewSession;