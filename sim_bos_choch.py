# Simulación en Python del motor de líneas L1-L4 con detección de
# CHoCH *y* BOS — base de la ESTRATEGIA 1 v8.56 (ver `trabajador multichart.mq5`).
#
# Qué modela (idéntico al MQL5):
#   · SE_OnClose / SE_OnTick  → estructura L1-L4 (rango + reacción L3/L4).
#   · CHoCH  = el rompimiento CAMBIA el bias (SE_CommitStructureMove).
#   · BOS    = continuación: con la reacción activa el precio CIERRA más allá
#              del nivel de referencia de la reacción (RefLevel):
#                 bias alcista  → cierre > RefLevel (techo L1 que se rompió)
#                 bias bajista  → cierre < RefLevel (suelo L2 que se rompió)
#              Un solo BOS por reacción (BosDone), sin tocar la detección
#              del CHoCH (S2 sigue viendo exactamente lo mismo que antes).
#   · 50% del tramo = punto medio del rango de la reacción/impulso que rompió
#              (L3/L4 en el momento del rompimiento) → nivel de la LIMIT.
#
# Series MQL5: índice 0 = vela en formación, 1 = última vela cerrada.

BIAS_UNDEF, BIAS_BULL, BIAS_BEAR = 0, 1, -1
PHASE_CONT, PHASE_REACTION = 0, 1


class SE:
    def __init__(self):
        self.L1 = self.L2 = self.L3 = self.L4 = self.EQ = 0.0
        self.L3L4 = False
        self.Bias = BIAS_UNDEF
        self.RefLevel = 0.0          # nivel de referencia para el BOS
        self.BosDone = False         # BOS del tramo actual ya emitido
        self.BosLegHigh = self.BosLegLow = 0.0   # tramo del BOS (retroceso → extremo)
        self.LastHigh = self.LastLow = 0.0   # tramo del último rompimiento
        self.Valid = False

    # --- SE_Init -----------------------------------------------------------
    def init(self, bars):
        self.L1 = max(b[1] for b in bars)
        self.L2 = min(b[2] for b in bars)
        c = bars[-1]
        self.Bias = BIAS_BULL if c[3] > c[0] else (BIAS_BEAR if c[3] < c[0] else BIAS_UNDEF)
        self.eq()
        self.Valid = True

    def eq(self):
        self.EQ = self.L2 + (self.L1 - self.L2) * 0.5

    # --- SE_ClearReaction --------------------------------------------------
    def clear_reaction(self):
        self.L3 = self.L4 = 0.0
        self.L3L4 = False
        self.RefLevel = 0.0
        self.BosDone = False
        self.BosLegHigh = self.BosLegLow = 0.0

    # --- SE_CommitStructureMove (CHoCH) -----------------------------------
    def commit(self, dirn):
        if dirn == 0 or not self.L3L4:
            return 0
        old = self.Bias
        new = BIAS_BULL if dirn > 0 else BIAS_BEAR
        self.LastHigh = max(self.L3, self.L4)     # tramo del rompimiento
        self.LastLow = min(self.L3, self.L4)
        self.L1, self.L2 = self.L3, self.L4
        if self.L1 < self.L2:
            self.L1, self.L2 = self.L2, self.L1
        self.Bias = new
        self.eq()
        self.clear_reaction()
        return dirn if (old != BIAS_UNDEF and old != new) else 0

    def break_dir(self, O, C):
        if not self.L3L4:
            return 0
        up = self.L3 > self.L1
        dn = self.L4 < self.L2
        if not up and not dn:
            return 0
        if up and dn:
            return 1 if C > O else -1
        return 1 if up else -1

    def check_break_and_commit(self, O, C):
        d = self.break_dir(O, C)
        return self.commit(d) if d else 0

    # --- SE_CheckContinuationBreak (BOS) ----------------------------------
    def continuation(self, C):
        if not self.L3L4 or self.RefLevel <= 0.0 or self.BosDone:
            return 0
        dirn = 0
        if self.Bias == BIAS_BULL and C > self.RefLevel:
            dirn = +1
        if self.Bias == BIAS_BEAR and C < self.RefLevel:
            dirn = -1
        if dirn == 0:
            return 0
        # tramo del BOS = retroceso (origen) → extremo del impulso
        self.LastHigh, self.LastLow = self.BosLegHigh, self.BosLegLow
        if self.LastHigh <= self.LastLow:
            self.LastHigh = max(self.L3, self.L4)
            self.LastLow = min(self.L3, self.L4)
        if self.LastHigh <= self.LastLow:
            return 0
        if dirn > 0 and self.LastHigh > self.L1:
            self.L1 = self.LastHigh; self.eq()
        if dirn < 0 and self.LastLow < self.L2:
            self.L2 = self.LastLow; self.eq()
        self.BosDone = True
        return dirn

    # --- SE_OnTick (solo L3/L4 y L1/L2 del lado del bias) -----------------
    def on_tick(self, price):
        if not self.L3L4:
            return
        if price > self.L3:
            self.L3 = price
        if price < self.L4:
            self.L4 = price
        if price > self.BosLegHigh:
            self.BosLegHigh = price
        if price < self.BosLegLow:
            self.BosLegLow = price
        if self.Bias == BIAS_BULL and price > self.L1:
            self.L1 = price
            self.eq()
        elif self.Bias == BIAS_BEAR and price < self.L2:
            self.L2 = price
            self.eq()

    # --- SE_OnClose --------------------------------------------------------
    def on_close(self, bar):
        """Devuelve (choch, bos)."""
        O, H, L, C = bar
        choch = bos = 0
        if not self.Valid:
            return 0, 0
        green, red = C > O, C < O
        if self.Bias == BIAS_UNDEF:
            if green:
                self.Bias = BIAS_BULL
            if red:
                self.Bias = BIAS_BEAR
            return 0, 0

        if self.L3L4:
            if H > self.L3:
                self.L3 = H
            if L < self.L4:
                self.L4 = L
            if H > self.BosLegHigh:
                self.BosLegHigh = H
            if L < self.BosLegLow:
                self.BosLegLow = L
            # vela contraria → re-arma el BOS (y abre tramo nuevo si ya hubo BOS)
            contrary = (self.Bias == BIAS_BULL and red) or \
                       (self.Bias == BIAS_BEAR and green)
            if contrary:
                if self.BosDone:
                    self.BosLegHigh, self.BosLegLow = H, L
                self.RefLevel = self.L1 if self.Bias == BIAS_BULL else self.L2
                self.BosDone = False
            blh, bll = self.BosLegHigh, self.BosLegLow
            trig = self.break_dir(O, C)
            choch = self.commit(trig) if trig else 0
            if trig != 0:
                if choch == 0:                    # misma dirección → BOS
                    if blh > bll:
                        self.LastHigh, self.LastLow = blh, bll
                    bos = trig
            else:
                bos = self.continuation(C)        # BOS por RefLevel (con ticks)
            return choch, bos

        if self.Bias == BIAS_BULL and H > self.L1:
            self.L1 = H
            self.eq()
        elif self.Bias == BIAS_BEAR and L < self.L2:
            self.L2 = L
            self.eq()

        if self.Bias == BIAS_BULL and red:
            self.L3L4 = True
            self.L3 = self.L1          # techo
            self.L4 = L                 # mínimo de la vela contraria
            self.RefLevel = self.L1     # nivel de referencia del BOS
            self.BosDone = False
            self.BosLegHigh, self.BosLegLow = H, L
            choch = self.check_break_and_commit(O, C)
        elif self.Bias == BIAS_BEAR and green:
            self.L3L4 = True
            self.L3 = H
            self.L4 = self.L2           # suelo
            self.RefLevel = self.L2
            self.BosDone = False
            self.BosLegHigh, self.BosLegLow = H, L
            choch = self.check_break_and_commit(O, C)
        return choch, bos


# ---------------------------------------------------------------------------
# Máquina de estados de la Estrategia 1 (CONFL) con BOS + CHoCH
# ---------------------------------------------------------------------------
class E1:
    def __init__(self, h1, m3, log=print, accept_bos=True, accept_choch=True):
        self.h1, self.m3, self.log = h1, m3, log
        self.accept_bos, self.accept_choch = accept_bos, accept_choch
        self.armedBuy = self.armedSell = False
        self.armBuyT = self.armSellT = -1
        self.waitBuy = self.waitSell = False
        self.entryBuy = self.entrySell = 0.0
        self.legBuy = self.legSell = (0.0, 0.0)      # (low, high) del tramo
        self.vpendBuy = self.vpendSell = False
        self.vpendBuyP = self.vpendSellP = 0.0
        self.pending = None                          # (dir, price)
        self.position = None
        self.results = []
        self.breakDir = 0
        self.breakIsChoch = True
        self.break50 = 0.0
        self.breakLeg = (0.0, 0.0)

    # --- zona H1 ----------------------------------------------------------
    def arming(self, bid, t):
        eq = self.h1.EQ
        if bid <= eq and not self.armedBuy:
            self.armedBuy = True
            self.armBuyT = t
            self.log(f"   t{t}: toca ZONA COMPRA H1 (50%={eq:.3f}) → busca BOS/CHoCH M3 alcista")
        if bid >= eq and not self.armedSell:
            self.armedSell = True
            self.armSellT = t
            self.log(f"   t{t}: toca ZONA VENTA H1 (50%={eq:.3f}) → busca BOS/CHoCH M3 bajista")

    # --- evento del motor M3 ---------------------------------------------
    def on_m3_event(self, dirn, is_choch, level50, leg, t):
        self.breakDir, self.breakIsChoch = dirn, is_choch
        self.break50, self.breakLeg = level50, leg

    def process(self, t):
        d = self.breakDir
        if d == 0:
            return
        self.breakDir = 0
        if self.position is not None or self.pending is not None:
            return
        if self.waitBuy or self.waitSell:
            return
        if self.breakIsChoch and not self.accept_choch:
            self.log(f"   t{t}: CHoCH dir={d:+d} ignorado (CHoCH desactivado)")
            return
        if (not self.breakIsChoch) and not self.accept_bos:
            self.log(f"   t{t}: BOS dir={d:+d} ignorado (BOS desactivado)")
            return
        name = "CHoCH" if self.breakIsChoch else "BOS"
        if d > 0 and self.h1.Bias == BIAS_BULL and self.armedBuy and t >= self.armBuyT:
            self.entryBuy = self.break50
            self.legBuy = self.breakLeg
            self.waitBuy = True
            self.log(f"   t{t}: {name} alcista M3 · tramo [{self.breakLeg[0]:.3f}.."
                     f"{self.breakLeg[1]:.3f}] → 50% CONGELADO @{self.break50:.3f} (compra)")
        elif d < 0 and self.h1.Bias == BIAS_BEAR and self.armedSell and t >= self.armSellT:
            self.entrySell = self.break50
            self.legSell = self.breakLeg
            self.waitSell = True
            self.log(f"   t{t}: {name} bajista M3 · tramo [{self.breakLeg[0]:.3f}.."
                     f"{self.breakLeg[1]:.3f}] → 50% CONGELADO @{self.break50:.3f} (venta)")

    # --- colocación de la LIMIT del lado correcto del 50% ----------------
    def try_place(self, bid, t):
        if self.pending is not None:
            return
        if self.waitBuy and bid > self.entryBuy:
            self.pending = (+1, self.entryBuy)
            self.waitBuy = False
            self.log(f"   t{t}: precio encima del 50% → BUY LIMIT @{self.entryBuy:.3f}")
        elif self.waitSell and bid < self.entrySell:
            self.pending = (-1, self.entrySell)
            self.waitSell = False
            self.log(f"   t{t}: precio debajo del 50% → SELL LIMIT @{self.entrySell:.3f}")

    # --- fill virtual -----------------------------------------------------
    def check_fill(self, bid, ask, t):
        if self.pending is None or self.position is not None:
            return
        d, p = self.pending
        if d > 0 and ask <= p:
            self.position = (d, p)
            self.pending = None
            self.log(f"   t{t}: vOPEN BUY @{p:.3f} (fill del 50% del tramo)")
        elif d < 0 and bid >= p:
            self.position = (d, p)
            self.pending = None
            self.log(f"   t{t}: vOPEN SELL @{p:.3f} (fill del 50% del tramo)")

    # --- invalidación del tramo (ruptura del origen) ----------------------
    def check_leg_break(self, py, t):
        if self.position is not None:
            return
        if (self.waitBuy or (self.pending and self.pending[0] > 0)) and self.legBuy[0] > 0:
            if py < self.legBuy[0]:
                self.waitBuy = False
                self.pending = None
                self.entryBuy = 0.0
                self.log(f"   t{t}: precio rompe el ORIGEN del tramo ({self.legBuy[0]:.3f}) → entrada cancelada")
        if (self.waitSell or (self.pending and self.pending[0] < 0)) and self.legSell[1] > 0:
            if py > self.legSell[1]:
                self.waitSell = False
                self.pending = None
                self.entrySell = 0.0
                self.log(f"   t{t}: precio rompe el ORIGEN del tramo ({self.legSell[1]:.3f}) → entrada cancelada")


def mk(rows):
    """rows de la MÁS ANTIGUA a la MÁS NUEVA → tuplas (O,H,L,C) invertidas."""
    return list(rows)[::-1]


def run(title, h1_rows, m3_rows, ticks, accept_bos=True, accept_choch=True, log=print):
    """h1_rows/m3_rows = [(O,H,L,C)] de la más antigua a la más nueva.
    ticks = [(bid, m3_bar_o_None)]"""
    print(f"\n===== {title} =====")
    h1 = SE(); h1.init(mk(h1_rows))
    m3 = SE(); m3.init(m3_rows[:1])   # arranca con la 1ª vela; el resto se procesa como cierres
    e1 = E1(h1, m3, log, accept_bos=accept_bos, accept_choch=accept_choch)
    print(f"  H1: L1={h1.L1:.2f} L2={h1.L2:.2f} EQ={h1.EQ:.2f} bias={h1.Bias:+d}")
    m3_close = m3_rows[0][3]
    for t, (bid, bar) in enumerate(ticks):
        m3.on_tick(bid)
        h1.on_tick(bid)
        e1.arming(bid, t)
        if bar is not None:
            m3_close = bar[3]           # cierre de la última vela M3 cerrada
            ch, bos = m3.on_close(bar)
            if ch != 0 or bos != 0:
                d = ch if ch != 0 else bos
                level = (m3.LastHigh + m3.LastLow) / 2.0
                print(f"   t{t}: motor M3 → {'CHoCH' if ch else 'BOS'} "
                      f"{'ALCISTA' if d > 0 else 'BAJISTA'} · tramo "
                      f"[{m3.LastLow:.3f}..{m3.LastHigh:.3f}] · 50%={level:.3f}")
                e1.on_m3_event(d, ch != 0, level, (m3.LastLow, m3.LastHigh), t)
        e1.process(t)
        e1.check_leg_break(m3_close, t)
        e1.try_place(bid, t)
        e1.check_fill(bid, bid + 0.00002, t)
    print(f"  RESULTADO: pendiente={e1.pending} posición={e1.position} "
          f"esperaB={e1.waitBuy}@{e1.entryBuy:.3f} esperaS={e1.waitSell}@{e1.entrySell:.3f}")
    return e1


# H1 alcista: rango amplio, la zona de compra es la parte baja (≤50%)
H1_BULL = [(1.0900 + i * 0.0002, 1.0910 + i * 0.0002, 1.0890 + i * 0.0002, 1.0905 + i * 0.0002)
           for i in range(10)]
#   L1≈1.0911, L2≈1.0890, EQ≈1.09005, bias ALCISTA → compras permitidas en ≤1.09005

# --- M3: tendencia alcista con retroceso y continuación (BOS) ------------
M3_BOS = [
    (1.08940, 1.08960, 1.08920, 1.08950),
    (1.08950, 1.08990, 1.08945, 1.08985),   # techo 1.08990
    (1.08985, 1.08995, 1.08960, 1.08965),   # vela bajista → reacción (RefLevel 1.08990)
    (1.08965, 1.08975, 1.08935, 1.08940),   # mínimo de la reacción 1.08935
    (1.08940, 1.08965, 1.08930, 1.08960),
    (1.08960, 1.09005, 1.08955, 1.09000),   # cierre 1.09000 > RefLevel → BOS alcista
]
# tramo del BOS = [1.08930 .. 1.09005] → 50% = 1.089675

run("1. BOS alcista en zona de compra H1 → LIMIT en el 50% del tramo",
    H1_BULL, M3_BOS,
    ticks=[(1.08950, None),
           (1.08950, M3_BOS[1]),
           (1.08960, M3_BOS[2]),
           (1.08940, M3_BOS[3]),
           (1.08935, M3_BOS[4]),
           (1.09000, M3_BOS[5]),      # ← BOS
           (1.09000, None),           # LIMIT colocada (precio > 50%)
           (1.08966, None),           # retroceso → fill
           ])

# --- CHoCH alcista: H1 alcista, M3 hace un giro --------------------------
M3_CHOCH = [
    (1.08980, 1.08985, 1.08955, 1.08960),
    (1.08960, 1.08965, 1.08930, 1.08935),
    (1.08935, 1.08940, 1.08910, 1.08915),   # rompe el suelo → bias BAJISTA
    (1.08915, 1.08920, 1.08880, 1.08885),   # mínimo del giro
    (1.08885, 1.08910, 1.08880, 1.08905),
    (1.08905, 1.08945, 1.08900, 1.08940),
    (1.08940, 1.08995, 1.08935, 1.08990),   # rompe el techo → CHoCH ALCISTA
]
run("2. CHoCH alcista en zona de compra H1 → LIMIT en el 50% del tramo",
    H1_BULL, M3_CHOCH,
    ticks=[(1.08950, None),
           (1.08950, M3_CHOCH[1]),
           (1.08940, M3_CHOCH[2]),
           (1.08920, M3_CHOCH[3]),
           (1.08890, M3_CHOCH[4]),
           (1.08900, M3_CHOCH[5]),
           (1.08990, M3_CHOCH[6]),    # ← CHoCH
           (1.08990, None),
           (1.08940, None),           # fill
           ])

# --- Rompimiento en dirección CONTRARIA a la zona H1 → se ignora -------
M3_CHOCH_BEAR = [
    (1.08940, 1.08960, 1.08920, 1.08950),   # bias ALCISTA, L1=1.08960 L2=1.08920
    (1.08950, 1.08970, 1.08945, 1.08965),   # L1=1.08970
    (1.08965, 1.08968, 1.08940, 1.08945),   # vela bajista → reacción (RefLevel 1.08970)
    (1.08945, 1.08950, 1.08910, 1.08915),   # cierra bajo L2 → CHoCH BAJISTA
]
run("3. CHoCH bajista con H1 alcista → IGNORADO (zona de compra = solo compras)",
    H1_BULL, M3_CHOCH_BEAR,
    ticks=[(1.08950, None),
           (1.08960, M3_CHOCH_BEAR[1]),
           (1.08950, M3_CHOCH_BEAR[2]),
           (1.08920, M3_CHOCH_BEAR[3])])

# --- El precio rompe el ORIGEN del tramo → entrada cancelada -----------
run("5. El precio rompe el origen del tramo → LIMIT cancelada",
    H1_BULL, M3_BOS,
    ticks=[(1.08950, None),
           (1.08950, M3_BOS[1]),
           (1.08960, M3_BOS[2]),
           (1.08940, M3_BOS[3]),
           (1.08935, M3_BOS[4]),
           (1.09000, M3_BOS[5]),      # BOS → LIMIT @50%
           (1.09000, None),
           (1.08920, (1.08960, 1.08965, 1.08915, 1.08920))])  # cierra bajo el origen

# --- BOS desactivado → solo se acepta CHoCH -----------------------------
run("4. BOS alcista con InpConfAcceptBOS=false → IGNORADO",
    H1_BULL, M3_BOS,
    ticks=[(1.08950, None),
           (1.08950, M3_BOS[1]),
           (1.08960, M3_BOS[2]),
           (1.08940, M3_BOS[3]),
           (1.08935, M3_BOS[4]),
           (1.09000, M3_BOS[5]),
           (1.09000, None)],
    accept_bos=False)


# ---------------------------------------------------------------------------
# ESCENARIO 6: re-armado del BOS (un rompimiento por retroceso)
# ---------------------------------------------------------------------------
def trace_engine(title, rows):
    print(f"\n===== {title} =====")
    se = SE(); se.init(rows[:1])
    for i, bar in enumerate(rows[1:], 1):
        se.on_tick(bar[3])
        ch, bos = se.on_close(bar)
        if ch or bos:
            mid = (se.LastHigh + se.LastLow) / 2.0
            print(f"  vela {i}: {'CHoCH' if ch else 'BOS'} {'ALCISTA' if (ch or bos) > 0 else 'BAJISTA'}"
                  f" · tramo [{se.LastLow:.4f}..{se.LastHigh:.4f}] · 50%={mid:.5f}"
                  f" · L1={se.L1:.4f} L2={se.L2:.4f}")
    print(f"  fin: L1={se.L1:.4f} L2={se.L2:.4f} bias={se.Bias:+d}")


M3_REARM = [
    (1.08940, 1.08960, 1.08920, 1.08950),
    (1.08950, 1.08990, 1.08945, 1.08985),   # techo 1.08990
    (1.08985, 1.08995, 1.08960, 1.08965),   # retroceso (reacción)  RefLevel 1.08990
    (1.08965, 1.08975, 1.08935, 1.08940),
    (1.08940, 1.08965, 1.08930, 1.08960),
    (1.08960, 1.09005, 1.08955, 1.09000),   # BOS 1: cierra > 1.08990
    (1.09000, 1.09005, 1.08975, 1.08980),   # nuevo retroceso → re-arma y ABRE TRAMO
    (1.08980, 1.09030, 1.08978, 1.09025),   # BOS 2: cierra > 1.09005 (techo del tramo nuevo)
]
trace_engine("6. Re-armado del BOS: dos rompimientos de continuación", M3_REARM)
