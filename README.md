# 🌱 Termo Ambiental

Projeto desenvolvido para a disciplina de Educação Ambiental da Universidade Estadual de Feira de Santana (UEFS), inspirado no jogo **Termo** (similar ao Wordle), com foco em conceitos, correntes e discussões críticas relacionadas à temática ambiental.

O jogo foi desenvolvido em Python utilizando a biblioteca **Pygame**, promovendo uma experiência educativa, interativa e lúdica para reforçar conteúdos estudados na disciplina.

---

## 📚 Sobre o Projeto

O **Termo Ambiental** adapta a mecânica clássica de jogos de palavras para o contexto da Educação Ambiental Crítica.  
A cada partida, o jogador deve descobrir uma palavra relacionada à temática ambiental em até 6 tentativas.

Além da mecânica de descoberta da palavra, o jogo possui um diferencial educativo:  
ao final de cada partida, é exibido um **flashcard contextualizado**, explicando o significado e a relevância do termo dentro das discussões ambientais contemporâneas.

O projeto busca unir:

- Aprendizagem lúdica;
- Educação ambiental crítica;
- Reflexão social e ecológica;
- Interatividade digital.

---

## 🎮 Como Funciona

- O jogo escolhe aleatoriamente uma palavra relacionada à Educação Ambiental;
- O jogador possui até **6 tentativas** para acertar;
- Após cada tentativa:
  - 🟩 Letras corretas e na posição correta ficam verdes;
  - 🟨 Letras existentes na palavra, mas em posição incorreta ficam amarelas;
  - ⬛ Letras ausentes ficam escuras;
- Ao final da partida, o jogo apresenta:
  - A palavra correta;
  - Um contexto educativo relacionado ao tema ambiental.

---

## 🧠 Temáticas Abordadas

O banco de palavras inclui conceitos ligados a:

- Justiça ambiental;
- Povos indígenas e quilombolas;
- Ecologia política;
- Sustentabilidade;
- Conservação;
- Crise socioambiental;
- Educação ambiental crítica;
- Racismo ambiental;
- Território;
- Resistência;
- Saberes tradicionais;
- Entre outros.

Exemplos de palavras presentes no jogo:

```text
NATUREZA
JUSTICA
FLORESTA
EMANCIPACAO
CONSERVACAO
DIALOGO
RESISTENCIA
ECOLOGIA
YANOMAMI
CIDADANIA
```

---

## 🛠️ Tecnologias Utilizadas

- Python 3
- Pygame
- JSON

---

## 📂 Estrutura do Projeto

```text
📁 termo-ambiental/
│
├── termo_ambiental.py          # Código principal do jogo
├── palavras_ambientais.json    # Banco de palavras e contextos
└── README.md                   # Documentação do projeto
```

---

## ▶️ Como Executar

### 1. Instale o Python

Certifique-se de possuir o Python 3 instalado.

---

### 2. Instale o Pygame

No terminal, execute:

```bash
pip install pygame
```

---

### 3. Execute o jogo

No diretório do projeto:

```bash
python termo_ambiental.py
```

---

## ✨ Funcionalidades

- Interface gráfica moderna;
- Teclado virtual interativo;
- Sistema de animações;
- Feedback visual semelhante ao Termo;
- Flashcards educativos;
- Sistema de partículas/confetes;
- Redimensionamento dinâmico da janela;
- Seleção de células por clique;
- Banco de palavras contextualizado.

---

## 🎯 Objetivo Educacional

O jogo foi criado com o objetivo de estimular o aprendizado de conceitos ambientais de maneira dinâmica e acessível, incentivando:

- Reflexão crítica sobre questões ambientais;
- Familiarização com conceitos da disciplina;
- Participação ativa dos estudantes;
- Aprendizagem por meio da ludicidade.

---

## 👥 Integrantes

* Daniel Braz
* Felipe Bastos
* Ítallo Guimarães
* Lucas Oliveira

---

## 🏫 Informações Acadêmicas

**Universidade Estadual de Feira de Santana (UEFS)**   
Disciplina: BIO606 - Educação Ambiental  
Semestre: 2026.1

---

## 📄 Licença

Projeto desenvolvido exclusivamente para fins acadêmicos e educacionais.
