---
tipo: guia
tags: [machine-learning, fraud-detection, threshold, shap, lime, eu-ai-act]
fecha: 03-11-26
objetivo: Guiar a estudiantes sin formación en programación por el laboratorio de umbral de fraude, paso a paso, con comandos de terminal.
---

# Laboratorio Clase 4 · Tú decides el umbral

**Módulo II – Navegando por los componentes de la IA · Sesión 4**

Hoy vas a ponerte en el rol de líder de negocio frente a un modelo de **detección de fraude**. El modelo ya está entrenado: entrega, para cada transacción, una **probabilidad de fraude**. Tu trabajo es decidir **desde qué probabilidad se bloquea la tarjeta** (el *umbral*) y entender qué significa eso en clientes y en pesos.

**No necesitas saber programar.** Solo vas a ejecutar comandos en la terminal y leer los resultados.

### Cómo usar este proyecto
1. En la carpeta del proyecto, ejecuta `uv sync` una vez.
2. Ejecuta cada paso con `uv run fraude <paso>`. Cada sección indica su comando.
3. Si prefieres, ejecuta `uv run fraude todo` y luego lee la salida de arriba hacia abajo.
4. Los gráficos quedan en la carpeta `salidas/`.

> Los datos son **sintéticos** (inventados con fines docentes). Ninguna persona real está en este laboratorio.

## Paso 1 · Preparar las herramientas
Una **librería** es un paquete de código que otras personas ya escribieron. La cargamos para no programar todo desde cero. Por ejemplo, `pandas` maneja tablas, `matplotlib` dibuja gráficos y `scikit-learn` entrena modelos. Más adelante, `shap` reparte el crédito de una predicción y `lime` intenta contar esa misma predicción con una regla simple.

El comando `uv sync` instala las librerías que usaremos. Se ejecuta una sola vez.

## Paso 2 · Los datos: 20.000 transacciones de un banco ficticio
Los datos son **sintéticos**: el propio proyecto los genera al azar, siguiendo reglas parecidas a las de un fraude real. Usamos una **semilla** (el número 42): un valor fijo que hace que el azar se repita igual. Así, todos en la sala verán exactamente los mismos números.

Cada fila es una compra con tarjeta. Las columnas son las pistas que usa el modelo:

| Columna | Qué significa |
|---|---|
| `monto_clp` | Monto de la compra en pesos |
| `hora_del_dia` | Hora de la compra (0 a 23) |
| `distancia_km` | Distancia entre el lugar de la compra y el domicilio del cliente |
| `intentos_fallidos_24h` | Intentos fallidos con la tarjeta en las últimas 24 horas |
| `antiguedad_cliente_meses` | Hace cuántos meses es cliente |
| `compra_internacional` | 1 si la compra es en el extranjero |
| `comercio_nuevo` | 1 si el cliente nunca había comprado en ese comercio |
| `es_fraude` | La respuesta real: 1 = fraude, 0 = compra legítima |

Las siete primeras columnas son las **variables**: la información que el modelo observa. La última, `es_fraude`, es la **etiqueta**: la respuesta correcta que el modelo intenta adivinar.

Ejecuta `uv run fraude datos` y fíjate en el resultado: solo cerca del 2% de las transacciones es fraude. Cuando un caso es así de raro, decimos que los datos están **desbalanceados**. Esto será clave en el Paso 4.

## Paso 3 · El equipo técnico entrena el modelo
Un **modelo de Machine Learning** (ML, aprendizaje automático) es un programa que aprende patrones a partir de ejemplos, en vez de seguir reglas escritas a mano. Aquí aprende qué combinaciones de variables suelen acompañar a un fraude.

**Entrenar** es mostrarle al modelo transacciones junto con su respuesta (`es_fraude`) para que encuentre esos patrones. **Evaluar** es probarlo con transacciones que nunca vio y comparar lo que predice con la realidad. Comando: `uv run fraude entrenar`. Separamos los datos en dos mitades: una para entrenar y otra para evaluar. Evaluar con los mismos ejemplos del entrenamiento sería como tomar una prueba cuyas respuestas ya conoces.

Usamos **Gradient Boosting**, un tipo de modelo que combina cientos de **árboles de decisión** pequeños. Cada árbol es una serie de preguntas simples, como *¿la compra es de madrugada?* o *¿el monto supera cierto valor?*. Cada árbol nuevo corrige los errores de los anteriores.

El modelo no responde *sí* o *no*. Para cada transacción entrega una **probabilidad de fraude**, un número entre 0 y 1. Por ejemplo, 0.85 equivale a 85% de probabilidad (Python usa punto decimal, no coma).

## Paso 4 · La trampa de la "exactitud"
La **exactitud** (en inglés, *accuracy*) es el porcentaje de transacciones en que el modelo acierta, sumando fraudes y compras legítimas. Parece la medida natural, pero tiene una trampa cuando el fraude es raro.

Un modelo con 90% de exactitud se equivoca en el 10% restante. La pregunta clave es: *¿qué tipo de error estamos cometiendo en ese 10%?* Ejecuta `uv run fraude exactitud` y mira lo que logra un "modelo" tramposo que responde siempre *no es fraude*.

## Antes de decidir: cinco conceptos clave
Necesitas estos cinco conceptos para leer el panel del Paso 5.

### 1. Umbral
El modelo entrega una probabilidad, pero el banco debe tomar una acción: bloquear la tarjeta o no. El **umbral** es el punto de corte. Con umbral 0.30, se bloquea toda transacción con probabilidad de fraude igual o mayor a 30%. Un umbral bajo bloquea más tarjetas; un umbral alto bloquea menos.

### 2. Los cuatro resultados posibles
Al comparar la decisión con la realidad, cada transacción cae en una de cuatro casillas. Esta tabla se llama **matriz de confusión**.

| | Era fraude | Era legítima |
|---|---|---|
| **Bloqueamos** | **VP**, verdadero positivo: fraude atrapado | **FP**, falso positivo: cliente bueno bloqueado (falsa alarma) |
| **No bloqueamos** | **FN**, falso negativo: fraude que se escapó | **VN**, verdadero negativo: cliente bueno sin molestia |

*Positivo* significa que el modelo dio la alarma de fraude. *Verdadero* o *falso* indica si esa decisión fue correcta.

### 3. Precisión
De todas las alarmas que dimos, ¿qué porcentaje era fraude de verdad?

**Precisión = VP / (VP + FP)**

Ejemplo: bloqueamos 100 tarjetas y 60 eran fraude. La precisión es 60%. Una precisión baja significa muchas falsas alarmas y muchos clientes molestos.

### 4. Recall
De todos los fraudes que ocurrieron, ¿qué porcentaje atrapamos?

**Recall = VP / (VP + FN)**

Ejemplo: hubo 200 fraudes y atrapamos 150. El recall es 75%. Un recall bajo significa que se escapa mucho fraude. En español también se llama **sensibilidad**; usamos *recall* porque es el término habitual en la industria.

### 5. El tira y afloja, y el costo
Bajar el umbral sube el recall (atrapamos más fraude), pero baja la precisión (damos más falsas alarmas). Subir el umbral hace lo contrario. Ningún umbral mejora todo a la vez. Para elegir, le ponemos precio a cada tipo de error:

**Costo total = (fraudes que se escaparon × costo de un fraude) + (clientes buenos bloqueados × costo de una falsa alarma)**

En este ejercicio, los aciertos (VP y VN) no tienen costo.

## Paso 5 · Tú decides
Ejecuta `uv run fraude panel` con distintos valores y observa qué pasa. Ejemplo: `uv run fraude panel --umbral 0.20 --costo-fraude 300000 --costo-falsa-alarma 15000`.

- **`--umbral`**: desde qué probabilidad bloqueamos la tarjeta. Bajo = bloqueamos más; alto = bloqueamos menos.
- **`--costo-fraude`**: lo que pierde el banco cuando un fraude se escapa (un FN).
- **`--costo-falsa-alarma`**: llamada al cliente, cliente molesto, compra perdida (un FP).

**Cómo leer el resultado.** Las cuatro primeras líneas son las casillas de la matriz de confusión: fraudes atrapados (VP), fraudes que se escaparon (FN), clientes buenos bloqueados (FP) y clientes buenos sin molestia (VN). Debajo aparecen la precisión, el recall y la exactitud, calculados con esas cuatro cifras.

**Cómo leer el gráfico** (`salidas/paso5_costo_por_umbral.png`). El eje horizontal es el umbral; el eje vertical es el costo total en millones de pesos. La curva azul muestra el costo de cada umbral posible. La línea roja es tu elección. La línea verde punteada marca el umbral más barato.

## Paso 6 · ¿Qué umbral conviene más?
Comparemos dos criterios: el umbral que da **mayor exactitud** y el que da **menor costo para el negocio**. El comando `uv run fraude comparar` prueba los 99 umbrales posibles (de 0.01 a 0.99) y elige el mejor según cada criterio.

**Cómo leer la tabla.** Cada columna es un umbral candidato. Compara sobre todo el recall, los fraudes que se escaparon y el costo total. Puedes cambiar los costos con `--costo-fraude` y `--costo-falsa-alarma`.

## Paso 7 · Abrir la caja negra con SHAP
Un modelo como Gradient Boosting combina cientos de árboles. Nadie puede leer su lógica completa a simple vista; por eso decimos que es una **caja negra**. Esto es un problema cuando hay que justificar una decisión ante un cliente o una autoridad. La **explicabilidad** busca responder *¿por qué el modelo decidió esto?*

**SHAP** (*SHapley Additive exPlanations*, explicaciones aditivas de Shapley) es un método de explicabilidad. Toma una sola predicción y calcula cuánto subió o bajó la probabilidad de fraude cada variable del cliente. Se basa en los **valores de Shapley**, una idea de teoría de juegos para repartir un resultado de forma justa entre varios participantes.

Elegimos a un **cliente bueno que el modelo bloqueó** (un falso positivo, FP) y le preguntamos al modelo *¿por qué?* Comando: `uv run fraude shap`. Tarda unos segundos. El gráfico queda en `salidas/paso7_shap_waterfall.png`.

Cómo leer el gráfico:
- Parte abajo en **E[f(x)]**: la probabilidad promedio de fraude que el modelo asigna a una transacción típica. Es el punto de partida.
- Cada barra **roja** empuja la probabilidad hacia arriba (más sospechoso); cada barra **azul** la baja. El número de la barra indica cuánto empuja.
- Arriba, **f(x)** es la probabilidad final que dio el modelo para este cliente: el punto de partida más todas las barras.

Esa cuenta responde cuánto crédito recibe cada variable frente al promedio. No responde si una regla corta, armada solo con casos parecidos a este cliente, cuenta la misma decisión. Esa segunda pregunta está en el Paso 8. Con Shapley solo, el bloqueo no queda justificado.

## Paso 8 · La misma decisión con LIME

El gráfico SHAP del Paso 7 responde una pregunta concreta. Toma la diferencia entre la probabilidad promedio y la probabilidad de este cliente, y reparte esa diferencia entre las variables. Los valores de Shapley cierran la cuenta: el punto de partida más las barras es la probabilidad del modelo. Por eso el gráfico se ve completo.

Esa cuenta no basta para defender el bloqueo.

El reparto depende del fondo de comparación. En el Paso 7 ese fondo es una muestra de 100 transacciones de entrenamiento. Otra muestra mueve las barras. El crédito de una variable es crédito frente a ese fondo.

El reparto pone un número por variable y los suma. El modelo puede estar reaccionando a una combinación, por ejemplo madrugada junto con compra internacional y varios intentos fallidos. Un número por variable no muestra la combinación. Aun así, la suma cierra, y la cuenta puede verse terminada aunque la razón sea conjunta.

Además, SHAP en este laboratorio mira por dentro del modelo. `TreeExplainer` usa la estructura de los árboles. Un cliente y un regulador piden otra cosa: una frase que se pueda leer en voz alta, válida para casos parecidos a este, y que no exija abrir la caja negra.

**LIME** (*Local Interpretable Model-agnostic Explanations*) construye esa frase.

- *Local*: la explicación vale para este cliente y su vecindario, no para todo el banco.
- *Interpretable*: la explicación es una regla corta.
- *Model-agnostic*: LIME no mira por dentro del modelo. Le basta con pedirle probabilidades. Sirve para Gradient Boosting y para cualquier otro modelo que entregue probabilidades.

El procedimiento, sobre el mismo cliente del Paso 7:

1. Crea miles de transacciones parecidas a este cliente. Cambia un poco cada variable. Ese conjunto es el **vecindario**.
2. Pide al modelo la probabilidad de fraude de cada transacción del vecindario.
3. Ajusta una **regresión lineal**. Las transacciones más cercanas al cliente pesan más. Las lejanas pesan menos.
4. Traduce cada coeficiente a una regla, por ejemplo `hora_del_dia <= 6` o `compra_internacional=1`.

Esa recta es un modelo chico. Intenta imitar al modelo grande solo en este vecindario. Hay que medir si la imitación alcanza.

### Cómo leer el resultado

Comando: `uv run fraude lime`. El comando imprime dos probabilidades. La primera es la del modelo. La segunda es la de la recta, para este mismo cliente. Al lado va el **R² ponderado**: qué tan bien la recta imita al modelo dentro del vecindario. En ese cálculo pesan más las transacciones parecidas a este cliente. Cerca de 1, la imitación es buena. Cerca de 0, la recta no explica más que un promedio.

Con la semilla de este laboratorio las dos probabilidades quedan lejos y el R² queda bajo. Eso no es un error del comando. Una regla lineal corta no reproduce esta decisión. Las barras de LIME, entonces, no alcanzan para justificar el bloqueo.

El gráfico usa los mismos colores que SHAP. La barra **roja** empuja hacia fraude. La barra **azul** empuja hacia compra legítima. El número de la barra es el coeficiente de la recta. Sumar las barras no devuelve la probabilidad del modelo. La librería LIME, en su gráfico por defecto, pinta los colores al revés. Por eso el gráfico lo dibuja el proyecto, en `salidas/paso8_lime.png`.

La tabla final pone lado a lado el signo de SHAP y el signo de LIME. Mismo signo quiere decir que ambos ven la variable empujando hacia el mismo lado. El orden puede cambiar. En esta semilla, SHAP asigna el mayor aporte a `intentos_fallidos_24h`. LIME asigna el mayor peso a la regla `compra_internacional=1`. Las dos lecturas pueden ser correctas a la vez, porque cada método hace una pregunta distinta. Ninguna de las dos es, por sí sola, la causa del bloqueo.

LIME también tiene límites. El vecindario depende de cuántas transacciones se inventan y de la semilla. Los rangos, como `monto_clp > 53000`, salen de cortar la variable en tramos, y el corte se ve más nítido de lo que es el modelo. Un R² bajo no dice que el bloqueo esté mal. Dice que esta explicación simple no alcanza para sostenerlo.

## Para la puesta en común
Anota tus respuestas; las conversaremos en la sala.

1. **¿Qué umbral minimizó el costo?** ¿Cuánto fraude se escapó y a cuántos clientes buenos bloqueaste?
2. **¿Por qué el umbral de mayor exactitud no es el de menor costo?**
3. **Con el gráfico SHAP y el gráfico LIME del mismo cliente, ¿defenderías el bloqueo ante el cliente o ante un regulador?** Mira dos cosas: si el orden de las variables coincide, y si la recta de LIME reproduce la probabilidad del modelo. (El **regulador** es la autoridad que supervisa a los bancos. En Chile es la CMF, Comisión para el Mercado Financiero.)
4. **Bonus:** sube el costo de la falsa alarma a $60.000 (cliente premium), con `uv run fraude comparar --costo-falsa-alarma 60000`. ¿Hacia dónde se mueve el mejor umbral? ¿Qué te dice eso sobre quién debe fijar el umbral: el equipo técnico o el negocio?

> Idea fuerza: el umbral **no es una decisión técnica**; es la traducción del **apetito de riesgo** del negocio, es decir, cuánto riesgo está dispuesta a aceptar la empresa para lograr sus objetivos.

El Paso 9 cierra esta decisión con un expediente: la finalidad del sistema, una persona responsable y un texto claro para el cliente.

## Paso 9 · Cumplir con el expediente de la decisión

Los gráficos de SHAP y de LIME no cumplen el Reglamento (UE) 2024/1689, la ley europea de inteligencia artificial. Cumplir, para esta decisión, tiene dos capas. La primera mantiene el sistema dentro de su finalidad. La segunda cierra el bloqueo con un texto que una persona pueda leer, corregir y discutir.

### Capa 1 · Quedarse en la finalidad prevista

El Anexo III, punto 5(b), clasifica como de alto riesgo a los sistemas que evalúan la solvencia de una persona natural o que fijan su puntaje de crédito. El mismo punto exceptúa a los sistemas usados para detectar fraude financiero.

Este laboratorio tiene una sola finalidad prevista: estimar si una transacción con tarjeta parece fraude y proponer un bloqueo provisorio. No evalúa si el cliente puede pagar un crédito. No fija un puntaje de crédito. No pone precio a un seguro de vida o de salud. No decide el acceso a vivienda, electricidad ni telecomunicaciones.

Esa frase queda escrita en el expediente. Si el banco usa después el mismo puntaje para negar un crédito, la excepción termina y el sistema entra al régimen de alto riesgo. En ese régimen importan, entre otros, el artículo 13 (información para que el responsable del despliegue interprete la salida), el artículo 14 (supervisión humana) y el artículo 86.

El artículo 86 da a la persona afectada, ante un sistema de alto riesgo del Anexo III, un derecho a explicaciones claras y significativas sobre el papel del sistema en la decisión y sobre los elementos principales de esa decisión. El derecho nace cuando la decisión produce efectos jurídicos o afecta de forma significativa su salud, seguridad o derechos fundamentales. Mientras este modelo se use solo para detectar fraude, ese artículo no es la norma que cierra el caso. El laboratorio igual usa ese estándar, porque bloquear la tarjeta afecta a la persona y porque es la manera de explicar la salida a quien despliega el sistema.

El **responsable del despliegue** es quien usa el sistema en su actividad, aquí el banco. El **proveedor** es quien lo desarrolla. El cliente es la **persona afectada**.

### Capa 2 · Cerrar el bloqueo con cinco reglas

1. Separar la probabilidad del modelo y el umbral del negocio. El modelo estima. El negocio fija desde qué probabilidad hay bloqueo.
2. Contar como elementos principales solo las variables en que SHAP y LIME empujan hacia el mismo lado. Dejar fuera las casi nulas. No nombrar una variable como la causa: en esta semilla los métodos no coinciden en cuál pesa más.
3. Medir si la recta local reproduce la probabilidad. La institución fija una barra. En este laboratorio la barra es 0,70 de R² ponderado. Bajo esa barra, el puntaje no cierra solo un bloqueo que perjudica al cliente.
4. Exigir una persona con autoridad para mantener o levantar el bloqueo. Si lo mantiene, declara que revisó los hechos de la transacción. Sin esa declaración, el expediente queda abierto.
5. Escribir un texto para el cliente con la finalidad del sistema, el corte del negocio, los hechos que puede corregir, el límite de la explicación simple, la decisión de la persona y la vía para pedir otra revisión.

Comando: `uv run fraude expediente`. Usa al mismo cliente de los pasos 7 y 8. Cuatro opciones le corresponden a una persona, no al modelo: `--decision` (`mantener` o `levantar`), `--revisor`, `--sin-revision` (la persona no declaró haber revisado los hechos) y `--fidelidad-minima` (la barra de la institución). Ejemplo: `uv run fraude expediente --decision mantener --sin-revision`.

Con la fidelidad de esta semilla, bajo la barra de 0,70, el procedimiento levanta el bloqueo provisorio. El puntaje queda como alerta, no como última palabra.

Esto es un procedimiento de aula. No es una evaluación de conformidad ni un dictamen jurídico.
