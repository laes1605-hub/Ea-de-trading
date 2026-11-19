'use strict';
/* =====================================================================
   SMC50-WEB · data.js — Fuentes de velas (TwelveData / Binance / Demo)
   ---------------------------------------------------------------------
   Todo corre en el navegador del usuario: la API key solo vive en su
   equipo (localStorage). Sin dependencias.
   Velas ascendentes: [{t: ms epoch, o, h, l, c}].
   ===================================================================== */

var SMC_TF_MIN = { M1: 1, M3: 3, M5: 5, M15: 15, M30: 30, H1: 60, H4: 240, D1: 1440 };
var SMC_TD_INTERVAL = { M1: '1min', M5: '5min', M15: '15min', M30: '30min', H1: '1h', H4: '4h', D1: '1day' };
var SMC_BN_INTERVAL = { M1: '1m', M3: '3m', M5: '5m', M15: '15m', M30: '30m', H1: '1h', H4: '4h', D1: '1d' };

var SMC_TD_SPECIAL = {
  US30: 'DJI', NAS100: 'NDX', SPX500: 'SPX',
  USOIL: 'WTI/USD', UKOIL: 'BCO/USD',
  XAUUSD: 'XAU/USD', XAGUSD: 'XAG/USD'
};
var SMC_BN_SPECIAL = { BTCUSD: 'BTCUSDT', ETHUSD: 'ETHUSDT' };

function smcFloorTime(ms, tfMin) {
  var s = tfMin * 60 * 1000;
  return Math.floor(ms / s) * s;
}

/* Agrega velas base ascendentes a un marco mayor (alineado a UTC). */
function smcAggregate(baseAsc, tfMin) {
  var out = [];
  var cur = null;
  for (var i = 0; i < baseAsc.length; i++) {
    var b = baseAsc[i];
    var bt = smcFloorTime(b.t, tfMin);
    if (!cur || cur.t !== bt) {
      if (cur) out.push(cur);
      cur = { t: bt, o: b.o, h: b.h, l: b.l, c: b.c };
    } else {
      if (b.h > cur.h) cur.h = b.h;
      if (b.l < cur.l) cur.l = b.l;
      cur.c = b.c;
    }
  }
  if (cur) out.push(cur);
  return out;
}

/* Separa la vela en formacion. Devuelve {closed, livePrice}. */
function smcSplitClosed(barsAsc, tfMin, nowMs) {
  nowMs = nowMs || Date.now();
  var curStart = smcFloorTime(nowMs, tfMin);
  var closed = [];
  var live = null;
  for (var i = 0; i < barsAsc.length; i++) {
    var b = barsAsc[i];
    if (b.t >= curStart) live = b.c;
    else closed.push(b);
  }
  if (live === null && closed.length) live = closed[closed.length - 1].c;
  return { closed: closed, livePrice: live };
}

function smcParseTDTime(s) {
  if (typeof s !== 'string') return NaN;
  if (/[TZ]|[+-]\d{2}:?\d{2}$/.test(s)) return Date.parse(s);
  return Date.parse(s.replace(' ', 'T') + 'Z'); /* naive = UTC */
}

function smcToTwelveSymbol(sym) {
  sym = (sym || '').toUpperCase().replace(/\s+/g, '');
  if (SMC_TD_SPECIAL[sym]) return SMC_TD_SPECIAL[sym];
  if (sym.indexOf('/') >= 0) return sym;
  if (/^[A-Z]{6}$/.test(sym)) return sym.slice(0, 3) + '/' + sym.slice(3);
  return sym;
}

function smcToBinanceSymbol(sym) {
  sym = (sym || '').toUpperCase().replace(/[\s/]/g, '');
  if (SMC_BN_SPECIAL[sym]) return SMC_BN_SPECIAL[sym];
  if (/^[A-Z0-9]+USDT$/.test(sym)) return sym;
  if (/^[A-Z0-9]+USD$/.test(sym)) return sym.slice(0, -3) + 'USDT';
  if (/^[A-Z0-9]+$/.test(sym)) return sym + 'USDT';
  return sym;
}

function smcLooksCrypto(sym) {
  var s = (sym || '').toUpperCase().replace(/[\s/]/g, '');
  return /^(BTC|ETH|BNB|SOL|XRP|DOGE|ADA|LTC|TRX|AVAX|LINK|DOT|ARB|OP|ATOM|NEAR|APT|SUI|TON|SHIB|PEPE)(USD|USDT)?$/.test(s);
}

/* ---------------- TwelveData (forex, metales, indices, cripto) ------- */
function smcFetchTwelveData(symbol, tf, key, count) {
  var mins = SMC_TF_MIN[tf];
  if (!mins) return Promise.reject(new Error('TF no soportado: ' + tf));
  var interval = SMC_TD_INTERVAL[tf];
  var needAgg = false;
  if (!interval) {
    if (tf === 'M3') { interval = '1min'; needAgg = true; }
    else return Promise.reject(new Error('TF no soportado en TwelveData: ' + tf));
  }
  var mult = (tf === 'M3') ? 3 : 1;
  var outputsize = Math.min(5000, (count || 300) * mult + 10);
  var url = 'https://api.twelvedata.com/time_series?symbol=' + encodeURIComponent(symbol) +
    '&interval=' + interval + '&outputsize=' + outputsize +
    '&format=JSON&timezone=UTC&apikey=' + encodeURIComponent(key);

  return fetch(url).then(function (r) { return r.json(); }).then(function (js) {
    if (!js || js.status === 'error') {
      var m = (js && js.message) ? js.message : 'respuesta invalida';
      if (/apikey|api key|invalid/i.test(m)) m += ' — revisa tu API key de TwelveData.';
      if (/not found|no data|invalid symbol/i.test(m)) m += ' — revisa el simbolo.';
      throw new Error('TwelveData: ' + m);
    }
    var vals = js.values;
    if (!vals || !vals.length) throw new Error('TwelveData: sin velas para ' + symbol + ' ' + interval);
    var bars = [];
    for (var i = 0; i < vals.length; i++) {
      var v = vals[i];
      var b = {
        t: smcParseTDTime(v.datetime),
        o: +v.open, h: +v.high, l: +v.low, c: +v.close
      };
      if (isFinite(b.t) && isFinite(b.o) && isFinite(b.h) && isFinite(b.l) && isFinite(b.c)) bars.push(b);
    }
    bars.sort(function (a, b) { return a.t - b.t; });
    if (needAgg) bars = smcAggregate(bars, mins);
    if (!bars.length) throw new Error('TwelveData: sin velas validas para ' + symbol);
    return smcSplitClosed(bars, mins);
  }).catch(function (e) {
    if (/TwelveData:/.test(e.message)) throw e;
    throw new Error('No se pudo contactar TwelveData (¿internet?). ' + e.message);
  });
}

/* ---------------- Binance (cripto, sin key) -------------------------- */
function smcFetchBinance(symbol, tf, count) {
  var iv = SMC_BN_INTERVAL[tf];
  var mins = SMC_TF_MIN[tf];
  if (!iv) return Promise.reject(new Error('TF no soportado en Binance: ' + tf));
  var url = 'https://api.binance.com/api/v3/klines?symbol=' + encodeURIComponent(symbol) +
    '&interval=' + iv + '&limit=' + Math.min(1000, (count || 300) + 2);

  return fetch(url).then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function (js) {
    if (!js || !js.length || !js[0].length) throw new Error('Binance: sin velas para ' + symbol);
    var bars = [];
    for (var i = 0; i < js.length; i++) {
      var k = js[i];
      bars.push({ t: k[0], o: +k[1], h: +k[2], l: +k[3], c: +k[4] });
    }
    return smcSplitClosed(bars, mins);
  }).catch(function (e) {
    if (/Binance:/.test(e.message)) throw e;
    throw new Error('No se pudo contactar Binance (¿internet?). ' + e.message);
  });
}

/* ---------------- Demo (datos generados, sin internet) --------------- */
function smcGenDemo(tf, count, seed) {
  var mins = SMC_TF_MIN[tf] || 15;
  var span = mins * 60 * 1000;
  var n = count || 300;
  var endStart = smcFloorTime(Date.now(), mins);
  var s = (seed === undefined ? 1234567 : seed) >>> 0;
  function rnd() { s = (s * 1103515245 + 12345) >>> 0; return s / 4294967296; }
  var px = 1.0850;
  var phase = 0;
  var bars = [];
  for (var i = n; i >= 1; i--) {
    var t = endStart - i * span;
    if (rnd() < 0.03) phase = (rnd() - 0.5) * 2;   /* cambios de regimen */
    var drift = phase * 0.0006 + (rnd() - 0.5) * 0.0009;
    var o = px;
    var c = o * (1 + drift);
    var h = Math.max(o, c) * (1 + rnd() * 0.0004);
    var l = Math.min(o, c) * (1 - rnd() * 0.0004);
    bars.push({ t: t, o: o, h: h, l: l, c: c });
    px = c;
  }
  return { closed: bars, livePrice: px };
}
