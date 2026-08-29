# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.30** (estrategias SMC).

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador multichart.mq5` | Código fuente del EA (se compila en MetaEditor). |
| `ea.txt` | Copia en texto plano del mismo archivo (sin BOM). |
| `smc2.mq5` | EA visual SMC independiente (motor de líneas L1-L4, OB y FVG) — referencia de la lógica portada. |

## Estrategias incluidas (v8.30)

Todas operan con la **gestión de riesgo integrada** (virtual → LIVE, tabla de 20 niveles, SL/TP 1:3).
Se activan/desactivan en Inputs. **Para validar una sola, deja solo su input en `true` y prueba en el Strategy Tester.**

| # | Nombre | Regla | Parámetros |
|---|---|---|---|
| 0 | **SMC** | Cambio de estructura (CHoCH): rompe L1 con bias bajista → compra; rompe L2 con bias alcista → venta | `InpLookbackBars=300` |
| 1 | **FVG** | Retest del último fair value gap H1 activo (filtrado por zona D1): la vela entra al gap y cierra sobre su piso/techo | `InpZoneScanBars=80` |
| 2 | **OB-H1** | Rebote en order block H1 (filtrado por D1): toca la zona y cierra a favor, como si rebotara en el bloque | `InpZoneScanBars=80` |
| 3 | **LINEAS** | Lógica de líneas de `smc2.mq5` portada al slot PERSONAL: entra en el *trigger* (cierre sobre L1 o bajo L2 con L3/L4 activos). Además **dibuja en el gráfico** las líneas D1 y del TF (L1, L2, EQ, L3, L4) | `InpLookbackBars=300` |

### Motor de estructura (común a las 4)

- **L1/L2** = máximo/mínimo de `InpLookbackBars` velas; **EQ** = punto medio. **Bias** = color de la última vela cerrada.
- **L3/L4** = zona de reacción activada por vela contraria dentro del rango; se extienden con el precio.
- **CHoCH** = cambio de bias al romper L1/L2. **Trigger** = cierre más allá de L1/L2 con L3/L4 activos → swap al cierre siguiente.
- **Order blocks H1**: vela roja con mecha bajo el EQ de D1 (discount) → OB alcista; vela verde sobre EQ (premium) → OB bajista. Se invalidan al romperse.
- **FVG H1**: hueco de 3 velas filtrado por zona D1; se invalida al cubrirse.

\* Con RR 1:3 el punto de equilibrio es ~25% de aciertos (más costos ≈ 27–30%), así que un win rate del 40% ya da expectativa positiva. Mide con **profit factor** (>1.5 sólido, >2.0 excelente) y **máximo drawdown**, no solo el win rate.

## Gestión de riesgo (intacta)

- **Tabla de riesgo de 20 niveles** (`InpRiskStep1..20`, % de la base): cada pérdida sube de nivel (CR) y aumenta el lote; cada ganancia resetea a nivel 1.
- **Sistema virtual → LIVE**: la estrategia opera en simulación (CV) y pasa a dinero real al alcanzar `InpXActivacion` pérdidas virtuales.
- **SL/TP con gestión 1:2**: SL a `InpSL_Points` (95), TP a `InpTP_Points` (305) → RR ≈ 1:3.2; con activación de SL protegido (`InpActivationPoints=210` / `InpProtectedSL=205`).
- **Circuit breaker diario** (`InpMaxDailyLossPct=4.5%`), **base dinámica de capital**, **split de lotes**, **filtro de horario**, hasta 20 símbolos con SL/TP propios.
- Panel gráfico en MT5 (Operar / Cuenta / Posic. / Config / Estrat).

## Cómo probar una estrategia

1. En Inputs del EA, activa **solo una** estrategia (ej. `InpUseSMC=true` y las demás `false`).
2. Estrategia Tester: elige símbolo + timeframe (las señales se calculan en el TF del gráfico; los OB/FVG usan H1 y el filtro D1), cuenta demo.
3. Revisa en el log: `vOPEN` (simulación), `LIVE`, `CV/CR`, `CIRCUIT BREAKER`.
4. Métricas: profit factor, win rate, nº de trades, **máximo drawdown** (crítico por la tabla de riesgo).

## Verificación

### 1) En el repositorio (Git)

```bash
git status                          # working tree limpio = todo commiteado
git log --oneline -3
git show --stat HEAD
```

- Estrategias SMC presentes (debe dar `> 0`):
  ```bash
  grep -cE "CheckSMCSignal|CheckFVGSignal|CheckOBBounceSignal|SE_OnClose" "trabajador multichart.mq5"
  ```
- Estrategias viejas eliminadas (debe dar `0`):
  ```bash
  grep -cE "CheckTrendRetraceSignal|CheckBreakoutSignal|CheckSRFlipSignal|CheckMomentumSignal|InpUseTrendRetrace" "trabajador multichart.mq5"
  ```

### 2) En MetaTrader 5 (funcional)

1. Abre **MetaEditor** → `Archivo > Abrir datos > MQL5 > Experts` → pega `trabajador multichart.mq5`.
2. Pulsa **F7 (Compilar)**: debe compilar sin errores.
3. En MT5: arrastra el EA al gráfico; en Inputs deben aparecer `ESTRATEGIAS SMC (RR 1:3)` y `PARAMETROS MOTOR SMC`.
4. Con la estrategia **LINEAS** activa verás en el gráfico las líneas de estructura (D1 gruesas, TF finas, L3/L4 discontinuas).

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
