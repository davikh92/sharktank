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
        // Relatório não existe, tentar gerar
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
        <div className="text-gray-400">
          {generating ? 'Gerando relatório...' : 'Carregando...'}
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
            className="text-gray-400 hover:text-white mb-4"
            data-testid="back-to-session-button"
          >
            ← Voltar para Sessão
          </button>
          <h1 
            className="text-5xl font-bold mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
            data-testid="report-title"
          >
            Relatório Factual
          </h1>
          <p className="text-gray-400">
            Análise objetiva da sessão. Sem recomendações, apenas fatos observáveis.
          </p>
        </div>

        {/* Report Content */}
        <div className="bg-white text-black rounded-lg p-12 space-y-12">
          {/* 1. Síntese */}
          <section data-testid="report-sintese">
            <h2 className="text-2xl font-bold mb-3 border-b border-gray-300 pb-2">
              Síntese da Sessão
            </h2>
            <p className="text-lg text-gray-800">{report.sintese}</p>
          </section>

          {/* 2. Linha do Tempo */}
          <section data-testid="report-timeline">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Linha do Tempo
            </h2>
            <div className="space-y-3">
              {report.linha_tempo.map((item, idx) => (
                <div key={idx} className="flex gap-4 border-l-2 border-gray-300 pl-4">
                  <div className="text-sm font-mono text-gray-600 min-w-[80px]">
                    {item.momento}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-800">{item.evento}</p>
                    <p className="text-sm text-gray-600">{item.ator}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 3. Leitura dos Sharks */}
          <section data-testid="report-sharks">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Leitura Individual dos Investidores
            </h2>
            <div className="space-y-6">
              {report.leitura_sharks.map((shark, idx) => (
                <div key={idx} className="bg-gray-50 rounded p-6">
                  <h3 className="text-xl font-bold mb-3 text-gray-900">
                    {shark.shark}
                  </h3>
                  <div className="space-y-2 text-gray-700">
                    <p><strong>O que buscava:</strong> {shark.o_que_buscava}</p>
                    <p><strong>O que encontrou:</strong> {shark.o_que_encontrou}</p>
                    <p><strong>Perguntas feitas:</strong> {shark.perguntas_feitas}</p>
                    <p>
                      <strong>Resultado:</strong>{' '}
                      <span className={shark.resultado === 'Saiu' ? 'text-red-600' : 'text-green-600'}>
                        {shark.resultado}
                      </span>
                    </p>
                    {shark.resultado === 'Saiu' && shark.momento_saida && (
                      <p className="text-sm text-gray-600">
                        Saiu em: {new Date(shark.momento_saida).toLocaleString('pt-BR')}
                      </p>
                    )}
                    <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                      <p>Interesse final: {shark.interesse_final.toFixed(0)}/100</p>
                      <p>Paciência final: {shark.paciencia_final.toFixed(0)}/100</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 4. Sinais de Mesa */}
          <section data-testid="report-sinais">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Sinais de Mesa (Não Verbais)
            </h2>
            <ul className="space-y-2">
              {report.sinais_mesa.map((sinal, idx) => (
                <li key={idx} className="flex gap-3">
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-800">{sinal}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* 5. Padrões do Apresentador */}
          <section data-testid="report-padroes">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Padrões Detectados no Apresentador
            </h2>
            <ul className="space-y-2">
              {report.padroes_apresentador.map((padrao, idx) => (
                <li key={idx} className="flex gap-3">
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-800">{padrao}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* 6. Pontos de Sustentação */}
          <section data-testid="report-sustentacao">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Pontos de Sustentação
            </h2>
            <ul className="space-y-2">
              {report.pontos_sustentacao.map((ponto, idx) => (
                <li key={idx} className="flex gap-3">
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-800">{ponto}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* 7. Veredito */}
          <section data-testid="report-veredito">
            <h2 className="text-2xl font-bold mb-4 border-b border-gray-300 pb-2">
              Veredito Final
            </h2>
            <p className="text-lg text-gray-800 font-medium">{report.veredito}</p>
          </section>

          {/* Footer */}
          <div className="text-center pt-8 border-t border-gray-300">
            <p className="text-sm text-gray-500">
              Relatório gerado em {new Date(report.generated_at).toLocaleString('pt-BR')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Report;
