#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sim_grid.py — modelo en Python de la REJILLA (GRID) del EA v8.59
================================================================
Replica la lógica de la rejilla que se aplica a las ENTRADAS de la
Estrategia 1 y de la Estrategia 3 (nunca a la S2):

  · la apertura sigue siendo la de E1/E3 (aquí se simula con open_base)
  · el nivel n se abre cuando el precio recorre, EN CONTRA, desde el
    PEOR precio de la cesta:
        dist(n) = InpGridStepPts · InpGridDistMult^(n-1)
        (InpGridStepPts = 0 → mitad del SL del par)
  · lotaje del nivel n = (InpGridLotInit o lote del par) · InpGridLotMult^(n-1)
    con tope InpGridLotCap y normalizado al paso de volumen del símbolo
  · TP común sobre el PRECIO MEDIO (InpGridAvgTP)
  · SL común sobre el PRECIO MEDIO (InpGridBasketSL); las posiciones con
    SL protegido (1:2) no se tocan
  · el NIVEL/CV del par se contabiliza UNA sola vez, cuando cierra la
    ÚLTIMA posición de la cesta

Ejecutar:  python3 sim_grid.py
"""

# ---------------------------------------------------------------------------
#  Modelo de la rejilla
# ---------------------------------------------------------------------------
class Grid:
    def __init__(self,
                 enable=True, on_e1=True, on_e3=True, strategy="E1",
                 step_pts=0.0, dist_mult=1.0, lot_init=0.0, lot_mult=1.0,
                 max_levels=4, lot_cap=5.0, avg_tp=True, basket_sl=True,
                 keep_trail=False,
                 point=0.00001, digits=5, sl_pts=95.0, tp_pts=305.0,
                 vol_min=0.01, vol_max=50.0, vol_step=0.01, pair_lot=0.10):
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
        self.avg_tp      = avg_tp
        self.basket_sl   = basket_sl
        self.keep_trail  = keep_trail
        self.point       = point
        self.digits      = digits
        self.sl_pts      = sl_pts
        self.tp_pts      = tp_pts
        self.vol_min     = vol_min
        self.vol_max     = vol_max
        self.vol_step    = vol_step
        self.pair_lot    = pair_lot
        # estado
        self.dir         = 0
        self.legs        = 0
        self.pos         = []      # [(precio, lotes, sl, tp, protegido)]
        self.log         = []
        self.level_events = 0      # nº de veces que se actualizó nivel/CV

    # -- utilidades ---------------------------------------------------------
    def uses_strategy(self):
        if not self.enable:
            return False
        if self.strategy == "E1":
            return self.on_e1
        if self.strategy == "E3":
            return self.on_e3
        return False        # S2 nunca usa rejilla

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
        base = self.lot_init if self.lot_init > 0 else self.pair_lot
        m = max(0.1, self.lot_mult)
        lots = base * (m ** max(0, self.legs))
        if self.lot_cap > 0:
            lots = min(lots, self.lot_cap)
        return self.norm_lot(lots)

    def stats(self):
        if not self.pos:
            return 0.0, 0.0, 0.0
        sv = sum(l for _, l, _, _, _ in self.pos)
        spv = sum(p * l for p, l, _, _, _ in self.pos)
        avg = spv / sv
        if self.dir > 0:
            worst = min(p for p, _, _, _, _ in self.pos)
        else:
            worst = max(p for p, _, _, _, _ in self.pos)
        return avg, worst, sv

    def basket_sl_price(self, avg):
        return avg - self.sl_pts * self.point if self.dir > 0 \
            else avg + self.sl_pts * self.point

    def basket_tp_price(self, avg):
        return avg + self.tp_pts * self.point if self.dir > 0 \
            else avg - self.tp_pts * self.point

    # -- apertura de la estrategia (E1/E3) ----------------------------------
    def open_base(self, direction, price, lots=None):
        lots = self.pair_lot if lots is None else lots
        self.dir = 1 if direction > 0 else -1
        ptype = 1 if self.dir > 0 else -1
        sl = price - ptype * self.sl_pts * self.point
        tp = price + ptype * self.tp_pts * self.point
        self.pos.append((price, lots, sl, tp, False))
        self.legs = 0
        self.log.append("BASE %s %.2f lotes @%.5f SL=%.5f TP=%.5f" %
                        ("COMPRA" if self.dir > 0 else "VENTA", lots, price, sl, tp))

    # -- motor --------------------------------------------------------------
    def can_open(self, cb=False, weekly=False, allowed=True):
        if not self.uses_strategy():
            return False
        if not self.pos:
            return False
        if cb or weekly or not allowed:
            return False
        if self.max_levels <= 0:
            return False
        return self.legs < self.max_levels

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
        self.pos.append((price, lots, 0.0, 0.0, False))
        self.legs += 1
        self.recalc()
        self.log.append("REJILLA L%d %s %.2f lotes @%.5f (dist %.0f pts, media %.5f)" %
                        (self.legs, "COMPRA" if self.dir > 0 else "VENTA",
                         lots, price, need, self.stats()[0]))
        return lots

    def recalc(self):
        if not (self.avg_tp or self.basket_sl) or not self.pos:
            return
        avg, _, _ = self.stats()
        tp = self.basket_tp_price(avg) if self.avg_tp else 0.0
        sl = self.basket_sl_price(avg) if self.basket_sl else 0.0
        out = []
        for (p, l, csl, ctp, prot) in self.pos:
            nsl = csl if (sl <= 0 or prot) else sl
            ntp = ctp if tp <= 0 else tp
            out.append((p, l, nsl, ntp, prot))
        self.pos = out

    # -- cierres ------------------------------------------------------------
    def close_positions(self, count):
        """Cierra `count` posiciones (las más antiguas) y devuelve el P/L."""
        total = 0.0
        avg, _, _ = self.stats()
        ref = avg
        for _ in range(min(count, len(self.pos))):
            p, l, _, _, _ = self.pos.pop(0)
            total += (ref - p) / self.point * l * 10.0 if self.dir > 0 else 0.0
        return total

    def close_all(self, at_price=None):
        """Cierra la cesta entera a `at_price` y contabiliza UNA vez."""
        if not self.pos:
            return None
        avg, _, _ = self.stats()
        px = avg if at_price is None else at_price
        pl = 0.0
        for (p, l, _, _, _) in self.pos:
            pl += (px - p) * (1 if self.dir > 0 else -1) * l
        self.pos = []
        self.level_events += 1          # ← una sola actualización de nivel/CV
        self.log.append("CIERRE CESTA @%.5f P/L=%.2f (evento de nivel/CV #%d)" %
                        (px, pl, self.level_events))
        return pl

    def partial_close_events(self, price):
        """Cierra una posición y dice si se contabiliza YA o se difiere."""
        if not self.pos:
            return None
        p, l, _, _, _ = self.pos.pop(0)
        pl = (price - p) * (1 if self.dir > 0 else -1) * l
        deferred = len(self.pos) > 0      # quedan posiciones → se difiere
        if not deferred:
            self.level_events += 1
        return pl, deferred, len(self.pos)


def money(pl, lots=1.0, pip_value=10.0, point=0.00001):
    """P/L aproximado en unidades de precio (no se usa en los asserts)."""
    return pl


# ---------------------------------------------------------------------------
#  Escenarios
# ---------------------------------------------------------------------------
OK = []


def check(name, cond, info=""):
    OK.append((name, bool(cond), info))


def esc1_progresion():
    """1) Progresión de distancia y lotaje (2× lote, 1.5× distancia)."""
    g = Grid(strategy="E1", step_pts=150, dist_mult=1.5, lot_init=0.10,
             lot_mult=2.0, max_levels=3)
    g.open_base(+1, 1.10000)
    # 149 pts en contra: no debe abrir
    check("1.1 no abre antes de la distancia",
          g.on_tick(1.10000 - 149 * g.point) is None)
    # 150 pts: nivel 1, lote 0.10
    l1 = g.on_tick(1.10000 - 150 * g.point)
    check("1.2 nivel 1 = 0.10 lotes a 150 pts", l1 == 0.10, "lot=%s" % l1)
    # el peor precio ahora es 1.09850 → el nivel 2 exige 225 pts más (1.09625)
    check("1.3 nivel 2 no abre a 224 pts",
          g.on_tick(1.09850 - 224 * g.point) is None)
    l2 = g.on_tick(1.09850 - 225 * g.point)
    check("1.4 nivel 2 = 0.20 lotes a 225 pts (1.5×)", l2 == 0.20, "lot=%s" % l2)
    # nivel 3: 337.5 pts desde 1.09625
    l3 = g.on_tick(1.09625 - 338 * g.point)
    check("1.5 nivel 3 = 0.40 lotes a 337.5 pts (1.5²)", l3 == 0.40, "lot=%s" % l3)
    check("1.6 no pasa del máximo de niveles",
          g.on_tick(1.09625 - 2000 * g.point) is None, "legs=%d" % g.legs)
    for ln in g.log:
        print("   ", ln)
    return g


def esc2_tp_medio():
    """2) TP común sobre la media: la cesta cierra en positivo."""
    g = Grid(strategy="E3", step_pts=150, dist_mult=1.0, lot_init=0.10,
             lot_mult=2.0, max_levels=3, sl_pts=300, tp_pts=305)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09850)
    g.on_tick(1.09700)
    avg, worst, lots = g.stats()
    tp = g.basket_tp_price(avg)
    sl = g.basket_sl_price(avg)
    # la entrada base usa el lote del par; la rejilla arranca en InpGridLotInit
    check("2.0 lotes de la cesta = base 0.10 + L1 0.10 + L2 0.20",
          [round(x[1], 2) for x in g.pos] == [0.10, 0.10, 0.20],
          str([round(x[1], 2) for x in g.pos]))
    esp = ((1.10000 * 0.10 + 1.09850 * 0.10 + 1.09700 * 0.20) / 0.40)
    check("2.1 media ponderada correcta", abs(avg - esp) < 1e-7,
          "avg=%.5f esp=%.5f" % (avg, esp))
    check("2.2 TP común = media + tp", abs(tp - (avg + 305 * g.point)) < 1e-9,
          "tp=%.5f" % tp)
    check("2.3 SL común = media - sl", abs(sl - (avg - 300 * g.point)) < 1e-9,
          "sl=%.5f" % sl)
    check("2.4 todas las posiciones comparten TP",
          all(abs(p[3] - tp) < 1e-9 for p in g.pos))
    check("2.5 todas comparten SL (ninguna protegida)",
          all(abs(p[2] - sl) < 1e-9 for p in g.pos))
    pl = g.close_all(at_price=tp)
    check("2.6 la cesta cierra en GANANCIA en el TP medio", pl > 0, "PL=%.5f" % pl)
    check("2.7 una sola actualización de nivel/CV", g.level_events == 1)
    print("    media=%.5f TP=%.5f SL=%.5f → PL=%.5f" % (avg, tp, sl, pl))
    return g


def esc3_tope_lote():
    """3) Tope de lote por nivel."""
    g = Grid(strategy="E1", step_pts=100, dist_mult=1.0, lot_init=0.10,
             lot_mult=2.0, max_levels=3, lot_cap=0.25)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09900)
    g.on_tick(1.09800)
    l3 = g.on_tick(1.09700)
    check("3.1 el tope de lote recorta 0.40 → 0.25", l3 == 0.25, "lot=%s" % l3)
    return g


def esc4_lote_par():
    """4) lot_init = 0 → usa el lote del nivel del par."""
    g = Grid(strategy="E3", step_pts=100, lot_init=0.0, lot_mult=1.0,
             pair_lot=0.37, max_levels=2)
    g.open_base(+1, 1.10000)
    l1 = g.on_tick(1.09900)
    check("4.1 lot_init=0 usa el lote del par (0.37)", l1 == 0.37, "lot=%s" % l1)
    return g


def esc5_paso_auto():
    """5) step_pts = 0 → mitad del SL del par."""
    g = Grid(strategy="E1", step_pts=0.0, sl_pts=200.0, lot_mult=1.0,
             max_levels=2)
    g.open_base(+1, 1.10000)
    check("5.1 paso automático = 100 pts (SL 200 / 2)",
          abs(g.step_points() - 100.0) < 1e-9, "paso=%.1f" % g.step_points())
    check("5.2 no abre a 99 pts", g.on_tick(1.10000 - 99 * g.point) is None)
    check("5.3 abre a 100 pts", g.on_tick(1.10000 - 100 * g.point) == 0.10)
    return g


def esc6_cierres_parciales():
    """6) Cierres parciales: el nivel/CV se contabiliza con la ÚLTIMA."""
    g = Grid(strategy="E1", step_pts=100, lot_mult=2.0, max_levels=2,
             sl_pts=300, tp_pts=305)
    g.open_base(+1, 1.10000)
    g.on_tick(1.09900)
    g.on_tick(1.09800)
    check("6.1 hay 3 posiciones en la cesta", len(g.pos) == 3)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("6.2 primer cierre se DIFIERE", deferred is True and left == 2,
          "left=%d" % left)
    check("6.3 todavía sin evento de nivel/CV", g.level_events == 0)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("6.4 segundo cierre se DIFIERE", deferred is True and left == 1)
    pl, deferred, left = g.partial_close_events(1.09800)
    check("6.5 el ÚLTIMO cierre contabiliza (1 evento)",
          deferred is False and g.level_events == 1, "eventos=%d" % g.level_events)
    return g


def esc7_filtros():
    """7) Filtros: rejilla apagada, S2, CB, ventana semanal, fuera de horario."""
    g = Grid(enable=False, strategy="E1", step_pts=100)
    g.open_base(+1, 1.10000)
    check("7.1 rejilla desactivada → no abre",
          g.on_tick(1.09000) is None and g.legs == 0)

    g2 = Grid(strategy="S2", step_pts=100)
    g2.open_base(+1, 1.10000)
    check("7.2 la Estrategia 2 no usa rejilla",
          g2.on_tick(1.09000) is None and g2.legs == 0)

    g3 = Grid(strategy="E1", step_pts=100)
    g3.open_base(+1, 1.10000)
    check("7.3 circuit breaker → no abre", g3.on_tick(1.09000, cb=True) is None)
    check("7.4 ventana semanal → no abre", g3.on_tick(1.09000, weekly=True) is None)
    check("7.5 fuera de horario → no abre", g3.on_tick(1.09000, allowed=False) is None)
    check("7.6 con todo permitido sí abre", g3.on_tick(1.09000) == 0.10)

    g4 = Grid(strategy="E3", on_e3=False, step_pts=100)
    g4.open_base(+1, 1.10000)
    check("7.7 InpGridOnE3=false → la E3 no usa rejilla", g4.on_tick(1.09000) is None)
    return g


def esc8_sl_protegido():
    """8) El 1:2 protegido no se sobrescribe; el TP sí se recalcula."""
    g = Grid(strategy="E1", step_pts=100, lot_mult=1.0, max_levels=2,
             sl_pts=300, tp_pts=305, basket_sl=True, avg_tp=True)
    g.open_base(+1, 1.10000)
    # la primera posición ya tiene el SL movido a protección
    p, l, sl, tp, prot = g.pos[0]
    g.pos[0] = (p, l, 1.10020, tp, True)      # protegido en +20 pts
    g.on_tick(1.09900)                        # nivel 1 → recalcula
    p, l, sl2, tp2, prot2 = g.pos[0]
    avg, _, _ = g.stats()
    check("8.1 el SL protegido NO se toca", abs(sl2 - 1.10020) < 1e-12,
          "sl=%.5f" % sl2)
    check("8.2 el TP sí pasa a la media",
          abs(tp2 - g.basket_tp_price(avg)) < 1e-12, "tp=%.5f" % tp2)
    p, l, sl3, tp3, prot3 = g.pos[1]
    check("8.3 la posición nueva sí lleva el SL de la media",
          abs(sl3 - g.basket_sl_price(avg)) < 1e-12, "sl=%.5f" % sl3)
    return g


def main():
    print("=" * 74)
    print(" SIMULACIÓN DE LA REJILLA (GRID) SOBRE LAS ENTRADAS DE E1 Y E3")
    print("=" * 74)
    for fn in (esc1_progresion, esc2_tp_medio, esc3_tope_lote, esc4_lote_par,
               esc5_paso_auto, esc6_cierres_parciales, esc7_filtros,
               esc8_sl_protegido):
        print("\n" + fn.__doc__.strip())
        fn()
    print("\n" + "=" * 74)
    fallos = [c for c in OK if not c[1]]
    for name, ok, info in OK:
        print(("  ✓ " if ok else "  ✗ ") + name + (("  [" + info + "]") if info and not ok else ""))
    print("=" * 74)
    if fallos:
        print("FALLAN %d comprobaciones de %d" % (len(fallos), len(OK)))
        raise SystemExit(1)
    print("Todos los escenarios de la REJILLA (v8.59) pasan (%d comprobaciones)." % len(OK))


if __name__ == "__main__":
    main()
