# Ea-de-trading

EA de trading para **MetaTrader 5** (MQL5) — `EA_GestionCuantitativa.mq5` **v8.10**.

## Archivos

| Archivo | Descripción |
|---|---|
| `trabajador multichart.mq5` | Código fuente del EA (se compila en MetaEditor). |
| `ea.txt` | Copia en texto plano del mismo archivo (sin BOM). |

## Estado actual (v8.10)

- Se eliminaron las 6 estrategias antiguas (EMA, Price Action, Fractales, S/R, Pivots, Breakout).
- Queda **una única estrategia personal** (`STRAT_PERSONAL`), cuya lógica de entrada se implementa
  en la función **`CheckPersonalSignal()`** dentro del archivo.
  - Debe devolver `+1` (compra), `-1` (venta) o `0` (sin señal).
  - Se evalúa 1 vez por cada **nueva vela** y por cada símbolo configurado.

## Gestión de riesgo (intacta)

- **Tabla de riesgo de 20 niveles** (`InpRiskStep1..20`, % de la base): cada pérdida sube de nivel (CR) y aumenta el lote; cada ganancia resetea a nivel 1.
- **Sistema virtual → LIVE**: la estrategia opera en simulación (CV) y pasa a dinero real al alcanzar `InpXActivacion` pérdidas virtuales.
- **SL/TP con gestión 1:2**: SL a `InpSL_Points`, TP a `InpTP_Points`; con activación de SL protegido (`InpActivationPoints` / `InpProtectedSL`).
- **Circuit breaker diario**: si la pérdida del día supera `InpMaxDailyLossPct`, cierra todo y pausa hasta el día siguiente.
- **Base dinámica de capital** (`InpBaseCapital`), **split de lotes** y **filtro de horario**.
- Multisímbolo: hasta 20 símbolos (`InpSymbol1..20`) con SL/TP propios por símbolo.
- Panel gráfico en MT5 (Operar / Cuenta / Posic. / Config / Estrat).

## Cómo verificar los cambios

### 1) En el repositorio (Git)

```bash
git status                          # working tree limpio = todo commiteado
git log --oneline -3                # el último commit debe ser el v8.10
git show --stat HEAD                # archivos modificados y nº de líneas
git ls-remote origin                # la rama debe aparecer en GitHub
```

- Rama de trabajo: `arena/01a04bc9-ea-de-trading`
- Referencias eliminadas (estrategias viejas) → debe dar `0`:
  ```bash
  grep -cE "InpUseEMA|STRAT_EMA|InpPA_|InpSR_|InpBO_|CalcPivots|signalInited" "trabajador multichart.mq5"
  ```
- Referencias de gestión de riesgo → debe dar `> 0`:
  ```bash
  grep -cE "InpRiskStep1|InitRiskTable|CalcLotByRisk|CheckCircuitBreaker|CheckPersonalSignal" "trabajador multichart.mq5"
  ```

### 2) En MetaTrader 5 (funcional)

1. Abre **MetaEditor** → `Archivo > Abrir datos > MQL5 > Experts` → pega `trabajador multichart.mq5`.
2. Pulsa **F7 (Compilar)**: debe compilar sin errores ni warnings relevantes.
3. En MT5: `Navegador > Asesores Expertos` → arrastra el EA al gráfico y revisa la pestaña **Inputs**:
   debe mostrar `ESTRATEGIA PERSONAL` (`InpUsePersonalStrategy`) y la **TABLA DE RIESGO (20 niveles)**.
4. Para probar la lógica: **View > Strategy Tester** con el EA, un símbolo de `InpSymbol1..20`,
   y revisa en el log los mensajes `vOPEN`, `LIVE`, `CV/CR` y `CIRCUIT BREAKER`.

## ⚠️ Advertencia

La tabla de riesgo llega al **2.414% de la base en el nivel 20**. En modo LIVE, una racha larga de
pérdidas puede destruir la cuenta (*blow-up*). Revisa la tabla, `InpMaxDailyLossPct` y `InpXActivacion`
antes de usarlo con dinero real.
