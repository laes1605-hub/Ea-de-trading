# Simulación en Python de la ESTRATEGIA 3 (v8.57) del EA:
#   SMC multi-temporal — CHoCH/BOS + POI (order block + FVG) + 50%
#   (ver `trabajador multichart.mq5`, funciones Smc3*).
#
# Qué modela (idéntico al MQL5):
#   · El motor de líneas L1-L4 se instancia TRES veces (TF alto, medio, bajo);
#     cada instancia emite CHoCH (cambia el bias) y BOS (continuación) con su
#     TRAMO (origen → extremo) en LastHigh/LastLow.
#   · TF ALTO  → bias + rango [L2..L1] y su 50% (premium / descuento).
#   · TF MEDIO → el rompimiento entrega el tramo; dentro de él se busca el POI:
#       - ORDER BLOCK = última vela contraria antes del impulso
#       - FVG (imbalance de 3 velas) que solape con el OB
#   · La zona se ARMA cuando el precio vuelve a entrar en ella, se MITIGA
#     cuando el cierre del TF medio la atraviesa y CADUCA por antigüedad.
#   · TF BAJO  → BOS/CHoCH a favor, con la zona armada → se congela el nivel
#     (50% del tramo del gatillo / 50% de la zona / borde proximal).
#   · Invalidación: cierre del TF bajo más allá del origen del tramo o del lado
#     contrario de la zona.
#   · Órdenes: LIMIT virtual → vOPEN → LIVE (aquí solo la fase virtual), con
#     SL/TP de la configuración del EA (InpSL_Points / InpTP_Points).
#
# Series MQL5: índice 0 = vela en formación, 1 = última vela cerrada.

BIAS_UNDEF, BIAS_BULL, BIAS_BEAR = 0, 1, -1

ENTRY_LEG50, ENTRY_ZONE50, ENTRY_ZONEPROX = "LEG50", "ZONE50", "ZONEPROX"


class SE:
    """Motor de líneas L1-L4 (mismo que la E1/E2: CHoCH y BOS)."""

    def __init__(self, bars=None):
        self.L1 = self.L2 = self.L3 = self.L4 = self.EQ = 0.0
        self.L3L4 = False
        self.Bias = BIAS_UNDEF
        self.RefLevel = 0.0
        self.BosDone = False
        self.BosLegHigh = self.BosLegLow = 0.0
        self.LastHigh = self.LastLow = 0.0
        self.Valid = False
        if bars:
            self.init(bars)

    def init(self, bars):
        self.L1 = max(b[1] for b in bars)
        self.L2 = min(b[2] for b in bars)
        c = bars[-1]
        self.Bias = BIAS_BULL if c[3] > c[0] else (BIAS_BEAR if c[3] < c[0] else BIAS_UNDEF)
        self.eq(); self.Valid = True

    def eq(self):
        self.EQ = self.L2 + (self.L1 - self.L2) * 0.5

    def clear_reaction(self):
        self.L3 = self.L4 = 0.0
        self.L3L4 = False
        self.RefLevel = 0.0
        self.BosDone = False
        self.BosLegHigh = self.BosLegLow = 0.0

    def commit(self, dirn):
        if dirn == 0 or not self.L3L4:
            return 0
        old = self.Bias
        new = BIAS_BULL if dirn > 0 else BIAS_BEAR
        self.LastHigh = max(self.L3, self.L4)
        self.LastLow = min(self.L3, self.L4)
        self.L1, self.L2 = self.L3, self.L4
        if self.L1 < self.L2:
            self.L1, self.L2 = self.L2, self.L1
        self.Bias = new
        self.eq(); self.clear_reaction()
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

    def on_tick(self, price):
        if not self.L3L4:
            return
        self.L3 = max(self.L3, price)
        self.L4 = min(self.L4, price)
        self.BosLegHigh = max(self.BosLegHigh, price)
        self.BosLegLow = min(self.BosLegLow, price)
        if self.Bias == BIAS_BULL and price > self.L1:
            self.L1 = price; self.eq()
        elif self.Bias == BIAS_BEAR and price < self.L2:
            self.L2 = price; self.eq()

    def on_close(self, bar):
        """Devuelve (choch, bos)."""
        O, H, L, C = bar
        green, red = C > O, C < O
        if self.Bias == BIAS_UNDEF:
            self.Bias = BIAS_BULL if green else (BIAS_BEAR if red else BIAS_UNDEF)
            return 0, 0
        if self.L3L4:
            if H > self.L3: self.L3 = H
            if L < self.L4: self.L4 = L
            if H > self.BosLegHigh: self.BosLegHigh = H
            if L < self.BosLegLow: self.BosLegLow = L
            contrary = (self.Bias == BIAS_BULL and red) or (self.Bias == BIAS_BEAR and green)
            if contrary:
                if self.BosDone:
                    self.BosLegHigh, self.BosLegLow = H, L
                self.RefLevel = self.L1 if self.Bias == BIAS_BULL else self.L2
                self.BosDone = False
            blh, bll = self.BosLegHigh, self.BosLegLow
            trig = self.break_dir(O, C)
            choch = self.commit(trig) if trig else 0
            if trig != 0:
                if choch == 0:
                    if blh > bll:
                        self.LastHigh, self.LastLow = blh, bll
                    return 0, trig
                return choch, 0
            return 0, self.continuation(C)
        # sin reacción: activar reacción con vela contraria / mover L1-L2
        if self.Bias == BIAS_BULL:
            if green:
                if H > self.L1: self.L1 = H; self.eq()
            else:
                self.L3L4 = True
                self.L3 = self.L1; self.L4 = L
                self.RefLevel = self.L1; self.BosDone = False
                self.BosLegHigh, self.BosLegLow = H, L
        else:
            if red:
                if L < self.L2: self.L2 = L; self.eq()
            else:
                self.L3L4 = True
                self.L3 = H; self.L4 = self.L2
                self.RefLevel = self.L2; self.BosDone = False
                self.BosLegHigh, self.BosLegLow = H, L
        return 0, 0


# ---------------------------------------------------------------------------
#  Estrategia 3
# ---------------------------------------------------------------------------
class Smc3:
    def __init__(self, h, m, l, entry_mode=ENTRY_LEG50, use_discount=True,
                 use_fvg=True, require_fvg=False, cancel_zone=True,
                 accept_bos=True, accept_choch=True, min_leg_pts=0.0,
                 lookback=8, zone_bars=120, point=0.00001):
        self.H, self.M, self.L = h, m, l
        self.entry_mode = entry_mode
        self.use_discount, self.use_fvg, self.require_fvg = use_discount, use_fvg, require_fvg
        self.cancel_zone = cancel_zone
        self.accept_bos, self.accept_choch = accept_bos, accept_choch
        self.min_leg_pts = min_leg_pts
        self.lookback, self.zone_bars, self.point = lookback, zone_bars, point
        self.zones = []          # dicts
        self.trig = None         # gatillo pendiente
        self.entry_buy = self.entry_sell = 0.0
        self.leg_bh = self.leg_bl = self.leg_sh = self.leg_sl = 0.0
        self.zone_bt = self.zone_bb = self.zone_st = self.zone_sb = 0.0
        self.wait_buy = self.wait_sell = False
        self.vpend_buy = self.vpend_sell = False
        self.vprice_buy = self.vprice_sell = 0.0
        self.virtual = None
        self.log = []
        self.now = 0

    # --- utilidades ------------------------------------------------------
    def say(self, txt):
        self.log.append(txt)
        print("   " + txt)

    def tol(self):
        return max(self.point * 2.0, 1e-7)

    def tm(self, s):
        return s  # en MQL5 es EnumToString(TF); aquí el nombre del TF

    # --- TF medio: rompimiento → POI -------------------------------------
    def build_poi(self, dirn, legH, legL, barsM):
        hi, lo = max(legH, legL), min(legH, legL)
        if hi <= lo:
            return None
        tol = self.tol()
        # 1) origen del tramo (extremo del impulso) mirando hacia atrás
        oJ, best = -1, 0.0
        for j in range(1, self.lookback + 1):
            O, H, L, C = barsM[j]
            if dirn > 0 and L < lo - tol:
                break
            if dirn < 0 and H > hi + tol:
                break
            if dirn > 0:
                if best == 0.0 or L < best:
                    best, oJ = L, j
            else:
                if best == 0.0 or H > best:
                    best, oJ = H, j
        if oJ < 0:
            return None
        # 2) orden block: última vela contraria antes del impulso
        obJ = -1
        for j in range(oJ, min(self.lookback, oJ + 5) + 1):
            O, H, L, C = barsM[j]
            if dirn > 0 and C < O:
                obJ = j; break
            if dirn < 0 and C > O:
                obJ = j; break
        if obJ < 0:
            return None
        obH, obL = barsM[obJ][1], barsM[obJ][2]
        # 3) FVG de 3 velas dentro del impulso
        has, fvgH, fvgL = False, 0.0, 0.0
        if self.use_fvg:
            for j in range(1, max(2, oJ)):
                hO, lO = barsM[j + 2][1], barsM[j + 2][2]
                hN, lN = barsM[j][1], barsM[j][2]
                if dirn > 0 and lN > hO:
                    fvgL, fvgH, has = hO, lN, True; break
                if dirn < 0 and hN < lO:
                    fvgH, fvgL, has = lO, hN, True; break
        if self.require_fvg and not has:
            return None
        # 4) zona = OB (∪ FVG si se solapan)
        zTop, zBot, use = obH, obL, False
        if has:
            ovTop, ovBot = min(obH, fvgH), max(obL, fvgL)
            if ovTop >= ovBot:
                zTop, zBot, use = max(obH, fvgH), min(obL, fvgL), True
        if zTop <= zBot:
            return None
        # 5) la zona tiene que estar en la mitad correcta del tramo
        leg50 = (hi + lo) * 0.5
        if dirn > 0 and zBot > leg50 + tol:
            return None
        if dirn < 0 and zTop < leg50 - tol:
            return None
        return dict(Active=True, IsBull=(dirn > 0), Top=zTop, Bottom=zBot,
                    OBHigh=obH, OBLow=obL, OBTime=oJ, HasFVG=use,
                    LegHigh=hi, LegLow=lo, Created=self.now, Mitigated=False,
                    Armed=False, ArmedTime=0, EntryFrozen=False, EntryPrice=0.0)

    def on_mid_break(self, dirn, is_choch, legH, legL, barsM):
        if dirn == 0:
            return
        if self.min_leg_pts > 0 and (max(legH, legL) - min(legH, legL)) / self.point < self.min_leg_pts:
            return
        z = self.build_poi(dirn, legH, legL, barsM)
        if not z:
            self.say("TF medio %s %s · tramo [%.5f..%.5f] → sin POI válido" %
                     ("CHoCH" if is_choch else "BOS", "ALCISTA" if dirn > 0 else "BAJISTA",
                      min(legH, legL), max(legH, legL)))
            return
        for old in self.zones:
            if old["IsBull"] == z["IsBull"] and old["OBTime"] == z["OBTime"]:
                return
        self.zones.append(z)
        self.say("TF medio %s %s · tramo [%.5f..%.5f] → POI %s [%.5f..%.5f]%s" %
                 ("CHoCH" if is_choch else "BOS", "ALCISTA" if dirn > 0 else "BAJISTA",
                  z["LegLow"], z["LegHigh"], "COMPRA" if z["IsBull"] else "VENTA",
                  z["Bottom"], z["Top"], " (OB+FVG)" if z["HasFVG"] else " (OB)"))

    # --- mantenimiento: caducidad / mitigación / armado -------------------
    def maintain(self, bid, closeM):
        tol = self.tol()
        for z in self.zones:
            if not z["Active"]:
                continue
            if self.now - z["Created"] > self.zone_bars:
                z["Active"] = False
                self.say("POI %s caducada" % ("COMPRA" if z["IsBull"] else "VENTA"))
                continue
            if closeM > 0:
                broke = (closeM < z["Bottom"] - tol) if z["IsBull"] else (closeM > z["Top"] + tol)
                if broke:
                    z["Mitigated"] = z["Active"] = z["Armed"] = False
                    self.say("POI %s [%.5f..%.5f] MITIGADA (cierre %.5f)" %
                             ("COMPRA" if z["IsBull"] else "VENTA",
                              z["Bottom"], z["Top"], closeM))
                    continue
            if not z["Armed"] and z["Bottom"] - tol <= bid <= z["Top"] + tol:
                z["Armed"] = True
                z["ArmedTime"] = self.now
                self.say("precio en el POI %s [%.5f..%.5f] → ARMADA" %
                         ("COMPRA" if z["IsBull"] else "VENTA", z["Bottom"], z["Top"]))

    # --- gatillo del TF bajo ---------------------------------------------
    def on_low_break(self, dirn, is_choch, legH, legL):
        self.trig = dict(dir=dirn, choch=is_choch, t=self.now,
                         hi=max(legH, legL), lo=min(legH, legL))
        self.trig["mid"] = (self.trig["hi"] + self.trig["lo"]) * 0.5

    def process_trigger(self, bid):
        if not self.trig:
            return
        g, self.trig = self.trig, None
        dirn, is_choch = g["dir"], g["choch"]
        if not self.accept_choch and is_choch:
            return
        if not self.accept_bos and not is_choch:
            return
        if self.now - g["t"] > 3:
            return
        if self.H.Bias != dirn:
            self.say("gatillo %s ignorado: TF alto %s" %
                     ("ALCISTA" if dirn > 0 else "BAJISTA",
                      {BIAS_BULL: "ALCISTA", BIAS_BEAR: "BAJISTA"}.get(self.H.Bias, "SIN BIAS")))
            return
        if self.use_discount and self.H.EQ > 0:
            if dirn > 0 and bid > self.H.EQ + self.tol():
                self.say("compra descartada: precio en PREMIUM (%.5f > 50%% %.5f)" % (bid, self.H.EQ)); return
            if dirn < 0 and bid < self.H.EQ - self.tol():
                self.say("venta descartada: precio en DESCUENTO (%.5f < 50%% %.5f)" % (bid, self.H.EQ)); return
        if self.M.Bias != dirn:
            self.say("gatillo ignorado: TF medio no acompaña"); return
        zi = -1
        for i, z in enumerate(self.zones):
            if not z["Active"] or z["Mitigated"] or not z["Armed"] or z["EntryFrozen"]:
                continue
            if z["IsBull"] != (dirn > 0):
                continue
            if z["ArmedTime"] > g["t"]:
                continue
            if zi < 0 or z["Created"] > self.zones[zi]["Created"]:
                zi = i
        if zi < 0:
            self.say("gatillo %s sin POI armada del lado %s" %
                     ("ALCISTA" if dirn > 0 else "BAJISTA",
                      "COMPRA" if dirn > 0 else "VENTA"))
            return
        z = self.zones[zi]
        lvl = g["mid"]
        if self.entry_mode == ENTRY_ZONE50:
            lvl = (z["Top"] + z["Bottom"]) * 0.5
        elif self.entry_mode == ENTRY_ZONEPROX:
            lvl = z["Top"] if dirn > 0 else z["Bottom"]
        if dirn > 0:
            self.entry_buy, self.leg_bh, self.leg_bl = lvl, g["hi"], g["lo"]
            self.zone_bt, self.zone_bb = z["Top"], z["Bottom"]
            self.wait_buy = True
        else:
            self.entry_sell, self.leg_sh, self.leg_sl = lvl, g["hi"], g["lo"]
            self.zone_st, self.zone_sb = z["Top"], z["Bottom"]
            self.wait_sell = True
        z["EntryFrozen"], z["EntryPrice"] = True, lvl
        self.say("%s %s con POI %s armada → %s CONGELADO @%.5f" %
                 ("CHoCH" if is_choch else "BOS", "ALCISTA" if dirn > 0 else "BAJISTA",
                  "COMPRA" if dirn > 0 else "VENTA",
                  {ENTRY_LEG50: "50% del tramo", ENTRY_ZONE50: "50% de la zona",
                   ENTRY_ZONEPROX: "borde proximal"}[self.entry_mode], lvl))

    # --- colocación de la LIMIT ------------------------------------------
    def try_place(self, bid):
        if self.wait_buy and bid > self.entry_buy:
            self.vpend_buy, self.vprice_buy, self.wait_buy = True, self.entry_buy, False
            self.say("precio encima del nivel congelado → LIMIT COMPRA @%.5f" % self.entry_buy)
        elif self.wait_sell and bid < self.entry_sell:
            self.vpend_sell, self.vprice_sell, self.wait_sell = True, self.entry_sell, False
            self.say("precio debajo del nivel congelado → LIMIT VENTA @%.5f" % self.entry_sell)

    def check_fill(self, ask, bid, sl_pts=95.0, tp_pts=305.0):
        if self.vpend_buy and ask <= self.vprice_buy:
            self.virtual = dict(dir=1, price=self.vprice_buy,
                                sl=self.vprice_buy - sl_pts * self.point,
                                tp=self.vprice_buy + tp_pts * self.point)
            self.vpend_buy = False
            self.say("vOPEN COMPRA @%.5f SL=%.5f TP=%.5f (virtual)" %
                     (self.virtual["price"], self.virtual["sl"], self.virtual["tp"]))
        elif self.vpend_sell and bid >= self.vprice_sell:
            self.virtual = dict(dir=-1, price=self.vprice_sell,
                                sl=self.vprice_sell + sl_pts * self.point,
                                tp=self.vprice_sell - tp_pts * self.point)
            self.vpend_sell = False
            self.say("vOPEN VENTA @%.5f SL=%.5f TP=%.5f (virtual)" %
                     (self.virtual["price"], self.virtual["sl"], self.virtual["tp"]))

    # --- invalidación por origen del tramo / zona ------------------------
    def check_invalid(self, closeL):
        if self.wait_buy or self.vpend_buy:
            if self.leg_bl > 0 and closeL < self.leg_bl:
                self.say("cierre %.5f rompe el ORIGEN del tramo de COMPRA (%.5f) → cancelada" %
                         (closeL, self.leg_bl))
                self.wait_buy = self.vpend_buy = False
                self.entry_buy = 0.0
                self.unfreeze(True)
                return
            if self.cancel_zone and self.zone_bb > 0 and closeL < self.zone_bb:
                self.say("cierre %.5f rompe la ZONA POI de COMPRA (%.5f) → cancelada" %
                         (closeL, self.zone_bb))
                self.wait_buy = self.vpend_buy = False
                self.entry_buy = 0.0
                self.unfreeze(True)
                return
        if self.wait_sell or self.vpend_sell:
            if self.leg_sh > 0 and closeL > self.leg_sh:
                self.say("cierre %.5f rompe el ORIGEN del tramo de VENTA (%.5f) → cancelada" %
                         (closeL, self.leg_sh))
                self.wait_sell = self.vpend_sell = False
                self.entry_sell = 0.0
                self.unfreeze(False)
                return
            if self.cancel_zone and self.zone_st > 0 and closeL > self.zone_st:
                self.say("cierre %.5f rompe la ZONA POI de VENTA (%.5f) → cancelada" %
                         (closeL, self.zone_st))
                self.wait_sell = self.vpend_sell = False
                self.entry_sell = 0.0
                self.unfreeze(False)

    def unfreeze(self, bull):
        for z in self.zones:
            if z["Active"] and z["IsBull"] == bull and z["EntryFrozen"]:
                z["EntryFrozen"], z["EntryPrice"], z["Armed"] = False, 0.0, False


# ---------------------------------------------------------------------------
#  Series de prueba (índice 0 = la más ANTIGUA; el motor usa bars[j] con
#  j = velas hacia atrás, igual que iHigh/iLow en MQL5).
# ---------------------------------------------------------------------------
H4_BULL = [
    (1.0810, 1.0830, 1.0800, 1.0825),
    (1.0825, 1.0850, 1.0820, 1.0845),
    (1.0845, 1.0870, 1.0840, 1.0865),
    (1.0865, 1.0890, 1.0860, 1.0885),
    (1.0885, 1.0910, 1.0880, 1.0905),
    (1.0905, 1.0930, 1.0900, 1.0925),
    (1.0925, 1.0950, 1.0920, 1.0945),
    (1.0945, 1.0970, 1.0940, 1.0965),
    (1.0965, 1.0990, 1.0960, 1.0985),
    (1.0985, 1.1000, 1.0975, 1.0995),   # último alcista → bias ALCISTA, L1=1.1000 L2=1.0800
]
H4_BEAR = [
    (1.0990, 1.1000, 1.0970, 1.0975),
    (1.0975, 1.0985, 1.0950, 1.0960),
    (1.0960, 1.0970, 1.0935, 1.0945),
    (1.0945, 1.0955, 1.0920, 1.0930),
    (1.0930, 1.0940, 1.0905, 1.0915),
    (1.0915, 1.0925, 1.0890, 1.0900),
    (1.0900, 1.0910, 1.0875, 1.0885),
    (1.0885, 1.0895, 1.0860, 1.0865),   # último bajista → bias BAJISTA
]
# TF medio: bias ALCISTA con techo L1 = 1.0870 y suelo L2 = 1.0845
M15_INIT = [
    (1.0850, 1.0860, 1.0845, 1.0855),
    (1.0855, 1.0862, 1.0848, 1.0852),
    (1.0852, 1.0865, 1.0850, 1.0862),
    (1.0862, 1.0870, 1.0855, 1.0865),   # último ALCISTA → bias ALCISTA
]
M15_BREAK = [
    (1.0865, 1.0868, 1.0855, 1.0858),   # vela contraria → reacción (L4=1.0855)
    (1.0858, 1.0890, 1.0857, 1.0885),   # impulso → BOS alcista, tramo [1.0855..1.0890]
]
# TF bajo: bias BAJISTA con techo L1 = 1.0870 y suelo L2 = 1.0850
M3_INIT = [
    (1.0875, 1.0870, 1.0855, 1.0860),
    (1.0860, 1.0868, 1.0852, 1.0856),
    (1.0856, 1.0866, 1.0850, 1.0864),
    (1.0864, 1.0866, 1.0858, 1.0860),   # último BAJISTA → bias BAJISTA
]
M3_CHOCH = [
    (1.0860, 1.0872, 1.0858, 1.0870),   # vela alcista contraria → reacción (L3=1.0872)
    (1.0862, 1.0878, 1.0860, 1.0874),   # cierra sobre L1 → CHoCH alcista, tramo [1.0850..1.0878]
]


def rev(bars):
    """La serie de prueba va de antigua a reciente; el motor indexa hacia atrás."""
    return list(reversed(bars))


def setup(entry_mode=ENTRY_LEG50, h4=H4_BULL, **kw):
    """Motor alto + medio ya con el BOS y su POI; TF bajo listo para el gatillo."""
    H = SE(list(h4))
    M = SE(list(M15_INIT))
    L = SE(list(M3_INIT))
    smc = Smc3(H, M, L, entry_mode=entry_mode, **kw)
    smc.now = 100
    barsM = rev(M15_INIT + M15_BREAK)          # barsM[1] = última vela cerrada
    choch = bos = 0
    for b in M15_BREAK:
        c, bo = M.on_close(b)
        choch = c or choch
        bos = bo or bos
    smc.now = 110
    if bos or choch:
        smc.on_mid_break(bos or choch, choch != 0, M.LastHigh, M.LastLow, barsM)
    return H, M, L, smc, barsM


def title(n, t):
    print("\n===== %s. %s =====" % (n, t))


# ---------------------------------------------------------------------------
#  1) Flujo completo: H4 alcista + descuento → POI del M15 → armada →
#     CHoCH M3 → entrada en el 50% del tramo → LIMIT → vOPEN
# ---------------------------------------------------------------------------
title(1, "Flujo completo: 3 temporalidades + POI + 50% del tramo del gatillo")
H, M, L, smc, barsM = setup()
smc.maintain(1.0862, barsM[1][3])              # el precio entra en el POI
for b in M3_CHOCH:
    c, bo = L.on_close(b)
    if c or bo:
        smc.on_low_break(c or bo, c != 0, L.LastHigh, L.LastLow)
smc.process_trigger(1.0874)
smc.try_place(1.0874)
smc.check_fill(1.0863, 1.0864)                 # el Ask baja al nivel → se llena
assert smc.virtual is not None, "no se abrió la virtual"
assert abs(smc.virtual["price"] - 1.08640) < 1e-9, smc.virtual
assert abs(smc.virtual["sl"] - 1.08545) < 1e-9
assert abs(smc.virtual["tp"] - 1.08945) < 1e-9
print("   RESULTADO: vOPEN", smc.virtual)

# ---------------------------------------------------------------------------
#  2) El TF alto manda: gatillo alcista con H4 bajista → IGNORADO
# ---------------------------------------------------------------------------
title(2, "Correlación: gatillo alcista con el TF alto BAJISTA → IGNORADO")
H2, M2, L2, smc2, barsM2 = setup(h4=H4_BEAR)
smc2.maintain(1.0862, barsM2[1][3])
for b in M3_CHOCH:
    c, bo = L2.on_close(b)
    if c or bo:
        smc2.on_low_break(c or bo, c != 0, L2.LastHigh, L2.LastLow)
smc2.process_trigger(1.0874)
smc2.try_place(1.0874)
assert smc2.virtual is None and not smc2.wait_buy and not smc2.vpend_buy
print("   RESULTADO: sin entrada (correcto)")

# ---------------------------------------------------------------------------
#  3) Premium: precio por encima del 50% del TF alto → compra descartada
# ---------------------------------------------------------------------------
title(3, "Descuento: precio en PREMIUM (encima del 50% del TF alto) → descartada")
H3, M3e, L3, smc3, barsM3 = setup()
smc3.maintain(1.0862, barsM3[1][3])
for b in M3_CHOCH:
    c, bo = L3.on_close(b)
    if c or bo:
        smc3.on_low_break(c or bo, c != 0, L3.LastHigh, L3.LastLow)
smc3.process_trigger(1.0950)                   # por encima del 50% (1.0900)
assert not smc3.wait_buy and not smc3.vpend_buy
print("   RESULTADO: sin entrada (correcto)")

# ---------------------------------------------------------------------------
#  4) El gatillo llega SIN que el precio haya tocado el POI → ignorado
# ---------------------------------------------------------------------------
title(4, "Gatillo sin POI armada (el precio nunca entró en la zona) → ignorado")
H4s, M4, L4, smc4, barsM4 = setup()
smc4.maintain(1.0895, barsM4[1][3])            # precio por encima de la zona → no arma
for b in M3_CHOCH:
    c, bo = L4.on_close(b)
    if c or bo:
        smc4.on_low_break(c or bo, c != 0, L4.LastHigh, L4.LastLow)
smc4.process_trigger(1.0874)
assert not smc4.wait_buy and not smc4.vpend_buy
print("   RESULTADO: sin entrada (correcto)")

# ---------------------------------------------------------------------------
#  5) Zona mitigada: el cierre del TF medio atraviesa el POI → zona muerta
# ---------------------------------------------------------------------------
title(5, "POI mitigada (cierre del TF medio debajo de la zona) → zona muerta")
H5, M5, L5, smc5, barsM5 = setup()
smc5.maintain(1.0862, 1.0840)                  # cierre M15 debajo del POI (1.0855)
assert all(not z["Active"] for z in smc5.zones)
for b in M3_CHOCH:
    c, bo = L5.on_close(b)
    if c or bo:
        smc5.on_low_break(c or bo, c != 0, L5.LastHigh, L5.LastLow)
smc5.process_trigger(1.0874)
assert not smc5.wait_buy and not smc5.vpend_buy
print("   RESULTADO: sin entrada (correcto)")

# ---------------------------------------------------------------------------
#  6) Invalidación: cierre del TF bajo rompe el ORIGEN del tramo → cancelada
# ---------------------------------------------------------------------------
title(6, "Cierre del TF de gatillo rompe el origen del tramo → entrada cancelada")
H6, M6, L6, smc6, barsM6 = setup()
smc6.maintain(1.0862, barsM6[1][3])
for b in M3_CHOCH:
    c, bo = L6.on_close(b)
    if c or bo:
        smc6.on_low_break(c or bo, c != 0, L6.LastHigh, L6.LastLow)
smc6.process_trigger(1.0874)
smc6.try_place(1.0874)
assert smc6.vpend_buy
smc6.check_invalid(1.0849)                     # por debajo del origen (1.0850)
assert not smc6.vpend_buy and smc6.entry_buy == 0.0
print("   RESULTADO: sin entrada (correcto)")

# ---------------------------------------------------------------------------
#  7) Modo de entrada: 50% de la ZONA POI (en vez del 50% del tramo)
# ---------------------------------------------------------------------------
title(7, "Modo de entrada: 50% de la ZONA POI")
H7, M7, L7, smc7, barsM7 = setup(entry_mode=ENTRY_ZONE50)
smc7.maintain(1.0862, barsM7[1][3])
for b in M3_CHOCH:
    c, bo = L7.on_close(b)
    if c or bo:
        smc7.on_low_break(c or bo, c != 0, L7.LastHigh, L7.LastLow)
smc7.process_trigger(1.0874)
z = smc7.zones[0]
esperado = (z["Top"] + z["Bottom"]) * 0.5
assert abs(smc7.entry_buy - esperado) < 1e-9, (smc7.entry_buy, esperado)
print("   RESULTADO: entrada en el 50%% de la zona = %.5f" % esperado)

print("\nTodos los escenarios de la Estrategia 3 (SMC multi-temporal) pasan.")
