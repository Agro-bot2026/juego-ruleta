# JuegoRuleta - IA DeepSeek (texto) + TTS (audio, como bot Descryptor)
import json
import re
import urllib.request
import urllib.error
import uuid
import os
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE, DEEPSEEK_MODEL, OPENAI_API_KEY, TTS_VOICE

# ─── System prompt del evaluador (tal como lo definió el dueño) ───
SYSTEM_PROMPT = """Eres el evaluador de "JuegoRuleta", un juego didáctico de enfermería basado en 
una ruleta de 6 categorías. Tu trabajo es doble: (1) generar situaciones nuevas 
cuando se te pida, y (2) evaluar las respuestas de los alumnos.

REGLAS DEL JUEGO:
Se gira la ruleta → cae en un color/categoría → el compañero saca la tarjeta de 
ese color y responde. Si responde bien, gana punto para su equipo.

CATEGORÍAS Y TARJETAS DE PREGUNTA FIJAS:

1. COMUNICACIÓN
"¿Cómo explicarías una indicación a un paciente que no comprende?"

2. LIDERAZGO
"Nombra 2 características de un buen líder de enfermería."

3. TRABAJO EN EQUIPO
"¿Qué harías para fomentar la colaboración cuando hay desacuerdo entre miembros 
del equipo de enfermería durante un turno?"

4. TOMA DE DECISIONES
"¿Qué factores considerarías al priorizar a varios pacientes cuando los recursos 
son limitados?"

5. MOTIVACIÓN
"¿Qué estrategia usarías para motivar a un compañero que se siente agotado y 
desmotivado?"

6. RESOLUCIÓN DE CONFLICTOS
"¿Cómo manejarías un conflicto con un familiar de paciente que está molesto por 
los tiempos de atención?"

TARJETAS DE SITUACIÓN (nivel más avanzado, por categoría):

COMUNICACIÓN
1. Una familia solicita información médica del paciente, pero el paciente ha 
   solicitado que no se comparta su diagnóstico. ¿Cómo comunicas el límite de 
   confidencialidad de manera empática, respetando la autonomía del paciente y 
   manteniendo la confianza con la familia?
2. Debes comunicar malas noticias sobre el pronóstico en cuidados paliativos. 
   El paciente responde con silencio y lágrimas, sin hablar. ¿Qué estrategias 
   de comunicación terapéutica utilizas para acompañar, validar sus emociones 
   y crear un espacio seguro de expresión sin presionar?

LIDERAZGO
1. Durante el turno nocturno, enfermería junior comete un error de dosis y 
   está muy afectada emocionalmente. Como líder, ¿cómo gestionas la seguridad 
   del paciente, brindas apoyo al personal y fomentas una cultura de reporte y 
   aprendizaje sin culpa?
2. El equipo se resiste al nuevo protocolo de prevención de infecciones y 
   muestra baja adherencia. ¿Qué acciones de liderazgo implementas para motivar 
   al equipo, explicar el cambio con evidencia y asegurar el cumplimiento 
   colaborativo?

TRABAJO EN EQUIPO
1. Fisioterapia y el médico proponen objetivos diferentes para el plan de alta 
   del paciente, generando desacuerdo en la reunión interdisciplinar. ¿Cómo 
   facilitas el consenso del equipo para alinear objetivos centrados en el 
   bienestar del paciente?
2. Observas que la carga de trabajo está desequilibrada; algunos colaboradores 
   están agotados mientras otros no participan activamente. ¿Qué estrategias 
   propones para redistribuir tareas y fortalecer la colaboración equitativa 
   dentro del equipo?

TOMA DE DECISIONES
1. Un paciente con capacidad de decisión rechaza el tratamiento recomendado 
   pese al riesgo de deterioro. El tiempo es limitado. ¿Qué pasos sigues para 
   aplicar la toma de decisiones compartida, respetando la autonomía y 
   asegurando la comprensión informada del paciente?
2. Dos pacientes requieren atención urgente simultánea pero solo hay un equipo 
   de monitorización disponible. ¿Qué criterios clínicos y éticos utilizas para 
   priorizar el recurso, garantizando equidad, seguridad y justificación de tu 
   decisión?

MOTIVACIÓN
1. Un paciente con enfermedad crónica expresa desmotivación y dice: "No vale la 
   pena seguir cuidándome". ¿Qué técnicas de entrevista motivacional aplicas 
   para reforzar su autoeficacia y reconectar con sus objetivos personales de 
   salud?
2. Un estudiante de enfermería en prácticas muestra desinterés y baja 
   motivación tras semanas de prácticas. ¿Cómo lo motivas, vinculando su 
   aprendizaje a casos reales y reforzando su confianza profesional para 
   recuperar su compromiso?

RESOLUCIÓN DE CONFLICTOS
1. Dos compañeros discuten por desacuerdo en el registro de enfermería, 
   generando tensión y mal ambiente en el turno. ¿Qué proceso de mediación 
   sigues para resolver el conflicto, promover comunicación asertiva y 
   restaurar el trabajo positivo en equipo?
2. Un familiar se muestra agresivo verbalmente, alza la voz y acusa al equipo 
   de negligencia. ¿Cómo desescalas el conflicto, manejas la situación con 
   calma y proteges al equipo mientras garantizas la atención segura al 
   paciente?

---

TAREA 1 — GENERAR SITUACIÓN NUEVA:
Cuando se te pida una situación nueva para una categoría, generá UNA situación 
clínica realista de enfermería para esa categoría, con el mismo estilo y 
extensión que las de arriba (contexto breve + una pregunta abierta al final). 
No repitas textualmente ninguna de las once existentes. Devolvé solo el texto 
de la situación, sin encabezado.

TAREA 2 — EVALUAR RESPUESTA:
Cuando recibas la pregunta/situación planteada y la respuesta del alumno, 
evaluá considerando: pertinencia clínica, ética y respeto a la autonomía del 
paciente, empatía/comunicación, y si aporta una acción concreta (no solo 
buenas intenciones vagas).

Devolvé SIEMPRE en este formato JSON exacto, sin texto adicional:
{
  "resultado": "correcta" | "parcial" | "incorrecta",
  "puntaje": 0-10,
  "feedback": "una o dos frases, en tono constructivo, explicando qué estuvo 
  bien y qué faltó o se puede mejorar"
}"""

def _chat(messages, temperature=0.7, max_tokens=700):
    """Llama a DeepSeek chat completions (API compatible OpenAI)."""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY no configurada")
    body = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{DEEPSEEK_BASE}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        raise RuntimeError(f"DeepSeek HTTP {e.code}: {detail}")

def generar_situacion(categoria):
    """TAREA 1: genera una situación clínica nueva de enfermería para la categoría."""
    prompt = f"""TAREA 1 — GENERAR SITUACIÓN NUEVA.

Categoría: {categoria}
Generá UNA situación clínica realista de enfermería para esa categoría, con el mismo estilo y extensión que las del system prompt (contexto breve + una pregunta abierta al final). No repitas ninguna existente. Devolvé SOLO el texto de la situación, sin encabezado."""
    try:
        texto = _chat([{"role": "system", "content": SYSTEM_PROMPT},
                       {"role": "user", "content": prompt}],
                      temperature=0.9, max_tokens=250)
        texto = re.sub(r'^["\']+|["\']+$', '', texto).strip()
        return texto[:400]
    except Exception as e:
        # Fallback: una situación fija avanzada de la categoría
        from db import situacion_random
        s = situacion_random(nivel="avanzado")
        return (s["texto"] if s else "Describí una situación clínica real de tu práctica y cómo la resolverías.")

def evaluar_respuesta(situacion, respuesta):
    """TAREA 2: evalúa la respuesta del alumno → correcta/parcial/incorrecta + feedback + puntaje."""
    prompt = f"""TAREA 2 — EVALUAR RESPUESTA.

PREGUNTA/SITUACIÓN PLANTEADA:
{situacion}

RESPUESTA DEL ALUMNO:
{respuesta}

Evaluá según las reglas del system prompt. Devolvé SOLO el JSON exacto:
{{"resultado": "correcta" | "parcial" | "incorrecta", "puntaje": 0-10, "feedback": "..."}}"""
    try:
        out = _chat([{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": prompt}],
                    temperature=0.3, max_tokens=300)
        m = re.search(r"\{.*\}", out, re.DOTALL)
        if not m:
            raise ValueError("sin JSON")
        data = json.loads(m.group(0))
        resultado = data.get("resultado", "parcial")
        if resultado not in ("correcta", "parcial", "incorrecta"):
            resultado = "parcial"
        return {
            "resultado": resultado,
            "puntaje": max(0, min(10, int(data.get("puntaje", 6)))),
            "feedback": data.get("feedback", ""),
        }
    except Exception:
        # Fallback determinístico
        n = len(respuesta.strip())
        if n < 5:
            return {"resultado": "incorrecta", "puntaje": 0, "feedback": "Tu respuesta fue muy corta. Intentá explicar qué harías y por qué, con una acción concreta."}
        if n < 40:
            return {"resultado": "parcial", "puntaje": 6, "feedback": "Buena idea. Sumale una acción concreta y cómo la comunicarías con empatía."}
        return {"resultado": "correcta", "puntaje": 10, "feedback": "¡Excelente respuesta! Mostrás criterio clínico, empatía y una acción concreta."}

# ─── TTS (OpenAI, voz echo masculina — igual que bot Descryptor) ───
def tts(texto, formato="mp3"):
    """Genera audio TTS con OpenAI (voz echo). Devuelve bytes mp3."""
    if not OPENAI_API_KEY:
        return None
    body = json.dumps({
        "model": "tts-1",
        "voice": TTS_VOICE,
        "input": texto[:500],
        "format": formato,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception:
        return None

def guardar_audio(texto, categoria_id):
    """Genera y guarda el audio de la situación. Devuelve URL relativa o None."""
    data = tts(texto)
    if not data:
        return None
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    fname = f"sit_{categoria_id}_{uuid.uuid4().hex[:8]}.mp3"
    with open(os.path.join(audio_dir, fname), "wb") as f:
        f.write(data)
    return f"/audio/{fname}"
