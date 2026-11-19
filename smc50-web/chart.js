'use strict';
/* =====================================================================
   SMC50-WEB · chart.js — Grafico de velas con lineas L1-L4, zonas 50%
   y etiquetas BOS/CHoCH ancladas al 50%. Canvas puro, sin dependencias.
   ===================================================================== */

var SMC_C = {
  bg: '#0b0e14',
  grid: 'rgba(120,140,170,0.12)',
  gridTxt: '#7d8aa0',
  bull: '#26a69a',
  bear: '#ef5350',
  l1l2: '#1e90ff',
  eq: '#ffd700',
  l3: '#ff4dff',
  l4: '#ff3b3b',
  mMain: '#ff8c1a',
  mEq: '#ffd700',
  last: '#9aa4b2',
  disc: 'rgba(0,160,90,0.10)',
  prem: 'rgba(220,60,60,0.10)',
  cross: 'rgba(160,180,210,0.55)'
};

function smcEventColor(e) {
  if (e.isChoch) return e.dir > 0 ? '#1e90ff' : '#ff8c1a';
  return e.dir > 0 ? '#32cd32' : '#ff6347';
}

function SMC50Chart(canvas, opts) {
  this.cv = canvas;
  this.ctx = canvas.getContext('2d');
  opts = opts || {};
  this.axisW = opts.axisW || 76;
  this.axisH = opts.axisH || 22;
  this.padL = opts.padL || 6;
  this.padT = opts.padT || 10;
  this.legendEl = opts.legendEl || null;

  this.bars = [];
  this.eng = null;
  this.events = [];
  this.mEng = null;
  this.mEvents = [];
  this.digits = 5;
  this.label = '';
  this.sublabel = '';
  this.showZones = true;
  this.showMother = true;
  this.anchorAt50 = true;
  this.legBars = 8;

  this.view = { count: 120, end: 0 };
  this.follow = true;
  this.mouse = { x: 0, y: 0, inside: false };
  this._drag = null;
  this.geo = null;

  this._bind();
  this.resize();
}

SMC50Chart.prototype._bind = function () {
  var self = this;
  this.cv.addEventListener('mousemove', function (e) {
    var r = self.cv.getBoundingClientRect();
    self.mouse.x = e.clientX - r.left;
    self.mouse.y = e.clientY - r.top;
    self.mouse.inside = true;
    self.render();
  });
  this.cv.addEventListener('mouseleave', function () {
    self.mouse.inside = false;
    self._drag = null;
    self.render();
  });
  this.cv.addEventListener('mousedown', function (e) {
    var r = self.cv.getBoundingClientRect();
    self._drag = { x: e.clientX - r.left, end: self.view.end };
  });
  window.addEventListener('mouseup', function () { self._drag = null; });
  this.cv.addEventListener('mousemove', function (e) {
    if (!self._drag || !self.geo) return;
    var r = self.cv.getBoundingClientRect();
    var dx = (e.clientX - r.left) - self._drag.x;
    self.view.end = self._drag.end - dx / self.geo.step;
    self.follow = false;
    self.render();
  });
  this.cv.addEventListener('wheel', function (e) {
    e.preventDefault();
    if (!self.bars.length) return;
    var r = self.cv.getBoundingClientRect();
    var mx = e.clientX - r.left;
    var f = e.deltaY > 0 ? 1.15 : 1 / 1.15;
    self._zoomAt(mx, f);
  }, { passive: false });
  this.cv.addEventListener('dblclick', function () { self.resetView(); });
  if (window.ResizeObserver) {
    var ro = new ResizeObserver(function () { self.resize(); });
    ro.observe(this.cv.parentElement || this.cv);
  } else {
    window.addEventListener('resize', function () { self.resize(); });
  }
};

SMC50Chart.prototype.resize = function () {
  var box = this.cv.parentElement || this.cv;
  var w = Math.max(200, box.clientWidth || 600);
  var h = Math.max(220, box.clientHeight || 420);
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  this.cv.width = Math.round(w * dpr);
  this.cv.height = Math.round(h * dpr);
  this.cv.style.width = w + 'px';
  this.cv.style.height = h + 'px';
  this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  this.W = w;
  this.H = h;
  this.render();
};

SMC50Chart.prototype.setData = function (d) {
  this.bars = d.bars || [];
  this.eng = d.engine || null;
  this.events = d.events || [];
  this.mEng = d.motherEngine || null;
  this.mEvents = d.motherEvents || [];
  if (d.digits !== undefined) this.digits = d.digits;
  if (d.label !== undefined) this.label = d.label;
  if (d.sublabel !== undefined) this.sublabel = d.sublabel;
  if (d.showZones !== undefined) this.showZones = d.showZones;
  if (d.showMother !== undefined) this.showMother = d.showMother;
  if (d.anchorAt50 !== undefined) this.anchorAt50 = d.anchorAt50;
  if (d.legBars) this.legBars = d.legBars;
  var n = this.bars.length;
  if (this.follow) {
    this.view.end = n - 1 + 2;
  } else {
    this.view.end = Math.min(this.view.end, n - 1 + this.view.count);
  }
  this.view.count = Math.min(this.view.count, Math.max(30, n + 10));
  this.render();
};

SMC50Chart.prototype.resetView = function () {
  this.follow = true;
  this.view.count = 120;
  this.view.end = this.bars.length - 1 + 2;
  this.render();
};

SMC50Chart.prototype.zoom = function (f) {
  if (!this.bars.length) return;
  var cx = this.padL + (this.W - this.axisW - this.padL) / 2;
  this._zoomAt(cx, f);
};

SMC50Chart.prototype._zoomAt = function (mx, f) {
  var n = this.bars.length;
  var plotW = this.W - this.axisW - this.padL;
  var oldCount = this.view.count;
  var oldStep = plotW / oldCount;
  var leftIdx = this.view.end - oldCount;
  var idxAt = leftIdx + (mx - this.padL) / oldStep;
  var nc = Math.max(15, Math.min(n + 10, Math.round(oldCount * f)));
  var nStep = plotW / nc;
  var nLeft = idxAt - (mx - this.padL) / nStep;
  this.view.count = nc;
  this.view.end = nLeft + nc;
  this.follow = false;
  this.render();
};

SMC50Chart.prototype._fmtPx = function (p) {
  return Number(p).toFixed(this.digits);
};

SMC50Chart.prototype._fmtTime = function (ms) {
  var d = new Date(ms);
  function z(x) { return (x < 10 ? '0' : '') + x; }
  return z(d.getHours()) + ':' + z(d.getMinutes());
};

SMC50Chart.prototype._fmtDay = function (ms) {
  var d = new Date(ms);
  function z(x) { return (x < 10 ? '0' : '') + x; }
  return z(d.getDate()) + '/' + z(d.getMonth() + 1);
};

SMC50Chart.prototype._rr = function (x, y, w, h, r) {
  var c = this.ctx;
  c.beginPath();
  c.moveTo(x + r, y);
  c.arcTo(x + w, y, x + w, y + h, r);
  c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r);
  c.arcTo(x, y, x + w, y, r);
  c.closePath();
};

SMC50Chart.prototype._niceStep = function (range, maxTicks) {
  var raw = range / Math.max(1, maxTicks);
  var mag = Math.pow(10, Math.floor(Math.log10(raw)));
  var n = raw / mag;
  var m = n >= 5 ? 10 : (n >= 2 ? 5 : (n >= 1 ? 2 : 1));
  return m * mag;
};

SMC50Chart.prototype.render = function () {
  var c = this.ctx;
  var W = this.W || 600, H = this.H || 420;
  c.fillStyle = SMC_C.bg;
  c.fillRect(0, 0, W, H);

  var n = this.bars.length;
  if (!n) {
    c.fillStyle = SMC_C.gridTxt;
    c.font = '13px Consolas, monospace';
    c.textAlign = 'center';
    c.fillText(this.label || 'Sin datos — pulsa CONECTAR', W / 2, H / 2);
    return;
  }

  var plotW = W - this.axisW - this.padL;
  var plotH = H - this.axisH - this.padT;
  var step = plotW / this.view.count;
  var leftIdx = this.view.end - this.view.count;
  var i0 = Math.max(0, Math.floor(leftIdx));
  var i1 = Math.min(n - 1, Math.ceil(this.view.end));

  /* Rango de precio visible */
  var lo = Infinity, hi = -Infinity, i, b;
  for (i = i0; i <= i1; i++) {
    b = this.bars[i];
    if (b.l < lo) lo = b.l;
    if (b.h > hi) hi = b.h;
  }
  function eat(p) { if (p > 0) { if (p < lo) lo = p; if (p > hi) hi = p; } }
  var e = this.eng;
  if (e && e.Valid) {
    eat(e.L1); eat(e.L2); eat(e.EQ);
    if (e.L3L4) { eat(e.L3); eat(e.L4); }
  }
  if (this.showMother && this.mEng && this.mEng.Valid) {
    eat(this.mEng.L1); eat(this.mEng.L2); eat(this.mEng.EQ);
  }
  var ev, ax;
  for (i = 0; i < this.events.length; i++) {
    ev = this.events[i];
    ax = this.anchorAt50 ? ev.eq50 : ev.leg50;
    eat(ax);
  }
  if (!(hi > lo)) { hi = lo + 1; }
  var pad = (hi - lo) * 0.08;
  lo -= pad; hi += pad;

  function X(idx) { return this.padL + (idx - leftIdx) * step; }
  X = X.bind(this);
  function Y(p) { return this.padT + (hi - p) / (hi - lo) * plotH; }
  Y = Y.bind(this);
  this.geo = { step: step, leftIdx: leftIdx, X: X, Y: Y, plotW: plotW, plotH: plotH };

  /* Rejilla horizontal + eje de precio */
  c.font = '11px Consolas, monospace';
  c.textAlign = 'left';
  c.textBaseline = 'middle';
  var pStep = this._niceStep(hi - lo, Math.max(3, Math.floor(plotH / 52)));
  c.lineWidth = 1;
  for (var p = Math.ceil(lo / pStep) * pStep; p < hi; p += pStep) {
    var y = Y(p);
    c.strokeStyle = SMC_C.grid;
    c.beginPath(); c.moveTo(this.padL, y); c.lineTo(this.padL + plotW, y); c.stroke();
    c.fillStyle = SMC_C.gridTxt;
    c.fillText(this._fmtPx(p), this.padL + plotW + 6, y);
  }

  /* Eje de tiempo */
  var steps = [1, 2, 3, 5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 360, 480, 720];
  var tStep = steps[steps.length - 1];
  for (i = 0; i < steps.length; i++) {
    if (steps[i] * step >= 85) { tStep = steps[i]; break; }
  }
  c.textAlign = 'center';
  var prevDay = '';
  for (i = i0; i <= i1; i++) {
    if (i % tStep !== 0) continue;
    var bx = X(i) + step / 2;
    if (bx < this.padL || bx > this.padL + plotW) continue;
    c.strokeStyle = SMC_C.grid;
    c.beginPath(); c.moveTo(bx, this.padT); c.lineTo(bx, this.padT + plotH); c.stroke();
    var day = this._fmtDay(this.bars[i].t);
    var txt = (day !== prevDay ? day + ' ' : '') + this._fmtTime(this.bars[i].t);
    prevDay = day;
    c.fillStyle = SMC_C.gridTxt;
    c.fillText(txt, bx, this.padT + plotH + this.axisH / 2);
  }

  /* Zonas premium / descuento del TF principal */
  if (this.showZones && e && e.Valid && e.L1 > 0 && e.L2 > 0) {
    c.fillStyle = SMC_C.prem;
    c.fillRect(this.padL, Y(e.L1), plotW, Y(e.EQ) - Y(e.L1));
    c.fillStyle = SMC_C.disc;
    c.fillRect(this.padL, Y(e.EQ), plotW, Y(e.L2) - Y(e.EQ));
  }

  /* Velas */
  var cw = Math.max(1, step * 0.65);
  for (i = i0; i <= i1; i++) {
    b = this.bars[i];
    var up = b.c >= b.o;
    c.fillStyle = up ? SMC_C.bull : SMC_C.bear;
    c.strokeStyle = c.fillStyle;
    var cx = X(i) + step / 2;
    c.beginPath(); c.moveTo(cx, Y(b.h)); c.lineTo(cx, Y(b.l)); c.stroke();
    var yO = Y(b.o), yC = Y(b.c);
    var top = Math.min(yO, yC);
    var hh = Math.max(1, Math.abs(yC - yO));
    c.fillRect(cx - cw / 2, top, cw, hh);
  }

  /* Linea corta del 50% del tramo de cada evento */
  var self = this;
  function leg50(evList, colorFn) {
    for (var k = 0; k < evList.length; k++) {
      var m = evList[k];
      var bi = self._barIndex(m.t);
      if (bi < i0 - 20 || bi > i1 + 1) continue;
      var x1 = X(bi), x2 = X(Math.min(bi + self.legBars, n - 1 + 3));
      var y = Y(m.leg50);
      c.strokeStyle = colorFn(m);
      c.setLineDash([3, 3]);
      c.lineWidth = 1;
      c.beginPath(); c.moveTo(x1, y); c.lineTo(x2, y); c.stroke();
      c.setLineDash([]);
    }
  }
  leg50(this.events, smcEventColor);
  if (this.showMother) leg50(this.mEvents, smcEventColor);

  /* Lineas horizontales con etiqueta a la derecha */
  function hline(price, color, dash, width, lbl) {
    if (!(price > 0)) return;
    var y = Y(price);
    if (y < self.padT - 30 || y > self.padT + plotH + 30) return;
    c.strokeStyle = color;
    c.setLineDash(dash || []);
    c.lineWidth = width || 1;
    c.beginPath(); c.moveTo(self.padL, y); c.lineTo(self.padL + plotW, y); c.stroke();
    c.setLineDash([]);
    var t2 = lbl + ' ' + self._fmtPx(price);
    c.font = 'bold 11px Consolas, monospace';
    var tw = c.measureText(t2).width;
    c.fillStyle = 'rgba(0,0,0,0.65)';
    c.fillRect(self.padL + plotW + 2, y - 9, tw + 8, 18);
    c.fillStyle = color;
    c.textAlign = 'left';
    c.fillText(t2, self.padL + plotW + 6, y);
  }

  if (e && e.Valid) {
    hline(e.L1, SMC_C.l1l2, [], 2, 'L1');
    hline(e.L2, SMC_C.l1l2, [], 2, 'L2');
    hline(e.EQ, SMC_C.eq, [2, 3], 1, '50%');
    if (e.L3L4) {
      hline(e.L3, SMC_C.l3, [6, 4], 2, 'L3');
      hline(e.L4, SMC_C.l4, [6, 4], 2, 'L4');
    }
  }
  if (this.showMother && this.mEng && this.mEng.Valid) {
    hline(this.mEng.L1, SMC_C.mMain, [], 1, 'H-L1');
    hline(this.mEng.L2, SMC_C.mMain, [], 1, 'H-L2');
    hline(this.mEng.EQ, SMC_C.mEq, [6, 4], 1, 'H-50%');
  }

  /* Ultimo precio */
  var lastC = this.bars[n - 1].c;
  (function () {
    var y = Y(lastC);
    c.strokeStyle = SMC_C.last;
    c.setLineDash([4, 4]);
    c.lineWidth = 1;
    c.beginPath(); c.moveTo(self.padL, y); c.lineTo(self.padL + plotW, y); c.stroke();
    c.setLineDash([]);
    var t2 = self._fmtPx(lastC);
    c.font = 'bold 11px Consolas, monospace';
    var tw = c.measureText(t2).width;
    c.fillStyle = '#39424f';
    c.fillRect(self.padL + plotW + 2, y - 9, tw + 8, 18);
    c.fillStyle = '#fff';
    c.textAlign = 'left';
    c.fillText(t2, self.padL + plotW + 6, y);
  })();

  /* Etiquetas BOS/CHoCH ancladas al 50% */
  function pill(evList, tfTag) {
    c.font = 'bold 11px Consolas, monospace';
    for (var k = 0; k < evList.length; k++) {
      var m = evList[k];
      var bi = self._barIndex(m.t);
      if (bi < i0 || bi > i1) continue;
      var anchor = self.anchorAt50 ? m.eq50 : m.leg50;
      var y = Y(anchor);
      var txt = '[' + tfTag + '] ' + (m.isChoch ? 'CHoCH' : 'BOS') +
        (m.dir > 0 ? ' ALC ' : ' BAJ ') + self._fmtPx(anchor);
      var tw = c.measureText(txt).width;
      var bx = X(bi) + step / 2;
      var tx = bx + 8;
      if (tx + tw + 12 > self.padL + plotW) tx = bx - 8 - (tw + 12);
      var col = smcEventColor(m);
      c.fillStyle = col;
      c.beginPath(); c.arc(bx, y, 3, 0, Math.PI * 2); c.fill();
      c.strokeStyle = col;
      c.beginPath(); c.moveTo(bx, y); c.lineTo(tx < bx ? tx + tw + 12 : tx, y); c.stroke();
      self._rr(tx, y - 10, tw + 12, 20, 4);
      c.fillStyle = 'rgba(5,8,12,0.88)';
      c.fill();
      c.strokeStyle = col;
      c.lineWidth = 1;
      c.stroke();
      c.fillStyle = col;
      c.textAlign = 'left';
      c.fillText(txt, tx + 6, y);
    }
  }
  pill(this.events, this._tfTag);
  if (this.showMother) pill(this.mEvents, this._mTag);

  /* Crosshair */
  if (this.mouse.inside &&
      this.mouse.x >= this.padL && this.mouse.x <= this.padL + plotW &&
      this.mouse.y >= this.padT && this.mouse.y <= this.padT + plotH) {
    var mx = this.mouse.x, my = this.mouse.y;
    c.strokeStyle = SMC_C.cross;
    c.setLineDash([4, 4]);
    c.beginPath(); c.moveTo(mx, this.padT); c.lineTo(mx, this.padT + plotH); c.stroke();
    c.beginPath(); c.moveTo(this.padL, my); c.lineTo(this.padL + plotW, my); c.stroke();
    c.setLineDash([]);
    var pv = hi - (my - this.padT) / plotH * (hi - lo);
    var tag = this._fmtPx(pv);
    c.font = 'bold 11px Consolas, monospace';
    var tw2 = c.measureText(tag).width;
    c.fillStyle = '#4a5568';
    c.fillRect(this.padL + plotW + 2, my - 9, tw2 + 8, 18);
    c.fillStyle = '#fff';
    c.textAlign = 'left';
    c.fillText(tag, this.padL + plotW + 6, my);
    var hov = Math.round(leftIdx + (mx - this.padL) / step);
    if (hov >= 0 && hov < n && this.legendEl) this._legend(this.bars[hov]);
  } else if (this.legendEl) {
    this._legend(this.bars[n - 1]);
  }

  /* Marca de agua */
  c.font = 'bold 12px Consolas, monospace';
  c.textAlign = 'left';
  c.fillStyle = 'rgba(140,160,190,0.55)';
  c.fillText(this.label, this.padL + 6, this.padT + 12);
  if (this.sublabel) {
    c.font = '11px Consolas, monospace';
    c.fillStyle = 'rgba(140,160,190,0.4)';
    c.fillText(this.sublabel, this.padL + 6, this.padT + 28);
  }
};

SMC50Chart.prototype._barIndex = function (t) {
  /* Busqueda binaria del indice de la vela con tiempo t */
  var a = 0, b = this.bars.length - 1, bi = -1;
  while (a <= b) {
    var m = (a + b) >> 1;
    var mt = this.bars[m].t;
    if (mt === t) return m;
    if (mt < t) { bi = m; a = m + 1; } else { b = m - 1; }
  }
  return bi;
};

SMC50Chart.prototype._legend = function (b) {
  if (!b) return;
  var up = b.c >= b.o;
  var d = new Date(b.t);
  function z(x) { return (x < 10 ? '0' : '') + x; }
  var dt = z(d.getDate()) + '/' + z(d.getMonth() + 1) + ' ' +
           z(d.getHours()) + ':' + z(d.getMinutes());
  this.legendEl.innerHTML =
    '<span class="lg-t">' + dt + '</span>' +
    ' O <b>' + this._fmtPx(b.o) + '</b>' +
    ' H <b>' + this._fmtPx(b.h) + '</b>' +
    ' L <b>' + this._fmtPx(b.l) + '</b>' +
    ' C <b class="' + (up ? 'up' : 'dn') + '">' + this._fmtPx(b.c) + '</b>';
};
