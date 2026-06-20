<p align="center">
  <img src="assets/cover.png" alt="slide-maker — design, redesign &amp; critique presentation-grade decks" width="100%">
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <b>Español</b>
</p>

# slide-maker

> **Crea, rediseña y evalúa presentaciones `.pptx` con calidad profesional** — para cualquier audiencia, en cualquier idioma, con o sin plantilla o material de origen.

La mayoría de las herramientas de IA crean diapositivas igual que generan texto: de una sola pasada, a partir de una suposición y sin *mirar* nunca lo que produjeron. **En cambio, slide-maker trabaja como un diseñador de presentaciones experimentado.** Pregunta qué necesitas realmente, se mantiene rigurosamente fiel a tu material de origen y se niega a dar una presentación por "terminada" hasta que un *crítico independiente* haya revisado las diapositivas renderizadas. Lo que recibes es un archivo PowerPoint real y editable que te pertenece — no una captura de pantalla ni una aplicación web que te deja atrapado.

Una sola convicción guía cada decisión: **una diapositiva es un apoyo visual para quien expone, no un documento para leer** — así que todo se optimiza para que se *entienda en segundos*.

---

## Por qué es diferente

Tres disciplinas discretas la separan de las formas habituales de hacer diapositivas:

- **Entrevista antes de construir.** Propósito, audiencia, fuente, estilo, idioma — todo se recoge desde el principio, nunca se da por supuesto. Se acabaron las presentaciones que responden con seguridad a la pregunta equivocada.
- **No puede inventar tu trabajo.** Cada cifra, afirmación y figura debe poder rastrearse hasta tu material de origen; la única excepción — el contenido prospectivo — se señala explícitamente como un añadido del propio modelo. Una audiencia experta detecta al instante un resultado inventado, así que no los inventa.
- **Revisa sus propios píxeles — con un segundo par de ojos.** `python-pptx` escribe a ciegas: los errores de desbordamiento, contraste y glifos solo aparecen una vez renderizados. Por eso cada presentación se renderiza como imágenes y un **subagente crítico independiente debe dar su consentimiento** antes de la entrega. Quien construye no califica su propia tarea.

### slide-maker frente a las formas habituales de hacer diapositivas

<sub>✓ sí&nbsp;&nbsp;·&nbsp;&nbsp;~ parcial / depende&nbsp;&nbsp;·&nbsp;&nbsp;✗ no</sub>

| Lo que obtienes | Prompt de IA de una sola pasada | Herramientas web de diapositivas | A mano (PPT / `python-pptx`) | **slide-maker** |
|---|:--:|:--:|:--:|:--:|
| Pregunta tu objetivo y tu audiencia *antes* de construir | ✗ | ~ | ✓ | **✓** |
| Se mantiene fiel a tu fuente — sin cifras inventadas | ~ | ~ | ✓ | **✓** |
| Usa las propias figuras de tu fuente — recortadas automáticamente del PDF, no redibujadas | ✗ | ✗ | ~ | **✓** |
| Un crítico independiente revisa las diapositivas **renderizadas** | ✗ | ✗ | ✗ | **✓** |
| Diseño ajustado al *propósito* (defensa ≠ pitch ≠ clase) | ~ | ~ | ✓ | **✓** |
| Un `.pptx` real y editable que te pertenece — sin ataduras | ~ | ~ | ✓ | **✓** |
| Cualquier idioma — incl. CJK y tipografía real de ecuaciones | ~ | ~ | ✓ | **✓** |
| Construcción reproducible + reedición segura | ✗ | ~ | ✓ | **✓** |
| Rapidez hasta una presentación *pulida* | ~ | ✓ | ✗ | **✓** |

Las demás opciones también pueden hacer diapositivas. slide-maker es la única que **pregunta, se mantiene fiel y verifica el resultado** — y aun así te entrega un archivo que te pertenece por completo.

---

## Cómo funciona — un único bucle disciplinado

> **Entrevistar → Comprender → Construir → Renderizar y criticar ⟲ → Entregar**

Cada presentación recorre siete pasos (`SKILL.md` es la especificación de referencia):

| Paso | Qué ocurre | Por qué existe |
|---|---|---|
| **0 — Entrevista** | Un único lote de `AskUserQuestion`: plantilla, propósito y audiencia, material de origen, estilo. (+seguimientos: sede de la conferencia, nueva plantilla.) | Los requisitos del usuario son la fuente de la verdad; los *aprendes*, nunca los heredas de una presentación anterior. |
| **1 — Comprender** | Lee todo el material a fondo; redacta un **resumen de comprensión** (mensaje en una frase, aportaciones, esencia del método, para qué sirve cada figura/tabla, limitaciones). | Una presentación que se ve bien pero malinterpreta el trabajo no engaña a ningún experto. La fidelidad empieza aquí. |
| **2 — Lienzo** | Decide la carpeta de salida (`~/Downloads/<deck>/`), carga la plantilla *o* diseña un aspecto adecuado al propósito; fija paleta/fuentes (incl. CJK `EAFONT`). | La identidad de marca vive en los diseños; el diseño debe señalar el *tipo* de documento correcto antes de leer una sola palabra. |
| **3 — Planificar** | El número de diapositivas se ajusta al tiempo disponible (~1/min): charla corta ~6–9, charla más larga/clase/defensa/job-talk ~10–20+. Una idea por diapositiva, con la conclusión primero, y un arco moldeado al propósito; ~15+ → despliegue por secciones (paso 4). | Corregir un guion es barato; corregir una presentación terminada es caro. |
| **4 — Construir** | Un único script de construcción con los ayudantes de `deckkit`. Figuras de origen completas, márgenes, acentos rotativos, ecuaciones reales, un solo idioma, builds/animación con propósito (se evalúa cada diapositiva; la mayoría permanece estática, animando solo donde un build ayude a la comprensión), notas del orador. | python-pptx es rápido; una sola ejecución del script, un autor coherente. |
| **5 — Renderizar + bucle del crítico** | Renderiza a PNGs y *mira*; luego un **subagente crítico independiente** devuelve JSON (consentimiento / revisar + correcciones por diapositiva). Repite hasta obtener el consentimiento. | python-pptx escribe a ciegas — los errores de desbordamiento/contraste/glifos solo se ven en los píxeles. Tú no juzgas tu propio trabajo. |
| **6 — Entregar + iterar** | Muestra el resultado al usuario, le da la ruta de la carpeta, le explica la editabilidad + los dos carriles de cambios e incorpora su feedback. | La presentación es suya, para conservarla y seguir ajustándola — con seguridad. |

**El bucle actor–crítico es el motor de calidad.** Su *intensidad* se ajusta a lo que está en juego — un crítico para una reunión de laboratorio, un panel de 2 o 3 críticos con enfoques distintos para una conferencia, una defensa o un pitch — pero el bucle en sí nunca se omite.

### Dos modos

- **Automático (por defecto):** entrevista → construcción → bucle del crítico hasta un listón alto → mostrar. El crítico captura la *calidad*.
- **Colaborativo (opcional):** añade **puntos de aprobación** económicos — elige una *dirección* entre opciones reales ya renderizadas → aprueba el *guion* → construye el resto. Los puntos de aprobación capturan la *preferencia* (el gusto), algo que un crítico no puede leer. Al diseñar desde cero, te muestra **3 direcciones distintas** — más una opción de *"describe la tuya"* — para elegir antes de comprometerse.

---

## Lo que puede hacer

- **Construir a partir de cualquier cosa — o de nada.** Un artículo, un código base, un documento o diapositivas existentes → una presentación. ¿No tienes material? Redacta a partir de su experiencia y **busca en la web para fundamentar y verificar** cada afirmación.
- **Usa tus figuras reales, con precisión.** Extrae las propias figuras de la fuente **directamente del artículo/PDF** — detectadas automáticamente por el pie de figura y recortadas a la extensión real de la figura (leyenda y ejes intactos), mostradas *enteras* en lugar de redibujadas o cortadas. Las cuadrículas de comparación densas pueden reensamblarse para mostrar solo las columnas que importan; los recortes dudosos se señalan para que les eches un vistazo.
- **Rediseñar tu presentación actual.** Primero diagnostica, confirma el alcance y luego reconstruye reutilizando tu contenido y tus figuras — nunca un reemplazo silencioso desde cero.
- **Reproducir un aspecto que te guste.** Pásale un ejemplo y reproduce el *estilo* — retícula, paleta, tipografía, motivos — en su propia construcción.
- **Hablar el idioma de tu audiencia.** Cualquier idioma, mantenido con coherencia de principio a fin, con **tipografía CJK** correcta y **ecuaciones reales con calidad LaTeX**.
- **Respetar la sede.** Para una charla de conferencia, identifica e investiga la sede — formato, relación de aspecto, plantilla oficial, audiencia — antes de construir.
- **Escalar a presentaciones grandes.** Más de 15 diapositivas → despliegue opcional por secciones con un estilo compartido, autoría en paralelo y un panel de críticos.
- **Entregar de forma limpia.** Una carpeta autocontenida, notas del orador, animación con propósito y un script de construcción reproducible para que puedas seguir editando con seguridad.

---

## Pruébalo

slide-maker es una **Agent Skill** — se ejecuta en Claude Code y en otros entornos compatibles con Agent Skills. No ejecutas comandos para usarla; simplemente **se lo pides**, y la skill toma el control (empezando por la entrevista).

```bash
# 1. Instalación (se muestra la ruta de Claude Code; sirve cualquier entorno de Agent Skills)
git clone https://github.com/dong845/slides_maker ~/.claude/skills/slide-maker

# 2. Comprobación única de la cadena de herramientas (python-pptx, LibreOffice, matplotlib, …)
bash ~/.claude/skills/slide-maker/scripts/check_env.sh
```

Luego simplemente pídeselo a tu agente:

> *"Crea una charla de conferencia de 12 minutos a partir de paper.pdf."*
> *"Mi presentación es demasiado densa — rediséñala."*
> *"Una clase sobre modelos de difusión, en 中文 — limpia y con muchos diagramas."*
> *"Convierte este repositorio en un pitch para inversores."*

Tu presentación terminada aparece en `~/Downloads/<deck-name>/` — el `.pptx`, una carpeta `render/` con los PNG de las diapositivas y el script de construcción que la generó.

---

## Qué ruta sigue tu solicitud

La entrevista (paso 0, especialmente la P3) encamina la solicitud:

| El usuario quiere… | Ruta |
|---|---|
| Una presentación a partir de su código/artículo/documento | Ruta de construcción (pasos 1–6), rama de contenido |
| Una presentación sin material | Ruta de construcción; redactar a partir de la experiencia + búsqueda web para fundamentar, confirmar el guion |
| **Mejorar su propia** presentación | **Ruta de rediseño** — diagnosticar primero, confirmar el alcance, reconstruir reutilizando su contenido/figuras (`references/redesign-existing-deck.md`) |
| Una presentación **con el aspecto de un ejemplo** | Imitación de estilo — redactar un resumen de estilo, reproducir el aspecto (`references/style-analysis.md`) |
| Una charla de **conferencia** | Identificar e investigar la sede en la web (reglas, plantilla, audiencia) y luego construir para ella |
| Un **póster** | Acotado: un único lienzo grande; las reglas de oficio siguen vigentes, pero la skill está afinada para charlas — confirmar la especificación primero |
| Una presentación **en otro idioma / CJK** | Fijar `EAFONT`, disciplina de un solo idioma, tipografía CJK (`references/multilingual.md`) |
| Una presentación **grande** (más de 15 diapositivas) | Despliegue opcional por secciones: `style.py` compartido, autores de sección en paralelo, `assemble.py`, panel de críticos (`references/large-deck-orchestration.md`) |
| **Ver opciones primero** | Puntos de aprobación del modo colaborativo |
| **Cambios tras la entrega** | Iterar con seguridad — nunca sobrescribir las ediciones hechas a mano (`references/handoff-and-iteration.md`) |

---

## Principios de diseño integrados en la skill

1. **Los requisitos por encima de los artefactos.** Una plantilla, una presentación antigua o el gusto del modelo son *entradas*, no instrucciones. Cuando entran en conflicto con el requisito declarado, gana el requisito.
2. **Fidelidad estricta.** Cada afirmación/cifra/figura se rastrea hasta la fuente. La única excepción es el contenido prospectivo, claramente señalado.
3. **Crítica independiente.** Un agente distinto juzga los píxeles renderizados — su independencia es lo que hace que el "consentimiento" signifique algo.
4. **Paralelizar la recopilación, nunca la comprensión.** Despliega la lectura y la preparación de recursos; una sola mente sostiene el hilo conductor.
5. **Diseño ajustado al propósito.** Una defensa, un informe ejecutivo y una clase no deberían parecerse.
6. **Un solo idioma, mantenido de principio a fin.**
7. **El script es la fuente de la verdad; el `.pptx` es un artefacto.** Reproducible y seguro para iterar sin perder las ediciones del usuario.

---

## Cadena de herramientas

`python-pptx`, `pymupdf` (renderizado + extracción de figuras), `matplotlib` + `Pillow` (ecuaciones/gráficos/recorte de figuras) y LibreOffice (`soffice`) para el renderizado. Ejecuta `bash scripts/check_env.sh` una vez en una máquina nueva; imprime la corrección exacta para cualquier cosa que falte.

<details>
<summary><b>Mapa del repositorio</b> (para colaboradores)</summary>

**Columna vertebral**
- `SKILL.md` — las instrucciones de funcionamiento que sigue el modelo (pasos 0–6, las reglas).

**Motor (`scripts/`)**
- `deckkit.py` — el kit de construcción: ayudantes de texto/formas/componentes (`bullet`, `callout`, `chip`, `arrow`, `modbox`, `hrule`), ayudantes de maquetación/imagen (`columns` para paneles divididos de igual ancho, `picture`), ecuaciones (`eq_par`, `equation_png`), `speaker_notes`, comprobación de contraste, paleta/fuentes (incl. CJK `EAFONT`), reutilización de plantillas (`open_template`, `content_slide`) y el armazón sin plantilla (`blank_deck`, `title_bar`, `footer`). Impórtalo; no vuelvas a derivar las primitivas.
- `render_deck.sh` — `.pptx` → un PNG por diapositiva (LibreOffice → PDF → PNG). Multiplataforma; usa un perfil privado de LibreOffice para que los renderizados paralelos o simultáneos no colisionen.
- `check_env.sh` — verificación previa única de la cadena de herramientas.
- `anim.py` — inyecta el XML de temporización de builds/animación de PowerPoint que python-pptx no puede escribir.
- `assemble.py` — combina módulos de sección creados en paralelo en una sola presentación (sin fusiones frágiles).
- `archetypes.py` — construye las mismas diapositivas de previsualización por dirección para el punto de aprobación colaborativo.
- `inspect_template.py` — imprime los diseños/marcadores de posición/logos de una plantilla.
- `extract_pdf.py` — detecta y recorta figuras con precisión *de* un PDF de origen: `figures`/`figure`/`autofig` **detectan y recortan automáticamente las figuras del artículo** (ancladas al pie de figura + ajuste al contenido, con comprobaciones de validez), además de la extracción manual por página/región/imagen incrustada.
- `crop_helper.py` — opera sobre una imagen *mirando, no adivinando*: `grid` (superposición de regla), `crop`/`--snap`, `trim` (ajuste al contenido; elimina el fondo sin recortar una leyenda/eje, con fondo claro u oscuro), `panel` (reensambla las columnas/filas elegidas de una cuadrícula de comparación densa).
- `extract_deck.py` — extrae texto/tablas/figuras *de* una presentación existente (rediseño + reconciliación).
- `export_notes.py` — exporta las notas del orador de una presentación a un guion de ensayo en texto plano.

**Juicio**
- `agents/critic.md` — el briefing del crítico independiente + el esquema JSON.
- `references/review-rubrics.md` — rúbrica universal + superposiciones por propósito (fundamentadas en investigación).
- `references/design-principles.md` — el oficio y el "porqué".

**Referencias por escenario**
- `design-by-purpose.md` · `animation.md` · `multilingual.md` · `font-guidance.md` · `style-analysis.md` · `redesign-existing-deck.md` · `collaborative-mode.md` · `large-deck-orchestration.md` · `handoff-and-iteration.md`
- `examples/` — script de construcción resuelto, la convención de estilo compartido + módulo de sección.

**Externo (no forma parte de la skill)**
- `~/.claude/slide-templates/` — el registro personal de plantillas del usuario; léelo para tomar decisiones y escribe en él los nuevos perfiles. Vacío para un usuario nuevo.

</details>
