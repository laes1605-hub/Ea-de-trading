'use strict';
/* =====================================================================
   SMC50-WEB · app.js — Union de motor + datos + grafico + panel
   ===================================================================== */

(function () {
  var $ = function (id) { return document.getElementById(id); };

  var els = {
    sym: $('sym'), tf: $('tf'), mom: $('mom'), src: $('src'),
    key: $('key'), ref: $('ref'), marks: $('marks'),
    btnGo: $('btnGo'), btnPause: $('btnPause'),
    btnFollow: $('btnFollow'), btnZi: $('btnZi'), btnZo: $('btnZo'),
    chkZones: $('chkZones'), chkMom: $('chkMom'), chkAnchor: $('chkAnchor'),
    chkSound: $('chkSound'), chkNotif: $('chkNotif'),
    status: $('status'), count: $('countdown'), err: $('errbar'),
    legend: $('legend'), dashMain: $('dashMain'), dashMom: $('dashMom'),
    feed: $('feed'), btnClear: $('btnClear'), btnHelpKey: $('btnHelpKey')
  };

  var LS = 'smc50web_v1';
  var S = {
    sym: 'BTCUSD', tf: 'M15', mom: 'H1', src: 'auto', key: '',
    ref: 20, marks: 30,
    zones: true, showMom: true, anchor: true, sound: true, notif: false,
    paused: false
  };
  try {
    var saved = JSON.parse(localStorage.getItem(LS) || '{}');
    for (var k in saved) { if (k in S) S[k] = saved[k]; }
  } catch (e) { /* localStorage no disponible */ }

  function save() {
    try {
      var o = {};
      for (var k in S) { if (k !== 'paused') o[k] = S[k]; }
      localStorage.setItem(LS, JSON.stringify(o));
    } catch (e) { /* noop */ }
  }

  function syncInputs() {
    els.sym.value = S.sym;
    els.tf.value = S.tf;
    els.mom.value = S.mom;
    els.src.value = S.src;
    els.key.value = S.key;
    els.ref.value = String(S.ref);
    els.marks.value = String(S.marks);
    els.chkZones.checked = S.zones;
    els.chkMom.checked = S.showMom;
    els.chkAnchor.checked = S.anchor;
    els.chkSound.checked = S.sound;
    els.chkNotif.checked = S.notif;
  }

  function readInputs() {
    S.sym = (els.sym.value || 'BTCUSD').toUpperCase().replace(/\s+/g, '');
    S.tf = els.tf.value;
    S.mom = els.mom.value;
    S.src = els.src.value;
    S.key = els.key.value.trim();
    S.ref = Math.max(10, Math.min(300, parseInt(els.ref.value, 10) || 20));
    S.marks = Math.max(5, Math.min(100, parseInt(els.marks.value, 10) || 30));
    S.zones = els.chkZones.checked;
    S.showMom = els.chkMom.checked;
    S.anchor = els.chkAnchor.checked;
    S.sound = els.chkSound.checked;
    S.notif = els.chkNotif.checked;
  }

  /* ---------------- sonido + notificaciones ------------------------- */
  var AC = null;
  function beep(freq, t0, dur) {
    try {
      if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)();
      if (AC.state === 'suspended') AC.resume();
      var o = AC.createOscillator();
      var g = AC.createGain();
      o.type = 'sine';
      o.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, AC.currentTime + t0);
      g.gain.exponentialRampToValueAtTime(0.25, AC.currentTime + t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, AC.currentTime + t0 + dur);
      o.connect(g);
      g.connect(AC.destination);
      o.start(AC.currentTime + t0);
      o.stop(AC.currentTime + t0 + dur + 0.02);
    } catch (e) { /* audio no disponible */ }
  }
  function alertNew(ev, tfTag, sym) {
    if (S.sound) {
      if (ev.isChoch) { beep(523, 0, 0.14); beep(784, 0.16, 0.18); }
      else beep(660, 0, 0.14);
    }
    if (S.notif && ('Notification' in window) && Notification.permission === 'granted') {
      try {
        new Notification('SMC50 ' + sym + ' ' + tfTag, {
          body: (ev.isChoch ? 'CHoCH' : 'BOS') + ' ' +
                (ev.dir > 0 ? 'ALCISTA' : 'BAJISTA') +
                ' — 50% estructura: ' + ev.eq50.toFixed(chart.digits)
        });
      } catch (e) { /* noop */ }
    }
  }
  els.chkNotif.addEventListener('change', function () {
    if (els.chkNotif.checked && ('Notification' in window) && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  });

  /* ---------------- grafico ----------------------------------------- */
  var chart = new SMC50Chart($('chart'), { legendEl: els.legend });

  /* ---------------- estado de datos --------------------------------- */
  var D = {
    bars: [], live: null, eng: null, events: [],
    mBars: [], mLive: null, mEng: null, mEvents: [],
    seen: {}, firstLoad: true, timer: null, cdTimer: null,
    nextAt: 0, loading: false, lastSrc: ''
  };

  function setStatus(txt, cls) {
    els.status.innerHTML = '<span class="dot ' + (cls || 'ok') + '"></span>' + txt;
  }

  function showErr(html) {
    if (!html) { els.err.classList.add('hidden'); els.err.innerHTML = ''; return; }
    els.err.classList.remove('hidden');
    els.err.innerHTML = html;
  }

  function digitsFor(sym) {
    var s = (sym || '').toUpperCase();
    if (s.indexOf('JPY') >= 0) return 3;
    if (s === 'XAUUSD') return 2;
    if (s === 'XAGUSD') return 3;
    if (/^(US30|NAS100|SPX500|US500|USTEC|DJ30)/.test(s)) return 2;
    if (s === 'BTCUSD' || s === 'BTCUSDT') return 1;
    if (smcLooksCrypto(s)) return 2;
    if (/^[A-Z]{6}$/.test(s.replace('/', ''))) return 5;
    return 5;
  }

  function resolveSource() {
    if (S.src === 'twelvedata') return 'twelvedata';
    if (S.src === 'binance') return 'binance';
    if (S.src === 'demo') return 'demo';
    if (smcLooksCrypto(S.sym)) return 'binance';
    if (S.key) return 'twelvedata';
    return 'nokey';
  }

  function fetchTF(tf, source) {
    if (source === 'demo') {
      return Promise.resolve(smcGenDemo(tf, 320, Date.now() % 100000));
    }
    if (source === 'binance') {
      return smcFetchBinance(smcToBinanceSymbol(S.sym), tf, 320);
    }
    return smcFetchTwelveData(smcToTwelveSymbol(S.sym), tf, S.key, 320);
  }

  function srcName(source) {
    if (source === 'demo') return 'DEMO (generados)';
    if (source === 'binance') return 'Binance';
    return 'TwelveData';
  }

  /* ---------------- panel ------------------------------------------- */
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  }

  function lastOf(list, wantChoch) {
    for (var i = list.length - 1; i >= 0; i--) {
      if (list[i].isChoch === wantChoch) return list[i];
    }
    return null;
  }

  function fmtT(ms) {
    var d = new Date(ms);
    function z(x) { return (x < 10 ? '0' : '') + x; }
    return z(d.getDate()) + '/' + z(d.getMonth() + 1) + ' ' +
           z(d.getHours()) + ':' + z(d.getMinutes());
  }

  function dashHTML(title, eng, events, digits) {
    if (!eng || !eng.Valid) {
      return '<h3>' + esc(title) + '</h3><p class="dim">Sin datos.</p>';
    }
    var bCls = eng.Bias === SMC_BIAS_BULL ? 'bull' : (eng.Bias === SMC_BIAS_BEAR ? 'bear' : '');
    var nB = 0, nC = 0, i;
    for (i = 0; i < events.length; i++) {
      if (events[i].isChoch) nC++; else nB++;
    }
    var lB = lastOf(events, false), lC = lastOf(events, true);
    function evLine(e2) {
      if (!e2) return '<span class="dim">—</span>';
      var px = (S.anchor ? e2.eq50 : e2.leg50).toFixed(digits);
      return '<span style="color:' + smcEventColor(e2) + '"><b>' +
        (e2.isChoch ? 'CHoCH' : 'BOS') + ' ' + (e2.dir > 0 ? 'ALC' : 'BAJ') +
        '</b> ' + fmtT(e2.t) + ' · 50%=' + px + '</span>';
    }
    function px(v) { return v > 0 ? v.toFixed(digits) : '—'; }
    return '<h3>' + esc(title) + '</h3>' +
      '<div class="biasrow"><span class="bias ' + bCls + '">' + smcBiasText(eng.Bias) + '</span>' +
      '<span class="phase">' + smcPhaseText(eng.Phase) + '</span></div>' +
      '<table class="lv">' +
      '<tr><td>L1</td><td>' + px(eng.L1) + '</td><td>L2</td><td>' + px(eng.L2) + '</td></tr>' +
      '<tr><td><b>50%</b></td><td><b>' + px(eng.EQ) + '</b></td><td>Ref BOS</td><td>' + px(eng.RefLevel) + '</td></tr>' +
      '<tr><td>L3</td><td>' + (eng.L3L4 ? px(eng.L3) : '—') + '</td><td>L4</td><td>' +
      (eng.L3L4 ? px(eng.L4) : '—') + '</td></tr>' +
      '</table>' +
      '<p class="cnt">BOS: <b>' + nB + '</b> · CHoCH: <b>' + nC + '</b></p>' +
      '<p class="ev">Último BOS: ' + evLine(lB) + '</p>' +
      '<p class="ev">Último CHoCH: ' + evLine(lC) + '</p>';
  }

  function feedAdd(ev, tfTag, live) {
    var d = document.createElement('div');
    d.className = 'fe' + (live ? ' new' : '');
    var kind = ev.isChoch ? 'CHoCH' : 'BOS';
    var dd = ev.dir > 0 ? 'ALCISTA' : 'BAJISTA';
    d.innerHTML = '<span class="ft">' + fmtT(ev.t) + '</span> ' +
      '<span class="fk" style="color:' + smcEventColor(ev) + '">[' + tfTag + '] ' +
      kind + ' ' + dd + '</span><br>' +
      '50% est <b>' + ev.eq50.toFixed(chart.digits) + '</b> · ' +
      'tramo 50% <b>' + ev.leg50.toFixed(chart.digits) + '</b> · cierre ' +
      ev.rc.toFixed(chart.digits);
    els.feed.insertBefore(d, els.feed.firstChild);
    while (els.feed.children.length > 200) {
      els.feed.removeChild(els.feed.lastChild);
    }
  }

  els.btnClear.addEventListener('click', function () { els.feed.innerHTML = ''; });

  /* ---------------- ciclo de actualizacion --------------------------- */
  function updatePanels() {
    els.dashMain.innerHTML = dashHTML(S.sym + ' · ' + S.tf + ' (principal)', D.eng, D.events, chart.digits);
    if (S.mom !== 'OFF' && D.mEng) {
      els.dashMom.style.display = '';
      els.dashMom.innerHTML = dashHTML(S.sym + ' · ' + S.mom + ' (madre)', D.mEng, D.mEvents, chart.digits);
    } else {
      els.dashMom.style.display = 'none';
    }
  }

  function ingest(list, tfTag) {
    for (var i = 0; i < list.length; i++) {
      var e2 = list[i];
      var key = tfTag + '|' + e2.t + '|' + e2.dir + '|' + (e2.isChoch ? 'C' : 'B');
      if (D.seen[key]) continue;
      D.seen[key] = 1;
      feedAdd(e2, tfTag, !D.firstLoad);
      if (!D.firstLoad) alertNew(e2, tfTag, S.sym);
    }
  }

  function refresh() {
    if (D.loading) return;
    readInputs();
    save();
    var source = resolveSource();

    if (source === 'nokey') {
      showErr('<b>' + esc(S.sym) + ' necesita datos de forex/metales.</b> ' +
        'Escribe tu <b>API key gratuita de TwelveData</b> arriba y pulsa CONECTAR ' +
        '(se consigue en 1 minuto en <b>twelvedata.com → Get free API key</b>), ' +
        'o elige un símbolo cripto (BTCUSD, ETHUSD) que funciona sin key, ' +
        'o fuente <b>Demo</b> para probar. ' +
        '<button id="btnDemo" class="mini">Probar con Demo</button>');
      var bd = $('btnDemo');
      if (bd) bd.addEventListener('click', function () {
        els.src.value = 'demo';
        refresh();
      });
      setStatus('Esperando API key', 'warn');
      schedule();
      return;
    }

    /* H1 madre == TF principal → reutiliza los mismos datos */
    var sameTF = (S.mom !== 'OFF' && S.mom === S.tf);
    D.loading = true;
    setStatus('Cargando ' + S.sym + ' ' + S.tf + '… (' + srcName(source) + ')', 'warn');
    showErr(null);

    var p1 = fetchTF(S.tf, source);
    var p2 = (S.mom === 'OFF' || sameTF) ? null : fetchTF(S.mom, source);

    Promise.all([p1, p2]).then(function (rs) {
      var r1 = rs[0];
      var r2 = sameTF ? r1 : rs[1];
      if (!r1.closed.length) throw new Error('Sin velas cerradas para ' + S.sym + ' ' + S.tf);

      D.bars = r1.closed;
      D.live = r1.livePrice;
      var run1 = smc50Run(D.bars, { maxMarks: S.marks, livePrice: D.live });
      D.eng = run1.engine;
      D.events = run1.events;

      if (S.mom !== 'OFF' && r2 && r2.closed.length) {
        D.mBars = r2.closed;
        D.mLive = r2.livePrice;
        var run2 = smc50Run(D.mBars, { maxMarks: S.marks, livePrice: D.mLive });
        D.mEng = run2.engine;
        D.mEvents = run2.events;
      } else {
        D.mBars = []; D.mEng = null; D.mEvents = [];
      }

      var digits = digitsFor(S.sym);
      chart._tfTag = S.tf;
      chart._mTag = S.mom;
      chart.setData({
        bars: D.bars, engine: D.eng, events: D.events,
        motherEngine: (S.showMom && S.mom !== 'OFF') ? D.mEng : null,
        motherEvents: (S.showMom && S.mom !== 'OFF') ? D.mEvents : [],
        digits: digits,
        label: S.sym + ' · ' + S.tf + (source === 'demo' ? ' · DEMO' : ''),
        sublabel: 'SMC50 · L1-L4 + BOS/CHoCH dentro del 50% · ' + srcName(source),
        showZones: S.zones, showMother: S.showMom, anchorAt50: S.anchor
      });

      ingest(D.events, S.tf);
      if (S.mom !== 'OFF') ingest(D.mEvents, S.mom);
      if (D.firstLoad) {
        /* En la primera carga el historial entra en silencio (ya sonó nada) */
        D.firstLoad = false;
      }
      updatePanels();

      var d = new Date();
      function z(x) { return (x < 10 ? '0' : '') + x; }
      D.lastSrc = srcName(source);
      setStatus(S.sym + ' ' + S.tf + ' · ' + D.bars.length + ' velas · ' +
        D.events.length + ' marcas · ' + D.lastSrc +
        ' · act. ' + z(d.getHours()) + ':' + z(d.getMinutes()) + ':' + z(d.getSeconds()),
        source === 'demo' ? 'warn' : 'ok');
      D.loading = false;
      schedule();
    }).catch(function (e) {
      D.loading = false;
      setStatus('Error de datos', 'err');
      var hint = '';
      if (/API key/i.test(e.message)) {
        hint = 'Consejo: crea una key gratuita en <b>twelvedata.com → Get free API key</b> y pégala arriba.';
      } else if (/Binance/i.test(e.message)) {
        hint = 'Consejo: revisa el símbolo (p. ej. BTCUSD, ETHUSD) o tu conexión.';
      } else if (/simbolo/i.test(e.message)) {
        hint = 'Consejo: para forex usa formato EURUSD; para índices prueba US30 / NAS100 / SPX500.';
      }
      showErr('<b>' + esc(e.message) + '</b><br>' + hint);
      schedule();
    });
  }

  function schedule() {
    if (D.timer) clearTimeout(D.timer);
    if (D.cdTimer) clearInterval(D.cdTimer);
    if (S.paused) {
      els.count.textContent = 'pausado';
      return;
    }
    D.nextAt = Date.now() + S.ref * 1000;
    D.timer = setTimeout(refresh, S.ref * 1000);
    var tick = function () {
      var s = Math.max(0, Math.round((D.nextAt - Date.now()) / 1000));
      els.count.textContent = 'próx. actualización en ' + s + 's';
    };
    tick();
    D.cdTimer = setInterval(tick, 1000);
  }

  /* ---------------- eventos UI -------------------------------------- */
  els.btnGo.addEventListener('click', function () {
    S.paused = false;
    els.btnPause.textContent = 'Pausar';
    D.seen = {};
    D.firstLoad = true;
    chart.follow = true;
    chart.view.count = 120;
    refresh();
  });
  els.btnPause.addEventListener('click', function () {
    S.paused = !S.paused;
    els.btnPause.textContent = S.paused ? 'Reanudar' : 'Pausar';
    if (S.paused) {
      if (D.timer) clearTimeout(D.timer);
      if (D.cdTimer) clearInterval(D.cdTimer);
      els.count.textContent = 'pausado';
    } else {
      refresh();
    }
  });
  els.btnFollow.addEventListener('click', function () { chart.resetView(); });
  els.btnZi.addEventListener('click', function () { chart.zoom(1 / 1.3); });
  els.btnZo.addEventListener('click', function () { chart.zoom(1.3); });

  [els.chkZones, els.chkMom, els.chkAnchor].forEach(function (el) {
    el.addEventListener('change', function () {
      readInputs(); save();
      chart.setData({
        bars: D.bars, engine: D.eng, events: D.events,
        motherEngine: (S.showMom && S.mom !== 'OFF') ? D.mEng : null,
        motherEvents: (S.showMom && S.mom !== 'OFF') ? D.mEvents : [],
        showZones: S.zones, showMother: S.showMom, anchorAt50: S.anchor
      });
      updatePanels();
    });
  });
  [els.chkSound, els.chkNotif, els.marks].forEach(function (el) {
    el.addEventListener('change', function () { readInputs(); save(); });
  });
  els.key.value = S.key;

  if (els.btnHelpKey) {
    els.btnHelpKey.addEventListener('click', function () {
      var h = $('helpKey');
      if (h) h.open = true;
      if (h) h.scrollIntoView({ behavior: 'smooth' });
    });
  }

  /* ---------------- arranque ---------------------------------------- */
  syncInputs();
  chart.resetView();
  refresh();
})();
