"""
╔══════════════════════════════════════════════════════════════════════╗
║         TERMO AMBIENTAL  –  Redesign Visual v3                      ║
║  Flip suave + teclado com cores por letra (igual Termo.ooo)         ║
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

SCREEN_W        = 700
SCREEN_H        = 920
FPS             = 60
MAX_TENTATIVAS  = 6
CELL_MARGIN     = 7
CELL_MAX_SIZE   = 74
JSON_FILE       = "palavras_ambientais.json"

HEADER_H        = 80
KEYBOARD_H      = 215

# ── Paleta (estilo Termo.ooo) ──────────────────────────────────────────
COR_BG_TOP      = (20,  20,  34)
COR_BG_BOT      = (12,  12,  22)
COR_HEADER_BG   = (24,  24,  38)
COR_DIVIDER     = (48,  48,  70)

COR_CELULA_VZ   = (44,  44,  64)
COR_CELULA_BD   = (70,  70,  98)
COR_CELULA_AT   = (60,  60,  85)
COR_CELULA_BDA  = (110, 110, 150)

COR_CORRETA     = (83,  205, 174)   # teal  – posição correta
COR_PRESENTE    = (200, 167, 112)   # bege  – presente fora de lugar
COR_AUSENTE     = (30,   30,  44)   # quase preto – ausente

COR_TEXTO       = (255, 255, 255)
COR_TEXTO_DIM   = (100, 100, 135)
COR_TITULO      = (83,  205, 174)

COR_TECLA_N     = (50,  50,  75)    # neutra
COR_TECLA_C     = (65,  165, 140)   # correta
COR_TECLA_P     = (170, 140,  90)   # presente
COR_TECLA_A     = (28,  28,  42)    # ausente
COR_TECLA_SPEC  = (68,  68,  95)    # ENTER / <<

COR_FLASH_BG    = (18,  18,  30)
COR_WIN_BORDA   = (83,  205, 174)
COR_LOSE_BORDA  = (210,  70,  80)
COR_WIN_TITULO  = (83,  205, 174)
COR_LOSE_TITULO = (220,  80,  80)
COR_PALAVRA_HL  = (255, 215,  65)

KEYBOARD_ROWS = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["ENTER","Z","X","C","V","B","N","M","<<"],
]

# ─────────────────────────────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────

def normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()

def quebrar_texto(font, texto: str, max_w: int) -> list:
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
    for n in ["Arial", "DejaVuSans", "Helvetica", "FreeSans", "Ubuntu"]:
        try:
            return pygame.font.SysFont(n, tam, bold=negrito)
        except Exception:
            continue
    return pygame.font.Font(None, tam)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_cor(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    """Curva suave ideal para o flip – acelera e desacelera naturalmente."""
    return -(math.cos(math.pi * t) - 1) / 2


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Celula
# ─────────────────────────────────────────────────────────────────────

class Celula:
    """
    Três camadas de animação:
      1) Pop    – escala ao digitar (0.13s)
      2) Flip   – scaleY com ease-in-out-sine, delay por coluna
      3) Bounce – salto ao vencer, delay por coluna
    """

    # ── Durações ─────────────────────────────────────────────────────
    POP_DUR    = 0.13   # pequeno "pop" ao digitar
    FLIP_DUR   = 0.70   # duração total de cada flip  ← aumentado (era 0.42)
    BOUNCE_DUR = 0.60

    def __init__(self, x, y, size):
        self.base   = pygame.Rect(x, y, size, size)
        self.letra  = ""
        self.estado = "vazio"

        # Pop
        self._pop_t    = 0.0
        self._popping  = False

        # Flip
        self._flip_t        = 0.0
        self._flip_delay    = 0.0
        self._flipping      = False
        self._flip_revealed = False
        self._flip_alvo     = None

        # Bounce
        self._bnc_t    = 0.0
        self._bnc_delay = 0.0
        self._bouncing  = False

    # ── Disparadores ─────────────────────────────────────────────────
    def pop(self):
        self._pop_t   = 0.0
        self._popping = True

    def flip(self, estado_final: str, delay: float):
        self._flip_alvo     = estado_final
        self._flip_delay    = delay
        self._flip_t        = 0.0
        self._flip_revealed = False
        self._flipping      = True

    def bounce(self, delay: float):
        self._bnc_delay = delay
        self._bnc_t     = 0.0
        self._bouncing  = True

    # ── Cores ─────────────────────────────────────────────────────────
    def cor(self):
        return {
            "vazio":    COR_CELULA_VZ,
            "ativo":    COR_CELULA_AT,
            "correta":  COR_CORRETA,
            "presente": COR_PRESENTE,
            "ausente":  COR_AUSENTE,
        }.get(self.estado, COR_CELULA_VZ)

    # ── Update ────────────────────────────────────────────────────────
    def update(self, dt: float):
        if self._popping:
            self._pop_t += dt
            if self._pop_t >= self.POP_DUR:
                self._popping = False

        if self._flipping:
            self._flip_t += dt
            efet = self._flip_t - self._flip_delay
            if efet > 0:
                prog = efet / self.FLIP_DUR
                # Exatamente na metade → troca cor (célula está "de lado")
                if prog >= 0.5 and not self._flip_revealed:
                    self._flip_revealed = True
                    self.estado         = self._flip_alvo
                if prog >= 1.0:
                    self._flipping = False

        if self._bouncing:
            self._bnc_t += dt
            if (self._bnc_t - self._bnc_delay) >= self.BOUNCE_DUR:
                self._bouncing = False

    # ── Transformações ────────────────────────────────────────────────
    def redimensionar(self, x, y, size):
        self.base = pygame.Rect(x, y, size, size)
        
    def _scale_pop(self) -> float:
        if not self._popping:
            return 1.0
        t = self._pop_t / self.POP_DUR
        return 1.0 + 0.12 * math.sin(t * math.pi)

    def _scale_y_flip(self) -> float:
        """
        ScaleY usando ease-in-out-sine:
          – Primeira metade  (0→0.5): comprime de 1 → 0  (ease-in)
          – Segunda metade   (0.5→1): expande de 0 → 1   (ease-out)
        Resultado: animação suave e natural, sem travamento no começo/fim.
        """
        if not self._flipping:
            return 1.0
        efet = self._flip_t - self._flip_delay
        if efet <= 0:
            return 1.0
        t = min(efet / self.FLIP_DUR, 1.0)

        if t < 0.5:
            # ease-in: 1 → 0
            e = ease_in_out_sine(t * 2)      # mapeia 0-0.5 para 0-1
            return 1.0 - e
        else:
            # ease-out: 0 → 1
            e = ease_in_out_sine((t - 0.5) * 2)
            return e

    def _off_bounce(self) -> float:
        if not self._bouncing:
            return 0.0
        efet = self._bnc_t - self._bnc_delay
        if efet <= 0:
            return 0.0
        t = min(efet / self.BOUNCE_DUR, 1.0)
        return -32 * math.sin(t * math.pi)

    # ── Draw ──────────────────────────────────────────────────────────
    def draw(self, surface, font, shake_dx=0):
        cor   = self.cor()
        sy    = self._scale_y_flip()
        sxy   = self._scale_pop()
        off_y = self._off_bounce()

        r = self.base.copy()
        r.x += shake_dx
        r.y += int(off_y)

        # Pop: inflate uniforme
        if sxy != 1.0:
            dw = int(r.width  * (sxy - 1))
            dh = int(r.height * (sxy - 1))
            r.inflate_ip(dw, dh)
            r.centerx = self.base.centerx + shake_dx
            r.centery  = self.base.centery + int(off_y)

        # Flip: comprime em Y mantendo centro
        if sy < 1.0:
            nh = max(2, int(r.height * sy))
            cy = r.centery
            r.height  = nh
            r.centery = cy

        pygame.draw.rect(surface, cor, r, border_radius=6)

        # Bordas (apenas para células sem resultado)
        if self.estado == "vazio":
            pygame.draw.rect(surface, COR_CELULA_BD,
                             pygame.Rect(self.base.x + shake_dx, self.base.y,
                                         self.base.w, self.base.h),
                             width=2, border_radius=6)
        elif self.estado == "ativo":
            pygame.draw.rect(surface, COR_CELULA_BDA,
                             pygame.Rect(self.base.x + shake_dx, self.base.y,
                                         self.base.w, self.base.h),
                             width=2, border_radius=6)

        # Letra – oculta quando a célula está quase de lado
        if self.letra and sy > 0.12:
            txt = font.render(self.letra, True, COR_TEXTO)
            surface.blit(txt, txt.get_rect(center=(r.centerx, r.centery)))


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Tabuleiro
# ─────────────────────────────────────────────────────────────────────

class Tabuleiro:
    """
    Grade adaptável com shake, flip escalonado e bounce de vitória.
    """

    FLIP_COL_DELAY   = 0.14   # delay entre colunas no flip  ← aumentado (era 0.09)
    BOUNCE_COL_DELAY = 0.08
    SHAKE_DUR        = 0.52
    SHAKE_AMP        = 9

    def __init__(self, palavra_len, max_tent, area):
        self.palavra_len     = palavra_len
        self.max_tent        = max_tent
        self.area            = area
        self.celulas         = []
        self.tentativa_atual = 0
        self.posicao_atual   = 0
        self._shake_t        = 0.0
        self._shaking        = False
        self._shake_row      = -1
        self._construir()

    def _construir(self):
        cw = (self.area.w - CELL_MARGIN * (self.palavra_len + 1)) // self.palavra_len
        ch = (self.area.h - CELL_MARGIN * (self.max_tent    + 1)) // self.max_tent
        self.cell_size = min(cw, ch, CELL_MAX_SIZE)

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

    # ── API ───────────────────────────────────────────────────────────
    def digitar(self, letra: str):
        if self.posicao_atual < self.palavra_len and self.tentativa_atual < self.max_tent:
            c = self.celulas[self.tentativa_atual][self.posicao_atual]
            c.letra  = letra
            c.estado = "ativo"
            c.pop()
            self.posicao_atual += 1

    def apagar(self):
        if self.posicao_atual > 0:
            self.posicao_atual -= 1
            c = self.celulas[self.tentativa_atual][self.posicao_atual]
            c.letra  = ""
            c.estado = "vazio"

    def atualizar_area(self, area):
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
        return "".join(c.letra for c in self.celulas[self.tentativa_atual])

    def aplicar_resultado(self, resultado: list, ganhou=False):
        n          = len(resultado)
        flip_total = n * self.FLIP_COL_DELAY + Celula.FLIP_DUR

        for i, est in enumerate(resultado):
            delay_flip = i * self.FLIP_COL_DELAY
            self.celulas[self.tentativa_atual][i].flip(est, delay_flip)
            if ganhou:
                delay_bnc = flip_total + i * self.BOUNCE_COL_DELAY
                self.celulas[self.tentativa_atual][i].bounce(delay_bnc)

        self.tentativa_atual += 1
        self.posicao_atual    = 0

    def shake(self):
        self._shaking   = True
        self._shake_t   = 0.0
        self._shake_row = self.tentativa_atual

    # ── Update / Draw ─────────────────────────────────────────────────
    def update(self, dt):
        if self._shaking:
            self._shake_t += dt
            if self._shake_t >= self.SHAKE_DUR:
                self._shaking = False
        for row in self.celulas:
            for c in row:
                c.update(dt)

    def _shake_dx(self) -> int:
        if not self._shaking:
            return 0
        p = self._shake_t / self.SHAKE_DUR
        return int(self.SHAKE_AMP * math.sin(p * math.pi * 5) * (1 - p))

    def draw(self, surface, font):
        dx = self._shake_dx()
        for ri, row in enumerate(self.celulas):
            sdx = dx if ri == self._shake_row else 0
            for c in row:
                c.draw(surface, font, shake_dx=sdx)


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: TecladoVirtual
# ─────────────────────────────────────────────────────────────────────

class TecladoVirtual:
    """
    Teclado QWERTY clicável.
    Cores: correta (teal) > presente (bege) > ausente (quase preto) > neutro
    As cores são aplicadas LETRA A LETRA conforme cada célula revela seu resultado.
    """

    KEY_H   = 50
    KEY_GAP = 5

    def __init__(self, area: pygame.Rect):
        self.area    = area
        self.estados = {}   # letra → estado
        self.rects   = {}   # tecla → Rect
        self.font    = carregar_fonte(14, negrito=True)
        self.font_sm = carregar_fonte(11, negrito=True)
        self._build()

    def _build(self):
        row_h   = self.KEY_H + self.KEY_GAP
        total_h = len(KEYBOARD_ROWS) * row_h - self.KEY_GAP
        start_y = self.area.centery - total_h // 2

        for ri, row in enumerate(KEYBOARD_ROWS):
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
        Hierarquia: correta (3) > presente (2) > ausente (1) > neutro (0).
        Uma vez verde, a tecla não volta para amarelo nem cinza.
        """
        hier = {"correta": 3, "presente": 2, "ausente": 1, "": 0}
        if hier.get(estado, 0) > hier.get(self.estados.get(letra, ""), 0):
            self.estados[letra] = estado
    
    def atualizar_area(self, area: pygame.Rect):
        self.area = area
        self.rects.clear()
        self._build()

    def _cor_tecla(self, key: str) -> tuple:
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
        for key, rect in self.rects.items():
            if rect.collidepoint(pos):
                return key
        return ""

    def draw(self, surface):
        for key, rect in self.rects.items():
            cor = self._cor_tecla(key)

            # Sombra
            pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 3), border_radius=7)
            # Tecla
            pygame.draw.rect(surface, cor, rect, border_radius=7)

            # Brilho sutil no topo
            br = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, rect.h // 3)
            bs = pygame.Surface((br.w, br.h), pygame.SRCALPHA)
            bs.fill((255, 255, 255, 20))
            surface.blit(bs, br.topleft)

            lbl = "DEL" if key == "<<" else key
            f   = self.font_sm if key == "ENTER" else self.font
            s   = f.render(lbl, True, COR_TEXTO)
            surface.blit(s, s.get_rect(center=rect.center))


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Particulas
# ─────────────────────────────────────────────────────────────────────

class Particula:
    CORES = [COR_CORRETA, COR_PRESENTE, (255, 215, 65),
             (255, 120, 120), (120, 180, 255), (200, 255, 200)]

    def __init__(self, x, y):
        ang      = random.uniform(0, math.pi * 2)
        spd      = random.uniform(100, 320)
        self.x   = float(x)
        self.y   = float(y)
        self.vx  = math.cos(ang) * spd
        self.vy  = math.sin(ang) * spd - random.uniform(60, 200)
        self.vida = random.uniform(0.9, 1.8)
        self.vmax = self.vida
        self.cor  = random.choice(self.CORES)
        self.w    = random.randint(5, 11)
        self.h    = random.randint(4, 8)
        self.rot  = random.uniform(0, 360)
        self.rot_v = random.uniform(-180, 180)

    def update(self, dt):
        self.vy   += 380 * dt
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.rot  += self.rot_v * dt
        self.vida -= dt

    @property
    def vivo(self):
        return self.vida > 0

    def draw(self, surface):
        alpha = max(0, int(255 * (self.vida / self.vmax)))
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((*self.cor, alpha))
        rd = math.radians(self.rot % 90)
        w2 = abs(self.w * math.cos(rd)) + abs(self.h * math.sin(rd))
        h2 = abs(self.w * math.sin(rd)) + abs(self.h * math.cos(rd))
        rs = pygame.transform.rotate(s, self.rot)
        surface.blit(rs, (int(self.x - w2 / 2), int(self.y - h2 / 2)))


class SistemaParticulas:
    def __init__(self):
        self.ps = []

    def emitir(self, x, y, n=100):
        for _ in range(n):
            self.ps.append(Particula(x, y))

    def update(self, dt):
        self.ps = [p for p in self.ps if p.vivo]
        for p in self.ps:
            p.update(dt)

    def draw(self, surface):
        for p in self.ps:
            p.draw(surface)


# ─────────────────────────────────────────────────────────────────────
#  CLASSE: Flashcard
# ─────────────────────────────────────────────────────────────────────

class Flashcard:
    """Tela final com slide-up animado e contexto educacional."""

    PAD = 34
    DUR = 0.45

    def __init__(self, ganhou, palavra_orig, palavra_norm, contexto, sw, sh):
        self.ganhou       = ganhou
        self.palavra_orig = palavra_orig
        self.palavra_norm = palavra_norm
        self.contexto     = contexto
        self.sw, self.sh  = sw, sh

        self.f_titulo  = carregar_fonte(36, negrito=True)
        self.f_palavra = carregar_fonte(52, negrito=True)
        self.f_ctx     = carregar_fonte(20)
        self.f_hint    = carregar_fonte(15)
        self.f_label   = carregar_fonte(12)

        self.card_w = min(570, sw - 56)
        self.linhas = quebrar_texto(self.f_ctx, contexto, self.card_w - self.PAD * 2)

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
        self.rect   = pygame.Rect((sw - self.card_w) // 2,
                                   (sh - self.card_h) // 2,
                                   self.card_w, self.card_h)
        self._t = 0.0

    def update(self, dt):
        self._t = min(self._t + dt, self.DUR)

    def atualizar_area(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.card_w = min(570, sw - 56)
        
        # Refaz a quebra de texto com a nova largura
        self.linhas = quebrar_texto(self.f_ctx, self.contexto, self.card_w - self.PAD * 2)
        
        # Recalcula a altura total
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
        self.rect   = pygame.Rect((sw - self.card_w) // 2,
                                   (sh - self.card_h) // 2,
                                   self.card_w, self.card_h)

    def draw(self, surface):
        prog  = ease_out_cubic(self._t / self.DUR)
        off_y = int(50 * (1 - prog))

        ov = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, int(190 * prog)))
        surface.blit(ov, (0, 0))

        r         = self.rect.move(0, off_y)
        cor_borda = COR_WIN_BORDA if self.ganhou else COR_LOSE_BORDA

        sombra = r.inflate(8, 8).move(4, 6)
        pygame.draw.rect(surface, (0, 0, 0), sombra, border_radius=20)
        pygame.draw.rect(surface, COR_FLASH_BG, r, border_radius=20)
        pygame.draw.rect(surface, cor_borda, r, width=3, border_radius=20)

        brilho = pygame.Surface((r.w - 4, r.h // 4), pygame.SRCALPHA)
        brilho.fill((255, 255, 255, 10))
        surface.blit(brilho, (r.x + 2, r.y + 2))

        cx = r.centerx
        y  = r.top + self.PAD

        titulo = "Você Venceu!" if self.ganhou else "Fim de Jogo!"
        cor_t  = COR_WIN_TITULO if self.ganhou else COR_LOSE_TITULO
        st = self.f_titulo.render(titulo, True, cor_t)
        surface.blit(st, st.get_rect(centerx=cx, top=y))
        y += st.get_height() + 16

        pygame.draw.line(surface, cor_borda, (r.left + 28, y), (r.right - 28, y), 1)
        y += 12

        sl = self.f_label.render("PALAVRA CORRETA", True, COR_TEXTO_DIM)
        surface.blit(sl, sl.get_rect(centerx=cx, top=y))
        y += sl.get_height() + 5

        exibir = (self.palavra_orig or self.palavra_norm).upper()
        sp = self.f_palavra.render(exibir, True, COR_PALAVRA_HL)
        surface.blit(sp, sp.get_rect(centerx=cx, top=y))
        y += sp.get_height() + 14

        pygame.draw.line(surface, (50, 50, 72), (r.left + 28, y), (r.right - 28, y), 1)
        y += 10

        for linha in self.linhas:
            sc = self.f_ctx.render(linha, True, COR_TEXTO)
            surface.blit(sc, sc.get_rect(centerx=cx, top=y))
            y += sc.get_height() + 5

        y += 12
        pygame.draw.line(surface, (50, 50, 72), (r.left + 28, y), (r.right - 28, y), 1)
        y += 10

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
    EV_FLASH   = pygame.USEREVENT + 1
    EV_CONFETE = pygame.USEREVENT + 2

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Termo Ambiental")
        self.clock = pygame.time.Clock()

        self.f_titulo = carregar_fonte(24, negrito=True)
        self.f_sub    = carregar_fonte(14)
        self.f_msg    = carregar_fonte(17, negrito=True)

        self.dados = self._carregar_json()
        self.bg    = self._criar_bg()

        self.particulas = SistemaParticulas()
        self.tabuleiro  = None
        self.teclado    = None
        self.flashcard  = None

        # ── Fila de atualizações de teclado agendadas ─────────────────
        # Cada item: (tempo_de_disparo, letra, estado)
        # As cores do teclado aparecem letra a letra, sincronizadas com
        # o momento exato em que cada célula vira (metade do flip).
        self._kbd_pending: list = []
        self._tempo: float      = 0.0   # cronômetro global em segundos

        self._nova_partida()

    # ── Background ────────────────────────────────────────────────────
    def _criar_bg(self) -> pygame.Surface:
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            cor = lerp_cor(COR_BG_TOP, COR_BG_BOT, y / SCREEN_H)
            pygame.draw.line(bg, cor, (0, y), (SCREEN_W, y))
        return bg

    # ── JSON ──────────────────────────────────────────────────────────
    def _carregar_json(self) -> list:
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
        self.entrada  = random.choice(self.dados)
        self.p_norm   = self.entrada["_norm"]
        self.p_orig   = self.entrada["palavra"]
        self.contexto = self.entrada["contexto"]
        self.p_len    = len(self.p_norm)

        fs = max(22, min(40, int(CELL_MAX_SIZE * 0.50)))
        self.f_cel = carregar_fonte(fs, negrito=True)
        w, h = self.screen.get_size()

        board_y    = HEADER_H + 8
        board_h    = h - HEADER_H - KEYBOARD_H - 16
        board_area = pygame.Rect(20, board_y, w - 40, board_h)
        kbd_area   = pygame.Rect(10, h - KEYBOARD_H + 5,
                                  w - 20, KEYBOARD_H - 10)

        self.tabuleiro  = Tabuleiro(self.p_len, MAX_TENTATIVAS, board_area)
        self.teclado    = TecladoVirtual(kbd_area)
        self.flashcard  = None
        self.game_over  = False
        self.ganhou     = False
        self.mensagem   = ""
        self.msg_timer  = 0.0
        self.particulas = SistemaParticulas()

        # Limpa fila de atualizações pendentes
        self._kbd_pending.clear()

        pygame.time.set_timer(self.EV_FLASH,   0)
        pygame.time.set_timer(self.EV_CONFETE, 0)

    # ── Validação ─────────────────────────────────────────────────────
    def _validar(self, tentativa: str) -> list:
        """
        Algoritmo Wordle em 2 passos para tratar letras duplicadas corretamente.
        Passo 1: marca posições CORRETAS e consome essas letras da palavra secreta.
        Passo 2: marca PRESENTES (letras que existem mas estão fora de lugar)
                 usando apenas as posições ainda não consumidas.
        """
        n        = self.p_len
        res      = ["ausente"] * n
        restante = list(self.p_norm)

        for i in range(n):
            if tentativa[i] == self.p_norm[i]:
                res[i]      = "correta"
                restante[i] = None

        for i in range(n):
            if res[i] == "correta":
                continue
            if tentativa[i] in restante:
                res[i] = "presente"
                restante[restante.index(tentativa[i])] = None

        return res

    # ── Confirmar tentativa ───────────────────────────────────────────
    def _confirmar(self):
        tent = self.tabuleiro.get_tentativa()
        if len(tent) < self.p_len:
            self._msg("Palavra incompleta!")
            self.tabuleiro.shake()
            return

        res    = self._validar(tent)
        ganhou = (tent == self.p_norm)
        self.tabuleiro.aplicar_resultado(res, ganhou=ganhou)

        # ── Agendar cores do teclado letra a letra ────────────────────
        # Cada tecla acende no EXATO momento em que a célula correspondente
        # chega à metade do flip (scaleY ≈ 0), revelando a cor.
        # Isso cria o efeito visual de "a tecla acende junto com a célula".
        flip_meio = Celula.FLIP_DUR / 2   # metade da duração do flip
        for i, letra in enumerate(tent):
            t_reveal = (self._tempo
                        + i * Tabuleiro.FLIP_COL_DELAY  # delay da coluna
                        + flip_meio)                    # metade do flip
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
        self.mensagem  = texto
        self.msg_timer = dur

    # ── Eventos ───────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                self._tratar_redimensionamento(event.w, event.h)

            if event.type == self.EV_FLASH:
                pygame.time.set_timer(self.EV_FLASH, 0)
                w, h = self.screen.get_size()
                self.flashcard = Flashcard(
                    self.ganhou, self.p_orig, self.p_norm,
                    self.contexto, w, h
                )

            if event.type == self.EV_CONFETE:
                pygame.time.set_timer(self.EV_CONFETE, 0)
                w, h = self.screen.get_size()
                self.particulas.emitir(w // 2, h // 3, n=150)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.flashcard:
                    self._nova_partida()
                    return
                if not self.game_over:
                    k = self.teclado.clique(event.pos)
                    if k == "ENTER":
                        self._confirmar()
                    elif k == "<<":
                        self.tabuleiro.apagar()
                    elif len(k) == 1:
                        self.tabuleiro.digitar(normalizar(k))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.flashcard:
                    self._nova_partida()
                    return
                if self.game_over:
                    continue
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirmar()
                elif event.key == pygame.K_BACKSPACE:
                    self.tabuleiro.apagar()
                elif event.unicode and event.unicode.isalpha():
                    self.tabuleiro.digitar(normalizar(event.unicode[0]))

    # ── Processar fila do teclado ─────────────────────────────────────
    def _processar_kbd_pending(self):
        """
        Dispara as atualizações de cor do teclado quando o tempo chegou.
        Remove os itens já processados da fila.
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
        pygame.draw.rect(self.screen, COR_HEADER_BG, (0, 0, SCREEN_W, HEADER_H))

        for x in range(SCREEN_W):
            t   = x / SCREEN_W
            cor = lerp_cor(COR_CORRETA, COR_PRESENTE, t)
            pygame.draw.line(self.screen, cor, (x, 0), (x, 3))

        pygame.draw.line(self.screen, COR_DIVIDER, (0, HEADER_H), (SCREEN_W, HEADER_H), 1)

        s = self.f_titulo.render("TERMO AMBIENTAL", True, COR_TITULO)
        self.screen.blit(s, s.get_rect(centerx=SCREEN_W // 2, top=14))

        tent_rest = MAX_TENTATIVAS - self.tabuleiro.tentativa_atual
        info = (f"{self.p_len} letras  •  "
                f"{tent_rest} tentativa{'s' if tent_rest != 1 else ''} "
                f"restante{'s' if tent_rest != 1 else ''}")
        s2 = self.f_sub.render(info, True, COR_TEXTO_DIM)
        self.screen.blit(s2, s2.get_rect(centerx=SCREEN_W // 2, top=46))

        pygame.draw.line(self.screen, (50, 100, 90),
                         (SCREEN_W // 2 - 60, HEADER_H - 1),
                         (SCREEN_W // 2 + 60, HEADER_H - 1), 2)

    def _draw_kbd_bg(self):
        r = pygame.Rect(0, SCREEN_H - KEYBOARD_H, SCREEN_W, KEYBOARD_H)
        pygame.draw.rect(self.screen, (16, 16, 28), r)
        pygame.draw.line(self.screen, COR_DIVIDER, (0, r.top), (SCREEN_W, r.top), 1)

    def _draw_msg(self):
        if not self.mensagem or self.msg_timer <= 0:
            return
        s  = self.f_msg.render(self.mensagem, True, COR_TEXTO)
        r  = s.get_rect(centerx=SCREEN_W // 2, top=HEADER_H + 8)
        bg = r.inflate(30, 14)
        pygame.draw.rect(self.screen, (38, 38, 60), bg, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 110), bg, width=1, border_radius=10)
        self.screen.blit(s, r)

    def _draw(self):
        self.screen.blit(self.bg, (0, 0))
        self._draw_header()
        self._draw_kbd_bg()
        self.tabuleiro.draw(self.screen, self.f_cel)
        self.teclado.draw(self.screen)
        self.particulas.draw(self.screen)
        self._draw_msg()
        if self.flashcard:
            self.flashcard.draw(self.screen)
        pygame.display.flip()

    def _tratar_redimensionamento(self, w, h):
        global SCREEN_W, SCREEN_H
        
        # Limita um tamanho mínimo para não quebrar a UI
        SCREEN_W = max(w, 400)
        SCREEN_H = max(h, 600)
        
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        self.bg     = self._criar_bg()  # Recria o gradiente com o novo tamanho

        board_y    = HEADER_H + 8
        board_h    = SCREEN_H - HEADER_H - KEYBOARD_H - 16
        board_area = pygame.Rect(20, board_y, SCREEN_W - 40, board_h)
        kbd_area   = pygame.Rect(10, SCREEN_H - KEYBOARD_H + 5,
                                  SCREEN_W - 20, KEYBOARD_H - 10)

        # Repassa o redimensionamento para os componentes
        if self.tabuleiro:
            self.tabuleiro.atualizar_area(board_area)
            # Ajusta a fonte caso as células tenham ficado menores
            fs = max(22, min(40, int(self.tabuleiro.cell_size * 0.50)))
            self.f_cel = carregar_fonte(fs, negrito=True)
            
        if self.teclado:
            self.teclado.atualizar_area(kbd_area)
            
        if self.flashcard:
            self.flashcard.atualizar_area(SCREEN_W, SCREEN_H)
        
    # ── Loop principal ────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self._tempo += dt                   # cronômetro global

            self._handle_events()
            self._processar_kbd_pending()        # ← cores do teclado letra a letra

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
