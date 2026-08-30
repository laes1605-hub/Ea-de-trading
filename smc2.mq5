//+------------------------------------------------------------------+
//|                    SMC_EA_Phase4_Final.mq5                       |
//|          Smart Money Concepts EA - Versión Final                |
//+------------------------------------------------------------------+
#property copyright   "SMC EA"
#property link        ""
#property version     "4.03"
#property description "SMC EA - Estructura MTF completa en M1"
#property strict

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| SECCIÓN 1: INSTANCIA GLOBAL                                      |
//+------------------------------------------------------------------+
CTrade Trade;

//+------------------------------------------------------------------+
//| SECCIÓN 2: INPUTS                                               |
//+------------------------------------------------------------------+
input group "=== CONFIGURACIÓN GENERAL ==="
input int    InpMagicNumber   = 100001;
input bool   InpShowLogs      = true;

input group "=== FILTRO DE HORARIO ==="
input int    InpStartHour     = 4;
input int    InpStartMinute   = 30;
input int    InpEndHour       = 20;
input int    InpEndMinute     = 0;

input group "=== MOTOR DE ESTRUCTURA ==="
input int    InpLookbackBars  = 300;

//+------------------------------------------------------------------+
//| SECCIÓN 3: ENUMERACIONES                                        |
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

//+------------------------------------------------------------------+
//| SECCIÓN 4: ESTRUCTURAS                                          |
//+------------------------------------------------------------------+
struct StructureEngine
{
   double               L1;
   double               L2;
   double               L3;
   double               L4;
   double               EQ;
   bool                 L3L4_Active;
   ENUM_STRUCTURE_BIAS  Bias;
   ENUM_STRUCTURE_PHASE Phase;
   bool                 Valid;
   ENUM_TIMEFRAMES      TF;
};

struct OrderBlock
{
   bool     Active;
   double   High;
   double   Low;
   datetime TimeStart;
   datetime TimeEnd;
   bool     IsBullish;
   string   ObjName;
   string   LabelName;
};

struct FVG
{
   bool     Active;
   double   High;
   double   Low;
   datetime TimeStart;
   datetime TimeEnd;
   bool     IsBullish;
   bool     HasOB;
   string   ObjName;
   string   LabelName;
};

//+------------------------------------------------------------------+
//| SECCIÓN 5: VARIABLES GLOBALES                                   |
//+------------------------------------------------------------------+
StructureEngine G_SE_D1;
StructureEngine G_SE_H1;
StructureEngine G_SE_TF;

datetime G_LastBar_D1 = 0;
datetime G_LastBar_H1 = 0;
datetime G_LastBar_TF = 0;

OrderBlock G_OB_Bull[2];
OrderBlock G_OB_Bear[2];
FVG        G_FVG_Bull[2];
FVG        G_FVG_Bear[2];

int    G_ObjCounter = 0;
double G_Point      = 0.0;
int    G_Digits     = 0;

//--- Colores escala de grises
color C_D1_Line    = C'30,30,30';      // Gris muy oscuro D1
color C_H1_Line    = C'90,90,90';      // Gris oscuro H1
color C_TF_Line    = C'150,150,150';   // Gris medio TF
color C_L3_Line    = C'100,100,180';   // Azul suave L3
color C_L4_Line    = C'180,100,100';   // Rojo suave L4
color C_EQ_Line    = C'180,180,180';   // Gris claro EQ
color C_D1_Zone    = C'210,210,210';   // Gris muy claro zona D1
color C_H1_Zone    = C'230,230,230';   // Gris casi blanco zona H1
color C_OB_Bull    = C'80,80,80';      // Gris oscuro OB alcista
color C_OB_Bear    = C'140,140,140';   // Gris medio OB bajista
color C_FVG_Bull   = C'110,110,110';   // Gris FVG alcista
color C_FVG_Bear   = C'170,170,170';   // Gris claro FVG bajista
color C_FVG_OB     = C'60,60,60';      // Gris muy oscuro FVG+OB
color C_Text_Dark  = C'30,30,30';      // Texto oscuro
color C_Text_Mid   = C'90,90,90';      // Texto medio

//+------------------------------------------------------------------+
//| SECCIÓN 6: OnInit()                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Trade.SetExpertMagicNumber(InpMagicNumber);
   Trade.SetDeviationInPoints(10);

   G_Point  = _Point;
   G_Digits = _Digits;

   if(!ValidateTimeInputs()) return(INIT_PARAMETERS_INCORRECT);

   DeleteAllSMCObjects();
   InitOBFVGArrays();

   if(!InitEngine(G_SE_D1, PERIOD_D1)) return(INIT_FAILED);
   if(!InitEngine(G_SE_H1, PERIOD_H1)) return(INIT_FAILED);
   if(!InitEngine(G_SE_TF, _Period))   return(INIT_FAILED);

   G_LastBar_D1 = (datetime)SeriesInfoInteger(_Symbol, PERIOD_D1, SERIES_LASTBAR_DATE);
   G_LastBar_H1 = (datetime)SeriesInfoInteger(_Symbol, PERIOD_H1, SERIES_LASTBAR_DATE);
   G_LastBar_TF = (datetime)SeriesInfoInteger(_Symbol, _Period,   SERIES_LASTBAR_DATE);

   ScanHistoricalOBs();
   ScanHistoricalFVGs();
   RenderAllVisuals();

   Print("=== SMC v4.03 iniciado ===");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| SECCIÓN 7: OnDeinit()                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   DeleteAllSMCObjects();
   Print("=== SMC detenido ===");
}

//+------------------------------------------------------------------+
//| SECCIÓN 8: OnTick()                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   double CurrentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(CurrentPrice <= 0.0) return;

   if(!IsWithinTradingHours())
   {
      DeletePendingOrders();
      return;
   }

   bool NewBar_D1 = CheckNewBar(PERIOD_D1, G_LastBar_D1);
   bool NewBar_H1 = CheckNewBar(PERIOD_H1, G_LastBar_H1);
   bool NewBar_TF = CheckNewBar(_Period,   G_LastBar_TF);

   if(NewBar_D1) UpdateEngineOnClose(G_SE_D1);
   if(NewBar_H1) UpdateEngineOnClose(G_SE_H1);
   if(NewBar_TF) UpdateEngineOnClose(G_SE_TF);

   //--- L1/L2/L3/L4 se actualizan al tick en todos los motores visuales
   UpdateEngineTick(G_SE_D1, CurrentPrice);
   UpdateEngineTick(G_SE_H1, CurrentPrice);
   UpdateEngineTick(G_SE_TF, CurrentPrice);

   if(NewBar_H1)
   {
      DetectNewOB_H1();
      DetectNewFVG_H1();
   }

   CheckOBInvalidation(CurrentPrice);
   CheckFVGCoverage(CurrentPrice);
   ExtendActiveZones();
   RenderAllVisuals();
}

//+------------------------------------------------------------------+
//| SECCIÓN 9: INICIALIZACIÓN DEL MOTOR                             |
//+------------------------------------------------------------------+
bool InitEngine(StructureEngine &SE, ENUM_TIMEFRAMES TF)
{
   SE.TF          = TF;
   SE.Valid       = false;
   SE.L1          = 0.0;
   SE.L2          = 0.0;
   SE.L3          = 0.0;
   SE.L4          = 0.0;
   SE.EQ          = 0.0;
   SE.L3L4_Active = false;
   SE.Bias        = BIAS_UNDEFINED;
   SE.Phase       = PHASE_CONTINUATION;

   double CurrentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(CurrentPrice <= 0.0) return(false);

   SE.L1 = CurrentPrice + 2.0 * G_Point;
   SE.L2 = CurrentPrice - 2.0 * G_Point;

   MqlRates Rates[];
   ArraySetAsSeries(Rates, true);
   int Copied = CopyRates(_Symbol, TF, 1, InpLookbackBars, Rates);
   if(Copied < 2) return(false);

   for(int i = 0; i < Copied; i++)
   {
      if(Rates[i].high > SE.L1) SE.L1 = Rates[i].high;
      if(Rates[i].low  < SE.L2) SE.L2 = Rates[i].low;
   }

   if(Rates[0].close > Rates[0].open) SE.Bias = BIAS_BULLISH;
   else if(Rates[0].close < Rates[0].open) SE.Bias = BIAS_BEARISH;

   SE.EQ    = SE.L2 + (SE.L1 - SE.L2) * 0.5;
   SE.Valid = true;

   if(InpShowLogs)
      Print("[Init][", EnumToString(TF), "] L1=", DoubleToString(SE.L1, G_Digits),
            " L2=", DoubleToString(SE.L2, G_Digits),
            " Bias=", EnumToString(SE.Bias));

   return(true);
}

//+------------------------------------------------------------------+
//| SECCIÓN 10: MOTOR DE ESTRUCTURA DE LÍNEAS                       |
//| L1 = tick más alto del rango; L2 = tick más bajo del rango.      |
//| En continuidad alcista solo sube L1; en continuidad bajista solo |
//| baja L2. L3/L4 se activan únicamente con una vela cerrada        |
//| contraria a la estructura, y desde ahí guardan máximos/mínimos   |
//| por tick (mechas incluidas). Cuando L3>L1 o L4<L2 se hace swap   |
//| inmediato: L1=L3, L2=L4 y L3/L4 desaparecen.                    |
//+------------------------------------------------------------------+
void UpdateStructureEQ(StructureEngine &SE)
{
   SE.EQ = SE.L2 + (SE.L1 - SE.L2) * 0.5;
}

void ClearStructureReaction(StructureEngine &SE)
{
   SE.L3          = 0.0;
   SE.L4          = 0.0;
   SE.L3L4_Active = false;
   SE.Phase       = PHASE_CONTINUATION;
}

int CommitStructureMove(StructureEngine &SE, int Dir)
{
   if(Dir == 0 || !SE.L3L4_Active) return(0);

   ENUM_STRUCTURE_BIAS OldBias = SE.Bias;
   ENUM_STRUCTURE_BIAS NewBias = BIAS_BULLISH;
   if(Dir < 0) NewBias = BIAS_BEARISH;

   SE.L1 = SE.L3;
   SE.L2 = SE.L4;
   if(SE.L1 < SE.L2)
   {
      double Tmp = SE.L1;
      SE.L1 = SE.L2;
      SE.L2 = Tmp;
   }

   SE.Bias = NewBias;
   UpdateStructureEQ(SE);
   ClearStructureReaction(SE);

   if(InpShowLogs)
   {
      string Tag = (OldBias != BIAS_UNDEFINED && OldBias != NewBias)
                   ? (Dir > 0 ? "[CHoCH BULL]" : "[CHoCH BEAR]")
                   : (Dir > 0 ? "[CONT BULL]"  : "[CONT BEAR]");
      Print(Tag,"[", EnumToString(SE.TF), "] L1=",
            DoubleToString(SE.L1, G_Digits),
            " L2=", DoubleToString(SE.L2, G_Digits));
   }

   return(Dir);
}

int LastBreakDirectionFromCandle(double O, double C, ENUM_STRUCTURE_BIAS CurrentBias)
{
   //--- Si solo tenemos OHLC y la misma vela toca ambos lados, se usa
   //    el sentido del cuerpo como último movimiento. Con ticks reales
   //    UpdateEngineTick procesa las rupturas en orden.
   if(C > O) return(+1);
   if(C < O) return(-1);
   if(CurrentBias == BIAS_BEARISH) return(+1);
   return(-1);
}

int CheckBreakAndCommit(StructureEngine &SE, double O, double C)
{
   if(!SE.Valid || !SE.L3L4_Active) return(0);

   bool BreakUp = (SE.L3 > SE.L1);  // L3 sobrepasa L1
   bool BreakDn = (SE.L4 < SE.L2);  // L4 sobrepasa L2 hacia abajo
   if(!BreakUp && !BreakDn) return(0);

   int Dir = 0;
   if(BreakUp && BreakDn) Dir = LastBreakDirectionFromCandle(O, C, SE.Bias);
   else if(BreakUp)       Dir = +1;
   else                   Dir = -1;

   return(CommitStructureMove(SE, Dir));
}

//+------------------------------------------------------------------+
//| ACTUALIZACIÓN AL CIERRE DE BARRA                                |
//+------------------------------------------------------------------+
void UpdateEngineOnClose(StructureEngine &SE)
{
   if(!SE.Valid) return;

   double ClosedOpen  = iOpen(_Symbol, SE.TF, 1);
   double ClosedClose = iClose(_Symbol, SE.TF, 1);
   double ClosedHigh  = iHigh(_Symbol, SE.TF, 1);
   double ClosedLow   = iLow(_Symbol, SE.TF, 1);
   if(ClosedOpen <= 0.0 || ClosedClose <= 0.0 ||
      ClosedHigh <= 0.0 || ClosedLow <= 0.0) return;

   bool ClosedGreen = (ClosedClose > ClosedOpen);
   bool ClosedRed   = (ClosedClose < ClosedOpen);

   if(SE.Bias == BIAS_UNDEFINED)
   {
      if(ClosedGreen) SE.Bias = BIAS_BULLISH;
      if(ClosedRed)   SE.Bias = BIAS_BEARISH;
      return;
   }

   //--- Si L3/L4 ya estaban activos, la vela cerrada también cuenta
   //    sus mechas dentro de la reacción.
   if(SE.L3L4_Active)
   {
      if(ClosedHigh > SE.L3) SE.L3 = ClosedHigh;
      if(ClosedLow  < SE.L4) SE.L4 = ClosedLow;
      if(CheckBreakAndCommit(SE, ClosedOpen, ClosedClose) == 0)
         SE.Phase = PHASE_REACTION;
      return;
   }

   //--- Reconstrucción de continuidad con la vela cerrada: antes de
   //    saber el color final, L1/L2 se mueven al tick.
   if(SE.Bias == BIAS_BULLISH)
   {
      if(ClosedHigh > SE.L1)
      {
         SE.L1 = ClosedHigh;
         UpdateStructureEQ(SE);
      }
   }
   else if(SE.Bias == BIAS_BEARISH)
   {
      if(ClosedLow < SE.L2)
      {
         SE.L2 = ClosedLow;
         UpdateStructureEQ(SE);
      }
   }

   //--- Activación de L3/L4 únicamente por cierre contrario.
   if(SE.Bias == BIAS_BULLISH && ClosedRed)
   {
      SE.L3L4_Active = true;
      SE.L3          = SE.L1;       // en alcista L3 inicia en L1
      SE.L4          = ClosedLow;   // L4 inicia en el mínimo de la vela contraria
      SE.Phase       = PHASE_REACTION;
      CheckBreakAndCommit(SE, ClosedOpen, ClosedClose);

      if(InpShowLogs && SE.L3L4_Active)
         Print("[L3/L4 BULL][", EnumToString(SE.TF),
               "] L3=", DoubleToString(SE.L3, G_Digits),
               " L4=", DoubleToString(SE.L4, G_Digits));
   }
   else if(SE.Bias == BIAS_BEARISH && ClosedGreen)
   {
      SE.L3L4_Active = true;
      SE.L3          = ClosedHigh;  // L3 inicia en el máximo de la vela contraria
      SE.L4          = SE.L2;       // en bajista L4 inicia en L2
      SE.Phase       = PHASE_REACTION;
      CheckBreakAndCommit(SE, ClosedOpen, ClosedClose);

      if(InpShowLogs && SE.L3L4_Active)
         Print("[L3/L4 BEAR][", EnumToString(SE.TF),
               "] L3=", DoubleToString(SE.L3, G_Digits),
               " L4=", DoubleToString(SE.L4, G_Digits));
   }
}

//+------------------------------------------------------------------+
//| SECCIÓN 11: ACTUALIZACIÓN TICK A TICK                           |
//+------------------------------------------------------------------+
void UpdateEngineTick(StructureEngine &SE, double Price)
{
   if(!SE.Valid || Price <= 0.0) return;
   if(SE.Bias == BIAS_UNDEFINED) return;

   if(SE.L3L4_Active)
   {
      if(Price > SE.L3) SE.L3 = Price;
      if(Price < SE.L4) SE.L4 = Price;
      CheckBreakAndCommit(SE, Price, Price);
      return;
   }

   if(SE.Bias == BIAS_BULLISH)
   {
      if(Price > SE.L1)
      {
         SE.L1 = Price;
         UpdateStructureEQ(SE);
      }
   }
   else if(SE.Bias == BIAS_BEARISH)
   {
      if(Price < SE.L2)
      {
         SE.L2 = Price;
         UpdateStructureEQ(SE);
      }
   }
}

//+------------------------------------------------------------------+
//| SECCIÓN 12: ORDER BLOCKS                                        |
//+------------------------------------------------------------------+
void InitOBFVGArrays()
{
   for(int i = 0; i < 2; i++)
   {
      G_OB_Bull[i].Active    = false;
      G_OB_Bull[i].ObjName   = "";
      G_OB_Bull[i].LabelName = "";
      G_OB_Bear[i].Active    = false;
      G_OB_Bear[i].ObjName   = "";
      G_OB_Bear[i].LabelName = "";
      G_FVG_Bull[i].Active    = false;
      G_FVG_Bull[i].ObjName   = "";
      G_FVG_Bull[i].LabelName = "";
      G_FVG_Bear[i].Active    = false;
      G_FVG_Bear[i].ObjName   = "";
      G_FVG_Bear[i].LabelName = "";
   }
}

void ScanHistoricalOBs()
{
   if(!G_SE_D1.Valid) return;
   int BullFound = 0, BearFound = 0;

   for(int i = 2; i <= 80 && (BullFound < 2 || BearFound < 2); i++)
   {
      double BarOpen  = iOpen(_Symbol, PERIOD_H1, i);
      double BarClose = iClose(_Symbol, PERIOD_H1, i);
      double BarHigh  = iHigh(_Symbol, PERIOD_H1, i);
      double BarLow   = iLow(_Symbol, PERIOD_H1, i);
      datetime BarTime = (datetime)iTime(_Symbol, PERIOD_H1, i);
      if(BarOpen <= 0.0 || BarClose <= 0.0) continue;

      bool IsGreen = (BarClose > BarOpen);
      bool IsRed   = (BarClose < BarOpen);

      if(IsRed && BullFound < 2 &&
         BarLow < G_SE_D1.EQ && BarLow > G_SE_D1.L2)
      {
         AddOB(G_OB_Bull, BullFound, BarHigh, BarLow, BarTime, true);
         BullFound++;
      }
      if(IsGreen && BearFound < 2 &&
         BarHigh > G_SE_D1.EQ && BarHigh < G_SE_D1.L1)
      {
         AddOB(G_OB_Bear, BearFound, BarHigh, BarLow, BarTime, false);
         BearFound++;
      }
   }
}

void DetectNewOB_H1()
{
   if(!G_SE_D1.Valid) return;

   double BarOpen  = iOpen(_Symbol, PERIOD_H1, 1);
   double BarClose = iClose(_Symbol, PERIOD_H1, 1);
   double BarHigh  = iHigh(_Symbol, PERIOD_H1, 1);
   double BarLow   = iLow(_Symbol, PERIOD_H1, 1);
   datetime BarTime = (datetime)iTime(_Symbol, PERIOD_H1, 1);
   if(BarOpen <= 0.0 || BarClose <= 0.0) return;

   bool IsGreen = (BarClose > BarOpen);
   bool IsRed   = (BarClose < BarOpen);

   if(IsRed && BarLow < G_SE_D1.EQ && BarLow > G_SE_D1.L2)
      AddOB(G_OB_Bull, GetAvailableOBSlot(G_OB_Bull),
            BarHigh, BarLow, BarTime, true);

   if(IsGreen && BarHigh > G_SE_D1.EQ && BarHigh < G_SE_D1.L1)
      AddOB(G_OB_Bear, GetAvailableOBSlot(G_OB_Bear),
            BarHigh, BarLow, BarTime, false);
}

int GetAvailableOBSlot(OrderBlock &OBArray[])
{
   for(int i = 0; i < 2; i++)
      if(!OBArray[i].Active) return(i);

   ObjectDelete(0, OBArray[1].ObjName);
   ObjectDelete(0, OBArray[1].LabelName);
   OBArray[1]           = OBArray[0];
   OBArray[0].Active    = false;
   OBArray[0].ObjName   = "";
   OBArray[0].LabelName = "";
   return(0);
}

void AddOB(OrderBlock &OBArray[], int Slot,
           double High, double Low, datetime TStart, bool IsBullish)
{
   G_ObjCounter++;
   string ObjName   = "OB_"  + IntegerToString(G_ObjCounter);
   string LabelName = "OBL_" + IntegerToString(G_ObjCounter);

   if(OBArray[Slot].ObjName != "")
   {
      ObjectDelete(0, OBArray[Slot].ObjName);
      ObjectDelete(0, OBArray[Slot].LabelName);
   }

   datetime TEnd = TimeCurrent() + PeriodSeconds(PERIOD_D1) * 10;

   OBArray[Slot].Active    = true;
   OBArray[Slot].High      = High;
   OBArray[Slot].Low       = Low;
   OBArray[Slot].TimeStart = TStart;
   OBArray[Slot].TimeEnd   = TEnd;
   OBArray[Slot].IsBullish = IsBullish;
   OBArray[Slot].ObjName   = ObjName;
   OBArray[Slot].LabelName = LabelName;

   color  OBColor = IsBullish ? C_OB_Bull : C_OB_Bear;
   string Label   = IsBullish ? "OB alcista" : "OB bajista";

   //--- Rectángulo del OB
   CreateFilledRect(ObjName, TStart, High, TEnd, Low, OBColor, 75);

   //--- Etiqueta centrada dentro del OB
   double   LabelPrice = Low + (High - Low) * 0.5;
   datetime LabelTime  = TStart + (long)(TEnd - TStart) / 2;
   CreateTextLabel(LabelName, LabelTime, LabelPrice, Label, C_Text_Dark, 8);
}

void CheckOBInvalidation(double Price)
{
   for(int i = 0; i < 2; i++)
   {
      if(G_OB_Bull[i].Active && Price < G_OB_Bull[i].Low)
      {
         ObjectDelete(0, G_OB_Bull[i].ObjName);
         ObjectDelete(0, G_OB_Bull[i].LabelName);
         G_OB_Bull[i].Active = false;
         G_OB_Bull[i].ObjName = ""; G_OB_Bull[i].LabelName = "";
      }
      if(G_OB_Bear[i].Active && Price > G_OB_Bear[i].High)
      {
         ObjectDelete(0, G_OB_Bear[i].ObjName);
         ObjectDelete(0, G_OB_Bear[i].LabelName);
         G_OB_Bear[i].Active = false;
         G_OB_Bear[i].ObjName = ""; G_OB_Bear[i].LabelName = "";
      }
   }
}

//+------------------------------------------------------------------+
//| SECCIÓN 13: FVGs                                                |
//+------------------------------------------------------------------+
void ScanHistoricalFVGs()
{
   if(!G_SE_D1.Valid) return;
   int BullFound = 0, BearFound = 0;

   for(int i = 3; i <= 80 && (BullFound < 2 || BearFound < 2); i++)
   {
      double O1 = iOpen(_Symbol, PERIOD_H1, i);
      double C1 = iClose(_Symbol, PERIOD_H1, i);
      double H1 = iHigh(_Symbol, PERIOD_H1, i);
      double L1 = iLow(_Symbol, PERIOD_H1, i);
      double O2 = iOpen(_Symbol, PERIOD_H1, i + 1);
      double C2 = iClose(_Symbol, PERIOD_H1, i + 1);
      datetime T1 = (datetime)iTime(_Symbol, PERIOD_H1, i);
      if(O1 <= 0.0 || O2 <= 0.0) continue;

      bool G1 = (C1 > O1), R1 = (C1 < O1);
      bool G2 = (C2 > O2), R2 = (C2 < O2);

      if(G1 && R2 && L1 > O2 && BullFound < 2 &&
         L1 < G_SE_D1.EQ && L1 > G_SE_D1.L2)
      {
         AddFVG(G_FVG_Bull, BullFound, H1, L1, T1, true,
                CheckNearbyOB(H1, L1, true));
         BullFound++;
      }
      if(R1 && G2 && H1 < O2 && BearFound < 2 &&
         H1 > G_SE_D1.EQ && H1 < G_SE_D1.L1)
      {
         AddFVG(G_FVG_Bear, BearFound, H1, L1, T1, false,
                CheckNearbyOB(H1, L1, false));
         BearFound++;
      }
   }
}

void DetectNewFVG_H1()
{
   if(!G_SE_D1.Valid) return;

   double O1 = iOpen(_Symbol, PERIOD_H1, 1);
   double C1 = iClose(_Symbol, PERIOD_H1, 1);
   double H1 = iHigh(_Symbol, PERIOD_H1, 1);
   double L1 = iLow(_Symbol, PERIOD_H1, 1);
   double O2 = iOpen(_Symbol, PERIOD_H1, 2);
   double C2 = iClose(_Symbol, PERIOD_H1, 2);
   datetime T1 = (datetime)iTime(_Symbol, PERIOD_H1, 1);
   if(O1 <= 0.0 || O2 <= 0.0) return;

   bool G1 = (C1 > O1), R1 = (C1 < O1);
   bool G2 = (C2 > O2), R2 = (C2 < O2);

   if(G1 && R2 && L1 > O2 && L1 < G_SE_D1.EQ && L1 > G_SE_D1.L2)
      AddFVG(G_FVG_Bull, GetAvailableFVGSlot(G_FVG_Bull),
             H1, L1, T1, true, CheckNearbyOB(H1, L1, true));

   if(R1 && G2 && H1 < O2 && H1 > G_SE_D1.EQ && H1 < G_SE_D1.L1)
      AddFVG(G_FVG_Bear, GetAvailableFVGSlot(G_FVG_Bear),
             H1, L1, T1, false, CheckNearbyOB(H1, L1, false));
}

int GetAvailableFVGSlot(FVG &FVGArray[])
{
   for(int i = 0; i < 2; i++)
      if(!FVGArray[i].Active) return(i);

   ObjectDelete(0, FVGArray[1].ObjName);
   ObjectDelete(0, FVGArray[1].LabelName);
   FVGArray[1]           = FVGArray[0];
   FVGArray[0].Active    = false;
   FVGArray[0].ObjName   = "";
   FVGArray[0].LabelName = "";
   return(0);
}

void AddFVG(FVG &FVGArray[], int Slot,
            double High, double Low, datetime TStart,
            bool IsBullish, bool HasOB)
{
   G_ObjCounter++;
   string ObjName   = "FVG_"  + IntegerToString(G_ObjCounter);
   string LabelName = "FVGL_" + IntegerToString(G_ObjCounter);

   if(FVGArray[Slot].ObjName != "")
   {
      ObjectDelete(0, FVGArray[Slot].ObjName);
      ObjectDelete(0, FVGArray[Slot].LabelName);
   }

   datetime TEnd = TimeCurrent() + PeriodSeconds(PERIOD_D1) * 10;

   FVGArray[Slot].Active    = true;
   FVGArray[Slot].High      = High;
   FVGArray[Slot].Low       = Low;
   FVGArray[Slot].TimeStart = TStart;
   FVGArray[Slot].TimeEnd   = TEnd;
   FVGArray[Slot].IsBullish = IsBullish;
   FVGArray[Slot].HasOB     = HasOB;
   FVGArray[Slot].ObjName   = ObjName;
   FVGArray[Slot].LabelName = LabelName;

   color  FVGColor = HasOB ? C_FVG_OB : (IsBullish ? C_FVG_Bull : C_FVG_Bear);
   string Label    = IsBullish ? "FVG alcista" : "FVG bajista";
   if(HasOB) Label = Label + " +OB";

   CreateFilledRect(ObjName, TStart, High, TEnd, Low, FVGColor, 70);

   double   LabelPrice = Low + (High - Low) * 0.5;
   datetime LabelTime  = TStart + (long)(TEnd - TStart) / 2;
   CreateTextLabel(LabelName, LabelTime, LabelPrice, Label, C_Text_Dark, 8);
}

bool CheckNearbyOB(double High, double Low, bool IsBullish)
{
   if(IsBullish)
   {
      for(int i = 0; i < 2; i++)
         if(G_OB_Bull[i].Active &&
            High >= G_OB_Bull[i].Low && Low <= G_OB_Bull[i].High)
            return(true);
   }
   else
   {
      for(int i = 0; i < 2; i++)
         if(G_OB_Bear[i].Active &&
            High >= G_OB_Bear[i].Low && Low <= G_OB_Bear[i].High)
            return(true);
   }
   return(false);
}

void CheckFVGCoverage(double Price)
{
   for(int i = 0; i < 2; i++)
   {
      if(G_FVG_Bull[i].Active && Price < G_FVG_Bull[i].Low)
      {
         ObjectDelete(0, G_FVG_Bull[i].ObjName);
         ObjectDelete(0, G_FVG_Bull[i].LabelName);
         G_FVG_Bull[i].Active = false;
         G_FVG_Bull[i].ObjName = ""; G_FVG_Bull[i].LabelName = "";
      }
      if(G_FVG_Bear[i].Active && Price > G_FVG_Bear[i].High)
      {
         ObjectDelete(0, G_FVG_Bear[i].ObjName);
         ObjectDelete(0, G_FVG_Bear[i].LabelName);
         G_FVG_Bear[i].Active = false;
         G_FVG_Bear[i].ObjName = ""; G_FVG_Bear[i].LabelName = "";
      }
   }
}

void ExtendActiveZones()
{
   datetime NewEnd = TimeCurrent() + PeriodSeconds(PERIOD_D1) * 10;

   for(int i = 0; i < 2; i++)
   {
      if(G_OB_Bull[i].Active)
      {
         G_OB_Bull[i].TimeEnd = NewEnd;
         ObjectSetInteger(0, G_OB_Bull[i].ObjName,   OBJPROP_TIME, 1, NewEnd);
         //--- Actualizar posicion de la etiqueta al centro del rect actualizado
         datetime LT = G_OB_Bull[i].TimeStart + (long)(NewEnd - G_OB_Bull[i].TimeStart) / 2;
         ObjectSetInteger(0, G_OB_Bull[i].LabelName, OBJPROP_TIME, 0, LT);
      }
      if(G_OB_Bear[i].Active)
      {
         G_OB_Bear[i].TimeEnd = NewEnd;
         ObjectSetInteger(0, G_OB_Bear[i].ObjName,   OBJPROP_TIME, 1, NewEnd);
         datetime LT = G_OB_Bear[i].TimeStart + (long)(NewEnd - G_OB_Bear[i].TimeStart) / 2;
         ObjectSetInteger(0, G_OB_Bear[i].LabelName, OBJPROP_TIME, 0, LT);
      }
      if(G_FVG_Bull[i].Active)
      {
         G_FVG_Bull[i].TimeEnd = NewEnd;
         ObjectSetInteger(0, G_FVG_Bull[i].ObjName,  OBJPROP_TIME, 1, NewEnd);
         datetime LT = G_FVG_Bull[i].TimeStart + (long)(NewEnd - G_FVG_Bull[i].TimeStart) / 2;
         ObjectSetInteger(0, G_FVG_Bull[i].LabelName, OBJPROP_TIME, 0, LT);
      }
      if(G_FVG_Bear[i].Active)
      {
         G_FVG_Bear[i].TimeEnd = NewEnd;
         ObjectSetInteger(0, G_FVG_Bear[i].ObjName,  OBJPROP_TIME, 1, NewEnd);
         datetime LT = G_FVG_Bear[i].TimeStart + (long)(NewEnd - G_FVG_Bear[i].TimeStart) / 2;
         ObjectSetInteger(0, G_FVG_Bear[i].LabelName, OBJPROP_TIME, 0, LT);
      }
   }
}

//+------------------------------------------------------------------+
//| SECCIÓN 14: RENDERIZADO VISUAL                                  |
//+------------------------------------------------------------------+
void RenderAllVisuals()
{
   //--- Rango visible del gráfico actual
   //    Usamos el tiempo de la primera y última barra visible
   datetime ChartFirstTime = (datetime)ChartGetInteger(0, CHART_FIRST_VISIBLE_BAR);
   int      VisibleBars    = (int)ChartGetInteger(0, CHART_VISIBLE_BARS);

   //--- Tiempo de inicio y fin del gráfico visible
   datetime T_Left  = (datetime)SeriesInfoInteger(_Symbol, _Period,
                       SERIES_FIRSTDATE);
   datetime T_Right = TimeCurrent() + PeriodSeconds(_Period) * 50;

   //--- Usar el rango completo visible para todos los rectángulos
   datetime ZoneStart = T_Left;
   datetime ZoneEnd   = T_Right;

   //------------------------------------------------------------------
   // D1 - Líneas gruesas + rectángulos ancho completo
   //------------------------------------------------------------------
   if(G_SE_D1.Valid)
   {
      //--- Líneas horizontales D1
      RenderHLine("D1_L1", G_SE_D1.L1, C_D1_Line, STYLE_SOLID, 3);
      RenderHLine("D1_L2", G_SE_D1.L2, C_D1_Line, STYLE_SOLID, 3);
      RenderHLine("D1_EQ", G_SE_D1.EQ, C_EQ_Line, STYLE_DOT,   1);

      //--- Zona Premium D1 (L1 → EQ) relleno gris muy claro
      CreateFilledRect("D1_Prem", ZoneStart, G_SE_D1.L1,
                       ZoneEnd, G_SE_D1.EQ, C_D1_Zone, 85);

      //--- Zona Discount D1 (EQ → L2) relleno gris muy claro
      CreateFilledRect("D1_Disc", ZoneStart, G_SE_D1.EQ,
                       ZoneEnd, G_SE_D1.L2, C_D1_Zone, 85);

      //--- Etiqueta PREMIUM D1 centrada en la zona
      double   PremMid  = G_SE_D1.EQ + (G_SE_D1.L1 - G_SE_D1.EQ) * 0.5;
      double   DiscMid  = G_SE_D1.L2 + (G_SE_D1.EQ - G_SE_D1.L2) * 0.5;
      datetime LblTime  = TimeCurrent();

      CreateTextLabel("D1_Lbl_P", LblTime, PremMid,
                      "D1 PREMIUM", C_Text_Dark, 9);
      CreateTextLabel("D1_Lbl_D", LblTime, DiscMid,
                      "D1 DISCOUNT", C_Text_Dark, 9);

      //--- L3/L4 de D1
      if(G_SE_D1.L3L4_Active && G_SE_D1.L3 > 0.0 && G_SE_D1.L4 > 0.0)
      {
         datetime T2_D1 = TimeCurrent() + PeriodSeconds(PERIOD_D1) * 3;
         RenderTrendLine("D1_L3",
                         G_LastBar_D1, G_SE_D1.L3, T2_D1, G_SE_D1.L3,
                         C_L3_Line, STYLE_DASH, 2);
         RenderTrendLine("D1_L4",
                         G_LastBar_D1, G_SE_D1.L4, T2_D1, G_SE_D1.L4,
                         C_L4_Line, STYLE_DASH, 2);
      }
      else
      {
         ObjectDelete(0, "D1_L3");
         ObjectDelete(0, "D1_L4");
      }
   }

   //------------------------------------------------------------------
   // H1 - Líneas medianas + rectángulos ancho completo
   //------------------------------------------------------------------
   if(G_SE_H1.Valid)
   {
      RenderHLine("H1_L1", G_SE_H1.L1, C_H1_Line, STYLE_SOLID, 2);
      RenderHLine("H1_L2", G_SE_H1.L2, C_H1_Line, STYLE_SOLID, 2);
      RenderHLine("H1_EQ", G_SE_H1.EQ, C_EQ_Line, STYLE_DOT,   1);

      //--- Zona Premium H1 (más transparente que D1)
      CreateFilledRect("H1_Prem", ZoneStart, G_SE_H1.L1,
                       ZoneEnd, G_SE_H1.EQ, C_H1_Zone, 90);

      //--- Zona Discount H1
      CreateFilledRect("H1_Disc", ZoneStart, G_SE_H1.EQ,
                       ZoneEnd, G_SE_H1.L2, C_H1_Zone, 90);

      //--- Etiquetas H1
      double   PremMidH1 = G_SE_H1.EQ + (G_SE_H1.L1 - G_SE_H1.EQ) * 0.5;
      double   DiscMidH1 = G_SE_H1.L2 + (G_SE_H1.EQ - G_SE_H1.L2) * 0.5;
      datetime LblTimeH1 = TimeCurrent() + PeriodSeconds(_Period) * 5;

      CreateTextLabel("H1_Lbl_P", LblTimeH1, PremMidH1,
                      "H1 PREMIUM", C_Text_Mid, 8);
      CreateTextLabel("H1_Lbl_D", LblTimeH1, DiscMidH1,
                      "H1 DISCOUNT", C_Text_Mid, 8);

      //--- L3/L4 de H1
      if(G_SE_H1.L3L4_Active && G_SE_H1.L3 > 0.0 && G_SE_H1.L4 > 0.0)
      {
         datetime T2_H1 = TimeCurrent() + PeriodSeconds(PERIOD_H1) * 5;
         RenderTrendLine("H1_L3",
                         G_LastBar_H1, G_SE_H1.L3, T2_H1, G_SE_H1.L3,
                         C_L3_Line, STYLE_DASH, 2);
         RenderTrendLine("H1_L4",
                         G_LastBar_H1, G_SE_H1.L4, T2_H1, G_SE_H1.L4,
                         C_L4_Line, STYLE_DASH, 2);
      }
      else
      {
         ObjectDelete(0, "H1_L3");
         ObjectDelete(0, "H1_L4");
      }
   }

   //------------------------------------------------------------------
   // TF - Solo líneas, sin rectángulos de fondo
   //------------------------------------------------------------------
   if(G_SE_TF.Valid)
   {
      RenderHLine("TF_L1", G_SE_TF.L1, C_TF_Line, STYLE_SOLID, 1);
      RenderHLine("TF_L2", G_SE_TF.L2, C_TF_Line, STYLE_SOLID, 1);
      RenderHLine("TF_EQ", G_SE_TF.EQ, C_EQ_Line, STYLE_DOT,   1);

      //--- L3/L4 de TF
      if(G_SE_TF.L3L4_Active && G_SE_TF.L3 > 0.0 && G_SE_TF.L4 > 0.0)
      {
         datetime T2_TF = TimeCurrent() + PeriodSeconds(_Period) * 30;
         RenderTrendLine("TF_L3",
                         G_LastBar_TF, G_SE_TF.L3, T2_TF, G_SE_TF.L3,
                         C_L3_Line, STYLE_DASH, 1);
         RenderTrendLine("TF_L4",
                         G_LastBar_TF, G_SE_TF.L4, T2_TF, G_SE_TF.L4,
                         C_L4_Line, STYLE_DASH, 1);
      }
      else
      {
         ObjectDelete(0, "TF_L3");
         ObjectDelete(0, "TF_L4");
      }
   }

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| SECCIÓN 15: FUNCIONES DE OBJETOS GRÁFICOS                      |
//+------------------------------------------------------------------+
void RenderHLine(string Name, double Price, color Color,
                 ENUM_LINE_STYLE Style, int Width)
{
   if(Price <= 0.0) return;
   if(ObjectFind(0, Name) < 0)
   {
      ObjectCreate(0, Name, OBJ_HLINE, 0, 0, Price);
      ObjectSetInteger(0, Name, OBJPROP_COLOR,      Color);
      ObjectSetInteger(0, Name, OBJPROP_STYLE,      Style);
      ObjectSetInteger(0, Name, OBJPROP_WIDTH,      Width);
      ObjectSetInteger(0, Name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, Name, OBJPROP_HIDDEN,     true);
   }
   else
   {
      ObjectSetDouble (0, Name, OBJPROP_PRICE, Price);
      ObjectSetInteger(0, Name, OBJPROP_COLOR, Color);
      ObjectSetInteger(0, Name, OBJPROP_STYLE, Style);
      ObjectSetInteger(0, Name, OBJPROP_WIDTH, Width);
   }
}

void RenderTrendLine(string Name, datetime T1, double P1,
                     datetime T2, double P2,
                     color Color, ENUM_LINE_STYLE Style, int Width)
{
   if(T1 <= 0 || T2 <= 0 || P1 <= 0.0 || P2 <= 0.0) return;
   if(ObjectFind(0, Name) < 0)
   {
      ObjectCreate(0, Name, OBJ_TREND, 0, T1, P1, T2, P2);
      ObjectSetInteger(0, Name, OBJPROP_COLOR,      Color);
      ObjectSetInteger(0, Name, OBJPROP_STYLE,      Style);
      ObjectSetInteger(0, Name, OBJPROP_WIDTH,      Width);
      ObjectSetInteger(0, Name, OBJPROP_RAY_RIGHT,  false);
      ObjectSetInteger(0, Name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, Name, OBJPROP_HIDDEN,     true);
   }
   else
   {
      ObjectSetInteger(0, Name, OBJPROP_TIME,  0, T1);
      ObjectSetDouble (0, Name, OBJPROP_PRICE, 0, P1);
      ObjectSetInteger(0, Name, OBJPROP_TIME,  1, T2);
      ObjectSetDouble (0, Name, OBJPROP_PRICE, 1, P2);
      ObjectSetInteger(0, Name, OBJPROP_COLOR, Color);
   }
}

void CreateFilledRect(string Name, datetime T1, double P1,
                      datetime T2, double P2,
                      color Color, int Transparency)
{
   if(P1 <= 0.0 || P2 <= 0.0 || T1 <= 0 || T2 <= 0) return;
   double   Top    = MathMax(P1, P2);
   double   Bottom = MathMin(P1, P2);
   datetime TLeft  = (datetime)MathMin((long)T1, (long)T2);
   datetime TRight = (datetime)MathMax((long)T1, (long)T2);
   uchar    Alpha  = (uchar)(255 - (Transparency * 255 / 100));
   color    CARGB  = (color)ColorToARGB(Color, Alpha);

   if(ObjectFind(0, Name) < 0)
   {
      if(!ObjectCreate(0, Name, OBJ_RECTANGLE, 0, TLeft, Top, TRight, Bottom))
         return;
      ObjectSetInteger(0, Name, OBJPROP_COLOR,      CARGB);
      ObjectSetInteger(0, Name, OBJPROP_BGCOLOR,    CARGB);
      ObjectSetInteger(0, Name, OBJPROP_FILL,       true);
      ObjectSetInteger(0, Name, OBJPROP_BACK,       true);
      ObjectSetInteger(0, Name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, Name, OBJPROP_HIDDEN,     true);
      ObjectSetInteger(0, Name, OBJPROP_WIDTH,      1);
   }
   else
   {
      ObjectSetInteger(0, Name, OBJPROP_TIME,   0, TLeft);
      ObjectSetDouble (0, Name, OBJPROP_PRICE,  0, Top);
      ObjectSetInteger(0, Name, OBJPROP_TIME,   1, TRight);
      ObjectSetDouble (0, Name, OBJPROP_PRICE,  1, Bottom);
      ObjectSetInteger(0, Name, OBJPROP_COLOR,   CARGB);
      ObjectSetInteger(0, Name, OBJPROP_BGCOLOR, CARGB);
   }
}

void CreateTextLabel(string Name, datetime Time, double Price,
                     string Text, color TextColor, int FontSize)
{
   if(Time <= 0 || Price <= 0.0) return;
   if(ObjectFind(0, Name) < 0)
   {
      ObjectCreate(0, Name, OBJ_TEXT, 0, Time, Price);
      ObjectSetString (0, Name, OBJPROP_TEXT,       Text);
      ObjectSetInteger(0, Name, OBJPROP_COLOR,      TextColor);
      ObjectSetInteger(0, Name, OBJPROP_FONTSIZE,   FontSize);
      ObjectSetString (0, Name, OBJPROP_FONT,       "Arial Bold");
      ObjectSetInteger(0, Name, OBJPROP_BACK,       false);
      ObjectSetInteger(0, Name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, Name, OBJPROP_HIDDEN,     true);
   }
   else
   {
      ObjectSetString (0, Name, OBJPROP_TEXT,  Text);
      ObjectSetInteger(0, Name, OBJPROP_COLOR, TextColor);
      ObjectSetInteger(0, Name, OBJPROP_FONTSIZE, FontSize);
      ObjectSetDouble (0, Name, OBJPROP_PRICE, Price);
      ObjectSetInteger(0, Name, OBJPROP_TIME,  0, Time);
   }
}

//+------------------------------------------------------------------+
//| SECCIÓN 16: FUNCIONES AUXILIARES                                |
//+------------------------------------------------------------------+
bool CheckNewBar(ENUM_TIMEFRAMES TF, datetime &LastBarTime)
{
   datetime Current = (datetime)SeriesInfoInteger(_Symbol, TF, SERIES_LASTBAR_DATE);
   if(Current != LastBarTime) { LastBarTime = Current; return(true); }
   return(false);
}

bool IsWithinTradingHours()
{
   MqlDateTime T;
   TimeToStruct(TimeCurrent(), T);
   int Now   = T.hour * 60 + T.min;
   int Start = InpStartHour * 60 + InpStartMinute;
   int End   = InpEndHour   * 60 + InpEndMinute;
   return(Now >= Start && Now < End);
}

void DeletePendingOrders()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong Ticket = OrderGetTicket(i);
      if(Ticket == 0) continue;
      if(OrderGetString(ORDER_SYMBOL)  != _Symbol)        continue;
      if(OrderGetInteger(ORDER_MAGIC)  != InpMagicNumber) continue;
      long OType = OrderGetInteger(ORDER_TYPE);
      if(OType == ORDER_TYPE_BUY_LIMIT || OType == ORDER_TYPE_SELL_LIMIT)
         Trade.OrderDelete(Ticket);
   }
}

bool ValidateTimeInputs()
{
   if(InpStartHour < 0   || InpStartHour > 23)   return(false);
   if(InpEndHour < 0     || InpEndHour > 23)      return(false);
   if(InpStartMinute < 0 || InpStartMinute > 59)  return(false);
   if(InpEndMinute < 0   || InpEndMinute > 59)    return(false);
   return(InpStartHour * 60 + InpStartMinute <
          InpEndHour   * 60 + InpEndMinute);
}

void DeleteAllSMCObjects()
{
   string Fixed[] = {
      "D1_L1","D1_L2","D1_L3","D1_L4","D1_EQ",
      "D1_Prem","D1_Disc","D1_Lbl_P","D1_Lbl_D",
      "H1_L1","H1_L2","H1_L3","H1_L4","H1_EQ",
      "H1_Prem","H1_Disc","H1_Lbl_P","H1_Lbl_D",
      "TF_L1","TF_L2","TF_L3","TF_L4","TF_EQ"
   };
   for(int i = 0; i < ArraySize(Fixed); i++)
      ObjectDelete(0, Fixed[i]);

   for(int i = 0; i < 2; i++)
   {
      ObjectDelete(0, G_OB_Bull[i].ObjName);
      ObjectDelete(0, G_OB_Bull[i].LabelName);
      ObjectDelete(0, G_OB_Bear[i].ObjName);
      ObjectDelete(0, G_OB_Bear[i].LabelName);
      ObjectDelete(0, G_FVG_Bull[i].ObjName);
      ObjectDelete(0, G_FVG_Bull[i].LabelName);
      ObjectDelete(0, G_FVG_Bear[i].ObjName);
      ObjectDelete(0, G_FVG_Bear[i].LabelName);
   }

   int Total = ObjectsTotal(0);
   for(int i = Total - 1; i >= 0; i--)
   {
      string N = ObjectName(0, i);
      if(StringFind(N, "OB_")   == 0 || StringFind(N, "OBL_")  == 0 ||
         StringFind(N, "FVG_")  == 0 || StringFind(N, "FVGL_") == 0)
         ObjectDelete(0, N);
   }
   ChartRedraw(0);
}
//+------------------------------------------------------------------+
//| FIN DEL ARCHIVO                                                  |
//+------------------------------------------------------------------+