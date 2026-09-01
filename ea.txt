//+------------------------------------------------------------------+
//|                    EA_GestionCuantitativa.mq5                    |
//+------------------------------------------------------------------+
#property copyright "Gestión Cuantitativa EA"
#property version   "8.50"
#property strict

#include <Canvas\Canvas.mqh>   // panel MULTI-PAR (tester visual + gráfico real)

//+------------------------------------------------------------------+
//| MODO DE CAPITAL BASE (3 modos de gestión del capital)            |
//+------------------------------------------------------------------+
enum ENUM_CAPITAL_MODE
{
   CAP_MODE_DYNAMIC = 0,   // Dinámica: la base crece con los nuevos máximos del balance
   CAP_MODE_FIXED   = 1,   // Fija: la base de decisión no crece ni disminuye
   CAP_MODE_ACCOUNT = 2    // % cuenta: la base = % del balance actual de la cuenta
};

//+------------------------------------------------------------------+
//| INPUTS — GENERALES                                               |
//+------------------------------------------------------------------+
input group "=== ESTRATEGIA ÚNICA: ESTRUCTURA LÍNEAS H1 + CONFLUENCIA M3 ==="
input bool            InpUseConfluencia    = true;       // Activar la estrategia (estructura + confluencia)
input bool            InpAllowConfluOrders = true;       // Permitir órdenes (virtuales/LIVE)
input ENUM_TIMEFRAMES InpConfTFSuperior    = PERIOD_H1;  // TF estructura madre (bias + rango L1-L2 + zona 50%)
input ENUM_TIMEFRAMES InpConfTFEntrada     = PERIOD_M3;  // TF entrada (CHoCH a favor de H1 + 50% L1-L2 M3)
input bool            InpShowConfluencias  = true;       // Dibujar 50% H1 (zonas) y entrada 50% M3

input group "=== ESTRATEGIA 2: ZONA 4H (L1-L2 + 50%) + ORDER BLOCKS 1H ==="
input bool            InpUseStrat2       = true;       // Activar Estrategia 2 (zona 4H + OB 1H + órdenes virtual→LIVE)
input ENUM_TIMEFRAMES InpStrat2TF        = PERIOD_H4;  // TF de la zona: líneas L1-L2 y su 50%
input ENUM_TIMEFRAMES InpStrat2OBTF      = PERIOD_H1;  // TF de los order blocks dentro de la zona
input bool            InpStrat2ShowZone  = true;       // Dibujar zona 4H (L1-L2) + 50%
input bool            InpStrat2ShowOBs   = true;       // Dibujar order blocks 1H dentro de la zona
input int             InpStrat2MaxOBs    = 5;          // Máx. order blocks por lado (compra y venta)
input int             InpStrat2Lookback  = 150;        // Velas 1H a revisar para encontrar order blocks
input int             InpStrat2MinAge    = 10;         // Velas 1H mínimas de antigüedad de la zona para ser válida
input bool            InpAllowStrat2Orders=true;      // Permitir órdenes S2 (virtuales y LIVE)

input group "=== GESTIÓN AVANZADA 1:2 (GLOBAL / FALLBACK) ==="
input double InpSL_Points        = 95.0;
input double InpSL_Offset        = 0.0;
input double InpTP_Points        = 305.0;
input double InpActivationPoints = 210.0;
input double InpProtectedSL      = 205.0;
input bool   InpAutoFromLevel5   = true;   // 1:2 automático desde nivel 5 (lógica Asistente 3)

input group "=== FILTRO DE HORARIO ==="
input bool   InpUseTimeFilter    = false;
input int    InpStartHour        = 8;
input int    InpStartMinute      = 0;
input int    InpEndHour          = 20;
input int    InpEndMinute        = 0;

input group "=== CIERRE SEMANAL (VIERNES) ==="
input bool InpUseFridayClose       = true;  // Cerrar posiciones del EA el viernes antes del cierre
input int  InpFridayCloseHour      = 22;    // Hora del servidor a la que cierra el mercado el viernes (ajustar según broker)
input int  InpFridayCloseMinBefore = 30;    // Minutos antes del cierre para cerrar las posiciones

input group "=== TABLA DE RIESGO (% de Base) — 20 niveles ==="
input double InpRiskStep1        = 1.0;
input double InpRiskStep2        = 2.0;
input double InpRiskStep3        = 3.0;
input double InpRiskStep4        = 4.0;
input double InpRiskStep5        = 6.0;
input double InpRiskStep6        = 9.0;
input double InpRiskStep7        = 13.0;
input double InpRiskStep8        = 19.0;
input double InpRiskStep9        = 28.0;
input double InpRiskStep10       = 42.0;
input double InpRiskStep11       = 63.0;
input double InpRiskStep12       = 94.0;
input double InpRiskStep13       = 141.0;
input double InpRiskStep14       = 212.0;
input double InpRiskStep15       = 318.0;
input double InpRiskStep16       = 477.0;
input double InpRiskStep17       = 715.0;
input double InpRiskStep18       = 1073.0;
input double InpRiskStep19       = 1609.0;
input double InpRiskStep20       = 2414.0;

input group "=== MODO DE CAPITAL BASE (3 MODOS) ==="
input ENUM_CAPITAL_MODE InpCapitalMode   = CAP_MODE_DYNAMIC; // Modo: Dinámica (crece) / Fija / % de la cuenta
input double            InpBaseCapital    = 1000.0;          // Capital base (modos Dinámica y Fija)
input double            InpBaseCapitalPct = 12.0;            // % de la cuenta (solo modo "% cuenta")

input group "=== SPLIT DE LOTES ==="
input double InpMaxLotsPerOrder  = 100.0;
input int    InpSplitDelayMs     = 200;

input group "=== CIRCUIT BREAKER DIARIO ==="
input double InpMaxDailyLossPct  = 4.5;

input group "=== SÍMBOLOS (vacío = no usar) ==="
input string InpSymbol1          = "";
input string InpSymbol2          = "";
input string InpSymbol3          = "";
input string InpSymbol4          = "";
input string InpSymbol5          = "";
input string InpSymbol6          = "";
input string InpSymbol7          = "";
input string InpSymbol8          = "";
input string InpSymbol9          = "";
input string InpSymbol10         = "";
input string InpSymbol11         = "";
input string InpSymbol12         = "";
input string InpSymbol13         = "";
input string InpSymbol14         = "";
input string InpSymbol15         = "";
input string InpSymbol16         = "";
input string InpSymbol17         = "";
input string InpSymbol18         = "";
input string InpSymbol19         = "";
input string InpSymbol20         = "";

input group "=== SL/TP POR SÍMBOLO (0 = usar global) ==="
input double InpSym1_SL          = 0.0;
input double InpSym1_SLOffset    = 0.0;
input double InpSym1_TP          = 0.0;
input double InpSym1_Activation  = 0.0;
input double InpSym1_ProtSL      = 0.0;
input double InpSym2_SL          = 0.0;
input double InpSym2_SLOffset    = 0.0;
input double InpSym2_TP          = 0.0;
input double InpSym2_Activation  = 0.0;
input double InpSym2_ProtSL      = 0.0;
input double InpSym3_SL          = 0.0;
input double InpSym3_SLOffset    = 0.0;
input double InpSym3_TP          = 0.0;
input double InpSym3_Activation  = 0.0;
input double InpSym3_ProtSL      = 0.0;
input double InpSym4_SL          = 0.0;
input double InpSym4_SLOffset    = 0.0;
input double InpSym4_TP          = 0.0;
input double InpSym4_Activation  = 0.0;
input double InpSym4_ProtSL      = 0.0;
input double InpSym5_SL          = 0.0;
input double InpSym5_SLOffset    = 0.0;
input double InpSym5_TP          = 0.0;
input double InpSym5_Activation  = 0.0;
input double InpSym5_ProtSL      = 0.0;
input double InpSym6_SL          = 0.0;
input double InpSym6_SLOffset    = 0.0;
input double InpSym6_TP          = 0.0;
input double InpSym6_Activation  = 0.0;
input double InpSym6_ProtSL      = 0.0;
input double InpSym7_SL          = 0.0;
input double InpSym7_SLOffset    = 0.0;
input double InpSym7_TP          = 0.0;
input double InpSym7_Activation  = 0.0;
input double InpSym7_ProtSL      = 0.0;
input double InpSym8_SL          = 0.0;
input double InpSym8_SLOffset    = 0.0;
input double InpSym8_TP          = 0.0;
input double InpSym8_Activation  = 0.0;
input double InpSym8_ProtSL      = 0.0;
input double InpSym9_SL          = 0.0;
input double InpSym9_SLOffset    = 0.0;
input double InpSym9_TP          = 0.0;
input double InpSym9_Activation  = 0.0;
input double InpSym9_ProtSL      = 0.0;
input double InpSym10_SL         = 0.0;
input double InpSym10_SLOffset   = 0.0;
input double InpSym10_TP         = 0.0;
input double InpSym10_Activation = 0.0;
input double InpSym10_ProtSL     = 0.0;
input double InpSym11_SL         = 0.0;
input double InpSym11_SLOffset   = 0.0;
input double InpSym11_TP         = 0.0;
input double InpSym11_Activation = 0.0;
input double InpSym11_ProtSL     = 0.0;
input double InpSym12_SL         = 0.0;
input double InpSym12_SLOffset   = 0.0;
input double InpSym12_TP         = 0.0;
input double InpSym12_Activation = 0.0;
input double InpSym12_ProtSL     = 0.0;
input double InpSym13_SL         = 0.0;
input double InpSym13_SLOffset   = 0.0;
input double InpSym13_TP         = 0.0;
input double InpSym13_Activation = 0.0;
input double InpSym13_ProtSL     = 0.0;
input double InpSym14_SL         = 0.0;
input double InpSym14_SLOffset   = 0.0;
input double InpSym14_TP         = 0.0;
input double InpSym14_Activation = 0.0;
input double InpSym14_ProtSL     = 0.0;
input double InpSym15_SL         = 0.0;
input double InpSym15_SLOffset   = 0.0;
input double InpSym15_TP         = 0.0;
input double InpSym15_Activation = 0.0;
input double InpSym15_ProtSL     = 0.0;
input double InpSym16_SL         = 0.0;
input double InpSym16_SLOffset   = 0.0;
input double InpSym16_TP         = 0.0;
input double InpSym16_Activation = 0.0;
input double InpSym16_ProtSL     = 0.0;
input double InpSym17_SL         = 0.0;
input double InpSym17_SLOffset   = 0.0;
input double InpSym17_TP         = 0.0;
input double InpSym17_Activation = 0.0;
input double InpSym17_ProtSL     = 0.0;
input double InpSym18_SL         = 0.0;
input double InpSym18_SLOffset   = 0.0;
input double InpSym18_TP         = 0.0;
input double InpSym18_Activation = 0.0;
input double InpSym18_ProtSL     = 0.0;
input double InpSym19_SL         = 0.0;
input double InpSym19_SLOffset   = 0.0;
input double InpSym19_TP         = 0.0;
input double InpSym19_Activation = 0.0;
input double InpSym19_ProtSL     = 0.0;
input double InpSym20_SL         = 0.0;
input double InpSym20_SLOffset   = 0.0;
input double InpSym20_TP         = 0.0;
input double InpSym20_Activation = 0.0;
input double InpSym20_ProtSL     = 0.0;

input group "=== CONFIGURACIÓN PANEL ==="
input int    InpPanelX           = 20;
input int    InpPanelY           = 50;

input group "=== PANEL MULTI-PAR (TESTER VISUAL + GRÁFICO REAL) ==="
input bool   InpShowMultiPanel   = true;   // Panel organizado por par (tabla legible)
input bool   InpShowMiniCharts   = true;   // Mini-gráfico con líneas por par
input bool   InpMPChartsAll      = false;  // Mini-gráficos también de pares sin posición/limit
input int    InpMPBars           = 48;     // Velas del mini-gráfico (16-240)
input int    InpMPX              = 0;      // X del panel (0 = automático: esquina derecha)
input int    InpMPY              = 24;     // Y del panel
input bool   InpShowPosLines     = true;   // Líneas ENTRADA/SL/TP/LIMIT en el gráfico
input long   InpMagicNumber      = 123456;
input string InpComment          = "QA_EA";

input group "=== SISTEMA DE GESTIÓN (VIRTUAL → LIVE) ==="
input int    InpXActivacion      = 4;   // X pérdidas virtuales → la operación X+1 es LIVE
input int    InpTableSize        = 20;

input group "=== PARAMETROS MOTOR DE LINEAS ==="
input int    InpLookbackBars        = 300;  // velas para L1/L2 del motor
input bool   InpShowStructureLines  = true; // dibujar líneas L1/L2/EQ/L3/L4 en el gráfico


//+------------------------------------------------------------------+
//| CONSTANTES                                                       |
//+------------------------------------------------------------------+
#define MAX_SYMBOLS      20
#define STRAT2_MAX_OBS   5           // máx. order blocks VISIBLES por lado (compra/venta) de la Estrategia 2
#define STRAT2_STORED_OBS 20         // máx. order blocks guardados por símbolo (10 por lado)
#define MAX_TABLE_SIZE   20
#define PNL_W            520
#define PNL_H            660
#define TITLE_H          36
#define INFOBAR_H        52
#define SYMBAR_H         30
#define TAB_H            30
#define CONTENT_Y0       (TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H)
#define CONTENT_H        (PNL_H-CONTENT_Y0-6)
#define TAB_OPERAR       0
#define TAB_CUENTA       1
#define TAB_POSIC        2
#define TAB_CONFIG       3
#define TAB_ESTRAT       4
#define N_TABS           5
#define STRAT_COUNT      2
#define DRAG_ZONE        "GQP_DRAG"
#define GV_PREFIX        "GQP_"
#define OBJ_TITLE        "GQP_TITLE"
#define OBJ_IB_PL        "GQP_IB_PL"
#define OBJ_IB_EQ        "GQP_IB_EQ"
#define OBJ_IB_CV        "GQP_IB_CV"
#define OBJ_IB_CVMAX     "GQP_IB_CVMAX"
#define OBJ_IB_LOT       "GQP_IB_LOT"
#define OBJ_IB_CB        "GQP_IB_CB"
#define EDIT_PRICE_NAME  "GQP_EDITPRICE"
#define LINE_LIMIT_NAME  "GQP_LIMIT_LINE"
#define LINE_LIMIT_LABEL "GQP_LIMIT_LABEL"
#define LINE_LIMIT_SL    "GQP_LIMIT_SL"
#define LINE_LIMIT_TP    "GQP_LIMIT_TP"

//+------------------------------------------------------------------+
//| ENUMS                                                            |
//+------------------------------------------------------------------+
enum ENUM_STRATEGY_ID
{
   STRAT_CONFLUENCIA  = 0,   // Estrategia 1: estructura de líneas L1-L4 (H1) + apertura confluencia (M3)
   STRAT_S2           = 1    // Estrategia 2: OB + imbalance históricos (zona 4H) + CHoCH M3 + 50% M3
};

enum ENUM_STRUCTURE_BIAS
{
   BIAS_UNDEFINED =  0,
   BIAS_BULLISH   =  1,
   BIAS_BEARISH   = -1
};

enum ENUM_STRUCTURE_PHASE
{
   PHASE_CONTINUATION = 0,
   PHASE_REACTION     = 1,
   PHASE_TRIGGERED    = 2
};

//+------------------------------------------------------------------+
//| STRUCTS                                                          |
//+------------------------------------------------------------------+
struct SymbolParams
{
   string   name;
   bool     active;
   double   sl_points;
   double   sl_offset;
   double   tp_points;
   double   activation;
   double   protectedSL;
};

struct StrategyState
{
   bool     enabled;
   bool     isLive;
   int      CV;
   int      CV_Max;
   bool     virtualActive;
   int      virtualDir;
   double   virtualOpen;
   int      virtualOpenLevel;   // nivel del par al abrir la virtual (regla -3/-4)
   double   virtualSL_price;
   double   virtualTP_price;
   bool     virtualSLMoved;
   long     magicNumber;
   string   name;
   datetime lastBarTime;
   bool     cbPaused;
   int      cbPausedCV;
   int      liveLogicLevel;   // nivel de lógica heredado de la serie virtual al
                              // activar LIVE (ej. 5): la tabla arranca en 1,
                              // pero el 1:2 se aplica como si estuviera en ese nivel
};

struct StructureEngine
{
   double               L1, L2, L3, L4, EQ;
   bool                 L3L4_Active;
   int                  PendingBreakDir;
   ENUM_STRUCTURE_BIAS  Bias;
   ENUM_STRUCTURE_PHASE Phase;
   bool                 Valid;
   ENUM_TIMEFRAMES      TF;
};

//--- Zona de rebote de la Estrategia 2: order block + imbalance juntos.
//    COMPRA: última vela BAJISTA antes del impulso al alza, confirmada por
//    un FVG/imbalance (misma vela o grupo de 3). Zona = inicio del imbalance
//    → final del order block. VENTA: simétrico con la última vela ALCISTA.
//    El rectángulo se extiende a la derecha hasta que la zona se MITIGA:
//    la mitigación ocurre cuando el precio CRUZA el imbalance (no lo
//    respeta), no cuando toca el OB. Si no se ha mitigado, se extiende
//    hasta el momento actual.
//    FLUJO DE ENTRADA: 1) tocar la zona → Armed; 2) CHoCH M3 a favor del
//    rebote → 50% de L1-L2 M3 CONGELADO (EntryPrice) como la Estrategia 1.
struct Strat2OrderBlock
{
   bool     Active;
   bool     IsBullish;    // true = zona de COMPRA (demanda), false = VENTA (oferta)
   double   OBHigh, OBLow;      // la vela del order block
   datetime OBTime;             // apertura de la vela del OB
   double   ZoneTop, ZoneBottom;// zona marcada: inicio imbalance → final OB
   datetime GroupStart, GroupEnd; // rango temporal (vela inicial → final del grupo)
   bool     InRange;            // la zona está DENTRO del rango L1-L2 de 4H
   datetime FoundTime;          // para ordenar por cercanía (más reciente primero)
   bool     Mitigated;          // el precio CRUZÓ el imbalance (ya no lo respeta)
   datetime MitigateTime;       // momento exacto en que se cruzó el imbalance
   //--- flujo de entrada (confirmación CHoCH M3)
   bool     Armed;              // zona tocada → búsqueda de CHoCH M3 activa
   datetime ArmedTime;          // momento del toque
   bool     EntryFrozen;        // CHoCH a favor → 50% L1-L2 M3 congelado
   double   EntryPrice;         // nivel de entrada (50% M3) CONGELADO
   datetime EntryTime;          // momento en que se congeló
};

struct SymbolSystemState
{
   bool     hasLive;
   int      activeLiveStrategy;
   StrategyState strategies[STRAT_COUNT];
   StructureEngine SE;        // motor visual del TF del gráfico (solo dibujo)
   StructureEngine SE_H1;     // estructura madre: líneas L1-L4 en H1 (manda bias/rango/zona)
   StructureEngine SE_M3;     // estructura de entrada: líneas L1-L4 en M3 (CHoCH + 50%)
   datetime structLastBar;   // última vela del TF del gráfico procesada (solo dibujo)
   datetime h1LastBar;       // última vela del TF madre procesada
   datetime m3LastBar;       // última vela del TF de entrada procesada

   //--- estado de la ESTRATEGIA 2 (zona 4H + order blocks históricos)
   StructureEngine      SE_H4;          // estructura de la zona: líneas L1-L4 en 4H
   datetime             h4LastBar;      // última vela 4H procesada
   datetime             ob1hLastBar;    // última vela 1H procesada para order blocks
   Strat2OrderBlock     ob2[STRAT2_STORED_OBS]; // OB+imbalance detectados
   int                  ob2Count;       // total de zonas guardadas
   int                  ob2Buys;        // zonas de COMPRA HOY visibles (debajo del precio)
   int                  ob2Sells;       // zonas de VENTA HOY visibles (encima del precio)
   int                  ob2BuyRange;    // de las visibles, cuántas están DENTRO del rango 4H
   int                  ob2SellRange;   // de las visibles, cuántas están DENTRO del rango 4H
   bool                 ob2Outside;     // el precio está FUERA del rango (L1-L2) → OB externos activos
   int                  ob2Mitigated;   // zonas OB ya mitigadas (el precio ya las tocó)
   int                  ob2Armed;       // zonas tocadas → esperando CHoCH M3
   int                  ob2Frozen;      // zonas con 50% M3 congelado (entrada lista)

   //--- CHoCH de M3 para la ESTRATEGIA 2 (independiente del de la Estrategia 1)
   int      m3ChochDir2;    // CHoCH de M3 pendiente de procesar para Estrategia 2 (+1/-1)
   datetime m3ChochTime2;   // momento del CHoCH de M3 para Estrategia 2

   //--- estado de la ESTRATEGIA ÚNICA (estructura H1 + confluencia M3)
   int      m3ChochDir;      // CHoCH de M3 pendiente de procesar (+1/-1)
   datetime m3ChochTime;     // momento del CHoCH de M3
   bool     confArmedBuy;    // zona de compra H1 tocada → búsqueda de compras activa
   bool     confArmedSell;   // zona de venta H1 tocada → búsqueda de ventas activa
   datetime confArmBuyTime;  // momento del toque (los CHoCH cuentan desde aquí)
   datetime confArmSellTime;
   double   confEntryBuy;    // 50% del rango M3 CONGELADO en el CHoCH para compra (0 = ninguno)
   double   confEntrySell;   // 50% del rango M3 CONGELADO en el CHoCH para venta (0 = ninguno)
   bool     confWaitBuy;     // 50% congelado: espera que el precio quede por ENCIMA para colocar la LIMIT
   bool     confWaitSell;    // 50% congelado: espera que el precio quede por DEBAJO para colocar la LIMIT
   bool     confVPendBuy;    // orden limit VIRTUAL de compra activa
   double   confVPendBuyPrice;
   bool     confVPendSell;   // orden limit VIRTUAL de venta activa
   double   confVPendSellPrice;

   //--- estado de la ESTRATEGIA 2 (OB/imbalance 4H + CHoCH M3 + 50% M3)
   double   s2EntryBuy;      // 50% L1-L2 M3 CONGELADO para zona de COMPRA (0 = ninguno)
   double   s2EntrySell;     // 50% L1-L2 M3 CONGELADO para zona de VENTA (0 = ninguno)
   bool     s2WaitBuy;       // 50% congelado: espera que el precio quede por ENCIMA para colocar la LIMIT
   bool     s2WaitSell;      // 50% congelado: espera que el precio quede por DEBAJO para colocar la LIMIT
   bool     s2VPendBuy;      // orden limit VIRTUAL de compra activa
   double   s2VPendBuyPrice;
   bool     s2VPendSell;     // orden limit VIRTUAL de venta activa
   double   s2VPendSellPrice;
};

struct TradeRecord
{
   ulong    ticket;
   bool     isPending;
   int      orderType;
   double   lots;
   double   openPrice;
   double   sl, tp, profit;
   int      CR_level, CV_level;
   bool     advActive, slMoved;
   ulong    splitGroupId;
   bool     isManual;
   int      strategyId;
   int      symbolIdx;
};

struct ClosedSnap
{
   ulong    ticket;
   double   openPrice, sl, tp;
   int      CR_level, CV_level;
   bool     slMoved;
   int      orderType;
   long     dealReason;
   bool     isManual;
   int      strategyId;
   int      symbolIdx;
};

//+------------------------------------------------------------------+
//| GLOBALES                                                         |
//+------------------------------------------------------------------+
SymbolParams       g_Symbols[MAX_SYMBOLS];
int                g_SymCount        = 0;
int                g_PanelSymIdx     = 0;
SymbolSystemState  g_SysState[MAX_SYMBOLS];

double   g_BaseCapital             = 1000.0;
double   g_BaseMaxBalance          = 0.0;
//+------------------------------------------------------------------+
//| NIVEL POR PAR (lógica de gestión de riesgo de "Asistente 3")     |
//|                                                                  |
//| Un solo nivel 1..20 por PAR, compartido por sus estrategias:     |
//|   · PÉRDIDA            → nivel +1 (sube por la tabla)            |
//|   · GANANCIA limpia    → nivel 1                                 |
//|   · GANANCIA con SL protegido → nivel −3 (abierto en nivel <10)  |
//|                               o −4 (abierto en nivel ≥10)        |
//|   · 1:2 (SL protegido) automático en posiciones abiertas desde   |
//|     nivel ≥5 (InpAutoFromLevel5)                                 |
//| El lote sigue saliendo de la TABLA DE RIESGO (% de la base de    |
//| capital), que se mantiene igual — solo cambia cómo se calcula la |
//| base según el modo: DINÁMICA / FIJA / % CUENTA.                  |
//+------------------------------------------------------------------+
int g_PairLevel[MAX_SYMBOLS];

double   g_RiskTable[MAX_TABLE_SIZE];

double   g_DayStartEquity          = 0.0;
datetime g_DayStartTime            = 0;
bool     g_CircuitBreakerOn        = false;
datetime g_CircuitBreakerUntil     = 0;

TradeRecord  g_Trades[];
int          g_TradeCount          = 0;
int          g_ScrollOffset        = 0;
ClosedSnap   g_ClosedQueue[];
int          g_ClosedCount         = 0;

int      ActiveTab                 = TAB_OPERAR;
int      PNL_X, PNL_Y;
bool     g_Dragging                = false;
int      g_DragOffX                = 0;
int      g_DragOffY                = 0;
int      g_PanelTableSize          = 20;
int      g_SaveCounter             = 0;
datetime g_LastDiagTime            = 0;
double   g_LimitPrice              = 0.0;
bool     g_AdvancedMode            = false;
bool     g_PendingRebuild          = false;

string   TAB_NAMES[N_TABS];
string   PFX      = "GQP_";
string   PFX_OP   = "GQP_OP_";
string   PFX_ACC  = "GQP_ACC_";
string   PFX_POS  = "GQP_POS_";
string   PFX_CFG  = "GQP_CFG_";
string   PFX_EST  = "GQP_EST_";

string   GV_ADV_MODE, GV_LIMIT_PRICE, GV_PANEL_X, GV_PANEL_Y;

//+------------------------------------------------------------------+
//| FORWARD DECLARATIONS                                             |
//+------------------------------------------------------------------+
void RebuildPanel();
void RebuildActiveTab();
void UpdateInfoBar();
void DeletePanel();
void DeleteContentObjects();
void BuildTabOperar();
void BuildTabCuenta();
void BuildTabPosiciones();
void BuildTabConfig();
void BuildTabEstrategias();
void RefreshTabBar();
void SaveState();
void SaveStateToFile();
void SelectNextLiveStrategy(int si);
void Strat2Update(int si);
void Strat2DeleteObjects(int si);
void Strat2ResetState(int si);
void DrawStrat2(int si);
void UpdateStrat2Orders(int si);
void Strat2ManagePendings(int si);
void Strat2OnTradeClosed(int si);
void Strat2ProcessChoch(int si);
bool Strat2HasPending(int si);
void ActivateLiveStrategy(int si, int st);
void OnLiveSL_Original(int si, int st);
void OnLiveSL_Protected(int si, int st, int openLevel);
void OnLiveTP(int si, int st);
void CloseAllSymbolsPositions();
void ClosePosition(ulong ticket);
void UpdateLimitLine();
void RemoveLimitLine();
bool SendMarketOrderEx(int si, int st, ENUM_ORDER_TYPE ot, double lots, long magic);
void _SendLimitManual(int si, ENUM_ORDER_TYPE ot, double lots, double lp);

//+------------------------------------------------------------------+
//| HELPERS BÁSICOS                                                  |
//+------------------------------------------------------------------+
bool IsTester()
{ return(MQLInfoInteger(MQL_TESTER)==1||MQLInfoInteger(MQL_OPTIMIZATION)==1); }

bool IsTradeTimeAllowed()
{
   if(!InpUseTimeFilter) return true;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   int now=dt.hour*60+dt.min;
   int s=InpStartHour*60+InpStartMinute;
   int e=InpEndHour*60+InpEndMinute;
   return(s<=e)?(now>=s&&now<e):(now>=s||now<e);
}

bool IsAnyMagic(long magic)
{
   for(int si=0;si<g_SymCount;si++)
      for(int st=0;st<STRAT_COUNT;st++)
         if(magic==g_SysState[si].strategies[st].magicNumber) return true;
   for(int si=0;si<g_SymCount;si++)
      if(magic==InpMagicNumber+(long)(si*10)+9) return true;
   return false;
}

long GetStrategyMagic(int symIdx, int sid)
{
   //--- la estrategia única (confluencia) conserva el offset +1 que tenían
   //    las versiones anteriores: así se siguen gestionando las órdenes y
   //    posiciones LIVE ya existentes (no quedan huérfanas al actualizar).
   return InpMagicNumber+(long)(symIdx*10)+
          ((sid==STRAT_CONFLUENCIA)?1:((sid==STRAT_S2)?2:0));
}

long MagicManual(int symIdx)
{ return InpMagicNumber+(long)(symIdx*10)+9; }

//+------------------------------------------------------------------+
//| CIERRE SEMANAL (VIERNES)                                        |
//|   · Ventana: viernes (hora de cierre − minutos) hasta el lunes. |
//|   · Posiciones del EA se cierran automáticamente en la ventana. |
//|   · Pérdida al cierre → cuenta como SL (nivel +1, CV +1).       |
//|   · Ganancia al cierre → no suma ni quita: NIVEL y CV quedan    |
//|     iguales, la próxima operación abre con el mismo nivel.      |
//+------------------------------------------------------------------+
bool IsWeeklyCloseWindow(datetime t=0)
{
   if(t==0) t=TimeCurrent();
   MqlDateTime dt; TimeToStruct(t,dt);
   if(dt.day_of_week==6||dt.day_of_week==0) return true;          // sábado / domingo
   if(dt.day_of_week==5)                                          // viernes
   { int nowMin=dt.hour*60+dt.min;
     int closeMin=MathMax(0,InpFridayCloseHour*60-InpFridayCloseMinBefore);
     return nowMin>=closeMin; }
   return false;
}

void WeeklyCloseAllIfDue()
{
   if(!InpUseFridayClose)        return;
   if(!IsWeeklyCloseWindow())    return;
   for(int i=PositionsTotal()-1;i>=0;i--)
   { ulong t=PositionGetTicket(i); if(t==0) continue;
     if(!PositionSelectByTicket(t)) continue;
     if(!IsAnyMagic((long)PositionGetInteger(POSITION_MAGIC))) continue;
     string sym=PositionGetString(POSITION_SYMBOL);
     double pl=PositionGetDouble(POSITION_PROFIT);
     Print("CIERRE SEMANAL [",sym,"] #",t," PL=",DoubleToString(pl,2),
           (pl<0?" → se contará como SL":" → nivel intacto para la próxima operación"));
     ClosePosition(t);
   }
}

string GetStrategyName(int sid)
{
   switch(sid)
   { case STRAT_CONFLUENCIA:  return "CONFL";
     case STRAT_S2:           return "S2-OB";
     default:                 return "???"; }
}

int FindTrade(ulong ticket)
{ for(int i=0;i<g_TradeCount;i++) if(g_Trades[i].ticket==ticket) return i; return -1; }

bool IsTrailingActive(int si, int st)
{
   //--- lógica Asistente 3: el 1:2 (SL protegido) se activa con nivel
   //    del par >= 5 (InpAutoFromLevel5). Si la estrategia entró a LIVE
   //    desde una serie virtual que alcanzó el nivel >=5, la lógica se
   //    aplica como si estuviera en ese nivel (liveLogicLevel) aunque
   //    la tabla haya arrancado en 1.
   if(st>=0 && g_SysState[si].strategies[st].liveLogicLevel>=5)
      return(InpAutoFromLevel5);
   return(InpAutoFromLevel5 && PairLevel(si)>=5);
}

int ApplyRetroceso(int val, int ret)
{ return MathMax(1,val-ret); }

void UpdateCVMax(int si, int st)
{
   if(g_SysState[si].strategies[st].CV > g_SysState[si].strategies[st].CV_Max)
      g_SysState[si].strategies[st].CV_Max = g_SysState[si].strategies[st].CV;
}

//+------------------------------------------------------------------+
//| NIVEL POR PAR — reglas de progresión de "Asistente 3"            |
//|   pérdida → +1 · ganancia limpia → 1 · ganancia protegida → −3/−4|
//+------------------------------------------------------------------+
int PairLevel(int si)
{ return(g_PairLevel[si]); }

void PairLevelUp(int si)          // PÉRDIDA → nivel +1
{ g_PairLevel[si]=MathMin(g_PanelTableSize,g_PairLevel[si]+1); }

void PairLevelReset(int si)       // GANANCIA limpia → nivel 1
{ g_PairLevel[si]=1; }

void PairLevelBack(int si,int openLevel)   // GANANCIA con SL protegido
{
   int r=(openLevel<10)?3:4;      // −3 si se abrió en nivel <10, si no −4
   g_PairLevel[si]=MathMax(1,g_PairLevel[si]-r);
}

double GetPairLot(int si)
{ return CalcLotByRisk(si,PairLevel(si)); }

//+------------------------------------------------------------------+
//| PARÁMETROS POR SÍMBOLO                                           |
//+------------------------------------------------------------------+
double SymSL(int si)
{ if(si<0||si>=g_SymCount) return InpSL_Points;
  return(g_Symbols[si].sl_points>0)?g_Symbols[si].sl_points:InpSL_Points; }

double SymSLOffset(int si)
{ if(si<0||si>=g_SymCount) return InpSL_Offset;
  return(g_Symbols[si].sl_offset>0)?g_Symbols[si].sl_offset:InpSL_Offset; }

double SymTP(int si)
{ if(si<0||si>=g_SymCount) return InpTP_Points;
  return(g_Symbols[si].tp_points>0)?g_Symbols[si].tp_points:InpTP_Points; }

double SymActivation(int si)
{ if(si<0||si>=g_SymCount) return InpActivationPoints;
  return(g_Symbols[si].activation>0)?g_Symbols[si].activation:InpActivationPoints; }

double SymProtectedSL(int si)
{ if(si<0||si>=g_SymCount) return InpProtectedSL;
  return(g_Symbols[si].protectedSL>0)?g_Symbols[si].protectedSL:InpProtectedSL; }

//+------------------------------------------------------------------+
//| LOTAJE DINÁMICO                                                  |
//+------------------------------------------------------------------+
double PointValue(string symbol)
{
   double tickVal  = SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE);
   double point    = SymbolInfoDouble(symbol,SYMBOL_POINT);
   if(tickSize<=0) return tickVal;
   return tickVal*(point/tickSize);
}

double CalcLotByRisk(int si, int cr)
{
   if(si<0||si>=g_SymCount) return 0.01;
   int    lvl      = MathMax(1,MathMin(g_PanelTableSize,cr))-1;
   double riskPct  = g_RiskTable[lvl];
   double riskMoney= EffectiveBaseCapital()*riskPct/100.0;
   double slPts    = SymSL(si);
   double ptVal    = PointValue(g_Symbols[si].name);
   if(slPts<=0||ptVal<=0) return 0.01;
   double lots=riskMoney/(slPts*ptVal);
   double minL =SymbolInfoDouble(g_Symbols[si].name,SYMBOL_VOLUME_MIN);
   double maxL =SymbolInfoDouble(g_Symbols[si].name,SYMBOL_VOLUME_MAX);
   double stepL=SymbolInfoDouble(g_Symbols[si].name,SYMBOL_VOLUME_STEP);
   if(stepL>0) lots=MathFloor(lots/stepL)*stepL;
   lots=MathMax(minL,MathMin(maxL,lots));
   return NormalizeDouble(lots,2);
}

double GetLotByCR(int si, int cr)
{ return CalcLotByRisk(si,cr); }

//+------------------------------------------------------------------+
//| MODO DE CAPITAL BASE (DINÁMICA / FIJA / % CUENTA)               |
//|                                                                  |
//|   · DINÁMICA  → base = InpBaseCapital + nuevos máximos de balance|
//|   · FIJA      → base = InpBaseCapital (nunca crece ni disminuye) |
//|   · % CUENTA  → base = InpBaseCapitalPct% del balance actual     |
//| El lote siempre sale de la TABLA DE RIESGO aplicada a la base    |
//| efectiva del modo seleccionado.                                  |
//+------------------------------------------------------------------+
string CapitalModeName()
{
   if(InpCapitalMode==CAP_MODE_FIXED)   return "FIJA";
   if(InpCapitalMode==CAP_MODE_ACCOUNT) return StringFormat("%.1f%% CUENTA",MathMax(0.0,InpBaseCapitalPct));
   return "DINÁMICA";
}

double EffectiveBaseCapital()
{
   if(InpCapitalMode==CAP_MODE_FIXED)
      return MathMax(0.01,InpBaseCapital);
   if(InpCapitalMode==CAP_MODE_ACCOUNT)
   { double bal=AccountInfoDouble(ACCOUNT_BALANCE);
     double pct=MathMax(0.0,InpBaseCapitalPct);
     return (bal>0)?bal*pct/100.0:0.0; }
   return g_BaseCapital;
}

string BaseDisplay(bool withMax)
{
   string txt=StringFormat("%s  %.2f",CapitalModeName(),EffectiveBaseCapital());
   if(withMax) txt+=StringFormat("  (Bal.máx: %.2f)",g_BaseMaxBalance);
   return txt;
}

//+------------------------------------------------------------------+
//| BASE DINÁMICA (solo crece la base en modo DINÁMICA; en los       |
//| modos FIJA y % CUENTA la base efectiva se calcula al vuelo y     |
//| nunca se incrementa aquí. El máximo de balance se sigue          |
//| registrando para el panel en todos los modos).                   |
//+------------------------------------------------------------------+
void UpdateDynamicBase()
{
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   if(bal<=g_BaseMaxBalance) return;
   if(InpCapitalMode==CAP_MODE_DYNAMIC)
   { double inc=bal-g_BaseMaxBalance;
     g_BaseCapital+=inc;
     Print("Base actualizada: +",DoubleToString(inc,2),
           " → Base=",DoubleToString(g_BaseCapital,2)); }
   g_BaseMaxBalance=bal;
}

//+------------------------------------------------------------------+
//| CIRCUIT BREAKER                                                  |
//+------------------------------------------------------------------+
double GetDailyLossPct()
{
   if(g_DayStartEquity<=0) return 0.0;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   return MathMax(0.0,(g_DayStartEquity-eq)/g_DayStartEquity*100.0);
}

void ReactivatePausedStrategies()
{
   for(int si=0;si<g_SymCount;si++)
   { for(int st=0;st<STRAT_COUNT;st++)
     { if(!g_SysState[si].strategies[st].cbPaused) continue;
       g_SysState[si].strategies[st].cbPaused=false;
       g_SysState[si].strategies[st].CV=g_SysState[si].strategies[st].cbPausedCV;
       Print("CB reanudada");
       if(g_SysState[si].strategies[st].isLive)
       { g_SysState[si].hasLive=true;
         g_SysState[si].activeLiveStrategy=st;
         Print("Reactivando LIVE [",g_Symbols[si].name,"/",
               g_SysState[si].strategies[st].name,
               "] CV=",g_SysState[si].strategies[st].CV,
               " NIVEL par=",PairLevel(si)); } } }
}

void CheckDayReset()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   MqlDateTime ds; TimeToStruct(g_DayStartTime,ds);
   if(dt.day!=ds.day||dt.mon!=ds.mon||dt.year!=ds.year)
   { g_DayStartEquity=AccountInfoDouble(ACCOUNT_EQUITY);
     g_DayStartTime=TimeCurrent();
     Print("Nuevo día — Equity ref: ",DoubleToString(g_DayStartEquity,2));
     if(g_CircuitBreakerOn)
     { g_CircuitBreakerOn=false;
       Print("Circuit breaker LEVANTADO");
       ReactivatePausedStrategies();
       if(!IsTester()) RebuildPanel(); } }
}

void CheckCircuitBreaker()
{
   if(g_DayStartEquity<=0) return;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   double lossPct=(g_DayStartEquity-eq)/g_DayStartEquity*100.0;
   if(!g_CircuitBreakerOn&&lossPct>=InpMaxDailyLossPct)
   { g_CircuitBreakerOn=true;
     g_CircuitBreakerUntil=g_DayStartTime+86400;
     Print("⚠ CIRCUIT BREAKER — Pérdida: ",DoubleToString(lossPct,2),"%");
     CloseAllSymbolsPositions();
     for(int si=0;si<g_SymCount;si++)
     { for(int st=0;st<STRAT_COUNT;st++)
       { if(!g_SysState[si].strategies[st].enabled) continue;
         if(g_SysState[si].strategies[st].isLive)
         { g_SysState[si].strategies[st].cbPausedCV=g_SysState[si].strategies[st].CV;
           OnLiveSL_Original(si,st);
           g_SysState[si].strategies[st].isLive=false;
           g_SysState[si].strategies[st].cbPaused=true;
           g_SysState[si].hasLive=false;
           g_SysState[si].activeLiveStrategy=-1;
           Print("CB: LIVE pausada [",g_Symbols[si].name,"/",
                 g_SysState[si].strategies[st].name,"]"); } } }
     SaveState();
     if(!IsTester()) RebuildPanel(); }
}

//+------------------------------------------------------------------+
//| SL / TP                                                          |
//+------------------------------------------------------------------+
double CalcSL(string symbol, int si, double openPrice, int posType)
{
   int    dg =(int)SymbolInfoInteger(symbol,SYMBOL_DIGITS);
   double pt =SymbolInfoDouble(symbol,SYMBOL_POINT);
   double slP=SymSL(si)-SymSLOffset(si);
   if(posType==POSITION_TYPE_BUY||posType==ORDER_TYPE_BUY||
      posType==ORDER_TYPE_BUY_LIMIT||posType==ORDER_TYPE_BUY_STOP)
      return NormalizeDouble(openPrice-slP*pt,dg);
   return NormalizeDouble(openPrice+slP*pt,dg);
}

double CalcTP(string symbol, int si, double openPrice, int posType)
{
   int    dg =(int)SymbolInfoInteger(symbol,SYMBOL_DIGITS);
   double pt =SymbolInfoDouble(symbol,SYMBOL_POINT);
   double tpP=SymTP(si);
   if(posType==POSITION_TYPE_BUY||posType==ORDER_TYPE_BUY||
      posType==ORDER_TYPE_BUY_LIMIT||posType==ORDER_TYPE_BUY_STOP)
      return NormalizeDouble(openPrice+tpP*pt,dg);
   return NormalizeDouble(openPrice-tpP*pt,dg);
}

bool RestoreSLTP(ulong ticket, double sl, double tp)
{
   if(!PositionSelectByTicket(ticket)) return false;
   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action=TRADE_ACTION_SLTP; req.position=ticket;
   req.symbol=PositionGetString(POSITION_SYMBOL);
   req.sl=sl; req.tp=tp;
   if(!OrderSend(req,res)||res.retcode!=TRADE_RETCODE_DONE) return false;
   return true;
}

void EnforceSLTP()
{
   for(int i=0;i<PositionsTotal();i++)
   { ulong t=PositionGetTicket(i);
     if(t==0||!PositionSelectByTicket(t)) continue;
     string sym=PositionGetString(POSITION_SYMBOL);
     if(!IsAnyMagic((long)PositionGetInteger(POSITION_MAGIC))) continue;
     double cSL=PositionGetDouble(POSITION_SL);
     double cTP=PositionGetDouble(POSITION_TP);
     if(cSL!=0&&cTP!=0) continue;
     int symIdx=-1;
     for(int s=0;s<g_SymCount;s++) if(g_Symbols[s].name==sym){symIdx=s;break;}
     double op=PositionGetDouble(POSITION_PRICE_OPEN);
     int    ptype=(int)PositionGetInteger(POSITION_TYPE);
     int    k=FindTrade(t);
     double tSL,tTP;
     if(k>=0&&g_Trades[k].slMoved)
     { double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
       int    dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
       double psl=SymProtectedSL(symIdx);
       tSL=(ptype==POSITION_TYPE_BUY)?NormalizeDouble(op+psl*pt,dg):NormalizeDouble(op-psl*pt,dg);
       tTP=CalcTP(sym,symIdx,op,ptype); }
     else
     { tSL=CalcSL(sym,symIdx,op,ptype);
       tTP=CalcTP(sym,symIdx,op,ptype); }
     RestoreSLTP(t,(cSL==0)?tSL:cSL,(cTP==0)?tTP:cTP); }
}

//+------------------------------------------------------------------+
//| SPLIT                                                            |
//+------------------------------------------------------------------+
int CalcSplitCount(double lots)
{ return(lots<=InpMaxLotsPerOrder)?1:(int)MathCeil(lots/InpMaxLotsPerOrder); }

double CalcSplitLot(string symbol, double totalLots, int idx, int parts)
{
   double maxL=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MAX);
   double minL=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN);
   double stp =SymbolInfoDouble(symbol,SYMBOL_VOLUME_STEP);
   double cap =MathMin(InpMaxLotsPerOrder,maxL);
   double full=MathFloor(totalLots/cap);
   double rem =totalLots-full*cap;
   double lot =(idx<(int)full)?cap:((rem>0)?rem:cap);
   if(stp>0) lot=MathFloor(lot/stp)*stp;
   return NormalizeDouble(MathMax(lot,minL),2);
}

//+------------------------------------------------------------------+
//| INICIALIZACIÓN SÍMBOLOS                                          |
//+------------------------------------------------------------------+
void LoadSymbolInputParams()
{
   string names[MAX_SYMBOLS];
   names[0]=InpSymbol1;  names[1]=InpSymbol2;  names[2]=InpSymbol3;
   names[3]=InpSymbol4;  names[4]=InpSymbol5;  names[5]=InpSymbol6;
   names[6]=InpSymbol7;  names[7]=InpSymbol8;  names[8]=InpSymbol9;
   names[9]=InpSymbol10; names[10]=InpSymbol11; names[11]=InpSymbol12;
   names[12]=InpSymbol13;names[13]=InpSymbol14; names[14]=InpSymbol15;
   names[15]=InpSymbol16;names[16]=InpSymbol17; names[17]=InpSymbol18;
   names[18]=InpSymbol19;names[19]=InpSymbol20;

   double sl_a[MAX_SYMBOLS]={InpSym1_SL,InpSym2_SL,InpSym3_SL,InpSym4_SL,InpSym5_SL,
                              InpSym6_SL,InpSym7_SL,InpSym8_SL,InpSym9_SL,InpSym10_SL,
                              InpSym11_SL,InpSym12_SL,InpSym13_SL,InpSym14_SL,InpSym15_SL,
                              InpSym16_SL,InpSym17_SL,InpSym18_SL,InpSym19_SL,InpSym20_SL};
   double slo[MAX_SYMBOLS]={InpSym1_SLOffset,InpSym2_SLOffset,InpSym3_SLOffset,
                             InpSym4_SLOffset,InpSym5_SLOffset,InpSym6_SLOffset,
                             InpSym7_SLOffset,InpSym8_SLOffset,InpSym9_SLOffset,
                             InpSym10_SLOffset,InpSym11_SLOffset,InpSym12_SLOffset,
                             InpSym13_SLOffset,InpSym14_SLOffset,InpSym15_SLOffset,
                             InpSym16_SLOffset,InpSym17_SLOffset,InpSym18_SLOffset,
                             InpSym19_SLOffset,InpSym20_SLOffset};
   double tp_a[MAX_SYMBOLS]={InpSym1_TP,InpSym2_TP,InpSym3_TP,InpSym4_TP,InpSym5_TP,
                              InpSym6_TP,InpSym7_TP,InpSym8_TP,InpSym9_TP,InpSym10_TP,
                              InpSym11_TP,InpSym12_TP,InpSym13_TP,InpSym14_TP,InpSym15_TP,
                              InpSym16_TP,InpSym17_TP,InpSym18_TP,InpSym19_TP,InpSym20_TP};
   double ac_a[MAX_SYMBOLS]={InpSym1_Activation,InpSym2_Activation,InpSym3_Activation,
                              InpSym4_Activation,InpSym5_Activation,InpSym6_Activation,
                              InpSym7_Activation,InpSym8_Activation,InpSym9_Activation,
                              InpSym10_Activation,InpSym11_Activation,InpSym12_Activation,
                              InpSym13_Activation,InpSym14_Activation,InpSym15_Activation,
                              InpSym16_Activation,InpSym17_Activation,InpSym18_Activation,
                              InpSym19_Activation,InpSym20_Activation};
   double ps_a[MAX_SYMBOLS]={InpSym1_ProtSL,InpSym2_ProtSL,InpSym3_ProtSL,
                              InpSym4_ProtSL,InpSym5_ProtSL,InpSym6_ProtSL,
                              InpSym7_ProtSL,InpSym8_ProtSL,InpSym9_ProtSL,
                              InpSym10_ProtSL,InpSym11_ProtSL,InpSym12_ProtSL,
                              InpSym13_ProtSL,InpSym14_ProtSL,InpSym15_ProtSL,
                              InpSym16_ProtSL,InpSym17_ProtSL,InpSym18_ProtSL,
                              InpSym19_ProtSL,InpSym20_ProtSL};
   g_SymCount=0;
   for(int i=0;i<MAX_SYMBOLS;i++)
   { string sn=names[i]; StringTrimLeft(sn); StringTrimRight(sn);
     if(StringLen(sn)==0) continue;
     if(!SymbolSelect(sn,true)){Print("WARNING: No se pudo agregar ",sn);continue;}
     int idx=g_SymCount;
     g_Symbols[idx].name=sn; g_Symbols[idx].active=true;
     g_Symbols[idx].sl_points=sl_a[i]; g_Symbols[idx].sl_offset=slo[i];
     g_Symbols[idx].tp_points=tp_a[i]; g_Symbols[idx].activation=ac_a[i];
     g_Symbols[idx].protectedSL=ps_a[i];
     g_SymCount++;
     Print("Símbolo [",idx,"]: ",sn," SL=",sl_a[i]," Offset=",slo[i],
           " TP=",tp_a[i]," Act=",ac_a[i]," ProtSL=",ps_a[i]); }
}

void InitRiskTable()
{
   g_RiskTable[0] =InpRiskStep1;  g_RiskTable[1] =InpRiskStep2;
   g_RiskTable[2] =InpRiskStep3;  g_RiskTable[3] =InpRiskStep4;
   g_RiskTable[4] =InpRiskStep5;  g_RiskTable[5] =InpRiskStep6;
   g_RiskTable[6] =InpRiskStep7;  g_RiskTable[7] =InpRiskStep8;
   g_RiskTable[8] =InpRiskStep9;  g_RiskTable[9] =InpRiskStep10;
   g_RiskTable[10]=InpRiskStep11; g_RiskTable[11]=InpRiskStep12;
   g_RiskTable[12]=InpRiskStep13; g_RiskTable[13]=InpRiskStep14;
   g_RiskTable[14]=InpRiskStep15; g_RiskTable[15]=InpRiskStep16;
   g_RiskTable[16]=InpRiskStep17; g_RiskTable[17]=InpRiskStep18;
   g_RiskTable[18]=InpRiskStep19; g_RiskTable[19]=InpRiskStep20;
}

void InitSystemState(int si)
{
   g_PairLevel[si]=1;              // nivel de riesgo del par (Asistente 3)
   g_SysState[si].hasLive=false;
   g_SysState[si].activeLiveStrategy=-1;
   g_SysState[si].SE.Valid=false;
   g_SysState[si].SE_H1.Valid=false;
   g_SysState[si].SE_M3.Valid=false;
   g_SysState[si].structLastBar=0;
   g_SysState[si].h1LastBar=0;
   g_SysState[si].m3LastBar=0;

   //--- Estrategia 2: zona 4H + order blocks históricos (se recalcula, no se persiste)
   ZeroMemory(g_SysState[si].SE_H4);
   g_SysState[si].h4LastBar=0;
   g_SysState[si].ob1hLastBar=0;
   g_SysState[si].ob2Count=0;
   g_SysState[si].ob2Buys=0;
   g_SysState[si].ob2Sells=0;
   g_SysState[si].ob2BuyRange=0;
   g_SysState[si].ob2SellRange=0;
   g_SysState[si].ob2Outside=false;
   g_SysState[si].ob2Mitigated=0;
   g_SysState[si].ob2Armed=0;
   g_SysState[si].ob2Frozen=0;
   g_SysState[si].m3ChochDir2=0;
   g_SysState[si].m3ChochTime2=0;
   g_SysState[si].s2EntryBuy=0.0;    g_SysState[si].s2EntrySell=0.0;
   g_SysState[si].s2WaitBuy=false;   g_SysState[si].s2WaitSell=false;
   g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
   g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0;
   for(int k=0;k<STRAT2_STORED_OBS;k++) ZeroMemory(g_SysState[si].ob2[k]);

   g_SysState[si].m3ChochDir=0;        g_SysState[si].m3ChochTime=0;
   g_SysState[si].confArmedBuy=false;  g_SysState[si].confArmedSell=false;
   g_SysState[si].confArmBuyTime=0;    g_SysState[si].confArmSellTime=0;
   g_SysState[si].confEntryBuy=0.0;    g_SysState[si].confEntrySell=0.0;
   g_SysState[si].confWaitBuy=false;   g_SysState[si].confWaitSell=false;
   g_SysState[si].confVPendBuy=false;  g_SysState[si].confVPendBuyPrice=0.0;
   g_SysState[si].confVPendSell=false; g_SysState[si].confVPendSellPrice=0.0;

   bool ena[STRAT_COUNT]={InpUseConfluencia,InpUseStrat2};
   for(int st=0;st<STRAT_COUNT;st++)
   { g_SysState[si].strategies[st].enabled        = ena[st];
     g_SysState[si].strategies[st].isLive         = false;
     g_SysState[si].strategies[st].CV             = 1;
     g_SysState[si].strategies[st].CV_Max         = 1;
     g_SysState[si].strategies[st].virtualActive  = false;
     g_SysState[si].strategies[st].virtualDir     = 0;
     g_SysState[si].strategies[st].virtualOpen    = 0;
     g_SysState[si].strategies[st].virtualOpenLevel=1;
     g_SysState[si].strategies[st].virtualSL_price= 0;
     g_SysState[si].strategies[st].virtualTP_price= 0;
     g_SysState[si].strategies[st].virtualSLMoved = false;
     g_SysState[si].strategies[st].magicNumber    = GetStrategyMagic(si,st);
     g_SysState[si].strategies[st].name           = GetStrategyName(st);
   g_SysState[si].strategies[st].lastBarTime    = 0;
   g_SysState[si].strategies[st].cbPaused       = false;
   g_SysState[si].strategies[st].cbPausedCV     = 1;
   g_SysState[si].strategies[st].liveLogicLevel = 0;
}
}



//+------------------------------------------------------------------+
//| PERSISTENCIA                                                     |
//+------------------------------------------------------------------+
void InitGlobalVarKeys()
{
   string s=IntegerToString(InpMagicNumber);
   GV_ADV_MODE   =GV_PREFIX+"ADV_"  +s;
   GV_LIMIT_PRICE=GV_PREFIX+"LIMIT_"+s;
   GV_PANEL_X    =GV_PREFIX+"PNLX_" +s;
   GV_PANEL_Y    =GV_PREFIX+"PNLY_" +s;
}

string GetStateFileName()
{ return "GQP_v830_"+IntegerToString(InpMagicNumber)+".dat"; }

void SaveState()
{
   if(IsTester()) return;
   GlobalVariableSet(GV_ADV_MODE,   g_AdvancedMode?1.0:0.0);
   GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice);
   GlobalVariableSet(GV_PANEL_X,    (double)PNL_X);
   GlobalVariableSet(GV_PANEL_Y,    (double)PNL_Y);
   SaveStateToFile();
}

void SaveStateToFile()
{
   int h=FileOpen(GetStateFileName(),FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h==INVALID_HANDLE) return;
   FileWriteString(h,"ADV_MODE="      +(g_AdvancedMode?"1":"0")          +"\n");
   FileWriteString(h,"LIMIT_PRICE="   +DoubleToString(g_LimitPrice,8)    +"\n");
   FileWriteString(h,"PANEL_X="       +IntegerToString(PNL_X)            +"\n");
   FileWriteString(h,"PANEL_Y="       +IntegerToString(PNL_Y)            +"\n");
   FileWriteString(h,"TABLE_SIZE="    +IntegerToString(g_PanelTableSize) +"\n");
   FileWriteString(h,"PANEL_SYM_IDX="+IntegerToString(g_PanelSymIdx)    +"\n");
   FileWriteString(h,"BASE_CAPITAL="  +DoubleToString(g_BaseCapital,8)   +"\n");
   FileWriteString(h,"BASE_MAX_BAL="  +DoubleToString(g_BaseMaxBalance,8)+"\n");
   FileWriteString(h,"DAY_START_EQ="  +DoubleToString(g_DayStartEquity,8)+"\n");
   FileWriteString(h,"DAY_START_TIME="+IntegerToString(g_DayStartTime)   +"\n");
   FileWriteString(h,"CB_ON="         +(g_CircuitBreakerOn?"1":"0")      +"\n");
   for(int si=0;si<g_SymCount;si++)
   { string sp="SYM"+IntegerToString(si)+"_";
     FileWriteString(h,sp+"NAME="    +g_Symbols[si].name                                +"\n");
     FileWriteString(h,sp+"HASLIVE="+(g_SysState[si].hasLive?"1":"0")                  +"\n");
     FileWriteString(h,sp+"ALIVE="  +IntegerToString(g_SysState[si].activeLiveStrategy)+"\n");
     for(int st=0;st<STRAT_COUNT;st++)
     { string pp=sp+((st==STRAT_S2)?"ST2_":"ST"+IntegerToString(st)+"_");
       FileWriteString(h,pp+"LIVE="    +(g_SysState[si].strategies[st].isLive?"1":"0")         +"\n");
       FileWriteString(h,pp+"CV="      +IntegerToString(g_SysState[si].strategies[st].CV)      +"\n");
       FileWriteString(h,pp+"CVMAX="   +IntegerToString(g_SysState[si].strategies[st].CV_Max)  +"\n");
       FileWriteString(h,pp+"VACT="    +(g_SysState[si].strategies[st].virtualActive?"1":"0")  +"\n");
       FileWriteString(h,pp+"VDIR="    +IntegerToString(g_SysState[si].strategies[st].virtualDir)+"\n");
       FileWriteString(h,pp+"VOP="     +DoubleToString(g_SysState[si].strategies[st].virtualOpen,8)+"\n");
       FileWriteString(h,pp+"VOL="    +IntegerToString(g_SysState[si].strategies[st].virtualOpenLevel)+"\n");
       FileWriteString(h,pp+"VSL="     +DoubleToString(g_SysState[si].strategies[st].virtualSL_price,8)+"\n");
       FileWriteString(h,pp+"VTP="     +DoubleToString(g_SysState[si].strategies[st].virtualTP_price,8)+"\n");
       FileWriteString(h,pp+"VSLMOV="  +(g_SysState[si].strategies[st].virtualSLMoved?"1":"0") +"\n");

       FileWriteString(h,pp+"CBPAUSE=" +(g_SysState[si].strategies[st].cbPaused?"1":"0")       +"\n");
       FileWriteString(h,pp+"CBCV="    +IntegerToString(g_SysState[si].strategies[st].cbPausedCV)+"\n");
       FileWriteString(h,pp+"VLOGIC="  +IntegerToString(g_SysState[si].strategies[st].liveLogicLevel)+"\n"); }
     //--- estado de la ESTRATEGIA ÚNICA (estructura H1 + confluencia M3)
     FileWriteString(h,sp+"PLEVEL="  +IntegerToString(PairLevel(si))+"\n");
     FileWriteString(h,sp+"CONF_ARMED_B="+(g_SysState[si].confArmedBuy?"1":"0")            +"\n");
     FileWriteString(h,sp+"CONF_ARM_BT=" +IntegerToString((long)g_SysState[si].confArmBuyTime)+"\n");
     FileWriteString(h,sp+"CONF_ARMED_S="+(g_SysState[si].confArmedSell?"1":"0")           +"\n");
     FileWriteString(h,sp+"CONF_ARM_ST=" +IntegerToString((long)g_SysState[si].confArmSellTime)+"\n");
     FileWriteString(h,sp+"CONF_ENTRY_B="+DoubleToString(g_SysState[si].confEntryBuy,8)    +"\n");
     FileWriteString(h,sp+"CONF_ENTRY_S="+DoubleToString(g_SysState[si].confEntrySell,8)   +"\n");
     FileWriteString(h,sp+"CONF_WAIT_B=" +(g_SysState[si].confWaitBuy?"1":"0")             +"\n");
     FileWriteString(h,sp+"CONF_WAIT_S=" +(g_SysState[si].confWaitSell?"1":"0")            +"\n");
     FileWriteString(h,sp+"CONF_VPEND_B="+(g_SysState[si].confVPendBuy?"1":"0")            +"\n");
     FileWriteString(h,sp+"CONF_VPEND_BP="+DoubleToString(g_SysState[si].confVPendBuyPrice,8)+"\n");
     FileWriteString(h,sp+"CONF_VPEND_S="+(g_SysState[si].confVPendSell?"1":"0")           +"\n");
     FileWriteString(h,sp+"CONF_VPEND_SP="+DoubleToString(g_SysState[si].confVPendSellPrice,8)+"\n");
     FileWriteString(h,sp+"S2_ENTRY_B="+DoubleToString(g_SysState[si].s2EntryBuy,8)    +"\n");
     FileWriteString(h,sp+"S2_ENTRY_S="+DoubleToString(g_SysState[si].s2EntrySell,8)   +"\n");
     FileWriteString(h,sp+"S2_WAIT_B=" +(g_SysState[si].s2WaitBuy?"1":"0")             +"\n");
     FileWriteString(h,sp+"S2_WAIT_S=" +(g_SysState[si].s2WaitSell?"1":"0")            +"\n");
     FileWriteString(h,sp+"S2_VPEND_B="+(g_SysState[si].s2VPendBuy?"1":"0")            +"\n");
     FileWriteString(h,sp+"S2_VPEND_BP="+DoubleToString(g_SysState[si].s2VPendBuyPrice,8)+"\n");
     FileWriteString(h,sp+"S2_VPEND_S="+(g_SysState[si].s2VPendSell?"1":"0")           +"\n");
     FileWriteString(h,sp+"S2_VPEND_SP="+DoubleToString(g_SysState[si].s2VPendSellPrice,8)+"\n"); }
   FileWriteString(h,"SAVED_AT="+TimeToString(TimeCurrent())+"\n");
   FileClose(h);
}

void LoadState()
{
   if(GlobalVariableCheck(GV_ADV_MODE))    g_AdvancedMode=(GlobalVariableGet(GV_ADV_MODE)>0.5);
   if(GlobalVariableCheck(GV_LIMIT_PRICE)){ double lp=GlobalVariableGet(GV_LIMIT_PRICE); if(lp>0) g_LimitPrice=lp; }
   if(GlobalVariableCheck(GV_PANEL_X))     PNL_X=(int)GlobalVariableGet(GV_PANEL_X);
   if(GlobalVariableCheck(GV_PANEL_Y))     PNL_Y=(int)GlobalVariableGet(GV_PANEL_Y);
   LoadStateFromFile();
}

void LoadStateFromFile()
{
   string fname=GetStateFileName();
   if(!FileIsExist(fname)) return;
   int h=FileOpen(fname,FILE_READ|FILE_TXT|FILE_ANSI);
   if(h==INVALID_HANDLE) return;
   while(!FileIsEnding(h))
   { string line=FileReadString(h);
     StringTrimLeft(line); StringTrimRight(line);
     if(StringLen(line)==0) continue;
     int sep=StringFind(line,"="); if(sep<0) continue;
     string key=StringSubstr(line,0,sep);
     string val=StringSubstr(line,sep+1);
     if(key=="ADV_MODE")        g_AdvancedMode=(StringToInteger(val)>0);
     else if(key=="LIMIT_PRICE"){ double lp=StringToDouble(val); if(lp>0) g_LimitPrice=lp; }
     else if(key=="PANEL_X")    PNL_X=(int)StringToInteger(val);
     else if(key=="PANEL_Y")    PNL_Y=(int)StringToInteger(val);
     else if(key=="TABLE_SIZE") g_PanelTableSize=MathMax(1,MathMin(MAX_TABLE_SIZE,(int)StringToInteger(val)));
     else if(key=="PANEL_SYM_IDX")  g_PanelSymIdx=(int)StringToInteger(val);
     else if(key=="BASE_CAPITAL")   g_BaseCapital=MathMax(0.01,StringToDouble(val));
     else if(key=="BASE_MAX_BAL")   g_BaseMaxBalance=StringToDouble(val);
     else if(key=="DAY_START_EQ")   g_DayStartEquity=StringToDouble(val);
     else if(key=="DAY_START_TIME") g_DayStartTime=(datetime)StringToInteger(val);
     else if(key=="CB_ON")          g_CircuitBreakerOn=(StringToInteger(val)>0);
     else
     { for(int si=0;si<g_SymCount;si++)
       { string sp="SYM"+IntegerToString(si)+"_";
         if(StringFind(key,sp)!=0) continue;
         string rest=StringSubstr(key,StringLen(sp));
         if(rest=="HASLIVE") g_SysState[si].hasLive=(StringToInteger(val)>0);
         else if(rest=="ALIVE") g_SysState[si].activeLiveStrategy=(int)StringToInteger(val);
         else if(rest=="PLEVEL")    g_PairLevel[si]=(int)MathMax(1,MathMin(MAX_TABLE_SIZE,StringToInteger(val)));
         else if(rest=="CONF_ARMED_B") g_SysState[si].confArmedBuy=(StringToInteger(val)>0);
         else if(rest=="CONF_ARM_BT")  g_SysState[si].confArmBuyTime=(datetime)StringToInteger(val);
         else if(rest=="CONF_ARMED_S") g_SysState[si].confArmedSell=(StringToInteger(val)>0);
         else if(rest=="CONF_ARM_ST")  g_SysState[si].confArmSellTime=(datetime)StringToInteger(val);
         else if(rest=="CONF_ENTRY_B") g_SysState[si].confEntryBuy=StringToDouble(val);
         else if(rest=="CONF_ENTRY_S") g_SysState[si].confEntrySell=StringToDouble(val);
         else if(rest=="CONF_WAIT_B")  g_SysState[si].confWaitBuy=(StringToInteger(val)>0);
         else if(rest=="CONF_WAIT_S")  g_SysState[si].confWaitSell=(StringToInteger(val)>0);
         else if(rest=="CONF_VPEND_B") g_SysState[si].confVPendBuy=(StringToInteger(val)>0);
         else if(rest=="CONF_VPEND_BP")g_SysState[si].confVPendBuyPrice=StringToDouble(val);
         else if(rest=="CONF_VPEND_S") g_SysState[si].confVPendSell=(StringToInteger(val)>0);
         else if(rest=="CONF_VPEND_SP")g_SysState[si].confVPendSellPrice=StringToDouble(val);
         else if(rest=="S2_ENTRY_B")  g_SysState[si].s2EntryBuy=StringToDouble(val);
         else if(rest=="S2_ENTRY_S")  g_SysState[si].s2EntrySell=StringToDouble(val);
         else if(rest=="S2_WAIT_B")   g_SysState[si].s2WaitBuy=(StringToInteger(val)>0);
         else if(rest=="S2_WAIT_S")   g_SysState[si].s2WaitSell=(StringToInteger(val)>0);
         else if(rest=="S2_VPEND_B")  g_SysState[si].s2VPendBuy=(StringToInteger(val)>0);
         else if(rest=="S2_VPEND_BP") g_SysState[si].s2VPendBuyPrice=StringToDouble(val);
         else if(rest=="S2_VPEND_S")  g_SysState[si].s2VPendSell=(StringToInteger(val)>0);
         else if(rest=="S2_VPEND_SP") g_SysState[si].s2VPendSellPrice=StringToDouble(val);
         else
         { for(int st=0;st<STRAT_COUNT;st++)
           { string pp=(st==STRAT_S2)?"ST2_":"ST"+IntegerToString(st)+"_";
             //--- compatibilidad: en archivos antiguos la estrategia de
             //    confluencia estaba en ST1_ (con PERSONAL en ST0_)
             if(StringFind(rest,pp)!=0)
             { if(st==0 && StringFind(rest,"ST1_")==0)
                 pp="ST1_";
               else continue; }
             string field=StringSubstr(rest,StringLen(pp));
             if(field=="LIVE")     g_SysState[si].strategies[st].isLive=(StringToInteger(val)>0);
             else if(field=="CV")  g_SysState[si].strategies[st].CV=MathMax(1,(int)StringToInteger(val));
             else if(field=="CVMAX")  g_SysState[si].strategies[st].CV_Max=(int)StringToInteger(val);
             else if(field=="VACT")   g_SysState[si].strategies[st].virtualActive=(StringToInteger(val)>0);
             else if(field=="VDIR")   g_SysState[si].strategies[st].virtualDir=(int)StringToInteger(val);
             else if(field=="VOP")    g_SysState[si].strategies[st].virtualOpen=StringToDouble(val);
             else if(field=="VOL") g_SysState[si].strategies[st].virtualOpenLevel=(int)StringToInteger(val);
             else if(field=="VSL")    g_SysState[si].strategies[st].virtualSL_price=StringToDouble(val);
             else if(field=="VTP")    g_SysState[si].strategies[st].virtualTP_price=StringToDouble(val);
             else if(field=="VSLMOV") g_SysState[si].strategies[st].virtualSLMoved=(StringToInteger(val)>0);

             else if(field=="CBPAUSE")g_SysState[si].strategies[st].cbPaused=(StringToInteger(val)>0);
             else if(field=="CBCV")   g_SysState[si].strategies[st].cbPausedCV=(int)StringToInteger(val);
             else if(field=="VLOGIC") g_SysState[si].strategies[st].liveLogicLevel=(int)StringToInteger(val);
             break; } }
         break; } } }
   FileClose(h);
   if(g_PanelSymIdx>=g_SymCount) g_PanelSymIdx=0;
}//+------------------------------------------------------------------+
//| LÓGICA DE NIVELES (reglas de "Asistente 3", aplicadas por PAR)   |
//|                                                                  |
//|   PÉRDIDA                 → nivel del par +1                     |
//|   GANANCIA limpia (TP)    → nivel del par = 1                    |
//|   GANANCIA con SL prot.   → nivel −3 (abierto en nivel <10)      |
//|                             o −4 (abierto en nivel ≥10)          |
//|                                                                  |
//|   El CV de cada estrategia SIEMPRE cuenta con el MISMO régimen   |
//|   que las operaciones LIVE:                                      |
//|     · pérdida            → CV +1  y  nivel del par +1            |
//|     · ganancia limpia    → CV = 1  y  nivel del par = 1          |
//|     · ganancia protegida → CV −3/−4 y nivel del par −3/−4        |
//|   Así, con InpXActivacion = X el EA pasa a LIVE al completar X   |
//|   pérdidas de la serie (CV = X+1) y la operación X+1 ya es LIVE. |
//|                                                                  |
//|   AL ACTIVAR LIVE: las X virtuales son SOLO la condición. La     |
//|   tabla SIEMPRE arranca en el NIVEL 1 (lote base) y la serie     |
//|   real progresa desde ahí (pérdida → 1→2→3…). El nivel que       |
//|   alcanzó la serie virtual se conserva como NIVEL DE LÓGICA      |
//|   (liveLogicLevel): el 1:2 automático se aplica como si la       |
//|   estrategia estuviera en ese nivel (ej. X=4 → lógica N5, 1:2 ON |
//|   desde el primer trade live aunque la tabla marque N1).         |
//|                                                                  |
//|   EXCEPCIÓN: si en el par ya hay una estrategia LIVE, los cierres|
//|   virtuales de las demás SOLO cuentan su CV (para no mover dos   |
//|   veces el nivel compartido); el nivel lo mueven únicamente las  |
//|   operaciones REALES. Al activar LIVE se cancela cualquier       |
//|   virtual pendiente para que no se reanude después.              |
//+------------------------------------------------------------------+
//--- Limpia el estado de una simulación virtual (se usa al entrar o
//    salir de LIVE para que lo virtual nunca vuelva a contar)
void ClearVirtualState(int si,int st)
{
   g_SysState[si].strategies[st].virtualActive  =false;
   g_SysState[si].strategies[st].virtualDir     =0;
   g_SysState[si].strategies[st].virtualOpen    =0;
   g_SysState[si].strategies[st].virtualOpenLevel=1;
   g_SysState[si].strategies[st].virtualSL_price=0;
   g_SysState[si].strategies[st].virtualTP_price=0;
   g_SysState[si].strategies[st].virtualSLMoved =false;
   g_SysState[si].strategies[st].liveLogicLevel=0;
   if(st==STRAT_CONFLUENCIA)
   { g_SysState[si].confVPendBuy=false;  g_SysState[si].confVPendBuyPrice=0.0;
     g_SysState[si].confVPendSell=false; g_SysState[si].confVPendSellPrice=0.0; }
   if(st==STRAT_S2)
   { g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
     g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0; }
}

//--- cierre VIRTUAL (simulación): MISMO régimen que LIVE.
//    · pérdida            → CV +1  y  nivel +1 (si no hay LIVE en el par)
//    · ganancia limpia    → CV = 1  y  nivel = 1 (si no hay LIVE en el par)
//    · ganancia protegida → CV −3/−4 y nivel −3/−4 (si no hay LIVE en el par)
//    El nivel de la serie virtual define el NIVEL DE LÓGICA con el que
//    arranca LIVE; al activarse, la TABLA se resetea a 1 (el lote del
//    primer trade real sale del nivel 1, pero el 1:2 se aplica como si
//    la estrategia estuviera en el nivel alcanzado por la virtual).
void OnVirtualSL_Original(int si, int st)
{
   int cv=g_SysState[si].strategies[st].CV;
   g_SysState[si].strategies[st].CV++;
   UpdateCVMax(si,st);
   if(g_SysState[si].hasLive)
      Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
            "] vSL orig CV:",cv,
            "→",g_SysState[si].strategies[st].CV,
            " NIVEL sin cambio (hay LIVE en el par → solo operaciones reales)");
   else
   { int lv=PairLevel(si); PairLevelUp(si);
     Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
           "] vSL orig CV:",cv,
           "→",g_SysState[si].strategies[st].CV,
           " NIVEL:",lv,"→",PairLevel(si),
           " Lot:",DoubleToString(GetPairLot(si),2)); }
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
   if(!g_SysState[si].hasLive&&
      g_SysState[si].strategies[st].CV>=(InpXActivacion+1))
      SelectNextLiveStrategy(si);
}

void OnVirtualSL_Protected(int si, int st, int openLevel)
{
   int cv=g_SysState[si].strategies[st].CV;
   int r=(cv>=10)?4:3;
   g_SysState[si].strategies[st].CV=ApplyRetroceso(cv,r);
   UpdateCVMax(si,st);
   if(g_SysState[si].hasLive)
      Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
            "] vSL prot CV:",cv,"→",g_SysState[si].strategies[st].CV,
            " NIVEL sin cambio (hay LIVE en el par → solo operaciones reales)");
   else
   { int lv=PairLevel(si); PairLevelBack(si,openLevel);
     Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
           "] vSL prot CV:",cv,"→",g_SysState[si].strategies[st].CV,
           " NIVEL:",lv,"→",PairLevel(si),
           " (abierto en nivel ",openLevel,")",
           " Lot:",DoubleToString(GetPairLot(si),2)); }
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
}

void OnVirtualTP(int si, int st)
{
   int cv=g_SysState[si].strategies[st].CV;
   if(g_SysState[si].hasLive)
      Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
            "] vTP CV:",cv,"→1",
            " NIVEL sin cambio (hay LIVE en el par → solo operaciones reales)");
   else
   { int lv=PairLevel(si); PairLevelReset(si);
     Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
           "] vTP CV:",cv,"→1 NIVEL:",lv,"→",PairLevel(si)); }
   g_SysState[si].strategies[st].CV=1;
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
}

//--- cierre LIVE (real)
void OnLiveSL_Original(int si, int st)
{
   int cv=g_SysState[si].strategies[st].CV;
   g_SysState[si].strategies[st].CV++;
   UpdateCVMax(si,st);
   int lv=PairLevel(si); PairLevelUp(si);
   Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
         "] LIVE SL orig CV:",cv,"→",g_SysState[si].strategies[st].CV,
         " NIVEL:",lv,"→",PairLevel(si),
         " Lot:",DoubleToString(GetPairLot(si),2));
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
}

void OnLiveSL_Protected(int si, int st, int openLevel)
{
   int cv=g_SysState[si].strategies[st].CV;
   int r=(cv>=10)?4:3;
   g_SysState[si].strategies[st].CV=ApplyRetroceso(cv,r);
   UpdateCVMax(si,st);
   int lv=PairLevel(si); PairLevelBack(si,openLevel);
   Print("[",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
         "] LIVE SL prot CV:",cv,"→",g_SysState[si].strategies[st].CV,
         " NIVEL:",lv,"→",PairLevel(si),
         " (abierto en nivel ",openLevel,")",
         " Lot:",DoubleToString(GetPairLot(si),2));
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
}

void OnLiveTP(int si, int st)
{
   Print("★ TP LIVE [",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
         "] CV:",g_SysState[si].strategies[st].CV,
         "→1 NIVEL:",PairLevel(si),"→1");
   g_SysState[si].strategies[st].CV=1;
   PairLevelReset(si);
   if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
   if(st==STRAT_S2) Strat2OnTradeClosed(si);
   g_SysState[si].strategies[st].isLive=false;
   g_SysState[si].hasLive=false;
   g_SysState[si].activeLiveStrategy=-1;
   ClearVirtualState(si,st);              // al salir de LIVE lo virtual empieza de cero
   SelectNextLiveStrategy(si);
   SaveState();
   if(!IsTester()) RebuildPanel();
}

void OnStrategyLiveTP(int si, int st)  { OnLiveTP(si,st); }
void OnStrategyLiveSL(int si, int st, bool slMoved, int openLevel)
{ if(slMoved) OnLiveSL_Protected(si,st,openLevel);
  else        OnLiveSL_Original(si,st);
  SaveState(); }

//+------------------------------------------------------------------+
//| SELECCIÓN LIVE                                                   |
//+------------------------------------------------------------------+
void SelectNextLiveStrategy(int si)
{
   int thr=InpXActivacion+1;
   int cand[STRAT_COUNT]; int cc=0,mx=0;
   for(int st=0;st<STRAT_COUNT;st++)
   { if(!g_SysState[si].strategies[st].enabled)  continue;
     if(g_SysState[si].strategies[st].CV<thr)     continue;
     if(g_SysState[si].strategies[st].cbPaused)   continue;
     cand[cc]=st; cc++;
     if(g_SysState[si].strategies[st].CV>mx) mx=g_SysState[si].strategies[st].CV; }
   if(cc==0)
   { Print("SelectNextLive [",g_Symbols[si].name,"]: ninguna CV>=",thr);
     g_SysState[si].hasLive=false; g_SysState[si].activeLiveStrategy=-1; return; }
   int top[STRAT_COUNT]; int tc=0;
   for(int i=0;i<cc;i++)
      if(g_SysState[si].strategies[cand[i]].CV==mx){top[tc]=cand[i];tc++;}
   int chosen=(tc==1)?top[0]:top[MathRand()%tc];
   ActivateLiveStrategy(si,chosen);
}

void ActivateLiveStrategy(int si, int st)
{
   for(int s=0;s<STRAT_COUNT;s++) g_SysState[si].strategies[s].isLive=false;
   //--- la serie VIRTUAL es solo la CONDICIÓN para pasar a LIVE:
   //    guardamos el nivel que alcanzó (lógica) pero la TABLA arranca
   //    SIEMPRE en el nivel 1. Ej: X=4 → serie virtual llegó a nivel 5,
   //    el primer trade LIVE se abre con nivel 1 (lote base) y con la
   //    lógica 1:2 como si estuviera en el nivel 5.
   int logicLevel=PairLevel(si);
   ClearVirtualState(si,st);              // cancela la virtual pendiente: en LIVE solo cuenta lo real
   g_SysState[si].strategies[st].isLive=true;
   g_SysState[si].strategies[st].liveLogicLevel=logicLevel;
   g_PairLevel[si]=1;                    // tabla: LIVE SIEMPRE desde el nivel 1
   g_SysState[si].hasLive=true;
   g_SysState[si].activeLiveStrategy=st;
   Print("★ LIVE [",g_Symbols[si].name,"/",g_SysState[si].strategies[st].name,
         "] CV=",g_SysState[si].strategies[st].CV,
         " NIVEL par=1 (serie virtual: N",logicLevel,")",
         " Lot=",DoubleToString(GetPairLot(si),2),
         " 1:2=",IsTrailingActive(si,st)?"ON":"OFF");
   SaveState(); if(!IsTester()) RebuildPanel();
}

//+------------------------------------------------------------------+
//| VIRTUAL                                                          |
//+------------------------------------------------------------------+
void StartStrategyVirtual(int si, int st, int signal)
{
   if(st==STRAT_CONFLUENCIA && !InpAllowConfluOrders) return;
   if(st==STRAT_S2 && !InpAllowStrat2Orders) return;
   if(signal==0||g_SysState[si].strategies[st].virtualActive) return;
   if(g_SysState[si].strategies[st].isLive) return;   // en LIVE jamás se abre/sigue una virtual
   string sym=g_Symbols[si].name;
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double openPrice=(signal>0)?ask:bid;
   int    ptypeEq=(signal>0)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   g_SysState[si].strategies[st].virtualDir       =signal;
   g_SysState[si].strategies[st].virtualOpen      =openPrice;
   g_SysState[si].strategies[st].virtualOpenLevel =PairLevel(si);   // nivel de apertura (regla −3/−4)
   g_SysState[si].strategies[st].virtualSL_price  =CalcSL(sym,si,openPrice,ptypeEq);
   g_SysState[si].strategies[st].virtualTP_price  =CalcTP(sym,si,openPrice,ptypeEq);
   g_SysState[si].strategies[st].virtualSLMoved   =false;
   g_SysState[si].strategies[st].virtualActive    =true;
   bool advNow=(InpAutoFromLevel5&&g_SysState[si].strategies[st].virtualOpenLevel>=5);
   Print("vOPEN [",sym,"/",g_SysState[si].strategies[st].name,"] ",
         (signal>0?"BUY":"SELL"),
         " @",DoubleToString(openPrice,(int)SymbolInfoInteger(sym,SYMBOL_DIGITS)),
         " CV=",g_SysState[si].strategies[st].CV,
         " NIVEL=",g_SysState[si].strategies[st].virtualOpenLevel,
         " 1:2=",advNow?"ON":"OFF");
}

void UpdateStrategyVirtual(int si, int st)
{
   if(!g_SysState[si].strategies[st].enabled)       return;
   if(g_SysState[si].strategies[st].isLive)         return;   // en LIVE no se avanza ninguna virtual
   if(!g_SysState[si].strategies[st].virtualActive) return;
   string sym=g_Symbols[si].name;
   int    dir=g_SysState[si].strategies[st].virtualDir;
   double pt =SymbolInfoDouble(sym,SYMBOL_POINT);
   int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   double checkPrice=(dir>0)?SymbolInfoDouble(sym,SYMBOL_BID)
                            :SymbolInfoDouble(sym,SYMBOL_ASK);
   bool vAdv=(g_AdvancedMode||(InpAutoFromLevel5&&g_SysState[si].strategies[st].virtualOpenLevel>=5));
   if(!g_SysState[si].strategies[st].virtualSLMoved&&vAdv)
   { double op=g_SysState[si].strategies[st].virtualOpen;
     double delta=(dir>0)?(checkPrice-op)/pt:(op-checkPrice)/pt;
     if(delta>=SymActivation(si))
     { double psl=SymProtectedSL(si);
       double nSL=(dir>0)?NormalizeDouble(op+psl*pt,dg):NormalizeDouble(op-psl*pt,dg);
       g_SysState[si].strategies[st].virtualSL_price=nSL;
       g_SysState[si].strategies[st].virtualSLMoved=true; } }
   bool win=false,loss=false;
   double vSL=g_SysState[si].strategies[st].virtualSL_price;
   double vTP=g_SysState[si].strategies[st].virtualTP_price;
   if(dir>0){if(checkPrice>=vTP)win=true;else if(checkPrice<=vSL)loss=true;}
   else     {if(checkPrice<=vTP)win=true;else if(checkPrice>=vSL)loss=true;}
   if(!win&&!loss) return;
   bool wasProtected=g_SysState[si].strategies[st].virtualSLMoved;
   int  openLevel  =g_SysState[si].strategies[st].virtualOpenLevel;  // nivel de apertura (regla −3/−4)
   g_SysState[si].strategies[st].virtualActive   =false;
   g_SysState[si].strategies[st].virtualOpen     =0;
   g_SysState[si].strategies[st].virtualSL_price =0;
   g_SysState[si].strategies[st].virtualTP_price =0;
   g_SysState[si].strategies[st].virtualDir      =0;
   g_SysState[si].strategies[st].virtualSLMoved  =false;
   if(win){OnVirtualTP(si,st);SaveState();if(!IsTester())RebuildActiveTab();return;}
   if(loss)
   { if(wasProtected) OnVirtualSL_Protected(si,st,openLevel); else OnVirtualSL_Original(si,st);
     SaveState(); if(!IsTester()) RebuildActiveTab(); }
}

//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| MOTOR DE ESTRUCTURA DE LÍNEAS                                      |
//| L1 = techo del rango; L2 = suelo del rango.                      |
//| L1/L2 solo se actualizan al cierre de vela (con high/low,        |
//| mechas incluidas). L3/L4 se activan únicamente cuando cierra una |
//| vela contraria a la estructura, y desde ahí guardan máximos/     |
//| mínimos al tick. Si L3>L1 o L4<L2 intrabar, la ruptura queda     |
//| pendiente y el swap L1=L3, L2=L4 se consolida al cierre.         |
//+------------------------------------------------------------------+
void SE_UpdateEQ(StructureEngine &SE)
{
   SE.EQ=SE.L2+(SE.L1-SE.L2)*0.5;
}

void SE_ClearReaction(StructureEngine &SE)
{
   SE.L3=0.0;
   SE.L4=0.0;
   SE.L3L4_Active=false;
   SE.PendingBreakDir=0;
   SE.Phase=PHASE_CONTINUATION;
}

int SE_CommitStructureMove(StructureEngine &SE, int dir, int &choch)
{
   if(dir==0 || !SE.L3L4_Active) return 0;

   ENUM_STRUCTURE_BIAS oldBias=SE.Bias;
   ENUM_STRUCTURE_BIAS newBias=BIAS_BULLISH;
   if(dir<0) newBias=BIAS_BEARISH;

   //--- El nuevo rango siempre queda definido por los extremos
   //    acumulados en la reacción: techo=L3, suelo=L4.
   SE.L1=SE.L3;
   SE.L2=SE.L4;
   if(SE.L1<SE.L2)
   {
      double tmp=SE.L1;
      SE.L1=SE.L2;
      SE.L2=tmp;
   }

   SE.Bias=newBias;
   SE_UpdateEQ(SE);
   SE_ClearReaction(SE);

   choch=(oldBias!=BIAS_UNDEFINED && oldBias!=newBias ? dir : 0);
   return dir;
}

int SE_LastBreakDirectionFromCandle(double O, double C, ENUM_STRUCTURE_BIAS currentBias)
{
   //--- Si una misma vela toca ambos lados y no hay ticks suficientes
   //    para conocer el orden, se usa el sentido del cuerpo como último
   //    movimiento. Con ticks reales, PendingBreakDir guarda el último
   //    lado que fue sobrepasado durante la vela.
   if(C>O) return +1;
   if(C<O) return -1;
   if(currentBias==BIAS_BEARISH) return +1;
   return -1;
}

int SE_BreakDirection(StructureEngine &SE, double O, double C)
{
   if(!SE.Valid || !SE.L3L4_Active) return 0;

   bool breakUp=(SE.L3>SE.L1);   // L3 sobrepasa L1
   bool breakDn=(SE.L4<SE.L2);   // L4 sobrepasa L2 hacia abajo
   if(!breakUp && !breakDn) return 0;

   if(breakUp && breakDn)
   {
      if(SE.PendingBreakDir!=0) return SE.PendingBreakDir;
      return SE_LastBreakDirectionFromCandle(O,C,SE.Bias);
   }
   if(breakUp) return +1;
   return -1;
}

void SE_MarkPendingBreak(StructureEngine &SE, double price)
{
   if(!SE.Valid || !SE.L3L4_Active || price<=0.0) return;

   //--- L3/L4 se actualizan al tick, pero L1/L2 NO cambian aquí:
   //    solo se marca el lado roto para consolidarlo al cierre.
   if(price>SE.L1)
   {
      SE.Phase=PHASE_TRIGGERED;
      SE.PendingBreakDir=+1;
   }
   if(price<SE.L2)
   {
      SE.Phase=PHASE_TRIGGERED;
      SE.PendingBreakDir=-1;
   }
}

int SE_CheckBreakAndCommit(StructureEngine &SE, double O, double C, int &choch)
{
   int dir=SE_BreakDirection(SE,O,C);
   if(dir==0) return 0;
   return SE_CommitStructureMove(SE,dir,choch);
}

bool SE_Init(StructureEngine &SE, string sym, ENUM_TIMEFRAMES tf)
{
   SE.TF=tf; SE.Valid=false;
   SE.L1=0; SE.L2=0; SE.L3=0; SE.L4=0; SE.EQ=0;
   SE.L3L4_Active=false; SE.PendingBreakDir=0;
   SE.Bias=BIAS_UNDEFINED; SE.Phase=PHASE_CONTINUATION;
   double p =SymbolInfoDouble(sym,SYMBOL_BID);
   double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
   if(p<=0.0||pt<=0.0) return false;
   SE.L1=p+2.0*pt; SE.L2=p-2.0*pt;
   MqlRates R[]; ArraySetAsSeries(R,true);
   int n=CopyRates(sym,tf,1,InpLookbackBars,R);
   if(n<2) return false;
   for(int i=0;i<n;i++)
   { if(R[i].high>SE.L1) SE.L1=R[i].high;
     if(R[i].low <SE.L2) SE.L2=R[i].low; }
   if(R[0].close>R[0].open)      SE.Bias=BIAS_BULLISH;
   else if(R[0].close<R[0].open) SE.Bias=BIAS_BEARISH;
   SE_UpdateEQ(SE);
   SE.Valid=true;
   return true;
}

//+------------------------------------------------------------------+
//| Actualización tick a tick: SOLO L3/L4 y ruptura pendiente        |
//+------------------------------------------------------------------+
int SE_OnTick(StructureEngine &SE, string sym, int &choch)
{
   choch=0;
   if(!SE.Valid || !SE.L3L4_Active) return 0;

   double price=SymbolInfoDouble(sym,SYMBOL_BID);
   if(price<=0.0) return 0;

   if(price>SE.L3) SE.L3=price;
   if(price<SE.L4) SE.L4=price;

   //--- L1/L2 rastrean al tick como pidió el usuario
   if(SE.Bias==BIAS_BULLISH && price>SE.L1) { SE.L1=price; SE_UpdateEQ(SE); }
   else if(SE.Bias==BIAS_BEARISH && price<SE.L2) { SE.L2=price; SE_UpdateEQ(SE); }

   SE_MarkPendingBreak(SE,price);

   //--- No hay trigger operativo aquí porque L1/L2 se actualizan
   //    únicamente al cierre de la vela.
   return 0;
}

//+------------------------------------------------------------------+
//| Procesa la vela cerrada: actualiza L1/L2 al cierre, activa       |
//| L3/L4 con vela contraria y consolida rupturas pendientes.        |
//+------------------------------------------------------------------+
void SE_OnClose(StructureEngine &SE, string sym, int &choch, int &trig)
{
   choch=0; trig=0;
   if(!SE.Valid) return;

   double O=iOpen(sym,SE.TF,1), C=iClose(sym,SE.TF,1);
   double H=iHigh(sym,SE.TF,1), L=iLow(sym,SE.TF,1);
   if(O<=0.0||C<=0.0||H<=0.0||L<=0.0) return;

   bool green=C>O, red=C<O;

   if(SE.Bias==BIAS_UNDEFINED)
   {
      if(green) SE.Bias=BIAS_BULLISH;
      if(red)   SE.Bias=BIAS_BEARISH;
      return;
   }

   //--- Si L3/L4 ya estaban activos, la vela cerrada también cuenta
   //    sus mechas dentro de la reacción; L1/L2 se actualizan solo si
   //    corresponde consolidar el rompimiento al cierre.
   if(SE.L3L4_Active)
   {
      if(H>SE.L3) SE.L3=H;
      if(L<SE.L4) SE.L4=L;
      trig=SE_CheckBreakAndCommit(SE,O,C,choch);
      if(trig==0) SE.Phase=PHASE_REACTION;
      return;
   }

   //--- Continuación sin reacción activa: L1/L2 se mueven al CIERRE.
   //    Alcista: solo L1 sube. Bajista: solo L2 baja.
   if(SE.Bias==BIAS_BULLISH)
   {
      if(H>SE.L1)
      { SE.L1=H; SE_UpdateEQ(SE); }
   }
   else if(SE.Bias==BIAS_BEARISH)
   {
      if(L<SE.L2)
      { SE.L2=L; SE_UpdateEQ(SE); }
   }

   //--- Activación de L3/L4 únicamente por cierre contrario.
   if(SE.Bias==BIAS_BULLISH && red)
   {
      SE.L3L4_Active=true;
      SE.L3=SE.L1;   // en alcista L3 inicia en L1
      SE.L4=L;       // L4 inicia en el mínimo de la vela contraria
      SE.Phase=PHASE_REACTION;
      trig=SE_CheckBreakAndCommit(SE,O,C,choch);
   }
   else if(SE.Bias==BIAS_BEARISH && green)
   {
      SE.L3L4_Active=true;
      SE.L3=H;       // en bajista L3 inicia en el máximo de la vela contraria
      SE.L4=SE.L2;   // en bajista L4 inicia en L2
      SE.Phase=PHASE_REACTION;
      trig=SE_CheckBreakAndCommit(SE,O,C,choch);
   }
}

//+------------------------------------------------------------------+
//| Actualiza motores de líneas por símbolo (llamar en cada tick)    |
//| - Estructura madre (H1): líneas L1-L4 → bias + rango + zona 50%. |
//| - Estructura de entrada (M3): líneas L1-L4 → CHoCH + 50% M3.     |
//| - TF del gráfico: solo se mantiene para el dibujo visual.         |
//+------------------------------------------------------------------+
void UpdateStructureState(int si)
{
   string sym=g_Symbols[si].name;

   if(!g_SysState[si].SE.Valid) SE_Init(g_SysState[si].SE,sym,PERIOD_CURRENT);

   //--- SE_M3 se comparte entre Estrategia 1 y Estrategia 2: hay que
   //    actualizarlo si cualquiera de las dos está activa.
   bool confOn=InpUseConfluencia;
   bool s2On  =InpUseStrat2;
   if(confOn)
      if(!g_SysState[si].SE_H1.Valid) SE_Init(g_SysState[si].SE_H1,sym,InpConfTFSuperior);
   if(confOn || s2On)
      if(!g_SysState[si].SE_M3.Valid) SE_Init(g_SysState[si].SE_M3,sym,InpConfTFEntrada);

   //--- vela del TF del gráfico nueva → actualizar solo el dibujo
   datetime bt=(datetime)SeriesInfoInteger(sym,PERIOD_CURRENT,SERIES_LASTBAR_DATE);
   if(bt!=g_SysState[si].structLastBar)
   {
      g_SysState[si].structLastBar=bt;
      int c2=0,t2=0;
      if(g_SysState[si].SE.Valid)
         SE_OnClose(g_SysState[si].SE,sym,c2,t2);
   }

   //--- vela del TF madre nueva → estructura madre (Estrategia 1)
   if(confOn)
   {
      datetime tm=(datetime)SeriesInfoInteger(sym,InpConfTFSuperior,SERIES_LASTBAR_DATE);
      if(tm!=g_SysState[si].h1LastBar)
      {
         g_SysState[si].h1LastBar=tm;
         int c1=0,t1=0;
         if(g_SysState[si].SE_H1.Valid)
         {
            SE_OnClose(g_SysState[si].SE_H1,sym,c1,t1);
            if(c1!=0) ConfluenciaOnH1Change(si,c1);   // rango madre nuevo → reinicio
         }
      }

   }
   if(confOn || s2On)
   {
      //--- vela del TF de entrada nueva → confirmación (Estrategias 1 y 2)
      datetime te=(datetime)SeriesInfoInteger(sym,InpConfTFEntrada,SERIES_LASTBAR_DATE);
      if(te!=g_SysState[si].m3LastBar)
      {
         g_SysState[si].m3LastBar=te;
         int c3=0,t3=0;
         if(g_SysState[si].SE_M3.Valid)
         {
            SE_OnClose(g_SysState[si].SE_M3,sym,c3,t3);
            if(c3!=0)
            {
               //--- el mismo CHoCH se reparte a ambas estrategias
               if(confOn)
               { g_SysState[si].m3ChochDir =c3;
                 g_SysState[si].m3ChochTime=TimeCurrent(); }
               g_SysState[si].m3ChochDir2=c3;
               g_SysState[si].m3ChochTime2=TimeCurrent();
            }
         }
      }
   }

   //--- actualización al tick: solo L3/L4 activos; L1/L2 esperan cierre.
   int ct=0;
   SE_OnTick(g_SysState[si].SE,sym,ct);

   if(confOn)
   {
      int ch=0;
      SE_OnTick(g_SysState[si].SE_H1,sym,ch);
      ConfluenciaUpdateArming(si);
   }
   if(confOn || s2On)
   {
      int cm=0;
      SE_OnTick(g_SysState[si].SE_M3,sym,cm);
   }

   //--- Estrategia 2: zona 4H (L1-L2 + 50%) y order blocks 1H
   Strat2Update(si);
}

//+==================================================================+
//| ESTRATEGIA ÚNICA: ESTRUCTURA DE LÍNEAS (H1) + CONFLUENCIA (M3)   |
//|                                                                  |
//| 1) El motor de líneas L1-L4 (el mismo de siempre) corre SIEMPRE  |
//|    en H1 (estructura madre) y en M3 (estructura de entrada).     |
//| 2) En H1: L1/L2 = rango (techo/suelo), EQ = 50%. El bias H1      |
//|    (alcista/bajista) manda la dirección: H1 alcista → solo       |
//|    compras; H1 bajista → solo ventas.                            |
//| 3) Zona de COMPRA = parte de abajo del rango H1 (≤ 50%); zona de |
//|    VENTA = parte de arriba (≥ 50%). Con solo TOCAR la zona se    |
//|    activa la búsqueda (aunque el precio salga de la zona).       |
//| 4) En M3 se espera un cambio de estructura (CHoCH) A FAVOR de la |
//|    estructura de H1: bajista→alcista en H1 alcista, o            |
//|    alcista→bajista en H1 bajista.                                |
//| 5) Al generarse el CHoCH de M3, el rango para medir el 50% es el |
//|    rango L1-L2 de M3 EN ESE MOMENTO; ese nivel queda CONGELADO   |
//|    y allí se coloca la orden LIMIT con el SL/TP del EA.          |
//|    allí se coloca una orden LIMIT de compra con el SL/TP del EA. |
//| 4) VENTA: simétrico (CHoCH alcista→bajista, cruce a la baja).    |
//| 5) Solo puede haber UNA posición abierta por par: al abrirse una |
//|    posición se eliminan las demás órdenes limit pendientes.      |
//|    Si la posición se pierde y el precio sigue en la zona, se     |
//|    puede buscar otra entrada (con CHoCH nuevo); si no está en    |
//|    la zona, hay que esperar un nuevo toque de la zona.           |
//| 6) Fase virtual (simulación) → LIVE: mismo sistema de gestión    |
//|    que el resto de estrategias (CV/CR, tabla de riesgo).         |
//+==================================================================+

//--- ¿Hay CUALQUIER posición abierta (EA o manual) en el par? -------
bool HasAnyPositionSymbol(int si)
{
   string sym=g_Symbols[si].name;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong t=PositionGetTicket(i);
      if(t==0) continue;
      if(PositionGetString(POSITION_SYMBOL)==sym) return true;
   }
   return false;
}

//--- Reinicio total del estado de confluencia -----------------------
void ConfluenciaResetState(int si)
{
   g_SysState[si].m3ChochDir=0;         g_SysState[si].m3ChochTime=0;
   g_SysState[si].confArmedBuy=false;   g_SysState[si].confArmedSell=false;
   g_SysState[si].confArmBuyTime=0;     g_SysState[si].confArmSellTime=0;
   g_SysState[si].confEntryBuy=0.0;     g_SysState[si].confEntrySell=0.0;
   g_SysState[si].confWaitBuy=false;    g_SysState[si].confWaitSell=false;
   g_SysState[si].confVPendBuy=false;   g_SysState[si].confVPendBuyPrice=0.0;
   g_SysState[si].confVPendSell=false;  g_SysState[si].confVPendSellPrice=0.0;
   ConfluenciaDeleteRealPendings(si);
}

//--- Reinicio por cambio de rango H1 (zonas nuevas → nuevo toque) ---
void ConfluenciaOnH1Change(int si, int dir)
{
   ConfluenciaResetState(si);
   Print("CONFL [",g_Symbols[si].name,"] estructura H1 ",
         (dir>0?"ALCISTA":"BAJISTA")," → zonas 50% reiniciadas (se requiere nuevo toque)");
}

//--- Toque de zona: solo con tocarla se activa la búsqueda ----------
void ConfluenciaUpdateArming(int si)
{
   if(!InpUseConfluencia)                  return;
   if(!g_SysState[si].SE_H1.Valid)         return;
   double eq=g_SysState[si].SE_H1.EQ;
   if(eq<=0.0)                             return;

   string   sym=g_Symbols[si].name;
   double   bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;
   datetime now=TimeCurrent();
   int      dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);

   //--- zona de COMPRA = parte de abajo del rango H1 (precio ≤ 50%)
   if(bid<=eq && !g_SysState[si].confArmedBuy)
   {
      g_SysState[si].confArmedBuy=true;
      g_SysState[si].confArmBuyTime=now;
      Print("CONFL [",sym,"] ZONA COMPRA H1 tocada (50%=",DoubleToString(eq,dg),
            ") → búsqueda de compras activa");
   }
   //--- zona de VENTA = parte de arriba del rango H1 (precio ≥ 50%)
   if(bid>=eq && !g_SysState[si].confArmedSell)
   {
      g_SysState[si].confArmedSell=true;
      g_SysState[si].confArmSellTime=now;
      Print("CONFL [",sym,"] ZONA VENTA H1 tocada (50%=",DoubleToString(eq,dg),
            ") → búsqueda de ventas activa");
   }
}

//--- CHoCH de M3 (cambio de estructura con la lógica de líneas) -----
void ConfluenciaProcessChoch(int si)
{
   if(!InpUseConfluencia)               return;
   if(!InpAllowConfluOrders)            return;
   int dir=g_SysState[si].m3ChochDir;
   if(dir==0)  return;
   g_SysState[si].m3ChochDir=0;          // consumir el evento
   if(g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused) return;
   datetime t=g_SysState[si].m3ChochTime;
   string   sym=g_Symbols[si].name;
   int      dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);

   //--- el rango para el 50% es L1-L2 de M3 EN EL MOMENTO del CHoCH
   if(!g_SysState[si].SE_M3.Valid)                 return;
   double mid=NormalizeDouble(g_SysState[si].SE_M3.EQ,dg);
   if(mid<=0.0)                                    return;

   //--- solo una posición y una limit por par
   if(HasAnyPositionSymbol(si))                    return;
   if(ConfluenciaHasPending(si))                   return;

   bool buySide =(g_SysState[si].SE_H1.Valid &&
                  g_SysState[si].SE_H1.Bias==BIAS_BULLISH);   // H1 alcista → solo compras
   bool sellSide=(g_SysState[si].SE_H1.Valid &&
                  g_SysState[si].SE_H1.Bias==BIAS_BEARISH);   // H1 bajista → solo ventas

   //--- COMPRA: CHoCH bajista→alcista a favor de la estructura H1.
   //    SOLO se congela el 50% aquí; la LIMIT se coloca cuando el precio
   //    quede por ENCIMA del nivel (ver ConfluenciaTryPlace): así la orden
   //    es siempre llenable y no se generan virtuales que pierden al instante.
   if(dir>0 && buySide && g_SysState[si].confArmedBuy &&
      t>=g_SysState[si].confArmBuyTime)
   {
      g_SysState[si].confEntryBuy=mid;             // nivel CONGELADO en el CHoCH
      g_SysState[si].confWaitBuy=true;             // espera del lado correcto
      g_SysState[si].confWaitSell=false;
      Print("CONFL [",sym,"] CHoCH M3 bajista→alcista → 50% de L1-L2 M3 CONGELADO en ",
            DoubleToString(mid,dg)," → esperando lado COMPRA (precio encima del 50%)");
   }
   //--- VENTA: CHoCH alcista→bajista a favor de la estructura H1
   else if(dir<0 && sellSide && g_SysState[si].confArmedSell &&
           t>=g_SysState[si].confArmSellTime)
   {
      g_SysState[si].confEntrySell=mid;            // nivel CONGELADO en el CHoCH
      g_SysState[si].confWaitSell=true;            // espera del lado correcto
      g_SysState[si].confWaitBuy=false;
      Print("CONFL [",sym,"] CHoCH M3 alcista→bajista → 50% de L1-L2 M3 CONGELADO en ",
            DoubleToString(mid,dg)," → esperando lado VENTA (precio debajo del 50%)");
   }
}

//--- Coloca la LIMIT cuando el precio está del lado correcto del 50% congelado.
//    COMPRA: precio por ENCIMA del nivel (limit abajo → se llena en el retroceso).
//    VENTA : precio por DEBAJO del nivel (limit arriba → se llena en el rebote).
void ConfluenciaTryPlace(int si)
{
   if(!InpUseConfluencia)                                   return;
   if(!InpAllowConfluOrders)                                return;
   if(g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused) return;
   if(HasAnyPositionSymbol(si))
   { g_SysState[si].confWaitBuy=false; g_SysState[si].confWaitSell=false; return; }
   if(ConfluenciaHasPending(si)) return;   // ya hay una limit o virtual en curso

   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;

   //--- COMPRA: solo si el precio ya está POR ENCIMA del 50% congelado
   if(g_SysState[si].confWaitBuy && bid>g_SysState[si].confEntryBuy)
   {
      if(ConfluenciaPlacePending(si,+1,g_SysState[si].confEntryBuy))
      { g_SysState[si].confWaitBuy=false;
        Print("CONFL [",sym,"] precio encima del 50% congelado → LIMIT COMPRA colocada"); }
   }
   //--- VENTA: solo si el precio ya está POR DEBAJO del 50% congelado
   else if(g_SysState[si].confWaitSell && bid<g_SysState[si].confEntrySell)
   {
      if(ConfluenciaPlacePending(si,-1,g_SysState[si].confEntrySell))
      { g_SysState[si].confWaitSell=false;
        Print("CONFL [",sym,"] precio debajo del 50% congelado → LIMIT VENTA colocada"); }
   }
}

//--- Coloca la orden limit (virtual en fase SIM, real en LIVE) ------
bool ConfluenciaPlacePending(int si, int dir, double price)
{
   string sym=g_Symbols[si].name;
   int    dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   int    st =STRAT_CONFLUENCIA;
   bool   isLive=g_SysState[si].strategies[st].isLive;
   double lots =GetPairLot(si);
   int    posType=(dir>0)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   double sl  =CalcSL(sym,si,price,posType);
   double tp  =CalcTP(sym,si,price,posType);

   //--- fase virtual: orden limit simulada
   if(!isLive)
   {
      if(dir>0){ g_SysState[si].confVPendBuy=true;   g_SysState[si].confVPendBuyPrice=price;  }
      else     { g_SysState[si].confVPendSell=true;  g_SysState[si].confVPendSellPrice=price; }
      Print("CONFL [",sym,"] vLIMIT ",(dir>0?"BUY":"SELL")," @",DoubleToString(price,dg),
            " SL=",DoubleToString(sl,dg)," TP=",DoubleToString(tp,dg),
            " CV=",g_SysState[si].strategies[st].CV,
            " NIVEL=",PairLevel(si)," Lot=",DoubleToString(lots,2));
      return true;
   }

   //--- fase LIVE: orden limit real con el SL/TP del EA
   if(IsWeeklyCloseWindow()) return false;   // no dejar límites nuevos en la ventana semanal
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double minDist=(double)SymbolInfoInteger(sym,SYMBOL_TRADE_STOPS_LEVEL)*
                  SymbolInfoDouble(sym,SYMBOL_POINT);
   if(dir>0 && (ask-price)<minDist)
   { Print("CONFL [",sym,"] BUY LIMIT muy cerca del precio → reintenta");  return false; }
   if(dir<0 && (price-bid)<minDist)
   { Print("CONFL [",sym,"] SELL LIMIT muy cerca del precio → reintenta"); return false; }

   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action =TRADE_ACTION_PENDING;
   req.symbol =sym;
   req.volume =lots;
   req.type   =(dir>0)?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT;
   req.price  =price;
   req.sl     =sl;
   req.tp     =tp;
   req.magic  =GetStrategyMagic(si,st);
   req.deviation=20;
   req.comment=StringFormat("%s_%s_CONF_LMT_N%d",InpComment,sym,PairLevel(si));
   if(!OrderSend(req,res) || (res.retcode!=TRADE_RETCODE_DONE &&
                              res.retcode!=TRADE_RETCODE_PLACED))
   { Print("ERROR CONFL Limit [",sym,"]: ",res.retcode); return false; }
   Print("CONFL [",sym,"] LIMIT ",(dir>0?"BUY":"SELL")," #",res.order,
         " @",DoubleToString(price,dg),
         " SL=",DoubleToString(sl,dg)," TP=",DoubleToString(tp,dg),
         " Lot=",DoubleToString(lots,2));
   return true;
}

//--- ¿Hay ya una limit (virtual o real) del par? -------------------
bool ConfluenciaHasPending(int si)
{
   if(g_SysState[si].confVPendBuy || g_SysState[si].confVPendSell) return true;
   string sym=g_Symbols[si].name;
   long   magic=GetStrategyMagic(si,STRAT_CONFLUENCIA);
   for(int i=OrdersTotal()-1;i>=0;i--)
   { ulong t=OrderGetTicket(i); if(t==0) continue;
     if(OrderGetString(ORDER_SYMBOL)!=sym)              continue;
     if(OrderGetInteger(ORDER_MAGIC)!=magic)            continue;
     long ty=OrderGetInteger(ORDER_TYPE);
     if(ty==ORDER_TYPE_BUY_LIMIT || ty==ORDER_TYPE_SELL_LIMIT) return true; }
   return false;
}

//--- Apertura virtual al tocar el nivel de la limit simulada --------
void ConfluenciaStartVirtual(int si, int dir, double price)
{
   string sym=g_Symbols[si].name;
   int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   int    st =STRAT_CONFLUENCIA;
   int    posType=(dir>0)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   g_SysState[si].strategies[st].virtualDir       =dir;
   g_SysState[si].strategies[st].virtualOpen      =price;
   g_SysState[si].strategies[st].virtualOpenLevel =PairLevel(si);   // nivel de apertura (regla −3/−4)
   g_SysState[si].strategies[st].virtualSL_price  =CalcSL(sym,si,price,posType);
   g_SysState[si].strategies[st].virtualTP_price  =CalcTP(sym,si,price,posType);
   g_SysState[si].strategies[st].virtualSLMoved   =false;
   g_SysState[si].strategies[st].virtualActive    =true;
   Print("vOPEN [",sym,"/",g_SysState[si].strategies[st].name,"] ",
         (dir>0?"BUY":"SELL")," (fill 50% M3) @",DoubleToString(price,dg),
         " CV=",g_SysState[si].strategies[st].CV,
         " NIVEL=",g_SysState[si].strategies[st].virtualOpenLevel,
         " SL=",DoubleToString(g_SysState[si].strategies[st].virtualSL_price,dg),
         " TP=",DoubleToString(g_SysState[si].strategies[st].virtualTP_price,dg));
}

//--- Ejecución de las límites virtuales -----------------------------
void ConfluenciaCheckVirtualFills(int si)
{
   if(!InpUseConfluencia)                                       return;
   if(!InpAllowConfluOrders)                                    return;
   if(g_SysState[si].strategies[STRAT_CONFLUENCIA].isLive)      return;
   if(g_SysState[si].strategies[STRAT_CONFLUENCIA].virtualActive) return;
   if(HasAnyPositionSymbol(si))                                 return;

   string sym=g_Symbols[si].name;
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);

   //--- COMPRA limit: se ejecuta cuando el Ask baja hasta el nivel
   if(g_SysState[si].confVPendBuy && ask>0.0 &&
      ask<=g_SysState[si].confVPendBuyPrice)
   {
      ConfluenciaStartVirtual(si,+1,g_SysState[si].confVPendBuyPrice);
      g_SysState[si].confVPendBuy=false;   g_SysState[si].confVPendBuyPrice=0.0;
      g_SysState[si].confVPendSell=false;  g_SysState[si].confVPendSellPrice=0.0; // una posición → resto fuera
      return;
   }
   //--- VENTA limit: se ejecuta cuando el Bid sube hasta el nivel
   if(g_SysState[si].confVPendSell && bid>0.0 &&
      bid>=g_SysState[si].confVPendSellPrice)
   {
      ConfluenciaStartVirtual(si,-1,g_SysState[si].confVPendSellPrice);
      g_SysState[si].confVPendBuy=false;   g_SysState[si].confVPendBuyPrice=0.0;
      g_SysState[si].confVPendSell=false;  g_SysState[si].confVPendSellPrice=0.0;
   }
}

//--- Borra las órdenes limit reales de la estrategia en el símbolo --
void ConfluenciaDeleteRealPendings(int si)
{
   string sym=g_Symbols[si].name;
   long   magic=GetStrategyMagic(si,STRAT_CONFLUENCIA);
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      ulong t=OrderGetTicket(i);
      if(t==0)                                          continue;
      if(OrderGetString(ORDER_SYMBOL)!=sym)             continue;
      if(OrderGetInteger(ORDER_MAGIC)!=magic)           continue;
      MqlTradeRequest req={}; MqlTradeResult res={};
      req.action=TRADE_ACTION_REMOVE; req.order=t;
      if(OrderSend(req,res))
         Print("CONFL [",sym,"] orden limit #",t," eliminada");
   }
}

//--- Gestión de pendientes (corre SIEMPRE, incluso sin horario/CB) --
void ConfluenciaManagePendings(int si)
{
   if(!InpUseConfluencia) return;

   bool hasPos =HasAnyPositionSymbol(si);
   bool riskOff=g_CircuitBreakerOn ||
                g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused ||
                (InpUseTimeFilter && !IsTradeTimeAllowed());

   if(!hasPos && !riskOff) return;

   //--- posición abierta (o riesgo pausado) → fuera las límites restantes
   if(g_SysState[si].confVPendBuy || g_SysState[si].confVPendSell)
   {
      if(hasPos)
         Print("CONFL [",g_Symbols[si].name,"] posición abierta → se retiran las demás órdenes limit");
      g_SysState[si].confVPendBuy=false;   g_SysState[si].confVPendBuyPrice=0.0;
      g_SysState[si].confVPendSell=false;  g_SysState[si].confVPendSellPrice=0.0;
   }
   ConfluenciaDeleteRealPendings(si);
}

//--- Cierre de un trade de la estrategia (TP o SL) ------------------
//    Limpia esperas y desactiva la búsqueda si el precio ya no está
//    en la zona correspondiente (hay que volver a tocarla).
void ConfluenciaOnTradeClosed(int si)
{
   g_SysState[si].confEntryBuy=0.0;
   g_SysState[si].confEntrySell=0.0;
   g_SysState[si].confWaitBuy=false;
   g_SysState[si].confWaitSell=false;

   if(!g_SysState[si].SE_H1.Valid) return;
   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double eq =g_SysState[si].SE_H1.EQ;
   if(bid<=0.0 || eq<=0.0) return;

   if(bid>eq && g_SysState[si].confArmedBuy)
   { g_SysState[si].confArmedBuy=false;
     Print("CONFL [",sym,"] fuera de la zona de COMPRA → búsqueda desactivada hasta un nuevo toque"); }
   if(bid<eq && g_SysState[si].confArmedSell)
   { g_SysState[si].confArmedSell=false;
     Print("CONFL [",sym,"] fuera de la zona de VENTA → búsqueda desactivada hasta un nuevo toque"); }
}

//--- Orquestador por símbolo (llamado desde UpdateAllStrategies) ----
void UpdateConfluencia(int si)
{
   if(!InpUseConfluencia) return;

   //--- Con una posición abierta en el par no avanza ningún flujo de
   //    entrada: las esperas y los CHoCH que lleguen caducan; al cerrar
   //    la posición hay que empezar de nuevo (nuevo toque si corresponde).
   if(HasAnyPositionSymbol(si))
   {
      g_SysState[si].m3ChochDir=0;
      g_SysState[si].confWaitBuy=false;
      g_SysState[si].confWaitSell=false;
      return;
   }

   ConfluenciaProcessChoch(si);
   ConfluenciaTryPlace(si);
   ConfluenciaCheckVirtualFills(si);
}

//+------------------------------------------------------------------+
//| ESTRATEGIA 2: ORDENES (virtual → LIVE, mismo ciclo que E1)      |
//|  · CHoCH M3 a favor del rebote → 50% L1-L2 M3 CONGELADO.        |
//|  · COMPRA: espera precio por ENCIMA del nivel; VENTA: por DEBAJO.|
//|  · Fase virtual: LIMIT simulada → fill → vOPEN virtual con CV.   |
//|  · Fase LIVE: LIMIT real con magia S2 y SL/TP del par.          |
//+------------------------------------------------------------------+
bool Strat2HasPending(int si)
{
   if(g_SysState[si].s2VPendBuy || g_SysState[si].s2VPendSell) return true;
   string sym=g_Symbols[si].name;
   long   magic=GetStrategyMagic(si,STRAT_S2);
   for(int i=OrdersTotal()-1;i>=0;i--)
   { ulong t=OrderGetTicket(i); if(t==0) continue;
     if(OrderGetString(ORDER_SYMBOL)!=sym)              continue;
     if(OrderGetInteger(ORDER_MAGIC)!=magic)            continue;
     long ty=OrderGetInteger(ORDER_TYPE);
     if(ty==ORDER_TYPE_BUY_LIMIT || ty==ORDER_TYPE_SELL_LIMIT) return true; }
   return false;
}

//--- Coloca la orden limit (virtual en fase simulada, real en LIVE)
bool Strat2PlacePending(int si, int dir, double price)
{
   string sym=g_Symbols[si].name;
   int    dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   int    st =STRAT_S2;
   bool   isLive=g_SysState[si].strategies[st].isLive;
   double lots =GetPairLot(si);
   int    posType=(dir>0)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   double sl  =CalcSL(sym,si,price,posType);
   double tp  =CalcTP(sym,si,price,posType);

   //--- fase virtual: orden limit simulada
   if(!isLive)
   {
      if(dir>0){ g_SysState[si].s2VPendBuy=true;  g_SysState[si].s2VPendBuyPrice=price;  }
      else     { g_SysState[si].s2VPendSell=true; g_SysState[si].s2VPendSellPrice=price; }
      Print("S2 [",sym,"] vLIMIT ",(dir>0?"BUY":"SELL")," @",DoubleToString(price,dg),
            " SL=",DoubleToString(sl,dg)," TP=",DoubleToString(tp,dg),
            " CV=",g_SysState[si].strategies[st].CV,
            " NIVEL=",PairLevel(si)," Lot=",DoubleToString(lots,2));
      return true;
   }

   //--- fase LIVE: orden limit real con el SL/TP del EA
   if(IsWeeklyCloseWindow()) return false;
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double minDist=(double)SymbolInfoInteger(sym,SYMBOL_TRADE_STOPS_LEVEL)*
                  SymbolInfoDouble(sym,SYMBOL_POINT);
   if(dir>0 && (ask-price)<minDist)
   { Print("S2 [",sym,"] BUY LIMIT muy cerca del precio → reintenta");  return false; }
   if(dir<0 && (price-bid)<minDist)
   { Print("S2 [",sym,"] SELL LIMIT muy cerca del precio → reintenta"); return false; }

   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action =TRADE_ACTION_PENDING;
   req.symbol =sym;
   req.volume =lots;
   req.type   =(dir>0)?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT;
   req.price  =price;
   req.sl     =sl;
   req.tp     =tp;
   req.magic  =GetStrategyMagic(si,st);
   req.deviation=20;
   req.comment=StringFormat("%s_%s_S2_LMT_N%d",InpComment,sym,PairLevel(si));
   if(!OrderSend(req,res) || (res.retcode!=TRADE_RETCODE_DONE &&
                              res.retcode!=TRADE_RETCODE_PLACED))
   { Print("ERROR S2 Limit [",sym,"]: ",res.retcode); return false; }
   Print("S2 [",sym,"] LIMIT ",(dir>0?"BUY":"SELL")," #",res.order,
         " @",DoubleToString(price,dg),
         " SL=",DoubleToString(sl,dg)," TP=",DoubleToString(tp,dg),
         " Lot=",DoubleToString(lots,2));
   return true;
}

//--- Coloca la LIMIT cuando el precio está del lado correcto del 50% congelado
void Strat2TryPlace(int si)
{
   if(!InpUseStrat2)                                    return;
   if(!InpAllowStrat2Orders)                            return;
   if(g_SysState[si].strategies[STRAT_S2].cbPaused)     return;
   if(HasAnyPositionSymbol(si))
   { g_SysState[si].s2WaitBuy=false; g_SysState[si].s2WaitSell=false; return; }
   if(Strat2HasPending(si)) return;   // ya hay una limit o virtual en curso

   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;

   if(g_SysState[si].s2WaitBuy && bid>g_SysState[si].s2EntryBuy)
   {
      if(Strat2PlacePending(si,+1,g_SysState[si].s2EntryBuy))
      { g_SysState[si].s2WaitBuy=false;
        Print("S2 [",sym,"] precio encima del 50% congelado → LIMIT COMPRA colocada"); }
   }
   else if(g_SysState[si].s2WaitSell && bid<g_SysState[si].s2EntrySell)
   {
      if(Strat2PlacePending(si,-1,g_SysState[si].s2EntrySell))
      { g_SysState[si].s2WaitSell=false;
        Print("S2 [",sym,"] precio debajo del 50% congelado → LIMIT VENTA colocada"); }
   }
}

//--- Apertura virtual al tocar el nivel de la limit simulada --------
void Strat2StartVirtual(int si, int dir, double price)
{
   string sym=g_Symbols[si].name;
   int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   int    st =STRAT_S2;
   int    posType=(dir>0)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   g_SysState[si].strategies[st].virtualDir       =dir;
   g_SysState[si].strategies[st].virtualOpen      =price;
   g_SysState[si].strategies[st].virtualOpenLevel =PairLevel(si);
   g_SysState[si].strategies[st].virtualSL_price  =CalcSL(sym,si,price,posType);
   g_SysState[si].strategies[st].virtualTP_price  =CalcTP(sym,si,price,posType);
   g_SysState[si].strategies[st].virtualSLMoved   =false;
   g_SysState[si].strategies[st].virtualActive    =true;
   Print("vOPEN [",sym,"/",g_SysState[si].strategies[st].name,"] ",
         (dir>0?"BUY":"SELL")," (fill 50% M3) @",DoubleToString(price,dg),
         " CV=",g_SysState[si].strategies[st].CV,
         " NIVEL=",g_SysState[si].strategies[st].virtualOpenLevel,
         " SL=",DoubleToString(g_SysState[si].strategies[st].virtualSL_price,dg),
         " TP=",DoubleToString(g_SysState[si].strategies[st].virtualTP_price,dg));
}

//--- Ejecución de las límites virtuales -----------------------------
void Strat2CheckVirtualFills(int si)
{
   if(!InpUseStrat2)                                        return;
   if(!InpAllowStrat2Orders)                                return;
   if(g_SysState[si].strategies[STRAT_S2].isLive)           return;
   if(g_SysState[si].strategies[STRAT_S2].virtualActive)    return;
   if(HasAnyPositionSymbol(si))                             return;

   string sym=g_Symbols[si].name;
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);

   if(g_SysState[si].s2VPendBuy && ask>0.0 &&
      ask<=g_SysState[si].s2VPendBuyPrice)
   {
      Strat2StartVirtual(si,+1,g_SysState[si].s2VPendBuyPrice);
      g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
      g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0;
      return;
   }
   if(g_SysState[si].s2VPendSell && bid>0.0 &&
      bid>=g_SysState[si].s2VPendSellPrice)
   {
      Strat2StartVirtual(si,-1,g_SysState[si].s2VPendSellPrice);
      g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
      g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0;
   }
}

//--- Borra las órdenes limit reales de la Estrategia 2 en el símbolo
void Strat2DeleteRealPendings(int si)
{
   string sym=g_Symbols[si].name;
   long   magic=GetStrategyMagic(si,STRAT_S2);
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      ulong t=OrderGetTicket(i);
      if(t==0)                                          continue;
      if(OrderGetString(ORDER_SYMBOL)!=sym)             continue;
      if(OrderGetInteger(ORDER_MAGIC)!=magic)           continue;
      MqlTradeRequest req={}; MqlTradeResult res={};
      req.action=TRADE_ACTION_REMOVE; req.order=t;
      if(OrderSend(req,res))
         Print("S2 [",sym,"] orden limit #",t," eliminada");
   }
}

//--- Gestión de pendientes (corre SIEMPRE, incluso sin horario/CB) --
void Strat2ManagePendings(int si)
{
   if(!InpUseStrat2) return;

   bool hasPos =HasAnyPositionSymbol(si);
   bool riskOff=g_CircuitBreakerOn ||
                g_SysState[si].strategies[STRAT_S2].cbPaused ||
                (InpUseTimeFilter && !IsTradeTimeAllowed());

   if(!hasPos && !riskOff) return;

   if(g_SysState[si].s2VPendBuy || g_SysState[si].s2VPendSell)
   {
      if(hasPos)
         Print("S2 [",g_Symbols[si].name,"] posición abierta → se retiran las demás órdenes limit");
      g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
      g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0;
   }
   Strat2DeleteRealPendings(si);
}

//--- Cierre de un trade de la Estrategia 2 (TP o SL) ----------------
//    Limpia esperas/entradas congeladas; una zona armada solo se
//    desactiva si el precio ya no está en el lado de la entrada.
void Strat2OnTradeClosed(int si)
{
   g_SysState[si].s2EntryBuy=0.0;
   g_SysState[si].s2EntrySell=0.0;
   g_SysState[si].s2WaitBuy=false;
   g_SysState[si].s2WaitSell=false;

   if(!g_SysState[si].SE_H4.Valid) return;
   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;

   for(int k=0;k<g_SysState[si].ob2Count;k++)
   {
      if(!g_SysState[si].ob2[k].Active)     continue;
      if(g_SysState[si].ob2[k].Mitigated)   continue;
      if(!g_SysState[si].ob2[k].Armed)      continue;
      if(!g_SysState[si].ob2[k].EntryFrozen) continue;
      // La zona congelada ya no sirve para el próximo ciclo: requiere nuevo toque
      g_SysState[si].ob2[k].EntryFrozen=false;
      g_SysState[si].ob2[k].EntryPrice=0.0;
      g_SysState[si].ob2[k].Armed=false;
      Print("S2 [",sym,"] ciclo cerrado → zona ",
            (g_SysState[si].ob2[k].IsBullish?"COMPRA":"VENTA"),
            " desactivada hasta un nuevo toque");
   }
}

//--- Orquestador de órdenes por símbolo (llamado desde UpdateAllStrategies)
void UpdateStrat2Orders(int si)
{
   if(!InpUseStrat2) return;

   if(HasAnyPositionSymbol(si))
   {
      g_SysState[si].m3ChochDir2=0;
      g_SysState[si].s2WaitBuy=false;
      g_SysState[si].s2WaitSell=false;
      return;
   }

   Strat2ProcessChoch(si);
   Strat2TryPlace(si);
   Strat2CheckVirtualFills(si);
}

//+------------------------------------------------------------------+
//| DIBUJO DE LÍNEAS DE ESTRUCTURA EN EL GRÁFICO (visual de smc2)    |
//| Colores vivos (visibles en fondo claro y oscuro) + etiqueta con  |
//| nombre y precio al lado derecho de cada línea.                   |
//+------------------------------------------------------------------+
#define SE_PREFIX      "GQP_SE_"
#define SE_LBL_OFF_BARS 6          // barras hacia el futuro para la etiqueta

void SE_HLine(string name,double price,color clr,ENUM_LINE_STYLE sty,int w,string lbl)
{
   string tn=name+"_T";
   if(price<=0){ ObjectDelete(0,name); ObjectDelete(0,tn); return; }
   if(ObjectFind(0,name)<0)
   { ObjectCreate(0,name,OBJ_HLINE,0,0,price);
     ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,name,OBJPROP_HIDDEN,true); }
   ObjectSetDouble (0,name,OBJPROP_PRICE,price);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,sty);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,w);
   ObjectSetInteger(0,name,OBJPROP_BACK,true);

   //--- etiqueta con nombre + precio a la derecha de la línea
   datetime tt=iTime(_Symbol,PERIOD_CURRENT,0)
             +PeriodSeconds(PERIOD_CURRENT)*SE_LBL_OFF_BARS;
   string   txt=lbl+"  "+DoubleToString(price,(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
   if(ObjectFind(0,tn)<0)
   { ObjectCreate(0,tn,OBJ_TEXT,0,tt,price);
     ObjectSetInteger(0,tn,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,tn,OBJPROP_HIDDEN,true); }
   ObjectSetInteger(0,tn,OBJPROP_TIME,tt);
   ObjectSetDouble (0,tn,OBJPROP_PRICE,price);
   ObjectSetString (0,tn,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,tn,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,tn,OBJPROP_FONTSIZE,8);
   ObjectSetString (0,tn,OBJPROP_FONT,"Arial Bold");
   ObjectSetInteger(0,tn,OBJPROP_ANCHOR,ANCHOR_LEFT);
   ObjectSetInteger(0,tn,OBJPROP_BACK,false);
}

//--- Rectángulo relleno (zonas 50%) a lo ancho del gráfico ----------
void SE_Rect(string name,double p1,double p2,color clr)
{
   if(p1<=0.0||p2<=0.0){ ObjectDelete(0,name); return; }
   datetime t1=TimeCurrent()-PeriodSeconds(PERIOD_CURRENT)*300;
   datetime t2=TimeCurrent()+PeriodSeconds(PERIOD_CURRENT)*50;
   double   top=MathMax(p1,p2), bot=MathMin(p1,p2);
   uchar    alpha=(uchar)(255-(86*255/100));          // transparencia 86%
   color    c=(color)ColorToARGB(clr,alpha);
   if(ObjectFind(0,name)<0)
   { ObjectCreate(0,name,OBJ_RECTANGLE,0,t1,top,t2,bot);
     ObjectSetInteger(0,name,OBJPROP_FILL,true);
     ObjectSetInteger(0,name,OBJPROP_BACK,true);
     ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,name,OBJPROP_HIDDEN,true); }
   ObjectSetInteger(0,name,OBJPROP_TIME, 0,t1);
   ObjectSetDouble (0,name,OBJPROP_PRICE,0,top);
   ObjectSetInteger(0,name,OBJPROP_TIME, 1,t2);
   ObjectSetDouble (0,name,OBJPROP_PRICE,1,bot);
   ObjectSetInteger(0,name,OBJPROP_COLOR,c);
   ObjectSetInteger(0,name,OBJPROP_BGCOLOR,c);
}

//--- Etiqueta de zona (nombre + estado) -----------------------------
void SE_ZoneLabel(string name,double price,string txt,color clr)
{
   if(price<=0.0){ ObjectDelete(0,name); return; }
   datetime tt=iTime(_Symbol,PERIOD_CURRENT,0)
             +PeriodSeconds(PERIOD_CURRENT)*SE_LBL_OFF_BARS;
   if(ObjectFind(0,name)<0)
   { ObjectCreate(0,name,OBJ_TEXT,0,tt,price);
     ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
     ObjectSetInteger(0,name,OBJPROP_FONTSIZE,8);
     ObjectSetString (0,name,OBJPROP_FONT,"Arial Bold");
     ObjectSetInteger(0,name,OBJPROP_ANCHOR,ANCHOR_LEFT);
     ObjectSetInteger(0,name,OBJPROP_BACK,false); }
   ObjectSetInteger(0,name,OBJPROP_TIME,tt);
   ObjectSetDouble (0,name,OBJPROP_PRICE,price);
   ObjectSetString (0,name,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
}

//+==================================================================+
//| ESTRATEGIA 2: ZONA 4H (L1-L2 + 50%) + ORDER BLOCKS HISTÓRICOS    |
//|                                                                  |
//| 1) El motor de líneas L1-L4 corre en 4H → rango L1-L2 + 50%(EQ). |
//| 2) Se buscan order blocks HISTÓRICOS con confirmación:           |
//|    - COMPRA: última vela BAJISTA antes de un movimiento fuerte al |
//|      alza, confirmada por un imbalance/FVG (grupo de 3 velas).   |
//|    - VENTA : última vela ALCISTA antes de un movimiento bajista,  |
//|      confirmada por el mismo tipo de imbalance.                  |
//| 3) La zona marcada = DESDE EL INICIO DEL IMBALANCE HASTA EL      |
//|    FINAL DEL ORDER BLOCK (rectángulo de precio y tiempo).        |
//| 4) El precio rebota en COMPRA en las zonas POR DEBAJO del precio |
//|    y en VENTA en las zonas POR ENCIMA.                           |
//| 5) Prioridad: zonas DENTRO del rango L1-L2 (siempre visibles).   |
//|    Cuando el precio SOBREPASA L1/L2, se activan además las zonas |
//|    históricas FUERA del rango, del lado por donde busca rebote.  |
//+==================================================================+
//--- borra los objetos gráficos de la Estrategia 2 del símbolo ------
void Strat2DeleteObjects(int si)
{
   string pfx=SE_PREFIX+"S2_"+g_Symbols[si].name+"_";
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   { string n=ObjectName(0,i,0,-1);
     if(StringFind(n,pfx)==0) ObjectDelete(0,n); }
}

//--- reset total del estado de la Estrategia 2 ----------------------
void Strat2ResetState(int si)
{
   ZeroMemory(g_SysState[si].SE_H4);
   g_SysState[si].h4LastBar=0;
   g_SysState[si].ob1hLastBar=0;
   g_SysState[si].ob2Count=0;
   g_SysState[si].ob2Buys=0;
   g_SysState[si].ob2Sells=0;
   g_SysState[si].ob2BuyRange=0;
   g_SysState[si].ob2SellRange=0;
   g_SysState[si].ob2Outside=false;
   g_SysState[si].ob2Mitigated=0;
   g_SysState[si].ob2Armed=0;
   g_SysState[si].ob2Frozen=0;
   g_SysState[si].m3ChochDir2=0;
   g_SysState[si].m3ChochTime2=0;
   g_SysState[si].s2EntryBuy=0.0;    g_SysState[si].s2EntrySell=0.0;
   g_SysState[si].s2WaitBuy=false;   g_SysState[si].s2WaitSell=false;
   g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0;
   g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0;
   for(int k=0;k<STRAT2_STORED_OBS;k++) ZeroMemory(g_SysState[si].ob2[k]);
   Strat2DeleteObjects(si);
}

//--- guarda una zona (OB + imbalance) en el array del par -----------
void Strat2AddZone(int si,bool isBull,
                   double obH,double obL,datetime obT,
                   double zT,double zB,datetime gA,datetime gB,
                   double L1,double L2)
{
   int maxStore=STRAT2_STORED_OBS;
   int lado=0;
   for(int k=0;k<g_SysState[si].ob2Count;k++)
      if(g_SysState[si].ob2[k].IsBullish==isBull) lado++;
   if(lado>=maxStore/2) return;

   Strat2OrderBlock ob;
   ZeroMemory(ob);
   ob.Active=true;
   ob.IsBullish=isBull;
   ob.OBHigh=obH; ob.OBLow=obL; ob.OBTime=obT;
   ob.ZoneTop=zT; ob.ZoneBottom=zB;
   ob.GroupStart=gA; ob.GroupEnd=gB;
   ob.InRange=(zB>=L2 && zT<=L1);
   ob.FoundTime=gB;
   g_SysState[si].ob2[g_SysState[si].ob2Count]=ob;
   g_SysState[si].ob2Count++;
}

//--- escanea 1H: OB + imbalance en el grupo de 3 velas --------------
//    En MQL5 el índice 0 es la vela ACTUAL y 1 la anterior: j es la
//    vela más RECIENTE del grupo; j+1 la media; j+2 la más ANTIGUA.
//    - FVG ALCISTA: low(j) > high(j+2) → inicio del imbalance = high(j+2)
//      OB de COMPRA: la vela BAJISTA del grupo (j+2 o j+1). Zona:
//      high(j+2) → low(OB).
//    - FVG BAJISTA: high(j) < low(j+2) → inicio del imbalance = low(j+2)
//      OB de VENTA: la vela ALCISTA del grupo. Zona: low(j+2) → high(OB).
void Strat2ScanOBs(int si)
{
   //--- conservar el estado de flujo (armado/entrada congelada) de las
   //    zonas que ya existían: el array se reconstruye en cada escaneo.
   Strat2OrderBlock old2[STRAT2_STORED_OBS];
   int prevCount=g_SysState[si].ob2Count;
   if(prevCount>STRAT2_STORED_OBS) prevCount=STRAT2_STORED_OBS;
   for(int o=0;o<prevCount;o++) old2[o]=g_SysState[si].ob2[o];

   g_SysState[si].ob2Count=0;
   for(int k=0;k<STRAT2_STORED_OBS;k++) ZeroMemory(g_SysState[si].ob2[k]);

   StructureEngine SE=g_SysState[si].SE_H4;
   if(!SE.Valid) return;

   string sym=g_Symbols[si].name;
   ENUM_TIMEFRAMES tf=InpStrat2OBTF;
   int look=MathMax(30,InpStrat2Lookback);
   int periodTF=PeriodSeconds(tf);
   int minAge=MathMax(1,InpStrat2MinAge);

   //--- zona VÁLIDA: como mínimo InpStrat2MinAge velas cerradas después
   //    del final del grupo (j empieza en minAge+1 → velas 1..j-1 ya
   //    cerradas y posteriores al grupo = j-1 >= minAge).
   for(int j=minAge+1;j<=look-2;j++)
   {
      //--- j = velas ACTUALES más recientes del grupo (índice 0 = ahora)
      double O1=iOpen(sym,tf,j),   C1=iClose(sym,tf,j);
      double H1=iHigh(sym,tf,j),   L1=iLow(sym,tf,j);
      double O2=iOpen(sym,tf,j+1), C2=iClose(sym,tf,j+1);
      double H2=iHigh(sym,tf,j+1), L2v=iLow(sym,tf,j+1);
      double O3=iOpen(sym,tf,j+2), C3=iClose(sym,tf,j+2);
      double H3=iHigh(sym,tf,j+2), L3=iLow(sym,tf,j+2);
      if(O1<=0.0||O2<=0.0||O3<=0.0) continue;

      datetime tA=(datetime)iTime(sym,tf,j+2);   // vela más ANTIGUA del grupo
      datetime tB=tA+periodTF*3;                 // fin del grupo (3 velas)

      //--- imbalance ALCISTA (low reciente > high antigua) → COMPRA
      if(L1>H3)
      {
         // OB en la vela más antigua del grupo (bajista)
         if(C3<O3)
            Strat2AddZone(si,true,H3,L3,tA,H3,L3,tA,tB,SE.L1,SE.L2);
         // OB = vela del medio del grupo (bajista)
         if(C2<O2)
            Strat2AddZone(si,true,H2,L2v,tA+periodTF,H3,L2v,tA,tB,SE.L1,SE.L2);
      }
      //--- imbalance BAJISTA (high reciente < low antigua) → VENTA
      if(H1<L3)
      {
         // OB en la vela más antigua del grupo (alcista)
         if(C3>O3)
            Strat2AddZone(si,false,H3,L3,tA,H3,L3,tA,tB,SE.L1,SE.L2);
         // OB = vela del medio del grupo (alcista)
         if(C2>O2)
            Strat2AddZone(si,false,H2,L2v,tA+periodTF,H2,L3,tA,tB,SE.L1,SE.L2);
      }
   }

   //--- restaurar el flujo de las zonas que ya existían (mismo grupo)
   if(prevCount>0)
   { double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
     double tol=MathMax(pt*2.0,0.00001);
     for(int n=0;n<g_SysState[si].ob2Count;n++)
       for(int o=0;o<prevCount;o++)
       { if(!old2[o].Active) continue;
         if(old2[o].IsBullish!=g_SysState[si].ob2[n].IsBullish) continue;
         if(old2[o].GroupStart!=g_SysState[si].ob2[n].GroupStart) continue;
         if(MathAbs(old2[o].ZoneTop-g_SysState[si].ob2[n].ZoneTop)>tol) continue;
         g_SysState[si].ob2[n].Armed       =old2[o].Armed;
         g_SysState[si].ob2[n].ArmedTime   =old2[o].ArmedTime;
         g_SysState[si].ob2[n].EntryFrozen =old2[o].EntryFrozen;
         g_SysState[si].ob2[n].EntryPrice  =old2[o].EntryPrice;
         g_SysState[si].ob2[n].EntryTime   =old2[o].EntryTime;
         break; } }

   //--- calcular hasta dónde se extiende cada zona (mitigación)
   Strat2ComputeMitigation(si,true);
}

//--- Mitigación: el precio CRUZA el imbalance (deja de respetarlo).--
//    COMPRA: la zona se invalida cuando el precio baja y atraviesa TODA
//    la zona (imbalance + OB), saliendo por el lado contrario (ZoneBottom).
//    VENTA : la zona se invalida cuando el precio sube y atraviesa TODA
//    la zona, saliendo por el lado contrario (ZoneTop).
//    Tocar el rectángulo NO es mitigación: activa la búsqueda (Armed);
//    solo si el precio rompe la zona por completo se cancela la búsqueda
//    y cualquier entrada congelada de esa zona.
//    full=true  → revisar todo el historial tras el grupo.
//    full=false → revisar solo la vela actual (intrabar, cada tick).

//--- limpia la entrada congelada de paquete de la S2 para un lado -----
//    También retira el pendiente virtuAL/real de ese lado: la zona que
//    justificaba la orden ya no es válida (se mitigó).
void Strat2ClearS2Entry(int si,bool isBull)
{
   if(isBull)
   { g_SysState[si].s2EntryBuy=0.0;   g_SysState[si].s2WaitBuy=false;
     g_SysState[si].s2VPendBuy=false;  g_SysState[si].s2VPendBuyPrice=0.0; }
   else
   { g_SysState[si].s2EntrySell=0.0;  g_SysState[si].s2WaitSell=false;
     g_SysState[si].s2VPendSell=false; g_SysState[si].s2VPendSellPrice=0.0; }
   Strat2DeleteRealPendings(si);
}

void Strat2ComputeMitigation(int si,bool full)
{
   if(!g_SysState[si].SE_H4.Valid) return;
   string sym=g_Symbols[si].name;
   ENUM_TIMEFRAMES tf=InpStrat2OBTF;
   int periodTF=PeriodSeconds(tf);
   int look=MathMax(30,InpStrat2Lookback);

   double hac=iHigh(sym,tf,0);   // vela actual (índice 0, abierta)
   double lac=iLow(sym,tf,0);

   for(int k=0;k<g_SysState[si].ob2Count;k++)
   {
      //--- MQL5 no permite referencia a un elemento de array anidado;
      //    se accede por índice directamente.
      if(!g_SysState[si].ob2[k].Active) continue;
      if(g_SysState[si].ob2[k].Mitigated) continue;

      if(full)
      {
         for(int i=0;i<=look;i++)
         {
            datetime t=(datetime)iTime(sym,tf,i);
            if(t<g_SysState[si].ob2[k].GroupEnd) continue;   // solo velas posteriores al grupo
            double hi=iHigh(sym,tf,i), lo=iLow(sym,tf,i);
            bool hit=false;
            if(g_SysState[si].ob2[k].IsBullish)
               hit=(lo<=g_SysState[si].ob2[k].ZoneBottom);   // atraviesa TODA la zona (compra)
            else
               hit=(hi>=g_SysState[si].ob2[k].ZoneTop);      // atraviesa TODA la zona (venta)
            if(hit)
            {
               bool wasFrozen=g_SysState[si].ob2[k].EntryFrozen;
               g_SysState[si].ob2[k].Mitigated=true;
               g_SysState[si].ob2[k].MitigateTime=t;
               g_SysState[si].ob2[k].Armed=false;            // zona rota → fin de la búsqueda
               g_SysState[si].ob2[k].EntryFrozen=false;
               g_SysState[si].ob2[k].EntryPrice=0.0;
               if(wasFrozen)   // solo si ESTA zona tenía la entrada congelada
                  Strat2ClearS2Entry(si,g_SysState[si].ob2[k].IsBullish);
               break;
            }
         }
      }
      else
      {
         datetime t0=TimeCurrent();
         bool hit=false;
         if(g_SysState[si].ob2[k].IsBullish)
            hit=(lac<=g_SysState[si].ob2[k].ZoneBottom);
         else
            hit=(hac>=g_SysState[si].ob2[k].ZoneTop);
         if(hit && t0>=g_SysState[si].ob2[k].GroupEnd)
         {
            bool wasFrozen=g_SysState[si].ob2[k].EntryFrozen;
            g_SysState[si].ob2[k].Mitigated=true;
            g_SysState[si].ob2[k].MitigateTime=t0;
            g_SysState[si].ob2[k].Armed=false;
            g_SysState[si].ob2[k].EntryFrozen=false;
            g_SysState[si].ob2[k].EntryPrice=0.0;
            if(wasFrozen)   // solo si ESTA zona tenía la entrada congelada
               Strat2ClearS2Entry(si,g_SysState[si].ob2[k].IsBullish);
         }
      }
   }
}

//--- cuenta las zonas HOY visibles (según precio y rango 4H) --------
//    COMPRA: zona por DEBAJO del precio. Prioridad dentro del rango;
//    fuera del rango (por debajo de L2) solo si el precio está < L2.
//    VENTA : zona por ENCIMA del precio. Prioridad dentro del rango;
//    fuera del rango (por encima de L1) solo si el precio está > L1.
void Strat2RefreshCounts(int si)
{
   g_SysState[si].ob2Buys=0;
   g_SysState[si].ob2Sells=0;
   g_SysState[si].ob2BuyRange=0;
   g_SysState[si].ob2SellRange=0;
   g_SysState[si].ob2Outside=false;
   g_SysState[si].ob2Mitigated=0;
   g_SysState[si].ob2Armed=0;
   g_SysState[si].ob2Frozen=0;
   if(!g_SysState[si].SE_H4.Valid) return;

   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;
   double L1=g_SysState[si].SE_H4.L1, L2=g_SysState[si].SE_H4.L2;
   double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
   double tol=pt*2.0;
   bool inR=(bid>=L2-tol && bid<=L1+tol);
   g_SysState[si].ob2Outside=!inR;

   //--- contar zonas ya mitigadas / armadas / con entrada congelada
   for(int k=0;k<g_SysState[si].ob2Count;k++)
   { if(!g_SysState[si].ob2[k].Active) continue;
     if(g_SysState[si].ob2[k].Mitigated)   g_SysState[si].ob2Mitigated++;
     else if(g_SysState[si].ob2[k].EntryFrozen) g_SysState[si].ob2Frozen++;
     else if(g_SysState[si].ob2[k].Armed)      g_SysState[si].ob2Armed++; }

   int maxL=MathMax(1,MathMin(STRAT2_MAX_OBS,InpStrat2MaxOBs));
   int cb=0,cs=0;
   // prioridad: primero DENTRO del rango, luego FUERA (si aplica)
   for(int pass=0;pass<2 && (cb<maxL || cs<maxL);pass++)
      for(int k=0;k<g_SysState[si].ob2Count;k++)
      {
         Strat2OrderBlock ob=g_SysState[si].ob2[k];
         if(!ob.Active) continue;
         if(ob.Mitigated) continue;
         bool inRange=ob.InRange;
         if(pass==0 && !inRange) continue;
         if(pass==1 && inRange)  continue;
         if(ob.IsBullish)
         {
            if(cb>=maxL) continue;
            if(ob.ZoneTop>=bid) continue;               // no está debajo del precio
            if(!pass && !inRange) continue;
            if(!inRange && !(bid<L2-tol && ob.ZoneTop<=L2+tol)) continue;
            cb++; if(inRange) g_SysState[si].ob2BuyRange++;
         }
         else
         {
            if(cs>=maxL) continue;
            if(ob.ZoneBottom<=bid) continue;            // no está encima del precio
            if(!inRange && !(bid>L1+tol && ob.ZoneBottom>=L1-tol)) continue;
            cs++; if(inRange) g_SysState[si].ob2SellRange++;
         }
      }
   g_SysState[si].ob2Buys=cb;
   g_SysState[si].ob2Sells=cs;
}

//--- TOQUE de la zona: activa la búsqueda de CHoCH M3 --------------
//    COMPRA: el precio entra al rectángulo desde arriba (bid ≤ ZoneTop).
//    VENTA : el precio entra al rectángulo desde abajo (bid ≥ ZoneBottom).
//    Solo zonas vigentes y visibles según las reglas de prioridad.
void Strat2CheckTouches(int si)
{
   if(!g_SysState[si].SE_H4.Valid) return;
   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0) return;
   datetime now=TimeCurrent();

   for(int k=0;k<g_SysState[si].ob2Count;k++)
   {
      if(!g_SysState[si].ob2[k].Active)          continue;
      if(g_SysState[si].ob2[k].Mitigated)        continue;
      if(g_SysState[si].ob2[k].Armed)            continue;
      if(g_SysState[si].ob2[k].EntryFrozen)      continue;
      if(!Strat2IsVisible(si,g_SysState[si].ob2[k])) continue;

      bool touch=false;
      if(g_SysState[si].ob2[k].IsBullish)
         touch=(bid<=g_SysState[si].ob2[k].ZoneTop &&
                bid>=g_SysState[si].ob2[k].ZoneBottom);
      else
         touch=(bid>=g_SysState[si].ob2[k].ZoneBottom &&
                bid<=g_SysState[si].ob2[k].ZoneTop);
      if(touch)
      {
         g_SysState[si].ob2[k].Armed=true;
         g_SysState[si].ob2[k].ArmedTime=now;
         Print("S2 [",sym,"] zona ",(g_SysState[si].ob2[k].IsBullish?"COMPRA":"VENTA"),
               " TOCADA (",DoubleToString(g_SysState[si].ob2[k].ZoneTop,(int)SymbolInfoInteger(sym,SYMBOL_DIGITS)),
               "/",DoubleToString(g_SysState[si].ob2[k].ZoneBottom,(int)SymbolInfoInteger(sym,SYMBOL_DIGITS)),
               ") → buscando CHoCH M3 a favor del rebote");
      }
   }
}

//--- CHoCH de M3 a favor del rebote → 50% de L1-L2 M3 CONGELADO -----
//    OB de VENTA: debe haber CHoCH alcista→bajista (dir<0).
//    OB de COMPRA: debe haber CHoCH bajista→alcista (dir>0).
//    Se elige UNA zona por lado (prioridad: dentro del rango 4H y la
//    más reciente); el resto de zonas del mismo lado quedan de espera.
void Strat2ProcessChoch(int si)
{
   if(!InpUseStrat2) return;
   if(!InpAllowStrat2Orders) return;
   int dir=g_SysState[si].m3ChochDir2;
   if(dir==0) return;
   g_SysState[si].m3ChochDir2=0;                 // consumir el evento
   if(g_SysState[si].strategies[STRAT_S2].cbPaused) return;
   if(g_SysState[si].strategies[STRAT_S2].virtualActive) return;
   if(HasAnyPositionSymbol(si)) return;
   if(Strat2HasPending(si)) return;
   if(!g_SysState[si].SE_M3.Valid) return;
   if(dir>0 && !g_SysState[si].SE_H4.Valid) return;
   if(dir<0 && !g_SysState[si].SE_H4.Valid) return;

   string sym=g_Symbols[si].name;
   int    dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   double entry=NormalizeDouble(g_SysState[si].SE_M3.EQ,dg);   // 50% L1-L2 M3
   if(entry<=0.0) return;
   datetime now=TimeCurrent();

   int best=-1; bool bestBuy=false;
   for(int pass=0;pass<2 && best<0;pass++)
      for(int k=0;k<g_SysState[si].ob2Count;k++)
      {
         if(!g_SysState[si].ob2[k].Active)        continue;
         if(g_SysState[si].ob2[k].Mitigated)      continue;
         if(!g_SysState[si].ob2[k].Armed)         continue;
         if(g_SysState[si].ob2[k].EntryFrozen)    continue;
         if(pass==0 && !g_SysState[si].ob2[k].InRange) continue;
         if(pass==1 &&  g_SysState[si].ob2[k].InRange) continue;
         if(g_SysState[si].ob2[k].IsBullish && dir<=0) continue;  // compra necesita CHoCH +
         if(!g_SysState[si].ob2[k].IsBullish && dir>=0) continue; // venta necesita CHoCH −
         best=k; bestBuy=g_SysState[si].ob2[k].IsBullish;
         break;
      }

   if(best<0) return;   // no hay zona armada del lado del CHoCH

   //--- congelar SOLO la elegida; las demás del mismo lado quedan libres
   for(int k=0;k<g_SysState[si].ob2Count;k++)
   {
      if(!g_SysState[si].ob2[k].Active || g_SysState[si].ob2[k].Mitigated) continue;
      if(!g_SysState[si].ob2[k].Armed || g_SysState[si].ob2[k].EntryFrozen) continue;
      if(g_SysState[si].ob2[k].IsBullish!=bestBuy) continue;
      g_SysState[si].ob2[k].Armed=false;   // dejan de buscar; la elegida actúa
   }
   g_SysState[si].ob2[best].EntryFrozen=true;
   g_SysState[si].ob2[best].EntryPrice=entry;
   g_SysState[si].ob2[best].EntryTime=now;

   //--- entrada CONGELADA también a nivel de paquete + espera del lado
   //    correcto (COMPRA: el precio debe quedar por ENCIMA para limit;
   //    VENTA: por DEBAJO), igual que la Estrategia 1.
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bestBuy)
   { g_SysState[si].s2EntryBuy =entry;
     g_SysState[si].s2EntrySell=0.0;
     g_SysState[si].s2WaitBuy  =true;
     g_SysState[si].s2WaitSell =false; }
   else
   { g_SysState[si].s2EntrySell=entry;
     g_SysState[si].s2EntryBuy =0.0;
     g_SysState[si].s2WaitSell =true;
     g_SysState[si].s2WaitBuy  =false; }
   if(bid<=0.0){ g_SysState[si].s2WaitBuy=false; g_SysState[si].s2WaitSell=false; }
   Print("S2 [",sym,"] CHoCH M3 ",
         (dir>0?"bajista→alcista (COMPRA)":"alcista→bajista (VENTA)"),
         " a favor del rebote → 50% L1-L2 M3 CONGELADO en ",
         DoubleToString(entry,dg));
}

//--- actualización por tick del motor 4H + resscaneo al cerrar vela -
void Strat2Update(int si)
{
   if(!InpUseStrat2) return;
   string sym=g_Symbols[si].name;

   if(!g_SysState[si].SE_H4.Valid) SE_Init(g_SysState[si].SE_H4,sym,InpStrat2TF);

   //--- vela 4H nueva → rango nuevo → reescanear todas las zonas
   datetime t4=(datetime)SeriesInfoInteger(sym,InpStrat2TF,SERIES_LASTBAR_DATE);
   if(t4!=g_SysState[si].h4LastBar)
   {
      g_SysState[si].h4LastBar=t4;
      int c4=0,t4t=0;
      if(g_SysState[si].SE_H4.Valid) SE_OnClose(g_SysState[si].SE_H4,sym,c4,t4t);
      Strat2ScanOBs(si);
   }

   //--- vela 1H nueva → reescanear (zona 4H sigue igual)
   datetime t1=(datetime)SeriesInfoInteger(sym,InpStrat2OBTF,SERIES_LASTBAR_DATE);
   if(t1!=g_SysState[si].ob1hLastBar)
   {
      g_SysState[si].ob1hLastBar=t1;
      Strat2ScanOBs(si);
   }

   int ct4=0;
   SE_OnTick(g_SysState[si].SE_H4,sym,ct4);

   //--- vigilar mitigación en la vela actual (intrabar)
   Strat2ComputeMitigation(si,false);

   //--- flujo visual: toque del rectángulo → armado (la confirmación
   //    CHoCH M3 y el congelado del 50% se procesan en UpdateAllStrategies,
   //    igual que la Estrategia 1: solo sin CB y con horario permitido)
   Strat2CheckTouches(si);

   Strat2RefreshCounts(si);
}

//--- ¿una zona está hoy visible? (misma regla que el conteo) --------
bool Strat2IsVisible(int si,const Strat2OrderBlock &ob)
{
   if(ob.Mitigated) return false;
   string sym=g_Symbols[si].name;
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(bid<=0.0 || !g_SysState[si].SE_H4.Valid) return false;
   double L1=g_SysState[si].SE_H4.L1, L2=g_SysState[si].SE_H4.L2;
   double pt=SymbolInfoDouble(sym,SYMBOL_POINT), tol=pt*2.0;
   bool inR=(bid>=L2-tol && bid<=L1+tol);
   if(ob.IsBullish)
   {
      if(ob.ZoneTop>=bid) return false;
      if(!ob.InRange) return (bid<L2-tol && ob.ZoneTop<=L2+tol);
      return true;
   }
   if(ob.ZoneBottom<=bid) return false;
   if(!ob.InRange) return (bid>L1+tol && ob.ZoneBottom>=L1-tol);
   return true;
}

//--- rectángulo genérico de la Estrategia 2 (zona ancha u OB) -------
void Strat2ObjRect(string name,double top,double bot,datetime ta,datetime tb,color clr)
{
   if(top<=0.0||bot<=0.0||ta<=0||tb<=0){ ObjectDelete(0,name); return; }
   uchar  alpha=(uchar)(255-(72*255/100));          // transparencia 72%
   color  c=(color)ColorToARGB(clr,alpha);
   double tp=MathMax(top,bot), bp=MathMin(top,bot);
   if(ObjectFind(0,name)<0)
   { ObjectCreate(0,name,OBJ_RECTANGLE,0,ta,tp,tb,bp);
     ObjectSetInteger(0,name,OBJPROP_FILL,true);
     ObjectSetInteger(0,name,OBJPROP_BACK,false);
     ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,name,OBJPROP_HIDDEN,true); }
   ObjectSetInteger(0,name,OBJPROP_TIME,0,ta);
   ObjectSetDouble (0,name,OBJPROP_PRICE,0,tp);
   ObjectSetInteger(0,name,OBJPROP_TIME,1,tb);
   ObjectSetDouble (0,name,OBJPROP_PRICE,1,bp);
   ObjectSetInteger(0,name,OBJPROP_COLOR,c);
   ObjectSetInteger(0,name,OBJPROP_BGCOLOR,c);
}

//--- dibuja zona 4H + 50% + zonas OB históricas de la Estrategia 2 --
void DrawStrat2(int si)
{
   if(!InpUseStrat2 || !g_SysState[si].SE_H4.Valid) { Strat2DeleteObjects(si); return; }

   string sym=g_Symbols[si].name;
   string pfx=SE_PREFIX+"S2_"+sym+"_";
   double L1=g_SysState[si].SE_H4.L1, L2=g_SysState[si].SE_H4.L2;
   double EQ=g_SysState[si].SE_H4.EQ;
   string tfz=EnumToString(InpStrat2TF);
   StringReplace(tfz,"PERIOD_","");
   SE_HLine(pfx+"L1",L1,C'0,190,255',STYLE_SOLID,2,"RANGO "+tfz+" L1");
   SE_HLine(pfx+"L2",L2,C'0,190,255',STYLE_SOLID,2,"RANGO "+tfz+" L2");
   SE_HLine(pfx+"EQ",EQ,clrGold,STYLE_DOT,1,"50% RANGO "+tfz);
   Strat2ObjRect(pfx+"ZB",EQ,L2,TimeCurrent()-PeriodSeconds(PERIOD_CURRENT)*300,
                 TimeCurrent()+PeriodSeconds(PERIOD_CURRENT)*50,C'0,80,40');
   Strat2ObjRect(pfx+"ZS",L1,EQ,TimeCurrent()-PeriodSeconds(PERIOD_CURRENT)*300,
                 TimeCurrent()+PeriodSeconds(PERIOD_CURRENT)*50,C'100,25,25');
   SE_ZoneLabel(pfx+"ZBL",(EQ+L2)*0.5,"RANGO "+tfz+": ZONA COMPRAS",clrLightGreen);
   SE_ZoneLabel(pfx+"ZSL",(L1+EQ)*0.5,"RANGO "+tfz+": ZONA VENTAS",clrLightSalmon);

   //--- borrar o dibujar las zonas OB según el input
   if(!InpStrat2ShowOBs)
   {
      for(int k=0;k<STRAT2_STORED_OBS;k++)
      { ObjectDelete(0,pfx+"OB"+IntegerToString(k));
        ObjectDelete(0,pfx+"OB"+IntegerToString(k)+"_T");
        ObjectDelete(0,pfx+"OBM"+IntegerToString(k));
        ObjectDelete(0,pfx+"OBM"+IntegerToString(k)+"_T");
        ObjectDelete(0,pfx+"ENT"+IntegerToString(k));
        ObjectDelete(0,pfx+"ENT"+IntegerToString(k)+"_T"); }
      return;
   }

   int maxL=MathMax(1,MathMin(STRAT2_MAX_OBS,InpStrat2MaxOBs));
   int maxM=MathMin(maxL,4);      // mitigados: hasta 4 por lado para no saturar
   datetime now=TimeCurrent();

   //--- 1) zonas ya MITIGADAS: rectángulo extendido hasta el momento de
   //       mitigación (gris; ya no cuentan como rebote válido)
   int mb=0,ms=0;
   for(int k=0;k<g_SysState[si].ob2Count;k++)
   {
      Strat2OrderBlock ob=g_SysState[si].ob2[k];
      if(!ob.Active || !ob.Mitigated) continue;
      if(ob.IsBullish){ if(mb>=maxM) continue; mb++; }
      else            { if(ms>=maxM) continue; ms++; }

      string nm=pfx+"OBM"+IntegerToString(k);
      color gcc=C'105,105,125';
      Strat2ObjRect(nm,ob.ZoneTop,ob.ZoneBottom,
                    ob.GroupStart,ob.MitigateTime,gcc);
      SE_ZoneLabel(nm+"_T",(ob.ZoneTop+ob.ZoneBottom)*0.5,
                   ob.IsBullish?"MITIGADO COMPRA":"MITIGADO VENTA",gcc);
   }

   //--- 2) zonas VIGENTES (no mitigadas): rectángulo extendido hasta AHORA
   int cb=0,cs=0;
   for(int pass=0;pass<2 && (cb<maxL || cs<maxL);pass++)
      for(int k=0;k<g_SysState[si].ob2Count;k++)
      {
         Strat2OrderBlock ob=g_SysState[si].ob2[k];
         if(!ob.Active || ob.Mitigated) continue;
         if(pass==0 && !ob.InRange) continue;
         if(pass==1 && ob.InRange)  continue;
         if(!Strat2IsVisible(si,ob)) continue;
         if(ob.IsBullish){ if(cb>=maxL) continue; cb++; }
         else            { if(cs>=maxL) continue; cs++; }

         string nm=pfx+"OB"+IntegerToString(k);
         color cc=ob.IsBullish?C'0,190,95':C'230,85,55';
         Strat2ObjRect(nm,ob.ZoneTop,ob.ZoneBottom,
                       ob.GroupStart,now,cc);
         //--- etiqueta según el estado del flujo de entrada
         string lbl=ob.IsBullish?"REBOTE COMPRA (OB+FVG)":"REBOTE VENTA (OB+FVG)";
         if(ob.EntryFrozen)
         { lbl=ob.IsBullish?"COMPRA · 50% M3 CONGELADO":"VENTA · 50% M3 CONGELADO";
           cc=ob.IsBullish?C'0,255,140':C'255,120,90'; }
         else if(ob.Armed)
           lbl+=" · TOCADA → CHoCH M3";
         SE_ZoneLabel(nm+"_T",(ob.ZoneTop+ob.ZoneBottom)*0.5,lbl,cc);

         //--- línea de entrada: 50% L1-L2 M3 CONGELADO en el CHoCH
         if(ob.EntryFrozen && ob.EntryPrice>0.0)
            SE_HLine(pfx+"ENT"+IntegerToString(k),ob.EntryPrice,
                     ob.IsBullish?C'0,255,140':C'255,120,90',
                     STYLE_DASH,2,ob.IsBullish?"ENTRADA S2 COMPRA (50% M3)":"ENTRADA S2 VENTA (50% M3)");
         else { ObjectDelete(0,pfx+"ENT"+IntegerToString(k));
                ObjectDelete(0,pfx+"ENT"+IntegerToString(k)+"_T"); }
      }
}

//--- Visuales de la ESTRATEGIA ÚNICA: estructura H1 + entrada M3 -----
void DrawConfluencia(int si)
{
   //--- estructura madre (H1): rango + 50% + reacción L3/L4
   SE_HLine(SE_PREFIX+"H1L1",g_SysState[si].SE_H1.L1,clrOrange,STYLE_SOLID,2,"H1 L1");
   SE_HLine(SE_PREFIX+"H1L2",g_SysState[si].SE_H1.L2,clrOrange,STYLE_SOLID,2,"H1 L2");
   SE_HLine(SE_PREFIX+"H1EQ",g_SysState[si].SE_H1.EQ,clrGold,STYLE_DOT,1,"50% H1");
   SE_HLine(SE_PREFIX+"H1L3",(g_SysState[si].SE_H1.Valid&&g_SysState[si].SE_H1.L3L4_Active)?
            g_SysState[si].SE_H1.L3:0,clrMagenta,STYLE_DASH,2,"H1 L3");
   SE_HLine(SE_PREFIX+"H1L4",(g_SysState[si].SE_H1.Valid&&g_SysState[si].SE_H1.L3L4_Active)?
            g_SysState[si].SE_H1.L4:0,clrRed,STYLE_DASH,2,"H1 L4");

   //--- zona de COMPRA (abajo: 50% → L2) y zona de VENTA (arriba: L1 → 50%)
   SE_Rect(SE_PREFIX+"H1ZB",g_SysState[si].SE_H1.EQ,g_SysState[si].SE_H1.L2,C'0,80,40');
   SE_Rect(SE_PREFIX+"H1ZS",g_SysState[si].SE_H1.L1,g_SysState[si].SE_H1.EQ,C'100,20,20');

   double midB=(g_SysState[si].SE_H1.EQ+g_SysState[si].SE_H1.L2)*0.5;
   double midS=(g_SysState[si].SE_H1.L1+g_SysState[si].SE_H1.EQ)*0.5;
   SE_ZoneLabel(SE_PREFIX+"H1ZBL",midB,
                g_SysState[si].confArmedBuy?"ZONA COMPRA H1  [BUSCANDO COMPRA]":"ZONA COMPRA H1",
                g_SysState[si].confArmedBuy?clrLime:clrLightGreen);
   SE_ZoneLabel(SE_PREFIX+"H1ZSL",midS,
                g_SysState[si].confArmedSell?"ZONA VENTA H1  [BUSCANDO VENTA]":"ZONA VENTA H1",
                g_SysState[si].confArmedSell?clrTomato:clrLightSalmon);

   //--- nivel de entrada CONGELADO (50% del rango M3)
   SE_HLine(SE_PREFIX+"CFB",g_SysState[si].confEntryBuy,clrLime,STYLE_DASH,2,
            "ENTRADA COMPRA (50% M3)");
   SE_HLine(SE_PREFIX+"CFS",g_SysState[si].confEntrySell,clrRed,STYLE_DASH,2,
            "ENTRADA VENTA (50% M3)");
}

void DrawStructureLines(int si)
{
   if(!InpShowStructureLines){ RemoveStructureLines(); return; }

   //--- TF del gráfico: SOLO las 4 líneas L1, L2, L3, L4 --------------
   SE_HLine(SE_PREFIX+"TFL1",g_SysState[si].SE.Valid?g_SysState[si].SE.L1:0,clrDodgerBlue,STYLE_SOLID,2,"L1");
   SE_HLine(SE_PREFIX+"TFL2",g_SysState[si].SE.Valid?g_SysState[si].SE.L2:0,clrDodgerBlue,STYLE_SOLID,2,"L2");
   //--- L3/L4 (zona de reacción activa): magenta/rojo discontinuas
   SE_HLine(SE_PREFIX+"TFL3",(g_SysState[si].SE.Valid&&g_SysState[si].SE.L3L4_Active)?g_SysState[si].SE.L3:0,clrMagenta,STYLE_DASH,2,"L3");
   SE_HLine(SE_PREFIX+"TFL4",(g_SysState[si].SE.Valid&&g_SysState[si].SE.L3L4_Active)?g_SysState[si].SE.L4:0,clrRed,STYLE_DASH,2,"L4");

   //--- ESTRATEGIA ÚNICA: estructura de líneas H1 + confluencia M3 -----------
   if(InpUseConfluencia && InpShowConfluencias && g_SysState[si].SE_H1.Valid)
      DrawConfluencia(si);
   else
   {
      string Cf[]={"H1L1","H1L2","H1L3","H1L4","H1EQ","H1ZB","H1ZS","H1ZBL","H1ZSL","CFB","CFS"};
      for(int c=0;c<ArraySize(Cf);c++)
      { ObjectDelete(0,SE_PREFIX+Cf[c]); ObjectDelete(0,SE_PREFIX+Cf[c]+"_T"); }
   }

   //--- ESTRATEGIA 2: zona 4H (L1-L2 + 50%) + order blocks 1H ----------------
   if(InpUseStrat2 && InpStrat2ShowZone) DrawStrat2(si);
   else                                  Strat2DeleteObjects(si);

   ChartRedraw();
}

void RemoveStructureLines()
{
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   { string n=ObjectName(0,i,0,-1);
     if(StringFind(n,SE_PREFIX)==0) ObjectDelete(0,n); }
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Dibuja (o borra) las líneas del símbolo del gráfico actual       |
//+------------------------------------------------------------------+
void DrawChartStructure()
{
   int cs=-1;
   for(int s2=0;s2<g_SymCount;s2++)
      if(g_Symbols[s2].name==_Symbol){cs=s2;break;}
   if(cs>=0&&g_SysState[cs].SE.Valid) DrawStructureLines(cs);
   else                               RemoveStructureLines();
}

//+------------------------------------------------------------------+
//| UPDATE ESTRATEGIAS                                               |
//|                                                                  |
//| Estrategia única (estructura H1 + confluencia M3): toda la        |
//| entrada/gestión de órdenes vive en UpdateConfluencia() — la fase  |
//| virtual (simulación de límites) y la fase LIVE (órdenes reales).  |
//+------------------------------------------------------------------+
void UpdateAllStrategies()
{
   if(g_CircuitBreakerOn) return;
   if(IsWeeklyCloseWindow()) return;   // sin nuevas entradas desde el cierre de viernes hasta el lunes
   for(int si=0;si<g_SymCount;si++)
   { if(!g_SysState[si].strategies[STRAT_CONFLUENCIA].enabled) continue;
     if(g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused) continue;
     UpdateConfluencia(si); }
   for(int si=0;si<g_SymCount;si++)
   { if(!g_SysState[si].strategies[STRAT_S2].enabled) continue;
     if(g_SysState[si].strategies[STRAT_S2].cbPaused) continue;
     UpdateStrat2Orders(si); }
}

//+------------------------------------------------------------------+
//| TRAILING                                                         |
//+------------------------------------------------------------------+
bool ModifySL(ulong ticket, double newSL)
{
   if(!PositionSelectByTicket(ticket)) return false;
   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action=TRADE_ACTION_SLTP; req.position=ticket;
   req.symbol=PositionGetString(POSITION_SYMBOL);
   req.sl=newSL; req.tp=PositionGetDouble(POSITION_TP);
   if(!OrderSend(req,res)||res.retcode!=TRADE_RETCODE_DONE)
   { Print("ERROR ModifySL #",ticket); return false; }
   return true;
}

void ManageOpenPositions()
{
   bool changed=false;
   for(int k=0;k<g_TradeCount;k++)
   { if(g_Trades[k].isPending||g_Trades[k].slMoved) continue;
     int si=g_Trades[k].symbolIdx; int st=g_Trades[k].strategyId;
     if(si<0||st<0) continue;
     if(!g_Trades[k].advActive) continue;   // 1:2 fijado al abrir (nivel>=5)
     ulong t=g_Trades[k].ticket;
     if(!PositionSelectByTicket(t)) continue;
     string sym=g_Symbols[si].name;
     double pt =SymbolInfoDouble(sym,SYMBOL_POINT);
     int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
     double op =g_Trades[k].openPrice;
     double cSL=PositionGetDouble(POSITION_SL);
     int    ptype=g_Trades[k].orderType;
     double bid=SymbolInfoDouble(sym,SYMBOL_BID);
     double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
     double mid=(bid+ask)/2.0;
     double delta=(ptype==POSITION_TYPE_BUY)?(mid-op)/pt:(op-mid)/pt;
     double actPts=SymActivation(si);
     if(delta>=actPts)
     { double psl=SymProtectedSL(si);
       double nSL=(ptype==POSITION_TYPE_BUY)?NormalizeDouble(op+psl*pt,dg):NormalizeDouble(op-psl*pt,dg);
       bool ok=(ptype==POSITION_TYPE_BUY)?(cSL<nSL||cSL==0):(cSL>nSL||cSL==0);
       if(ok&&ModifySL(t,nSL))
       { g_Trades[k].slMoved=true; g_Trades[k].sl=nSL;
         for(int q=0;q<g_ClosedCount;q++)
            if(g_ClosedQueue[q].ticket==t)
            { g_ClosedQueue[q].slMoved=true; g_ClosedQueue[q].sl=nSL; break; }
         changed=true;
         Print("Trailing [",sym,"/",g_SysState[si].strategies[st].name,
               "] CV=",g_SysState[si].strategies[st].CV," newSL=",nSL); } } }
   if(changed&&!IsTester()) RebuildActiveTab();
}

//+------------------------------------------------------------------+
//| TRADING                                                          |
//+------------------------------------------------------------------+
bool _SendSingle(string sym, ENUM_ORDER_TYPE ot, double lots,
                 double sl, double tp, long magic, int si, int st)
{
   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action=TRADE_ACTION_DEAL; req.symbol=sym;
   req.volume=lots; req.type=ot;
   req.price=(ot==ORDER_TYPE_BUY)?SymbolInfoDouble(sym,SYMBOL_ASK):SymbolInfoDouble(sym,SYMBOL_BID);
   req.sl=sl; req.tp=tp; req.deviation=20; req.magic=magic;
   req.type_filling=ORDER_FILLING_IOC;
   string sn=(si>=0&&st>=0)?g_SysState[si].strategies[st].name:"MAN";
   int    nl=(si>=0)?PairLevel(si):1;
   req.comment=StringFormat("%s_%s_%s_N%d",InpComment,sym,sn,nl);
   if(!OrderSend(req,res)||res.retcode!=TRADE_RETCODE_DONE)
   { Print("ERROR Send [",sym,"]: ",res.retcode); return false; }
   return true;
}

bool SendMarketOrderEx(int si, int st, ENUM_ORDER_TYPE ot, double totalLots, long magic)
{
   string sym=g_Symbols[si].name;
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double mid=(ask+bid)/2.0;
   int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   int    posType=(ot==ORDER_TYPE_BUY)?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   double sl=CalcSL(sym,si,mid,posType);
   double tp=CalcTP(sym,si,mid,posType);
   int parts=CalcSplitCount(totalLots); ulong gid=(ulong)TimeCurrent(); bool ok=true;
   for(int i=0;i<parts;i++)
   { double pl=CalcSplitLot(sym,totalLots,i,parts); if(pl<=0) continue;
     if(i>0&&!IsTester()) Sleep(InpSplitDelayMs);
     if(!_SendSingle(sym,ot,pl,sl,tp,magic,si,st)) ok=false; }
   return ok;
}

void ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;
   string sym=PositionGetString(POSITION_SYMBOL);
   long   magic=(long)PositionGetInteger(POSITION_MAGIC);
   long   ptype=PositionGetInteger(POSITION_TYPE);
   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action=TRADE_ACTION_DEAL; req.position=ticket;
   req.symbol=sym; req.volume=PositionGetDouble(POSITION_VOLUME);
   req.deviation=20; req.magic=magic; req.comment="CLOSE_ONE";
   req.type_filling=ORDER_FILLING_IOC;
   if(ptype==POSITION_TYPE_BUY)
   { req.type=ORDER_TYPE_SELL; req.price=SymbolInfoDouble(sym,SYMBOL_BID); }
   else
   { req.type=ORDER_TYPE_BUY;  req.price=SymbolInfoDouble(sym,SYMBOL_ASK); }
   if(!OrderSend(req,res) || res.retcode!=TRADE_RETCODE_DONE)
      Print("ClosePosition [",sym,"] #",ticket," error: ",res.retcode);
}

void CloseAllSymbolsPositions()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   { ulong t=PositionGetTicket(i); if(t==0) continue;
     if(!IsAnyMagic((long)PositionGetInteger(POSITION_MAGIC))) continue;
     ClosePosition(t); }
}

void _SendLimitManual(int si, ENUM_ORDER_TYPE ot, double lots, double lp)
{
   if(si<0||si>=g_SymCount) return;
   string sym=g_Symbols[si].name;
   int    dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(lp<=0) lp=NormalizeDouble((ask+bid)/2.0,dg);
   lp=NormalizeDouble(lp,dg);
   int posType=(ot==ORDER_TYPE_BUY_LIMIT||ot==ORDER_TYPE_BUY_STOP)?
               POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   double sl=CalcSL(sym,si,lp,posType);
   double tp=CalcTP(sym,si,lp,posType);
   MqlTradeRequest req={}; MqlTradeResult res={};
   req.action=TRADE_ACTION_PENDING; req.symbol=sym;
   req.volume=lots; req.type=ot; req.price=lp;
   req.sl=sl; req.tp=tp; req.magic=MagicManual(si);
   req.comment=StringFormat("%s_%s_MAN_LMT",InpComment,sym);
   if(!OrderSend(req,res)||res.retcode!=TRADE_RETCODE_DONE)
      Print("ERROR LimitManual [",sym,"]: ",res.retcode);
}

//+------------------------------------------------------------------+
//| SYNC TRADES                                                      |
//+------------------------------------------------------------------+
void SyncAllTrades()
{
   ulong  pTkt[]; bool pAdv[],pMov[],pMan[];
   int    pCR[],pCV[],pSid[],pSi[];
   ulong  pGrp[]; int pType[];
   double pOP[],pSL[],pTP[];
   int pN=g_TradeCount;
   ArrayResize(pTkt,pN);  ArrayResize(pAdv,pN);  ArrayResize(pMov,pN);
   ArrayResize(pCR,pN);   ArrayResize(pCV,pN);   ArrayResize(pGrp,pN);
   ArrayResize(pType,pN); ArrayResize(pOP,pN);   ArrayResize(pSL,pN);
   ArrayResize(pTP,pN);   ArrayResize(pMan,pN);  ArrayResize(pSid,pN);
   ArrayResize(pSi,pN);
   for(int i=0;i<pN;i++)
   { pTkt[i]=g_Trades[i].ticket;    pAdv[i]=g_Trades[i].advActive;
     pMov[i]=g_Trades[i].slMoved;   pCR[i]=g_Trades[i].CR_level;
     pCV[i]=g_Trades[i].CV_level;   pGrp[i]=g_Trades[i].splitGroupId;
     pType[i]=g_Trades[i].orderType;pOP[i]=g_Trades[i].openPrice;
     pSL[i]=g_Trades[i].sl;         pTP[i]=g_Trades[i].tp;
     pMan[i]=g_Trades[i].isManual;  pSid[i]=g_Trades[i].strategyId;
     pSi[i]=g_Trades[i].symbolIdx; }
   g_TradeCount=0; ArrayResize(g_Trades,0);
   for(int i=0;i<PositionsTotal();i++)
   { ulong t=PositionGetTicket(i);
     if(t==0||!PositionSelectByTicket(t)) continue;
     string sym=PositionGetString(POSITION_SYMBOL);
     long   magic=(long)PositionGetInteger(POSITION_MAGIC);
     if(!IsAnyMagic(magic)) continue;
     int symIdx=-1;
     for(int s=0;s<g_SymCount;s++) if(g_Symbols[s].name==sym){symIdx=s;break;}
     if(symIdx<0) continue;
     int sid=-1;
     for(int s=0;s<STRAT_COUNT;s++)
        if(magic==GetStrategyMagic(symIdx,s)){sid=s;break;}
     bool isMan=(magic==MagicManual(symIdx));
     int idx=g_TradeCount; ArrayResize(g_Trades,idx+1);
     g_Trades[idx].ticket    =t;
     g_Trades[idx].isPending =false;
     g_Trades[idx].isManual  =isMan;
     g_Trades[idx].strategyId=sid;
     g_Trades[idx].symbolIdx =symIdx;
     g_Trades[idx].orderType =(int)PositionGetInteger(POSITION_TYPE);
     g_Trades[idx].lots      =PositionGetDouble(POSITION_VOLUME);
     g_Trades[idx].openPrice =PositionGetDouble(POSITION_PRICE_OPEN);
     g_Trades[idx].profit    =PositionGetDouble(POSITION_PROFIT);
     g_Trades[idx].splitGroupId=0;
     double srvSL=PositionGetDouble(POSITION_SL);
     double srvTP=PositionGetDouble(POSITION_TP);
     bool found=false;
     for(int s=0;s<pN;s++)
     { if(pTkt[s]!=t) continue;
       g_Trades[idx].advActive    =pAdv[s];
       g_Trades[idx].slMoved      =pMov[s];
       g_Trades[idx].CR_level     =pCR[s];
       g_Trades[idx].CV_level     =pCV[s];
       g_Trades[idx].splitGroupId =pGrp[s];
       g_Trades[idx].sl=(pMov[s]&&pSL[s]>0)?pSL[s]:((srvSL>0)?srvSL:pSL[s]);
       g_Trades[idx].tp=(srvTP>0)?srvTP:pTP[s];
       found=true; break; }
     if(!found)
     { int cvN=(sid>=0)?g_SysState[symIdx].strategies[sid].CV:1;
       g_Trades[idx].CR_level =PairLevel(symIdx);   // nivel del par al abrir
       g_Trades[idx].CV_level =cvN;
       g_Trades[idx].advActive=(g_AdvancedMode||
                                ((sid>=0)?IsTrailingActive(symIdx,sid):
                                          (InpAutoFromLevel5&&PairLevel(symIdx)>=5)));
       g_Trades[idx].slMoved  =false; g_Trades[idx].splitGroupId=0;
       g_Trades[idx].sl=srvSL; g_Trades[idx].tp=srvTP; }
     g_TradeCount++; }
   for(int s=0;s<pN;s++)
   { int pt=pType[s];
     if(pt==ORDER_TYPE_BUY_LIMIT||pt==ORDER_TYPE_SELL_LIMIT||
        pt==ORDER_TYPE_BUY_STOP||pt==ORDER_TYPE_SELL_STOP) continue;
     bool still=false;
     for(int k=0;k<g_TradeCount;k++) if(g_Trades[k].ticket==pTkt[s]){still=true;break;}
     if(!still)
     { bool q=false;
       for(int qq=0;qq<g_ClosedCount;qq++) if(g_ClosedQueue[qq].ticket==pTkt[s]){q=true;break;}
       if(!q)
       { int qi=g_ClosedCount; ArrayResize(g_ClosedQueue,qi+1);
         g_ClosedQueue[qi].ticket    =pTkt[s];
         g_ClosedQueue[qi].openPrice =pOP[s];
         g_ClosedQueue[qi].sl        =pSL[s];
         g_ClosedQueue[qi].tp        =pTP[s];
         g_ClosedQueue[qi].CR_level  =pCR[s];
         g_ClosedQueue[qi].CV_level  =pCV[s];
         g_ClosedQueue[qi].slMoved   =pMov[s];
         g_ClosedQueue[qi].orderType =pt;
         g_ClosedQueue[qi].dealReason=-1;
         g_ClosedQueue[qi].isManual  =pMan[s];
         g_ClosedQueue[qi].strategyId=pSid[s];
         g_ClosedQueue[qi].symbolIdx =pSi[s];
         g_ClosedCount++;
         string sn=(pSid[s]>=0)?g_SysState[pSi[s]].strategies[pSid[s]].name:"MAN";
         Print("Cierre detectado #",pTkt[s]," [",
               (pSi[s]>=0?g_Symbols[pSi[s]].name:"?"),"/",sn,"]"); } } }
   if(g_ScrollOffset>=g_TradeCount&&g_ScrollOffset>0)
      g_ScrollOffset=MathMax(0,g_TradeCount-1);
}

//+------------------------------------------------------------------+
//| PROCESAR CIERRES                                                 |
//+------------------------------------------------------------------+
void ProcessClosedQueue()
{
   if(g_ClosedCount==0) return;
   HistorySelect(TimeCurrent()-432000,TimeCurrent()+60);   // 5 días: cubre cierres del viernes procesados el lunes
   ClosedSnap pending[]; int pc=0; bool anyP=false;
   // Un cierre lógico por estrategia/par aunque la orden haya sido dividida
   // en varios tickets (split de lotaje).
   bool counted[MAX_SYMBOLS][STRAT_COUNT];
   ArrayInitialize(counted,false);
   for(int q=0;q<g_ClosedCount;q++)
   { ClosedSnap snap=g_ClosedQueue[q]; if(snap.ticket==0) continue;
     double cPL=0,cPr=0; long dR=-1; bool found=false;
     long   dTime=0;
     for(int d=HistoryDealsTotal()-1;d>=0;d--)
     { ulong dt=HistoryDealGetTicket(d); if(dt==0) continue;
       if(!IsAnyMagic((long)HistoryDealGetInteger(dt,DEAL_MAGIC))) continue;
       if((long)HistoryDealGetInteger(dt,DEAL_ENTRY)!=DEAL_ENTRY_OUT) continue;
       if((long)HistoryDealGetInteger(dt,DEAL_POSITION_ID)!=(long)snap.ticket) continue;
       cPL=HistoryDealGetDouble(dt,DEAL_PROFIT);
       cPr=HistoryDealGetDouble(dt,DEAL_PRICE);
       dR=(long)HistoryDealGetInteger(dt,DEAL_REASON);
       dTime=(long)HistoryDealGetInteger(dt,DEAL_TIME);
       found=true; break; }
     if(!found){ArrayResize(pending,pc+1);pending[pc]=snap;pc++;continue;}
     int si=snap.symbolIdx; int st=snap.strategyId;
     double tol=(si>=0)?SymbolInfoDouble(g_Symbols[si].name,SYMBOL_POINT)*5:0.00001;
     // Si el SL fue movido a protección, esa marca tiene prioridad sobre
     // la razón/precio reportados por el broker: es una ganancia protegida.
     bool hTP=false;
     bool hSL=false;
     if(snap.slMoved)
     { hSL=true; hTP=false; }
     else if(dR==DEAL_REASON_SL)
     { hSL=true; hTP=false; } // todo SL real sube el nivel
     else if(dR==DEAL_REASON_TP)
     { hTP=true; hSL=false; }
     else
     { hTP=(snap.tp>0&&MathAbs(cPr-snap.tp)<=tol);
       hSL=(snap.sl>0&&MathAbs(cPr-snap.sl)<=tol);
       if(!hTP&&!hSL){hTP=(cPL>0);hSL=(cPL<=0);} }
     string sn=(si>=0&&st>=0)?g_SysState[si].strategies[st].name:"MAN";
     string sym=(si>=0)?g_Symbols[si].name:"?";
     bool wc=(dTime>0)&&IsWeeklyCloseWindow((datetime)dTime);   // cierre dentro de la ventana semanal
     Print("Cierre [",sym,"/",sn,"] #",snap.ticket," PL=",cPL," TP=",hTP," SL=",hSL,
           wc?" [SEMANAL]":"");
     if(!snap.isManual&&si>=0&&si<MAX_SYMBOLS&&st>=0&&st<STRAT_COUNT&&
        !counted[si][st])
     {
        counted[si][st]=true;
        if(wc&&cPL<0)
        { Print("CIERRE SEMANAL en PÉRDIDA [",sym,"/",sn,"] #",snap.ticket,
                " PL=",DoubleToString(cPL,2)," → cuenta como SL (nivel +1)");
          OnLiveSL_Original(si,st); }
        else if(wc)
        { Print("CIERRE SEMANAL en GANANCIA [",sym,"/",sn,"] #",snap.ticket,
                " PL=",DoubleToString(cPL,2)," → NIVEL intacto, próxima operación con el mismo nivel");
          if(st==STRAT_CONFLUENCIA) ConfluenciaOnTradeClosed(si);
          if(st==STRAT_S2) Strat2OnTradeClosed(si); }
        else
        { // Un SL que dejó beneficio es necesariamente el trailing/protegido,
          // aunque el broker no cierre exactamente en el precio guardado.
          bool trailingClose=(snap.slMoved || (hSL && cPL>0.0));
          if(hTP && !trailingClose) OnStrategyLiveTP(si,st);
          else                     OnStrategyLiveSL(si,st,trailingClose,snap.CR_level); }
     }
     anyP=true; }
   ArrayResize(g_ClosedQueue,pc);
   for(int i=0;i<pc;i++) g_ClosedQueue[i]=pending[i];
   g_ClosedCount=pc;
   if(anyP){SaveState(); if(!IsTester()) RebuildPanel();}
}//+------------------------------------------------------------------+
//| HELPERS GRÁFICOS                                                 |
//+------------------------------------------------------------------+
void ObjRect(string n,int x,int y,int w,int h,color bg,color brd,int bw=1)
{
   ObjectDelete(0,n);
   ObjectCreate(0,n,OBJ_RECTANGLE_LABEL,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,brd);
   ObjectSetInteger(0,n,OBJPROP_BORDER_TYPE,BORDER_FLAT);
   ObjectSetInteger(0,n,OBJPROP_WIDTH,bw);
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_ZORDER,0);
}

void ObjLbl(string n,int x,int y,string txt,color clr,int fs=9,
            string font="Arial Bold",ENUM_ANCHOR_POINT anc=ANCHOR_LEFT_UPPER)
{
   ObjectDelete(0,n);
   ObjectCreate(0,n,OBJ_LABEL,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetString(0,n,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,n,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,fs);
   ObjectSetString(0,n,OBJPROP_FONT,font);
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_ANCHOR,anc);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_ZORDER,10);
}

void ObjBtn(string n,int x,int y,int w,int h,string txt,
            color bg,color fg,int fs=9,string font="Arial Bold")
{
   ObjectDelete(0,n);
   ObjectCreate(0,n,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetString(0,n,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,n,OBJPROP_COLOR,fg);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,fs);
   ObjectSetString(0,n,OBJPROP_FONT,font);
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_ZORDER,20);
   ObjectSetInteger(0,n,OBJPROP_STATE,false);
}

void ObjEdit(string n,int x,int y,int w,int h,string txt,color bg,color fg,int fs=10)
{
   ObjectDelete(0,n);
   ObjectCreate(0,n,OBJ_EDIT,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetString(0,n,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,n,OBJPROP_COLOR,fg);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,fs);
   ObjectSetString(0,n,OBJPROP_FONT,"Arial Bold");
   ObjectSetInteger(0,n,OBJPROP_ALIGN,ALIGN_CENTER);
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_ZORDER,30);
   ObjectSetInteger(0,n,OBJPROP_READONLY,false);
}

void ObjSep(string n,int x,int y,int w)
{ ObjRect(n,x,y,w,1,C'60,60,90',C'60,60,90',0); }

string GetTypeName(int otype,bool isPending)
{
   if(!isPending) return(otype==POSITION_TYPE_BUY)?"BUY":"SELL";
   switch(otype)
   { case ORDER_TYPE_BUY_LIMIT:  return "BUY LMT";
     case ORDER_TYPE_SELL_LIMIT: return "SELL LMT";
     case ORDER_TYPE_BUY_STOP:   return "BUY STP";
     case ORDER_TYPE_SELL_STOP:  return "SELL STP";
     default:                    return "PENDING"; }
}

color GetTypeColor(int otype,bool isPending)
{
   if(!isPending) return(otype==POSITION_TYPE_BUY)?clrLimeGreen:clrTomato;
   return(otype==ORDER_TYPE_BUY_LIMIT||otype==ORDER_TYPE_BUY_STOP)?
          C'100,220,100':C'220,100,100';
}

//+------------------------------------------------------------------+
//| PANEL — DRAG ZONE                                                |
//+------------------------------------------------------------------+
void BuildDragZone()
{
   ObjectDelete(0,DRAG_ZONE);
   ObjectCreate(0,DRAG_ZONE,OBJ_RECTANGLE_LABEL,0,0,0);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_XDISTANCE,PNL_X);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_YDISTANCE,PNL_Y);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_XSIZE,PNL_W);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_YSIZE,TITLE_H);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_BGCOLOR,C'8,8,42');
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_BORDER_COLOR,C'70,70,200');
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_BORDER_TYPE,BORDER_FLAT);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_WIDTH,1);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_BACK,false);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,DRAG_ZONE,OBJPROP_ZORDER,5);
}

//+------------------------------------------------------------------+
//| PANEL — ESTRUCTURA ESTÁTICA                                      |
//+------------------------------------------------------------------+
void BuildStaticStructure()
{
   int x=PNL_X,y=PNL_Y,W=PNL_W;

   ObjRect(PFX+"BG",x,y,W,PNL_H,C'15,15,25',C'60,60,150',2);

   BuildDragZone();
   ObjLbl(OBJ_TITLE,x+W/2,y+10,
          "▲▼  GESTIÓN CUANTITATIVA  v8.50  ▲▼",
          clrGold,10,"Arial Bold",ANCHOR_CENTER);
   ObjLbl(PFX+"DRAG_HINT",x+W-4,y+24,"☰ drag",
          C'80,80,120',6,"Arial",ANCHOR_RIGHT_UPPER);

   // ── InfoBar ──────────────────────────────────────────────────
   int ibY=y+TITLE_H;
   ObjRect(PFX+"IB_BG",x,ibY,W,INFOBAR_H,C'12,18,12',C'35,75,35',1);

   int cw=W/5;

   ObjRect(PFX+"IB_C0",x+2,ibY+2,cw-2,INFOBAR_H-4,C'16,24,16',C'40,80,40',1);
   ObjLbl(PFX+"IB_H0",x+2+cw/2,ibY+5,"P&L FLOTANTE",C'150,150,150',6,"Arial",ANCHOR_CENTER);
   ObjLbl(OBJ_IB_PL,  x+2+cw/2,ibY+18,"---",clrWhite,10,"Arial Bold",ANCHOR_CENTER);

   int c2x=x+cw+2;
   ObjRect(PFX+"IB_C1",c2x,ibY+2,cw-2,INFOBAR_H-4,C'16,24,16',C'40,80,40',1);
   ObjLbl(PFX+"IB_H1",c2x+cw/2,ibY+5,"EQUIDAD",C'150,150,150',6,"Arial",ANCHOR_CENTER);
   ObjLbl(OBJ_IB_EQ,  c2x+cw/2,ibY+18,"---",clrWhite,10,"Arial Bold",ANCHOR_CENTER);

   int c3x=x+2*cw+2;
   ObjRect(PFX+"IB_C2",c3x,ibY+2,cw-2,INFOBAR_H-4,C'16,24,16',C'40,80,40',1);
   ObjLbl(PFX+"IB_H2",c3x+cw/2,ibY+5,"CV LIVE",C'150,150,150',6,"Arial",ANCHOR_CENTER);
   ObjLbl(OBJ_IB_CV,  c3x+cw/2,ibY+18,"---",clrWhite,10,"Arial Bold",ANCHOR_CENTER);

   int c4x=x+3*cw+2;
   ObjRect(PFX+"IB_C3",c4x,ibY+2,cw-2,INFOBAR_H-4,C'16,24,16',C'40,80,40',1);
   ObjLbl(PFX+"IB_H3",c4x+cw/2,ibY+5,"CV MAX",C'150,150,150',6,"Arial",ANCHOR_CENTER);
   ObjLbl(OBJ_IB_CVMAX,c4x+cw/2,ibY+18,"---",clrGold,10,"Arial Bold",ANCHOR_CENTER);

   int c5x=x+4*cw+2;
   int c5w=W-4*cw-4;
   ObjRect(PFX+"IB_C4",c5x,ibY+2,c5w,INFOBAR_H-4,C'16,16,28',C'50,50,90',1);
   ObjLbl(PFX+"IB_H4",c5x+c5w/2,ibY+5,"PÉRD.DÍA",C'150,150,150',6,"Arial",ANCHOR_CENTER);
   ObjLbl(OBJ_IB_CB,  c5x+c5w/2,ibY+18,"---",C'120,120,180',9,"Arial Bold",ANCHOR_CENTER);
   ObjRect(PFX+"IB_CBBG",c5x+2,ibY+38,c5w-4,8,C'25,25,35',C'50,50,70',1);
   ObjRect(PFX+"IB_CBFG",c5x+2,ibY+38,2,     8,clrGray,clrGray,0);

   // ── Barra navegación símbolos ─────────────────────────────────
   int sbY=ibY+INFOBAR_H;
   ObjRect(PFX+"SB_BG",x,sbY,W,SYMBAR_H,C'10,10,22',C'40,40,120',1);
   ObjBtn(PFX+"SB_PREV",x+2,      sbY+3,28,24,"◄",C'25,25,55',clrWhite,11,"Arial Bold");
   ObjBtn(PFX+"SB_NEXT",x+W-30,   sbY+3,28,24,"►",C'25,25,55',clrWhite,11,"Arial Bold");
   ObjRect(PFX+"SB_NMBG",x+32,sbY+3,W-64,24,C'18,18,40',C'55,55,130',1);
   ObjLbl(PFX+"SB_NAME",x+W/2,sbY+8,"---",clrGold,10,"Arial Bold",ANCHOR_CENTER);
   ObjLbl(PFX+"SB_IDX", x+W-32,sbY+8,"---",C'100,100,150',7,"Arial",ANCHOR_RIGHT_UPPER);

   // ── Tabs ──────────────────────────────────────────────────────
   int tabY=sbY+SYMBAR_H;
   int tabW=W/N_TABS;
   for(int t=0;t<N_TABS;t++)
   {
      bool active=(t==ActiveTab);
      ObjBtn(PFX+"TAB"+IntegerToString(t),
             x+t*tabW,tabY,tabW,TAB_H,TAB_NAMES[t],
             active?C'35,35,75':C'18,18,35',
             active?clrGold:C'140,140,160',7,"Arial Bold");
      if(active)
         ObjRect(PFX+"TABU"+IntegerToString(t),
                 x+t*tabW+2,tabY+TAB_H-3,tabW-4,3,clrGold,clrGold,0);
   }

   ObjRect(PFX+"CONTENT_BG",x,tabY+TAB_H,W,CONTENT_H,C'18,18,28',C'50,50,100',1);
}

//+------------------------------------------------------------------+
//| INFOBAR                                                          |
//+------------------------------------------------------------------+
void UpdateInfoBar()
{
   int si=g_PanelSymIdx;
   int    dispCV=1, dispCVMax=0;
   double dispLot=0.01;

   if(si>=0&&si<g_SymCount)
   {
      int alive=g_SysState[si].activeLiveStrategy;
      if(alive>=0)
      { dispCV  = g_SysState[si].strategies[alive].CV; }
      dispLot = GetPairLot(si);   // lote por nivel del par (Asistente 3)
      for(int s=0;s<STRAT_COUNT;s++)
         if(g_SysState[si].strategies[s].CV_Max>dispCVMax)
            dispCVMax=g_SysState[si].strategies[s].CV_Max;
   }

   double eq  = AccountInfoDouble(ACCOUNT_EQUITY);
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   double fPL = eq-bal;

   ObjectSetString(0,OBJ_IB_PL,OBJPROP_TEXT,
                   StringFormat("%s%.2f",(fPL>=0)?"+":"",fPL));
   ObjectSetInteger(0,OBJ_IB_PL,OBJPROP_COLOR,(fPL>=0)?clrLimeGreen:clrTomato);

   ObjectSetString(0,OBJ_IB_EQ,OBJPROP_TEXT,StringFormat("%.2f",eq));
   ObjectSetInteger(0,OBJ_IB_EQ,OBJPROP_COLOR,(eq>=bal)?clrLimeGreen:clrTomato);

   ObjectSetString(0,OBJ_IB_CV,   OBJPROP_TEXT,StringFormat("%d",dispCV));
   ObjectSetString(0,OBJ_IB_CVMAX,OBJPROP_TEXT,StringFormat("%d",dispCVMax));

   double lossPct = GetDailyLossPct();
   double limPct  = InpMaxDailyLossPct;
   string cbTxt;
   color  cbClr;
   if(g_CircuitBreakerOn)
   { cbTxt="⛔ BLOQUEADO"; cbClr=clrTomato; }
   else
   { cbTxt=StringFormat("%.2f%% / %.1f%%",lossPct,limPct);
     cbClr=(lossPct>=limPct*0.8)?clrOrange:
           (lossPct>=limPct*0.5)?clrYellow:C'120,180,120'; }
   ObjectSetString(0,OBJ_IB_CB, OBJPROP_TEXT,cbTxt);
   ObjectSetInteger(0,OBJ_IB_CB,OBJPROP_COLOR,cbClr);

   // Mini barra CB
   int W=PNL_W;
   int cw=W/5;
   int c5x=PNL_X+4*cw+2;
   int c5w=W-4*cw-4;
   int ibY=PNL_Y+TITLE_H;
   int barW=MathMax(2,(int)MathMin((double)(c5w-4)*lossPct/MathMax(limPct,0.001),
                                    (double)(c5w-4)));
   color barC=g_CircuitBreakerOn?clrTomato:
              (lossPct>=limPct*0.8)?clrTomato:
              (lossPct>=limPct*0.5)?clrOrange:clrDodgerBlue;
   ObjRect(PFX+"IB_CBFG",c5x+2,ibY+38,barW,8,barC,barC,0);

   // Barra de símbolos
   if(si>=0&&si<g_SymCount)
   {
      bool hasLive=g_SysState[si].hasLive;
      ObjectSetString(0,PFX+"SB_NAME",OBJPROP_TEXT,g_Symbols[si].name);
      ObjectSetString(0,PFX+"SB_IDX", OBJPROP_TEXT,
                      StringFormat("%d/%d",si+1,g_SymCount));
      ObjectSetInteger(0,PFX+"SB_NAME",OBJPROP_COLOR,
                       hasLive?clrLimeGreen:clrGold);
   }
   else
   {
      ObjectSetString(0,PFX+"SB_NAME",OBJPROP_TEXT,"Sin símbolo");
      ObjectSetString(0,PFX+"SB_IDX", OBJPROP_TEXT,"0/0");
   }
}

//+------------------------------------------------------------------+
//| TABS — GESTIÓN                                                   |
//+------------------------------------------------------------------+
void RefreshTabBar()
{
   int x=PNL_X,W=PNL_W,tabW=W/N_TABS;
   int tabY=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H;
   for(int t=0;t<N_TABS;t++)
   {
      bool active=(t==ActiveTab);
      ObjectSetInteger(0,PFX+"TAB"+IntegerToString(t),OBJPROP_BGCOLOR,
                       active?C'35,35,75':C'18,18,35');
      ObjectSetInteger(0,PFX+"TAB"+IntegerToString(t),OBJPROP_COLOR,
                       active?clrGold:C'140,140,160');
      if(active)
         ObjRect(PFX+"TABU"+IntegerToString(t),
                 x+t*tabW+2,tabY+TAB_H-3,tabW-4,3,clrGold,clrGold,0);
      else
         ObjectDelete(0,PFX+"TABU"+IntegerToString(t));
   }
}

void DeleteContentObjects()
{
   string pfxList[5]={PFX_OP,PFX_ACC,PFX_POS,PFX_CFG,PFX_EST};
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   {
      string name=ObjectName(0,i,0,-1);
      for(int p=0;p<5;p++)
         if(StringFind(name,pfxList[p])==0){ObjectDelete(0,name);break;}
   }
   ObjectDelete(0,EDIT_PRICE_NAME);
}

void DeletePanel()
{
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   {
      string name=ObjectName(0,i,0,-1);
      if(StringFind(name,SE_PREFIX)==0) continue;   // no borrar líneas de estructura
      if(StringFind(name,PFX)==0) ObjectDelete(0,name);
   }
   ObjectDelete(0,EDIT_PRICE_NAME);
   ObjectDelete(0,DRAG_ZONE);
   ChartRedraw();
}

void RebuildPanel()
{
   DeletePanel();
   BuildStaticStructure();
   RebuildActiveTab();
   UpdateInfoBar();
   ChartRedraw();
}

void RebuildActiveTab()
{
   DeleteContentObjects();
   RefreshTabBar();
   switch(ActiveTab)
   {
      case TAB_OPERAR: BuildTabOperar();      break;
      case TAB_CUENTA: BuildTabCuenta();      break;
      case TAB_POSIC:  BuildTabPosiciones();  break;
      case TAB_CONFIG: BuildTabConfig();      break;
      case TAB_ESTRAT: BuildTabEstrategias(); break;
   }
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| TAB 0 — OPERAR                                                   |
//+------------------------------------------------------------------+
void BuildTabOperar()
{
   int si=g_PanelSymIdx;
   int x=PNL_X,W=PNL_W;
   int y=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H+6;
   int cx=x+6,cw=W-12;
   int dg=(si>=0&&si<g_SymCount)?
          (int)SymbolInfoInteger(g_Symbols[si].name,SYMBOL_DIGITS):5;

   // Alerta Circuit Breaker
   if(g_CircuitBreakerOn)
   {
      ObjRect(PFX_OP+"CB_ALERT",cx,y,cw,36,C'40,5,5',C'180,20,20',2);
      ObjLbl(PFX_OP+"CB_TXT1",cx+cw/2,y+5,
             "⛔  CIRCUIT BREAKER ACTIVO",
             clrTomato,10,"Arial Bold",ANCHOR_CENTER);
      ObjLbl(PFX_OP+"CB_TXT2",cx+cw/2,y+22,
             "Trading bloqueado — Reanuda al 00:00 servidor",
             C'200,100,100',7,"Arial",ANCHOR_CENTER);
      y+=40;
   }

   if(si<0||si>=g_SymCount)
   {
      ObjLbl(PFX_OP+"NOSYM",cx+cw/2,y+10,
             "Sin símbolo seleccionado",clrYellow,9,"Arial Bold",ANCHOR_CENTER);
      return;
   }

   int alive=g_SysState[si].activeLiveStrategy;
   string liveStr=(alive>=0)?
      StringFormat("★ LIVE: %s  |  1:2: %s",
                   g_SysState[si].strategies[alive].name,
                   IsTrailingActive(si,alive)?"ON":"OFF")
      :"◌  Sin estrategia LIVE activa";
   color liveC =(alive>=0)?clrLimeGreen:clrYellow;
   color liveBG=(alive>=0)?C'8,28,8':C'22,20,10';
   color liveBD=(alive>=0)?C'30,110,30':C'100,90,20';
   ObjRect(PFX_OP+"LIVE_BG",cx,y,cw,26,liveBG,liveBD,1);
   ObjLbl(PFX_OP+"LIVE_ST",cx+cw/2,y+7,liveStr,liveC,9,"Arial Bold",ANCHOR_CENTER);
   y+=30;

   if(alive>=0)
   {
      ObjRect(PFX_OP+"CVLIVE_BG",cx,y,cw,44,C'12,22,12',C'35,80,35',1);
      ObjLbl(PFX_OP+"CVLIVE_TXT",cx+8,y+4,"CV (virtual):",C'150,150,150',7,"Arial");
      ObjLbl(PFX_OP+"CVLIVE_VAL",cx+cw/2,y+4,
             StringFormat("%d",g_SysState[si].strategies[alive].CV),
             clrLimeGreen,14,"Arial Bold",ANCHOR_CENTER);
      ObjLbl(PFX_OP+"CRLIVE_TXT",cx+8,y+26,"NIVEL → Lotaje:",C'150,150,150',7,"Arial");
      ObjLbl(PFX_OP+"CRLIVE_VAL",cx+cw/2,y+26,
             StringFormat("NIV %d  →  %.2f lots",
                          PairLevel(si),GetPairLot(si)),
             clrDodgerBlue,10,"Arial Bold",ANCHOR_CENTER);
      y+=48;
   }
   else
   {
      ObjRect(PFX_OP+"NOSIM_BG",cx,y,cw,26,C'20,20,30',C'50,50,80',1);
      ObjLbl(PFX_OP+"NOSIM_TXT",cx+cw/2,y+7,
             StringFormat("X=%d  →  LIVE tras %d pérdidas (operación %d)",
                          InpXActivacion,InpXActivacion,InpXActivacion+1),
             C'120,120,180',8,"Arial Bold",ANCHOR_CENTER);
      y+=30;
   }

   // SL / TP / RR
   ObjRect(PFX_OP+"SLTP_BG",cx,y,cw,30,C'22,22,38',C'50,50,85',1);
   double slP=SymSL(si), slOff=SymSLOffset(si), tpP=SymTP(si);
   double slReal=slP-slOff;
   double rr=(slP>0)?tpP/slP:0;
   ObjLbl(PFX_OP+"LBL_SL", cx+4,        y+4, "SL cálc.", clrTomato,    6,"Arial");
   ObjLbl(PFX_OP+"VAL_SL", cx+4,        y+16,StringFormat("%.0fpt",slP),clrTomato,9,"Arial Bold");
   ObjLbl(PFX_OP+"LBL_SLR",cx+cw/4,    y+4, "SL real",  clrOrange,    6,"Arial");
   ObjLbl(PFX_OP+"VAL_SLR",cx+cw/4,    y+16,StringFormat("%.0fpt",slReal),clrOrange,9,"Arial Bold");
   ObjLbl(PFX_OP+"LBL_TP", cx+cw/2,    y+4, "TP",        clrDodgerBlue,6,"Arial");
   ObjLbl(PFX_OP+"VAL_TP", cx+cw/2,    y+16,StringFormat("%.0fpt",tpP),clrDodgerBlue,9,"Arial Bold");
   ObjLbl(PFX_OP+"LBL_RR", cx+3*cw/4,  y+4, "R:R",       clrMagenta,   6,"Arial");
   ObjLbl(PFX_OP+"VAL_RR", cx+3*cw/4,  y+16,StringFormat("1:%.1f",rr), clrMagenta,9,"Arial Bold");
   y+=34;

   // Base y lotaje
   ObjRect(PFX_OP+"BASE_BG",cx,y,cw,28,C'14,22,14',C'35,75,35',1);
   ObjLbl(PFX_OP+"BASE_L",cx+6,y+4,"Base capital:",C'140,140,180',7,"Arial");
   ObjLbl(PFX_OP+"BASE_V",cx+cw-6,y+4,
          BaseDisplay(true),
          clrGold,8,"Arial Bold",ANCHOR_RIGHT_UPPER);
   ObjLbl(PFX_OP+"BASE_L2",cx+6,y+16,"Lot CR1:",C'140,140,180',7,"Arial");
   ObjLbl(PFX_OP+"BASE_V2",cx+cw-6,y+16,
          StringFormat("%.4f lots  (Riesgo: %.6f%%)",GetLotByCR(si,1),g_RiskTable[0]),
          clrLimeGreen,8,"Arial Bold",ANCHOR_RIGHT_UPPER);
   y+=32;

   // --- ESTADO ESTRUCTURA + CONDICIONES DE ENTRADA (1H / 3M) ---
   int h1BiasVal = (g_SysState[si].SE_H1.Bias==BIAS_BULLISH)?0:(g_SysState[si].SE_H1.Bias==BIAS_BEARISH)?1:2;
   int m3BiasVal = (g_SysState[si].SE_M3.Bias==BIAS_BULLISH)?0:(g_SysState[si].SE_M3.Bias==BIAS_BEARISH)?1:2;
   string h1Str = (h1BiasVal==0)?"ALC":(h1BiasVal==1)?"BAJ":"---";
   string m3Str = (m3BiasVal==0)?"ALC":(m3BiasVal==1)?"BAJ":"---";
   bool zB = g_SysState[si].confArmedBuy, zS = g_SysState[si].confArmedSell;
   bool limB = g_SysState[si].confVPendBuy, limS = g_SysState[si].confVPendSell;
   string zoneSt = zB?"BUY-ZONA":(zS?"SELL-ZONA":"SIN-ZONA");
   string limSt = (limB||limS)?"LIMIT-PUESTA":"SIN-LIMIT";
   string missSt = "";
   if(g_SysState[si].hasLive) missSt = "TIENE-ORDEN";
   else if(limB||limS)        missSt = "LIMIT PUESTA";
   else if(g_SysState[si].confWaitBuy)  missSt = "50% CONGELADO · ESPERA PRECIO (compra)";
   else if(g_SysState[si].confWaitSell) missSt = "50% CONGELADO · ESPERA PRECIO (venta)";
   else if(zB && h1Str=="ALC") missSt = "ESPERA CHoCH M3 (compra)";
   else if(zS && h1Str=="BAJ") missSt = "ESPERA CHoCH M3 (venta)";
   else if(zB && h1Str!="ALC") missSt = "FALTA: H1 alcista";
   else if(zS && h1Str!="BAJ") missSt = "FALTA: H1 bajista";
   else if(!zB && !zS) missSt = "FALTA: tocar zona";
   else missSt = "CONFIRMAR";
   ObjRect(PFX_OP+"ENTER_BG",cx,y,cw,36,C'16,24,16',C'40,100,40',1);
   ObjLbl(PFX_OP+"ENTER_H",cx+4,y+3,"ENTRADA: H1="+h1Str+" M3="+m3Str+" | "+zoneSt+" "+limSt,C'150,200,100',7,"Arial Bold");
   ObjLbl(PFX_OP+"ENTER_M",cx+4,y+17,"CORRELACION: "+missSt,C'200,220,80',7,"Arial Bold");
   y+=40;

   //--- ESTRATEGIA 2: rango 4H + order blocks históricos (OB+imbalance) --------
   if(InpUseStrat2)
   {
      string s2="";
      if(g_SysState[si].SE_H4.Valid)
         s2=StringFormat("S2 · RANGO 4H: L1=%s  L2=%s  50%%=%s",
                         DoubleToString(g_SysState[si].SE_H4.L1,dg),
                         DoubleToString(g_SysState[si].SE_H4.L2,dg),
                         DoubleToString(g_SysState[si].SE_H4.EQ,dg));
      else s2="S2 · SIN RANGO 4H";
      string s2m=StringFormat("OBs: %d C (%d en rango) · %d V (%d en rango) · armados %d · 50%% M3 %d · mitigados %d",
                              g_SysState[si].ob2Buys,g_SysState[si].ob2BuyRange,
                              g_SysState[si].ob2Sells,g_SysState[si].ob2SellRange,
                              g_SysState[si].ob2Armed,g_SysState[si].ob2Frozen,
                              g_SysState[si].ob2Mitigated);
      if(g_SysState[si].ob2Outside)
         s2m+=" · PRECIO FUERA RANGO → OB histórico activos";
      else
         s2m+=" · PRECIO EN RANGO";
      ObjRect(PFX_OP+"S2_BG",cx,y,cw,30,C'14,22,30',C'30,60,90',1);
      ObjLbl(PFX_OP+"S2_H",cx+4,y+3,s2,C'90,200,255',7,"Arial Bold");
      ObjLbl(PFX_OP+"S2_M",cx+4,y+17,s2m,
             (g_SysState[si].ob2Buys>0)?clrLimeGreen:
             (g_SysState[si].ob2Sells>0)?clrTomato:C'140,140,160',7,"Arial Bold");
      y+=34;
   }

   ObjSep(PFX_OP+"SEP0",cx,y,cw); y+=6;

   // Precio límite
   ObjLbl(PFX_OP+"PH",cx+4,y,"PRECIO LÍMITE",C'120,120,160',7,"Arial Bold"); y+=14;
   ObjEdit(EDIT_PRICE_NAME,cx,y,cw,26,
           (g_LimitPrice>0)?DoubleToString(g_LimitPrice,dg):"0",
           C'25,25,42',clrWhite,10);
   y+=30;
   int tw=(cw-8)/3;
   ObjBtn(PFX_OP+"ASK",cx,           y,tw,22,"= ASK",C'0,60,100',  clrWhite,8,"Arial");
   ObjBtn(PFX_OP+"BID",cx+tw+4,      y,tw,22,"= BID",C'100,50,0',  clrWhite,8,"Arial");
   ObjBtn(PFX_OP+"RST",cx+2*(tw+4),  y,tw,22,"RESET",C'50,50,50',  clrWhite,8,"Arial");
   y+=26;

   ObjSep(PFX_OP+"SEP1",cx,y,cw); y+=6;

   // Operación manual
   ObjLbl(PFX_OP+"MAN_H",cx+4,y,"OPERACIÓN MANUAL",C'140,140,80',7,"Arial Bold"); y+=14;
   int bw2=(cw-4)/2;
   ObjBtn(PFX_OP+"BUY",    cx,        y,bw2,32,"▲  BUY",  C'0,120,0', clrWhite,10);
   ObjBtn(PFX_OP+"SELL",   cx+bw2+4,  y,bw2,32,"▼  SELL", C'170,0,0', clrWhite,10);
   y+=36;
   ObjBtn(PFX_OP+"BUYLMT", cx,        y,bw2,24,"BUY LIMIT",  C'0,80,60', clrWhite,8);
   ObjBtn(PFX_OP+"SELLLMT",cx+bw2+4,  y,bw2,24,"SELL LIMIT", C'120,40,0',clrWhite,8);
   y+=28;
   ObjSep(PFX_OP+"SEP2",cx,y,cw); y+=6;
   ObjBtn(PFX_OP+"CLOSEALL",cx,y,cw,24,
          StringFormat("✕  CERRAR TODO [%s]",g_Symbols[si].name),
          C'80,0,80',clrWhite,8);
}

//+------------------------------------------------------------------+
//| TAB 1 — CUENTA                                                   |
//+------------------------------------------------------------------+
void BuildCuentaRow(string pfx,int cx,int ry,int cw,
                    string hdr,string val,color valC)
{
   ObjRect(pfx+"BG",cx,ry,cw,38,C'18,22,32',C'40,50,80',1);
   ObjLbl(pfx+"H",cx+8,ry+5,hdr,C'120,120,150',7,"Arial");
   ObjLbl(pfx+"V",cx+cw-8,ry+12,val,valC,12,"Arial Bold",ANCHOR_RIGHT_UPPER);
}

void BuildTabCuenta()
{
   int x=PNL_X,W=PNL_W;
   int y=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H+6;
   int cx=x+6,cw=W-12;

   string cur=AccountInfoString(ACCOUNT_CURRENCY);
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double eq =AccountInfoDouble(ACCOUNT_EQUITY);
   double mrg=AccountInfoDouble(ACCOUNT_MARGIN);
   double fm =AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   double mLv=(mrg>0)?(eq/mrg)*100.0:0.0;
   double fPL=eq-bal;
   double uPct=(bal>0)?MathMin(mrg/bal,1.0):0.0;

   BuildCuentaRow(PFX_ACC+"BAL",cx,y,cw,"BALANCE",
                  StringFormat("%.2f  %s",bal,cur),clrWhite); y+=42;
   BuildCuentaRow(PFX_ACC+"EQ",cx,y,cw,"EQUIDAD",
                  StringFormat("%.2f  %s",eq,cur),
                  (eq>=bal)?clrLimeGreen:clrTomato); y+=42;
   BuildCuentaRow(PFX_ACC+"PL",cx,y,cw,"P&L FLOTANTE",
                  StringFormat("%s%.2f  %s",(fPL>=0)?"+":"",fPL,cur),
                  (fPL>=0)?clrLimeGreen:clrTomato); y+=42;
   BuildCuentaRow(PFX_ACC+"MRG",cx,y,cw,"MARGEN USADO",
                  StringFormat("%.2f  %s",mrg,cur),clrOrange); y+=42;
   BuildCuentaRow(PFX_ACC+"FM",cx,y,cw,"MARGEN LIBRE",
                  StringFormat("%.2f  %s",fm,cur),
                  (fm<bal*0.20)?clrTomato:clrLimeGreen); y+=42;

   string mTxt; color mC;
   if(mrg<=0)       {mTxt="N/A";                     mC=C'120,120,120';}
   else if(mLv>=200){mTxt=StringFormat("%.0f%%",mLv); mC=clrLimeGreen;}
   else if(mLv>=120){mTxt=StringFormat("%.0f%%",mLv); mC=clrYellow;}
   else if(mLv>=100){mTxt=StringFormat("%.0f%%",mLv); mC=clrOrange;}
   else             {mTxt=StringFormat("%.0f%%",mLv); mC=clrTomato;}
   BuildCuentaRow(PFX_ACC+"MPC",cx,y,cw,"NIVEL DE MARGEN",mTxt,mC); y+=42;

   ObjRect(PFX_ACC+"BASE_BG",cx,y,cw,38,C'14,22,14',C'35,75,35',1);
   ObjLbl(PFX_ACC+"BASE_H",cx+8,y+5,
          StringFormat("BASE CAPITAL  (%s)",CapitalModeName()),
          C'120,150,120',7,"Arial");
   ObjLbl(PFX_ACC+"BASE_V",cx+cw-8,y+12,
          StringFormat("%s   Máx.Bal: %.2f",BaseDisplay(false),g_BaseMaxBalance),
          clrGold,10,"Arial Bold",ANCHOR_RIGHT_UPPER); y+=42;

   ObjLbl(PFX_ACC+"BL",cx,y,"Uso de margen / balance:",C'100,100,130',7,"Arial"); y+=14;
   ObjRect(PFX_ACC+"BARBG",cx,y,cw,14,C'30,30,30',C'55,55,55',1);
   int fw=(int)MathMax(2,(double)cw*uPct);
   color bC=(uPct<0.30)?clrLimeGreen:(uPct<0.60)?clrYellow:(uPct<0.80)?clrOrange:clrTomato;
   ObjRect(PFX_ACC+"BAR",cx,y,fw,14,bC,bC,0);
   ObjLbl(PFX_ACC+"BPCT",cx+cw/2,y+2,
          StringFormat("%.1f%%",uPct*100),clrWhite,7,"Arial",ANCHOR_CENTER); y+=20;

   ObjSep(PFX_ACC+"SEP",cx,y,cw); y+=8;
   string at=(AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_DEMO)?"DEMO":"REAL";
   ObjLbl(PFX_ACC+"BRK",cx,y,
          StringFormat("Broker: %s",AccountInfoString(ACCOUNT_COMPANY)),
          C'100,100,130',7,"Arial"); y+=14;
   ObjLbl(PFX_ACC+"ACC",cx,y,
          StringFormat("Cuenta #%d  [ %s ]",
                       (int)AccountInfoInteger(ACCOUNT_LOGIN),at),
          (at=="DEMO")?clrYellow:clrLimeGreen,8,"Arial Bold");
}

//+------------------------------------------------------------------+
//| TAB 2 — POSICIONES                                               |
//+------------------------------------------------------------------+
void BuildTabPosiciones()
{
   int si=g_PanelSymIdx;
   int x=PNL_X,W=PNL_W;
   int y=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H+6;
   int cx=x+6,cw=W-12;
   int dg=(si>=0&&si<g_SymCount)?
          (int)SymbolInfoInteger(g_Symbols[si].name,SYMBOL_DIGITS):5;

   // Filtrar trades del símbolo visible
   int symTrades[]; int stCount=0;
   for(int k=0;k<g_TradeCount;k++)
      if(g_Trades[k].symbolIdx==si)
      { ArrayResize(symTrades,stCount+1); symTrades[stCount]=k; stCount++; }

   int nT=0,nP=0; double tPL=0;
   for(int i=0;i<stCount;i++)
   { int k=symTrades[i];
     if(g_Trades[k].isPending) nP++;
     else{ nT++; tPL+=g_Trades[k].profit; } }

   string sym=(si>=0&&si<g_SymCount)?g_Symbols[si].name:"---";
   bool hasLive=(si>=0&&si<g_SymCount)&&g_SysState[si].hasLive;
   int  aliveS =(si>=0&&si<g_SymCount)?g_SysState[si].activeLiveStrategy:-1;

   ObjRect(PFX_POS+"HDR",cx,y,cw,44,C'12,22,32',C'30,60,100',1);
   ObjLbl(PFX_POS+"HDR0",cx+cw/2,y+4,
          StringFormat("[ %s ]  Abiertas: %d   Pend: %d",sym,nT,nP),
          C'160,160,220',8,"Arial Bold",ANCHOR_CENTER);
   ObjLbl(PFX_POS+"HDRPL",cx+cw/2,y+20,
          StringFormat("P&L:  %s%.2f",(tPL>=0)?"+":"",tPL),
          (tPL>=0)?clrLimeGreen:clrTomato,10,"Arial Bold",ANCHOR_CENTER);

   string sysStr=hasLive&&aliveS>=0?
      StringFormat("LIVE: %s  CV=%d  NIVEL=%d  Lot=%.2f",
                   g_SysState[si].strategies[aliveS].name,
                   g_SysState[si].strategies[aliveS].CV,
                   PairLevel(si),GetPairLot(si))
      :"Simulando  (sin LIVE)";
   ObjLbl(PFX_POS+"HDRSYS",cx+8,y+34,sysStr,
          hasLive?clrLimeGreen:clrYellow,7,"Arial");
   y+=48;

   if(stCount==0)
   {
      ObjRect(PFX_POS+"EMPTY",cx,y,cw,50,C'18,18,28',C'40,40,70',1);
      ObjLbl(PFX_POS+"ET1",cx+cw/2,y+10,
             "No hay operaciones para este símbolo",
             C'100,100,130',8,"Arial",ANCHOR_CENTER);
      ObjLbl(PFX_POS+"ET2",cx+cw/2,y+28,
             hasLive?"Esperando señal de entrada":"Estrategias en simulación",
             C'80,80,110',7,"Arial",ANCHOR_CENTER);
      return;
   }

   int rowH=78,maxV=4;
   int visible=MathMin(stCount-g_ScrollOffset,maxV);
   for(int v=0;v<visible;v++)
   {
      int vi=v+g_ScrollOffset;
      if(vi>=stCount) break;
      int k=symTrades[vi];
      TradeRecord tr=g_Trades[k];
      string rid=IntegerToString(v);
      int    st2=tr.strategyId;
      string sn=(st2>=0&&st2<STRAT_COUNT)?
                 g_SysState[si].strategies[st2].name:"MAN";
      bool trailOn=(st2>=0)?IsTrailingActive(si,st2):false;

      color rBG,rBRD;
      if(tr.isPending)    {rBG=C'22,22,14';rBRD=C'70,70,25';}
      else if(tr.isManual){rBG=C'14,18,30';rBRD=C'35,55,110';}
      else if(tr.orderType==POSITION_TYPE_BUY){rBG=C'10,26,14';rBRD=C'25,85,35';}
      else{rBG=C'28,12,14';rBRD=C'85,25,30';}

      ObjRect(PFX_POS+"ROW"+rid,cx,y,cw,rowH-2,rBG,rBRD,1);
      color barC=(tr.orderType==POSITION_TYPE_BUY||
                  tr.orderType==ORDER_TYPE_BUY_LIMIT||
                  tr.orderType==ORDER_TYPE_BUY_STOP)?clrLimeGreen:clrTomato;
      if(tr.isManual) barC=clrDodgerBlue;
      ObjRect(PFX_POS+"BAR"+rid,cx,y,4,rowH-2,barC,barC,0);

      ObjLbl(PFX_POS+"L1"+rid,cx+10,y+4,
             StringFormat("[%s]  %s  #%d",
                          sn,GetTypeName(tr.orderType,tr.isPending),(int)tr.ticket),
             tr.isManual?clrDodgerBlue:GetTypeColor(tr.orderType,tr.isPending),
             9,"Arial Bold");

      ObjRect(PFX_POS+"T12BG"+rid,cx+cw-52,y+3,48,14,
              trailOn?(tr.slMoved?C'50,40,0':C'0,60,0'):C'30,30,30',
              trailOn?(tr.slMoved?C'120,100,0':C'0,120,0'):C'50,50,50',1);
      ObjLbl(PFX_POS+"T12"+rid,cx+cw-52+24,y+4,
             tr.slMoved?"PROT.":(trailOn?"1:2 ON":"1:2 OFF"),
             tr.slMoved?clrGold:(trailOn?clrLimeGreen:C'100,100,100'),
             6,"Arial Bold",ANCHOR_CENTER);

      ObjLbl(PFX_POS+"L2"+rid,cx+10,y+20,
             StringFormat("Lots: %.2f   Lot Base: %.2f",
                          tr.lots,GetLotByCR(si,1)),
             C'160,160,200',8,"Arial Bold");

      string slS=(tr.sl>0)?StringFormat("%.*f",dg,tr.sl):"---";
      string tpS=(tr.tp>0)?StringFormat("%.*f",dg,tr.tp):"---";
      ObjLbl(PFX_POS+"L3O"+rid,cx+10,y+34,
             StringFormat("Open: %.*f",dg,tr.openPrice),C'130,130,160',7,"Arial");
      ObjLbl(PFX_POS+"L3S"+rid,cx+10,y+46,
             StringFormat("SL: %s",slS),clrTomato,7,"Arial Bold");
      ObjLbl(PFX_POS+"L3T"+rid,cx+cw/2,y+46,
             StringFormat("TP: %s",tpS),clrDodgerBlue,7,"Arial Bold");

      if(!tr.isPending)
      {
         color plC=(tr.profit>=0)?clrLimeGreen:clrTomato;
         ObjRect(PFX_POS+"PLBG"+rid,cx+8,y+58,cw-64,16,C'10,10,18',C'30,30,60',1);
         ObjLbl(PFX_POS+"L4"+rid,cx+8+(cw-64)/2,y+60,
                StringFormat("P&L:  %s%.2f",(tr.profit>=0)?"+":"",tr.profit),
                plC,9,"Arial Bold",ANCHOR_CENTER);
      }

      // Botón close — usa índice real k en el nombre
      ObjBtn(PFX_POS+"CLZ"+IntegerToString(k),
             cx+cw-54,y+54,50,20,"✕ CLOSE",C'90,20,20',clrWhite,7,"Arial Bold");
      y+=rowH+4;
   }

   if(stCount>maxV)
   {
      ObjSep(PFX_POS+"SEP",cx,y,cw); y+=4;
      int hw=(cw-4)/2;
      ObjBtn(PFX_POS+"SCRUP",cx,      y,hw,22,"▲ Anterior", C'30,30,50',clrWhite,8,"Arial");
      ObjBtn(PFX_POS+"SCRDN",cx+hw+4, y,hw,22,"▼ Siguiente",C'30,30,50',clrWhite,8,"Arial");
      y+=26;
      ObjLbl(PFX_POS+"SCRINF",cx+cw/2,y,
             StringFormat("%d - %d  de  %d",
                          g_ScrollOffset+1,
                          MathMin(g_ScrollOffset+maxV,stCount),stCount),
             C'100,100,130',7,"Arial",ANCHOR_CENTER);
   }
}

//+------------------------------------------------------------------+
//| TAB 3 — CONFIG                                                   |
//+------------------------------------------------------------------+
void BuildTabConfig()
{
   int si=g_PanelSymIdx;
   int x=PNL_X,W=PNL_W;
   int y=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H+6;
   int cx=x+6,cw=W-12;

   ObjLbl(PFX_CFG+"T1",cx+cw/2,y,"PARÁMETROS ACTIVOS",
          clrGold,9,"Arial Bold",ANCHOR_CENTER); y+=20;
   ObjSep(PFX_CFG+"S1",cx,y,cw); y+=8;

   string symName=(si>=0&&si<g_SymCount)?g_Symbols[si].name:"---";
   bool hasLive=(si>=0&&si<g_SymCount)&&g_SysState[si].hasLive;
   int  aliveS =(si>=0&&si<g_SymCount)?g_SysState[si].activeLiveStrategy:-1;
   string liveStr=(hasLive&&aliveS>=0)?
                   g_SysState[si].strategies[aliveS].name:"NINGUNA";

   string rows_L[14],rows_V[14]; color rows_C[14];
   rows_L[0]="Símbolo panel";
   rows_V[0]=symName; rows_C[0]=clrGold;

   rows_L[1]="Timeframe";
   rows_V[1]=EnumToString(Period()); rows_C[1]=C'150,150,150';

   rows_L[2]="Magic Base";
   rows_V[2]=IntegerToString(InpMagicNumber); rows_C[2]=clrLimeGreen;

   rows_L[3]="SL cálc./ real";
   rows_V[3]=StringFormat("%.0f / %.0f pts",SymSL(si),SymSL(si)-SymSLOffset(si));
   rows_C[3]=clrTomato;

   rows_L[4]="TP";
   rows_V[4]=StringFormat("%.0f pts",SymTP(si)); rows_C[4]=clrDodgerBlue;

   rows_L[5]="Activación 1:2";
   rows_V[5]=StringFormat("%.0f pts",SymActivation(si)); rows_C[5]=clrMagenta;

   rows_L[6]="SL protegido";
   rows_V[6]=StringFormat("%.0f pts",SymProtectedSL(si)); rows_C[6]=clrOrange;

   rows_L[7]="X activación";
   rows_V[7]=StringFormat("%d → LIVE tras %d pérdidas (op.%d)",
                          InpXActivacion,InpXActivacion,InpXActivacion+1);
   rows_C[7]=clrOrange;

   rows_L[8]="LIVE activa";
   rows_V[8]=liveStr; rows_C[8]=hasLive?clrLimeGreen:clrYellow;

   rows_L[9]="Base capital / modo";
   rows_V[9]=BaseDisplay(false); rows_C[9]=clrGold;

   rows_L[10]="Bal. máx hist.";
   rows_V[10]=StringFormat("%.2f",g_BaseMaxBalance); rows_C[10]=clrGold;

   rows_L[11]="Nivel par / Lot";
   rows_V[11]=StringFormat("Niv.%d  %.4f lots",PairLevel(si),GetPairLot(si));
   rows_C[11]=clrLimeGreen;

   rows_L[12]="CB Diario";
   rows_V[12]=StringFormat("%.1f%%  [%s]",InpMaxDailyLossPct,
              g_CircuitBreakerOn?"ACTIVO":"OK");
   rows_C[12]=g_CircuitBreakerOn?clrTomato:clrLimeGreen;

   rows_L[13]="Símbolos activos";
   rows_V[13]=StringFormat("%d configurados",g_SymCount); rows_C[13]=C'130,130,180';

   for(int i=0;i<14;i++)
   {
      color bg=(i%2==0)?C'20,20,32':C'16,16,26';
      ObjRect(PFX_CFG+"R"+IntegerToString(i),cx,y,cw,24,bg,bg,0);
      ObjLbl(PFX_CFG+"L"+IntegerToString(i),cx+8,y+6,
             rows_L[i],C'120,120,150',7,"Arial");
      ObjLbl(PFX_CFG+"V"+IntegerToString(i),cx+cw-8,y+6,
             rows_V[i],rows_C[i],8,"Arial Bold",ANCHOR_RIGHT_UPPER);
      y+=25;
   }

   ObjSep(PFX_CFG+"S2",cx,y,cw); y+=8;
   int bw=(cw-4)/2;
   ObjBtn(PFX_CFG+"CLR",cx,      y,bw,28,"🗑  Borrar estado", C'70,25,25',clrWhite,8,"Arial Bold");
   ObjBtn(PFX_CFG+"SAV",cx+bw+4, y,bw,28,"💾  Guardar ahora", C'25,70,25',clrWhite,8,"Arial Bold");
   y+=32;
   ObjBtn(PFX_CFG+"ADV",cx,y,cw,28,
          g_AdvancedMode?"⚡ MODO AVANZADO: ACTIVO":"⚡ MODO AVANZADO: INACTIVO",
          g_AdvancedMode?C'0,100,60':C'50,50,70',clrWhite,9,"Arial Bold");
}

//+------------------------------------------------------------------+
//| TAB 4 — ESTRATEGIAS                                              |
//+------------------------------------------------------------------+
void BuildTabEstrategias()
{
   int si=g_PanelSymIdx;
   int x=PNL_X,W=PNL_W;
   int y=PNL_Y+TITLE_H+INFOBAR_H+SYMBAR_H+TAB_H+6;
   int cx=x+6,cw=W-12;

   if(si<0||si>=g_SymCount)
   {
      ObjLbl(PFX_EST+"NOSYM",cx+cw/2,y+20,
             "Sin símbolo seleccionado",clrYellow,9,"Arial Bold",ANCHOR_CENTER);
      return;
   }

   bool hasLive=g_SysState[si].hasLive;
   int  alive  =g_SysState[si].activeLiveStrategy;

   string sysStr;
   if(hasLive&&alive>=0)
   { int ll=g_SysState[si].strategies[alive].liveLogicLevel;
     sysStr=StringFormat("★  LIVE: %s  |  CV=%d  NIVEL=%d%s  Lot=%.2f",
                         g_SysState[si].strategies[alive].name,
                         g_SysState[si].strategies[alive].CV,
                         PairLevel(si),(ll>0?StringFormat(" (lóg.N%d)",ll):""),
                         GetPairLot(si)); }
   else
      sysStr=StringFormat("◌  SIMULANDO  |  X=%d  →  LIVE tras %d pérdidas (op.%d)",
                          InpXActivacion,InpXActivacion,InpXActivacion+1);
   color sysC =hasLive?clrLimeGreen:clrYellow;
   color sysBG=hasLive?C'8,25,8':C'22,20,8';
   ObjRect(PFX_EST+"HDR",cx,y,cw,26,sysBG,hasLive?C'30,110,30':C'100,90,20',1);
   ObjLbl(PFX_EST+"HTXT",cx+cw/2,y+7,sysStr,sysC,8,"Arial Bold",ANCHOR_CENTER);
   y+=30;

   int gMax=0; string gMaxN="---";
   for(int s=0;s<STRAT_COUNT;s++)
   {
      if(!g_SysState[si].strategies[s].enabled) continue;
      if(g_SysState[si].strategies[s].CV_Max>gMax)
      { gMax=g_SysState[si].strategies[s].CV_Max;
        gMaxN=g_SysState[si].strategies[s].name; }
   }
   ObjRect(PFX_EST+"GMAX",cx,y,cw,22,C'25,22,8',C'110,95,18',1);
   ObjLbl(PFX_EST+"GMTXT",cx+cw/2,y+5,
          StringFormat("CV MAX [%s]:  %d   (%s)",g_Symbols[si].name,gMax,gMaxN),
          clrGold,9,"Arial Bold",ANCHOR_CENTER);
   y+=26;
   ObjSep(PFX_EST+"SEP0",cx,y,cw); y+=6;

   int rowH=64;
   for(int st=0;st<STRAT_COUNT;st++)
   {
      bool ena      = g_SysState[si].strategies[st].enabled;
      bool isLive   = g_SysState[si].strategies[st].isLive;
      bool isPaused = g_SysState[si].strategies[st].cbPaused;
      bool rdy      = (g_SysState[si].strategies[st].CV>=(InpXActivacion+1));
      string rid    = IntegerToString(st);

      color rBG,rBRD;
      if(!ena)       {rBG=C'16,16,16'; rBRD=C'35,35,35';}
      else if(isPaused){rBG=C'26,10,10';rBRD=C'110,28,28';}
      else if(isLive)  {rBG=C'8,26,8';  rBRD=C'28,110,28';}
      else if(rdy)     {rBG=C'26,24,8'; rBRD=C'100,95,18';}
      else             {rBG=C'16,18,28';rBRD=C'38,42,80';}

      ObjRect(PFX_EST+"ROW"+rid,cx,y,cw,rowH-2,rBG,rBRD,1);
      color lbarC=!ena?C'35,35,35':isPaused?clrTomato:
                  isLive?clrLimeGreen:rdy?clrYellow:C'60,70,140';
      ObjRect(PFX_EST+"LB"+rid,cx,y,4,rowH-2,lbarC,lbarC,0);

      ObjLbl(PFX_EST+"NM"+rid,cx+10,y+5,
             g_SysState[si].strategies[st].name,
             ena?clrWhite:C'70,70,70',12,"Arial Bold");

      string est; color estC,estBG;
      if(!ena)       {est="OFF";      estC=C'80,80,80'; estBG=C'25,25,25';}
      else if(isPaused){est="CB PAUSE";estC=clrBlack;   estBG=clrTomato;}
      else if(isLive)  {est="★ LIVE"; estC=clrBlack;   estBG=clrLimeGreen;}
      else if(rdy)     {est="ESPERA"; estC=clrBlack;   estBG=clrYellow;}
      else             {est="SIM";    estC=clrWhite;   estBG=C'35,45,90';}

      int ebw=60;
      ObjRect(PFX_EST+"EB"+rid,cx+cw-ebw-4,y+4,ebw,16,estBG,estBG,0);
      ObjLbl(PFX_EST+"ES"+rid,cx+cw-ebw-4+ebw/2,y+5,
             est,estC,7,"Arial Bold",ANCHOR_CENTER);

      if(ena)
      {
         ObjLbl(PFX_EST+"CVL"+rid,cx+10,y+24,"CV:",C'120,120,150',7,"Arial");
         ObjLbl(PFX_EST+"CVV"+rid,cx+38,y+24,
                IntegerToString(g_SysState[si].strategies[st].CV),
                IsTrailingActive(si,st)?clrLimeGreen:clrWhite,9,"Arial Bold");
         ObjLbl(PFX_EST+"FAL"+rid,cx+72,y+24,"Falta:",C'120,120,150',7,"Arial");
         ObjLbl(PFX_EST+"FAV"+rid,cx+102,y+24,
                IntegerToString(rdy?0:MathMax(0,(InpXActivacion+1)-g_SysState[si].strategies[st].CV)),
                rdy?clrYellow:(g_SysState[si].strategies[st].CV>=(InpXActivacion/2+2))?clrOrange:clrDodgerBlue,
                9,"Arial Bold");

         ObjLbl(PFX_EST+"CML"+rid,cx+10,y+38,"CVmax:",C'120,120,150',7,"Arial");
         ObjLbl(PFX_EST+"CMV"+rid,cx+50,y+38,
                IntegerToString(g_SysState[si].strategies[st].CV_Max),
                clrGold,9,"Arial Bold");

         ObjLbl(PFX_EST+"TRL"+rid,cx+cw/2,y+24,"1:2:",C'120,120,150',7,"Arial");
         ObjLbl(PFX_EST+"TRV"+rid,cx+cw/2+28,y+24,
                IsTrailingActive(si,st)?"ON":"OFF",
                IsTrailingActive(si,st)?clrLimeGreen:C'100,100,100',8,"Arial Bold");

         if(isLive)
         {
            ObjLbl(PFX_EST+"CRL"+rid,cx+cw/2,y+38,"NIV→Lot:",C'120,120,150',7,"Arial");
            ObjLbl(PFX_EST+"CRV"+rid,cx+cw/2+46,y+38,
                   StringFormat("%d→%.2f",PairLevel(si),GetPairLot(si)),
                   clrDodgerBlue,8,"Arial Bold");
         }

         int  thr=InpXActivacion+1;
         int  bw2=cw-12;
         ObjRect(PFX_EST+"PBG"+rid,cx+6,y+54,bw2,5,C'25,25,25',C'40,40,40',1);
         double pct=(thr>0)?MathMin((double)g_SysState[si].strategies[st].CV/thr,1.5):0.0;
         int    fw=(int)MathMax(1,(double)bw2*MathMin(pct,1.0));
         color  pfC=isLive?clrLimeGreen:
                    (pct>=1.0?clrYellow:(pct>=0.6?clrDodgerBlue:C'45,55,110'));
         ObjRect(PFX_EST+"PFL"+rid,cx+6,y+54,fw,5,pfC,pfC,0);
      }
      else
      {
         ObjLbl(PFX_EST+"DIS"+rid,cx+cw/2,y+25,
                "Desactivada en Inputs",C'55,55,55',7,"Arial",ANCHOR_CENTER);
      }
      y+=rowH+4;
   }

   ObjSep(PFX_EST+"SEP1",cx,y,cw); y+=6;
   int bw2=(cw-4)/2;
   ObjBtn(PFX_EST+"RSTALL",cx,       y,bw2,24,"↺  Reset símbolo",C'60,25,25',clrWhite,7,"Arial Bold");
   ObjBtn(PFX_EST+"FRCNXT", cx+bw2+4,y,bw2,24,"▶  Buscar LIVE",  C'25,55,25',clrWhite,7,"Arial Bold");
}

//+------------------------------------------------------------------+
//| LÍNEAS DE REFERENCIA                                             |
//+------------------------------------------------------------------+
void DrawRefLine(string name,double price,string label,
                 color clr,ENUM_LINE_STYLE style,int width)
{
   string ln=name+"_L", tn=name+"_T";
   if(ObjectFind(0,ln)<0)
   { ObjectCreate(0,ln,OBJ_HLINE,0,0,price);
     ObjectSetInteger(0,ln,OBJPROP_COLOR,clr);
     ObjectSetInteger(0,ln,OBJPROP_WIDTH,width);
     ObjectSetInteger(0,ln,OBJPROP_STYLE,style);
     ObjectSetInteger(0,ln,OBJPROP_BACK,true);
     ObjectSetInteger(0,ln,OBJPROP_SELECTABLE,false); }
   else ObjectSetDouble(0,ln,OBJPROP_PRICE,price);
   if(ObjectFind(0,tn)<0)
   { ObjectCreate(0,tn,OBJ_TEXT,0,iTime(_Symbol,PERIOD_CURRENT,0),price);
     ObjectSetInteger(0,tn,OBJPROP_COLOR,clr);
     ObjectSetInteger(0,tn,OBJPROP_FONTSIZE,8);
     ObjectSetString(0,tn,OBJPROP_FONT,"Arial");
     ObjectSetInteger(0,tn,OBJPROP_ANCHOR,ANCHOR_LEFT);
     ObjectSetInteger(0,tn,OBJPROP_BACK,false);
     ObjectSetInteger(0,tn,OBJPROP_SELECTABLE,false); }
   else ObjectMove(0,tn,0,iTime(_Symbol,PERIOD_CURRENT,0),price);
   ObjectSetString(0,tn,OBJPROP_TEXT,label);
}

void UpdateLimitLine()
{
   int si=g_PanelSymIdx;
   if(g_LimitPrice<=0){RemoveLimitLine();return;}
   if(si<0||si>=g_SymCount) return;
   string sym=g_Symbols[si].name;
   int    dg =(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   double pt =SymbolInfoDouble(sym,SYMBOL_POINT);

   if(ObjectFind(0,LINE_LIMIT_NAME)<0)
   { ObjectCreate(0,LINE_LIMIT_NAME,OBJ_HLINE,0,0,g_LimitPrice);
     ObjectSetInteger(0,LINE_LIMIT_NAME,OBJPROP_COLOR,clrGold);
     ObjectSetInteger(0,LINE_LIMIT_NAME,OBJPROP_WIDTH,2);
     ObjectSetInteger(0,LINE_LIMIT_NAME,OBJPROP_STYLE,STYLE_DASH);
     ObjectSetInteger(0,LINE_LIMIT_NAME,OBJPROP_BACK,false);
     ObjectSetInteger(0,LINE_LIMIT_NAME,OBJPROP_SELECTABLE,true); }
   else ObjectSetDouble(0,LINE_LIMIT_NAME,OBJPROP_PRICE,g_LimitPrice);

   if(ObjectFind(0,LINE_LIMIT_LABEL)<0)
   { ObjectCreate(0,LINE_LIMIT_LABEL,OBJ_TEXT,0,iTime(_Symbol,PERIOD_CURRENT,0),g_LimitPrice);
     ObjectSetInteger(0,LINE_LIMIT_LABEL,OBJPROP_COLOR,clrGold);
     ObjectSetInteger(0,LINE_LIMIT_LABEL,OBJPROP_FONTSIZE,9);
     ObjectSetString(0,LINE_LIMIT_LABEL,OBJPROP_FONT,"Arial Bold");
     ObjectSetInteger(0,LINE_LIMIT_LABEL,OBJPROP_ANCHOR,ANCHOR_LEFT);
     ObjectSetInteger(0,LINE_LIMIT_LABEL,OBJPROP_BACK,false);
     ObjectSetInteger(0,LINE_LIMIT_LABEL,OBJPROP_SELECTABLE,false); }
   else ObjectMove(0,LINE_LIMIT_LABEL,0,iTime(_Symbol,PERIOD_CURRENT,0),g_LimitPrice);
   ObjectSetString(0,LINE_LIMIT_LABEL,OBJPROP_TEXT,
                   StringFormat("  LIMIT[%s]: %s",sym,DoubleToString(g_LimitPrice,dg)));

   double slPts=SymSL(si)-SymSLOffset(si);
   double tpPts=SymTP(si);
   double slR=NormalizeDouble(g_LimitPrice-slPts*pt,dg);
   double tpR=NormalizeDouble(g_LimitPrice+tpPts*pt,dg);
   DrawRefLine(LINE_LIMIT_SL,slR,"  SL: "+DoubleToString(slR,dg),clrTomato,STYLE_DOT,1);
   DrawRefLine(LINE_LIMIT_TP,tpR,"  TP: "+DoubleToString(tpR,dg),clrDodgerBlue,STYLE_DOT,1);
   ChartRedraw();
}

void RemoveLimitLine()
{
   ObjectDelete(0,LINE_LIMIT_NAME);
   ObjectDelete(0,LINE_LIMIT_LABEL);
   ObjectDelete(0,LINE_LIMIT_SL+"_L");
   ObjectDelete(0,LINE_LIMIT_SL+"_T");
   ObjectDelete(0,LINE_LIMIT_TP+"_L");
   ObjectDelete(0,LINE_LIMIT_TP+"_T");
   ChartRedraw();
}

double ReadEditPrice()
{
   string t=ObjectGetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT);
   StringTrimLeft(t); StringTrimRight(t);
   return StringToDouble(t);
}

void SyncLimitLinePrice()
{
   if(ObjectFind(0,LINE_LIMIT_NAME)<0) return;
   int si=g_PanelSymIdx;
   if(si<0||si>=g_SymCount) return;
   int    dg=(int)SymbolInfoInteger(g_Symbols[si].name,SYMBOL_DIGITS);
   double lp=NormalizeDouble(ObjectGetDouble(0,LINE_LIMIT_NAME,OBJPROP_PRICE),dg);
   if(MathAbs(lp-g_LimitPrice)>SymbolInfoDouble(g_Symbols[si].name,SYMBOL_POINT)*0.5&&lp>0)
   { g_LimitPrice=lp;
     if(ObjectFind(0,EDIT_PRICE_NAME)>=0)
        ObjectSetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT,DoubleToString(g_LimitPrice,dg));
     UpdateLimitLine();
     GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice); }
}

//+------------------------------------------------------------------+
//| PANEL MULTI-PAR (TESTER VISUAL + GRÁFICO REAL)                   |
//|                                                                  |
//| Panel organizado y legible con una fila por par: bias H1/M3,     |
//| zona, limit congelada, posición abierta (lotes/P&L), nivel de    |
//| riesgo, lote y el PRÓXIMO PASO de la estrategia. Debajo, un      |
//| mini-gráfico por par con sus líneas: L1/L2 del TF de entrada,    |
//| rango H1, 50% H1, entrada limit congelada y ENTRADA/SL/TP de la  |
//| posición. Se dibuja igual en el Strategy Tester (modo visual) y  |
//| en el gráfico real, sobre un único bitmap (rápido, sin parpadeo).|
//+------------------------------------------------------------------+
#define MP_CANVAS_NAME  "MPNL_CANVAS"
#define MP_PSLINE_PFX   "PSLN_"
#define MP_MAX_ROWS     10
#define MP_MAX_CHARTS   6
#define MP_ROW_H        15
#define MP_BOX_H        104

CCanvas  g_MP;
bool     g_MPReady       = false;
int      g_MPW           = 0;
int      g_MPH           = 0;
uint     g_MPLastUpd     = 0;
uint     g_MPLastPosLine = 0;
int      g_MPLastTrades  = -1;

//--- ¿hay gráfico visible donde dibujar? (tester: solo modo visual)
bool IsVisual()
{ return(!IsTester() || MQLInfoInteger(MQL_VISUAL_MODE)==1); }

uint MPC(color c)
{ return(ColorToARGB(c,255)); }

//--- nombre corto del TF (H1, M3, ...)
string MPTFName(ENUM_TIMEFRAMES tf)
{
   string s=EnumToString(tf);
   StringReplace(s,"PERIOD_","");
   return(s);
}

//+------------------------------------------------------------------+
//| Snapshot legible por símbolo (una fila del panel)                |
//+------------------------------------------------------------------+
struct MPSnapshot
{
   int    si;
   string sym;
   int    dg;
   double bid;
   string h1Txt, m3Txt;
   color  h1Clr, m3Clr;
   bool   zBuy, zSell;
   bool   hasLim;  double limPrice; int limDir;
   bool   hasPos;  double posLots, posPL, posEntry; int posDir;
   int    cr, cv;
   double lot;
   bool   trail, paused;
   string state;
   color  stateClr;
   int    prio;    // 3=posición · 2=limit · 1=esperando · 0=resto
};

void MPFillSnapshot(int si,MPSnapshot &s)
{
   s.si=si;
   s.sym=g_Symbols[si].name;
   s.dg =(int)SymbolInfoInteger(s.sym,SYMBOL_DIGITS);
   s.bid=SymbolInfoDouble(s.sym,SYMBOL_BID);

   s.h1Txt=(g_SysState[si].SE_H1.Bias==BIAS_BULLISH)?"ALC":
           (g_SysState[si].SE_H1.Bias==BIAS_BEARISH)?"BAJ":"--";
   s.h1Clr=(g_SysState[si].SE_H1.Bias==BIAS_BULLISH)?clrLimeGreen:
           (g_SysState[si].SE_H1.Bias==BIAS_BEARISH)?clrTomato:clrGray;
   s.m3Txt=(g_SysState[si].SE_M3.Bias==BIAS_BULLISH)?"ALC":
           (g_SysState[si].SE_M3.Bias==BIAS_BEARISH)?"BAJ":"--";
   s.m3Clr=(g_SysState[si].SE_M3.Bias==BIAS_BULLISH)?clrLimeGreen:
           (g_SysState[si].SE_M3.Bias==BIAS_BEARISH)?clrTomato:clrGray;

   s.zBuy =g_SysState[si].confArmedBuy;
   s.zSell=g_SysState[si].confArmedSell;

   //--- Solo mostrar órdenes pendientes que existen realmente en la cuenta.
   //    Las limits virtuales no son operaciones de cuenta.
   s.hasLim=false; s.limPrice=0.0; s.limDir=0;
   {
      for(int i=OrdersTotal()-1;i>=0;i--)
      { ulong ot=OrderGetTicket(i); if(ot==0) continue;
        if(OrderGetString(ORDER_SYMBOL)!=s.sym) continue;
        if(!IsAnyMagic((long)OrderGetInteger(ORDER_MAGIC))) continue;
        long ty=OrderGetInteger(ORDER_TYPE);
        if(ty!=ORDER_TYPE_BUY_LIMIT &&ty!=ORDER_TYPE_SELL_LIMIT &&
           ty!=ORDER_TYPE_BUY_STOP &&ty!=ORDER_TYPE_SELL_STOP) continue;
        s.hasLim=true; s.limPrice=OrderGetDouble(ORDER_PRICE_OPEN);
        s.limDir=(ty==ORDER_TYPE_BUY_LIMIT||ty==ORDER_TYPE_BUY_STOP)?1:-1;
        break; }
   }

   //--- posición abierta (agregada: puede haber split de lotes)
   s.hasPos=false; s.posLots=0.0; s.posPL=0.0; s.posEntry=0.0; s.posDir=0;
   for(int k=0;k<g_TradeCount;k++)
   { if(g_Trades[k].symbolIdx!=si) continue;
     s.hasPos=true; s.posLots+=g_Trades[k].lots; s.posPL+=g_Trades[k].profit;
     s.posEntry=g_Trades[k].openPrice;
     s.posDir=(g_Trades[k].orderType==POSITION_TYPE_BUY)?1:-1; }

   int al=g_SysState[si].activeLiveStrategy;
   s.cr=PairLevel(si);
   s.cv=(al>=0)?g_SysState[si].strategies[al].CV:1;
   s.lot=GetPairLot(si);
   s.trail=IsTrailingActive(si,al);
   s.paused=(g_CircuitBreakerOn||
             g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused);

   //--- estado legible: qué está pasando / qué falta
   if(s.hasPos)
   { s.state="POSICIÓN ABIERTA"; s.stateClr=clrLimeGreen; s.prio=3; }
   else if(s.hasLim)
   { s.state=StringFormat("LIMIT %s %s",(s.limDir>0?"B":"S"),
                          DoubleToString(s.limPrice,s.dg));
     s.stateClr=(s.limDir>0)?clrLime:clrOrangeRed; s.prio=2; }
   else if(g_SysState[si].confVPendBuy)
   { s.state=StringFormat("LIMIT VIRTUAL B %s",
                          DoubleToString(g_SysState[si].confVPendBuyPrice,s.dg));
     s.stateClr=clrLime; s.prio=2; }
   else if(g_SysState[si].confVPendSell)
   { s.state=StringFormat("LIMIT VIRTUAL S %s",
                          DoubleToString(g_SysState[si].confVPendSellPrice,s.dg));
     s.stateClr=clrOrangeRed; s.prio=2; }
   else if(g_SysState[si].confWaitBuy)
   { s.state=StringFormat("50%% CONGELADO %s · ESPERA PRECIO",
                          DoubleToString(g_SysState[si].confEntryBuy,s.dg));
     s.stateClr=clrYellow; s.prio=1; }
   else if(g_SysState[si].confWaitSell)
   { s.state=StringFormat("50%% CONGELADO %s · ESPERA PRECIO",
                          DoubleToString(g_SysState[si].confEntrySell,s.dg));
     s.stateClr=clrYellow; s.prio=1; }
   else if(s.zBuy)
   { s.state=(g_SysState[si].SE_H1.Bias==BIAS_BULLISH)?"ZONA C ✓ CHoCH M3"
                                                       :"ZONA C ✓ H1 NO ALCISTA";
     s.stateClr=clrYellow; s.prio=1; }
   else if(s.zSell)
   { s.state=(g_SysState[si].SE_H1.Bias==BIAS_BEARISH)?"ZONA V ✓ CHoCH M3"
                                                       :"ZONA V ✓ H1 NO BAJISTA";
     s.stateClr=clrYellow; s.prio=1; }
   else if(s.paused)
   { s.state="PAUSA (CIRCUIT BREAKER)"; s.stateClr=clrTomato; s.prio=0; }
   else
   { s.state="FUERA DE ZONA"; s.stateClr=clrSilver; s.prio=0; }
}

//+------------------------------------------------------------------+
//| Helpers de dibujo sobre el canvas                                |
//+------------------------------------------------------------------+
//--- tamaño en "puntos" como los OBJ_LABEL del panel → décimas negativas
void MPText(int x,int y,string t,color c,bool bold=false,int size=8)
{
   g_MP.FontSet("Consolas",-size*10,bold?FW_BOLD:0);
   g_MP.TextOut(x,y,t,MPC(c));
}
int MPTextW(string t,bool bold=false,int size=8)
{
   g_MP.FontSet("Consolas",-size*10,bold?FW_BOLD:0);
   return(g_MP.TextWidth(t));
}
void MPTextR(int xRight,int y,string t,color c,bool bold=false,int size=8)
{ MPText(xRight-MPTextW(t,bold,size),y,t,c,bold,size); }

void MPRect(int x,int y,int w,int h,color c)
{ g_MP.FillRectangle(x,y,x+w-1,y+h-1,MPC(c)); }
void MPFrame(int x,int y,int w,int h,color c)
{ g_MP.Rectangle(x,y,x+w-1,y+h-1,MPC(c)); }
void MPSeg(int x1,int x2,int y,color c)
{ if(x2<x1) return; g_MP.Line(x1,y,x2,y,MPC(c)); }
void MPDash(int x1,int x2,int y,color c,int on,int off)
{
   for(int x=x1;x<=x2;x+=on+off)
   { int xe=MathMin(x2,x+on-1);
     for(int xx=x;xx<=xe;xx++) g_MP.PixelSet(xx,y,MPC(c)); }
}
void MPDot(int x,int y,color c,int r=2)
{ g_MP.FillRectangle(x-r,y-r,x+r,y+r,MPC(c)); }

//--- añade un nivel al listado de líneas del mini-gráfico (si está cerca)
int MPAddLvl(double &lv[],color &lc[],int &ls[],string &ln[],
             int nl,double p,color c,int st,string nm,
             double extLo,double extHi)
{
   if(p>0.0 && p>=extLo && p<=extHi && nl<16)
   { lv[nl]=p; lc[nl]=c; ls[nl]=st; ln[nl]=nm; nl++; }
   return(nl);
}

//+------------------------------------------------------------------+
//| Mini-gráfico de un par con sus líneas                            |
//+------------------------------------------------------------------+
void MPDrawMini(int x,int y,int w,int h,int si,MPSnapshot &s)
{
   MPRect(x,y,w,h,C'13,15,25');
   MPFrame(x,y,w,h,C'55,65,110');

   ENUM_TIMEFRAMES tf=InpUseConfluencia?InpConfTFEntrada:PERIOD_CURRENT;
   double cArr[];
   int nb=MathMax(16,MathMin(240,InpMPBars));
   int n=CopyClose(s.sym,tf,0,nb,cArr);
   if(n<8) n=CopyClose(s.sym,PERIOD_CURRENT,0,nb,cArr);
   if(n<8)
   { MPText(x+8,y+8,"SIN DATOS",clrGray,true,9); return; }

   //--- posición/limit de este par (para dibujar sus niveles)
   double ePX=0,eSL=0,eTP=0;
   for(int k=0;k<g_TradeCount;k++)
   { if(g_Trades[k].symbolIdx!=si) continue;
     ePX=g_Trades[k].openPrice; eSL=g_Trades[k].sl; eTP=g_Trades[k].tp; }

   //--- rango de la serie
   double hi=-DBL_MAX, lo=DBL_MAX;
   for(int i=0;i<n;i++)
   { if(cArr[i]>hi) hi=cArr[i]; if(cArr[i]<lo) lo=cArr[i]; }
   double span=(hi-lo); if(span<=0.0) span=MathMax(hi*0.0005,_Point);
   double extLo=lo-span*1.6, extHi=hi+span*1.6;

   //--- niveles: 0 sólida · 1 discontinua · 2 punteada · 3 raya-punto
   double lv[16]; color lc[16]; int ls[16]; string ln[16]; int nl=0;
   if(g_SysState[si].SE_M3.Valid)
   {
      nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_M3.L1,clrDeepSkyBlue,0,"L1",extLo,extHi);
      nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_M3.L2,clrDeepSkyBlue,0,"L2",extLo,extHi);
      if(g_SysState[si].SE_M3.L3L4_Active)
      { nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_M3.L3,clrMagenta,1,"L3",extLo,extHi);
        nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_M3.L4,clrOrangeRed,1,"L4",extLo,extHi); }
   }
   if(g_SysState[si].SE_H1.Valid)
   {
      nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_H1.L1,clrOrange,1,"H1L1",extLo,extHi);
      nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_H1.L2,clrOrange,1,"H1L2",extLo,extHi);
      if(g_SysState[si].SE_H1.L3L4_Active)
      { nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_H1.L3,clrMagenta,1,"H1L3",extLo,extHi);
        nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_H1.L4,clrOrangeRed,1,"H1L4",extLo,extHi); }
      nl=MPAddLvl(lv,lc,ls,ln,nl,g_SysState[si].SE_H1.EQ,clrGold,2,"50%",extLo,extHi);
   }
   if(s.hasLim)
      nl=MPAddLvl(lv,lc,ls,ln,nl,s.limPrice,(s.limDir>0)?clrLime:clrRed,3,
                  (s.limDir>0)?"LIM B":"LIM S",extLo,extHi);
   if(s.hasPos)
   {
      nl=MPAddLvl(lv,lc,ls,ln,nl,ePX,clrWhite,3,"ENTRADA",extLo,extHi);
      nl=MPAddLvl(lv,lc,ls,ln,nl,eSL,clrOrangeRed,2,"SL",extLo,extHi);
      nl=MPAddLvl(lv,lc,ls,ln,nl,eTP,clrSpringGreen,2,"TP",extLo,extHi);
   }

   //--- escala final (serie + niveles incluidos, con margen)
   double hiF=hi+span*0.15, loF=lo-span*0.15;
   for(int j=0;j<nl;j++)
   { if(lv[j]>hiF) hiF=lv[j]; if(lv[j]<loF) loF=lv[j]; }
   double rng=(hiF-loF); if(rng<=0.0) rng=span;
   hiF+=rng*0.06; loF-=rng*0.06; rng=hiF-loF;

   int px0=x+6, px1=x+w-46, py0=y+18, py1=y+h-10;

   //--- niveles
   for(int j=0;j<nl;j++)
   {
      int yy=(int)MathRound(py1-(lv[j]-loF)/rng*(py1-py0));
      if(yy<py0||yy>py1) continue;
      switch(ls[j])
      { case 0:  MPSeg(px0,px1,yy,lc[j]);               break;
        case 1:  MPDash(px0,px1,yy,lc[j],5,4);          break;
        case 2:  MPDash(px0,px1,yy,lc[j],1,2);          break;
        default: MPDash(px0,px1,yy,lc[j],7,3);          break; }
      MPText(px1+4,yy-4,ln[j],lc[j],false,7);
   }

   //--- escala mín/máx
   MPText(px0,py0+1,DoubleToString(hiF,s.dg),C'110,110,130',false,7);
   MPText(px0,py1-8,DoubleToString(loF,s.dg),C'110,110,130',false,7);

   //--- serie de precios
   int prevx=px0, prevy=(int)MathRound(py1-(cArr[0]-loF)/rng*(py1-py0));
   for(int i=1;i<n;i++)
   { int xx=(int)MathRound(px0+(double)i/(n-1)*(px1-px0));
     int yy=(int)MathRound(py1-(cArr[i]-loF)/rng*(py1-py0));
     g_MP.Line(prevx,prevy,xx,yy,MPC(clrDeepSkyBlue));
     prevx=xx; prevy=yy; }
   MPDot(px1,prevy,clrYellow,2);

   //--- cabecera del box: par · TF · precio + chip de estado
   double cur=(s.bid>0)?s.bid:cArr[n-1];
   string ttl=s.sym+"  "+MPTFName(tf);
   MPText(x+6,y+3,ttl,clrGold,true,9);
   string chip;
   color  chipClr;
   if(s.hasPos)
   { chip=StringFormat("%s %s  %+.2f",(s.posDir>0)?"▲":"▼",
                       DoubleToString(s.posLots,2),s.posPL);
     chipClr=(s.posPL>=0)?clrLimeGreen:clrTomato; }
   else if(s.hasLim)
   { chip=(s.limDir>0)?"LIMIT B":"LIMIT S"; chipClr=(s.limDir>0)?clrLime:clrOrangeRed; }
   else { chip="---"; chipClr=clrGray; }
   MPTextR(x+w-6,y+4,chip,chipClr,true,9);
   MPText(x+6+MPTextW(ttl,true,9)+8,y+4,DoubleToString(cur,s.dg),clrWhite,false,8);
}

//+------------------------------------------------------------------+
//| Cabecera, resumen de cuenta, tabla y leyenda                     |
//+------------------------------------------------------------------+
void MPDrawHeader(int x,int y,int w,int nOpen,int nLim)
{
   MPRect(x,y,w,22,C'22,22,58');
   MPFrame(x,y,w,22,C'70,80,150');
   string mode=IsTester()?"TESTER VISUAL":"REAL";
   string t=StringFormat("MULTI-PAR · %s · %d pares · %d abiertos · %d limits",
                         mode,g_SymCount,nOpen,nLim);
   MPText(x+8,y+6,t,clrGold,true,9);
   MPTextR(x+w-8,y+7,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES),
           C'150,150,170',false,8);
}

void MPDrawAccount(int x,int y,int w)
{
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double eq =AccountInfoDouble(ACCOUNT_EQUITY);
   double fPL=eq-bal;
   double lp =GetDailyLossPct();

   MPRect(x,y,w,24,C'15,17,27');
   int cw=w/4;
   string cap[4]={"BALANCE","EQUIDAD","P&L FLOTANTE","CB DÍA"};
   string val[4];
   val[0]=DoubleToString(bal,2);
   val[1]=DoubleToString(eq,2);
   val[2]=StringFormat("%s%.2f",(fPL>=0)?"+":"",fPL);
   val[3]=(g_CircuitBreakerOn)?"BLOQUEADO":
          StringFormat("%.2f%% / %.1f%%",lp,InpMaxDailyLossPct);
   color vc[4];
   vc[0]=clrWhite;
   vc[1]=(eq>=bal)?clrLimeGreen:clrTomato;
   vc[2]=(fPL>=0)?clrLimeGreen:clrTomato;
   vc[3]=g_CircuitBreakerOn?clrTomato:
          (lp>=InpMaxDailyLossPct*0.8)?clrOrange:
          (lp>=InpMaxDailyLossPct*0.5)?clrYellow:C'120,180,120';
   for(int i=0;i<4;i++)
   { MPText(x+i*cw+8,y+3,cap[i],C'130,130,150',false,7);
     MPText(x+i*cw+8,y+11,val[i],vc[i],true,9);
     if(i>0) g_MP.Line(x+i*cw,y+3,x+i*cw,y+20,MPC(C'45,50,75')); }
}

//--- columnas de la tabla (offsets X dentro del panel, ancho 620)
#define MPC_X_PAR   8
#define MPC_X_H1   92
#define MPC_X_M3  122
#define MPC_X_ZONA 152
#define MPC_X_LIM  188
#define MPC_X_POS  236
#define MPC_X_NIV  350
#define MPC_X_LOT  390
#define MPC_X_PNL  430
#define MPC_X_EST  470

void MPDrawTable(int x,int y,int w,MPSnapshot &snaps[],int &ord[],int nShown)
{
   //--- cabecera de columnas
   MPRect(x,y,w,14,C'26,26,50');
   MPText(x+MPC_X_PAR ,y+3,"PAR",clrSilver,true,8);
   MPText(x+MPC_X_H1  ,y+3,"H1",clrSilver,true,8);
   MPText(x+MPC_X_M3  ,y+3,"M3",clrSilver,true,8);
   MPText(x+MPC_X_ZONA,y+3,"ZONA",clrSilver,true,8);
   MPText(x+MPC_X_LIM ,y+3,"LÍMITE",clrSilver,true,8);
   MPText(x+MPC_X_POS ,y+3,"POSICIÓN",clrSilver,true,8);
   MPText(x+MPC_X_NIV ,y+3,"NTV",clrSilver,true,8);
   MPText(x+MPC_X_LOT ,y+3,"LOT",clrSilver,true,8);
   MPText(x+MPC_X_PNL ,y+3,"P&L",clrSilver,true,8);
   MPText(x+MPC_X_EST ,y+3,"ESTADO / PRÓXIMO PASO",clrSilver,true,8);
   y+=14;

   for(int r=0;r<nShown;r++)
   {
      int si=ord[r];
      MPSnapshot s=snaps[si];
      int ry=y+r*MP_ROW_H;

      color bg=s.hasPos?C'8,52,30':
              s.hasLim?C'10,34,64':
              s.paused?C'55,18,18':((r%2)!=0?C'20,20,32':C'15,15,25');
      MPRect(x,ry,w,MP_ROW_H,bg);
      g_MP.Line(x,ry+MP_ROW_H-1,x+w-1,ry+MP_ROW_H-1,MPC(C'35,35,55'));

      MPText(x+MPC_X_PAR ,ry+3,s.sym,s.hasPos?clrLime:clrGold,true,8);
      MPText(x+MPC_X_H1  ,ry+3,s.h1Txt,s.h1Clr,false,8);
      MPText(x+MPC_X_M3  ,ry+3,s.m3Txt,s.m3Clr,false,8);
      string zs=(s.zBuy&&s.zSell)?"C+V":s.zBuy?"C":s.zSell?"V":"-";
      MPText(x+MPC_X_ZONA,ry+3,zs,s.zBuy?clrLime:(s.zSell?clrTomato:clrGray),false,8);
      MPText(x+MPC_X_LIM ,ry+3,s.hasLim?StringFormat("%s %s",(s.limDir>0)?"B":"S",
                                  DoubleToString(s.limPrice,s.dg)):"-",
             s.hasLim?((s.limDir>0)?clrLime:clrOrangeRed):clrGray,false,8);
      MPText(x+MPC_X_POS ,ry+3,s.hasPos?StringFormat("%s %s %s",
                                  (s.posDir>0)?"▲":"▼",DoubleToString(s.posLots,2),
                                  DoubleToString(s.posEntry,s.dg)):"-",
             s.hasPos?clrWhite:clrGray,false,8);
      MPText(x+MPC_X_NIV ,ry+2,StringFormat("%d",s.cr),clrAqua,true,10);
      MPText(x+MPC_X_LOT ,ry+3,DoubleToString(s.lot,2),clrDodgerBlue,false,8);
      MPText(x+MPC_X_PNL ,ry+3,s.hasPos?StringFormat("%s%.2f",(s.posPL>=0)?"+":"",s.posPL):"-",
             s.hasPos?((s.posPL>=0)?clrLimeGreen:clrTomato):clrGray,false,8);
      MPText(x+MPC_X_EST ,ry+3,s.state,s.stateClr,false,8);
   }

   if(g_SymCount>nShown)
      MPText(x+MPC_X_PAR,y+nShown*MP_ROW_H+2,
             StringFormat("… y %d pares más (ordenados por actividad)",g_SymCount-nShown),
             C'130,130,150',false,8);
}

void MPDrawLegend(int x,int y)
{
   int lx=x+8;
   MPSeg(lx,lx+12,y+6,clrDeepSkyBlue);            lx+=16;
   MPText(lx,y+2,"precio",clrSilver,false,7);      lx+=MPTextW("precio",false,7)+12;
   MPSeg(lx,lx+12,y+6,clrOrange);                  lx+=16;
   MPText(lx,y+2,"H1 L1/L2",clrSilver,false,7);    lx+=MPTextW("H1 L1/L2",false,7)+12;
   MPDash(lx,lx+12,y+6,clrGold,1,2);               lx+=16;
   MPText(lx,y+2,"50% H1",clrSilver,false,7);      lx+=MPTextW("50% H1",false,7)+12;
   MPDash(lx,lx+12,y+6,clrLime,7,3);               lx+=16;
   MPText(lx,y+2,"limit",clrSilver,false,7);       lx+=MPTextW("limit",false,7)+12;
   MPDash(lx,lx+12,y+6,clrWhite,7,3);              lx+=16;
   MPText(lx,y+2,"entrada",clrSilver,false,7);     lx+=MPTextW("entrada",false,7)+12;
   MPDash(lx,lx+12,y+6,clrOrangeRed,1,2);          lx+=16;
   MPText(lx,y+2,"SL",clrSilver,false,7);          lx+=MPTextW("SL",false,7)+12;
   MPDash(lx,lx+12,y+6,clrSpringGreen,1,2);        lx+=16;
   MPText(lx,y+2,"TP",clrSilver,false,7);
}

//+------------------------------------------------------------------+
//| SECCIÓN "VIRTUAL → LIVE": estado por par y por estrategia        |
//|                                                                  |
//| Muestra, para cada par y cada estrategia, en qué punto va la     |
//| fase virtual (pérdidas completadas de X, CV, cuánto falta para   |
//| activar LIVE), el nivel/lote que tomará y el estado (SIM,        |
//| ESPERA, ★ LIVE, PAUSA, OFF).                                     |
//+------------------------------------------------------------------+
#define MP_VROW_H 15

int MPVirtScore(int si,int thr)
{
   if(g_SysState[si].hasLive) return 3000;
   if(g_CircuitBreakerOn)     return 0;
   int best=0;
   for(int st=0;st<STRAT_COUNT;st++)
   { if(!g_SysState[si].strategies[st].enabled) continue;
     if(g_SysState[si].strategies[st].cbPaused) continue;
     int cv=g_SysState[si].strategies[st].CV;
     if(cv>=thr) return 2000+MathMin(cv,999);
     if(cv>best) best=cv; }
   return best;
}

//--- una estrategia de un par (columna del estado virtual) ---------
void MPVirtStratLine(int x,int y,int w,int si,int st,int thr)
{
   StrategyState S=g_SysState[si].strategies[st];   // copia de solo lectura
   MPText(x,y+4,S.name,C'150,160,190',true,7);

   int bx=x+42, bw=MathMin(96,w-42-108);
   if(bw<20) bw=20;
   MPRect(bx,y+2,bw,11,C'28,32,50');
   MPFrame(bx,y+2,bw,11,C'60,66,100');

   double frac; color fc;
   if(!S.enabled)     { frac=0.0; fc=C'60,60,70'; }
   else if(S.cbPaused){ frac=0.0; fc=C'120,40,40'; }
   else if(S.isLive)  { frac=1.0; fc=clrLimeGreen; }
   else
   { int losses=MathMax(0,S.CV-1);
     frac=MathMin((double)losses/(double)MathMax(1,InpXActivacion),1.0);
     fc=(S.CV>=thr)?clrYellow:
        (frac>=0.75)?clrOrange:
        (frac>=0.5)?clrDodgerBlue:C'60,80,150'; }
   int fw=(int)MathRound(bw*frac);
   if(fw>0) MPRect(bx,y+2,fw,11,fc);
   // marcas de las X pérdidas objetivo
   for(int q=1;q<MathMax(1,InpXActivacion);q++)
   { int sx=bx+(int)MathRound((double)bw*q/MathMax(1,InpXActivacion));
     g_MP.Line(sx,y+2,sx,y+12,MPC(C'80,90,130')); }

   string txt; color tc;
   if(!S.enabled)      { txt="OFF";      tc=C'95,95,110'; }
   else if(S.cbPaused) { txt="PAUSA";    tc=clrTomato; }
   else if(S.isLive)
   { if(S.liveLogicLevel>=5) txt="★ LIVE · 1:2 (lóg.N5)";
     else if(S.liveLogicLevel>0) txt=StringFormat("★ LIVE · lóg.N%d",S.liveLogicLevel);
     else txt="★ LIVE";
     tc=clrLimeGreen; }
   else if(S.CV>=thr)  { txt="ESPERA";   tc=clrYellow; }
   else
   { int losses=MathMax(0,S.CV-1);
     int falta=MathMax(0,thr-S.CV);
     txt=StringFormat("pérd %d/%d · falta %d",
                      losses,MathMax(1,InpXActivacion),falta);
     if(S.virtualActive) txt+=" · vOPEN";
     bool wait50=(st==STRAT_S2)?
        (g_SysState[si].s2WaitBuy || g_SysState[si].s2WaitSell):
        (g_SysState[si].confWaitBuy || g_SysState[si].confWaitSell);
     if(wait50) txt+=" · ESPERA PRECIO (50%)";
     tc=(falta<=1)?clrOrange:(falta<=2)?clrDodgerBlue:C'150,170,210'; }
   MPText(x+42+bw+6,y+4,txt,tc,false,7);
}

//--- cabecera + filas del estado virtual (devuelve la altura) ------
int MPDrawVirtualState(int x,int y,int w)
{
   int thr=InpXActivacion+1;

   //--- orden: pares con LIVE primero, después los más cerca de LIVE
   int vo[MAX_SYMBOLS]; int nAct=0;
   for(int i=0;i<g_SymCount;i++)
      if(g_Symbols[i].active) vo[nAct++]=i;
   for(int i=1;i<nAct;i++)
   { int key=vo[i]; int kv=MPVirtScore(key,thr); int j=i-1;
     while(j>=0 && MPVirtScore(vo[j],thr)<kv){ vo[j+1]=vo[j]; j--; }
     vo[j+1]=key; }
   int rows=MathMin(nAct,MP_MAX_ROWS);

   MPRect(x,y,w,16,C'24,30,54');
   MPFrame(x,y,w,16,C'70,85,150');
   string t=StringFormat("VIRTUAL → LIVE  ·  X=%d → LIVE tras %d pérdidas (op.%d)",
                         InpXActivacion,InpXActivacion,InpXActivacion+1);
   MPText(x+8,y+4,t,clrGold,true,8);
   MPTextR(x+w-8,y+4,StringFormat("%d pares",rows),C'150,160,190',false,8);
   int h=16;

   int rows2=InpUseStrat2?2:1;          // líneas por par: E1 y S2
   int vRowH=MP_VROW_H*rows2;
   for(int r=0;r<rows;r++)
   { int si=vo[r];
     bool hasLive=g_SysState[si].hasLive;
     int ry=y+h+r*vRowH;
     color bg=hasLive?C'10,34,18':
              g_SysState[si].strategies[STRAT_CONFLUENCIA].isLive?C'10,34,18':
              g_SysState[si].strategies[STRAT_CONFLUENCIA].cbPaused?C'55,18,18':
              ((r%2)!=0?C'19,21,33':C'15,17,27');
     MPRect(x,ry,w,vRowH,bg);
     g_MP.Line(x,ry+vRowH-1,x+w-1,ry+vRowH-1,MPC(C'35,35,55'));
     MPText(x+8,ry+4,g_Symbols[si].name,clrGold,true,8);
     MPVirtStratLine(x+88,ry,w-96,si,STRAT_CONFLUENCIA,thr);
     if(InpUseStrat2)
        MPVirtStratLine(x+88,ry+MP_VROW_H,w-96,si,STRAT_S2,thr);
   }
   h+=rows*vRowH;
   if(nAct>rows)
   { MPText(x+8,y+h+2,
            StringFormat("… y %d pares más (tabla de arriba y pestaña ESTRAT)",nAct-rows),
            C'130,130,150',false,8);
     h+=13; }
   return h;
}

//+------------------------------------------------------------------+
//| Actualización del panel (con throttle para no frenar el tester)  |
//+------------------------------------------------------------------+
void MultiPanelUpdate(bool force=false)
{
   if(!InpShowMultiPanel || !IsVisual()) return;

   uint now=GetTickCount();
   if(!force && g_MPReady && now-g_MPLastUpd<250) return;
   g_MPLastUpd=now;

   //--- snapshot de todos los pares + orden por actividad
   MPSnapshot snaps[MAX_SYMBOLS];
   int ord[MAX_SYMBOLS];
   int nOpen=0, nLim=0;
   for(int i=0;i<g_SymCount;i++)
   { if(!g_Symbols[i].active){ ord[i]=-1; continue; }
      MPFillSnapshot(i,snaps[i]);
      if(snaps[i].hasPos) nOpen++;
      if(snaps[i].hasLim) nLim++; }
   int nAct=0;
   for(int i=0;i<g_SymCount;i++)
      if(g_Symbols[i].active){ ord[nAct++]=i; }
   for(int i=1;i<nAct;i++)                      // inserción estable por prioridad
   { int key=ord[i]; int kv=snaps[key].prio; int j=i-1;
     while(j>=0 && snaps[ord[j]].prio<kv){ ord[j+1]=ord[j]; j--; }
     ord[j+1]=key; }

   //--- tamaño del panel
   int rows=MathMin(nAct,MP_MAX_ROWS);
   int chartSlots=0;
   if(InpShowMiniCharts)
   { chartSlots=(InpMPChartsAll)?nAct:(nOpen+nLim);
      if(chartSlots==0) chartSlots=MathMin(1,nAct);
      chartSlots=MathMin(chartSlots,MP_MAX_CHARTS); }
   int chartRows=(chartSlots+1)/2;
   int W=700;
   int H=22+24+14+rows*MP_ROW_H;
   if(nAct>rows) H+=13;
   //--- sección estado virtual (por par / por estrategia)
   int vRows=MathMin(nAct,MP_MAX_ROWS);
   int vRows2=InpUseStrat2?2:1;
   H+=6+16+vRows*MP_VROW_H*vRows2;
   if(nAct>vRows) H+=13;
   if(chartRows>0) H+=8+chartRows*MP_BOX_H+(chartRows-1)*6;
   H+=20;

   //--- posición (auto: esquina superior derecha)
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS,0);
   int ch=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS,0);
   if(cw<=0) cw=800;
   if(ch<=0) ch=600;
   int px=(InpMPX>0)?InpMPX:MathMax(0,cw-W-12);
   int py=MathMin(InpMPY,MathMax(0,ch-H-6));

   //--- crear/recrear bitmap si cambia el tamaño
   if(!g_MPReady || g_MPW!=W || g_MPH!=H)
   {
      if(g_MPReady){ g_MP.Destroy(); g_MPReady=false; }
      ObjectDelete(0,MP_CANVAS_NAME);
      if(!g_MP.CreateBitmapLabel(MP_CANVAS_NAME,px,py,W,H,COLOR_FORMAT_XRGB_NOALPHA))
         return;
      g_MPReady=true; g_MPW=W; g_MPH=H;
      ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_HIDDEN,true);
      ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_BACK,false);
      ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_ZORDER,10);
   }
   ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_XDISTANCE,px);
   ObjectSetInteger(0,MP_CANVAS_NAME,OBJPROP_YDISTANCE,py);

   //--- dibujo
   g_MP.Erase(MPC(C'10,10,18'));
   int y=0;
   MPDrawHeader(0,y,W,nOpen,nLim);  y+=22;
   MPDrawAccount(0,y,W);            y+=24;
   MPDrawTable(0,y,W,snaps,ord,rows);
   y+=14+rows*MP_ROW_H;
   if(nAct>rows) y+=13;

   //--- estado virtual: cuánto falta por par y por estrategia
   y+=6;
   y+=MPDrawVirtualState(0,y,W);

   if(chartSlots>0)
   {
      y+=8;
      int bw=(W-18)/2, drawn=0;
      //--- 1º: pares con posición o limit
      for(int i=0;i<nAct && drawn<chartSlots;i++)
      { int si=ord[i];
         if(!snaps[si].hasPos && !snaps[si].hasLim) continue;
         MPDrawMini(6+(drawn%2)*(bw+6),y+(drawn/2)*(MP_BOX_H+6),bw,MP_BOX_H,si,snaps[si]);
         drawn++; }
      //--- 2º: si no hay nada abierto, mostrar el símbolo del gráfico
      if(!InpMPChartsAll && drawn==0 && chartSlots>0)
      {
         int cs=-1;
         for(int i=0;i<nAct;i++)
            if(g_Symbols[ord[i]].name==_Symbol){ cs=ord[i]; break; }
         if(cs<0 && nAct>0) cs=ord[0];
         if(cs>=0 && snaps[cs].sym!="")
         { MPDrawMini(6,y,bw,MP_BOX_H,cs,snaps[cs]); drawn++; }
      }
      //--- 3º: rellenar el resto de huecos (solo con InpMPChartsAll)
      for(int i=0;i<nAct && drawn<chartSlots;i++)
      { int si=ord[i];
         if(snaps[si].hasPos || snaps[si].hasLim) continue;
         if(!InpMPChartsAll) break;
         MPDrawMini(6+(drawn%2)*(bw+6),y+(drawn/2)*(MP_BOX_H+6),bw,MP_BOX_H,si,snaps[si]);
         drawn++; }
      y+=chartRows*MP_BOX_H+(chartRows-1)*6;
   }
   MPDrawLegend(0,y+2);

   g_MP.Update(true);
   ChartRedraw();
}

void MultiPanelDestroy()
{
   if(g_MPReady){ g_MP.Destroy(); g_MPReady=false; }
   ObjectDelete(0,MP_CANVAS_NAME);
}

//+------------------------------------------------------------------+
//| LÍNEAS DE POSICIONES/LIMITS DEL SÍMBOLO DEL GRÁFICO              |
//| ENTRADA (blanca), SL (roja), TP (verde) y LIMIT (lima/rojo)      |
//| visibles en el tester visual y en el gráfico real                |
//+------------------------------------------------------------------+
void PL_HLine(string name,double price,color clr,ENUM_LINE_STYLE sty,
              int wdt,string lbl)
{
   string tn=name+"_T";
   if(price<=0.0){ ObjectDelete(0,name); ObjectDelete(0,tn); return; }
   if(ObjectFind(0,name)<0)
   { ObjectCreate(0,name,OBJ_HLINE,0,0,price);
     ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
     ObjectSetInteger(0,name,OBJPROP_BACK,true); }
   ObjectSetDouble (0,name,OBJPROP_PRICE,price);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,sty);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,wdt);
   datetime tt=iTime(_Symbol,PERIOD_CURRENT,0)
             +PeriodSeconds(PERIOD_CURRENT)*8;
   if(ObjectFind(0,tn)<0)
   { ObjectCreate(0,tn,OBJ_TEXT,0,tt,price);
     ObjectSetInteger(0,tn,OBJPROP_SELECTABLE,false);
     ObjectSetInteger(0,tn,OBJPROP_HIDDEN,true);
     ObjectSetString (0,tn,OBJPROP_FONT,"Arial Bold");
     ObjectSetInteger(0,tn,OBJPROP_FONTSIZE,8);
     ObjectSetInteger(0,tn,OBJPROP_ANCHOR,ANCHOR_LEFT); }
   ObjectSetInteger(0,tn,OBJPROP_TIME,tt);
   ObjectSetDouble (0,tn,OBJPROP_PRICE,price);
   ObjectSetString (0,tn,OBJPROP_TEXT,lbl);
   ObjectSetInteger(0,tn,OBJPROP_COLOR,clr);
}

void RemovePositionLines()
{
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   { string n=ObjectName(0,i,0,-1);
     if(StringFind(n,MP_PSLINE_PFX)==0) ObjectDelete(0,n); }
}

void DrawPositionLines()
{
   if(!InpShowPosLines || !IsVisual()) return;

   uint now=GetTickCount();
   if(now-g_MPLastPosLine<300 && g_MPLastTrades==g_TradeCount) return;
   g_MPLastPosLine=now; g_MPLastTrades=g_TradeCount;

   string keep[]; int kn=0; ArrayResize(keep,0);
   for(int k=0;k<g_TradeCount;k++)
   {
      int si=g_Trades[k].symbolIdx;
      if(si<0 || g_Symbols[si].name!=_Symbol) continue;
      ulong  t=g_Trades[k].ticket;
      bool   isBuy=(g_Trades[k].orderType==POSITION_TYPE_BUY);
      string tag=StringFormat("#%I64u",t%100000);
      string eN=StringFormat("%sE_%I64u",MP_PSLINE_PFX,t);
      string sN=StringFormat("%sS_%I64u",MP_PSLINE_PFX,t);
      string tN=StringFormat("%sT_%I64u",MP_PSLINE_PFX,t);
      PL_HLine(eN,g_Trades[k].openPrice,clrWhite,STYLE_DASH,1,
               StringFormat("ENTRADA %s %s %s",(isBuy?"▲":"▼"),
                            DoubleToString(g_Trades[k].lots,2),tag));
      PL_HLine(sN,g_Trades[k].sl,clrRed,STYLE_DOT,1,"SL "+tag);
      PL_HLine(tN,g_Trades[k].tp,clrLime,STYLE_DOT,1,"TP "+tag);
      for(int q=0;q<3;q++)
      { string base=(q==0)?eN:(q==1)?sN:tN;
         ArrayResize(keep,kn+2); keep[kn]=base; keep[kn+1]=base+"_T"; kn+=2; }
   }
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      ulong ot=OrderGetTicket(i); if(ot==0) continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol) continue;
      if(!IsAnyMagic((long)OrderGetInteger(ORDER_MAGIC))) continue;
      long ty=OrderGetInteger(ORDER_TYPE);
      if(ty!=ORDER_TYPE_BUY_LIMIT &&ty!=ORDER_TYPE_SELL_LIMIT &&
         ty!=ORDER_TYPE_BUY_STOP &&ty!=ORDER_TYPE_SELL_STOP) continue;
      bool b=(ty==ORDER_TYPE_BUY_LIMIT||ty==ORDER_TYPE_BUY_STOP);
      string lN=StringFormat("%sL_%I64u",MP_PSLINE_PFX,ot);
      PL_HLine(lN,OrderGetDouble(ORDER_PRICE_OPEN),b?clrLime:clrOrangeRed,
               STYLE_DASHDOT,1,b?"LIMIT COMPRA":"LIMIT VENTA");
      ArrayResize(keep,kn+2); keep[kn]=lN; keep[kn+1]=lN+"_T"; kn+=2;
   }
   //--- borrar líneas de tickets que ya no existen
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   { string n=ObjectName(0,i,0,-1);
      if(StringFind(n,MP_PSLINE_PFX)!=0) continue;
      bool found=false;
      for(int j=0;j<kn;j++) if(keep[j]==n){ found=true; break; }
      if(!found) ObjectDelete(0,n); }
   ChartRedraw();
}

//--- limpia objetos sueltos de versiones anteriores
void CleanupLegacyObjects()
{
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   { string n=ObjectName(0,i,0,-1);
      if(StringFind(n,"PAIRLBL_")==0 || n=="VALIDA_SUM") ObjectDelete(0,n); }
}

//+------------------------------------------------------------------+
//| TESTER INFO                                                      |
//+------------------------------------------------------------------+
void ShowTesterInfo()
{
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double eq =AccountInfoDouble(ACCOUNT_EQUITY);
   double fPL=eq-bal;
   double lossPct=GetDailyLossPct();
   string msg="╔══════════════════════════════════════════╗\n";
   msg+="║    GESTIÓN CUANTITATIVA  v8.50           ║\n";
   msg+="╠══════════════════════════════════════════╣\n";
   msg+=StringFormat("║  Base capital : %s   Bal.máx: %.2f\n",
                     BaseDisplay(false),g_BaseMaxBalance);
   msg+=StringFormat("║  CB Diario    : %.2f%% / %.1f%%   [%s]\n",
                     lossPct,InpMaxDailyLossPct,
                     g_CircuitBreakerOn?"⛔BLOQ":"OK");
   msg+="╠══════════════════════════════════════════╣\n";
   for(int si=0;si<g_SymCount;si++)
   {
      int alive=g_SysState[si].activeLiveStrategy;
      string liveN=(alive>=0)?g_SysState[si].strategies[alive].name:"NINGUNA";
      msg+=StringFormat("║  [%s]  LIVE: %s  NIVEL par: %d  Lot: %.2f\n",
                        g_Symbols[si].name,liveN,PairLevel(si),GetPairLot(si));
      for(int st=0;st<STRAT_COUNT;st++)
      {
         if(!g_SysState[si].strategies[st].enabled) continue;
         string est=g_SysState[si].strategies[st].cbPaused?"CB-PAUSE":
                    g_SysState[si].strategies[st].isLive?"★LIVE":
                    (g_SysState[si].strategies[st].CV>=(InpXActivacion+1))?"ESPERA":"SIM";
         msg+=StringFormat("║    %-5s %-8s CV:%-3d CVmax:%-3d Lot:%.2f\n",
                           g_SysState[si].strategies[st].name,est,
                           g_SysState[si].strategies[st].CV,
                           g_SysState[si].strategies[st].CV_Max,
                           GetPairLot(si));
      }
   }
   msg+="╠══════════════════════════════════════════╣\n";
   msg+=StringFormat("║  Balance : %.2f\n",bal);
   msg+=StringFormat("║  Equidad : %.2f\n",eq);
   msg+=StringFormat("║  P&L     : %s%.2f\n",(fPL>=0)?"+":"",fPL);
   msg+="╚══════════════════════════════════════════╝";
   Comment(msg);
}

void PrintDiag()
{
   if(IsTester()) return;
   datetime now=TimeCurrent();
   if(now-g_LastDiagTime<60) return;
   g_LastDiagTime=now;
   Print("=== DIAG v8.50 === X=",InpXActivacion,
         " CB=",g_CircuitBreakerOn?"ACTIVO":"OFF",
         " Base=",BaseDisplay(false));
   for(int si=0;si<g_SymCount;si++)
   {
      int alive=g_SysState[si].activeLiveStrategy;
      Print("  [",g_Symbols[si].name,"] Live:",
            (alive>=0)?g_SysState[si].strategies[alive].name:"NONE");
      for(int st=0;st<STRAT_COUNT;st++)
      {
         if(!g_SysState[si].strategies[st].enabled) continue;
         Print("    ",g_SysState[si].strategies[st].name,
               " CV:",g_SysState[si].strategies[st].CV,
               " NIVEL par:",PairLevel(si),
               " 1:2:",IsTrailingActive(si,st)?"ON":"OFF",
               " Lot:",GetPairLot(si),
               g_SysState[si].strategies[st].cbPaused?" [CB-PAUSED]":"");
      }
   }
}

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   PNL_X=InpPanelX; PNL_Y=InpPanelY;
   g_PanelTableSize=MathMax(1,MathMin(MAX_TABLE_SIZE,InpTableSize));
   g_TradeCount=0; g_ScrollOffset=0; g_SaveCounter=0;
   g_MPLastUpd=0; g_MPLastPosLine=0; g_MPLastTrades=-1;
   CleanupLegacyObjects();
   g_ClosedCount=0; g_LastDiagTime=0;
   g_Dragging=false; g_PendingRebuild=false;
   ArrayResize(g_Trades,0); ArrayResize(g_ClosedQueue,0);

   TAB_NAMES[0]="OPERAR"; TAB_NAMES[1]="CUENTA"; TAB_NAMES[2]="POSIC.";
   TAB_NAMES[3]="CONFIG"; TAB_NAMES[4]="ESTRAT";

   InitGlobalVarKeys();
   InitRiskTable();
   LoadSymbolInputParams();

   //--- En el tester, si el símbolo del gráfico no está en InpSymbol1..20,
   //    añadirlo automáticamente para poder operar y DIBUJAR LAS LÍNEAS
   //    sobre el símbolo que se está probando (no requiere configuración).
   if(IsTester())
   {
      bool chartSymPresent=false;
      for(int s0=0;s0<g_SymCount;s0++)
         if(g_Symbols[s0].name==_Symbol){ chartSymPresent=true; break; }
      if(!chartSymPresent && g_SymCount<MAX_SYMBOLS)
      {
         SymbolSelect(_Symbol,true);
         int idx=g_SymCount;
         g_Symbols[idx].name        = _Symbol;
         g_Symbols[idx].active      = true;
         g_Symbols[idx].sl_points   = 0.0;   // usa el SL global
         g_Symbols[idx].sl_offset   = 0.0;
         g_Symbols[idx].tp_points   = 0.0;   // usa el TP global
         g_Symbols[idx].activation  = 0.0;
         g_Symbols[idx].protectedSL = 0.0;
         g_SymCount++;
         Print("TESTER: símbolo del gráfico [",_Symbol,"] añadido automáticamente.");
      }
   }

   if(g_SymCount==0)
   { Print("ERROR: No hay símbolos. Configura InpSymbol1..20");
     return INIT_FAILED; }

   for(int si=0;si<g_SymCount;si++) InitSystemState(si);

   g_BaseCapital    = InpBaseCapital;
   g_BaseMaxBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_DayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_DayStartTime   = TimeCurrent();
   g_CircuitBreakerOn=false;

   if(!IsTester()) LoadState();

   //--- Inicializar motores de líneas para poder dibujar de inmediato
   for(int si=0;si<g_SymCount;si++) UpdateStructureState(si);

   //--- Diagnóstico en el log: confirma que las líneas se calcularon
   if(IsTester() && InpShowStructureLines)
   {
      for(int si=0;si<g_SymCount;si++)
      {
         if(g_SysState[si].SE.Valid)
            Print("ESTRUCTURA [",g_Symbols[si].name,"] L1=",
                  DoubleToString(g_SysState[si].SE.L1,_Digits),
                  "  L2=",DoubleToString(g_SysState[si].SE.L2,_Digits),
                  "  L3L4=",g_SysState[si].SE.L3L4_Active?"ACTIVO":"-");
         if(InpUseConfluencia && g_SysState[si].SE_H1.Valid)
            Print("CONFL [",g_Symbols[si].name,"] H1 L1=",
                  DoubleToString(g_SysState[si].SE_H1.L1,_Digits),
                  "  L2=",DoubleToString(g_SysState[si].SE_H1.L2,_Digits),
                  "  50%=",DoubleToString(g_SysState[si].SE_H1.EQ,_Digits),
                  "  Bias=",(g_SysState[si].SE_H1.Bias==BIAS_BULLISH?"ALCISTA":
                            g_SysState[si].SE_H1.Bias==BIAS_BEARISH?"BAJISTA":"-"));
         if(InpUseConfluencia && g_SysState[si].SE_M3.Valid)
            Print("CONFL [",g_Symbols[si].name,"] M3 L1=",
                  DoubleToString(g_SysState[si].SE_M3.L1,_Digits),
                  "  L2=",DoubleToString(g_SysState[si].SE_M3.L2,_Digits),
                  "  50%=",DoubleToString(g_SysState[si].SE_M3.EQ,_Digits));
      }
      Print("ESTRUCTURA: las líneas se dibujan en el gráfico SOLO en Modo Visual del tester.");
   }

   if(g_PanelSymIdx>=g_SymCount) g_PanelSymIdx=0;

   if(InpUseConfluencia && !InpAllowConfluOrders)
      Print("CONFL: operativa pausada (InpAllowConfluOrders=false). Solo se calculan/dibujan zonas.");

   SyncAllTrades();

   if(!IsTester())
   { BuildStaticStructure(); RebuildActiveTab(); UpdateInfoBar();
     if(g_LimitPrice>0) UpdateLimitLine();
     DrawChartStructure(); }

   //--- PANEL MULTI-PAR + líneas de posiciones (tester visual y real)
   if(IsVisual())
   { MultiPanelUpdate(true); DrawPositionLines(); }

   Print("EA v8.50 | Símbolos:",g_SymCount,
         " | X=",InpXActivacion," LIVE@CV>=",InpXActivacion+1,
         " | Base=",BaseDisplay(false),
         " | CB=",DoubleToString(InpMaxDailyLossPct,1),"%");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(!IsTester()) SaveState();
   if(!IsTester()){ DeletePanel(); RemoveLimitLine(); RemoveStructureLines(); }
   MultiPanelDestroy();
   RemovePositionLines();
   Comment("");
   Print("EA v8.50 cerrado | Razón:",reason);
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   CheckDayReset();
   UpdateDynamicBase();

   int prevCount=g_TradeCount;
   WeeklyCloseAllIfDue();     // viernes: cierra posiciones del EA antes del cierre del mercado
   SyncAllTrades();
   ProcessClosedQueue();
   CheckCircuitBreaker();

   //--- Motores de líneas (estructura) por símbolo
   for(int si=0;si<g_SymCount;si++) UpdateStructureState(si);

   //--- ESTRATEGIA ÚNICA: al abrirse una posición se retiran las demás
   //    órdenes limit del par (siempre, aunque haya CB/filtro horario)
   for(int si=0;si<g_SymCount;si++) ConfluenciaManagePendings(si);
   for(int si=0;si<g_SymCount;si++) Strat2ManagePendings(si);

   if(!g_CircuitBreakerOn)
   { EnforceSLTP();
     ManageOpenPositions(); }

   // Virtuales siempre (salvo cbPaused individual)
   for(int si=0;si<g_SymCount;si++)
      for(int st=0;st<STRAT_COUNT;st++)
      { if(!g_SysState[si].strategies[st].enabled)  continue;
        if(g_SysState[si].strategies[st].cbPaused)  continue;
        if(g_SysState[si].strategies[st].isLive)    continue;
        UpdateStrategyVirtual(si,st); }

   if(!g_CircuitBreakerOn&&IsTradeTimeAllowed())
      UpdateAllStrategies();

   if(IsTester())
   {
      //--- Comment de respaldo solo si el panel MULTI-PAR está apagado
      if(!(InpShowMultiPanel&&IsVisual())) ShowTesterInfo();
      DrawChartStructure();
      MultiPanelUpdate();
      DrawPositionLines();
      ValidateAllSymbols();
      UpdateInfoBar();
   }
   else
   {
      PrintDiag();
      UpdateInfoBar();
      SyncLimitLinePrice();
      DrawChartStructure();
      MultiPanelUpdate();
      DrawPositionLines();
      ValidateAllSymbols();
      g_SaveCounter++;
      if(g_SaveCounter>=300){ SaveState(); g_SaveCounter=0; }
      if(g_TradeCount!=prevCount)
         RebuildActiveTab();
      else if(ActiveTab==TAB_CUENTA||ActiveTab==TAB_POSIC||ActiveTab==TAB_ESTRAT)
      { DeleteContentObjects();
        if(ActiveTab==TAB_CUENTA) BuildTabCuenta();
        if(ActiveTab==TAB_POSIC)  BuildTabPosiciones();
        if(ActiveTab==TAB_ESTRAT) BuildTabEstrategias();
        ChartRedraw(); }
   }
}

//+------------------------------------------------------------------+
//| OnChartEvent                                                     |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,const long &lparam,
                  const double &dparam,const string &sparam)
{
   int si=g_PanelSymIdx;
   int dg=(si>=0&&si<g_SymCount)?
          (int)SymbolInfoInteger(g_Symbols[si].name,SYMBOL_DIGITS):5;

   // ── DRAG ──────────────────────────────────────────────────────
   if(id==CHARTEVENT_MOUSE_MOVE)
   {
      if((int)lparam==1&&g_Dragging)
      {
         int mx=(int)dparam;
         int my=(int)StringToInteger(sparam);
         int nx=MathMax(0,MathMin(
                (int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS)-PNL_W,mx-g_DragOffX));
         int ny=MathMax(0,MathMin(
                (int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS)-PNL_H,my-g_DragOffY));
         if(nx!=PNL_X||ny!=PNL_Y){ PNL_X=nx; PNL_Y=ny; RebuildPanel(); }
      }
      else if((int)lparam==0) g_Dragging=false;
      return;
   }

   if(id==CHARTEVENT_OBJECT_CLICK&&sparam==DRAG_ZONE)
   {
      int mx=(int)dparam;
      int my=(int)StringToInteger(sparam);
      g_DragOffX=mx-PNL_X; g_DragOffY=my-PNL_Y;
      if(g_DragOffX<0) g_DragOffX=0;
      if(g_DragOffY<0) g_DragOffY=0;
      g_Dragging=true; return;
   }

   // ── EDIT PRECIO ───────────────────────────────────────────────
   if(id==CHARTEVENT_OBJECT_ENDEDIT&&sparam==EDIT_PRICE_NAME)
   {
      double val=ReadEditPrice();
      g_LimitPrice=(val>0)?NormalizeDouble(val,dg):0.0;
      GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice);
      UpdateLimitLine(); return;
   }

   // ── DRAG LÍNEA LÍMITE ─────────────────────────────────────────
   if(id==CHARTEVENT_OBJECT_DRAG&&sparam==LINE_LIMIT_NAME)
   {
      g_LimitPrice=NormalizeDouble(
                   ObjectGetDouble(0,LINE_LIMIT_NAME,OBJPROP_PRICE),dg);
      if(ObjectFind(0,EDIT_PRICE_NAME)>=0)
         ObjectSetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT,
                         DoubleToString(g_LimitPrice,dg));
      GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice);
      UpdateLimitLine(); return;
   }

   if(id==CHARTEVENT_OBJECT_CLICK&&sparam==LINE_LIMIT_NAME)
   { ChartRedraw(); return; }

   if(id!=CHARTEVENT_OBJECT_CLICK) return;

   if(ObjectGetInteger(0,sparam,OBJPROP_TYPE)==OBJ_BUTTON)
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
   ChartRedraw();

   // ── TABS ──────────────────────────────────────────────────────
   for(int t=0;t<N_TABS;t++)
      if(sparam==PFX+"TAB"+IntegerToString(t))
      { ActiveTab=t; RebuildActiveTab(); return; }

   // ── NAVEGACIÓN SÍMBOLOS ───────────────────────────────────────
   if(sparam==PFX+"SB_PREV")
   { if(g_SymCount>0)
     { g_PanelSymIdx=(g_PanelSymIdx-1+g_SymCount)%g_SymCount;
       g_ScrollOffset=0; SaveState(); RebuildPanel(); }
     return; }

   if(sparam==PFX+"SB_NEXT")
   { if(g_SymCount>0)
     { g_PanelSymIdx=(g_PanelSymIdx+1)%g_SymCount;
       g_ScrollOffset=0; SaveState(); RebuildPanel(); }
     return; }

   // ── TAB OPERAR ────────────────────────────────────────────────
   if(si>=0&&si<g_SymCount)
   {
      string sym=g_Symbols[si].name;

      if(sparam==PFX_OP+"ASK")
      { g_LimitPrice=NormalizeDouble(SymbolInfoDouble(sym,SYMBOL_ASK),dg);
        if(ObjectFind(0,EDIT_PRICE_NAME)>=0)
           ObjectSetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT,
                           DoubleToString(g_LimitPrice,dg));
        GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice);
        UpdateLimitLine(); return; }

      if(sparam==PFX_OP+"BID")
      { g_LimitPrice=NormalizeDouble(SymbolInfoDouble(sym,SYMBOL_BID),dg);
        if(ObjectFind(0,EDIT_PRICE_NAME)>=0)
           ObjectSetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT,
                           DoubleToString(g_LimitPrice,dg));
        GlobalVariableSet(GV_LIMIT_PRICE,g_LimitPrice);
        UpdateLimitLine(); return; }

      if(sparam==PFX_OP+"RST")
      { g_LimitPrice=0.0;
        if(ObjectFind(0,EDIT_PRICE_NAME)>=0)
           ObjectSetString(0,EDIT_PRICE_NAME,OBJPROP_TEXT,"0");
        GlobalVariableSet(GV_LIMIT_PRICE,0.0);
        RemoveLimitLine(); return; }

      double lots=GetPairLot(si);   // lote manual = nivel del par (Asistente 3)

      if(sparam==PFX_OP+"BUY")
      { SendMarketOrderEx(si,-1,ORDER_TYPE_BUY, lots,MagicManual(si)); return; }
      if(sparam==PFX_OP+"SELL")
      { SendMarketOrderEx(si,-1,ORDER_TYPE_SELL,lots,MagicManual(si)); return; }
      if(sparam==PFX_OP+"BUYLMT")
      { _SendLimitManual(si,ORDER_TYPE_BUY_LIMIT, lots,g_LimitPrice); return; }
      if(sparam==PFX_OP+"SELLLMT")
      { _SendLimitManual(si,ORDER_TYPE_SELL_LIMIT,lots,g_LimitPrice); return; }

      if(sparam==PFX_OP+"CLOSEALL")
      { for(int i=PositionsTotal()-1;i>=0;i--)
        { ulong t=PositionGetTicket(i); if(t==0) continue;
          if(PositionGetString(POSITION_SYMBOL)!=sym) continue;
          if(!IsAnyMagic((long)PositionGetInteger(POSITION_MAGIC))) continue;
          ClosePosition(t); }
        return; }
   }

   // ── TAB POSICIONES — cerrar individual ───────────────────────
   if(StringFind(sparam,PFX_POS+"CLZ")==0)
   {
      int k=(int)StringToInteger(StringSubstr(sparam,StringLen(PFX_POS+"CLZ")));
      if(k>=0&&k<g_TradeCount&&!g_Trades[k].isPending)
         ClosePosition(g_Trades[k].ticket);
      return;
   }

   if(sparam==PFX_POS+"SCRUP")
   { if(g_ScrollOffset>0){ g_ScrollOffset--; RebuildActiveTab(); } return; }
   if(sparam==PFX_POS+"SCRDN")
   { g_ScrollOffset++; RebuildActiveTab(); return; }

   // ── TAB CONFIG ────────────────────────────────────────────────
   if(sparam==PFX_CFG+"SAV")
   { SaveState(); RebuildActiveTab(); return; }

   if(sparam==PFX_CFG+"CLR")
   {
      GlobalVariableDel(GV_ADV_MODE);
      GlobalVariableDel(GV_LIMIT_PRICE);
      if(FileIsExist(GetStateFileName())) FileDelete(GetStateFileName());
      for(int s=0;s<g_SymCount;s++)
      { for(int st=0;st<STRAT_COUNT;st++)
        { g_SysState[s].strategies[st].CV            =1;
          g_PairLevel[s]                =1;
          g_SysState[s].strategies[st].CV_Max        =1;
          g_SysState[s].strategies[st].virtualActive =false;
          g_SysState[s].strategies[st].isLive        =false;
          g_SysState[s].strategies[st].virtualSLMoved=false;
          g_SysState[s].strategies[st].cbPaused      =false;
          g_SysState[s].strategies[st].liveLogicLevel =0; }
        g_SysState[s].hasLive=false;
        g_SysState[s].activeLiveStrategy=-1;
        ConfluenciaResetState(s);
        Strat2ResetState(s); }
      g_BaseCapital     =InpBaseCapital;
      g_BaseMaxBalance  =AccountInfoDouble(ACCOUNT_BALANCE);
      g_CircuitBreakerOn=false;
      RebuildPanel(); return;
   }

   if(sparam==PFX_CFG+"ADV")
   { g_AdvancedMode=!g_AdvancedMode; SaveState(); RebuildActiveTab(); return; }

   // ── TAB ESTRATEGIAS ───────────────────────────────────────────
   if(sparam==PFX_EST+"RSTALL")
   {
      if(si>=0&&si<g_SymCount)
      { for(int st=0;st<STRAT_COUNT;st++)
        { g_SysState[si].strategies[st].CV            =1;
          g_PairLevel[si]               =1;
          g_SysState[si].strategies[st].CV_Max        =1;
          g_SysState[si].strategies[st].virtualActive =false;
          g_SysState[si].strategies[st].isLive        =false;
          g_SysState[si].strategies[st].virtualSLMoved=false;
          g_SysState[si].strategies[st].cbPaused      =false;
          g_SysState[si].strategies[st].liveLogicLevel =0; }
        g_SysState[si].hasLive=false;
        g_SysState[si].activeLiveStrategy=-1;
        ConfluenciaResetState(si);
        Strat2ResetState(si); }
      SaveState(); RebuildPanel(); return;
   }

   if(sparam==PFX_EST+"FRCNXT")
   { if(si>=0&&si<g_SymCount) SelectNextLiveStrategy(si);
     RebuildActiveTab(); return; }
}

//+------------------------------------------------------------------+
//| VALIDACIÓN POR PAR — resumen en el LOG (throttle 5 min)          |
//| El resumen visual en gráfico lo da el PANEL MULTI-PAR; esto      |
//| deja constancia periódica en el journal sin inundarlo por tick.  |
//+------------------------------------------------------------------+
datetime g_LastValidateTime=0;

void ValidateAllSymbols()
{
   datetime now=TimeCurrent();
   if(g_LastValidateTime!=0 && now-g_LastValidateTime<300) return;
   g_LastValidateTime=now;

   Print("=== VALIDACIÓN PARES — Nivel | CV | OPEN | Lot | Trail | Estado ===");
   for(int si=0;si<g_SymCount;si++)
   {
      if(!g_Symbols[si].active) continue;
      MPSnapshot s;
      MPFillSnapshot(si,s);
      string line=s.sym
         +" | Niv="+IntegerToString(s.cr)
         +" CV="+IntegerToString(s.cv)
         +" | H1="+s.h1Txt+" M3="+s.m3Txt
         +" | ZONA="+((s.zBuy&&s.zSell)?"C+V":s.zBuy?"C":s.zSell?"V":"-")
         +" | "+(s.hasPos?"OPEN":"CERR")
         +" | Lot="+DoubleToString(s.lot,2)
         +" | 1:2="+((s.trail)?"ON":"OFF")
         +" -> "+s.state;
      Print(line);
   }
}
