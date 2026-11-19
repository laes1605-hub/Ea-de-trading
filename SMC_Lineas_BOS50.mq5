//+------------------------------------------------------------------+
//|                                        SMC_Lineas_BOS50.mq5      |
//|  Líneas L1-L4 + BOS/CHoCH anclados al 50% de la estructura       |
//|  Indicador VISUAL para la terminal MT5 (Exness). NO opera.       |
//+------------------------------------------------------------------+
//| LÓGICA (idéntica al EA v8.56+ "trabajador multichart.mq5"):      |
//|  · L1 = techo del rango, L2 = suelo del rango.                   |
//|  · EQ = 50% de la estructura = L2 + (L1-L2)*0.5.                 |
//|  · L3/L4 se activan solo con vela cerrada CONTRARIA al bias y    |
//|    guardan máximos/mínimos al tick; la ruptura L3>L1 / L4<L2     |
//|    se consolida al cierre (swap L1=L3, L2=L4).                   |
//|  · CHoCH = rompimiento que CAMBIA el bias.                       |
//|  · BOS   = rompimiento de CONTINUACIÓN (mismo bias):             |
//|      - por cierre más allá de RefLevel, o                        |
//|      - por commit en la dirección del bias.                      |
//|  · TRAMO de cada rompimiento en LastBreakHigh/Low; su 50%        |
//|    (leg50) es el nivel de entrada del EA.                        |
//|                                                                  |
//| VISUALIZACIÓN "DENTRO DEL 50%":                                  |
//|  · Cada etiqueta BOS/CHoCH se dibuja ANCLADA al 50% (EQ) de la   |
//|    estructura vigente al momento del rompimiento                 |
//|    (InpAnchorAt50=false la ancla al 50% del tramo).              |
//|  · Además se dibuja la línea corta del 50% del tramo.            |
//|                                                                  |
//| TERMINAL EXNESS:                                                 |
//|  · Cero configuración: funciona en cuanto se adjunta al gráfico  |
//|    (_Symbol / _Period + overlay H1 opcional).                    |
//|  · Convive con el EA en el MISMO gráfico (los indicadores no     |
//|    interfieren con los EAs).                                     |
//|  · Cada BOS/CHoCH se registra con Print() → ver en              |
//|    Caja de herramientas → Expertos.                              |
//|  · Funciona aunque el trading algorítmico esté desactivado.      |
//+------------------------------------------------------------------+
#property copyright   "SMC Líneas BOS50"
#property version     "1.00"
#property description "L1-L4 + BOS/CHoCH anclados al 50% — visual para terminal Exness (no opera)"
#property strict
#property indicator_chart_window

//+------------------------------------------------------------------+
//| INPUTS                                                           |
//+------------------------------------------------------------------+
input group "=== MOTOR DE LÍNEAS ==="
input int    InpLookbackBars  = 300;         // Velas para L1/L2 e historial de marcas

input group "=== SEGUNDA ESTRUCTURA (MADRE) ==="
input bool            InpUseTF2 = true;      // Mostrar estructura madre
input ENUM_TIMEFRAMES InpTF2    = PERIOD_H1; // TF de la estructura madre

input group "=== DIBUJO ==="
input bool InpShowLines   = true;  // Líneas L1/L2/L3/L4
input bool InpShowEQ50    = true;  // Línea del 50% (EQ) de la estructura
input bool InpShowZones   = true;  // Zonas premium/descuento del TF del gráfico
input bool InpShowBOS     = true;  // Marcas BOS
input bool InpShowCHoCH   = true;  // Marcas CHoCH
input bool InpAnchorAt50  = true;  // Etiquetas BOS/CHoCH DENTRO del 50% (false = 50% del tramo)
input bool InpShowLeg50   = true;  // Línea corta del 50% del tramo
input int  InpLegBars     = 8;     // Largo de la línea del 50% del tramo (velas)
input int  InpMaxMarks    = 30;    // Marcas BOS/CHoCH visibles por TF (1-100)
input int  InpMarkShiftBars = 1;   // Desplazamiento de la etiqueta (velas)

input group "=== PANEL + TERMINAL ==="
input bool InpShowDashboard = true;  // Panel en el gráfico
input int  InpDashX         = 10;    // X del panel
input int  InpDashY         = 20;    // Y del panel
input bool InpLogTerminal   = true;  // Avisos BOS/CHoCH en la pestaña Expertos
input bool InpUseAlert      = false; // Alerta emergente en cada BOS/CHoCH

//+------------------------------------------------------------------+
//| ENUMS / STRUCTS (motor v8.56)                                    |
//+------------------------------------------------------------------+
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

struct StructureEngine
{
   double               L1, L2, L3, L4, EQ;
   bool                 L3L4_Active;
   int                  PendingBreakDir;
   double               RefLevel;      // nivel que debe CERRARSE para el BOS
   bool                 BosDone;       // BOS del tramo actual ya emitido
   double               BosLegHigh;    // extremo superior del tramo del BOS
   double               BosLegLow;     // extremo inferior del tramo del BOS
   double               LastBreakHigh; // tramo que rompió (su 50% = entrada EA)
   double               LastBreakLow;
   ENUM_STRUCTURE_BIAS  Bias;
   ENUM_STRUCTURE_PHASE Phase;
   bool                 Valid;
   ENUM_TIMEFRAMES      TF;
};

//--- Marca de rompimiento (BOS o CHoCH) con sus dos 50% -------------
struct BreakMark
{
   datetime t;        // hora de la vela cerrada que confirmó
   int      dir;      // +1 alcista / -1 bajista
   bool     isChoch;  // true = CHoCH · false = BOS
   double   eq50;      // 50% de la ESTRUCTURA al momento del evento
   double   legH;      // tramo: extremo superior
   double   legL;      // tramo: extremo inferior
   double   leg50;     // 50% del TRAMO
   double   rc;        // cierre que confirmó
};

//+------------------------------------------------------------------+
//| GLOBALES                                                         |
//+------------------------------------------------------------------+
#define PFX_TF "SMC50_TF_"
#define PFX_H1 "SMC50_H1_"
#define PFX_D  "SMC50_D_"

StructureEngine G_SE_TF;
StructureEngine G_SE_H1;
bool            G_H1_On = false;

BreakMark G_MarksTF[];
BreakMark G_MarksH1[];

datetime G_LastClosedTF = 0;
datetime G_LastClosedH1 = 0;

int G_DrawnTF = 0;   // marcas dibujadas (para borrar sobrantes)
int G_DrawnH1 = 0;
int G_DashLines = 0;

//+------------------------------------------------------------------+
//| MOTOR — funciones idénticas al EA v8.56                          |
//+------------------------------------------------------------------+
void SE_UpdateEQ(StructureEngine &SE)
{
   SE.EQ = SE.L2 + (SE.L1 - SE.L2) * 0.5;
}

void SE_ClearReaction(StructureEngine &SE)
{
   SE.L3 = 0.0;
   SE.L4 = 0.0;
   SE.L3L4_Active = false;
   SE.PendingBreakDir = 0;
   SE.RefLevel = 0.0;
   SE.BosDone = false;
   SE.BosLegHigh = 0.0;
   SE.BosLegLow = 0.0;
   SE.Phase = PHASE_CONTINUATION;
}

int SE_CommitStructureMove(StructureEngine &SE, int dir, int &choch)
{
   if(dir == 0 || !SE.L3L4_Active) return 0;

   ENUM_STRUCTURE_BIAS oldBias = SE.Bias;
   ENUM_STRUCTURE_BIAS newBias = BIAS_BULLISH;
   if(dir < 0) newBias = BIAS_BEARISH;

   //--- TRAMO del rompimiento = rango de reacción/impulso (L3..L4)
   SE.LastBreakHigh = MathMax(SE.L3, SE.L4);
   SE.LastBreakLow  = MathMin(SE.L3, SE.L4);

   SE.L1 = SE.L3;
   SE.L2 = SE.L4;
   if(SE.L1 < SE.L2)
   {
      double tmp = SE.L1;
      SE.L1 = SE.L2;
      SE.L2 = tmp;
   }

   SE.Bias = newBias;
   SE_UpdateEQ(SE);
   SE_ClearReaction(SE);

   choch = (oldBias != BIAS_UNDEFINED && oldBias != newBias ? dir : 0);
   return dir;
}

int SE_LastBreakDirectionFromCandle(double O, double C, ENUM_STRUCTURE_BIAS currentBias)
{
   if(C > O) return +1;
   if(C < O) return -1;
   if(currentBias == BIAS_BEARISH) return +1;
   return -1;
}

int SE_BreakDirection(StructureEngine &SE, double O, double C)
{
   if(!SE.Valid || !SE.L3L4_Active) return 0;

   bool breakUp = (SE.L3 > SE.L1);
   bool breakDn = (SE.L4 < SE.L2);
   if(!breakUp && !breakDn) return 0;

   if(breakUp && breakDn)
   {
      if(SE.PendingBreakDir != 0) return SE.PendingBreakDir;
      return SE_LastBreakDirectionFromCandle(O, C, SE.Bias);
   }
   if(breakUp) return +1;
   return -1;
}

void SE_MarkPendingBreak(StructureEngine &SE, double price)
{
   if(!SE.Valid || !SE.L3L4_Active || price <= 0.0) return;

   if(price > SE.L1)
   {
      SE.Phase = PHASE_TRIGGERED;
      SE.PendingBreakDir = +1;
   }
   if(price < SE.L2)
   {
      SE.Phase = PHASE_TRIGGERED;
      SE.PendingBreakDir = -1;
   }
}

int SE_CheckBreakAndCommit(StructureEngine &SE, double O, double C, int &choch)
{
   int dir = SE_BreakDirection(SE, O, C);
   if(dir == 0) return 0;
   return SE_CommitStructureMove(SE, dir, choch);
}

//--- BOS: continuación — cierre más allá de RefLevel ---------------
int SE_CheckContinuationBreak(StructureEngine &SE, double C)
{
   if(!SE.Valid || !SE.L3L4_Active) return 0;
   if(SE.BosDone)                   return 0;
   if(SE.RefLevel <= 0.0)           return 0;

   int dir = 0;
   if(SE.Bias == BIAS_BULLISH && C > SE.RefLevel) dir = +1;
   if(SE.Bias == BIAS_BEARISH && C < SE.RefLevel) dir = -1;
   if(dir == 0) return 0;

   SE.LastBreakHigh = MathMax(SE.BosLegHigh, SE.BosLegLow);
   SE.LastBreakLow  = MathMin(SE.BosLegHigh, SE.BosLegLow);
   if(SE.LastBreakHigh <= SE.LastBreakLow)
   {
      SE.LastBreakHigh = MathMax(SE.L3, SE.L4);
      SE.LastBreakLow  = MathMin(SE.L3, SE.L4);
   }
   if(SE.LastBreakHigh <= SE.LastBreakLow) return 0;

   if(dir > 0 && SE.LastBreakHigh > SE.L1) { SE.L1 = SE.LastBreakHigh; SE_UpdateEQ(SE); }
   if(dir < 0 && SE.LastBreakLow  < SE.L2) { SE.L2 = SE.LastBreakLow;  SE_UpdateEQ(SE); }

   SE.BosDone = true;
   return dir;
}

//--- Estado inicial = mismo SE_Init del EA (máx/mín del lookback) ---
bool SE_InitLive(StructureEngine &SE, string sym, ENUM_TIMEFRAMES tf, int lookback)
{
   SE.TF = tf;
   SE.Valid = false;
   SE.L1 = 0; SE.L2 = 0; SE.L3 = 0; SE.L4 = 0; SE.EQ = 0;
   SE.L3L4_Active = false;
   SE.PendingBreakDir = 0;
   SE.Bias = BIAS_UNDEFINED;
   SE.Phase = PHASE_CONTINUATION;
   SE.RefLevel = 0.0;
   SE.BosDone = false;
   SE.BosLegHigh = 0.0;
   SE.BosLegLow = 0.0;
   SE.LastBreakHigh = 0.0;
   SE.LastBreakLow = 0.0;

   double p  = SymbolInfoDouble(sym, SYMBOL_BID);
   double pt = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(p <= 0.0 || pt <= 0.0) return false;

   SE.L1 = p + 2.0 * pt;
   SE.L2 = p - 2.0 * pt;

   MqlRates R[];
   ArraySetAsSeries(R, true);
   int n = CopyRates(sym, tf, 1, lookback, R);
   if(n < 2) return false;

   for(int i = 0; i < n; i++)
   {
      if(R[i].high > SE.L1) SE.L1 = R[i].high;
      if(R[i].low  < SE.L2) SE.L2 = R[i].low;
   }
   if(R[0].close > R[0].open)      SE.Bias = BIAS_BULLISH;
   else if(R[0].close < R[0].open) SE.Bias = BIAS_BEARISH;

   SE_UpdateEQ(SE);
   SE.Valid = true;
   return true;
}

//--- Tick: solo L3/L4 + tramo BOS + ruptura pendiente ---------------
void SE_ApplyTick(StructureEngine &SE, double price)
{
   if(!SE.Valid || !SE.L3L4_Active) return;
   if(price <= 0.0) return;

   if(price > SE.L3) SE.L3 = price;
   if(price < SE.L4) SE.L4 = price;

   if(price > SE.BosLegHigh) SE.BosLegHigh = price;
   if(price < SE.BosLegLow)  SE.BosLegLow  = price;

   if(SE.Bias == BIAS_BULLISH && price > SE.L1)      { SE.L1 = price; SE_UpdateEQ(SE); }
   else if(SE.Bias == BIAS_BEARISH && price < SE.L2) { SE.L2 = price; SE_UpdateEQ(SE); }

   SE_MarkPendingBreak(SE, price);
}

//+------------------------------------------------------------------+
//| Vela cerrada (cuerpo = SE_OnClose v8.56, con OHLC explícito).    |
//| Salidas: choch = cambio de bias · bos = continuación.            |
//| El TRAMO queda en LastBreakHigh/Low.                             |
//+------------------------------------------------------------------+
void SE_ProcessClosedBar(StructureEngine &SE, double O, double H, double L, double C,
                         int &choch, int &trig, int &bos)
{
   choch = 0; trig = 0; bos = 0;
   if(!SE.Valid) return;
   if(O <= 0.0 || C <= 0.0 || H <= 0.0 || L <= 0.0) return;

   bool green = (C > O), red = (C < O);

   if(SE.Bias == BIAS_UNDEFINED)
   {
      if(green) SE.Bias = BIAS_BULLISH;
      if(red)   SE.Bias = BIAS_BEARISH;
      return;
   }

   if(SE.L3L4_Active)
   {
      if(H > SE.L3) SE.L3 = H;
      if(L < SE.L4) SE.L4 = L;

      if(H > SE.BosLegHigh) SE.BosLegHigh = H;
      if(L < SE.BosLegLow)  SE.BosLegLow  = L;

      //--- vela CONTRARIA re-arma el BOS; si ya hubo BOS abre tramo nuevo
      bool contrary = ((SE.Bias == BIAS_BULLISH && red) ||
                       (SE.Bias == BIAS_BEARISH && green));
      if(contrary)
      {
         if(SE.BosDone)
         {
            SE.BosLegHigh = H;
            SE.BosLegLow  = L;
         }
         SE.RefLevel = (SE.Bias == BIAS_BULLISH ? SE.L1 : SE.L2);
         SE.BosDone = false;
      }

      //--- el CHoCH manda primero
      double blh = SE.BosLegHigh, bll = SE.BosLegLow;
      trig = SE_CheckBreakAndCommit(SE, O, C, choch);
      if(trig != 0)
      {
         if(choch == 0)   // misma dirección = BOS por commit
         {
            if(blh > bll)
            {
               SE.LastBreakHigh = blh;
               SE.LastBreakLow  = bll;
            }
            bos = trig;
         }
         return;
      }
      bos = SE_CheckContinuationBreak(SE, C);
      if(bos == 0) SE.Phase = PHASE_REACTION;
      return;
   }

   //--- Continuación sin reacción: L1/L2 al CIERRE
   if(SE.Bias == BIAS_BULLISH)
   {
      if(H > SE.L1) { SE.L1 = H; SE_UpdateEQ(SE); }
   }
   else if(SE.Bias == BIAS_BEARISH)
   {
      if(L < SE.L2) { SE.L2 = L; SE_UpdateEQ(SE); }
   }

   //--- Activación de L3/L4 solo por cierre contrario
   if(SE.Bias == BIAS_BULLISH && red)
   {
      SE.L3L4_Active = true;
      SE.L3 = SE.L1;
      SE.L4 = L;
      SE.RefLevel = SE.L1;
      SE.BosDone = false;
      SE.BosLegHigh = H;
      SE.BosLegLow  = L;
      SE.Phase = PHASE_REACTION;
      trig = SE_CheckBreakAndCommit(SE, O, C, choch);
   }
   else if(SE.Bias == BIAS_BEARISH && green)
   {
      SE.L3L4_Active = true;
      SE.L3 = H;
      SE.L4 = SE.L2;
      SE.RefLevel = SE.L2;
      SE.BosDone = false;
      SE.BosLegHigh = H;
      SE.BosLegLow  = L;
      SE.Phase = PHASE_REACTION;
      trig = SE_CheckBreakAndCommit(SE, O, C, choch);
   }
}

//+------------------------------------------------------------------+
//| MARCAS BOS/CHoCH                                                 |
//+------------------------------------------------------------------+
void RecordMark(BreakMark &marks[], datetime t, int dir, bool isChoch,
                double eq50, double legH, double legL, double rc)
{
   if(dir == 0 || legH <= legL || legL <= 0.0 || eq50 <= 0.0) return;

   int maxM = MathMax(1, MathMin(100, InpMaxMarks));
   while(ArraySize(marks) >= maxM)
      ArrayRemove(marks, 0, 1);

   int n = ArraySize(marks);
   ArrayResize(marks, n + 1);
   marks[n].t       = t;
   marks[n].dir     = dir;
   marks[n].isChoch = isChoch;
   marks[n].eq50    = eq50;
   marks[n].legH    = legH;
   marks[n].legL    = legL;
   marks[n].leg50   = (legH + legL) * 0.5;
   marks[n].rc      = rc;
}

string TFName(ENUM_TIMEFRAMES tf)
{
   if(tf == PERIOD_CURRENT) tf = _Period;
   switch(tf)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M2:  return "M2";
      case PERIOD_M3:  return "M3";
      case PERIOD_M4:  return "M4";
      case PERIOD_M5:  return "M5";
      case PERIOD_M6:  return "M6";
      case PERIOD_M10: return "M10";
      case PERIOD_M12: return "M12";
      case PERIOD_M15: return "M15";
      case PERIOD_M20: return "M20";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H2:  return "H2";
      case PERIOD_H3:  return "H3";
      case PERIOD_H4:  return "H4";
      case PERIOD_H6:  return "H6";
      case PERIOD_H8:  return "H8";
      case PERIOD_H12: return "H12";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
   }
   return EnumToString(tf);
}

color MarkColor(BreakMark &m)
{
   if(m.isChoch) return (m.dir > 0 ? clrDodgerBlue : clrOrange);
   return (m.dir > 0 ? clrLimeGreen : clrTomato);
}

string MarkText(BreakMark &m, string tf)
{
   string kind = (m.isChoch ? "CHoCH" : "BOS");
   string dd   = (m.dir > 0 ? "ALC" : "BAJ");
   double px   = (InpAnchorAt50 ? m.eq50 : m.leg50);
   return "[" + tf + "] " + kind + " " + dd + " 50%=" + DoubleToString(px, _Digits);
}

//+------------------------------------------------------------------+
//| HISTORIAL: reproduce velas cerradas para mostrar marcas pasadas  |
//+------------------------------------------------------------------+
void BackfillEngine(BreakMark &marks[], ENUM_TIMEFRAMES tf)
{
   ArrayResize(marks, 0);

   MqlRates R[];
   ArraySetAsSeries(R, true);
   int n = CopyRates(_Symbol, tf, 1, InpLookbackBars, R);
   if(n < 5) return;

   //--- motor de repetición sembrado con la vela más antigua
   StructureEngine s;
   s.TF = tf;
   s.Valid = true;
   s.L1 = R[n - 1].high;
   s.L2 = R[n - 1].low;
   s.L3 = 0; s.L4 = 0; s.EQ = 0;
   s.L3L4_Active = false;
   s.PendingBreakDir = 0;
   s.RefLevel = 0.0;
   s.BosDone = false;
   s.BosLegHigh = 0.0;
   s.BosLegLow = 0.0;
   s.LastBreakHigh = 0.0;
   s.LastBreakLow = 0.0;
   s.Phase = PHASE_CONTINUATION;
   if(R[n - 1].close > R[n - 1].open)      s.Bias = BIAS_BULLISH;
   else if(R[n - 1].close < R[n - 1].open) s.Bias = BIAS_BEARISH;
   else                                   s.Bias = BIAS_UNDEFINED;
   SE_UpdateEQ(s);

   for(int i = n - 2; i >= 0; i--)   // antigua → reciente
   {
      int c = 0, t = 0, b = 0;
      SE_ProcessClosedBar(s, R[i].open, R[i].high, R[i].low, R[i].close, c, t, b);
      if(c != 0)
         RecordMark(marks, R[i].time, c, true, s.EQ,
                    s.LastBreakHigh, s.LastBreakLow, R[i].close);
      else if(b != 0)
         RecordMark(marks, R[i].time, b, false, s.EQ,
                    s.LastBreakHigh, s.LastBreakLow, R[i].close);
   }
}

//--- Procesa las velas cerradas pendientes (con puesta al día) ------
void EngineCatchUp(StructureEngine &SE, BreakMark &marks[], datetime &lastClosed, string tag)
{
   if(!SE.Valid) return;

   datetime curBar = (datetime)SeriesInfoInteger(_Symbol, SE.TF, SERIES_LASTBAR_DATE);
   if(curBar <= 0) return;

   if(lastClosed <= 0)
   {
      lastClosed = (datetime)iTime(_Symbol, SE.TF, 1);
      return;
   }

   MqlRates R[];
   ArraySetAsSeries(R, true);
   int n = CopyRates(_Symbol, SE.TF, 0, 400, R);
   if(n < 2) return;

   for(int i = n - 1; i >= 1; i--)   // antigua → reciente
   {
      if(R[i].time <= lastClosed)  continue;
      if(R[i].time >= curBar)      continue;   // aún en formación

      int c = 0, t = 0, b = 0;
      SE_ProcessClosedBar(SE, R[i].open, R[i].high, R[i].low, R[i].close, c, t, b);

      if(c != 0 || b != 0)
      {
         int  dir     = (c != 0 ? c : b);
         bool isChoch = (c != 0);
         RecordMark(marks, R[i].time, dir, isChoch, SE.EQ,
                    SE.LastBreakHigh, SE.LastBreakLow, R[i].close);
         LogBreak(tag, SE.TF, dir, isChoch, SE.EQ,
                  SE.LastBreakHigh, SE.LastBreakLow, R[i].close);
      }
      lastClosed = R[i].time;
   }
}

//+------------------------------------------------------------------+
//| AVISO EN LA TERMINAL (pestaña Expertos / alerta)                 |
//+------------------------------------------------------------------+
void LogBreak(string tag, ENUM_TIMEFRAMES tf, int dir, bool isChoch,
              double eq50, double legH, double legL, double rc)
{
   if(!InpLogTerminal && !InpUseAlert) return;

   string kind = (isChoch ? "CHoCH" : "BOS");
   string dd   = (dir > 0 ? "ALCISTA" : "BAJISTA");
   double leg50 = (legH + legL) * 0.5;
   string msg = StringFormat("SMC50 [%s,%s][%s] %s %s cierre=%s | 50%% estructura=%s | tramo=[%s-%s] 50%% tramo=%s",
                             _Symbol, TFName(tf), tag, kind, dd,
                             DoubleToString(rc, _Digits),
                             DoubleToString(eq50, _Digits),
                             DoubleToString(legH, _Digits),
                             DoubleToString(legL, _Digits),
                             DoubleToString(leg50, _Digits));
   if(InpLogTerminal) Print(msg);
   if(InpUseAlert)    Alert(msg);
}

//+------------------------------------------------------------------+
//| DIBUJO — líneas, zonas, marcas                                   |
//+------------------------------------------------------------------+
void D_HLine(string name, double price, color clr, ENUM_LINE_STYLE sty, int w, string lbl)
{
   string tn = name + "_T";
   if(price <= 0.0) { ObjectDelete(0, name); ObjectDelete(0, tn); return; }

   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   }
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_STYLE, sty);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, w);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);

   datetime tt = iTime(_Symbol, _Period, 0) + PeriodSeconds(_Period) * 6;
   string txt = lbl + "  " + DoubleToString(price, _Digits);
   if(ObjectFind(0, tn) < 0)
   {
      ObjectCreate(0, tn, OBJ_TEXT, 0, tt, price);
      ObjectSetInteger(0, tn, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, tn, OBJPROP_HIDDEN, true);
   }
   ObjectSetInteger(0, tn, OBJPROP_TIME, tt);
   ObjectSetDouble(0, tn, OBJPROP_PRICE, price);
   ObjectSetString(0, tn, OBJPROP_TEXT, txt);
   ObjectSetInteger(0, tn, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, tn, OBJPROP_FONTSIZE, 8);
   ObjectSetString(0, tn, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(0, tn, OBJPROP_ANCHOR, ANCHOR_LEFT);
   ObjectSetInteger(0, tn, OBJPROP_BACK, false);
}

void D_Rect(string name, double p1, double p2, color clr)
{
   if(p1 <= 0.0 || p2 <= 0.0) { ObjectDelete(0, name); return; }
   datetime t1 = TimeCurrent() - PeriodSeconds(_Period) * 300;
   datetime t2 = TimeCurrent() + PeriodSeconds(_Period) * 50;
   double top = MathMax(p1, p2), bot = MathMin(p1, p2);
   uchar alpha = (uchar)(255 - (86 * 255 / 100));
   color c = (color)ColorToARGB(clr, alpha);
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bot);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   }
   ObjectSetInteger(0, name, OBJPROP_TIME, 0, t1);
   ObjectSetDouble(0, name, OBJPROP_PRICE, 0, top);
   ObjectSetInteger(0, name, OBJPROP_TIME, 1, t2);
   ObjectSetDouble(0, name, OBJPROP_PRICE, 1, bot);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, c);
}

void D_ZoneLabel(string name, double price, string txt, color clr)
{
   if(price <= 0.0) { ObjectDelete(0, name); return; }
   datetime tt = iTime(_Symbol, _Period, 0) + PeriodSeconds(_Period) * 6;
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_TEXT, 0, tt, price);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 8);
      ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
   }
   ObjectSetInteger(0, name, OBJPROP_TIME, tt);
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetString(0, name, OBJPROP_TEXT, txt);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//--- Etiqueta de una marca BOS/CHoCH anclada al 50% -----------------
void D_Mark(string pfx, int idx, BreakMark &m, string tf, long tfSec)
{
   string nm = pfx + "MK" + IntegerToString(idx);
   string lg = pfx + "LG" + IntegerToString(idx);

   bool show = (m.isChoch ? InpShowCHoCH : InpShowBOS);
   if(!show) { ObjectDelete(0, nm); ObjectDelete(0, lg); return; }

   double anchor = (InpAnchorAt50 ? m.eq50 : m.leg50);
   long shift = (long)MathMax(0, InpMarkShiftBars) * tfSec;
   datetime tt = m.t + shift;
   color cc = MarkColor(m);

   if(ObjectFind(0, nm) < 0)
   {
      ObjectCreate(0, nm, OBJ_TEXT, 0, tt, anchor);
      ObjectSetInteger(0, nm, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, nm, OBJPROP_HIDDEN, true);
      ObjectSetInteger(0, nm, OBJPROP_FONTSIZE, 9);
      ObjectSetString(0, nm, OBJPROP_FONT, "Arial Bold");
      ObjectSetInteger(0, nm, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, nm, OBJPROP_BACK, false);
   }
   ObjectSetInteger(0, nm, OBJPROP_TIME, tt);
   ObjectSetDouble(0, nm, OBJPROP_PRICE, anchor);
   ObjectSetString(0, nm, OBJPROP_TEXT, MarkText(m, tf));
   ObjectSetInteger(0, nm, OBJPROP_COLOR, cc);

   //--- línea corta del 50% del tramo
   if(!InpShowLeg50 || m.leg50 <= 0.0) { ObjectDelete(0, lg); return; }
   datetime t2 = m.t + (long)MathMax(1, InpLegBars) * tfSec;
   if(ObjectFind(0, lg) < 0)
   {
      ObjectCreate(0, lg, OBJ_TREND, 0, m.t, m.leg50, t2, m.leg50);
      ObjectSetInteger(0, lg, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, lg, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, lg, OBJPROP_HIDDEN, true);
   }
   ObjectSetInteger(0, lg, OBJPROP_TIME, 0, m.t);
   ObjectSetDouble(0, lg, OBJPROP_PRICE, 0, m.leg50);
   ObjectSetInteger(0, lg, OBJPROP_TIME, 1, t2);
   ObjectSetDouble(0, lg, OBJPROP_PRICE, 1, m.leg50);
   ObjectSetInteger(0, lg, OBJPROP_COLOR, cc);
   ObjectSetInteger(0, lg, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, lg, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, lg, OBJPROP_BACK, false);
}

void D_DeleteStaleMarks(string pfx, int fromIdx, int toIdx)
{
   for(int i = fromIdx; i < toIdx; i++)
   {
      ObjectDelete(0, pfx + "MK" + IntegerToString(i));
      ObjectDelete(0, pfx + "LG" + IntegerToString(i));
   }
}

//--- Líneas + zonas de un motor -------------------------------------
void DrawEngineLines(string pfx, StructureEngine &SE, string tag,
                     color cMain, color cEQ, ENUM_LINE_STYLE eqStyle, bool zones)
{
   if(!SE.Valid)
   {
      string all[] = {"L1", "L2", "EQ", "L3", "L4", "ZB", "ZS", "ZBL", "ZSL"};
      for(int i = 0; i < ArraySize(all); i++)
      {
         ObjectDelete(0, pfx + all[i]);
         ObjectDelete(0, pfx + all[i] + "_T");
      }
      return;
   }

   if(InpShowLines)
   {
      D_HLine(pfx + "L1", SE.L1, cMain, STYLE_SOLID, 2, tag + " L1");
      D_HLine(pfx + "L2", SE.L2, cMain, STYLE_SOLID, 2, tag + " L2");
      D_HLine(pfx + "L3", (SE.L3L4_Active ? SE.L3 : 0.0), clrMagenta, STYLE_DASH, 2, tag + " L3");
      D_HLine(pfx + "L4", (SE.L3L4_Active ? SE.L4 : 0.0), clrRed, STYLE_DASH, 2, tag + " L4");
   }
   else
   {
      string ll[] = {"L1", "L2", "L3", "L4"};
      for(int i = 0; i < ArraySize(ll); i++)
      {
         ObjectDelete(0, pfx + ll[i]);
         ObjectDelete(0, pfx + ll[i] + "_T");
      }
   }

   if(InpShowEQ50)
      D_HLine(pfx + "EQ", SE.EQ, cEQ, eqStyle, 1, "50% " + tag);
   else
   {
      ObjectDelete(0, pfx + "EQ");
      ObjectDelete(0, pfx + "EQ_T");
   }

   if(zones && InpShowZones)
   {
      D_Rect(pfx + "ZB", SE.EQ, SE.L2, C'0,120,60');    // descuento (compra)
      D_Rect(pfx + "ZS", SE.L1, SE.EQ, C'160,30,30');   // premium (venta)
      D_ZoneLabel(pfx + "ZBL", (SE.EQ + SE.L2) * 0.5, tag + " DESCUENTO", clrLightGreen);
      D_ZoneLabel(pfx + "ZSL", (SE.L1 + SE.EQ) * 0.5, tag + " PREMIUM", clrLightSalmon);
   }
   else
   {
      ObjectDelete(0, pfx + "ZB");
      ObjectDelete(0, pfx + "ZS");
      ObjectDelete(0, pfx + "ZBL");
      ObjectDelete(0, pfx + "ZSL");
   }
}

//--- Marcas de un motor ----------------------------------------------
void DrawEngineMarks(string pfx, BreakMark &marks[], string tf, long tfSec, int &drawn)
{
   int n = ArraySize(marks);
   for(int i = 0; i < n; i++)
      D_Mark(pfx, i, marks[i], tf, tfSec);
   if(drawn > n)
      D_DeleteStaleMarks(pfx, n, drawn);
   drawn = n;
}

//+------------------------------------------------------------------+
//| PANEL EN EL GRÁFICO                                              |
//+------------------------------------------------------------------+
string BiasText(ENUM_STRUCTURE_BIAS b)
{
   if(b == BIAS_BULLISH) return "ALCISTA";
   if(b == BIAS_BEARISH) return "BAJISTA";
   return "-";
}

string PhaseText(ENUM_STRUCTURE_PHASE p)
{
   if(p == PHASE_REACTION)  return "REACCION";
   if(p == PHASE_TRIGGERED) return "RUPTURA";
   return "CONT.";
}

void LastOfKind(BreakMark &marks[], bool wantChoch, int &pos)
{
   pos = -1;
   for(int i = ArraySize(marks) - 1; i >= 0; i--)
   {
      if(marks[i].isChoch == wantChoch) { pos = i; break; }
   }
}

string MarkShort(BreakMark &m)
{
   string k = (m.isChoch ? "CHoCH" : "BOS");
   string d = (m.dir > 0 ? "ALC ▲" : "BAJ ▼");
   return StringFormat("%s %s %s 50%%=%s", k, d,
                       TimeToString(m.t, TIME_MINUTES),
                       DoubleToString((InpAnchorAt50 ? m.eq50 : m.leg50), _Digits));
}

void DashLine(int idx, string text, color clr)
{
   string n = PFX_D + "L" + IntegerToString(idx);
   if(ObjectFind(0, n) < 0)
   {
      ObjectCreate(0, n, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, n, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, n, OBJPROP_FONTSIZE, 8);
      ObjectSetString(0, n, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, n, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, n, OBJPROP_HIDDEN, true);
      ObjectSetInteger(0, n, OBJPROP_BACK, false);
   }
   ObjectSetInteger(0, n, OBJPROP_XDISTANCE, InpDashX + 8);
   ObjectSetInteger(0, n, OBJPROP_YDISTANCE, InpDashY + 8 + idx * 16);
   ObjectSetString(0, n, OBJPROP_TEXT, text);
   ObjectSetInteger(0, n, OBJPROP_COLOR, clr);
}

void DashAdd(string &L[], color &C[], string txt, color clr)
{
   int n = ArraySize(L);
   ArrayResize(L, n + 1);
   ArrayResize(C, n + 1);
   L[n] = txt;
   C[n] = clr;
}

void DrawDashboard()
{
   string bg = PFX_D + "BG";
   if(!InpShowDashboard)
   {
      ObjectDelete(0, bg);
      for(int i = 0; i < G_DashLines; i++)
         ObjectDelete(0, PFX_D + "L" + IntegerToString(i));
      G_DashLines = 0;
      return;
   }

   string tfTag = TFName(_Period);
   string h1Tag = TFName(InpTF2);

   string L[];
   color  C[];
   ArrayResize(L, 0);
   ArrayResize(C, 0);

   DashAdd(L, C, StringFormat("SMC50 LINEAS+BOS/CHoCH@50%%  %s %s", _Symbol, tfTag), clrGold);
   DashAdd(L, C, StringFormat("[%s] %s (%s)  L1=%s L2=%s 50%%=%s",
                         tfTag, BiasText(G_SE_TF.Bias), PhaseText(G_SE_TF.Phase),
                         DoubleToString(G_SE_TF.L1, _Digits),
                         DoubleToString(G_SE_TF.L2, _Digits),
                         DoubleToString(G_SE_TF.EQ, _Digits)), clrWhite);
   DashAdd(L, C, StringFormat("[%s] L3=%s L4=%s Ref=%s BOS:%s  marcas=%d",
                         tfTag,
                         (G_SE_TF.L3L4_Active ? DoubleToString(G_SE_TF.L3, _Digits) : "-"),
                         (G_SE_TF.L3L4_Active ? DoubleToString(G_SE_TF.L4, _Digits) : "-"),
                         (G_SE_TF.RefLevel > 0 ? DoubleToString(G_SE_TF.RefLevel, _Digits) : "-"),
                         (G_SE_TF.BosDone ? "si" : "no"),
                         ArraySize(G_MarksTF)), clrSilver);
   int pB = -1, pC = -1;
   LastOfKind(G_MarksTF, false, pB);
   LastOfKind(G_MarksTF, true, pC);
   DashAdd(L, C, StringFormat("[%s] ultimo BOS: %s", tfTag, (pB >= 0 ? MarkShort(G_MarksTF[pB]) : "-")),
            (pB >= 0 ? MarkColor(G_MarksTF[pB]) : clrGray));
   DashAdd(L, C, StringFormat("[%s] ultimo CHoCH: %s", tfTag, (pC >= 0 ? MarkShort(G_MarksTF[pC]) : "-")),
            (pC >= 0 ? MarkColor(G_MarksTF[pC]) : clrGray));

   if(G_H1_On && G_SE_H1.Valid)
   {
      int qB = -1, qC = -1;
      LastOfKind(G_MarksH1, false, qB);
      LastOfKind(G_MarksH1, true, qC);
      DashAdd(L, C, StringFormat("[%s] %s (%s)  L1=%s L2=%s 50%%=%s  marcas=%d",
                            h1Tag, BiasText(G_SE_H1.Bias), PhaseText(G_SE_H1.Phase),
                            DoubleToString(G_SE_H1.L1, _Digits),
                            DoubleToString(G_SE_H1.L2, _Digits),
                            DoubleToString(G_SE_H1.EQ, _Digits),
                            ArraySize(G_MarksH1)), clrWhite);
      DashAdd(L, C, StringFormat("[%s] BOS: %s  |  CHoCH: %s", h1Tag,
                            (qB >= 0 ? MarkShort(G_MarksH1[qB]) : "-"),
                            (qC >= 0 ? MarkShort(G_MarksH1[qC]) : "-")), clrSilver);
   }

   int nL = ArraySize(L);
   int W = 520, H = nL * 16 + 14;
   if(ObjectFind(0, bg) < 0)
   {
      ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, bg, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, C'25,25,25');
      ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, bg, OBJPROP_COLOR, clrDimGray);
      ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, bg, OBJPROP_HIDDEN, true);
      ObjectSetInteger(0, bg, OBJPROP_BACK, false);
   }
   ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, InpDashX);
   ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, InpDashY);
   ObjectSetInteger(0, bg, OBJPROP_XSIZE, W);
   ObjectSetInteger(0, bg, OBJPROP_YSIZE, H);

   for(int i = 0; i < nL; i++)
      DashLine(i, L[i], C[i]);
   for(int i = nL; i < G_DashLines; i++)
      ObjectDelete(0, PFX_D + "L" + IntegerToString(i));
   G_DashLines = nL;
}

//+------------------------------------------------------------------+
//| LIMPIEZA                                                         |
//+------------------------------------------------------------------+
void DeleteAllSMC50()
{
   int total = ObjectsTotal(0, 0, -1);
   for(int i = total - 1; i >= 0; i--)
   {
      string n = ObjectName(0, i, 0, -1);
      if(StringFind(n, "SMC50_") == 0)
         ObjectDelete(0, n);
   }
   G_DrawnTF = 0;
   G_DrawnH1 = 0;
   G_DashLines = 0;
}

//+------------------------------------------------------------------+
//| OnInit / OnDeinit / OnCalculate                                  |
//+------------------------------------------------------------------+
int OnInit()
{
   if(InpLookbackBars < 50)
   {
      Print("SMC50: InpLookbackBars mínimo 50");
      return INIT_PARAMETERS_INCORRECT;
   }

   G_H1_On = (InpUseTF2 && InpTF2 != _Period);

   DeleteAllSMC50();   // arrancar limpio (p. ej. tras cambiar de TF)

   if(!SE_InitLive(G_SE_TF, _Symbol, _Period, InpLookbackBars))
   {
      Print("SMC50: sin datos para ", _Symbol, " ", TFName(_Period));
      return INIT_FAILED;
   }
   G_LastClosedTF = (datetime)iTime(_Symbol, _Period, 1);
   BackfillEngine(G_MarksTF, _Period);

   if(G_H1_On)
   {
      if(!SE_InitLive(G_SE_H1, _Symbol, InpTF2, InpLookbackBars))
      {
         Print("SMC50: sin datos madre ", TFName(InpTF2), " — solo TF del gráfico");
         G_H1_On = false;
      }
      else
      {
         G_LastClosedH1 = (datetime)iTime(_Symbol, InpTF2, 1);
         BackfillEngine(G_MarksH1, InpTF2);
      }
   }

   Print(StringFormat("SMC50 v1.00 [%s,%s] L1=%s L2=%s 50%%=%s Bias=%s | marcas TF=%d%s",
                      _Symbol, TFName(_Period),
                      DoubleToString(G_SE_TF.L1, _Digits),
                      DoubleToString(G_SE_TF.L2, _Digits),
                      DoubleToString(G_SE_TF.EQ, _Digits),
                      BiasText(G_SE_TF.Bias),
                      ArraySize(G_MarksTF),
                      (G_H1_On ? StringFormat(" | H1 marcas=%d", ArraySize(G_MarksH1)) : "")));
   Print("SMC50: etiquetas BOS/CHoCH ancladas al ",
         (InpAnchorAt50 ? "50% de la ESTRUCTURA (EQ)" : "50% del TRAMO"),
         " — ver avisos en Caja de herramientas → Expertos.");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   DeleteAllSMC50();
   ChartRedraw();
   Print("SMC50 detenido. Razón: ", reason);
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   if(!G_SE_TF.Valid)
      return rates_total;

   //--- 1) velas cerradas nuevas (con puesta al día)
   EngineCatchUp(G_SE_TF, G_MarksTF, G_LastClosedTF, "TF");
   if(G_H1_On)
      EngineCatchUp(G_SE_H1, G_MarksH1, G_LastClosedH1, "MADRE");

   //--- 2) tick: L3/L4 + tramo BOS al tick
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(bid > 0.0)
   {
      SE_ApplyTick(G_SE_TF, bid);
      if(G_H1_On)
         SE_ApplyTick(G_SE_H1, bid);
   }

   //--- 3) dibujo
   DrawEngineLines(PFX_TF, G_SE_TF, TFName(_Period),
                   clrDodgerBlue, clrGold, STYLE_DOT, true);
   DrawEngineMarks(PFX_TF, G_MarksTF, TFName(_Period),
                   (long)PeriodSeconds(_Period), G_DrawnTF);

   if(G_H1_On)
   {
      DrawEngineLines(PFX_H1, G_SE_H1, TFName(InpTF2),
                      clrDarkOrange, clrGold, STYLE_DASH, false);
      DrawEngineMarks(PFX_H1, G_MarksH1, TFName(InpTF2),
                      (long)PeriodSeconds(InpTF2), G_DrawnH1);
   }

   DrawDashboard();
   ChartRedraw();
   return rates_total;
}
//+------------------------------------------------------------------+
//| FIN                                                              |
//+------------------------------------------------------------------+
