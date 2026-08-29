# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.20**.

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador multichart.mq5` | Código fuente del EA (se compila en MetaEditor). |
| `ea.txt` | Copia en texto plano del mismo archivo (sin BOM). |

## Estrategias incluidas (v8.20)

Todas operan con la **gestión de riesgo integrada** (virtual → LIVE, tabla de 20 niveles, SL/TP 1:3).
Se activan/desactivan en Inputs. **Para validar una sola, deja solo su input en `true` y prueba en el Strategy Tester.**

| # | Nombre | Regla | Parámetros | WR típico* |
|---|---|---|---|---|
| 1 | **TREND-RT** | Retroceso de tendencia: EMA rápida > lenta; el precio retrocede bajo la EMA rápida y la recupera | `InpTR_EmaFast=20`, `InpTR_EmaSlow=50` | 35–45% |
| 2 | **BO-RT** | Ruptura del rango de N velas con volumen + retest del nivel roto | `InpBR_Bars=10`, `InpBR_VolMult=1.5`, `InpBR_RetestTol=10` | 35–45% |
| 3 | **S/R-FLIP** | Ruptura de máximo/mínimo fractal y retest (flip de soporte/resistencia) | `InpSRF_Lookback=40`, `InpSRF_Tol=10` | 35–45% |
| 4 | **MOM-ADX** | ADX alto y creciente + cierre por encima/debajo del extremo de N velas | `InpMO_AdxPeriod=14`, `InpMO_AdxMin=25`, `InpMO_SwingBars=10` | 35–45% |
| 5 | **PERSONAL** | Tu estrategia (pendiente de definir en `CheckPersonalSignal()`) | `InpUsePersonalStrategy` | — |

\* Rangos típicos para estrategias de tendencia con RR 1:3 (**no garantizados** — hay que validarlos en tu broker). Con RR 1:3 el punto de equilibrio es ~25% de aciertos (más costos ≈ 27–30%), así que un win rate del 40% ya da expectativa positiva (~+0.8R por trade). Mide con **profit factor** (>1.5 sólido, >2.0 excelente) y **máximo drawdown**, no solo el win rate.

## Gestión de riesgo (intacta)

- **Tabla de riesgo de 20 niveles** (`InpRiskStep1..20`, % de la base): cada pérdida sube de nivel (CR) y aumenta el lote; cada ganancia resetea a nivel 1.
- **Sistema virtual → LIVE**: la estrategia opera en simulación (CV) y pasa a dinero real al alcanzar `InpXActivacion` pérdidas virtuales.
- **SL/TP con gestión 1:2**: SL a `InpSL_Points` (95), TP a `InpTP_Points` (305) → RR ≈ 1:3.2; con activación de SL protegido (`InpActivationPoints=210` / `InpProtectedSL=205`).
- **Circuit breaker diario** (`InpMaxDailyLossPct=4.5%`), **base dinámica de capital**, **split de lotes**, **filtro de horario**, hasta 20 símbolos con SL/TP propios.
- Panel gráfico en MT5 (Operar / Cuenta / Posic. / Config / Estrat).

## Cómo probar una estrategia

1. En Inputs del EA, activa **solo una** estrategia (ej. `InpUseTrendRetrace=true` y las demás `false`).
2. Estrategia Tester: elige símbolo + timeframe (las señales se calculan en el TF del gráfico), cuenta demo.
3. Revisa en el log: `vOPEN` (simulación), `LIVE`, `CV/CR`, `CIRCUIT BREAKER`.
4. Métricas: profit factor, win rate, nº de trades, **máximo drawdown** (crítico por la tabla de riesgo).

## Verificación

### 1) En el repositorio (Git)

```bash
git status                          # working tree limpio = todo commiteado
git log --oneline -3                # el último commit debe ser el v8.20
git show --stat HEAD                # archivos modificados y nº de líneas
git ls-remote origin                # la rama debe aparecer en GitHub
```

- Rama de trabajo: `arena/01a04bc9-ea-de-trading`
- Estrategias nuevas presentes (debe dar `> 0`):
  ```bash
  grep -cE "CheckTrendRetraceSignal|CheckBreakoutSignal|CheckSRFlipSignal|CheckMomentumSignal" "trabajador multichart.mq5"
  ```
- Referencias eliminadas (estrategias viejas) → debe dar `0`:
  ```bash
  grep -cE "InpUseEMA|STRAT_EMA|InpPA_|InpSR_|InpBO_|signalInited" "trabajador multichart.mq5"
  ```

### 2) En MetaTrader 5 (funcional)

1. Abre **MetaEditor** → `Archivo > Abrir datos > MQL5 > Experts` → pega `trabajador multichart.mq5`.
2. Pulsa **F7 (Compilar)**: debe compilar sin errores ni warnings relevantes.
3. En MT5: `Navegador > Asesores Expertos` → arrastra el EA al gráfico y revisa la pestaña **Inputs**:
   deben aparecer los grupos `ESTRATEGIAS PARA PROBAR (RR 1:3)` y los parámetros de cada una.
4. Para probar la lógica: **View > Strategy Tester** con el EA, un símbolo de `InpSymbol1..20`,
   y revisa en el log los mensajes `vOPEN`, `LIVE`, `CV/CR` y `CIRCUIT BREAKER`.

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
