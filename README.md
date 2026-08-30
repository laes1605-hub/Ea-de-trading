# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.31** (estrategia PERSONAL de líneas).

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador multichart.mq5` | Código fuente del EA (se compila en MetaEditor). |
| `ea.txt` | Copia en texto plano del mismo archivo (sin BOM). |
| `smc2.mq5` | EA visual SMC independiente (motor de líneas L1-L4, OB y FVG) — referencia de la lógica portada. |

## Estrategia (v8.31 — solo la PERSONAL)

**LINEAS** — lógica de las 4 líneas de `smc2.mq5`, operativa con la **gestión de riesgo integrada** (virtual → LIVE, tabla de 20 niveles, SL/TP 1:3).

- Entra en el *trigger*: cierre por encima de **L1** (compra) o por debajo de **L2** (venta) con la zona de reacción **L3/L4** activa.
- Las estrategias antiguas **SMC (CHoCH), FVG y OB-H1 fueron eliminadas**; ya no aparecen en Inputs ni en el panel ESTRAT.
- Parámetro: `InpUsePersonal` (única estrategia, por defecto `true`) y `InpLookbackBars=300`.

### Motor de estructura (las 4 líneas)

- **L1/L2** = máximo/mínimo de `InpLookbackBars` velas; **EQ** = punto medio. **Bias** = color de la última vela cerrada.
- **L3/L4** = zona de reacción activada por vela contraria dentro del rango; se extienden con el precio.
- **Trigger** = cierre más allá de L1/L2 con L3/L4 activos → swap al cierre siguiente.

## Líneas visibles en el gráfico

Las líneas ahora **se marcan con colores vivos y etiqueta con nombre + precio** (antes eran grises casi invisibles y no se dibujaban en el Strategy Tester):

| Línea | Color | Estilo | Significado |
|---|---|---|---|
| `D1 L1` / `D1 L2` | 🟠 Naranja | Sólida, grosor 3 | Máximo/mínimo diario |
| `D1 EQ` | Gris | Punteada | Equilibrio D1 |
| `L1` / `L2` | 🔵 Azul (DodgerBlue) | Sólida, grosor 2 | Máximo/mínimo del TF del gráfico |
| `EQ` | Gris | Punteada | Equilibrio del TF |
| `L3` | 🟣 Magenta | Discontinua, grosor 2 | Techo de la zona de reacción (activa) |
| `L4` | 🔴 Rojo | Discontinua, grosor 2 | Suelo de la zona de reacción (activa) |

- Se dibujan en el gráfico **en vivo y también en el Strategy Tester (modo visual)**.
- Etiqueta al lado derecho de cada línea con su nombre y precio (ej. `L1  1.08452`).
- Input `InpShowStructureLines=true` para activar/desactivar el dibujado.
- L3/L4 solo aparecen cuando la zona de reacción está activa (así funciona el motor).

\* Con RR 1:3 el punto de equilibrio es ~25% de aciertos (más costos ≈ 27–30%), así que un win rate del 40% ya da expectativa positiva. Mide con **profit factor** (>1.5 sólido, >2.0 excelente) y **máximo drawdown**, no solo el win rate.

## Gestión de riesgo (intacta)

- **Tabla de riesgo de 20 niveles** (`InpRiskStep1..20`, % de la base): cada pérdida sube de nivel (CR) y aumenta el lote; cada ganancia resetea a nivel 1.
- **Sistema virtual → LIVE**: la estrategia opera en simulación (CV) y pasa a dinero real al alcanzar `InpXActivacion` pérdidas virtuales.
- **SL/TP con gestión 1:2**: SL a `InpSL_Points` (95), TP a `InpTP_Points` (305) → RR ≈ 1:3.2; con activación de SL protegido (`InpActivationPoints=210` / `InpProtectedSL=205`).
- **Circuit breaker diario** (`InpMaxDailyLossPct=4.5%`), **base dinámica de capital**, **split de lotes**, **filtro de horario**, hasta 20 símbolos con SL/TP propios.
- Panel gráfico en MT5 (Operar / Cuenta / Posic. / Config / Estrat).

## Cómo probar

1. Estrategia Tester: elige símbolo + timeframe (las señales se calculan en el TF del gráfico), cuenta demo. **Marca "Modo visual"** para ver las líneas.
2. En el log: `vOPEN` (simulación), `LIVE`, `CV/CR`, `CIRCUIT BREAKER`.
3. Métricas: profit factor, win rate, nº de trades, **máximo drawdown** (crítico por la tabla de riesgo).

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
- Una sola estrategia (debe dar `1`):
  ```bash
  grep -c "STRAT_COUNT      1" "trabajador multichart.mq5"
  ```

### 2) En MetaTrader 5 (funcional)

1. Abre **MetaEditor** → `Archivo > Abrir datos > MQL5 > Experts` → pega `trabajador multichart.mq5`.
2. Pulsa **F7 (Compilar)**: debe compilar sin errores.
3. En MT5: arrastra el EA al gráfico; en Inputs debe aparecer `ESTRATEGIA PERSONAL (LÍNEAS L1-L4, RR 1:3)` con `InpUsePersonal=true` y `PARAMETROS MOTOR DE LINEAS`.
4. Verás en el gráfico las líneas de estructura con etiqueta (D1 naranja gruesas, L1/L2 azules, EQ gris punteada, L3/L4 discontinuas cuando la zona está activa). En el tester, activa el **modo visual** para verlas.

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
