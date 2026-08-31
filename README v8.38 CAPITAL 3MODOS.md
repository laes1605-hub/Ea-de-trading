# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.38** (estrategia PERSONAL de líneas + ESTRATEGIA 1 de confluencia H1+M3 + **panel MULTI-PAR** + **gestión de riesgo de Asistente 3 por par** + **3 modos de capital base**).

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador multichart.mq5` | Código fuente del EA (se compila en MetaEditor). |
| `ea.txt` | Copia en texto plano del mismo archivo (sin BOM). |
| `smc2.mq5` | EA visual SMC independiente (motor de líneas L1-L4, OB y FVG) — referencia de la lógica portada. |

## Estrategia (v8.35)

### Líneas visibles (paso 1)

- **En el TF del gráfico solo existen las 4 líneas: L1, L2, L3 y L4.** Se eliminaron las líneas D1 y las EQ del dibujo (el motor es el mismo de siempre, esa lógica no cambió).
- La **ESTRATEGIA 1** añade encima sus propios visuales: rango H1 (naranja), **línea del 50% H1** (dorado punteada), **zona de COMPRA** (mitad inferior, relleno verde) y **zona de VENTA** (mitad superior, relleno rojo), y el **nivel de entrada congelado 50% M3** (verde/rojo discontinua).
- Input `InpShowConfluencias` para mostrar/ocultar los visuales de la confluencia.

### ESTRATEGIA 1 — Confluencia H1 (madre) + M3 (entrada)

Dos temporalidades de confluencia: **H1 = estructura madre** y **M3 = confirmación de entrada** (configurables en `InpConfTFSuperior` / `InpConfTFEntrada`). Ambas usan el mismo motor de líneas L1-L4.

**Cómo funciona:**

1. Se marca el **50% del rango actual H1**: zona de **COMPRA = parte de abajo** (precio ≤ 50%) y zona de **VENTA = parte de arriba** (precio ≥ 50%).
2. **En estructura H1 alcista solo se hacen compras; en bajista solo ventas.**
3. **Compras** (simétrico para ventas):
   1. Se activa la búsqueda de compras cuando el precio **toca** la zona de compra H1 — solo con tocarla basta, aunque luego salga de la zona.
   2. Con la lógica de líneas en **M3** se espera un **cambio de estructura bajista→alcista (CHoCH)**.
   3. Detectado el cambio, se marca el **50% del rango M3 solo cuando el precio lo cruza**; ese nivel queda **CONGELADO** (no se actualiza aunque el rango se ensanche) y allí se coloca una **orden LIMIT de compra** con el SL/TP del EA.
4. Ventas: toque de la zona de venta H1 → CHoCH **alcista→bajista** en M3 → cruce del 50% M3 a la baja → **SELL LIMIT** congelado en ese 50%.

**Reglas de órdenes:**

- **Solo puede haber una posición abierta por par.** Con una posición abierta no se coloca nada y los CHoCH que llegan caducan.
- **Al abrirse una posición se eliminan el resto de órdenes limit** pendientes del par.
- Sin posición abierta puede colocar las órdenes limit que la lógica genere (un CHoCH válido = una orden).
- Si la orden se ejecutó y la posición **se perió estando el precio aún en la zona**, puede buscar otra entrada (con un CHoCH nuevo). Si **ya no está en la zona**, no busca hasta que **vuelva a tocarla**.
- Un **cambio de estructura H1** reinicia las zonas y exige un nuevo toque.

**Fases:** igual que el resto del EA, la estrategia primero opera en **simulación (virtual)** —sus limit se simulan y se registran como `vOPEN`— y pasa a **LIVE** (órdenes limit reales) al alcanzar el umbral `InpXActivacion`. Toda la gestión (CV/CR, tabla de riesgo, trailing 1:2, circuit breaker) se aplica igual.

- Inputs: `InpUseConfluencia` (activar), `InpAllowConfluOrders` (permitir órdenes, por defecto `true`), `InpConfTFSuperior=H1`, `InpConfTFEntrada=M3`, `InpShowConfluencias`.

### Estrategia PERSONAL (líneas L1-L4, RR 1:3)

- Entra en el *trigger* al cierre: si durante la reacción **L3** sobrepasa **L1** (compra/estructura alcista) o **L4** sobrepasa **L2** hacia abajo (venta/estructura bajista), el rompimiento queda pendiente y se consolida con vela cerrada.
- **Operativa pausada por seguridad**: `InpAllowPersonalOrders=false` por defecto; el EA solo calcula/dibuja sus líneas hasta activar ese input.
- Las estrategias antiguas **SMC (CHoCH), FVG y OB-H1 siguen eliminadas**.

### Motor de estructura (las 4 líneas)

- **L1/L2** = techo/suelo del rango; **EQ** = punto medio. Tras inicializar con `InpLookbackBars`, se actualizan **solo al cierre de vela**, usando high/low para incluir mechas: en estructura alcista solo sube **L1** y en estructura bajista solo baja **L2**.
- **L3/L4** = zona de reacción. Solo aparece cuando cierra una vela contraria a la estructura (bajista en alcista, alcista en bajista) y desde ese momento guarda máximo/mínimo **al tick**, contando mechas.
- Activación: en alcista **L3=L1** y **L4=mínimo** de la vela contraria; en bajista **L3=máximo** de la vela contraria y **L4=L2**.
- **Trigger/swap al cierre** = si durante la reacción **L3>L1** o **L4<L2**, se marca la ruptura como pendiente; al cierre se consolida **L1=L3**, **L2=L4**, se ocultan L3/L4 y el bias queda en la dirección del rompimiento. Si una vela toca ambos extremos, se respeta el último lado roto por tick; si solo hay OHLC, se usa el sentido del cuerpo.

## Líneas visibles en el gráfico

Las líneas **se marcan con colores vivos y etiqueta con nombre + precio**:

| Línea | Color | Estilo | Significado |
|---|---|---|---|
| `L1` / `L2` | 🔵 Azul (DodgerBlue) | Sólida, grosor 2 | Máximo/mínimo del TF del gráfico |
| `L3` | 🟣 Magenta | Discontinua, grosor 2 | Techo de la zona de reacción (activa) |
| `L4` | 🔴 Rojo | Discontinua, grosor 2 | Suelo de la zona de reacción (activa) |
| `H1 L1` / `H1 L2` | 🟠 Naranja | Sólida, grosor 2 | Rango de la estructura madre H1 (Estrategia 1) |
| `50% H1` | 🟡 Dorado | Punteada | Punto medio del rango H1 (Estrategia 1) |
| Zona COMPRA / VENTA H1 | 🟢 Verde / 🔴 Rojo | Rectángulo relleno | Mitad inferior / superior del rango H1 |
| `ENTRADA (50% M3)` | 🟢 Lima / 🔴 Rojo | Discontinua | Nivel congelado de la orden limit (Estrategia 1) |

- Se dibujan en el gráfico **en vivo y también en el Strategy Tester (modo visual)**.
- Etiqueta al lado derecho de cada línea con su nombre y precio (ej. `L1  1.08452`).
- Inputs `InpShowStructureLines` (líneas del TF) e `InpShowConfluencias` (zonas H1/M3).
- L3/L4 solo aparecen cuando la zona de reacción está activa (así funciona el motor).
- Además, para cada **posición abierta** del símbolo del gráfico se dibujan: **ENTRADA** (blanca discontinua, con dirección y lotes), **SL** (roja punteada), **TP** (verde punteada) y las órdenes **LIMIT** pendientes (lima/rojo raya-punto) — en el tester visual y en el gráfico real (`InpShowPosLines`).

\* Con RR 1:3 el punto de equilibrio es ~25% de aciertos (más costos ≈ 27–30%), así que un win rate del 40% ya da expectativa positiva. Mide con **profit factor** (>1.5 sólido, >2.0 excelente) y **máximo drawdown**, no solo el win rate.

## PANEL MULTI-PAR (v8.36) — tester visual y gráfico real

Panel **organizado y legible con una fila por par**, dibujado sobre un único bitmap (canvas, sin parpadeo). Aparece automáticamente en la **esquina superior derecha** del gráfico, **igual en el Strategy Tester (modo visual) que en el gráfico real**:

1. **Cabecera**: modo (TESTER VISUAL / REAL), nº de pares, posiciones abiertas y limits pendientes, fecha/hora.
2. **Resumen de cuenta**: Balance · Equidad · P&L flotante · Circuit breaker del día (con color).
3. **Tabla por par** (hasta 10 filas, ordenadas por actividad: posición > limit > esperando):

   | PAR | H1 | M3 | ZONA | LÍMITE | POSICIÓN | NIV | LOT | P&L | ESTADO / PRÓXIMO PASO |
   |---|---|---|---|---|---|---|---|---|---|
   | EURUSD | ALC | BAJ | C | B 1.08452 | ▲ 0.02 1.0845 | 3 | 0.03 | +1.25 | POSICIÓN ABIERTA |

   - Fila **verde** = posición abierta · **azul** = limit pendiente · **roja** = pausa por circuit breaker.
   - **ESTADO** dice qué falta en lenguaje claro: `ESPERA CRUCE 50% (C)`, `ZONA C ✓ CHoCH M3`, `ZONA C ✓ H1 NO ALCISTA`, `FUERA DE ZONA`, `LIMIT B 1.08452`, `POSICIÓN ABIERTA`.
4. **Mini-gráficos por par** (hasta 6): precio del TF de entrada (M3) con **sus propias líneas** — L1/L2/L3/L4 del motor, rango H1 y 50% H1, entrada limit congelada y ENTRADA/SL/TP de la posición. Cada par tiene su propia escala, así que **todos los pares abiertos se ven con sus líneas aunque el tester solo muestre un gráfico**.
5. **Leyenda** de colores al pie.

Inputs (grupo `PANEL MULTI-PAR`): `InpShowMultiPanel` (panel on/off), `InpShowMiniCharts` (mini-gráficos on/off), `InpMPChartsAll` (mostrar también pares sin posición), `InpMPBars` (velas del mini-gráfico), `InpMPX`/`InpMPY` (posición; X=0 = automática derecha), `InpShowPosLines` (líneas ENTRADA/SL/TP/LIMIT en el gráfico).

Extras de esta versión:

- El resumen de validación por pares ya **no se imprime en cada tick** (inundaba el journal): ahora va al log cada 5 min y su versión visual es el panel.
- Se eliminaron las etiquetas sueltas de 7px (`PAIRLBL_*`, `VALIDA_SUM`) que se encimaban; si el panel está apagado en el tester, vuelve el `Comment()` de siempre como respaldo.

## Gestión de riesgo (v8.38 — lógica de "Asistente 3", nivel POR PAR)

La progresión de niveles es la del EA **Asistente 3**, aplicada con **un nivel 1-20 por par** (compartido por las estrategias del par), y el lote sigue saliendo de la **tabla de riesgo de 20 niveles** (% de la base de capital) que se mantiene igual:

| Cierre | Nivel del par |
|---|---|
| **PÉRDIDA** (SL) | **+1** (sube por la tabla → lote mayor) |
| **GANANCIA limpia** (TP) | **= 1** (reset) |
| **GANANCIA con SL protegido** (1:2) | **−3** si la posición se abrió en nivel <10, **−4** si se abrió en nivel ≥10 |

- **1:2 automático desde nivel 5** (`InpAutoFromLevel5=true`, como Asistente 3): las posiciones abiertas con nivel del par ≥5 activan el SL protegido al avanzar `InpActivationPoints` (210) → SL a `InpProtectedSL` (205). Esa ganancia "protegida" baja el nivel −3/−4 en vez de resetear a 1.
- **MODO AVANZADO** (panel CONFIG): fuerza el 1:2 en todas las posiciones nuevas, además del automático por nivel.
- **Se mantiene igual**: la **tabla de riesgo** (`InpRiskStep1..20`, % de la base), la **base dinámica de capital**, el **sistema virtual → LIVE** (`InpXActivacion=4`: la estrategia simula con CV y pasa a real al alcanzar el umbral — el CV solo cuenta pérdidas virtuales, ya no mueve niveles), el **circuit breaker diario** (`InpMaxDailyLossPct=4.5%`), **SL/TP** (95/305, RR ≈ 1:3.2), **split de lotes**, **filtro de horario** y hasta 20 símbolos con SL/TP propios.
- Los cierres **virtuales no mueven el nivel** ni se contabilizan como operaciones de cuenta; únicamente actualizan el CV para decidir cuándo activar LIVE. El nivel solo cambia con cierres LIVE reales.
- El nivel y su lote se ven en el panel (pestaña OPERAR "NIVEL → Lotaje", CUENTA "Nivel par / Lot", ESTRAT "NIV→Lot") y en la columna **NIV** del PANEL MULTI-PAR. En el log: `NIVEL:3→4`.
- El estado se guarda por par (`PLEVEL`) en el archivo de estado; los comentarios de órdenes llevan el nivel (`QA_EA_EURUSD_CONFL_N3`).

### Modos de capital base (v8.38)

El lote siempre sale de la **tabla de riesgo de 20 niveles** (% de la base). Lo que cambia es **qué capital base** se usa para calcular ese porcentaje. Se selecciona con el input `InpCapitalMode` (grupo de inputs "MODO DE CAPITAL BASE"):

| Modo | Input | Cómo se calcula la base de decisión |
|---|---|---|
| **DINÁMICA** (por defecto) | `CAP_MODE_DYNAMIC` | Como antes: `InpBaseCapital` + los aumentos de balance por encima del máximo histórico (`Bal.máx`). Crece con la cuenta y **no** baja con las pérdidas. |
| **FIJA** | `CAP_MODE_FIXED` | Siempre = `InpBaseCapital` (ej. 1000). No crece ni disminuye aunque la cuenta suba o baje. |
| **% DE LA CUENTA** | `CAP_MODE_ACCOUNT` | Siempre = `InpBaseCapitalPct`% del **balance actual** (ej. `InpBaseCapitalPct=12` → base = 12% de la cuenta en cada decisión). Crece si la cuenta crece y baja si la cuenta baja. |

- `InpBaseCapital` (1000 por defecto): capital base de arranque de los modos **DINÁMICA** y **FIJA**.
- `InpBaseCapitalPct` (12.0 por defecto): porcentaje del balance usado solo en el modo **% DE LA CUENTA**.
- El modo elegido se muestra en el panel: pestaña **OPERAR** (`Base capital: DINÁMICA 1.234,56 …`), pestaña **CUENTA** (`BASE CAPITAL (12.0% CUENTA)`) y en el log de arranque (`EA v8.38 | … | Base=DINÁMICA 1000.00`).
- En el modo **FIJA** el lote del nivel N es idéntico siempre (mismo capital base), en el modo **% DE LA CUENTA** se recalcula a cada orden con el balance del momento, y en **DINÁMICA** se comporta exactamente como la versión anterior (no cambia el comportamiento por defecto).

## Cómo probar

1. Estrategia Tester: elige símbolo + timeframe (las señales se calculan en el TF del gráfico), cuenta demo. **Marca "Modo visual"** para ver las líneas y el panel.
   - **Ya no necesitas rellenar `InpSymbol1..20` en el tester**: el EA añade automáticamente el símbolo del gráfico que estás probando, opera sobre él y dibuja sus líneas.
   - El **PANEL MULTI-PAR** aparece arriba a la derecha: tabla con el estado de cada par + mini-gráficos con sus líneas. Si pruebas varios pares (rellenando `InpSymbol1..20`), cada par abierto muestra su mini-gráfico con L1/L2, H1, 50%, entrada y SL/TP — todo en el único gráfico del tester.
   - En el log verás `TESTER: símbolo del gráfico [XXX] añadido automáticamente.` y las líneas calculadas (`LINEAS [...] L1=… L2=…`).
2. En el log: `vOPEN` (simulación), `LIVE`, `CV/CR`, `CIRCUIT BREAKER`.
3. Métricas: profit factor, win rate, nº de trades, **máximo drawdown** (crítico por la tabla de riesgo).

### Si no ves las líneas en el tester

1. **"Modo visual" tiene que estar marcado** — sin él el tester no muestra gráfico, así que no hay dónde dibujar las líneas.
2. Mira el **log del tester**: debe aparecer `LINEAS [símbolo] L1=… L2=…`. Si no aparece, es que `InpShowStructureLines=false` o el símbolo no cargó datos (prueba con otro símbolo/timeframe).
3. Las líneas **L3/L4 solo aparecen cuando la zona de reacción está activa** (así funciona el motor); L1/L2 sí se ven siempre. Las zonas del 50% H1 aparecen con `InpUseConfluencia=true` e `InpShowConfluencias=true`.

## Verificación

### 1) En el repositorio (Git)

```bash
git status                          # working tree limpio = todo commiteado
git log --oneline -3
git show --stat HEAD
```

- Estrategia PERSONAL presente (debe dar `> 0`):
  ```bash
  grep -cE "CheckPersonalSignal|SE_OnClose|DrawStructureLines" "trabajador multichart.mq5"
  ```
- Estrategias eliminadas (debe dar `0`):
  ```bash
  grep -cE "CheckSMCSignal|CheckFVGSignal|CheckOBBounceSignal|InpUseSMC|InpUseFVG|InpUseOBBounce|InpZoneScanBars" "trabajador multichart.mq5"
  ```
- Dos estrategias (PERSONAL + CONFLUENCIA, debe dar `2`):
  ```bash
  grep -c "STRAT_COUNT      2" "trabajador multichart.mq5"
  ```
- Estrategia 1 de confluencia presente (debe dar `> 0`):
  ```bash
  grep -cE "UpdateConfluencia|ConfluenciaTryPlace|ConfluenciaProcessChoch|InpUseConfluencia" "trabajador multichart.mq5"
  ```
- Panel MULTI-PAR presente (debe dar `> 0`):
  ```bash
  grep -cE "MultiPanelUpdate|MPDrawMini|DrawPositionLines|InpShowMultiPanel" "trabajador multichart.mq5"
  ```
- Tres modos de capital base presentes (debe dar `> 0`):
  ```bash
  grep -cE "ENUM_CAPITAL_MODE|InpCapitalMode|EffectiveBaseCapital|InpBaseCapitalPct" "trabajador multichart.mq5"
  ```
- Etiquetas sueltas antiguas eliminadas (debe dar `0`):
  ```bash
  grep -cE "void DrawPerPairInfo" "trabajador multichart.mq5"
  ```
- Sin líneas D1 ni EQ dibujadas (debe dar `0`):
  ```bash
  grep -cE "SE_D1|d1LastBar|D1L1|D1EQ|TFEQ" "trabajador multichart.mq5"
  ```

### 2) En MetaTrader 5 (funcional)

1. Abre **MetaEditor** → `Archivo > Abrir datos > MQL5 > Experts` → pega `trabajador multichart.mq5`.
2. Pulsa **F7 (Compilar)**: debe compilar sin errores (usa `Canvas.mqh` de la librería estándar de MT5, ya incluida en la instalación).
3. En MT5: arrastra el EA al gráfico; en Inputs debe aparecer `ESTRATEGIA PERSONAL (LÍNEAS L1-L4, RR 1:3)`, `ESTRATEGIA 1: CONFLUENCIA (H1 MADRE + M3 ENTRADA)`, `PANEL MULTI-PAR (TESTER VISUAL + GRÁFICO REAL)` y `PARAMETROS MOTOR DE LINEAS`.
4. Verás en el gráfico las líneas L1-L4 del TF (azules/magenta/rojo) y, con la confluencia activa, el rango H1 naranja con su 50% dorado, las zonas verde (compra) y roja (venta), y la entrada 50% M3 cuando se congele. Arriba a la derecha, el **PANEL MULTI-PAR** con la tabla de todos los pares y sus mini-gráficos. En el tester, activa el **modo visual** para verlas.

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
