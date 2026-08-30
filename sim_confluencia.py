# Simulación en Python del motor de líneas (SE) y de la máquina de estados
# de la ESTRATEGIA 1 (Confluencia H1 + M3) tal como están en el MQL5.

BIAS_UNDEF, BIAS_BULL, BIAS_BEAR = 0, 1, -1

class SE:  # StructureEngine (port de SE_* en MQL5)
    def __init__(self, name):
        self.name=name; self.valid=False
        self.L1=self.L2=self.L3=self.L4=self.EQ=0.0
        self.L3L4_Active=False; self.PendingBreakDir=0
        self.Bias=BIAS_UNDEF
        self.history=[]  # velas cerradas [(O,H,L,C)]

    def init(self, bars):
        self.history=bars
        self.L1=max(b[1] for b in bars); self.L2=min(b[2] for b in bars)
        c=bars[-1]
        self.Bias=BIAS_BULL if c[3]>c[0] else (BIAS_BEAR if c[3]<c[0] else BIAS_UNDEF)
        self.update_eq(); self.valid=True

    def update_eq(self): self.EQ=self.L2+(self.L1-self.L2)*0.5

    def on_close(self, bar):
        """Procesa la vela cerrada (igual que SE_OnClose). Devuelve (choch,trig)."""
        O,H,L,C=bar; choch=0; trig=0
        green=C>O; red=C<O
        if self.Bias==BIAS_UNDEF:
            if green: self.Bias=BIAS_BULL
            if red:   self.Bias=BIAS_BEAR
            return choch,trig
        if self.L3L4_Active:
            if H>self.L3: self.L3=H
            if L<self.L4: self.L4=L
            trig=self.check_break_and_commit(O,C)
            return choch,trig
        if self.Bias==BIAS_BULL and H>self.L1: self.L1=H; self.update_eq()
        elif self.Bias==BIAS_BEAR and L<self.L2: self.L2=L; self.update_eq()
        if self.Bias==BIAS_BULL and red:
            self.L3L4_Active=True; self.L3=self.L1; self.L4=L
            trig=self.check_break_and_commit(O,C)
        elif self.Bias==BIAS_BEAR and green:
            self.L3L4_Active=True; self.L3=H; self.L4=self.L2
            trig=self.check_break_and_commit(O,C)
        return choch,trig

    def break_dir(self,O,C):
        if not self.L3L4_Active: return 0
        up=self.L3>self.L1; dn=self.L4<self.L2
        if not up and not dn: return 0
        if up and dn: return self.PendingBreakDir if self.PendingBreakDir else (1 if C>O else -1)
        return 1 if up else -1

    def commit(self,dirn):
        if dirn==0 or not self.L3L4_Active: return 0
        old=self.Bias; new=BIAS_BULL if dirn>0 else BIAS_BEAR
        self.L1,self.L2=self.L3,self.L4
        if self.L1<self.L2: self.L1,self.L2=self.L2,self.L1
        self.Bias=new; self.update_eq()
        self.L3=self.L4=0.0; self.L3L4_Active=False; self.PendingBreakDir=0
        return dirn if (old!=BIAS_UNDEF and old!=new) else 0

    def check_break_and_commit(self,O,C):
        d=self.break_dir(O,C)
        return self.commit(d) if d else 0


class Confluencia:  # máquina de estados (port de las funciones Confluencia_*)
    def __init__(self, h1, m3, log):
        self.h1=h1; self.m3=m3; self.log=log
        self.armedBuy=False; self.armBuyTime=-1
        self.armedSell=False; self.armSellTime=-1
        self.waitBuy=False; self.waitSell=False
        self.entryBuy=0.0; self.entrySell=0.0
        self.vpendBuy=False; self.vpendBuyPrice=0.0
        self.vpendSell=False; self.vpendSellPrice=0.0
        self.chochDir=0; self.chochTime=-1
        self.orders=[]          # limits colocadas (dir, price)
        self.position=None      # (dir, open)
        self.closed=[]          # resultados

    # --- toque de zona (cada tick) ---
    def arming(self, bid, t):
        eq=self.h1.EQ
        if bid<=eq and not self.armedBuy:
            self.armedBuy=True; self.armBuyTime=t
            self.log(f"t{t}: ZONA COMPRA tocada (50%={eq:.2f}) -> búsqueda compra ACTIVA")
        if bid>=eq and not self.armedSell:
            self.armedSell=True; self.armSellTime=t
            self.log(f"t{t}: ZONA VENTA tocada (50%={eq:.2f}) -> búsqueda venta ACTIVA")

    # --- CHoCH M3 (evento) ---
    def process_choch(self, t):
        d=self.chochDir
        if d==0: return
        self.chochDir=0; ct=self.chochTime
        if d>0: self.waitSell=False
        if d<0: self.waitBuy=False
        if d>0 and self.h1.Bias==BIAS_BULL and self.armedBuy and ct>=self.armBuyTime:
            self.waitBuy=True; self.log(f"t{t}: CHoCH M3 bajista->alcista OK -> espera cruce 50% M3 (compra)")
        elif d<0 and self.h1.Bias==BIAS_BEAR and self.armedSell and ct>=self.armSellTime:
            self.waitSell=True; self.log(f"t{t}: CHoCH M3 alcista->bajista OK -> espera cruce 50% M3 (venta)")
        else:
            self.log(f"t{t}: CHoCH M3 dir={d} IGNORADO (bias H1={'BULL' if self.h1.Bias>0 else 'BEAR'}, armedB={self.armedBuy}, armedS={self.armedSell})")

    # --- cruce del 50% M3 y colocación ---
    def try_place(self, bid, t):
        mid=self.m3.EQ
        if self.waitBuy and self.position is None and bid>mid:
            self.entryBuy=mid
            self.vpendBuy=True; self.vpendBuyPrice=mid
            self.waitBuy=False
            self.log(f"t{t}: 50% M3 cruzado al alza -> BUY LIMIT congelada @ {mid:.2f}")
        if self.waitSell and self.position is None and bid<mid:
            self.entrySell=mid
            self.vpendSell=True; self.vpendSellPrice=mid
            self.waitSell=False
            self.log(f"t{t}: 50% M3 cruzado a la baja -> SELL LIMIT congelada @ {mid:.2f}")

    # --- fills de limits virtuales ---
    def check_fills(self, bid, ask, t):
        if self.position is not None: return
        if self.vpendBuy and ask<=self.vpendBuyPrice:
            self.position=(+1,self.vpendBuyPrice)
            self.log(f"t{t}: vBUY LIMIT ejecutada @ {self.vpendBuyPrice:.2f} -> posición abierta, resto de limits fuera")
            self.vpendBuy=self.vpendSell=False
        elif self.vpendSell and bid>=self.vpendSellPrice:
            self.position=(-1,self.vpendSellPrice)
            self.log(f"t{t}: vSELL LIMIT ejecutada @ {self.vpendSellPrice:.2f} -> posición abierta, resto de limits fuera")
            self.vpendBuy=self.vpendSell=False

    # --- cierre de trade (SL/TP) ---
    def on_trade_closed(self, bid, t):
        self.waitBuy=self.waitSell=False
        self.entryBuy=self.entrySell=0.0
        eq=self.h1.EQ
        if bid>eq and self.armedBuy:
            self.armedBuy=False; self.log(f"t{t}: fuera de zona COMPRA -> búsqueda compra desactivada")
        if bid<eq and self.armedSell:
            self.armedSell=False; self.log(f"t{t}: fuera de zona VENTA -> búsqueda venta desactivada")

    # --- con posición abierta no avanza nada ---
    def gate_position(self):
        if self.position is not None:
            self.waitBuy=self.waitSell=False; self.chochDir=0
            return True
        return False


def run_scenario(title, h1_bars, m3_bars, ticks, sl_tp, log=print):
    print(f"\n===== {title} =====")
    h1=SE('H1'); m3=SE('M3')
    h1.init(h1_bars); m3.init(m3_bars)
    cf=Confluencia(h1,m3,log)
    sl_dist,tp_dist=sl_tp
    for t,(bid,m3bar,h1bar) in enumerate(ticks):
        # posición virtual: SL/TP
        if cf.position is not None:
            d,op=cf.position
            hit = (bid<=op-sl_dist) if d>0 else (bid>=op+sl_dist)
            hit2= (bid>=op+tp_dist) if d>0 else (bid<=op-tp_dist)
            if hit or hit2:
                win=bool(hit2 and not hit)
                cf.closed.append(win)
                cf.log(f"t{t}: posición {'TP (ganancia)' if win else 'SL (pérdida)'} cerrada")
                cf.position=None
                cf.on_trade_closed(bid,t)
        # velas cerradas
        if h1bar is not None:
            _,c=h1.on_close(h1bar)   # 2º elemento = flag CHoCH en este port
            if c!=0:
                print(f"t{t}: H1 CHoCH -> {'ALCISTA' if c>0 else 'BAJISTA'} (reset zonas)")
                cf.armedBuy=cf.armedSell=False; cf.waitBuy=cf.waitSell=False
                cf.entryBuy=cf.entrySell=0.0; cf.vpendBuy=cf.vpendSell=False
                cf.armBuyTime=cf.armSellTime=-1
        if m3bar is not None:
            _,choch=m3.on_close(m3bar)   # 2º elemento = flag CHoCH en este port
            if choch!=0:
                cf.chochDir=choch; cf.chochTime=t
        cf.arming(bid,t)
        if not cf.gate_position():
            cf.process_choch(t)
            cf.try_place(bid,t)
            cf.check_fills(bid,bid+0.02,t)
    print(f"RESULTADO: trades cerrados={[( 'TP' if w else 'SL') for w in cf.closed]}, "
          f"armedB={cf.armedBuy}, armedS={cf.armedSell}, límites activas B={cf.vpendBuy}@{cf.vpendBuyPrice:.2f} S={cf.vpendSell}@{cf.vpendSellPrice:.2f}")
    return cf


# Datos base
H1_BARS=[(100+i*0.1, 101+i*0.1, 99+i*0.1, 100.5+i*0.1) for i in range(8)]  # tendencia alcista
M3_BARS=[(100+i*0.05, 100.4+i*0.05, 99.6+i*0.05, 100.2+i*0.05) for i in range(8)]
#   M3 init: L1=100.75, L2=99.60, Bias BULL. EQ=100.175

def bar(O,H,L,C): return (O,H,L,C)

# ESCENARIO 1: compra completa (toque zona -> CHoCH -> cruce -> fill -> TP)
# t1 vela bajista: activa reacción y ROMPE L4<L2 -> CHoCH bajista (rango nuevo)
# t3 vela alcista: su máximo ROMPE L3>L1 -> CHoCH alcista (el que buscamos)
ticks=[
    (99.0, None, None),                                   # t0: precio en zona compra H1 (<=50%=100.35)
    (98.6, bar(100,100.1,98.5,98.6), None),               # t1: M3 bajista -> L4=98.5<L2 -> CHoCH bear
    (98.4, bar(98.6,98.7,97.9,98.0), None),               # t2: continuación bajista (L2=97.9)
    (98.3, bar(98.0,101.0,98.0,100.9), None),             # t3: M3 alcista, high 101.0>L1 -> CHoCH bull
    (101.2, None, None),                                  # t4: bid > 50% M3 (99.45) -> BUY LIMIT @99.45
    (99.4, None, None),                                   # t5: retrocede al nivel -> FILL (ask<=99.45)
    (99.6, None, None),
    (102.6, None, None),                                  # t6: TP (op 99.45 + 3)
]
run_scenario("ESCENARIO 1: compra completa hasta TP", H1_BARS, M3_BARS, ticks, sl_tp=(2.0,3.0))

# ESCENARIO 2: pérdida y sigue en zona -> nueva búsqueda con CHoCH nuevo
ticks=[
    (99.0, None, None),
    (98.6, bar(100,100.1,98.5,98.6), None),
    (98.4, bar(98.6,98.7,97.9,98.0), None),
    (98.3, bar(98.0,101.0,98.0,100.9), None),
    (101.2, None, None),
    (99.4, None, None),                                   # fill @99.45
    (98.0, None, None),                                   # cae
    (97.4, None, None),                                   # SL (op-2) — sigue en zona compra H1
    (99.0, None, None),                                   # vuelve a zona (armed persiste)
    (98.9, bar(98.8,98.9,97.8,97.9), None),               # reacción bajista: L4=97.8<L2 -> CHoCH bear
    (98.2, bar(97.9,101.5,97.8,101.4), None),             # CHoCH bull (high 101.5 > L1 nuevo)
    (101.7, None, None),                                  # cruce 50% -> nueva BUY LIMIT
    (99.3, None, None),                                   # fill
    (102.5, None, None),                                  # TP
]
run_scenario("ESCENARIO 2: SL y re-entrada en zona", H1_BARS, M3_BARS, ticks, sl_tp=(2.0,3.0))

# ESCENARIO 3: pérdida (buy) mientras otra búsqueda del lado contrario estaba
# armada: al cerrar fuera de la zona de compra, esa búsqueda se desactiva.
ticks=[
    (99.0, None, None),                                   # armedBuy
    (101.0, None, None),                                  # sube por encima del 50% H1 -> armedSell también
    (98.6, bar(100,100.1,98.5,98.6), None),
    (98.4, bar(98.6,98.7,97.9,98.0), None),
    (98.3, bar(98.0,101.0,98.0,100.9), None),
    (101.2, None, None),                                  # cruce -> BUY LIMIT @99.45
    (99.4, None, None),                                   # fill
    (97.4, None, None),                                   # SL — price 97.4 sigue en zona compra (<=100.35)
    (102.0, None, None),                                  # ahora sube a zona venta (fuera de zona compra)
    (102.0, bar(101.6,101.7,100.8,100.9), None),          # reacción bajista M3 en zona alta
    (101.0, bar(100.9,102.0,100.8,101.9), None),          # CHoCH bear (low rompe L2) -> espera cruce para VENTA
    (100.2, None, None),                                  # cruce a la baja -> SELL LIMIT @50% M3
    (100.6, None, None),                                  # rebote -> fill sell @nivel
    (103.2, None, None),                                  # SL del sell (op+2) — en zona venta: armedSell persiste
]
run_scenario("ESCENARIO 3: venta tras SL, cruce a la baja", H1_BARS, M3_BARS, ticks, sl_tp=(2.0,3.0))

# ESCENARIO 4: CHoCH sin toque previo de zona (otro símbolo/estado) -> ignorado
ticks=[
    (101.0, None, None),                                  # arranca en zona venta (armedSell), NO en compra
    (101.0, bar(100,100.1,98.5,98.6), None),
    (98.4, bar(98.6,98.7,97.9,98.0), None),
    (98.3, bar(98.0,101.0,98.0,100.9), None),             # CHoCH bull con H1 BULL pero zona compra NO tocada
    (101.2, None, None),
]
run_scenario("ESCENARIO 4: CHoCH sin toque de zona de compra -> ignorado", H1_BARS, M3_BARS, ticks, sl_tp=(2.0,3.0))
