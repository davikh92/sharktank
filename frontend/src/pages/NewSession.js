import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSharks, createSession } from '../api';
import { toast } from 'sonner';

// Dicas e recomendações para cada campo
const fieldTips = {
  titulo: {
    placeholder: "Ex: FoodTech - Delivery para Restaurantes Premium",
    tip: "Seja específico. Inclua o setor e o que faz.",
    examples: ["FinTech para PMEs", "HealthTech - Telemedicina", "EdTech B2B"]
  },
  problema: {
    placeholder: "Descreva a dor real do seu cliente...",
    tip: "Foque em UMA dor principal. Seja específico sobre quem sofre e quanto custa.",
    guide: "Quem sofre? Quanto custa? Com que frequência?"
  },
  solucao: {
    placeholder: "Como seu produto resolve o problema...",
    tip: "Mostre o 'antes e depois'. O que muda na vida do cliente?",
    guide: "O que é? Como funciona? Qual o diferencial?"
  },
  mercado: {
    placeholder: "Ex: Mercado de R$ 50 bilhões, 10.000 empresas potenciais...",
    tip: "TAM, SAM, SOM. Números específicos impressionam mais.",
    guide: "Tamanho total → Mercado endereçável → Meta de 3 anos"
  },
  modelo_negocio: {
    placeholder: "Ex: SaaS com assinatura mensal de R$ 500/mês...",
    tip: "Seja claro sobre como ganha dinheiro. Inclua ticket médio.",
    guide: "Como cobra? Quanto? Recorrência?"
  },
  tracao: {
    placeholder: "Ex: 50 clientes pagantes, R$ 30k MRR, crescendo 15% ao mês...",
    tip: "Números reais > promessas. MRR, clientes, crescimento mensal.",
    guide: "Clientes • Receita • Crescimento • Retenção"
  }
};

// Indicador de força do pitch
const PitchStrengthIndicator = ({ pitch }) => {
  const analysis = useMemo(() => {
    let score = 0;
    let feedback = [];
    
    // Título
    if (pitch.titulo.length > 10) score += 10;
    
    // Problema
    if (pitch.problema.length > 50) score += 15;
    if (pitch.problema.includes('R$') || pitch.problema.includes('%')) {
      score += 5;
      feedback.push({ type: 'good', text: 'Problema quantificado' });
    }
    
    // Solução
    if (pitch.solucao.length > 50) score += 15;
    
    // Mercado
    if (pitch.mercado.length > 30) score += 10;
    if (pitch.mercado.match(/\d+/) && (pitch.mercado.includes('bilh') || pitch.mercado.includes('milh'))) {
      score += 10;
      feedback.push({ type: 'good', text: 'Mercado dimensionado' });
    }
    
    // Modelo de negócio
    if (pitch.modelo_negocio.length > 30) score += 10;
    if (pitch.modelo_negocio.match(/R\$\s*[\d.,]+/)) {
      score += 5;
      feedback.push({ type: 'good', text: 'Ticket médio definido' });
    }
    
    // Tração
    if (pitch.tracao.length > 30) score += 10;
    if (pitch.tracao.match(/\d+/) && (pitch.tracao.includes('cliente') || pitch.tracao.includes('MRR') || pitch.tracao.includes('usuário'))) {
      score += 10;
      feedback.push({ type: 'good', text: 'Métricas de tração' });
    }
    
    // Pedido
    if (pitch.pedido_valor && pitch.pedido_equity) {
      score += 10;
      
      // Calcular valuation implícito
      const valorMatch = pitch.pedido_valor.match(/[\d.,]+/);
      const equityMatch = pitch.pedido_equity.match(/[\d.,]+/);
      
      if (valorMatch && equityMatch) {
        const valor = parseFloat(valorMatch[0].replace(/[.,]/g, ''));
        const equity = parseFloat(equityMatch[0].replace(',', '.'));
        if (equity > 0) {
          const valuation = (valor / (equity / 100));
          feedback.push({ 
            type: 'info', 
            text: `Valuation implícito: R$ ${(valuation / 1000000).toFixed(1)}M` 
          });
        }
      }
    }
    
    // Warnings
    if (pitch.problema.length > 0 && pitch.problema.length < 50) {
      feedback.push({ type: 'warn', text: 'Problema pouco detalhado' });
    }
    if (pitch.tracao.length > 0 && !pitch.tracao.match(/\d+/)) {
      feedback.push({ type: 'warn', text: 'Tração sem números' });
    }
    
    return { score: Math.min(score, 100), feedback };
  }, [pitch]);

  const getScoreColor = (score) => {
    if (score < 30) return 'bg-red-500';
    if (score < 60) return 'bg-yellow-500';
    if (score < 80) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getScoreLabel = (score) => {
    if (score < 30) return 'Fraco';
    if (score < 60) return 'Moderado';
    if (score < 80) return 'Bom';
    return 'Forte';
  };

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-zinc-400">Força do Pitch</span>
        <span className={`text-sm font-medium ${
          analysis.score < 30 ? 'text-red-400' :
          analysis.score < 60 ? 'text-yellow-400' :
          analysis.score < 80 ? 'text-blue-400' : 'text-green-400'
        }`}>
          {getScoreLabel(analysis.score)} ({analysis.score}%)
        </span>
      </div>
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden mb-3">
        <div 
          className={`h-full ${getScoreColor(analysis.score)} transition-all duration-500`}
          style={{ width: `${analysis.score}%` }}
        />
      </div>
      {analysis.feedback.length > 0 && (
        <div className="space-y-1">
          {analysis.feedback.map((fb, idx) => (
            <div key={idx} className={`text-xs flex items-center gap-2 ${
              fb.type === 'good' ? 'text-green-400' :
              fb.type === 'warn' ? 'text-yellow-400' : 'text-zinc-400'
            }`}>
              <span>{fb.type === 'good' ? '✓' : fb.type === 'warn' ? '⚠' : 'ℹ'}</span>
              <span>{fb.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Campo de input melhorado
const PitchField = ({ label, name, value, onChange, multiline = false, required = true, pitch }) => {
  const tip = fieldTips[name];
  const [showTip, setShowTip] = useState(false);
  
  const charCount = value.length;
  const isGoodLength = charCount >= 50;
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm text-gray-300 font-medium">
          {label} {required && <span className="text-red-400">*</span>}
        </label>
        <button
          type="button"
          onClick={() => setShowTip(!showTip)}
          className="text-xs text-zinc-500 hover:text-zinc-300"
        >
          {showTip ? 'Ocultar dica' : 'Ver dica'}
        </button>
      </div>
      
      {showTip && tip && (
        <div className="bg-zinc-800/50 border border-zinc-700 rounded p-3 text-xs space-y-1">
          <p className="text-zinc-300">{tip.tip}</p>
          {tip.guide && <p className="text-zinc-500 italic">{tip.guide}</p>}
          {tip.examples && (
            <p className="text-zinc-500">
              Ex: {tip.examples.join(' | ')}
            </p>
          )}
        </div>
      )}
      
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-zinc-700 rounded text-white placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none transition-colors"
          rows={3}
          placeholder={tip?.placeholder}
          required={required}
          data-testid={`pitch-${name}-input`}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-zinc-700 rounded text-white placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none transition-colors"
          placeholder={tip?.placeholder}
          required={required}
          data-testid={`pitch-${name}-input`}
        />
      )}
      
      {multiline && (
        <div className="flex justify-between text-xs">
          <span className={charCount > 0 ? (isGoodLength ? 'text-green-500' : 'text-yellow-500') : 'text-zinc-600'}>
            {charCount > 0 && (isGoodLength ? '✓ Bom tamanho' : 'Detalhe mais')}
          </span>
          <span className="text-zinc-600">{charCount} caracteres</span>
        </div>
      )}
    </div>
  );
};

// Card do Shark melhorado
const SharkCard = ({ shark, selected, onToggle, disabled }) => {
  const archetypeIcons = {
    'O Operador': '⚙️',
    'O Financeiro': '📊',
    'O Cético': '🔍',
    'O Visionário': '🚀'
  };

  const archetypeColors = {
    'O Operador': 'border-blue-500/50 bg-blue-900/20',
    'O Financeiro': 'border-green-500/50 bg-green-900/20',
    'O Cético': 'border-orange-500/50 bg-orange-900/20',
    'O Visionário': 'border-purple-500/50 bg-purple-900/20'
  };

  return (
    <div
      onClick={() => !disabled && onToggle(shark.name)}
      className={`relative rounded-lg p-5 cursor-pointer transition-all duration-300 border-2 ${
        selected 
          ? archetypeColors[shark.name] || 'border-white/50 bg-white/10'
          : 'border-zinc-700/50 bg-zinc-900/30 hover:border-zinc-600'
      } ${disabled && !selected ? 'opacity-50 cursor-not-allowed' : ''}`}
      data-testid={`shark-option-${shark.id}`}
    >
      {selected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center">
          <span className="text-black text-sm">✓</span>
        </div>
      )}
      
      <div className="flex items-start gap-3">
        <div className="text-3xl">{archetypeIcons[shark.name] || '👤'}</div>
        <div className="flex-1">
          <h3 className="text-white font-semibold mb-1">{shark.name}</h3>
          <p className="text-xs text-zinc-400 mb-2">{shark.tese}</p>
          <div className="flex flex-wrap gap-1">
            {shark.foco && shark.foco.slice(0, 3).map((item, idx) => (
              <span key={idx} className="text-xs px-2 py-0.5 bg-zinc-800 rounded text-zinc-400">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const NewSession = () => {
  const [sharks, setSharks] = useState([]);
  const [selectedSharks, setSelectedSharks] = useState([]);
  const [useRandom, setUseRandom] = useState(true);
  const [readingHints, setReadingHints] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(1);
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

  const handlePitchChange = (field, value) => {
    setPitch(prev => ({ ...prev, [field]: value }));
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

  const canSubmit = useMemo(() => {
    const requiredFields = ['titulo', 'problema', 'solucao', 'mercado', 'modelo_negocio', 'tracao'];
    const allFilled = requiredFields.every(field => pitch[field].trim().length > 0);
    const sharksOk = useRandom || selectedSharks.length === 4;
    return allFilled && sharksOk;
  }, [pitch, useRandom, selectedSharks]);

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
      toast.success('Sessão criada! Prepare-se para as perguntas difíceis...');
      navigate(`/sessions/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar sessão');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="studio-background min-h-screen">
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-5xl mx-auto">
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
              className="text-4xl font-bold mb-2"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
              data-testid="new-session-title"
            >
              Prepare seu Pitch
            </h1>
            <p className="text-gray-500">
              Quanto mais detalhado, mais realistas serão as perguntas dos investidores.
            </p>
          </div>

          {/* Steps indicator */}
          <div className="flex items-center gap-2 mb-8">
            <button
              onClick={() => setActiveStep(1)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeStep === 1 ? 'bg-white text-black' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              <span className="w-6 h-6 rounded-full bg-current/20 flex items-center justify-center text-sm">1</span>
              <span className="text-sm font-medium">Pitch</span>
            </button>
            <div className="w-8 h-px bg-zinc-700" />
            <button
              onClick={() => setActiveStep(2)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeStep === 2 ? 'bg-white text-black' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              <span className="w-6 h-6 rounded-full bg-current/20 flex items-center justify-center text-sm">2</span>
              <span className="text-sm font-medium">Painel</span>
            </button>
            <div className="w-8 h-px bg-zinc-700" />
            <button
              onClick={() => setActiveStep(3)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeStep === 3 ? 'bg-white text-black' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              <span className="w-6 h-6 rounded-full bg-current/20 flex items-center justify-center text-sm">3</span>
              <span className="text-sm font-medium">Revisar</span>
            </button>
          </div>

          <form onSubmit={handleSubmit} data-testid="new-session-form">
            {/* Step 1: Pitch Data */}
            {activeStep === 1 && (
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Main form */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-6 space-y-6">
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                      <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm">📝</span>
                      Dados do Pitch
                    </h2>

                    <PitchField
                      label="Nome do Negócio"
                      name="titulo"
                      value={pitch.titulo}
                      onChange={handlePitchChange}
                      pitch={pitch}
                    />

                    <PitchField
                      label="Problema"
                      name="problema"
                      value={pitch.problema}
                      onChange={handlePitchChange}
                      multiline
                      pitch={pitch}
                    />

                    <PitchField
                      label="Solução"
                      name="solucao"
                      value={pitch.solucao}
                      onChange={handlePitchChange}
                      multiline
                      pitch={pitch}
                    />

                    <PitchField
                      label="Mercado"
                      name="mercado"
                      value={pitch.mercado}
                      onChange={handlePitchChange}
                      multiline
                      pitch={pitch}
                    />

                    <PitchField
                      label="Modelo de Negócio"
                      name="modelo_negocio"
                      value={pitch.modelo_negocio}
                      onChange={handlePitchChange}
                      multiline
                      pitch={pitch}
                    />

                    <PitchField
                      label="Tração"
                      name="tracao"
                      value={pitch.tracao}
                      onChange={handlePitchChange}
                      multiline
                      pitch={pitch}
                    />
                  </div>

                  {/* Investment ask */}
                  <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-6">
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2 mb-4">
                      <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm">💰</span>
                      Pedido de Investimento
                    </h2>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-300 mb-2">Valor</label>
                        <input
                          type="text"
                          value={pitch.pedido_valor}
                          onChange={(e) => handlePitchChange('pedido_valor', e.target.value)}
                          className="w-full px-4 py-3 bg-black/50 border border-zinc-700 rounded text-white placeholder:text-zinc-600"
                          placeholder="Ex: R$ 500.000"
                          data-testid="pitch-investment-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-2">Equity oferecido</label>
                        <input
                          type="text"
                          value={pitch.pedido_equity}
                          onChange={(e) => handlePitchChange('pedido_equity', e.target.value)}
                          className="w-full px-4 py-3 bg-black/50 border border-zinc-700 rounded text-white placeholder:text-zinc-600"
                          placeholder="Ex: 10%"
                          data-testid="pitch-equity-input"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-zinc-500 mt-3">
                      Dica: Valuation implícito muito alto pode gerar resistência. Muito baixo pode parecer desespero.
                    </p>
                  </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                  <PitchStrengthIndicator pitch={pitch} />
                  
                  <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-zinc-300 mb-3">O que os sharks vão avaliar:</h3>
                    <ul className="space-y-2 text-xs text-zinc-500">
                      <li className="flex items-start gap-2">
                        <span className="text-blue-400">●</span>
                        <span>Clareza do problema e solução</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400">●</span>
                        <span>Tamanho e potencial do mercado</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-yellow-400">●</span>
                        <span>Modelo de receita e unit economics</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-400">●</span>
                        <span>Tração e métricas reais</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">●</span>
                        <span>Diferencial competitivo defensável</span>
                      </li>
                    </ul>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveStep(2)}
                    className="w-full px-4 py-3 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 transition-colors"
                  >
                    Próximo: Painel →
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Panel Selection */}
            {activeStep === 2 && (
              <div className="space-y-6">
                <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-6">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2 mb-4">
                    <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm">👥</span>
                    Painel de Investidores
                  </h2>

                  <div className="flex items-center gap-4 mb-6 p-4 bg-zinc-800/50 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        checked={useRandom}
                        onChange={() => setUseRandom(true)}
                        className="w-4 h-4 accent-white"
                        data-testid="random-panel-radio"
                      />
                      <div>
                        <span className="text-white font-medium">Painel completo</span>
                        <p className="text-xs text-zinc-500">Todos os 4 arquétipos (recomendado)</p>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        checked={!useRandom}
                        onChange={() => setUseRandom(false)}
                        className="w-4 h-4 accent-white"
                        data-testid="custom-panel-radio"
                      />
                      <div>
                        <span className="text-white font-medium">Personalizar</span>
                        <p className="text-xs text-zinc-500">Escolha 4 investidores</p>
                      </div>
                    </label>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    {sharks.map((shark) => (
                      <SharkCard
                        key={shark.id}
                        shark={shark}
                        selected={useRandom || selectedSharks.includes(shark.name)}
                        onToggle={toggleShark}
                        disabled={useRandom}
                      />
                    ))}
                  </div>

                  {!useRandom && (
                    <div className="mt-4 text-sm text-zinc-400">
                      Selecionados: {selectedSharks.length}/4
                      {selectedSharks.length < 4 && (
                        <span className="text-yellow-500 ml-2">
                          (selecione mais {4 - selectedSharks.length})
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Options */}
                <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-6">
                  <label className="flex items-center gap-4 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={readingHints}
                      onChange={(e) => setReadingHints(e.target.checked)}
                      className="w-5 h-5 accent-white"
                      data-testid="reading-hints-checkbox"
                    />
                    <div>
                      <span className="text-white font-medium">Dicas de leitura de mesa</span>
                      <p className="text-xs text-zinc-500 mt-1">
                        Receba pistas sutis sobre o humor e engajamento dos investidores (modo mais fácil)
                      </p>
                    </div>
                  </label>
                </div>

                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={() => setActiveStep(1)}
                    className="px-6 py-3 border border-zinc-700 text-zinc-400 rounded-lg hover:border-zinc-500"
                  >
                    ← Voltar
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveStep(3)}
                    className="flex-1 px-6 py-3 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700"
                  >
                    Revisar →
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Review */}
            {activeStep === 3 && (
              <div className="space-y-6">
                <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-6">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2 mb-6">
                    <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm">✓</span>
                    Revisar e Iniciar
                  </h2>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Pitch summary */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">Seu Pitch</h3>
                      <div className="space-y-3">
                        <div>
                          <span className="text-xs text-zinc-500">Negócio</span>
                          <p className="text-white">{pitch.titulo || '-'}</p>
                        </div>
                        <div>
                          <span className="text-xs text-zinc-500">Problema</span>
                          <p className="text-zinc-300 text-sm line-clamp-2">{pitch.problema || '-'}</p>
                        </div>
                        <div>
                          <span className="text-xs text-zinc-500">Mercado</span>
                          <p className="text-zinc-300 text-sm line-clamp-2">{pitch.mercado || '-'}</p>
                        </div>
                        <div>
                          <span className="text-xs text-zinc-500">Pedido</span>
                          <p className="text-green-400 font-medium">
                            {pitch.pedido_valor || '?'} por {pitch.pedido_equity || '?'}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Panel summary */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">Seu Painel</h3>
                      <div className="space-y-2">
                        {(useRandom ? sharks : sharks.filter(s => selectedSharks.includes(s.name))).map(shark => (
                          <div key={shark.id} className="flex items-center gap-3 py-2 border-b border-zinc-800 last:border-0">
                            <span className="text-xl">
                              {shark.name === 'O Operador' && '⚙️'}
                              {shark.name === 'O Financeiro' && '📊'}
                              {shark.name === 'O Cético' && '🔍'}
                              {shark.name === 'O Visionário' && '🚀'}
                            </span>
                            <div>
                              <p className="text-white text-sm">{shark.name}</p>
                              <p className="text-xs text-zinc-500">{shark.tese}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {readingHints && (
                        <div className="text-xs text-yellow-500/80 bg-yellow-900/20 px-3 py-2 rounded">
                          ⚡ Dicas de leitura ativadas (modo mais fácil)
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Warning */}
                <div className="bg-red-900/20 border border-red-900/50 rounded-lg p-4">
                  <p className="text-red-300 text-sm">
                    ⚠️ <strong>Aviso:</strong> Os investidores serão duros. Eles vão questionar cada número, 
                    cada premissa, cada decisão. Se você não tiver resposta, eles vão perceber. 
                    Esteja preparado para defender seu negócio.
                  </p>
                </div>

                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={() => setActiveStep(2)}
                    className="px-6 py-3 border border-zinc-700 text-zinc-400 rounded-lg hover:border-zinc-500"
                  >
                    ← Voltar
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !canSubmit}
                    className="flex-1 px-6 py-4 bg-white text-black font-bold rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    data-testid="create-session-button"
                  >
                    {loading ? 'Preparando painel...' : 'Entrar na Sala →'}
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewSession;
