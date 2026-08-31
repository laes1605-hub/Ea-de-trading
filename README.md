# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.43** (**una sola estrategia**: estructura de líneas L1-L4 en H1 + apertura por confluencia en M3 + **panel MULTI-PAR** + **gestión de riesgo de Asistente 3 por par** + **3 modos de capital base** + **fase virtual→LIVE con conteo idéntico a LIVE** + **estado virtual por par en el panel**).

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador INICIAL v8.37.mq5` | **Código inicial del proyecto (v8.37, commit `b9df22f`)** — tal como estaba antes de empezar este chat: DOS estrategias (PERSONAL `LINEAS` + CONFLUENCIA `CONFL`), base dinámica de capital, panel MULTI-PAR, gestión de riesgo de Asistente 3 por par. |
| `trabajador v8.36 MULTI-PAR.mq5` | **Versión 8.36 (commit `2531c9b`)** — DOS estrategias (PERSONAL `LINEAS` + CONFLUENCIA H1/M3), **panel MULTI-PAR v8.36** (tester visual + gráfico real), sin la gestión de Asistente 3 por par (eso llegó en v8.37). |
| `ea v8.36 MULTI-PAR.txt` | Copia en texto plano de `trabajador v8.36 MULTI-PAR.mq5` (tal como estaba el `ea.txt` en ese commit). |
| `README v8.36 MULTI-PAR.md` | README original de esa versión. |
| `ea INICIAL v8.37.txt` | Copia en texto plano de `trabajador INICIAL v8.37.mq5` (tal como estaba en el repo al inicio). |
| `README INICIAL v8.37.md` | README original de esa versión. |
| `trabajador multichart.mq5` | **Versión actual (v8.43)**: estrategia única (estructura L1-L4 H1 + confluencia M3) + panel MULTI-PAR + 3 modos de capital + LIVE desde nivel 1 + **fix del bucle (limit solo del lado correcto del 50%)**. |
| `trabajador v8.40 LINEAS+CONFL.mq5` | Versión anterior (v8.40) con **DOS estrategias** (PERSONAL `LINEAS` + CONFLUENCIA `CONFL`), recuperada del historial (commit `c5bb1a7`). |
| `ea.txt` | Copia en texto plano de `trabajador multichart.mq5` (sin BOM). |
| `ea v8.40 LINEAS+CONFL.txt` | Copia en texto plano de `trabajador v8.40 LINEAS+CONFL.mq5` (sin BOM). |
| `smc2.mq5` | EA visual SMC independiente (motor de líneas L1-L4, OB y FVG) — referencia de la lógica portada. |

## Estrategia única (v8.43): estructura de líneas H1 + confluencia M3

El EA tiene **una sola estrategia**: la **estructura** se reconoce con la lógica de líneas **L1-L4** (la misma de siempre) y la **apertura** se hace con la lógica de confluencia. No hay una segunda estrategia de entrada.

**Cómo funciona:**

1. **Estructura madre (H1)** — el motor de líneas L1-L4 corre **siempre**:
   - **L1/L2** = techo/suelo del rango; **EQ** = 50% del rango; **L3/L4** = zona de reacción (vela contraria).
   - El **bias H1** (alcista/bajista) manda la dirección: **H1 alcista → solo compras; H1 bajista → solo ventas**.
   - Zona de **COMPRA = parte de abajo** del rango H1 (precio ≤ 50%) y zona de **VENTA = parte de arriba** (precio ≥ 50%).
2. **Toque de zona**: con solo tocar la zona se activa la búsqueda (aunque el precio luego salga de ella; un cambio de estructura H1 reinicia zonas y exige un nuevo toque).
3. **Estructura de entrada (M3)** — el motor de líneas L1-L4 de M3 también corre **siempre**:
   - Se espera un **cambio de estructura (CHoCH) en M3 a favor de la estructura de H1** (bajista→alcista si H1 es alcista; alcista→bajista si H1 es bajista).
4. **Entrada**: al generarse el CHoCH de M3, el rango para medir el **50% es el rango L1-L2 del M3 en ese momento** (el nivel queda **CONGELADO**). La **orden LIMIT** (BUY/SELL) con el SL/TP del EA **solo se coloca cuando el precio está del lado correcto del 50%** (por encima para compras, por debajo para ventas); si aún no está, el EA espera el cruce. Así la order siempre es llenable y no se generan virtuales que pierden al instante.
5. **Gestión**: la misma de siempre — tabla de riesgo, nivel 1-20 por par, trailing 1:2 automático, virtual→LIVE, circuit breaker.

**Reglas de órdenes:**

- **Solo puede haber una posición abierta por par** y **una limit pendiente por par**. Con posición abierta no se coloca nada y los CHoCH que llegan caducan.
- **La LIMIT solo se coloca con el precio del lado correcto del 50% congelado** (v8.43): el CHoCH congela el 50% y marca una espera; cuando el precio cruza al lado correcto (por encima para COMPRA / por debajo para VENTA) se coloca la limit en ese nivel. Esto evita que la limit quede "fuera de mercado" (que en virtual se llenara al instante y perdiera, disparando el LIVE y el "bucle"; y que el broker la rechazara en LIVE por estar pegada al precio).
- **Al abrirse una posición se eliminan el resto de órdenes limit** pendientes del par.
- Si la orden se ejecutó y la posición **se perdió estando el precio aún en la zona**, puede buscar otra entrada (con un CHoCH nuevo). Si **ya no está en la zona**, no busca hasta que **vuelva a tocarla**.
- Un **cambio de estructura H1** reinicia las zonas y exige un nuevo toque.

**Fases:** la estrategia primero opera en **simulación (virtual)** —sus limit se simulan y se registran como `vOPEN`— y pasa a **LIVE** (órdenes limit reales) al alcanzar el umbral `InpXActivacion`. Toda la gestión (CV/CR, tabla de riesgo, trailing 1:2, circuit breaker) se aplica igual.

**Inputs:** `InpUseConfluencia` (activar la estrategia), `InpAllowConfluOrders` (permitir órdenes, por defecto `true`), `InpConfTFSuperior=H1`, `InpConfTFEntrada=M3`, `InpShowConfluencias`.

### Motor de estructura (las 4 líneas)

- **L1/L2** = techo/suelo del rango; **EQ** = punto medio. Tras inicializar con `InpLookbackBars`, se actualizan **solo al cierre de vela**, usando high/low para incluir mechas: en estructura alcista solo sube **L1** y en estructura bajista solo baja **L2**.
- **L3/L4** = zona de reacción. Solo aparece cuando cierra una vela contraria a la estructura (bajista en alcista, alcista en bajista) y desde ese momento guarda máximo/mínimo **al tick**, contando mechas.
- Activación: en alcista **L3=L1** y **L4=mínimo** de la vela contraria; en bajista **L3=máximo** de la vela contraria y **L4=L2**.
- **Trigger/swap al cierre** = si durante la reacción **L3>L1** o **L4<L2**, se marca la ruptura como pendiente; al cierre se consolida **L1=L3**, **L2=L4**, se ocultan L3/L4 y el bias queda en la dirección del rompimiento. Si una vela toca ambos extremos, se respeta el último lado roto por tick; si solo hay OHLC, se usa el sentido del cuerpo.

> Nota: el motor del TF del gráfico (L1-L4 azules L1/L2, magenta/rojo L3/L4) se mantiene **solo como referencia visual**; la estructura que manda la operativa es la de H1.

## Líneas visibles en el gráfico

Las líneas **se marcan con colores vivos y etiqueta con nombre + precio**:

| Línea | Color | Estilo | Significado |
|---|---|---|---|
| `L1` / `L2` | 🔵 Azul (DodgerBlue) | Sólida, grosor 2 | Máximo/mínimo del TF del gráfico |
| `L3` | 🟣 Magenta | Discontinua, grosor 2 | Techo de la zona de reacción (activa) |
| `L4` | 🔴 Rojo | Discontinua, grosor 2 | Suelo de la zona de reacción (activa) |
| `H1 L1` / `H1 L2` | 🟠 Naranja | Sólida, grosor 2 | Rango de la estructura madre H1 (estructura única) |
| `50% H1` | 🟡 Dorado | Punteada | Punto medio del rango H1 (estructura única) |
| Zona COMPRA / VENTA H1 | 🟢 Verde / 🔴 Rojo | Rectángulo relleno | Mitad inferior / superior del rango H1 |
| `ENTRADA (50% M3)` | 🟢 Lima / 🔴 Rojo | Discontinua | 50% L1-L2 de M3 congelado en el CHoCH (orden limit) |

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
   - **ESTADO** dice qué falta en lenguaje claro: `50% CONGELADO 1.08452 · ESPERA PRECIO`, `ZONA C ✓ CHoCH M3`, `ZONA C ✓ H1 NO ALCISTA`, `FUERA DE ZONA`, `LIMIT B 1.08452`, `POSICIÓN ABIERTA`.
4. **Mini-gráficos por par** (hasta 6): precio del TF de entrada (M3) con **sus propias líneas** — L1/L2/L3/L4 del motor, rango H1 y 50% H1, entrada limit congelada y ENTRADA/SL/TP de la posición. Cada par tiene su propia escala, así que **todos los pares abiertos se ven con sus líneas aunque el tester solo muestre un gráfico**.
5. **Leyenda** de colores al pie.

Inputs (grupo `PANEL MULTI-PAR`): `InpShowMultiPanel` (panel on/off), `InpShowMiniCharts` (mini-gráficos on/off), `InpMPChartsAll` (mostrar también pares sin posición), `InpMPBars` (velas del mini-gráfico), `InpMPX`/`InpMPY` (posición; X=0 = automática derecha), `InpShowPosLines` (líneas ENTRADA/SL/TP/LIMIT en el gráfico).

Extras de esta versión:

- El resumen de validación por pares ya **no se imprime en cada tick** (inundaba el journal): ahora va al log cada 5 min y su versión visual es el panel.
- Se eliminaron las etiquetas sueltas de 7px (`PAIRLBL_*`, `VALIDA_SUM`) que se encimaban; si el panel está apagado en el tester, vuelve el `Comment()` de siempre como respaldo.

## Gestión de riesgo (v8.42 — lógica de "Asistente 3", nivel POR PAR)

La progresión de niveles es la del EA **Asistente 3**, aplicada con **un nivel 1-20 por par** (compartido por la estrategia única del par), y el lote sigue saliendo de la **tabla de riesgo de 20 niveles** (% de la base de capital) que se mantiene igual:

| Cierre | Nivel del par |
|---|---|
| **PÉRDIDA** (SL) | **+1** (sube por la tabla → lote mayor) |
| **GANANCIA limpia** (TP) | **= 1** (reset) |
| **GANANCIA con SL protegido** (1:2) | **−3** si la posición se abrió en nivel <10, **−4** si se abrió en nivel ≥10 |

- **1:2 automático desde nivel 5** (`InpAutoFromLevel5=true`, como Asistente 3): las posiciones abiertas con nivel del par ≥5 activan el SL protegido al avanzar `InpActivationPoints` (210) → SL a `InpProtectedSL` (205). Esa ganancia "protegida" baja el nivel −3/−4 en vez de resetear a 1.
- **MODO AVANZADO** (panel CONFIG): fuerza el 1:2 en todas las posiciones nuevas, además del automático por nivel.
- **Se mantiene igual**: la **tabla de riesgo** (`InpRiskStep1..20`, % de la base), los **3 modos de capital base**, el **circuit breaker diario** (`InpMaxDailyLossPct=4.5%`), **SL/TP** (95/305, RR ≈ 1:3.2), **split de lotes**, **filtro de horario** y hasta 20 símbolos con SL/TP propios.
- **Fase virtual → LIVE (v8.42)**: la estrategia **siempre** simula primero. Con `InpXActivacion=X` el EA pasa a LIVE cuando se **completan X pérdidas virtuales**, de modo que la **operación X+1 ya es LIVE** (ej. `X=4` → operaciones 1-4 virtuales, operación 5 en LIVE). El conteo de las operaciones virtuales usa **exactamente el mismo régimen que las operaciones LIVE** (reglas de Asistente 3):
  - **Pérdida** → CV +1 y nivel del par +1 (sube por la tabla).
  - **Ganancia limpia (TP)** → CV = 1 y nivel del par = 1 (reset).
  - **Ganancia con SL protegido (1:2)** → CV y nivel −3 (abierto en nivel <10) o −4 (abierto en nivel ≥10).
  - **Las X virtuales son SOLO la condición para pasar a LIVE.**
- **Al activar LIVE (v8.42) — regla clave**: la estrategia **NO arranca en el nivel al que llegó la serie virtual**. La **tabla arranca SIEMPRE en el NIVEL 1** (lote base) y la serie real progresa desde ahí (pérdida → `1→2→3…`). El nivel que alcanzó la serie virtual se recuerda como **nivel de lógica** (`liveLogicLevel`):
  - Ejemplo con `X=4`: la serie virtual llegó a nivel 5 → al activar LIVE la tabla marca **N1** (lote de nivel 1), pero el **1:2 automático se aplica como si estuviera en el nivel 5** (`★ LIVE · 1:2 (lóg.N5)` en el panel).
  - Si la primera operación live pierde, el nivel pasa **1→2** (no 5→6). Si gana limpia, vuelve a 1 y la sesión live termina; el "nivel de lógica" se limpia.
- `InpUseVirtualBeforeLive` se eliminó: la fase virtual ya no se puede saltar (antes, con `false`, las estrategias podían abrir órdenes reales sin pasar por el conteo virtual).
- Los cierres virtuales nunca se contabilizan como operaciones de la cuenta real.

### Estado virtual por par (v8.42)

El **PANEL MULTI-PAR** (esquina superior derecha, tester visual y gráfico real) tiene ahora una sección **`VIRTUAL → LIVE`** entre la tabla de pares y los mini-gráficos que muestra, en **una fila por par**, el estado de la estrategia (`CONFL`):

- **Pérdidas completadas / objetivo**: `pérd 2/4` (con `X=4`, 4 pérdidas = LIVE) — llegas a `3/4`, `4/4`…
- **Cuánto falta**: `falta 2` — número de pérdidas más para activar LIVE.
- **Barra de progreso** con marcas por pérdida (azul → naranja → amarillo cuando está lista).
- **Indicador `vOPEN`** cuando hay una operación virtual simulada en curso.
- **Estado**: `SIM`, `ESPERA` (próxima operación LIVE), `★ LIVE`, `PAUSA` (circuit breaker) u `OFF`.
- El **nivel y lote** de cada par se ven en la tabla de arriba (columnas `NTV` / `LOT`) y en la pestaña **ESTRAT**.
- Los pares se ordenan primero por los que ya están en **LIVE** y luego por los más **cerca de activarse**; si hay más de 10 pares, se indica cuántos quedan (también están todos en la tabla de arriba y en la pestaña **ESTRAT** del panel, que además muestra **"Falta: n"** para el par seleccionado).
- El nivel y su lote se ven en el panel (pestaña OPERAR "NIVEL → Lotaje", CUENTA "Nivel par / Lot", ESTRAT "NIV→Lot") y en la columna **NIV** del PANEL MULTI-PAR. En el log: `NIVEL:3→4`.
- El estado se guarda por par (`PLEVEL`) en el archivo de estado; los comentarios de órdenes llevan el nivel (`QA_EA_EURUSD_CONFL_N3`).

### Modos de capital base (v8.42)

El lote siempre sale de la **tabla de riesgo de 20 niveles** (% de la base). Lo que cambia es **qué capital base** se usa para calcular ese porcentaje. Se selecciona con el input `InpCapitalMode` (grupo de inputs "MODO DE CAPITAL BASE"):

| Modo | Input | Cómo se calcula la base de decisión |
|---|---|---|
| **DINÁMICA** (por defecto) | `CAP_MODE_DYNAMIC` | Como antes: `InpBaseCapital` + los aumentos de balance por encima del máximo histórico (`Bal.máx`). Crece con la cuenta y **no** baja con las pérdidas. |
| **FIJA** | `CAP_MODE_FIXED` | Siempre = `InpBaseCapital` (ej. 1000). No crece ni disminuye aunque la cuenta suba o baje. |
| **% DE LA CUENTA** | `CAP_MODE_ACCOUNT` | Siempre = `InpBaseCapitalPct`% del **balance actual** (ej. `InpBaseCapitalPct=12` → base = 12% de la cuenta en cada decisión). Crece si la cuenta crece y baja si la cuenta baja. |

- `InpBaseCapital` (1000 por defecto): capital base de arranque de los modos **DINÁMICA** y **FIJA**.
- `InpBaseCapitalPct` (12.0 por defecto): porcentaje del balance usado solo en el modo **% DE LA CUENTA**.
- El modo elegido se muestra en el panel: pestaña **OPERAR** (`Base capital: DINÁMICA 1.234,56 …`), pestaña **CUENTA** (`BASE CAPITAL (12.0% CUENTA)`) y en el log de arranque (`EA v8.42 | … | Base=DINÁMICA 1000.00`).
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

- ESTRATEGIA PERSONAL eliminada (debe dar `0`):
  ```bash
  grep -cE "CheckPersonalSignal|InpAllowPersonalOrders|STRAT_PERSONAL|InpUsePersonal" "trabajador multichart.mq5"
  ```
- Estrategias eliminadas (debe dar `0`):
  ```bash
  grep -cE "CheckSMCSignal|CheckFVGSignal|CheckOBBounceSignal|InpUseSMC|InpUseFVG|InpUseOBBounce|InpZoneScanBars" "trabajador multichart.mq5"
  ```
- Estrategia única (debe dar `1`):
  ```bash
  grep -c "STRAT_COUNT      1" "trabajador multichart.mq5"
  ```
- Estrategia única (estructura H1 + confluencia M3) presente (debe dar `> 0`):
  ```bash
  grep -cE "UpdateConfluencia|ConfluenciaProcessChoch|ConfluenciaPlacePending|InpUseConfluencia" "trabajador multichart.mq5"
  ```
- Panel MULTI-PAR presente (debe dar `> 0`):
  ```bash
  grep -cE "MultiPanelUpdate|MPDrawMini|DrawPositionLines|InpShowMultiPanel" "trabajador multichart.mq5"
  ```
- Tres modos de capital base presentes (debe dar `> 0`):
  ```bash
  grep -cE "ENUM_CAPITAL_MODE|InpCapitalMode|EffectiveBaseCapital|InpBaseCapitalPct" "trabajador multichart.mq5"
  ```
- Sección de estado virtual del panel presente (debe dar `> 0`):
  ```bash
  grep -cE "MPVirtStratLine|MPDrawVirtualState|falta %d|VIRTUAL → LIVE" "trabajador multichart.mq5"
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
3. En MT5: arrastra el EA al gráfico; en Inputs debe aparecer `ESTRATEGIA ÚNICA: ESTRUCTURA LÍNEAS H1 + CONFLUENCIA M3`, `PANEL MULTI-PAR (TESTER VISUAL + GRÁFICO REAL)` y `PARAMETROS MOTOR DE LINEAS`.
4. Verás en el gráfico las líneas L1-L4 del TF (azules/magenta/rojo) y, con la confluencia activa, el rango H1 naranja con su 50% dorado, las zonas verde (compra) y roja (venta), y la entrada 50% M3 cuando se congele. Arriba a la derecha, el **PANEL MULTI-PAR** con la tabla de todos los pares y sus mini-gráficos. En el tester, activa el **modo visual** para verlas.

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
