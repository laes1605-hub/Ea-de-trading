#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sim_grid.py — modelo en Python de la REJILLA (GRID) del EA v8.60
================================================================
Replica la lógica de la rejilla que se aplica a las ENTRADAS de la
Estrategia 1 y de la Estrategia 3 (nunca a la S2):

  · la apertura sigue siendo la de E1/E3 (aquí se simula con open_base)
  · el nivel n se abre cuando el precio recorre, EN CONTRA, desde el
    PEOR precio de la cesta:
        dist(n) = InpGridStepPts · InpGridDistMult^(n-1)
        (InpGridStepPts = 0 → mitad del SL del par)
  · LOTaje PROPIO de la rejilla (nunca el de la tabla de riesgo):
        lot(n) = InpGridLotInit · InpGridLotMult^(n-1)
    con tope InpGridLotCap y normalizado al paso de volumen
  · la CESTA va SIN STOP LOSS (InpGridStripSL)
  · TP de la CESTA EN USD (InpGridTPUsd): cuando el beneficio flotante
    (profit + swap) llega al objetivo se cierran TODAS las posiciones y
    el cierre cuenta como TP (NIVEL→1, CV→1)
  · HORARIO: el PRIMER nivel de la rejilla solo en horario permitido;
    los niveles 2..20 se abren a CUALQUIER hora
  · máximo GRID_MAX_LEVELS = 20 operaciones de rejilla por par

Ejecutar:  python3 sim_grid.py
"""

GRID_MAX_LEVELS = 20


class Grid:
    def __init__(self,
                 enable=True, on_e1=True, on_e3=True, strategy="E1",
                 step_pts=0.0, dist_mult=1.0, lot_init=0.01, lot_mult=1.0,
                 max_levels=20, lot_cap=5.0, tp_usd=5.0, strip_sl=True,
                 avg_tp=False, free_hours=True, keep_trail=False,
                 point=0.00001, digits=5, sl_pts=95.0, tp_pts=305.0,
                 vol_min=0.01, vol_max=50.0, vol_step=0.01,
                 table_lot=0.37, usd_per_point_lot=1.0):
        self.enable      = enable
        self.on_e1       = on_e1
        self.on_e3       = on_e3
        self.strategy    = strategy
        self.step_pts    = step_pts
        self.dist_mult   = dist_mult
        self.lot_init    = lot_init
        self.lot_mult    = lot_mult
        self.max_levels  = max_levels
        self.lot_cap     = lot_cap
        self.tp_usd      = tp_usd
        self.strip_sl    = strip_sl
        self.avg_tp      = avg_tp
        self.free_hours  = free_hours
        self.keep_trail  = keep_trail
        self.point       = point
        self.digits      = digits
        self.sl_pts      = sl_pts
        self.tp_pts      = tp_pts
        self.vol_min     = vol_min
        self.vol_max     = vol_max
        self.vol_step    = vol_step
        self.table_lot   = table_lot        # lote que daría la TABLA (no se usa)
        self.usd_pt_lot  = usd_per_point_lot
        # estado
        self.dir         = 0
        self.legs        = 0
        self.pos         = []      # [(precio, lotes, sl, tp)]
        self.log         = []
        self.level_events = 0      # veces que se actualizó nivel/CV
        self.last_event  = None    # "TP" / "SL" / "PARCIAL"

    # -- utilidades ---------------------------------------------------------
    def uses_strategy(self):
        if not self.enable:
            return False
        if self.strategy == "E1":
            return self.on_e1
        if self.strategy == "E3":
            return self.on_e3
        return False        # S2 nunca usa rejilla

    def max_levels_cap(self):
        m = int(self.max_levels)
        if m < 0:
            m = 0
        return min(m, GRID_MAX_LEVELS)

    def norm_lot(self, lots):
        cap = self.lot_cap if self.lot_cap > 0 else self.vol_max
        mx = min(self.vol_max, cap)
        lots = int(lots / self.vol_step + 1e-9) * self.vol_step
        lots = max(self.vol_min, min(mx, lots))
        return round(lots, 2)

    def step_points(self):
        base = self.step_pts if self.step_pts > 0 else self.sl_pts * 0.5
        m = max(0.1, self.dist_mult)
        return base * (m ** max(0, self.legs))

    def next_lot(self):
        # LOTaje PROPIO de la rejilla (independiente de la tabla de riesgo)
        base = self.lot_init if self.lot_init > 0 else self.vol_min
        m = max(0.1, self.lot_mult)
        lots = base * (m ** max(0, self.legs))
        if self.lot_cap > 0:
            lots = min(lots, self.lot_cap)
        return self.norm_lot(lots)

    def stats(self):
        if not self.pos:
            return 0.0, 0.0, 0.0
        sv = sum(l for _, l, _, _ in self.pos)
        spv = sum(p * l for p, l, _, _ in self.pos)
        avg = spv / sv
        if self.dir > 0:
            worst = min(p for p, _, _, _ in self.pos)
        else:
            worst = max(p for p, _, _, _ in self.pos)
        return avg, worst, sv

    def basket_profit(self, price):
        """Beneficio flotante de la cesta en USD (profit + swap ≈ profit)."""
        pl = 0.0
        for p, l, _, _ in self.pos:
            d = (price - p) if self.dir > 0 else (p - price)
            pl += (d / self.point) * l * self.usd_pt_lot
        return pl

    def basket_sl_price(self, avg):
        return avg - self.sl_pts * self.point if self.dir > 0 \
            else avg + self.sl_pts * self.point

    def basket_tp_price(self, avg):
        return avg + self.tp_pts * self.point if self.dir > 0 \
            else avg - self.tp_pts * self.point

    # -- apertura de la estrategia (E1/E3) ----------------------------------
    def open_base(self, direction, price, lots=None):
        """La ENTRADA es la de E1/E3: usa el lote de la TABLA de riesgo."""
        lots = self.table_lot if lots is None else lots
        self.dir = 1 if direction > 0 else -1
        sl = 0.0 if self.strip_sl else \
            (price - self.dir * self.sl_pts * self.point)
        tp = 0.0 if (self.tp_usd > 0 or not self.avg_tp) else \
            (price + self.dir * self.tp_pts * self.point)
        self.pos.append((price, lots, sl, tp))
        self.legs = 0
        self.log.append("BASE (tabla) %s %.2f lotes @%.5f SL=%.5f TP=%.5f" %
                        ("COMPRA" if self.dir > 0 else "VENTA", lots, price, sl, tp))

    # -- motor --------------------------------------------------------------
    def can_open(self, cb=False, weekly=False, allowed=True):
        if not self.uses_strategy() or not self.pos:
            return False
        if cb or weekly:
            return False
        if self.max_levels_cap() <= 0:
            return False
        if self.legs >= self.max_levels_cap():
            return False
        # el PRIMER nivel exige horario; los siguientes, no
        if (self.legs == 0 or not self.free_hours) and not allowed:
            return False
        return True

    def on_tick(self, price, cb=False, weekly=False, allowed=True):
        """Devuelve los lotes del nivel abierto (o None si no toca)."""
        if not self.can_open(cb, weekly, allowed):
            return None
        avg, worst, lots = self.stats()
        need = self.step_points()
        adv = (worst - price) / self.point if self.dir > 0 \
            else (price - worst) / self.point
        if adv + 1e-4 < need:
            return None
        lots = self.next_lot()
        if lots <= 0:
            return None
        self.pos.append((price, lots, 0.0, 0.0))
        self.legs += 1
        # respaldo por PRECIO MEDIO: todas las posiciones comparten el TP
        if self.tp_usd <= 0 and self.avg_tp:
            avg2, _, _ = self.stats()
            tp2 = self.basket_tp_price(avg2)
            self.pos = [(p, l, sl, tp2) for (p, l, sl, _) in self.pos]
        self.log.append("REJILLA L%d %s %.2f lotes @%.5f (dist %.0f pts, media %.5f)" %
                        (self.legs, "COMPRA" if self.dir > 0 else "VENTA",
                         lots, price, need, self.stats()[0]))
        return lots

    # -- TP en USD ----------------------------------------------------------
    def check_tp_usd(self, price):
        """Cierra TODA la cesta si el flotante llega al objetivo (cuenta como TP)."""
        if self.tp_usd <= 0 or not self.pos:
            return None
        pl = self.basket_profit(price)
        if pl + 1e-9 < self.tp_usd:
            return None
        n = len(self.pos)
        self.pos = []
        self.level_events += 1
        self.last_event = "TP"
        self.log.append("★ TP en USD alcanzado: %.2f ≥ %.2f → cierra la CESTA "
                        "(%d posiciones) · NIVEL→1 CV→1" % (pl, self.tp_usd, n))
        return pl

    # -- cierres ------------------------------------------------------------
    def close_all(self, at_price=None):
        if not self.pos:
            return None
        avg, _, _ = self.stats()
        px = avg if at_price is None else at_price
        pl = self.basket_profit(px)
        self.pos = []
        self.level_events += 1
        self.last_event = "TP" if pl > 0 else "SL"
        self.log.append("CIERRE CESTA @%.5f P/L=%.2f USD (evento #%d)" %
                        (px, pl, self.level_events))
        return pl

    def partial_close_events(self, price):
        if not self.pos:
            return None
        p, l, _, _ = self.pos.pop(0)
        pl = (price - p) * self.dir / self.point * l * self.usd_pt_lot
        deferred = len(self.pos) > 0
        if not deferred:
            self.level_events += 1
        return pl, deferred, len(self.pos)


# ---------------------------------------------------------------------------
#  Escenarios
# ---------------------------------------------------------------------------
OK = []


def check(name, cond, info=""):
    OK.append((name, bool(cond), info))


def esc1_progresion():
    """1) Progresión de distancia y de lotaje (2× lote, 1.5× distancia)."""
    g = Grid(strategy="E1", step_pts=150, dist_mult=1.5, lot_init=0.10,
             lot_mult=2.0, max_levels=3)
    g.open_base(+1, 1.10000)
    check("1.1 no abre antes de la distancia",
          g.on_tick(1.10000 - 149 * g.point) is None)
    l1 = g.on_tick(1.10000 - 150 * g.point)
    check("1.2 nivel 1 = 0.10 lotes a 150 pts", l1 == 0.10, "lot=%s" % l1)
    check("1.3 nivel 2 no abre a 224 pts",
          g.on_tick(1.09850 - 224 * g.point) is None)
    l2 = g.on_tick(1.09850 - 225 * g.point)
    check("1.4 nivel 2 = 0.20 lotes a 225 pts (1.5×)", l2 == 0.20, "lot=%s" % l2)
    l3 = g.on_tick(1.09625 - 338 * g.point)
    check("1.5 nivel 3 = 0.40 lotes a 337.5 pts (1.5²)", l3 == 0.40, "lot=%s" % l3)
    check("1.6 no pasa del máximo de niveles",
          g.on_tick(1.09625 - 2000 * g.point) is None, "legs=%d" % g.legs)
    for ln in g.log:
        print("   ", ln)
    return g


def esc2_lote_propio():
    """2) LOTaje propio: la rejilla ignora el lote de la tabla de riesgo."""
    g = Grid(strategy="E1", step_pts=100, lot_init=0.02, lot_mult=1.0,
             table_lot=0.37, max_levels=2)
    g.open_base(+1, 1.10000)
    check("2.1 la entrada base sí usa el lote de la tabla (0.37)",
          g.pos[0][1] == 0.37, "lot=%s" % g.pos[0][1])
    l1 = g.on_tick(1.09900)
    check("2.2 el nivel de rejilla usa SU lote (0.02), no el de la tabla",
          l1 == 0.02, "lot=%s" % l1)
    g2 = Grid(strategy="E1", step_pts=100, lot_init=0.0, vol_min=0.01,
              table_lot=0.37, max_levels=1)
    g2.open_base(+1, 1.10000)
    check("2.3 lot_init=0 → lote mínimo del símbolo (0.01), no la tabla",
          g2.on_tick(1.09900) == 0.01)
    return g


def esc3_sin_sl():
    """3) La CESTA no lleva STOP LOSS."""
    g = Grid(strategy="E3", step_pts=100, lot_init=0.01, max_levels=3,
             strip_sl=True, tp_usd=5.0)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09900)
    g.on_tick(1.09800)
    check("3.1 ninguna posición de la cesta tiene SL",
          all(p[2] == 0.0 for p in g.pos))
    check("3.2 ninguna tiene TP por precio con InpGridTPUsd>0",
          all(p[3] == 0.0 for p in g.pos))
    print("    posiciones:", [(round(p[0], 5), p[1]) for p in g.pos])
    return g


def esc4_tp_usd():
    """4) TP en USD: cierra toda la cesta y cuenta como TP (nivel→1, CV→1)."""
    g = Grid(strategy="E1", step_pts=150, dist_mult=1.0, lot_init=0.01,
             lot_mult=1.0, max_levels=5, tp_usd=5.0, strip_sl=True,
             usd_per_point_lot=1.0)
    g.open_base(+1, 1.10000, lots=0.01)      # 0.01 de tabla
    for k in (1, 2, 3, 4):                   # 4 niveles de 0.01 → 5 posiciones
        g.on_tick(1.10000 - k * 150 * g.point)
    total_lots = sum(p[1] for p in g.pos)
    avg, worst, _ = g.stats()
    check("4.1 la cesta tiene 5 posiciones de 0.01", len(g.pos) == 5,
          "n=%d" % len(g.pos))
    # el objetivo de 5 USD con 0.05 lotes exige 100 puntos desde la media
    need_pts = 5.0 / (total_lots * g.usd_pt_lot)
    px_tp = avg + need_pts * g.point
    check("4.2 antes del objetivo (99 pts) NO cierra",
          g.check_tp_usd(avg + 99 * g.point) is None)
    pl = g.check_tp_usd(px_tp + g.point)
    check("4.3 al llegar al objetivo cierra TODA la cesta", pl is not None and len(g.pos) == 0,
          "pl=%s" % pl)
    check("4.4 el cierre se contabiliza UNA vez y como TP",
          g.level_events == 1 and g.last_event == "TP")
    print("    media=%.5f lotes=%.2f → objetivo +%.1f pts (%.5f) · P/L=%.2f USD" %
          (avg, total_lots, need_pts, px_tp, pl if pl else 0))
    for ln in g.log[-2:]:
        print("   ", ln)
    return g


def esc5_maximo_20():
    """5) Hasta 20 operaciones de rejilla (tope duro)."""
    g = Grid(strategy="E3", step_pts=100, dist_mult=1.0, lot_init=0.01,
             lot_mult=1.0, max_levels=20, strip_sl=True, tp_usd=0)
    g.open_base(+1, 1.10000)
    for k in range(1, 30):
        g.on_tick(1.10000 - k * 100 * g.point)
    check("5.1 se detiene en 20 niveles extra", g.legs == 20, "legs=%d" % g.legs)
    check("5.2 la cesta tiene 21 posiciones (entrada + 20)",
          len(g.pos) == 21, "n=%d" % len(g.pos))

    g2 = Grid(strategy="E3", step_pts=100, max_levels=50, tp_usd=0)
    check("5.3 un valor >20 se recorta a 20", g2.max_levels_cap() == 20,
          "cap=%d" % g2.max_levels_cap())

    g3 = Grid(strategy="E3", step_pts=100, max_levels=0, tp_usd=0)
    g3.open_base(+1, 1.10000)
    check("5.4 max_levels=0 → sin rejilla", g3.on_tick(1.09000) is None)
    return g


def esc6_horario():
    """6) Horario: el 1er nivel solo en horario; los siguientes a cualquier hora."""
    g = Grid(strategy="E1", step_pts=100, lot_init=0.01, max_levels=5,
             free_hours=True, tp_usd=0)
    g.open_base(+1, 1.10000)
    check("6.1 fuera de horario NO abre el primer nivel",
          g.on_tick(1.09900, allowed=False) is None)
    check("6.2 en horario sí abre el primer nivel",
          g.on_tick(1.09900, allowed=True) == 0.01)
    check("6.3 fuera de horario SÍ abre el segundo nivel",
          g.on_tick(1.09800, allowed=False) == 0.01, "legs=%d" % g.legs)
    check("6.4 y el tercero también", g.on_tick(1.09700, allowed=False) is not None)

    g2 = Grid(strategy="E1", step_pts=100, max_levels=5, free_hours=False,
              tp_usd=0)
    g2.open_base(+1, 1.10000)
    g2.on_tick(1.09900, allowed=True)
    check("6.5 con InpGridFreeHours=false no abre fuera de horario",
          g2.on_tick(1.09800, allowed=False) is None and g2.legs == 1)
    return g


def esc7_filtros():
    """7) Filtros: apagada, S2, circuit breaker, ventana semanal, tope de lote."""
    g = Grid(enable=False, strategy="E1", step_pts=100)
    g.open_base(+1, 1.10000)
    check("7.1 rejilla desactivada → no abre",
          g.on_tick(1.09000) is None and g.legs == 0)

    g2 = Grid(strategy="S2", step_pts=100)
    g2.open_base(+1, 1.10000)
    check("7.2 la Estrategia 2 no usa rejilla", g2.on_tick(1.09000) is None)

    g3 = Grid(strategy="E1", step_pts=100, tp_usd=0)
    g3.open_base(+1, 1.10000)
    check("7.3 circuit breaker → no abre", g3.on_tick(1.09000, cb=True) is None)
    check("7.4 ventana semanal → no abre", g3.on_tick(1.09000, weekly=True) is None)
    check("7.5 con todo permitido sí abre", g3.on_tick(1.09000) == 0.01)

    g4 = Grid(strategy="E3", on_e3=False, step_pts=100, tp_usd=0)
    g4.open_base(+1, 1.10000)
    check("7.6 InpGridOnE3=false → la E3 no usa rejilla", g4.on_tick(1.09000) is None)

    g5 = Grid(strategy="E1", step_pts=100, lot_init=0.10, lot_mult=2.0,
              lot_cap=0.25, max_levels=3, tp_usd=0)
    g5.open_base(+1, 1.10000)
    g5.on_tick(1.09900)
    g5.on_tick(1.09800)
    check("7.7 el tope de lote recorta 0.40 → 0.25", g5.on_tick(1.09700) == 0.25)
    return g


def esc8_cierres_parciales():
    """8) Cierres parciales: el nivel/CV se contabiliza con la ÚLTIMA."""
    g = Grid(strategy="E1", step_pts=100, lot_mult=2.0, max_levels=2,
             lot_init=0.01, tp_usd=0)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09900)
    g.on_tick(1.09800)
    check("8.1 hay 3 posiciones en la cesta", len(g.pos) == 3)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("8.2 primer cierre se DIFIERE", deferred is True and left == 2)
    check("8.3 todavía sin evento de nivel/CV", g.level_events == 0)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("8.4 segundo cierre se DIFIERE", deferred is True and left == 1)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("8.5 el ÚLTIMO cierre contabiliza (1 evento)",
          deferred is False and g.level_events == 1)
    return g


def esc9_tp_respaldo():
    """9) Respaldo: TP por precio medio cuando InpGridTPUsd = 0."""
    g = Grid(strategy="E1", step_pts=150, lot_init=0.01, lot_mult=1.0,
             max_levels=3, tp_usd=0.0, avg_tp=True, sl_pts=300, tp_pts=305)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09850)
    avg, _, _ = g.stats()
    check("9.1 sin TP en USD aparece el TP por precio medio",
          all(abs(p[3] - (avg + 305 * g.point)) < 1e-9 for p in g.pos),
          "tp=%.5f esp=%.5f" % (g.pos[-1][3], avg + 305 * g.point))
    check("9.2 la cesta sigue SIN SL", all(p[2] == 0.0 for p in g.pos))
    return g


def main():
    print("=" * 74)
    print(" SIMULACIÓN DE LA REJILLA (GRID) v8.60 — LOTE PROPIO · SIN SL ·")
    print(" TP EN USD · HASTA 20 NIVELES · NIVELES 2..N A CUALQUIER HORA")
    print("=" * 74)
    for fn in (esc1_progresion, esc2_lote_propio, esc3_sin_sl, esc4_tp_usd,
               esc5_maximo_20, esc6_horario, esc7_filtros,
               esc8_cierres_parciales, esc9_tp_respaldo):
        print("\n" + fn.__doc__.strip())
        fn()
    print("\n" + "=" * 74)
    fallos = [c for c in OK if not c[1]]
    for name, ok, info in OK:
        print(("  ✓ " if ok else "  ✗ ") + name +
              (("  [" + info + "]") if info and not ok else ""))
    print("=" * 74)
    if fallos:
        print("FALLAN %d comprobaciones de %d" % (len(fallos), len(OK)))
        raise SystemExit(1)
    print("Todos los escenarios de la REJILLA (v8.60) pasan (%d comprobaciones)." % len(OK))


if __name__ == "__main__":
    main()
