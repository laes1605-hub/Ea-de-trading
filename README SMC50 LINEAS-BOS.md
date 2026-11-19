# SMC50 — Líneas L1-L4 + BOS/CHoCH dentro del 50% (visual para Exness)

Indicador **visual** para MetaTrader 5 (sirve en la terminal de **Exness**).
Pone en el gráfico la **lógica de líneas** del EA y el **reconocimiento de BOS y CHoCH**,
con cada etiqueta **anclada dentro del 50% de la estructura**.

> **No opera.** Solo dibuja y avisa. Puede ir en el **mismo gráfico que el EA**
> (los indicadores no interfieren con los EAs) y funciona aunque el
> trading algorítmico esté desactivado.

Archivos: `SMC_Lineas_BOS50.mq5` (+ copia `SMC_Lineas_BOS50.txt`).

## Qué dibuja

| Elemento | Color / estilo | Significado |
|---|---|---|
| `L1` / `L2` (TF del gráfico) | Azul, gruesa | Techo / suelo del rango |
| `50%` (TF del gráfico) | Dorada, punteada | **50% de la estructura** (EQ) |
| `L3` / `L4` | Magenta / roja, discontinuas | Reacción activa (solo con vela contraria cerrada) |
| Zona `DESCUENTO` | Rectángulo verde | Debajo del 50% (zona de compra) |
| Zona `PREMIUM` | Rectángulo rojo | Encima del 50% (zona de venta) |
| `L1` / `L2` / `50%` H1 | Naranja / dorada discontinua | Estructura madre (overlay, configurable) |
| `[M15] BOS ALC 50%=...` | Verde (alc) / tomate (baj) | Ruptura de **continuación**, etiqueta en el 50% |
| `[M15] CHoCH BAJ 50%=...` | Azul (alc) / naranja (baj) | **Cambio** de estructura, etiqueta en el 50% |
| Línea corta punteada | Mismo color de la marca | **50% del tramo** del rompimiento (= entrada del EA) |
| Panel superior izquierdo | Fondo oscuro | Bias, fase, niveles y últimos BOS/CHoCH |

Al adjuntarlo se **reproducen las últimas 300 velas** para mostrar los BOS/CHoCH
pasados; los nuevos aparecen al cierre de cada vela.

## Lógica (idéntica al EA v8.56+)

- `L1`/`L2` solo se mueven **al cierre** (mechas incluidas); `L3`/`L4` al **tick**.
- `L3`/`L4` se activan **solo con vela cerrada contraria** al bias.
- **CHoCH** = rompimiento `L3>L1` / `L4<L2` que **cambia** el bias (consolida al cierre).
- **BOS** = rompimiento de **continuación** (mismo bias): cierre más allá de
  `RefLevel`, o commit en la dirección del bias.
- Cada rompimiento guarda su **tramo**; el **50% del tramo** es el nivel de la
  LIMIT del EA, y la etiqueta se ancla al **50% de la estructura (EQ)** vigente
  al momento del evento (`InpAnchorAt50=false` la ancla al 50% del tramo).

## Instalación en la terminal de Exness (MT5)

1. En MT5: **Archivo → Abrir carpeta de datos → MQL5 → Indicators**.
2. Copia ahí `SMC_Lineas_BOS50.mq5`.
3. Abre MetaEditor (**F4**), localiza el archivo y pulsa **F7** (compilar).
   Debe decir `0 errors`.
4. En MT5, arrastra `SMC_Lineas_BOS50` desde **Navegador → Indicadores** al gráfico.
   Sin configurar nada ya se ven líneas, zonas, marcas y panel.

### Dónde ver los avisos BOS/CHoCH

Cada rompimiento se registra en el diario del terminal:

- **Caja de herramientas → Expertos**: líneas `SMC50 [XAUUSD,M15][TF] BOS ALCISTA ...`.
- Opcional: `InpUseAlert=true` para ventana emergente en cada evento.

## Inputs principales

| Input | Efecto |
|---|---|
| `InpLookbackBars` | Velas para L1/L2 e historial de marcas (mín. 50) |
| `InpUseTF2` / `InpTF2` | Estructura madre superpuesta (por defecto H1) |
| `InpShowLines` / `InpShowEQ50` / `InpShowZones` | Líneas L1-L4 / línea 50% / zonas |
| `InpShowBOS` / `InpShowCHoCH` | Marcas BOS / CHoCH |
| `InpAnchorAt50` | `true` = etiquetas **dentro del 50%** de la estructura; `false` = en el 50% del tramo |
| `InpShowLeg50` / `InpLegBars` | Línea del 50% del tramo y su largo |
| `InpMaxMarks` | Marcas visibles por TF (1-100) |
| `InpShowDashboard` / `InpDashX` / `InpDashY` | Panel y posición |
| `InpLogTerminal` / `InpUseAlert` | Aviso en Expertos / alerta emergente |

## Notas

- Si el gráfico está en H1 y la madre también es H1, se muestra una sola estructura.
- Los objetos usan el prefijo `SMC50_` y se borran solos al quitar el indicador.
- La comprobación de la lógica sin MetaTrader sigue en `python3 sim_bos_choch.py`.
