# Índice — todas las versiones 8.37 del EA

La cadena de desarrollo de la **v8.37** dejó **15 versiones distintas del EA** (además de 3 merges que no cambian el código). Cada una está extraída **byte a byte** del commit indicado (la hora es la del commit, convertida a Bogotá): el `.mq5` (LF, listo para MetaEditor) y el `.txt` (tal cual estaba el `ea.txt` histórico en ese commit, con CRLF).

| # | Commit | Fecha | **Hora de commit (Bogotá UTC−5)** | PR | Commit / cambio |
|---|---|---|---|---|---|
| V01 | `338c0fb` | 2026-08-30 | **2026-08-30 03:16:02** | PR #8 (main) | v8.37: gestión de riesgo de Asistente 3 con nivel POR PAR |
| V02 | `aa74e0f` | 2026-08-30 | **2026-08-30 03:25:40** | PR #9 | Fix compilación MQL5: arrays por referencia en MPDrawTable + limpiar 4 warnings (ACCOUNT_MARGIN_FREE, casts long->int, check OrderSend, ternaria booleana) |
| V03 | `1a60ec4` | 2026-08-30 | **2026-08-30 03:55:44** | PR #9 | NIVEL por par: con estrategia LIVE solo cuentan operaciones reales de la cuenta |
| V04 | `54d68aa` | 2026-08-30 | **2026-08-30 04:07:41** | PR #9 | Cierre semanal viernes: 30 min antes del cierre, pérdida=SL / ganancia=nivel intacto |
| V05 | `0345127` | 2026-08-30 | **2026-08-30 04:27:41** | PR #10 | Contar nivel solo con operaciones reales |
| V06 | `1efe843` | 2026-08-30 | **2026-08-30 04:36:05** | PR #10 | Ignorar cierres virtuales en contadores |
| V07 | `11356d2` | 2026-08-30 | **2026-08-30 04:39:54** | PR #10 | No mostrar posiciones virtuales en panel |
| V08 | `404986a` | 2026-08-30 | **2026-08-30 04:46:02** | PR #10 | Limitar a una posición abierta por par |
| V09 | `ce7d02b` | 2026-08-30 | **2026-08-30 04:57:44** | PR #10 | Permitir entradas reales sin fase virtual |
| V10 | `ade2196` | 2026-08-30 | **2026-08-30 05:03:56** | PR #10 | Agregar modo configurable virtual a LIVE |
| V11 | `ae4a7a0` | 2026-08-30 | **2026-08-30 12:18:17** | PR #10 | Clasificar correctamente cierres con SL protegido |
| V12 | `399c1c7` | 2026-08-30 | **2026-08-30 12:45:42** | PR #10 | Asegurar que el SL real incremente el nivel |
| V13 | `8983980` | 2026-08-30 | **2026-08-30 13:00:52** | PR #10 | Reforzar conteo de cierres y ampliar panel |
| V14 | `4ed7f16` | 2026-08-30 | **2026-08-30 13:31:27** | PR #10 | Reforzar trailing y hacer visible contador NTV |
| V15 | `52dae62` | 2026-08-30 | **2026-08-30 13:33:11** | PR #10 | Procesar TP real tambien en modo directo |

## Orden de uso recomendado

- **V15** (`52dae62`, merge PR #10 `b9df22f`) = **la v8.37 final**, y es exactamente la que ya estaba guardada en raíz como `trabajador INICIAL v8.37.mq5` / `ea INICIAL v8.37.txt` (el estado del repo al iniciar este chat). Usa esta si quieres **la 8.37 definitiva**.
- **V01** (`338c0fb`) = la primera v8.37 en `main` (gestión de Asistente 3 con nivel POR PAR).
- V02–V04 = mejoras aplicadas sobre V01 (PR #9): fix de compilación, nivel por par con solo operaciones reales y cierre semanal.
- V05–V15 = mejoras de PR #10: conteo solo con operaciones reales, omisión de cierres virtuales en contadores, una posición por par, fase virtual configurable, clasificación de SL protegido, trailing reforzado y TP real en modo directo.

> Nota: los tres merges (`516a60f` PR #8, `fb03f84` PR #9, `b9df22f` PR #10) no introducen EA nuevo — heredan el árbol de su rama, así que sus `.mq5` son idénticos a V01 (PR #8), V04 (PR #9) y V15 (PR #10) respectivamente.

La siguiente versión tras la serie 8.37 es la **v8.38** (`104251f`, 3 modos de capital base), guardada en raíz como `trabajador v8.38 CAPITAL 3MODOS.mq5`.
