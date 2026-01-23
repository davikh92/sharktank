import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

// Componente de seção expandível do guia
const GuideSection = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border-b border-zinc-800 last:border-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-4 flex items-center justify-between text-left hover:bg-zinc-900/30 transition-colors px-2 -mx-2 rounded"
      >
        <span className="text-lg text-white font-medium">{title}</span>
        <span className={`text-zinc-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      <div className={`overflow-hidden transition-all duration-500 ${isOpen ? 'max-h-[2000px] opacity-100 pb-6' : 'max-h-0 opacity-0'}`}>
        <div className="text-gray-400 space-y-4 leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
};

const Landing = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showFullGuide, setShowFullGuide] = useState(false);

  React.useEffect(() => {
    if (user) {
      navigate('/sessions');
    }
  }, [user, navigate]);

  return (
    <div className="studio-background vignette min-h-screen">
      <div className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Hero */}
          <div className="text-center mb-12">
            <h1 
              className="text-5xl md:text-6xl font-bold mb-6 tracking-tight"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
              data-testid="landing-title"
            >
              Investor Panel Simulator
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-8">
              Você não entra aqui para &ldquo;ver se dá certo&rdquo;.
            </p>
            <p className="text-lg text-gray-500 max-w-xl mx-auto">
              Você entra para descobrir se a sua ideia aguenta a mesa.
            </p>
          </div>

          {/* Intro Statement */}
          <div className="spotlight rounded-lg p-8 mb-8 text-center">
            <p className="text-gray-300 text-lg leading-relaxed mb-4">
              Às vezes, você sai sem nada.<br />
              Às vezes, quase fecha.<br />
              E, em raros casos, o painel compra.
            </p>
            <p className="text-gray-400">
              Quando isso acontece, não é sorte. Não é simpatia.<br />
              E definitivamente não é porque o jogo facilitou.
            </p>
            <p className="text-white font-medium mt-4">
              É porque, sob pressão, o que você defendeu se sustentou.
            </p>
          </div>

          {/* CTA Principal */}
          <div className="text-center mb-12">
            <button
              onClick={() => navigate('/auth')}
              className="px-12 py-4 bg-white text-black font-semibold rounded-sm hover:bg-gray-200 transition-all text-lg"
              data-testid="start-button"
            >
              Entrar na Sala
            </button>
            <p className="mt-3 text-sm text-gray-600">
              O painel já está esperando.
            </p>
          </div>

          {/* Guia Expandível */}
          <div className="mt-16">
            <button
              onClick={() => setShowFullGuide(!showFullGuide)}
              className="w-full text-center mb-6 group"
              data-testid="toggle-guide-button"
            >
              <span className="text-zinc-500 text-sm uppercase tracking-wider group-hover:text-zinc-300 transition-colors">
                {showFullGuide ? 'Ocultar guia' : 'Entenda as regras antes de entrar'}
              </span>
              <div className={`mx-auto mt-2 w-8 h-8 flex items-center justify-center text-zinc-600 transition-transform duration-300 ${showFullGuide ? 'rotate-180' : ''}`}>
                ▼
              </div>
            </button>

            <div className={`overflow-hidden transition-all duration-700 ${showFullGuide ? 'max-h-[5000px] opacity-100' : 'max-h-0 opacity-0'}`}>
              <div className="spotlight rounded-lg p-8 space-y-2">
                
                <GuideSection title="Antes de começar" defaultOpen={true}>
                  <p>Este não é um jogo de escolhas certas.</p>
                  <p>E definitivamente não é um simulador de respostas bonitas.</p>
                  <p className="text-white font-medium pt-2">Aqui, ninguém está tentando te ajudar.</p>
                  <p>O painel existe para uma coisa: <span className="text-white">testar se a sua ideia aguenta pressão real.</span></p>
                </GuideSection>

                <GuideSection title="O que isso é (e o que não é)">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-white font-medium mb-2">Isso é:</p>
                      <ul className="space-y-1 text-gray-400">
                        <li>• Uma simulação séria de um painel de investidores</li>
                        <li>• Um ambiente de decisão com tempo, tensão e desgaste</li>
                        <li>• Um teste de clareza, consistência e convicção</li>
                      </ul>
                    </div>
                    <div>
                      <p className="text-white font-medium mb-2">Isso não é:</p>
                      <ul className="space-y-1 text-gray-400">
                        <li>• Um curso de pitch</li>
                        <li>• Um coach de startups</li>
                        <li>• Um jogo com final feliz garantido</li>
                      </ul>
                    </div>
                  </div>
                  <p className="text-yellow-500/80 mt-4 text-sm">Se você procura validação, este não é o lugar.</p>
                </GuideSection>

                <GuideSection title="Como o painel pensa">
                  <p>Cada investidor entra com:</p>
                  <ul className="space-y-1 pl-4">
                    <li>• uma tese própria</li>
                    <li>• limites claros</li>
                    <li>• intolerância a respostas vagas</li>
                  </ul>
                  <p className="text-white mt-4">Eles não avaliam o que você quis dizer.</p>
                  <p>Avaliam o que você sustenta quando é pressionado.</p>
                  <div className="bg-zinc-800/50 rounded p-4 mt-4 text-sm">
                    <p className="text-zinc-300">Silêncios contam.</p>
                    <p className="text-zinc-300">Interrupções contam.</p>
                    <p className="text-white">O que você evita responder conta mais ainda.</p>
                  </div>
                </GuideSection>

                <GuideSection title="Regras que não aparecem na tela">
                  <p>O painel não segue um roteiro.</p>
                  <p>E não reage de forma previsível.</p>
                  <p className="mt-4">Algumas coisas pesam mais do que parecem.</p>
                  <p>Outras parecem importantes… até não serem.</p>
                  <p className="text-white mt-4">Há momentos em que a mesa muda.</p>
                  <p>E normalmente isso acontece antes de você perceber.</p>
                  <p className="text-red-400/80 mt-4">Se alguém sair, não é um evento isolado. É um sinal.</p>
                  <p className="text-zinc-500 text-sm mt-2">O jogo não vai te avisar quando isso acontecer.</p>
                </GuideSection>

                <GuideSection title="Como jogar (sem manual)">
                  <p><span className="text-white">Entre sabendo o que está defendendo.</span></p>
                  <p>Não tente sustentar tudo ao mesmo tempo.</p>
                  <p className="mt-4">Em certos momentos, avançar ajuda.</p>
                  <p>Em outros, insistir afasta.</p>
                  <p className="text-white mt-4">Aqui, o painel respeita quem decide.</p>
                  <p>E perde interesse rápido em quem contorna.</p>
                  <div className="bg-zinc-800/50 rounded p-4 mt-4">
                    <p className="text-zinc-300">Você não precisa dizer tudo.</p>
                    <p className="text-white">Mas o que disser precisa sustentar pressão.</p>
                  </div>
                </GuideSection>

                <GuideSection title="Sobre ganhar e perder">
                  <p>Você pode sair daqui com:</p>
                  <ul className="space-y-1 pl-4 mt-2">
                    <li>• uma oferta</li>
                    <li>• várias ofertas</li>
                    <li>• uma negociação tensa</li>
                    <li>• ou nenhuma proposta</li>
                  </ul>
                  <p className="text-zinc-400 mt-4">Todas são respostas válidas do sistema.</p>
                  <p className="text-white mt-4">O fracasso aqui não é &ldquo;sair sem investimento&rdquo;.</p>
                  <p className="text-red-400/80">O fracasso é não entender por que saiu.</p>
                </GuideSection>

                <GuideSection title="O que acontece depois">
                  <p>Quando a sessão termina, nada é resumido em uma frase simples.</p>
                  <p className="mt-4">O jogo não te diz:</p>
                  <ul className="space-y-1 pl-4 text-zinc-500">
                    <li>• se você foi bem</li>
                    <li>• se foi mal</li>
                    <li>• se &ldquo;quase deu&rdquo;</li>
                  </ul>
                  <p className="text-zinc-400 mt-4">Porque essa não é a pergunta certa.</p>
                  <p className="text-white mt-4">O que fica registrado é o comportamento da mesa.</p>
                  <p className="mt-4">Depois da sessão, o sistema recompõe tudo o que aconteceu:</p>
                  <ul className="space-y-2 pl-4 mt-2 text-zinc-300">
                    <li>• quando a dinâmica começou a mudar</li>
                    <li>• qual decisão alterou o clima da mesa</li>
                    <li>• quem perdeu interesse primeiro — e o que desencadeou isso</li>
                    <li>• quais perguntas voltaram disfarçadas</li>
                    <li>• quais respostas nunca se sustentaram sob pressão</li>
                  </ul>
                  <p className="text-zinc-500 text-sm mt-4 italic">
                    Há coisas que só aparecem quando você sai da arena.
                  </p>
                  <p className="text-zinc-400 mt-2">
                    Durante o jogo, você sente a tensão.<br />
                    Depois, você entende de onde ela veio.
                  </p>
                </GuideSection>

                <GuideSection title="O que o relatório mostra">
                  <p>O relatório não existe para te corrigir.</p>
                  <p>E não existe para te convencer de nada.</p>
                  <p className="text-white mt-4">Ele existe para tornar visível o que, no momento, foi invisível.</p>
                  <p className="mt-4">Você vê:</p>
                  <ul className="space-y-2 pl-4 mt-2 text-zinc-300">
                    <li>• o instante exato em que a mesa deixou de te acompanhar</li>
                    <li>• micro-sinais que indicavam desgaste antes de qualquer saída</li>
                    <li>• temas que drenaram paciência — mesmo quando pareciam inofensivos</li>
                    <li>• decisões evitadas que custaram mais do que erros assumidos</li>
                  </ul>
                  <p className="text-zinc-500 mt-4">
                    Nada vem como recomendação.<br />
                    Nada vem como "faça assim".
                  </p>
                  <p className="text-white mt-2">
                    É um replay factual da sessão —<br />
                    sem edição, sem filtro, sem narrativa heroica.
                  </p>
                </GuideSection>

                <GuideSection title="Por que isso importa">
                  <p>É comum sair de uma sessão achando que sabe exatamente onde errou.</p>
                  <p className="text-white mt-4">Na maioria das vezes, não foi ali.</p>
                  <p className="mt-4">O relatório mostra:</p>
                  <ul className="space-y-2 pl-4 mt-2 text-zinc-300">
                    <li>• o erro que você achou que foi grande — e não foi</li>
                    <li>• o detalhe pequeno que mudou tudo</li>
                    <li>• o momento em que ainda havia margem</li>
                    <li>• e o ponto em que a mesa já tinha ido embora</li>
                  </ul>
                  <p className="text-zinc-400 mt-4">
                    Algumas pessoas leem e confirmam suas suspeitas.<br />
                    Outras descobrem que estavam lutando contra o problema errado.
                  </p>
                  <p className="text-white mt-2">Ambos os casos mudam a próxima tentativa.</p>
                </GuideSection>

                <GuideSection title="Um aviso honesto">
                  <p className="text-yellow-500/80">Nem todo mundo gosta de ver isso.</p>
                  <p className="mt-4">O relatório não suaviza.</p>
                  <p>Não protege.</p>
                  <p>Não tenta te deixar confortável.</p>
                  <p className="text-white mt-4">
                    Ele apenas organiza a verdade da sessão<br />
                    de um jeito impossível de ignorar.
                  </p>
                </GuideSection>

                {/* Final CTA dentro do guia */}
                <div className="pt-8 border-t border-zinc-800 mt-8">
                  <div className="text-center">
                    <p className="text-lg text-white mb-2">Quando estiver pronto</p>
                    <p className="text-gray-400 mb-6">
                      O painel já está esperando.<br />
                      E ele só respeita quem passa no teste.
                    </p>
                    <button
                      onClick={() => navigate('/auth')}
                      className="px-10 py-3 bg-white text-black font-semibold rounded-sm hover:bg-gray-200 transition-all"
                      data-testid="guide-start-button"
                    >
                      Entrar na Sala
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer info */}
          <div className="mt-12 text-center text-sm text-gray-600">
            <p>Sessões ilimitadas • Relatórios completos • Sem final feliz garantido</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
