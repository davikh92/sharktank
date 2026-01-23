import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReport, generateReport } from '../api';
import { toast } from 'sonner';

const Report = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadReport();
  }, [sessionId]);

  const loadReport = async () => {
    try {
      const response = await getReport(sessionId);
      setReport(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        handleGenerateReport();
      } else {
        toast.error('Erro ao carregar relatório');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const response = await generateReport(sessionId);
      setReport(response.data);
      toast.success('Relatório gerado');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao gerar relatório');
    } finally {
      setGenerating(false);
    }
  };

  if (loading || generating) {
    return (
      <div className="studio-background min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4" />
          <div className="text-gray-400">
            {generating ? 'Gerando autópsia da sessão...' : 'Carregando...'}
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="studio-background min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Relatório não disponível</p>
          <button
            onClick={() => navigate(`/sessions/${sessionId}`)}
            className="px-6 py-2 bg-white text-black rounded hover:bg-gray-200"
          >
            Voltar para Sessão
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="studio-background min-h-screen" data-testid="report-page">
      <div className="container mx-auto px-6 py-12 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/sessions/${sessionId}`)}
            className="text-gray-400 hover:text-white mb-4 flex items-center gap-2"
            data-testid="back-to-session-button"
          >
            <span>←</span> Voltar para Sessão
          </button>
          <h1 
            className="text-5xl font-bold mb-2"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
            data-testid="report-title"
          >
            Autópsia da Sessão
          </h1>
          <p className="text-gray-500 text-sm">
            Não te diz se foi bem ou mal. Te mostra onde perdeu, onde ganhou, e o que ficou sem resposta.
          </p>
        </div>

        {/* Report Content */}
        <div className="space-y-8">
          
          {/* Síntese - Card destacado */}
          <section 
            className="bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700 rounded-lg p-8"
            data-testid="report-sintese"
          >
            <p className="text-xl text-gray-200 leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              "{report.sintese}"
            </p>
          </section>

          {/* AUTÓPSIA - Perguntas-chave */}
          {report.autopsia && (
            <section 
              className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-8"
              data-testid="report-autopsia"
            >
              <h2 className="text-2xl font-bold mb-6 text-white border-b border-zinc-700 pb-3">
                As Perguntas Que Importam
              </h2>
              
              <div className="space-y-6">
                {/* Momento Irreversível */}
                {report.autopsia.momento_irreversivel && (
                  <div className="border-l-2 border-red-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-red-400/80 mb-1">
                      Qual foi o momento irreversível?
                    </p>
                    <p className="text-gray-300">{report.autopsia.momento_irreversivel}</p>
                  </div>
                )}

                {/* Primeiro Shark Perdido */}
                {report.autopsia.primeiro_shark_perdido && (
                  <div className="border-l-2 border-orange-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-orange-400/80 mb-1">
                      Qual shark você perdeu primeiro — e por quê?
                    </p>
                    <p className="text-gray-300">{report.autopsia.primeiro_shark_perdido}</p>
                  </div>
                )}

                {/* Pergunta Não Respondida */}
                {report.autopsia.pergunta_nao_respondida && (
                  <div className="border-l-2 border-yellow-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-yellow-400/80 mb-1">
                      O que você nunca respondeu de verdade?
                    </p>
                    <p className="text-gray-300">{report.autopsia.pergunta_nao_respondida}</p>
                  </div>
                )}

                {/* Onde Perdeu Tração */}
                {report.autopsia.onde_perdeu_tracao && (
                  <div className="border-l-2 border-zinc-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-zinc-400/80 mb-1">
                      Onde você perdeu tração?
                    </p>
                    <p className="text-gray-300">{report.autopsia.onde_perdeu_tracao}</p>
                  </div>
                )}

                {/* Onde Ganhou Respeito */}
                {report.autopsia.onde_ganhou_respeito && (
                  <div className="border-l-2 border-green-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-green-400/80 mb-1">
                      Onde você ganhou respeito?
                    </p>
                    <p className="text-gray-300">{report.autopsia.onde_ganhou_respeito}</p>
                  </div>
                )}

                {/* Risco Desnecessário */}
                {report.autopsia.risco_desnecessario && (
                  <div className="border-l-2 border-purple-500/50 pl-4">
                    <p className="text-xs uppercase tracking-wider text-purple-400/80 mb-1">
                      Onde tomou risco desnecessário?
                    </p>
                    <p className="text-gray-300">{report.autopsia.risco_desnecessario}</p>
                  </div>
                )}

                {/* Decisão Que Matou */}
                {report.autopsia.decisao_que_matou && (
                  <div className="border-l-2 border-red-600/50 pl-4 bg-red-900/10 py-2 -ml-1 pl-5">
                    <p className="text-xs uppercase tracking-wider text-red-400 mb-1">
                      Qual decisão matou o jogo?
                    </p>
                    <p className="text-red-200 font-medium">{report.autopsia.decisao_que_matou}</p>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* MICRO-SINAIS - Comportamentos não verbais */}
          {report.micro_sinais && report.micro_sinais.length > 0 && (
            <section 
              className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-8"
              data-testid="report-micro-sinais"
            >
              <h2 className="text-2xl font-bold mb-2 text-white">
                O Que Não Foi Dito
              </h2>
              <p className="text-gray-500 text-sm mb-6">Micro-sinais observados durante a sessão</p>
              
              <div className="space-y-3">
                {report.micro_sinais.map((sinal, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-start gap-4 py-2 border-b border-zinc-800/50 last:border-0"
                  >
                    <div className="text-xs font-mono text-zinc-600 min-w-[60px]">
                      T{sinal.turno}
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-300">
                        <span className="text-white font-medium">{sinal.shark}</span>
                        {' '}{sinal.sinal}
                      </p>
                    </div>
                    <div className="text-xs text-zinc-500 italic min-w-[140px] text-right">
                      {sinal.traducao_psicologica}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Linha do Tempo da Negociação */}
          {report.linha_tempo && report.linha_tempo.length > 0 && (
            <section 
              className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-8"
              data-testid="report-timeline"
            >
              <h2 className="text-2xl font-bold mb-6 text-white">
                Linha do Tempo
              </h2>
              <div className="space-y-3">
                {report.linha_tempo.map((item, idx) => (
                  <div key={idx} className="flex gap-4 border-l-2 border-zinc-700 pl-4 py-1">
                    <div className="text-xs font-mono text-zinc-500 min-w-[80px]">
                      {item.tipo === 'OFERTA' && '💰 '}
                      {item.tipo === 'RETIRADA' && '⚠️ '}
                      {item.tipo === 'DEAL' && '🤝 '}
                      {item.tipo === 'SAIDA' && '🚪 '}
                      {item.tipo === 'CONFLITO' && '⚡ '}
                      T{item.turno}
                    </div>
                    <div className="flex-1">
                      <p className={`${
                        item.tipo === 'DEAL' ? 'text-green-400' :
                        item.tipo === 'RETIRADA' ? 'text-red-400' :
                        item.tipo === 'OFERTA' ? 'text-yellow-400' :
                        'text-gray-300'
                      }`}>
                        {item.descricao}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Leitura dos Sharks */}
          <section 
            className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-8"
            data-testid="report-sharks"
          >
            <h2 className="text-2xl font-bold mb-6 text-white">
              O Que Cada Um Pensou
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {report.leitura_sharks.map((shark, idx) => (
                <div 
                  key={idx} 
                  className={`rounded-lg p-5 border ${
                    shark.fechou_deal 
                      ? 'bg-green-900/20 border-green-800/50' 
                      : shark.resultado === 'Saiu' 
                        ? 'bg-red-900/10 border-red-900/30' 
                        : 'bg-zinc-800/30 border-zinc-700/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold text-white">
                      {shark.shark}
                    </h3>
                    <span className={`text-xs px-2 py-1 rounded ${
                      shark.fechou_deal 
                        ? 'bg-green-500/20 text-green-400' 
                        : shark.resultado === 'Saiu' 
                          ? 'bg-red-500/20 text-red-400'
                          : shark.fez_oferta
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-zinc-700 text-zinc-400'
                    }`}>
                      {shark.resultado}
                    </span>
                  </div>
                  
                  <p className="text-sm text-zinc-400 mb-3">
                    <span className="text-zinc-500">Buscava:</span> {shark.o_que_buscava}
                  </p>
                  
                  <p className="text-sm text-gray-300 italic mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                    "{shark.o_que_pensou}"
                  </p>
                  
                  {/* Barras de confiança */}
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-xs text-zinc-500 mb-1">
                        <span>Confiança na Ideia</span>
                        <span>{shark.confianca_ideia?.toFixed(0) || 50}/100</span>
                      </div>
                      <div className="h-1 bg-zinc-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${shark.confianca_ideia || 50}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-zinc-500 mb-1">
                        <span>Confiança na Apresentação</span>
                        <span>{shark.confianca_apresentacao?.toFixed(0) || 50}/100</span>
                      </div>
                      <div className="h-1 bg-zinc-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-purple-500 rounded-full"
                          style={{ width: `${shark.confianca_apresentacao || 50}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Avaliação Ideia vs Apresentação */}
          {report.avaliacao_idea && (
            <section 
              className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-8"
              data-testid="report-avaliacao"
            >
              <h2 className="text-2xl font-bold mb-6 text-white">
                Ideia vs. Apresentação
              </h2>
              
              <div className="grid grid-cols-2 gap-8 mb-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-400 mb-1">
                    {report.avaliacao_idea.idea_score?.toFixed(0) || '—'}
                  </div>
                  <div className="text-xs uppercase tracking-wider text-zinc-500">Score da Ideia</div>
                  <div className="text-sm text-zinc-400 mt-1">
                    ({report.avaliacao_idea.idea_tier || 'N/A'})
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-400 mb-1">
                    {report.avaliacao_idea.apresentacao_score?.toFixed(0) || '—'}
                  </div>
                  <div className="text-xs uppercase tracking-wider text-zinc-500">Score da Apresentação</div>
                </div>
              </div>
              
              <div className="bg-zinc-800/50 rounded p-4">
                <p className="text-gray-300 mb-2">{report.avaliacao_idea.analise}</p>
                <p className="text-sm text-zinc-500">{report.avaliacao_idea.recomendacao}</p>
              </div>
            </section>
          )}

          {/* Momento de Virada */}
          {report.momento_virada && report.momento_virada.houve_virada && (
            <section 
              className="bg-yellow-900/10 border border-yellow-800/30 rounded-lg p-8"
              data-testid="report-momento-virada"
            >
              <h2 className="text-lg font-bold mb-3 text-yellow-400">
                Momento de Virada
              </h2>
              <p className="text-gray-300">{report.momento_virada.descricao}</p>
            </section>
          )}

          {/* Pergunta Provocativa Final */}
          {report.pergunta_provocativa && (
            <section 
              className="bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 border border-zinc-600 rounded-lg p-10 text-center"
              data-testid="report-pergunta-provocativa"
            >
              <p 
                className="text-2xl text-gray-200 leading-relaxed"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                "{report.pergunta_provocativa}"
              </p>
            </section>
          )}

          {/* Footer */}
          <div className="text-center pt-4">
            <p className="text-xs text-zinc-600">
              Gerado em {new Date(report.generated_at).toLocaleString('pt-BR')}
            </p>
          </div>

          {/* CTA */}
          <div className="flex justify-center gap-4 pt-4">
            <button
              onClick={() => navigate('/sessions/new')}
              className="px-8 py-3 bg-white text-black rounded-lg hover:bg-gray-200 font-medium"
              data-testid="new-session-button"
            >
              Tentar Novamente
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-3 border border-zinc-600 text-zinc-400 rounded-lg hover:border-zinc-500 hover:text-zinc-300"
              data-testid="dashboard-button"
            >
              Ver Histórico
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Report;
