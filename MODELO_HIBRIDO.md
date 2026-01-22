# 🧠 MODELO HÍBRIDO — Motor de Decisão dos Sharks

## Princípio Fundamental

**O shark decide com base em estado acumulado, padrão recente e eventos críticos, nunca por uma resposta isolada.**

O sistema nunca reage ao último turno.  
Ele reage à história que está se formando.

---

## 🎯 Visão Geral da Arquitetura

```
Resposta do Usuário
    ↓
Análise de Qualidade
    ↓
┌─────────────────────────────────────────┐
│  5 CAMADAS DE PROCESSAMENTO (híbrido)  │
├─────────────────────────────────────────┤
│  1. Estado Latente (interesse, paciência) │
│  2. Memória Ponderada (histórico)       │
│  3. Confiança Implícita (coerência)     │
│  4. Eventos Críticos (momentos-chave)   │
│  5. Decisão Emergente (saúde composta)  │
└─────────────────────────────────────────┘
    ↓
Decisão: Continuar, Leaning Out, ou Sair
```

---

## 📊 CAMADA 1 — Estado Latente

### Variáveis Mantidas
```python
interesse: 0..100      # Começa em 50
paciencia: 0..100      # Começa em 100
fadiga: 0..100         # Começa em 0
confianca: 0..100      # Começa em 50
```

### Atualização por Turno (sempre)
```python
paciencia -= desgaste_natural  # 3-4 pontos
fadiga += turno * 0.5           # Cresce com tempo
```

**Desgaste natural varia por perfil:**
- Operador: -4 pontos/turno (menos paciente)
- Financeiro: -3.5 pontos/turno
- Cético: -3 pontos/turno
- Visionário: -3 pontos/turno

---

## 🧩 CAMADA 2 — Memória Ponderada

### Estrutura
```python
ResponseMemory = [
  { 
    quality: -1 | 0 | +1,    # Qualidade do conteúdo
    peso: 0.0..1.0,          # Decai com tempo
    details: {...}           # Análise completa
  }
]
```

### Qualidade da Resposta
- **+1 (BOA):** Resposta direta, com dados, coerente com tese do shark
- **0 (NEUTRA):** Resposta aceitável mas sem destaque
- **-1 (FRACA):** Evasiva, sem dados, genérica, contraditória

### Decaimento Suave
```python
A cada nova resposta:
  for resposta in ResponseMemory:
    resposta.peso *= 0.85  # Decai 15%
  
  Adiciona nova resposta com peso 1.0
```

### Pattern Score (não pontual)
```python
pattern_score = sum(resposta.quality * resposta.peso)
```

**Interpretação:**
- `score > 2.0`: Padrão consistentemente bom → confiança cresce
- `score < -2.0`: Padrão consistentemente ruim → tolerância cai
- Respostas antigas têm peso menor automaticamente

**Resultado:**
✅ Uma resposta boa "mal escrita" NÃO mata  
✅ Três respostas medianas seguidas SIM afetam

---

## 🔗 CAMADA 3 — Confiança Implícita

### Conceito
Confiança **não reage à forma**, reage à **coerência longitudinal**.

### Construção de Confiança
```python
if resposta_boa:
  confianca += 3

if resposta_ruim:
  confianca -= 5

if contradicao_detectada:
  confianca -= 15  # Grave!

if pattern_score > 2.0:
  confianca += 2   # Consistência recompensa

if pattern_score < -2.0:
  confianca -= 3   # Inconsistência penaliza
```

### Efeito da Confiança
```python
confidence_multiplier = 1 - (confianca / 120)  # 0.0 a 0.83

# Penalidades são moduladas
penalidade_real = penalidade_base * (1 + confidence_multiplier)
bonus_real = bonus_base * (1 - confidence_multiplier)
```

**Resultado:**
- **Alta confiança (80+):** Perdoa forma ruim, foca no conteúdo
- **Baixa confiança (20-):** Amplifica qualquer erro

---

## ⚡ CAMADA 4 — Eventos Críticos

### Eventos Não-Aditivos
Alguns momentos **mudam trajetória**, não são apenas pontos.

```python
EVENTOS DETECTADOS:
  - PEDIDO_FORTE: Pedido claro com números
  - INSIGHT_UNICO: Diferenciação real, patente, inovação
  - CONTRADICAO_GRAVE: Contradiz resposta anterior
  - PITCH_CLEAR: Excepcional em clareza e dados
```

### Impactos
```python
if PEDIDO_FORTE:
  interesse += 15
  confianca += 20

if INSIGHT_UNICO:
  interesse += 10
  confianca += 10

if CONTRADICAO_GRAVE:
  confianca -= 40  # Devastador!
  paciencia -= 25

if PITCH_CLEAR:
  interesse += 8
  confianca += 12
```

**Esses eventos não dependem do histórico.**  
Simulam momentos onde "a sala ficou diferente".

---

## ⏳ CAMADA 5 — Decisão Emergente

### Cálculo de Saúde Composta
```python
health = (
  interesse * 0.4 +      # 40% peso
  paciencia * 0.3 +      # 30% peso
  confianca * 0.3        # 30% peso
) - (fadiga * 0.2)       # Fadiga penaliza
```

**Não é só pontos de interesse/paciência!**  
É uma composição que reflete o estado psicológico completo.

### Probabilidade de Saída
```python
# Base: depende de saúde
if health < 20:
  base_prob = 0.70      # Crítico
elif health < 35:
  base_prob = 0.50      # Baixo
elif health < 50:
  base_prob = 0.30      # Médio-baixo
else:
  base_prob = 0.15      # OK

# Pattern penalty
if pattern_score < -2.0:
  pattern_penalty = 1.5  # Aumenta chance
elif pattern_score > 2.0:
  pattern_penalty = 0.6  # Protege

base_prob *= pattern_penalty

# Multiplicador temporal (turno 10+)
if turno >= 10:
  time_multiplier = 1.0
  if turno >= 15:
    time_multiplier = 1.3
  if turno >= 18:
    time_multiplier = 1.6
  
  base_prob *= time_multiplier
```

### Proteção Inicial (Turnos 1-4)
```python
if turno <= 4:
  # Mesmo com decisão OUT, apenas 15% de chance
  return random() < 0.15
```

**Por quê?**  
Investidores observam antes de julgar.  
Evita frustração precoce.

---

## 🎭 Exemplos Práticos

### Exemplo 1: Resposta Boa, Mal Escrita (Turno 8)

**Input:**
- Conteúdo bom (+1)
- Forma ruim (longa demais)
- Confiança alta (75)

**Processamento:**
```
1. Memória: adiciona +1 com peso 1.0
2. Pattern score: positivo (histórico bom)
3. Confiança: aumenta +3
4. Confidence multiplier: baixo (0.38)
5. Penalidade de forma: 15 * 1.38 = 20.7
6. Interesse: mantém (bônus compensa)
7. Decisão: CONTINUA
```

**Resultado:** Ninguém sai. Confiança alta perdoou a forma.

---

### Exemplo 2: Quarta Resposta Confusa Seguida

**Input:**
- Conteúdo fraco (-1)
- Histórico: 3 respostas ruins anteriores
- Confiança baixa (30)

**Processamento:**
```
1. Memória: adiciona -1 com peso 1.0
2. Pattern score: -3.5 (muito negativo)
3. Confiança: cai para 22
4. Confidence multiplier: alto (0.82)
5. Penalidades: amplificadas
6. Saúde composta: cai para 28
7. Probabilidade saída: 50% * 1.5 = 75%
8. Decisão: Provavelmente SAI
```

**Resultado:** "Ele se perdeu" → saída faz sentido.

---

### Exemplo 3: Evento Crítico (Contradição Grave)

**Input:**
- Turno 6: "Já temos 500 clientes"
- Turno 12: "Ainda estamos validando com usuários"
- Sistema detecta contradição

**Processamento:**
```
1. Evento: CONTRADICAO_GRAVE
2. Confiança: -40 pontos (de 60 para 20)
3. Paciência: -25 pontos
4. Próximas penalidades: amplificadas
5. Saúde: cai drasticamente
```

**Resultado:** A mesa virou. Shark provavelmente sai nos próximos 2-3 turnos.

---

## 📏 Thresholds de Decisão Latente

```python
if health < 25:
  decisao = "OUT"           # Deve sair
elif health < 45:
  decisao = "LEANING_OUT"   # Inclinado a sair
else:
  decisao = "ACTIVE"        # Ativo
```

**Importante:** Thresholds são baseados em saúde composta, não interesse isolado.

---

## 🎯 Resultados Possíveis por Tipo de Pitch

### Pitch Excelente
- Pattern score: consistentemente positivo
- Confiança: cresce para 80+
- Eventos críticos: PEDIDO_FORTE, PITCH_CLEAR
- Saúde: mantém acima de 60
- **Resultado:** Todos ficam até turno 20

### Pitch Médio
- Pattern score: oscila entre -1 e +2
- Confiança: estável em 40-60
- Alguns eventos neutros
- Saúde: oscila 35-55
- **Resultado:** 1-2 saem após turno 12

### Pitch Fraco
- Pattern score: negativo persistente
- Confiança: cai para 20-
- Contradições detectadas
- Saúde: abaixo de 30
- **Resultado:** 3-4 saem, sessão pode acabar vazia

---

## ✅ Garantias do Sistema

### O Que o Sistema GARANTE
✅ Pressão progressiva natural (fadiga + desgaste)  
✅ Primeiros turnos com proteção (observação)  
✅ Decisão baseada em histórico completo  
✅ Eventos críticos mudam trajetória  
✅ Resultado emerge das interações  

### O Que o Sistema NÃO FAZ
❌ Não força saída em turno específico  
❌ Não ignora histórico positivo  
❌ Não pune uma resposta boa mal escrita  
❌ Não cria padrão previsível  
❌ Não garante final feliz  

---

## 🔬 Monitoramento e Debug

### Métricas-Chave para Observar
```
Por Shark:
  - health (saúde composta)
  - pattern_score (tendência)
  - confianca (coerência)
  - fadiga (cansaço temporal)

Por Sessão:
  - Turno da primeira saída
  - Pattern score médio
  - Eventos críticos detectados
  - Saúde final dos sharks ativos
```

---

## 🎬 Conclusão: Modelo Comportamental

> "Isso que você está construindo já não é 'simulador'.  
> É modelo comportamental."

O sistema:
- Não reage ao último turno
- Reage à história que está se formando
- Modula penalidades pela confiança construída
- Detecta momentos que mudam trajetória
- Cria condições para o final acontecer

**Resultado:** Arena, não algoritmo.
