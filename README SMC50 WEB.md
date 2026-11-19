# SMC50-WEB — Líneas + BOS/CHoCH dentro del 50% para usar junto a Exness Terminal

App web (carpeta `smc50-web/`) que muestra la **lógica de líneas L1-L4** del EA y el
**reconocimiento de BOS y CHoCH dentro del 50% de la estructura**, en vivo y sin
instalar nada.

> **Por qué una app web:** la terminal web de Exness **no permite instalar
> indicadores ni EAs personalizados** (lo confirma la ayuda oficial de Exness:
> *"Custom (third-party) indicators cannot be installed on either Exness Trade
> or Exness Terminal"*). La forma de ver esta lógica junto a Exness es abrir
> esta app en una pestaña al lado (o media pantalla cada una) con el mismo
> símbolo y temporalidad.

> **No opera.** Solo visualiza y avisa. Sin servidor, sin instalación, sin
> build: son 6 archivos estáticos (`index.html`, `styles.css`, `engine.js`,
> `data.js`, `chart.js`, `app.js`).

## Qué muestra

- **Velas + líneas L1/L2/L3/L4** del TF principal y **línea del 50% (EQ)**.
- **Zonas premium/descuento** (encima/debajo del 50%).
- **Estructura madre** superpuesta (H1 por defecto): sus líneas L1/L2/50% y sus
  marcas BOS/CHoCH.
- Cada **BOS** (continuación) y **CHoCH** (cambio) como etiqueta
  `[M15] BOS ALC 1.08520` **anclada al 50% de la estructura** vigente al
  momento del evento, más la **línea corta del 50% del tramo** (= nivel de
  entrada del EA).
- **Panel lateral**: bias, fase, niveles, conteo y últimos BOS/CHoCH por TF.
- **Terminal de eventos** con fecha/hora y precios + **sonido** y
  **notificación de navegador** opcionales en cada evento nuevo.
- Gráfico interactivo: zoom (rueda/botones), arrastre para mover, doble clic
  para volver al vivo, crosshair con OHLC.

## Lógica (idéntica al EA v8.56)

`engine.js` es un port 1:1 del motor (`trabajador multichart.mq5` /
`sim_bos_choch.py`): L1/L2 al cierre, L3/L4 al tick tras vela contraria,
CHoCH por commit con cambio de bias, BOS por cierre más allá de `RefLevel` o
commit a favor, tramo en `LastHigh/LastLow` y su 50%.

Verificado con 24 pruebas en Node (`engine.js` + `data.js`): reproduce exacto
los escenarios del simulador Python (tramo BOS `[1.08930..1.09005]`,
50% = `1.089675`, CHoCH alcista, agregación M1→M3, etc.).

## Datos en vivo

| Símbolos | Fuente | ¿Necesita key? |
|---|---|---|
| Cripto (BTCUSD, ETHUSD…) | Binance (público) | No — funciona al abrir |
| Forex, oro/plata, índices, petróleo | TwelveData | Sí, gratuita (ver abajo) |
| Probar sin internet | Generador demo incluido | No |

**API key gratuita de TwelveData (1 minuto):** entra a `twelvedata.com` →
*Get free API key* → crea la cuenta → pega la key en la app → Conectar. La key
se guarda **solo en tu navegador** (localStorage), nunca sale a otro servidor.
El plan gratis da ~800 consultas/día: con actualización cada 20s (≈6/min, TF +
madre) alcanza para unas 2 horas diarias por símbolo; para más tiempo usa 60s.

Símbolos: escríbelos como en Exness (`XAUUSD`, `EURUSD`, `US30`, `NAS100`,
`BTCUSD`…). La app los traduce sola al formato de cada fuente.

## Cómo usarla

1. Abre `smc50-web/index.html`: con doble clic funciona (los datos se piden
   directo desde tu navegador), o sírvela con `python3 -m http.server` en esa
   carpeta, o súbela a cualquier hosting estático (GitHub Pages, Netlify…).
2. Elige símbolo, TF principal (M1/M3/M5/M15/M30/H1/H4) y TF madre
   (OFF/M15/H1/H4/D1), y pulsa **Conectar**.
3. Pon el **mismo símbolo y TF en Exness Terminal** al lado y opera manual
   allá con lo que ves aquí.

Horas en hora local de tu equipo. M3 en TwelveData se construye agregando
velas de 1 minuto (TwelveData no ofrece M3 nativo).
