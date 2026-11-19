'use strict';
/* =====================================================================
   SMC50-WEB · engine.js — Motor de estructura L1-L4 + BOS/CHoCH
   ---------------------------------------------------------------------
   Port 1:1 del motor v8.56 del EA ("trabajador multichart.mq5") y de
   sim_bos_choch.py. Sin dependencias: funciona en navegador y en Node.
   ---------------------------------------------------------------------
   · L1 = techo del rango, L2 = suelo. EQ = 50% = L2+(L1-L2)*0.5.
   · L1/L2 solo se mueven al CIERRE; L3/L4 al tick tras vela contraria.
   · CHoCH = rompimiento que CAMBIA el bias (commit L3>L1 / L4<L2).
   · BOS   = rompimiento de CONTINUACION (mismo bias): cierre mas alla
             de RefLevel, o commit en la direccion del bias.
   · Cada rompimiento deja su TRAMO en LastHigh/LastLow; su 50% es el
     nivel de entrada del EA.
   ===================================================================== */

var SMC_BIAS_UNDEF = 0;
var SMC_BIAS_BULL = 1;
var SMC_BIAS_BEAR = -1;

var SMC_PHASE_CONT = 0;
var SMC_PHASE_REACTION = 1;
var SMC_PHASE_TRIGGERED = 2;

function SMC50Engine() {
  this.reset();
}

SMC50Engine.prototype.reset = function () {
  this.L1 = 0; this.L2 = 0; this.L3 = 0; this.L4 = 0; this.EQ = 0;
  this.L3L4 = false;
  this.Pending = 0;
  this.RefLevel = 0;
  this.BosDone = false;
  this.BosLegHigh = 0;
  this.BosLegLow = 0;
  this.LastHigh = 0;
  this.LastLow = 0;
  this.Bias = SMC_BIAS_UNDEF;
  this.Phase = SMC_PHASE_CONT;
  this.Valid = false;
};

SMC50Engine.prototype.updateEQ = function () {
  this.EQ = this.L2 + (this.L1 - this.L2) * 0.5;
};

SMC50Engine.prototype.clearReaction = function () {
  this.L3 = 0; this.L4 = 0;
  this.L3L4 = false;
  this.Pending = 0;
  this.RefLevel = 0;
  this.BosDone = false;
  this.BosLegHigh = 0;
  this.BosLegLow = 0;
  this.Phase = SMC_PHASE_CONT;
};

/* Consolida el rompimiento. Devuelve choch (dir si cambia el bias). */
SMC50Engine.prototype.commit = function (dir) {
  if (dir === 0 || !this.L3L4) return 0;
  var old = this.Bias;
  var nw = dir > 0 ? SMC_BIAS_BULL : SMC_BIAS_BEAR;

  /* TRAMO del rompimiento = rango de reaccion/impulso (L3..L4) */
  this.LastHigh = Math.max(this.L3, this.L4);
  this.LastLow = Math.min(this.L3, this.L4);

  this.L1 = this.L3;
  this.L2 = this.L4;
  if (this.L1 < this.L2) {
    var t = this.L1; this.L1 = this.L2; this.L2 = t;
  }
  this.Bias = nw;
  this.updateEQ();
  this.clearReaction();
  return (old !== SMC_BIAS_UNDEF && old !== nw) ? dir : 0;
};

SMC50Engine.prototype.breakDir = function (O, C) {
  if (!this.Valid || !this.L3L4) return 0;
  var up = this.L3 > this.L1;
  var dn = this.L4 < this.L2;
  if (!up && !dn) return 0;
  if (up && dn) {
    if (this.Pending !== 0) return this.Pending;
    if (C > O) return 1;
    if (C < O) return -1;
    return this.Bias === SMC_BIAS_BEAR ? 1 : -1;
  }
  return up ? 1 : -1;
};

SMC50Engine.prototype.checkBreakAndCommit = function (O, C) {
  var d = this.breakDir(O, C);
  if (d === 0) return { trig: 0, choch: 0 };
  var ch = this.commit(d);
  return { trig: d, choch: ch };
};

/* BOS por cierre mas alla del nivel de referencia (continuacion). */
SMC50Engine.prototype.continuation = function (C) {
  if (!this.Valid || !this.L3L4) return 0;
  if (this.BosDone) return 0;
  if (!(this.RefLevel > 0)) return 0;
  var dir = 0;
  if (this.Bias === SMC_BIAS_BULL && C > this.RefLevel) dir = 1;
  if (this.Bias === SMC_BIAS_BEAR && C < this.RefLevel) dir = -1;
  if (dir === 0) return 0;

  this.LastHigh = Math.max(this.BosLegHigh, this.BosLegLow);
  this.LastLow = Math.min(this.BosLegHigh, this.BosLegLow);
  if (!(this.LastHigh > this.LastLow)) {
    this.LastHigh = Math.max(this.L3, this.L4);
    this.LastLow = Math.min(this.L3, this.L4);
  }
  if (!(this.LastHigh > this.LastLow)) return 0;

  if (dir > 0 && this.LastHigh > this.L1) { this.L1 = this.LastHigh; this.updateEQ(); }
  if (dir < 0 && this.LastLow < this.L2) { this.L2 = this.LastLow; this.updateEQ(); }
  this.BosDone = true;
  return dir;
};

/* Tick: solo L3/L4 + tramo BOS + L1/L2 del lado del bias + pendiente. */
SMC50Engine.prototype.onTick = function (price) {
  if (!this.Valid || !this.L3L4) return;
  if (!(price > 0)) return;
  if (price > this.L3) this.L3 = price;
  if (price < this.L4) this.L4 = price;
  if (price > this.BosLegHigh) this.BosLegHigh = price;
  if (price < this.BosLegLow) this.BosLegLow = price;
  if (this.Bias === SMC_BIAS_BULL && price > this.L1) {
    this.L1 = price; this.updateEQ();
  } else if (this.Bias === SMC_BIAS_BEAR && price < this.L2) {
    this.L2 = price; this.updateEQ();
  }
  if (price > this.L1) { this.Phase = SMC_PHASE_TRIGGERED; this.Pending = 1; }
  if (price < this.L2) { this.Phase = SMC_PHASE_TRIGGERED; this.Pending = -1; }
};

/* Vela cerrada {o,h,l,c}. Devuelve {choch, bos, trig}. */
SMC50Engine.prototype.onClose = function (b) {
  var O = b.o, H = b.h, L = b.l, C = b.c;
  var choch = 0, bos = 0, trig = 0;
  if (!this.Valid) return { choch: 0, bos: 0, trig: 0 };
  if (!(O > 0 && C > 0 && H > 0 && L > 0)) return { choch: 0, bos: 0, trig: 0 };

  var green = C > O, red = C < O;
  if (this.Bias === SMC_BIAS_UNDEF) {
    if (green) this.Bias = SMC_BIAS_BULL;
    if (red) this.Bias = SMC_BIAS_BEAR;
    return { choch: 0, bos: 0, trig: 0 };
  }

  if (this.L3L4) {
    if (H > this.L3) this.L3 = H;
    if (L < this.L4) this.L4 = L;
    if (H > this.BosLegHigh) this.BosLegHigh = H;
    if (L < this.BosLegLow) this.BosLegLow = L;

    /* Vela CONTRARIA re-arma el BOS; si ya hubo BOS abre tramo nuevo */
    var contrary = (this.Bias === SMC_BIAS_BULL && red) ||
                   (this.Bias === SMC_BIAS_BEAR && green);
    if (contrary) {
      if (this.BosDone) {
        this.BosLegHigh = H;
        this.BosLegLow = L;
      }
      this.RefLevel = (this.Bias === SMC_BIAS_BULL ? this.L1 : this.L2);
      this.BosDone = false;
    }

    /* El CHoCH manda primero */
    var blh = this.BosLegHigh, bll = this.BosLegLow;
    var r = this.checkBreakAndCommit(O, C);
    trig = r.trig; choch = r.choch;
    if (trig !== 0) {
      if (choch === 0) {           /* misma direccion = BOS por commit */
        if (blh > bll) {
          this.LastHigh = blh;
          this.LastLow = bll;
        }
        bos = trig;
      }
      return { choch: choch, bos: bos, trig: trig };
    }
    bos = this.continuation(C);
    if (bos === 0) this.Phase = SMC_PHASE_REACTION;
    return { choch: choch, bos: bos, trig: trig };
  }

  /* Continuacion sin reaccion: L1/L2 al CIERRE */
  if (this.Bias === SMC_BIAS_BULL) {
    if (H > this.L1) { this.L1 = H; this.updateEQ(); }
  } else if (this.Bias === SMC_BIAS_BEAR) {
    if (L < this.L2) { this.L2 = L; this.updateEQ(); }
  }

  /* Activacion de L3/L4 solo por cierre contrario */
  if (this.Bias === SMC_BIAS_BULL && red) {
    this.L3L4 = true;
    this.L3 = this.L1;
    this.L4 = L;
    this.RefLevel = this.L1;
    this.BosDone = false;
    this.BosLegHigh = H;
    this.BosLegLow = L;
    this.Phase = SMC_PHASE_REACTION;
    var r2 = this.checkBreakAndCommit(O, C);
    trig = r2.trig; choch = r2.choch;
  } else if (this.Bias === SMC_BIAS_BEAR && green) {
    this.L3L4 = true;
    this.L3 = H;
    this.L4 = this.L2;
    this.RefLevel = this.L2;
    this.BosDone = false;
    this.BosLegHigh = H;
    this.BosLegLow = L;
    this.Phase = SMC_PHASE_REACTION;
    var r3 = this.checkBreakAndCommit(O, C);
    trig = r3.trig; choch = r3.choch;
  }
  return { choch: choch, bos: bos, trig: trig };
};

/* Corre el motor sobre velas cerradas ascendentes [{t,o,h,l,c}].
   opts: {maxMarks, livePrice}. Devuelve {engine, events}. */
function smc50Run(barsAsc, opts) {
  opts = opts || {};
  var maxMarks = Math.max(1, Math.min(200, opts.maxMarks || 30));
  var eng = new SMC50Engine();
  var events = [];
  var n = barsAsc ? barsAsc.length : 0;

  if (n >= 1) {
    var f = barsAsc[0];
    eng.L1 = f.h;
    eng.L2 = f.l;
    if (f.c > f.o) eng.Bias = SMC_BIAS_BULL;
    else if (f.c < f.o) eng.Bias = SMC_BIAS_BEAR;
    eng.updateEQ();
    eng.Valid = true;
  }
  for (var i = 1; i < n; i++) {
    var b = barsAsc[i];
    var r = eng.onClose(b);
    var dir = r.choch !== 0 ? r.choch : r.bos;
    if (dir !== 0) {
      var legH = eng.LastHigh, legL = eng.LastLow;
      if (legH > legL && legL > 0 && eng.EQ > 0) {
        events.push({
          t: b.t, dir: dir, isChoch: r.choch !== 0,
          eq50: eng.EQ, legH: legH, legL: legL,
          leg50: (legH + legL) / 2, rc: b.c
        });
        while (events.length > maxMarks) events.shift();
      }
    }
  }
  if (opts.livePrice > 0) eng.onTick(opts.livePrice);
  return { engine: eng, events: events };
}

/* Etiquetas de ayuda para la interfaz. */
function smcBiasText(b) {
  if (b === SMC_BIAS_BULL) return 'ALCISTA';
  if (b === SMC_BIAS_BEAR) return 'BAJISTA';
  return '—';
}

function smcPhaseText(p) {
  if (p === SMC_PHASE_REACTION) return 'REACCION';
  if (p === SMC_PHASE_TRIGGERED) return 'RUPTURA';
  return 'CONT.';
}
