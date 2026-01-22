import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

const Landing = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  React.useEffect(() => {
    if (user) {
      navigate('/sessions');
    }
  }, [user, navigate]);

  return (
    <div className="studio-background vignette min-h-screen">
      <div className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto">
          {/* Hero */}
          <div className="text-center mb-16">
            <h1 
              className="text-6xl md:text-7xl font-bold mb-6 tracking-tight"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
              data-testid="landing-title"
            >
              Investor Panel Simulator
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Simulação realista de um painel de investidores. Sem modo fácil. Apenas o modo difícil.
            </p>
          </div>

          {/* Features */}
          <div className="spotlight rounded-lg p-12 mb-12">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <div className="w-2 h-2 bg-gray-600 rounded-full" />
                <p className="text-gray-300">
                  <span className="font-semibold text-white">4 investidores autônomos</span> com teses e personalidades distintas
                </p>
              </div>
              <div className="space-y-3">
                <div className="w-2 h-2 bg-gray-600 rounded-full" />
                <p className="text-gray-300">
                  <span className="font-semibold text-white">Interrupções e saídas reais</span> baseadas no desempenho
                </p>
              </div>
              <div className="space-y-3">
                <div className="w-2 h-2 bg-gray-600 rounded-full" />
                <p className="text-gray-300">
                  <span className="font-semibold text-white">Relatório factual</span> sem recomendações, apenas fatos observáveis
                </p>
              </div>
              <div className="space-y-3">
                <div className="w-2 h-2 bg-gray-600 rounded-full" />
                <p className="text-gray-300">
                  <span className="font-semibold text-white">Sem final feliz garantido</span> - pode não haver investimento
                </p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center">
            <button
              onClick={() => navigate('/auth')}
              className="px-12 py-4 bg-white text-black font-semibold rounded-sm hover:bg-gray-200 transition-all"
              data-testid="start-button"
            >
              Iniciar Sessão
            </button>
            <p className="mt-4 text-sm text-gray-500">
              Sessões ilimitadas • Relatórios completos gratuitos
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;