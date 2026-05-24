"""
╔══════════════════════════════════════════════════════════════════════╗
║         TERMO AMBIENTAL  –  Redesign Visual v3                      ║
║  Flip suave + teclado com cores por letra (igual Termo.ooo)         ║
║  + Seleção de célula por clique (v3.1)                              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import pygame
import json
import random
import sys
import os
import unicodedata
import math

# ─────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────

SCREEN_W        = 700       # largura inicial da janela em pixels
SCREEN_H        = 920       # altura inicial da janela em pixels
FPS             = 60        # quadros por segundo alvo
MAX_TENTATIVAS  = 6         # número máximo de tentativas por partida
CELL_MARGIN     = 7         # espaço em pixels entre células da grade
CELL_MAX_SIZE   = 74        # tamanho máximo de cada célula em pixels
JSON_FILE       = "palavras_ambientais.json"   # arquivo de palavras e contextos

HEADER_H        = 80        # altura do cabeçalho (título + info)
KEYBOARD_H      = 215       # altura da área do teclado virtual

# ── Paleta (estilo Termo.ooo) ──────────────────────────────────────────
COR_BG_TOP      = (20,  20,  34)    # topo do gradiente de fundo
COR_BG_BOT      = (12,  12,  22)    # base do gradiente de fundo
COR_HEADER_BG   = (24,  24,  38)    # fundo do cabeçalho
COR_DIVIDER     = (48,  48,  70)    # linha divisória sutil

COR_CELULA_VZ   = (44,  44,  64)    # célula vazia (sem letra)
COR_CELULA_BD   = (70,  70,  98)    # borda de célula vazia
COR_CELULA_AT   = (60,  60,  85)    # célula ativa (com letra digitada)
COR_CELULA_BDA  = (110, 110, 150)   # borda de célula ativa

COR_CORRETA     = (83,  205, 174)   # teal  – letra na posição correta
COR_PRESENTE    = (200, 167, 112)   # bege  – letra presente, fora de lugar
COR_AUSENTE     = (30,   30,  44)   # quase preto – letra ausente na palavra

COR_TEXTO       = (255, 255, 255)   # texto branco principal
COR_TEXTO_DIM   = (100, 100, 135)   # texto secundário esmaecido
COR_TITULO      = (83,  205, 174)   # cor do título no cabeçalho

# [NOVO] Cores exclusivas do cursor de seleção por clique
# COR_CURSOR_BD  : borda azul-clara desenhada ao redor da célula focada
# COR_CURSOR_GLOW: cor do preenchimento semitransparente de brilho interno
COR_CURSOR_BD   = (180, 220, 255)   # azul-claro – borda da célula focada
COR_CURSOR_GLOW = (100, 160, 230)   # azul médio – brilho interno pulsante

COR_TECLA_N     = (50,  50,  75)    # tecla neutra (estado desconhecido)
COR_TECLA_C     = (65,  165, 140)   # tecla correta (verde-teal)
COR_TECLA_P     = (170, 140,  90)   # tecla presente (bege)
COR_TECLA_A     = (28,  28,  42)    # tecla ausente (quase preto)
COR_TECLA_SPEC  = (68,  68,  95)    # teclas especiais ENTER e <<

COR_FLASH_BG    = (18,  18,  30)    # fundo do card de resultado final
COR_WIN_BORDA   = (83,  205, 174)   # borda teal do card de vitória
COR_LOSE_BORDA  = (210,  70,  80)   # borda vermelha do card de derrota
COR_WIN_TITULO  = (83,  205, 174)   # título do card de vitória
COR_LOSE_TITULO = (220,  80,  80)   # título do card de derrota
COR_PALAVRA_HL  = (255, 215,  65)   # destaque amarelo-ouro da palavra revelada

# Layout físico do teclado QWERTY em três linhas
KEYBOARD_ROWS = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["ENTER","Z","X","C","V","B","N","M","<<"],
]

# ─────────────────────────────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────

def normalizar(texto: str) -> str:
    """Remove acentos e converte para maiúsculas para comparação uniforme."""
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()

def quebrar_texto(font, texto: str, max_w: int) -> list:
    """
    Quebra 'texto' em linhas que caibam dentro de 'max_w' pixels,
    respeitando os espaços entre palavras. Retorna lista de strings.
    """
    palavras = texto.split()
    linhas, linha = [], ""
    for p in palavras:
        cand = f"{linha} {p}".strip()
        if font.size(cand)[0] <= max_w:
            linha = cand
        else:
            if linha:
                linhas.append(linha)
            linha = p
    if linha:
        linhas.append(linha)
    return linhas

def carregar_fonte(tam, negrito=False):
    """
    Tenta carregar uma fonte do sistema em ordem de preferência.
    Cai para a fonte padrão do pygame se nenhuma for encontrada.
    """
    for n in ["Arial", "DejaVuSans", "Helvetica", "FreeSans", "Ubuntu"]:
        try:
            return pygame.font.SysFont(n, tam, bold=negrito)
        except Exception:
            continue
    return pygame.font.Font(None, tam)

def lerp(a, b, t):
    """Interpolação linear: retorna o valor entre 'a' e 'b' na proporção 't' (0→1)."""
    return a + (b - a) * t

def lerp_cor(c1, c2, t):
    """Interpola linearmente entre duas cores RGB componente a componente."""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def ease_out_cubic(t):
    """Curva ease-out cúbica: começa rápido e desacelera no final."""
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    """
    Curva ease-in-out baseada em seno: acelera suavemente no início
    e desacelera suavemente no final. Ideal para o flip das células.
    """
    return -(math.cos(math.pi * t) - 1) / 2


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Celula
# ─────────────────────────────────────────────────────────────────────

class Celula:
    """
    Representa uma célula individual da grade de jogo.

    Três camadas de animação independentes:
      1) Pop    – leve expansão ao digitar uma letra (0.13 s)
      2) Flip   – compressão e expansão em Y ao revelar o resultado,
                  com ease-in-out-sine e delay configurável por coluna
      3) Bounce – salto vertical ao vencer, com delay por coluna

    [NOVO] O método draw() recebe dois parâmetros extras:
      • is_cursor : indica se esta célula é o cursor de seleção ativo
      • pulse_t   : tempo global em segundos, usado para animar a borda pulsante
    """

    # ── Durações das animações ────────────────────────────────────────
    POP_DUR    = 0.13   # duração do pop ao digitar (segundos)
    FLIP_DUR   = 0.70   # duração total de cada flip (segundos)
    BOUNCE_DUR = 0.60   # duração do salto de vitória (segundos)

    def __init__(self, x, y, size):
        self.base   = pygame.Rect(x, y, size, size)   # retângulo base da célula
        self.letra  = ""                               # letra atualmente exibida
        self.estado = "vazio"                          # estado visual atual

        # ── Estado interno do Pop ─────────────────────────────────────
        self._pop_t    = 0.0    # tempo acumulado da animação de pop
        self._popping  = False  # True enquanto o pop estiver ativo

        # ── Estado interno do Flip ────────────────────────────────────
        self._flip_t        = 0.0   # tempo acumulado desde o início do flip
        self._flip_delay    = 0.0   # delay antes de começar (escalonado por coluna)
        self._flipping      = False # True enquanto o flip estiver ativo
        self._flip_revealed = False # True após a troca de cor na metade do flip
        self._flip_alvo     = None  # estado final que será aplicado na virada

        # ── Estado interno do Bounce ──────────────────────────────────
        self._bnc_t    = 0.0    # tempo acumulado do bounce
        self._bnc_delay = 0.0   # delay antes de começar (escalonado por coluna)
        self._bouncing  = False # True enquanto o bounce estiver ativo

    # ── Disparadores de animação ──────────────────────────────────────
    def pop(self):
        """Inicia o efeito de pop (chamado ao digitar uma letra)."""
        self._pop_t   = 0.0
        self._popping = True

    def flip(self, estado_final: str, delay: float):
        """
        Inicia a animação de flip que revela o resultado da letra.
        'estado_final' será aplicado exatamente na metade da animação.
        'delay' adia o início (usado para escalonar colunas da esquerda para a direita).
        """
        self._flip_alvo     = estado_final
        self._flip_delay    = delay
        self._flip_t        = 0.0
        self._flip_revealed = False
        self._flipping      = True

    def bounce(self, delay: float):
        """
        Inicia o salto de vitória.
        'delay' adia o início para criar o efeito cascata entre colunas.
        """
        self._bnc_delay = delay
        self._bnc_t     = 0.0
        self._bouncing  = True

    # ── Mapeamento estado → cor de fundo ──────────────────────────────
    def cor(self):
        """Retorna a cor de fundo da célula de acordo com seu estado atual."""
        return {
            "vazio":    COR_CELULA_VZ,
            "ativo":    COR_CELULA_AT,
            "correta":  COR_CORRETA,
            "presente": COR_PRESENTE,
            "ausente":  COR_AUSENTE,
        }.get(self.estado, COR_CELULA_VZ)

    # ── Atualização de estado por frame ──────────────────────────────
    def update(self, dt: float):
        """Avança todas as animações ativas pelo delta de tempo 'dt' (segundos)."""

        # Pop: avança o timer e desativa quando termina
        if self._popping:
            self._pop_t += dt
            if self._pop_t >= self.POP_DUR:
                self._popping = False

        # Flip: avança o timer, aplica a troca de estado na metade, desativa no fim
        if self._flipping:
            self._flip_t += dt
            efet = self._flip_t - self._flip_delay   # tempo efetivo após o delay
            if efet > 0:
                prog = efet / self.FLIP_DUR
                # Exatamente na metade da animação a célula está "de lado":
                # é o momento ideal para trocar a cor sem que o jogador perceba
                if prog >= 0.5 and not self._flip_revealed:
                    self._flip_revealed = True
                    self.estado         = self._flip_alvo
                if prog >= 1.0:
                    self._flipping = False

        # Bounce: desativa quando o tempo efetivo supera a duração total
        if self._bouncing:
            self._bnc_t += dt
            if (self._bnc_t - self._bnc_delay) >= self.BOUNCE_DUR:
                self._bouncing = False

    # ── Transformações geométricas ────────────────────────────────────
    def redimensionar(self, x, y, size):
        """Reposiciona e redimensiona o retângulo base (chamado ao redimensionar a janela)."""
        self.base = pygame.Rect(x, y, size, size)

    def _scale_pop(self) -> float:
        """
        Retorna o fator de escala uniforme (X e Y) durante o pop.
        Usa uma curva senoidal para expandir e retornar ao tamanho original.
        """
        if not self._popping:
            return 1.0
        t = self._pop_t / self.POP_DUR
        return 1.0 + 0.12 * math.sin(t * math.pi)   # pico de +12% no meio

    def _scale_y_flip(self) -> float:
        """
        Retorna o fator de escala em Y durante o flip usando ease-in-out-sine:
          – Primeira metade  (t 0→0.5): comprime de 1 → 0  (ease-in)
          – Segunda metade   (t 0.5→1): expande de 0 → 1   (ease-out)
        O resultado é uma virada suave e natural, sem travamento.
        """
        if not self._flipping:
            return 1.0
        efet = self._flip_t - self._flip_delay
        if efet <= 0:
            return 1.0
        t = min(efet / self.FLIP_DUR, 1.0)

        if t < 0.5:
            # ease-in: mapeia 0-0.5 → 0-1 e comprime de 1 até 0
            e = ease_in_out_sine(t * 2)
            return 1.0 - e
        else:
            # ease-out: mapeia 0.5-1 → 0-1 e expande de 0 até 1
            e = ease_in_out_sine((t - 0.5) * 2)
            return e

    def _off_bounce(self) -> float:
        """
        Retorna o deslocamento vertical em pixels durante o bounce.
        Usa seno para criar um salto suave que começa e termina em zero.
        Valor negativo = movimento para cima na tela.
        """
        if not self._bouncing:
            return 0.0
        efet = self._bnc_t - self._bnc_delay
        if efet <= 0:
            return 0.0
        t = min(efet / self.BOUNCE_DUR, 1.0)
        return -32 * math.sin(t * math.pi)   # pico de -32 px (32 px acima)

    # ── Desenho ───────────────────────────────────────────────────────
    def draw(self, surface, font, shake_dx=0, is_cursor=False, pulse_t=0.0):
        """
        Desenha a célula aplicando todas as transformações ativas.

        Parâmetros:
          surface   : superfície pygame de destino
          font      : fonte para renderizar a letra
          shake_dx  : deslocamento horizontal do shake (erro de palavra incompleta)
          is_cursor : [NOVO] True quando esta célula é o cursor de seleção ativo
          pulse_t   : [NOVO] tempo global em segundos para calcular o pulso do cursor
        """
        cor   = self.cor()
        sy    = self._scale_y_flip()   # escala vertical (flip)
        sxy   = self._scale_pop()      # escala uniforme  (pop)
        off_y = self._off_bounce()     # deslocamento vertical (bounce)

        # Copia o rect base e aplica shake e bounce
        r = self.base.copy()
        r.x += shake_dx
        r.y += int(off_y)

        # Aplica escala uniforme do pop: infla o rect mantendo o centro
        if sxy != 1.0:
            dw = int(r.width  * (sxy - 1))
            dh = int(r.height * (sxy - 1))
            r.inflate_ip(dw, dh)
            r.centerx = self.base.centerx + shake_dx
            r.centery  = self.base.centery + int(off_y)

        # Aplica escala vertical do flip: reduz a altura mantendo o centro
        if sy < 1.0:
            nh = max(2, int(r.height * sy))   # altura mínima de 2 px
            cy = r.centery
            r.height  = nh
            r.centery = cy

        # Desenha o fundo colorido da célula
        pygame.draw.rect(surface, cor, r, border_radius=6)

        # ── Borda padrão conforme o estado ───────────────────────────
        if self.estado == "vazio":
            # Célula vazia: borda fina discreta
            pygame.draw.rect(surface, COR_CELULA_BD,
                             pygame.Rect(self.base.x + shake_dx, self.base.y,
                                         self.base.w, self.base.h),
                             width=2, border_radius=6)
        elif self.estado == "ativo":
            # Célula com letra digitada: borda mais clara
            pygame.draw.rect(surface, COR_CELULA_BDA,
                             pygame.Rect(self.base.x + shake_dx, self.base.y,
                                         self.base.w, self.base.h),
                             width=2, border_radius=6)

        # [NOVO] ── Cursor: borda pulsante azul-claro ──────────────────
        # Só é desenhada nas células sem resultado (vazio ou ativo),
        # pois células reveladas (correta/presente/ausente) não podem
        # ser editadas e não devem receber o indicador de seleção.
        if is_cursor and self.estado in ("vazio", "ativo"):
            # Calcula o fator de pulso oscilando entre 0.1 e 1.0
            # usando sin(t * 4.0) → frequência de ~0.64 Hz (ciclo a cada ~1.57 s)
            pulse = 0.55 + 0.45 * math.sin(pulse_t * 4.0)
            alpha = int(255 * pulse)

            # Borda interna pulsante – usa SRCALPHA para suportar transparência
            brd_surf = pygame.Surface((self.base.w, self.base.h), pygame.SRCALPHA)
            bd_col = (*COR_CURSOR_BD, alpha)
            pygame.draw.rect(brd_surf, bd_col,
                             pygame.Rect(0, 0, self.base.w, self.base.h),
                             width=3, border_radius=6)
            surface.blit(brd_surf, (self.base.x + shake_dx, self.base.y))

            # Fundo interno levemente iluminado no tom azul (glow sutil)
            glow_surf = pygame.Surface((self.base.w - 4, self.base.h - 4), pygame.SRCALPHA)
            glow_surf.fill((*COR_CURSOR_GLOW, int(30 * pulse)))
            surface.blit(glow_surf, (self.base.x + shake_dx + 2, self.base.y + 2))

        # ── Letra: só exibe quando a célula não está quase de lado ────
        # sy > 0.12 evita renderizar a letra quando ela seria invisível
        # por estar quase totalmente comprimida durante o flip
        if self.letra and sy > 0.12:
            txt = font.render(self.letra, True, COR_TEXTO)
            surface.blit(txt, txt.get_rect(center=(r.centerx, r.centery)))


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Tabuleiro
# ─────────────────────────────────────────────────────────────────────

class Tabuleiro:
    """
    Gerencia a grade de células do jogo.

    Funcionalidades:
      • Grade adaptável ao tamanho da janela (atualizar_area)
      • Animação de shake na linha atual ao erro
      • Flip escalonado coluna a coluna ao confirmar tentativa
      • Bounce cascata nas células ao vencer

    [NOVO] Seleção de célula por clique:
      • cursor_col  rastreia qual coluna está visualmente focada
      • clicar_celula() move o cursor ao clicar na linha ativa
      • digitar() sobrescreve a célula no cursor e avança
      • apagar() tem lógica inteligente: apaga o cursor ou recua
      • draw() recebe pulse_t e repassa is_cursor para cada Celula
    """

    FLIP_COL_DELAY   = 0.14   # delay entre colunas no flip (escalonamento)
    BOUNCE_COL_DELAY = 0.08   # delay entre colunas no bounce de vitória
    SHAKE_DUR        = 0.52   # duração total do shake de erro (segundos)
    SHAKE_AMP        = 9      # amplitude máxima do shake em pixels

    def __init__(self, palavra_len, max_tent, area):
        self.palavra_len     = palavra_len   # número de letras da palavra
        self.max_tent        = max_tent      # número máximo de tentativas
        self.area            = area          # Rect da área disponível na tela
        self.celulas         = []            # grade 2D: celulas[row][col]
        self.tentativa_atual = 0             # linha que está sendo editada
        self.posicao_atual   = 0             # coluna onde a próxima letra vai

        # [NOVO] cursor_col: coluna visualmente focada pelo cursor de seleção.
        # Começa em 0 e é atualizado tanto pela digitação quanto pelo clique.
        self.cursor_col      = 0

        # ── Estado interno do shake ───────────────────────────────────
        self._shake_t   = 0.0    # tempo acumulado do shake atual
        self._shaking   = False  # True enquanto o shake estiver ativo
        self._shake_row = -1     # linha que está sofrendo o shake

        self._construir()

    def _construir(self):
        """
        Calcula o tamanho de cada célula para preencher a área disponível
        e instancia todas as Celulas posicionadas na grade.
        """
        # Calcula o tamanho máximo que cabe tanto em largura quanto em altura
        cw = (self.area.w - CELL_MARGIN * (self.palavra_len + 1)) // self.palavra_len
        ch = (self.area.h - CELL_MARGIN * (self.max_tent    + 1)) // self.max_tent
        self.cell_size = min(cw, ch, CELL_MAX_SIZE)

        # Centraliza a grade dentro da área disponível
        gw = self.palavra_len * self.cell_size + (self.palavra_len - 1) * CELL_MARGIN
        gh = self.max_tent    * self.cell_size + (self.max_tent    - 1) * CELL_MARGIN
        ox = self.area.x + (self.area.w - gw) // 2
        oy = self.area.y + (self.area.h - gh) // 2

        for row in range(self.max_tent):
            linha = []
            for col in range(self.palavra_len):
                x = ox + col * (self.cell_size + CELL_MARGIN)
                y = oy + row * (self.cell_size + CELL_MARGIN)
                linha.append(Celula(x, y, self.cell_size))
            self.celulas.append(linha)

    # ── API pública ───────────────────────────────────────────────────

    # [NOVO]
    def clicar_celula(self, pos) -> bool:
        """
        Verifica se o clique em 'pos' acertou alguma célula da linha atual.
        Se sim, move o cursor (posicao_atual e cursor_col) para essa coluna
        e retorna True para sinalizar que o clique foi consumido (não deve
        ser repassado ao teclado virtual).

        Retorna False se o clique não foi em nenhuma célula da linha ativa
        ou se o jogo já terminou (tentativa_atual >= max_tent).
        """
        if self.tentativa_atual >= self.max_tent:
            return False
        for col, celula in enumerate(self.celulas[self.tentativa_atual]):
            if celula.base.collidepoint(pos):
                self.posicao_atual = col
                self.cursor_col    = col
                return True
        return False

    def digitar(self, letra: str):
        """
        [MODIFICADO] Insere 'letra' na posição do cursor (posicao_atual),
        sobrescrevendo qualquer letra que já estivesse ali.

        Após inserir, avança o cursor para a próxima coluna disponível.
        Se já estiver na última coluna, o cursor permanece ali (o jogador
        pode corrigir a última letra sem precisar apagar).

        Atualiza cursor_col para manter sincronismo visual.
        """
        if self.tentativa_atual >= self.max_tent:
            return
        if self.posicao_atual >= self.palavra_len:
            return

        c = self.celulas[self.tentativa_atual][self.posicao_atual]
        c.letra  = letra
        c.estado = "ativo"
        c.pop()   # dispara o efeito visual de pop

        # Avança o cursor sem ultrapassar o limite da linha
        if self.posicao_atual < self.palavra_len - 1:
            self.posicao_atual += 1
        # else: permanece na última célula para permitir correção

        self.cursor_col = self.posicao_atual   # sincroniza o indicador visual

    def apagar(self):
        """
        [MODIFICADO] Backspace com comportamento inteligente:

          • Se a célula no cursor atual já tem uma letra:
              → Apaga essa letra e mantém o cursor no mesmo lugar.
                O jogador pode redigitar imediatamente.

          • Se a célula no cursor atual está vazia:
              → Recua o cursor uma posição e apaga a letra anterior.
                Comportamento padrão ao digitar em sequência.

        Isso permite corrigir qualquer célula após clicar nela,
        sem que o cursor pule inesperadamente para outra posição.
        """
        if self.tentativa_atual >= self.max_tent:
            return

        col_atual    = self.posicao_atual
        celula_atual = self.celulas[self.tentativa_atual][col_atual]

        if celula_atual.letra:
            # Apaga a letra na posição atual; cursor permanece aqui
            celula_atual.letra  = ""
            celula_atual.estado = "vazio"
        elif col_atual > 0:
            # Célula atual já está vazia: recua e apaga a célula anterior
            self.posicao_atual -= 1
            self.cursor_col    = self.posicao_atual
            c = self.celulas[self.tentativa_atual][self.posicao_atual]
            c.letra  = ""
            c.estado = "vazio"

    def atualizar_area(self, area):
        """
        Recalcula posições e tamanhos de todas as células quando a janela
        é redimensionada. Não recria os objetos Celula; apenas os reposiciona.
        """
        self.area = area
        cw = (self.area.w - CELL_MARGIN * (self.palavra_len + 1)) // self.palavra_len
        ch = (self.area.h - CELL_MARGIN * (self.max_tent    + 1)) // self.max_tent
        self.cell_size = min(cw, ch, CELL_MAX_SIZE)

        gw = self.palavra_len * self.cell_size + (self.palavra_len - 1) * CELL_MARGIN
        gh = self.max_tent    * self.cell_size + (self.max_tent    - 1) * CELL_MARGIN
        ox = self.area.x + (self.area.w - gw) // 2
        oy = self.area.y + (self.area.h - gh) // 2

        for row in range(self.max_tent):
            for col in range(self.palavra_len):
                x = ox + col * (self.cell_size + CELL_MARGIN)
                y = oy + row * (self.cell_size + CELL_MARGIN)
                self.celulas[row][col].redimensionar(x, y, self.cell_size)

    def get_tentativa(self) -> str:
        """Retorna a string formada pelas letras da linha em edição."""
        return "".join(c.letra for c in self.celulas[self.tentativa_atual])

    def aplicar_resultado(self, resultado: list, ganhou=False):
        """
        Dispara o flip em cada célula da linha atual com o estado correto
        e, se ganhou, encadeia o bounce após o flip terminar.
        Avança a tentativa e reseta o cursor para a coluna 0.
        """
        n          = len(resultado)
        flip_total = n * self.FLIP_COL_DELAY + Celula.FLIP_DUR

        for i, est in enumerate(resultado):
            delay_flip = i * self.FLIP_COL_DELAY          # escalonamento de colunas
            self.celulas[self.tentativa_atual][i].flip(est, delay_flip)
            if ganhou:
                delay_bnc = flip_total + i * self.BOUNCE_COL_DELAY
                self.celulas[self.tentativa_atual][i].bounce(delay_bnc)

        self.tentativa_atual += 1
        self.posicao_atual    = 0
        self.cursor_col       = 0   # [NOVO] reseta o cursor para o início da próxima linha

    def shake(self):
        """Inicia a animação de shake na linha atual (palavra inválida ou incompleta)."""
        self._shaking   = True
        self._shake_t   = 0.0
        self._shake_row = self.tentativa_atual

    # ── Atualização e desenho ─────────────────────────────────────────
    def update(self, dt):
        """Avança o shake e delega update() para todas as células."""
        if self._shaking:
            self._shake_t += dt
            if self._shake_t >= self.SHAKE_DUR:
                self._shaking = False
        for row in self.celulas:
            for c in row:
                c.update(dt)

    def _shake_dx(self) -> int:
        """
        Calcula o deslocamento horizontal do shake no frame atual.
        Usa seno amortecido: a amplitude decresce conforme o tempo avança.
        """
        if not self._shaking:
            return 0
        p = self._shake_t / self.SHAKE_DUR
        return int(self.SHAKE_AMP * math.sin(p * math.pi * 5) * (1 - p))

    def draw(self, surface, font, pulse_t=0.0):
        """
        Desenha todas as células, aplicando shake na linha correta.

        [NOVO] pulse_t: tempo global repassado para cada Celula.draw() a fim
        de animar a borda pulsante do cursor. O parâmetro is_cursor é
        calculado aqui e passado individualmente para cada célula:
          – True  apenas para a célula na linha ativa E na coluna cursor_col
          – False para todas as demais células
        """
        dx = self._shake_dx()
        for ri, row in enumerate(self.celulas):
            sdx = dx if ri == self._shake_row else 0
            for ci, c in enumerate(row):
                # [NOVO] Determina se esta célula deve exibir o indicador de cursor
                is_cursor = (
                    ri == self.tentativa_atual         # apenas a linha em edição
                    and ci == self.cursor_col          # apenas a coluna focada
                    and self.tentativa_atual < self.max_tent  # jogo ainda ativo
                )
                c.draw(surface, font, shake_dx=sdx,
                       is_cursor=is_cursor, pulse_t=pulse_t)


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: TecladoVirtual
# ─────────────────────────────────────────────────────────────────────

class TecladoVirtual:
    """
    Teclado QWERTY clicável exibido na parte inferior da tela.

    Cores das teclas refletem o melhor resultado já obtido para cada letra:
      correta (teal) > presente (bege) > ausente (quase preto) > neutra

    As cores são atualizadas letra a letra, sincronizadas com o momento
    exato em que cada célula revela seu resultado (metade do flip).
    """

    KEY_H   = 50   # altura de cada tecla em pixels
    KEY_GAP = 5    # espaço entre teclas em pixels

    def __init__(self, area: pygame.Rect):
        self.area    = area   # Rect da área destinada ao teclado
        self.estados = {}     # dicionário letra → estado mais alto já revelado
        self.rects   = {}     # dicionário tecla → Rect de colisão e desenho
        self.font    = carregar_fonte(14, negrito=True)   # fonte das teclas normais
        self.font_sm = carregar_fonte(11, negrito=True)   # fonte menor para "ENTER"
        self._build()

    def _build(self):
        """Calcula os Rects de todas as teclas centralizados na área."""
        row_h   = self.KEY_H + self.KEY_GAP
        total_h = len(KEYBOARD_ROWS) * row_h - self.KEY_GAP
        start_y = self.area.centery - total_h // 2

        for ri, row in enumerate(KEYBOARD_ROWS):
            # Teclas especiais (ENTER, <<) são mais largas que as normais
            widths = []
            for k in row:
                widths.append(int(self.KEY_H * 1.65) if k in ("ENTER", "<<") else self.KEY_H)
            total_w = sum(widths) + (len(row) - 1) * self.KEY_GAP
            x = self.area.centerx - total_w // 2
            y = start_y + ri * row_h
            for ki, key in enumerate(row):
                self.rects[key] = pygame.Rect(x, y, widths[ki], self.KEY_H)
                x += widths[ki] + self.KEY_GAP

    def atualizar(self, letra: str, estado: str):
        """
        Atualiza a cor da tecla respeitando a hierarquia de estados:
          correta (3) > presente (2) > ausente (1) > neutro (0)
        Uma vez verde, a tecla não regride para amarelo ou cinza.
        """
        hier = {"correta": 3, "presente": 2, "ausente": 1, "": 0}
        if hier.get(estado, 0) > hier.get(self.estados.get(letra, ""), 0):
            self.estados[letra] = estado

    def atualizar_area(self, area: pygame.Rect):
        """Recalcula os Rects das teclas após redimensionamento da janela."""
        self.area = area
        self.rects.clear()
        self._build()

    def _cor_tecla(self, key: str) -> tuple:
        """Retorna a cor de fundo da tecla de acordo com seu estado atual."""
        if key in ("ENTER", "<<"):
            return COR_TECLA_SPEC
        est = self.estados.get(key, "")
        return {
            "correta":  COR_TECLA_C,
            "presente": COR_TECLA_P,
            "ausente":  COR_TECLA_A,
            "":         COR_TECLA_N,
        }.get(est, COR_TECLA_N)

    def clique(self, pos) -> str:
        """
        Retorna o nome da tecla clicada em 'pos', ou string vazia se
        nenhuma tecla foi atingida.
        """
        for key, rect in self.rects.items():
            if rect.collidepoint(pos):
                return key
        return ""

    def draw(self, surface):
        """Desenha todas as teclas com sombra, brilho sutil e rótulo."""
        for key, rect in self.rects.items():
            cor = self._cor_tecla(key)

            # Sombra deslocada para baixo (efeito de profundidade)
            pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 3), border_radius=7)
            # Corpo principal da tecla
            pygame.draw.rect(surface, cor, rect, border_radius=7)

            # Brilho sutil no terço superior (simula luz vinda de cima)
            br = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, rect.h // 3)
            bs = pygame.Surface((br.w, br.h), pygame.SRCALPHA)
            bs.fill((255, 255, 255, 20))
            surface.blit(bs, br.topleft)

            # Rótulo: "DEL" para "<<", fonte menor para "ENTER"
            lbl = "DEL" if key == "<<" else key
            f   = self.font_sm if key == "ENTER" else self.font
            s   = f.render(lbl, True, COR_TEXTO)
            surface.blit(s, s.get_rect(center=rect.center))


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Particulas
# ─────────────────────────────────────────────────────────────────────

class Particula:
    """
    Fragmento individual de confete emitido ao vencer.
    Cada partícula tem posição, velocidade, cor, tamanho e rotação aleatórios.
    """
    CORES = [COR_CORRETA, COR_PRESENTE, (255, 215, 65),
             (255, 120, 120), (120, 180, 255), (200, 255, 200)]

    def __init__(self, x, y):
        ang      = random.uniform(0, math.pi * 2)       # direção aleatória
        spd      = random.uniform(100, 320)              # velocidade inicial
        self.x   = float(x)
        self.y   = float(y)
        self.vx  = math.cos(ang) * spd
        self.vy  = math.sin(ang) * spd - random.uniform(60, 200)   # impulso para cima
        self.vida = random.uniform(0.9, 1.8)   # tempo de vida em segundos
        self.vmax = self.vida                  # armazena o máximo para calcular alpha
        self.cor  = random.choice(self.CORES)
        self.w    = random.randint(5, 11)      # largura do fragmento
        self.h    = random.randint(4, 8)       # altura do fragmento
        self.rot  = random.uniform(0, 360)     # rotação inicial em graus
        self.rot_v = random.uniform(-180, 180) # velocidade angular (graus/s)

    def update(self, dt):
        """Aplica física simples: gravidade, movimento e rotação."""
        self.vy   += 380 * dt    # aceleração da gravidade
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.rot  += self.rot_v * dt
        self.vida -= dt

    @property
    def vivo(self):
        """True enquanto a partícula ainda tem tempo de vida restante."""
        return self.vida > 0

    def draw(self, surface):
        """Desenha o fragmento rotacionado com alpha proporcional à vida restante."""
        alpha = max(0, int(255 * (self.vida / self.vmax)))
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((*self.cor, alpha))
        # Calcula as dimensões do bounding box após a rotação
        rd = math.radians(self.rot % 90)
        w2 = abs(self.w * math.cos(rd)) + abs(self.h * math.sin(rd))
        h2 = abs(self.w * math.sin(rd)) + abs(self.h * math.cos(rd))
        rs = pygame.transform.rotate(s, self.rot)
        surface.blit(rs, (int(self.x - w2 / 2), int(self.y - h2 / 2)))


class SistemaParticulas:
    """Gerencia um pool de partículas: emissão, atualização e desenho em lote."""

    def __init__(self):
        self.ps = []   # lista de partículas ativas

    def emitir(self, x, y, n=100):
        """Cria 'n' partículas novas a partir do ponto (x, y)."""
        for _ in range(n):
            self.ps.append(Particula(x, y))

    def update(self, dt):
        """Remove partículas mortas e atualiza as vivas."""
        self.ps = [p for p in self.ps if p.vivo]
        for p in self.ps:
            p.update(dt)

    def draw(self, surface):
        """Desenha todas as partículas ativas."""
        for p in self.ps:
            p.draw(surface)


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Flashcard
# ─────────────────────────────────────────────────────────────────────

class Flashcard:
    """
    Card de resultado final exibido após vitória ou derrota.
    Apresenta a palavra correta, o contexto educacional e o botão
    para jogar novamente. Entra na tela com animação de slide-up.
    """

    PAD = 34    # padding interno do card em pixels
    DUR = 0.45  # duração da animação de entrada (segundos)

    def __init__(self, ganhou, palavra_orig, palavra_norm, contexto, sw, sh):
        self.ganhou       = ganhou        # True → vitória, False → derrota
        self.palavra_orig = palavra_orig  # palavra com acentos para exibição
        self.palavra_norm = palavra_norm  # palavra normalizada (fallback)
        self.contexto     = contexto      # texto educacional sobre a palavra
        self.sw, self.sh  = sw, sh        # dimensões atuais da tela

        # Fontes internas do card
        self.f_titulo  = carregar_fonte(36, negrito=True)
        self.f_palavra = carregar_fonte(52, negrito=True)
        self.f_ctx     = carregar_fonte(20)
        self.f_hint    = carregar_fonte(15)
        self.f_label   = carregar_fonte(12)

        self.card_w = min(570, sw - 56)
        self.linhas = quebrar_texto(self.f_ctx, contexto, self.card_w - self.PAD * 2)
        self._calc_card_h()   # calcula altura e posiciona o Rect
        self._t = 0.0         # tempo acumulado da animação de entrada

    def _calc_card_h(self):
        """Calcula a altura total do card com base no conteúdo e posiciona o Rect."""
        h  = self.PAD
        h += self.f_titulo.get_height()  + 16
        h += 1 + 12
        h += self.f_label.get_height()   + 5
        h += self.f_palavra.get_height() + 14
        h += 1 + 10
        for _ in self.linhas:
            h += self.f_ctx.get_height() + 5
        h += 12 + 1 + 10
        h += self.f_hint.get_height() + 14
        h += self.PAD
        self.card_h = h
        # Centraliza o card na tela
        self.rect = pygame.Rect((self.sw - self.card_w) // 2,
                                 (self.sh - self.card_h) // 2,
                                 self.card_w, self.card_h)

    def update(self, dt):
        """Avança a animação de entrada até o fim."""
        self._t = min(self._t + dt, self.DUR)

    def atualizar_area(self, sw, sh):
        """Reposiciona e reformata o card após redimensionamento da janela."""
        self.sw, self.sh = sw, sh
        self.card_w = min(570, sw - 56)
        self.linhas = quebrar_texto(self.f_ctx, self.contexto, self.card_w - self.PAD * 2)
        self._calc_card_h()

    def draw(self, surface):
        """
        Desenha o overlay escuro e o card com animação de slide-up.
        O card desce 50 px antes de subir para a posição final (ease-out cúbico).
        """
        prog  = ease_out_cubic(self._t / self.DUR)
        off_y = int(50 * (1 - prog))   # deslocamento que vai de 50 → 0

        # Overlay semitransparente sobre o jogo
        ov = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, int(190 * prog)))
        surface.blit(ov, (0, 0))

        r         = self.rect.move(0, off_y)
        cor_borda = COR_WIN_BORDA if self.ganhou else COR_LOSE_BORDA

        # Sombra do card
        sombra = r.inflate(8, 8).move(4, 6)
        pygame.draw.rect(surface, (0, 0, 0), sombra, border_radius=20)
        # Fundo e borda do card
        pygame.draw.rect(surface, COR_FLASH_BG, r, border_radius=20)
        pygame.draw.rect(surface, cor_borda, r, width=3, border_radius=20)
        # Brilho sutil no topo do card
        brilho = pygame.Surface((r.w - 4, r.h // 4), pygame.SRCALPHA)
        brilho.fill((255, 255, 255, 10))
        surface.blit(brilho, (r.x + 2, r.y + 2))

        cx = r.centerx
        y  = r.top + self.PAD

        # Título ("Você Venceu!" ou "Fim de Jogo!")
        titulo = "Você Venceu!" if self.ganhou else "Fim de Jogo!"
        cor_t  = COR_WIN_TITULO if self.ganhou else COR_LOSE_TITULO
        st = self.f_titulo.render(titulo, True, cor_t)
        surface.blit(st, st.get_rect(centerx=cx, top=y))
        y += st.get_height() + 16

        pygame.draw.line(surface, cor_borda, (r.left + 28, y), (r.right - 28, y), 1)
        y += 12

        # Rótulo "PALAVRA CORRETA" e a palavra em destaque
        sl = self.f_label.render("PALAVRA CORRETA", True, COR_TEXTO_DIM)
        surface.blit(sl, sl.get_rect(centerx=cx, top=y))
        y += sl.get_height() + 5

        exibir = (self.palavra_orig or self.palavra_norm).upper()
        sp = self.f_palavra.render(exibir, True, COR_PALAVRA_HL)
        surface.blit(sp, sp.get_rect(centerx=cx, top=y))
        y += sp.get_height() + 14

        pygame.draw.line(surface, (50, 50, 72), (r.left + 28, y), (r.right - 28, y), 1)
        y += 10

        # Texto educacional quebrado em linhas
        for linha in self.linhas:
            sc = self.f_ctx.render(linha, True, COR_TEXTO)
            surface.blit(sc, sc.get_rect(centerx=cx, top=y))
            y += sc.get_height() + 5

        y += 12
        pygame.draw.line(surface, (50, 50, 72), (r.left + 28, y), (r.right - 28, y), 1)
        y += 10

        # Botão "jogar novamente"
        hint  = "Pressione  ESPAÇO  para jogar novamente"
        sh_s  = self.f_hint.render(hint, True, COR_TITULO)
        hr    = sh_s.get_rect(centerx=cx, top=y)
        btn   = hr.inflate(26, 14)
        pygame.draw.rect(surface, (38, 38, 58), btn, border_radius=10)
        pygame.draw.rect(surface, COR_WIN_BORDA, btn, width=1, border_radius=10)
        surface.blit(sh_s, hr)


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Jogo
# ─────────────────────────────────────────────────────────────────────

class Jogo:
    """
    Controlador principal: inicializa o pygame, gerencia o loop de jogo,
    processa eventos e orquestra todos os subsistemas.
    """

    EV_FLASH   = pygame.USEREVENT + 1   # evento agendado para abrir o flashcard
    EV_CONFETE = pygame.USEREVENT + 2   # evento agendado para emitir confetes

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Termo Ambiental")
        self.clock = pygame.time.Clock()

        # Fontes globais (cabeçalho e mensagens)
        self.f_titulo = carregar_fonte(24, negrito=True)
        self.f_sub    = carregar_fonte(14)
        self.f_msg    = carregar_fonte(17, negrito=True)

        self.dados = self._carregar_json()   # lista de palavras + contextos
        self.bg    = self._criar_bg()        # superfície com gradiente de fundo

        self.particulas = SistemaParticulas()
        self.tabuleiro  = None
        self.teclado    = None
        self.flashcard  = None

        # ── Fila de atualizações de teclado agendadas ─────────────────
        # Cada item: (tempo_de_disparo, letra, estado)
        # As cores do teclado aparecem letra a letra, sincronizadas com
        # o momento exato em que cada célula vira (metade do flip).
        self._kbd_pending: list = []
        self._tempo: float      = 0.0   # cronômetro global acumulado em segundos

        self._nova_partida()

    # ── Background ────────────────────────────────────────────────────
    def _criar_bg(self) -> pygame.Surface:
        """Cria uma superfície com gradiente vertical de COR_BG_TOP a COR_BG_BOT."""
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            cor = lerp_cor(COR_BG_TOP, COR_BG_BOT, y / SCREEN_H)
            pygame.draw.line(bg, cor, (0, y), (SCREEN_W, y))
        return bg

    # ── JSON ──────────────────────────────────────────────────────────
    def _carregar_json(self) -> list:
        """
        Carrega o arquivo JSON de palavras do mesmo diretório do script
        ou do diretório de trabalho atual. Encerra o jogo se não encontrar.
        Pré-computa a versão normalizada de cada palavra como '_norm'.
        """
        for path in [os.path.join(os.path.dirname(__file__), JSON_FILE), JSON_FILE]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                for d in dados:
                    d["_norm"] = normalizar(d["palavra"])
                return dados
        print(f"[ERRO] '{JSON_FILE}' não encontrado.")
        pygame.quit()
        sys.exit(1)

    # ── Nova partida ──────────────────────────────────────────────────
    def _nova_partida(self):
        """
        Sorteia uma nova palavra e recria todos os componentes visuais
        zerados para iniciar uma partida limpa.
        """
        self.entrada  = random.choice(self.dados)
        self.p_norm   = self.entrada["_norm"]    # palavra sem acentos, maiúscula
        self.p_orig   = self.entrada["palavra"]  # palavra original (com acentos)
        self.contexto = self.entrada["contexto"] # texto educacional
        self.p_len    = len(self.p_norm)

        # Fonte das letras nas células: escala com o tamanho da célula
        fs = max(22, min(40, int(CELL_MAX_SIZE * 0.50)))
        self.f_cel = carregar_fonte(fs, negrito=True)
        w, h = self.screen.get_size()

        # Áreas de layout
        board_y    = HEADER_H + 8
        board_h    = h - HEADER_H - KEYBOARD_H - 16
        board_area = pygame.Rect(20, board_y, w - 40, board_h)
        kbd_area   = pygame.Rect(10, h - KEYBOARD_H + 5, w - 20, KEYBOARD_H - 10)

        self.tabuleiro  = Tabuleiro(self.p_len, MAX_TENTATIVAS, board_area)
        self.teclado    = TecladoVirtual(kbd_area)
        self.flashcard  = None
        self.game_over  = False
        self.ganhou     = False
        self.mensagem   = ""
        self.msg_timer  = 0.0
        self.particulas = SistemaParticulas()

        # Limpa fila de atualizações pendentes do teclado
        self._kbd_pending.clear()

        # Cancela quaisquer timers de eventos pendentes
        pygame.time.set_timer(self.EV_FLASH,   0)
        pygame.time.set_timer(self.EV_CONFETE, 0)

    # ── Validação ─────────────────────────────────────────────────────
    def _validar(self, tentativa: str) -> list:
        """
        Algoritmo Wordle em 2 passos para tratar letras duplicadas corretamente.

        Passo 1: marca posições CORRETAS e consome essas letras da palavra secreta.
        Passo 2: marca PRESENTES (letras que existem mas estão fora de lugar)
                 usando apenas as posições ainda não consumidas.

        Retorna lista de strings: "correta", "presente" ou "ausente".
        """
        n        = self.p_len
        res      = ["ausente"] * n
        restante = list(self.p_norm)   # cópia mutável para controle de consumo

        # Passo 1: posições exatas
        for i in range(n):
            if tentativa[i] == self.p_norm[i]:
                res[i]      = "correta"
                restante[i] = None   # consome a letra da palavra secreta

        # Passo 2: letras presentes fora de lugar
        for i in range(n):
            if res[i] == "correta":
                continue
            if tentativa[i] in restante:
                res[i] = "presente"
                restante[restante.index(tentativa[i])] = None

        return res

    # ── Confirmar tentativa ───────────────────────────────────────────
    def _confirmar(self):
        """
        Valida e processa a tentativa atual.

        [MODIFICADO] A verificação de completude agora inspeciona todas as
        células da linha (não apenas o comprimento da string), pois com a
        seleção por clique o jogador pode deixar buracos no meio da linha.
        """
        tent = self.tabuleiro.get_tentativa()
        # Verifica se alguma célula da linha ativa ainda está vazia
        if len(tent) < self.p_len or "" in [
            c.letra for c in self.tabuleiro.celulas[self.tabuleiro.tentativa_atual]
        ]:
            self._msg("Palavra incompleta!")
            self.tabuleiro.shake()
            return

        res    = self._validar(tent)
        ganhou = (tent == self.p_norm)
        self.tabuleiro.aplicar_resultado(res, ganhou=ganhou)

        # ── Agenda as cores do teclado letra a letra ──────────────────
        # Cada tecla acende no exato momento em que a célula correspondente
        # chega à metade do flip (scaleY ≈ 0), revelando a cor.
        flip_meio = Celula.FLIP_DUR / 2
        for i, letra in enumerate(tent):
            t_reveal = (self._tempo
                        + i * Tabuleiro.FLIP_COL_DELAY   # delay da coluna
                        + flip_meio)                     # metade do flip
            self._kbd_pending.append((t_reveal, letra, res[i]))

        if ganhou:
            self.ganhou    = True
            self.game_over = True
            flip_total   = (self.p_len * Tabuleiro.FLIP_COL_DELAY
                            + Celula.FLIP_DUR + 0.10)
            bounce_total = (flip_total
                            + self.p_len * Tabuleiro.BOUNCE_COL_DELAY
                            + Celula.BOUNCE_DUR + 0.25)
            pygame.time.set_timer(self.EV_CONFETE, int(flip_total   * 1000))
            pygame.time.set_timer(self.EV_FLASH,   int(bounce_total * 1000))

        elif self.tabuleiro.tentativa_atual >= MAX_TENTATIVAS:
            self.game_over = True
            flip_total = (self.p_len * Tabuleiro.FLIP_COL_DELAY
                          + Celula.FLIP_DUR + 0.10)
            pygame.time.set_timer(self.EV_FLASH, int(flip_total * 1000) + 300)

    def _msg(self, texto, dur=2.0):
        """Exibe uma mensagem temporária no centro da tela por 'dur' segundos."""
        self.mensagem  = texto
        self.msg_timer = dur

    # ── Eventos ───────────────────────────────────────────────────────
    def _handle_events(self):
        """
        Processa todos os eventos pygame do frame atual.

        [NOVO] Cliques no tabuleiro têm prioridade sobre o teclado virtual:
          1. Se o clique acertar uma célula da linha ativa → move o cursor
             e consome o evento (continue), sem repassar ao teclado.
          2. Caso contrário → testa o teclado virtual normalmente.

        [NOVO] Teclas de seta ← → movem o cursor coluna a coluna dentro
          da linha atual sem alterar nenhuma letra.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                self._tratar_redimensionamento(event.w, event.h)

            # Abre o flashcard após o tempo calculado em _confirmar()
            if event.type == self.EV_FLASH:
                pygame.time.set_timer(self.EV_FLASH, 0)
                w, h = self.screen.get_size()
                self.flashcard = Flashcard(
                    self.ganhou, self.p_orig, self.p_norm,
                    self.contexto, w, h
                )

            # Emite confetes após o flip terminar (só na vitória)
            if event.type == self.EV_CONFETE:
                pygame.time.set_timer(self.EV_CONFETE, 0)
                w, h = self.screen.get_size()
                self.particulas.emitir(w // 2, h // 3, n=150)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clique com flashcard aberto → nova partida
                if self.flashcard:
                    self._nova_partida()
                    return

                if not self.game_over:
                    # [NOVO] Prioridade 1: clique em célula do tabuleiro
                    # Se o clique foi consumido, não repassa ao teclado
                    if self.tabuleiro.clicar_celula(event.pos):
                        continue

                    # Prioridade 2: teclado virtual
                    k = self.teclado.clique(event.pos)
                    if k == "ENTER":
                        self._confirmar()
                    elif k == "<<":
                        self.tabuleiro.apagar()
                    elif len(k) == 1:
                        self.tabuleiro.digitar(normalizar(k))

            if event.type == pygame.KEYDOWN:
                # ESPAÇO com flashcard aberto → nova partida
                if event.key == pygame.K_SPACE and self.flashcard:
                    self._nova_partida()
                    return
                if self.game_over:
                    continue

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirmar()
                elif event.key == pygame.K_BACKSPACE:
                    self.tabuleiro.apagar()

                # [NOVO] Setas movem o cursor sem alterar letras
                elif event.key == pygame.K_LEFT:
                    if self.tabuleiro.posicao_atual > 0:
                        self.tabuleiro.posicao_atual -= 1
                        self.tabuleiro.cursor_col    = self.tabuleiro.posicao_atual
                elif event.key == pygame.K_RIGHT:
                    if self.tabuleiro.posicao_atual < self.tabuleiro.palavra_len - 1:
                        self.tabuleiro.posicao_atual += 1
                        self.tabuleiro.cursor_col    = self.tabuleiro.posicao_atual

                elif event.unicode and event.unicode.isalpha():
                    self.tabuleiro.digitar(normalizar(event.unicode[0]))

    # ── Processar fila do teclado ─────────────────────────────────────
    def _processar_kbd_pending(self):
        """
        Percorre a fila de atualizações agendadas para o teclado e dispara
        as que já atingiram seu tempo de revelação.
        Itens ainda no futuro são mantidos na fila para o próximo frame.
        """
        ainda_pendentes = []
        for (t_fire, letra, estado) in self._kbd_pending:
            if self._tempo >= t_fire:
                self.teclado.atualizar(letra, estado)
            else:
                ainda_pendentes.append((t_fire, letra, estado))
        self._kbd_pending = ainda_pendentes

    # ── Render ────────────────────────────────────────────────────────
    def _draw_header(self):
        """Desenha o cabeçalho: faixa colorida, título e informações da partida."""
        w = self.screen.get_width()
        pygame.draw.rect(self.screen, COR_HEADER_BG, (0, 0, w, HEADER_H))

        # Faixa de gradiente de 3 px no topo (de teal a bege)
        for x in range(w):
            t   = x / w
            cor = lerp_cor(COR_CORRETA, COR_PRESENTE, t)
            pygame.draw.line(self.screen, cor, (x, 0), (x, 3))

        pygame.draw.line(self.screen, COR_DIVIDER, (0, HEADER_H), (w, HEADER_H), 1)

        s = self.f_titulo.render("TERMO AMBIENTAL", True, COR_TITULO)
        self.screen.blit(s, s.get_rect(centerx=w // 2, top=14))

        tent_rest = MAX_TENTATIVAS - self.tabuleiro.tentativa_atual
        info = (f"{self.p_len} letras  •  "
                f"{tent_rest} tentativa{'s' if tent_rest != 1 else ''} "
                f"restante{'s' if tent_rest != 1 else ''}")
        s2 = self.f_sub.render(info, True, COR_TEXTO_DIM)
        self.screen.blit(s2, s2.get_rect(centerx=w // 2, top=46))

        # Acento teal embaixo do título
        pygame.draw.line(self.screen, (50, 100, 90),
                         (w // 2 - 60, HEADER_H - 1), (w // 2 + 60, HEADER_H - 1), 2)

    def _draw_kbd_bg(self):
        """Desenha o fundo escuro e a linha divisória da área do teclado."""
        w = self.screen.get_width()
        h = self.screen.get_height()
        r = pygame.Rect(0, h - KEYBOARD_H, w, KEYBOARD_H)
        pygame.draw.rect(self.screen, (16, 16, 28), r)
        pygame.draw.line(self.screen, COR_DIVIDER, (0, r.top), (w, r.top), 1)

    def _draw_msg(self):
        """Desenha a mensagem temporária centralizada abaixo do cabeçalho."""
        if not self.mensagem or self.msg_timer <= 0:
            return
        w = self.screen.get_width()
        s  = self.f_msg.render(self.mensagem, True, COR_TEXTO)
        r  = s.get_rect(centerx=w // 2, top=HEADER_H + 8)
        bg = r.inflate(30, 14)
        pygame.draw.rect(self.screen, (38, 38, 60), bg, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 110), bg, width=1, border_radius=10)
        self.screen.blit(s, r)

    def _draw(self):
        """Compõe o frame completo: fundo, cabeçalho, grade, teclado e sobreposições."""
        self.screen.blit(self.bg, (0, 0))
        self._draw_header()
        self._draw_kbd_bg()
        # [NOVO] Passa pulse_t para que o Tabuleiro possa animar a borda do cursor
        self.tabuleiro.draw(self.screen, self.f_cel, pulse_t=self._tempo)
        self.teclado.draw(self.screen)
        self.particulas.draw(self.screen)
        self._draw_msg()
        if self.flashcard:
            self.flashcard.draw(self.screen)
        pygame.display.flip()

    def _tratar_redimensionamento(self, w, h):
        """
        Atualiza a resolução e redistribui todas as áreas de layout
        quando o jogador redimensiona a janela.
        """
        global SCREEN_W, SCREEN_H
        SCREEN_W = max(w, 400)   # largura mínima de 400 px
        SCREEN_H = max(h, 600)   # altura mínima de 600 px
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        self.bg     = self._criar_bg()   # recria o gradiente no novo tamanho

        board_y    = HEADER_H + 8
        board_h    = SCREEN_H - HEADER_H - KEYBOARD_H - 16
        board_area = pygame.Rect(20, board_y, SCREEN_W - 40, board_h)
        kbd_area   = pygame.Rect(10, SCREEN_H - KEYBOARD_H + 5,
                                  SCREEN_W - 20, KEYBOARD_H - 10)

        if self.tabuleiro:
            self.tabuleiro.atualizar_area(board_area)
            fs = max(22, min(40, int(self.tabuleiro.cell_size * 0.50)))
            self.f_cel = carregar_fonte(fs, negrito=True)
        if self.teclado:
            self.teclado.atualizar_area(kbd_area)
        if self.flashcard:
            self.flashcard.atualizar_area(SCREEN_W, SCREEN_H)

    # ── Loop principal ────────────────────────────────────────────────
    def run(self):
        """
        Loop principal do jogo (roda a 60 FPS):
          1. Avança o cronômetro global
          2. Processa eventos
          3. Processa atualizações agendadas do teclado
          4. Conta regressiva da mensagem temporária
          5. Atualiza animações
          6. Desenha o frame
        """
        while True:
            dt = self.clock.tick(FPS) / 1000.0   # delta em segundos
            self._tempo += dt                     # cronômetro global acumulado

            self._handle_events()
            self._processar_kbd_pending()   # cores do teclado letra a letra

            if self.msg_timer > 0:
                self.msg_timer -= dt
                if self.msg_timer <= 0:
                    self.mensagem = ""

            self.tabuleiro.update(dt)
            self.particulas.update(dt)
            if self.flashcard:
                self.flashcard.update(dt)

            self._draw()


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    jogo = Jogo()
    jogo.run()