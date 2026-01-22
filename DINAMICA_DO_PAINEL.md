# 🎭 Dinâmica do Painel - Investor Panel Simulator

## Princípio Central

**O painel não decide o final. Ele cria as condições para o final acontecer.**

O sistema não força resultados. Ele retira proteção conforme o tempo passa.

---

## Tempo e Turnos

- **Máximo:** 20 turnos por sessão
- **Duração típica:** 15-20 turnos
- Cada turno representa uma interação pergunta-resposta

---

## Desgaste Natural

### Paciência dos Investidores
- **Desgasta 3 pontos a cada turno** (natural)
- Desgaste adicional baseado na qualidade da resposta:
  - Respostas evasivas: -15 a -30 pontos
  - Sem números (Financeiro): -20 pontos
  - Falta de clareza (Operador): -30 pontos
  - Sem diferencial (Cético): -25 pontos
  - Sem visão (Visionário): -15 pontos

### Interesse dos Investidores
- Começa em 50 pontos
- Diminui baseado em:
  - Respostas inadequadas
  - Falta de dados específicos
  - Evasão de perguntas diretas

---

## Proteção nos Primeiros Turnos

**Turnos 1-4: Fase de Observação**
- Investidores raramente saem
- Mesmo com decisão "OUT", apenas 15% de chance real
- Foco em fazer perguntas e entender o negócio

**Por quê?**
- Evita frustração precoce
- Dá tempo para o pitch se desenvolver
- Simula comportamento real de investidores

---

## Multiplicador Progressivo (Turno 10+)

A partir do turno 10, o sistema **multiplica a probabilidade de saída** baseado no estado atual:

### Cálculo de "Saúde" do Investidor
```
health_score = (interesse + paciência) / 2
```

### Multiplicadores
- **health < 20:** 3.0x (saúde crítica)
- **health < 35:** 2.0x (saúde baixa)
- **health < 50:** 1.5x (saúde média-baixa)
- **health >= 50:** 1.0x (saúde OK)

### Multiplicadores Temporais
- **Turno 15+:** +30% no multiplicador
- **Turno 18+:** +50% no multiplicador

---

## Decisões Latentes

### Estados Internos do Investidor

**ACTIVE** (Padrão)
- Interesse e paciência normais
- Participa ativamente

**LEANING_OUT** (Inclinado a sair)
- Interesse < 30 OU paciência < 25
- Probabilidade base de saída: 40%
- Com multiplicadores: até 180% após turno 18

**OUT** (Decidido a sair)
- Interesse < 15 OU paciência < 10
- Sai na próxima oportunidade

---

## Resultados Possíveis

### ✅ Pitch Excelente
- Todos os 4 investidores mantêm interesse
- Múltiplas propostas possíveis
- Sessão pode terminar com 100% de engajamento

### ⚖️ Pitch Médio
- 1-2 investidores saem
- 2-3 mantêm interesse parcial
- Resultado incerto até o final

### ❌ Pitch Fraco
- 3-4 investidores saem
- Sessão pode terminar vazia
- Sem final feliz garantido

---

## O Que NÃO Acontece

❌ Não existe saída garantida no turno X
❌ Não existe padrão fixo de "sempre 2 saem"
❌ Não existe proteção artificial após turno 10
❌ Não existe roteiro predeterminado

---

## O Que Acontece

✅ Se você está indo mal → sai mais rápido após turno 10
✅ Se você está indo bem → pode manter todos interessados
✅ Resultado emerge das interações reais
✅ Imprevisibilidade mantém legitimidade

---

## Comunicação ao Usuário

**Linguagem de Arena, não Algoritmo**

❌ Evite: "O sistema vai fazer X no turno Y"
✅ Use: "A tolerância do painel diminui com o tempo"

❌ Evite: "Você precisa conseguir pontos"
✅ Use: "Investidores podem sair a qualquer momento"

❌ Evite: "Algoritmo de decisão"
✅ Use: "Pressão crescente do painel"

---

## Relatório Final

### Captura de Tensão

O relatório deve responder:
- **"Em que turno a mesa virou?"**
- **"Quem desistiu primeiro e por quê?"**
- **"O que nunca foi respondido?"**
- **"Quais temas drenaram paciência?"**

### Momento de Virada

Identificado automaticamente:
- Primeiro investidor a sair
- Turno crítico
- Contexto (após interrupções, evasão, etc)

---

## Filosofia do Produto

> "O painel não reage para te agradar.  
> Ele reage para testar consistência sob pressão."

Isso comunica **arena**, não **algoritmo**.
