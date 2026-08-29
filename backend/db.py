# JuegoRuleta - base de datos SQLite (esquema fijo del contrato API)
import sqlite3
import os
from config import DB_PATH

# ─── Categorías (IDs y colores FIJOS del contrato) ───
CATEGORIAS = [
    (1, "Comunicación",             "#1e88e5"),
    (2, "Liderazgo",                "#43a047"),
    (3, "Trabajo en equipo",        "#fdd835"),
    (4, "Toma de decisiones",       "#fb8c00"),
    (5, "Motivación",               "#8e24aa"),
    (6, "Resolución de conflictos", "#e53935"),
]

# ─── Preguntas fijas (IDs 1-6) ───
PREGUNTAS = {
    1: "¿Cómo explicarías una indicación a un paciente que no comprende?",
    2: "Nombra 2 características de un buen líder de enfermería.",
    3: "¿Qué harías para fomentar la colaboración cuando hay desacuerdo entre miembros del equipo de enfermería durante un turno?",
    4: "¿Qué factores considerarías al priorizar a varios pacientes cuando los recursos son limitados?",
    5: "¿Qué estrategia usarías para motivar a un compañero que se siente agotado y desmotivado?",
    6: "¿Cómo manejarías un conflicto con un familiar de paciente que está molesto por los tiempos de atención?",
}

# ─── Situaciones avanzadas (IDs 101-602: categoria*100 + numero) ───
SITUACIONES = {
    101: "Una familia solicita información médica del paciente, pero el paciente ha solicitado que no se comparta su diagnóstico. ¿Cómo comunicas el límite de confidencialidad de manera empática, respetando la autonomía del paciente y manteniendo la confianza con la familia?",
    102: "Debes comunicar malas noticias sobre el pronóstico en cuidados paliativos. El paciente responde con silencio y lágrimas, sin hablar. ¿Qué estrategias de comunicación terapéutica utilizas para acompañar, validar sus emociones y crear un espacio seguro de expresión sin presionar?",
    201: "Durante el turno nocturno, enfermería junior comete un error de dosis y está muy afectada emocionalmente. Como líder, ¿cómo gestionas la seguridad del paciente, brindas apoyo al personal y fomentas una cultura de reporte y aprendizaje sin culpa?",
    202: "El equipo se resiste al nuevo protocolo de prevención de infecciones y muestra baja adherencia. ¿Qué acciones de liderazgo implementas para motivar al equipo, explicar el cambio con evidencia y asegurar el cumplimiento colaborativo?",
    301: "Fisioterapia y el médico proponen objetivos diferentes para el plan de alta del paciente, generando desacuerdo en la reunión interdisciplinar. ¿Cómo facilitas el consenso del equipo para alinear objetivos centrados en el bienestar del paciente?",
    302: "Observas que la carga de trabajo está desequilibrada; algunos colaboradores están agotados mientras otros no participan activamente. ¿Qué estrategias propones para redistribuir tareas y fortalecer la colaboración equitativa dentro del equipo?",
    401: "Un paciente con capacidad de decisión rechaza el tratamiento recomendado pese al riesgo de deterioro. El tiempo es limitado. ¿Qué pasos sigues para aplicar la toma de decisiones compartida, respetando la autonomía y asegurando la comprensión informada del paciente?",
    402: "Dos pacientes requieren atención urgente simultánea pero solo hay un equipo de monitorización disponible. ¿Qué criterios clínicos y éticos utilizas para priorizar el recurso, garantizando equidad, seguridad y justificación de tu decisión?",
    501: "Un paciente con enfermedad crónica expresa desmotivación y dice: \"No vale la pena seguir cuidándome\". ¿Qué técnicas de entrevista motivacional aplicas para reforzar su autoeficacia y reconectar con sus objetivos personales de salud?",
    502: "Un estudiante de enfermería en prácticas muestra desinterés y baja motivación tras semanas de prácticas. ¿Cómo lo motivas, vinculando su aprendizaje a casos reales y reforzando su confianza profesional para recuperar su compromiso?",
    601: "Dos compañeros discuten por desacuerdo en el registro de enfermería, generando tensión y mal ambiente en el turno. ¿Qué proceso de mediación sigues para resolver el conflicto, promover comunicación asertiva y restaurar el trabajo positivo en equipo?",
    602: "Un familiar se muestra agresivo verbalmente, alza la voz y acusa al equipo de negligencia. ¿Cómo desescalas el conflicto, manejas la situación con calma y proteges al equipo mientras garantizas la atención segura al paciente?",
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY,
        nombre TEXT UNIQUE NOT NULL,
        color TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS preguntas (
        id INTEGER PRIMARY KEY,
        categoria_id INTEGER NOT NULL REFERENCES categorias(id),
        texto TEXT NOT NULL,
        generada_por_ia INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS situaciones (
        id INTEGER PRIMARY KEY,
        categoria_id INTEGER NOT NULL REFERENCES categorias(id),
        numero INTEGER NOT NULL,
        texto TEXT NOT NULL,
        generada_por_ia INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS partidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo1 TEXT NOT NULL,
        equipo2 TEXT NOT NULL,
        fecha TEXT DEFAULT (datetime('now','localtime'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS rondas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partida_id INTEGER NOT NULL REFERENCES partidas(id),
        categoria_id INTEGER NOT NULL,
        tarjeta_id INTEGER NOT NULL,
        tarjeta_tipo TEXT NOT NULL,
        equipo INTEGER NOT NULL,
        respuesta_texto TEXT,
        puntaje_ia INTEGER DEFAULT 0,
        resultado TEXT DEFAULT 'parcial'
    )""")
    # Sembrar categorías (IDs fijos)
    for cid, nombre, color in CATEGORIAS:
        c.execute("INSERT OR IGNORE INTO categorias (id, nombre, color) VALUES (?,?,?)", (cid, nombre, color))
    # Sembrar preguntas (IDs fijos 1-6)
    for cid, texto in PREGUNTAS.items():
        c.execute("INSERT OR IGNORE INTO preguntas (id, categoria_id, texto, generada_por_ia) VALUES (?,?,?,0)", (cid, cid, texto))
    # Sembrar situaciones (IDs fijos 101-602)
    for sid, texto in SITUACIONES.items():
        cat_id = sid // 100
        numero = sid % 100
        c.execute("INSERT OR IGNORE INTO situaciones (id, categoria_id, numero, texto, generada_por_ia) VALUES (?,?,?,?,0)",
                  (sid, cat_id, numero, texto))
    conn.commit()
    conn.close()

# ─── Consultas (formato del contrato API) ───
def listar_categorias():
    conn = get_db()
    cats = conn.execute("SELECT * FROM categorias ORDER BY id").fetchall()
    conn.close()
    return [dict(c) for c in cats]

def get_preguntas():
    conn = get_db()
    rows = conn.execute("SELECT * FROM preguntas ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_situaciones():
    conn = get_db()
    rows = conn.execute("SELECT * FROM situaciones ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def tarjeta_random(categoria_id=None, tipo=None):
    """Devuelve una tarjeta al azar: tipo 'pregunta' o 'situacion'."""
    conn = get_db()
    import random
    if tipo == "pregunta":
        if categoria_id:
            rows = conn.execute("SELECT * FROM preguntas WHERE categoria_id=? ORDER BY RANDOM() LIMIT 1", (categoria_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM preguntas ORDER BY RANDOM() LIMIT 1").fetchall()
        conn.close()
        if rows:
            r = dict(rows[0])
            return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "pregunta",
                    "texto": r["texto"], "generada_por_ia": bool(r["generada_por_ia"])}
    elif tipo == "situacion":
        if categoria_id:
            rows = conn.execute("SELECT * FROM situaciones WHERE categoria_id=? ORDER BY RANDOM() LIMIT 1", (categoria_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM situaciones ORDER BY RANDOM() LIMIT 1").fetchall()
        conn.close()
        if rows:
            r = dict(rows[0])
            return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "situacion",
                    "numero": r["numero"], "texto": f"Situación: {r['texto']}",
                    "generada_por_ia": bool(r["generada_por_ia"])}
    conn.close()
    return None

def tarjeta_por_id(tarjeta_id, tipo):
    conn = get_db()
    if tipo == "pregunta":
        row = conn.execute("SELECT * FROM preguntas WHERE id=?", (tarjeta_id,)).fetchone()
        conn.close()
        if not row:
            return None
        r = dict(row)
        return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "pregunta",
                "texto": r["texto"], "generada_por_ia": bool(r["generada_por_ia"])}
    row = conn.execute("SELECT * FROM situaciones WHERE id=?", (tarjeta_id,)).fetchone()
    conn.close()
    if not row:
        return None
    r = dict(row)
    return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "situacion",
            "numero": r["numero"], "texto": f"Situación: {r['texto']}",
            "generada_por_ia": bool(r["generada_por_ia"])}

def guardar_situacion_ia(categoria_id, texto):
    """Guarda una situación generada por IA. Devuelve el nuevo id (sigue el esquema)."""
    conn = get_db()
    # Max id existente en la categoría +1 (o 3 si no hay)
    row = conn.execute("SELECT MAX(numero) as mx FROM situaciones WHERE categoria_id=?", (categoria_id,)).fetchone()
    numero = (row["mx"] or 2) + 1
    sid = categoria_id * 100 + numero
    cur = conn.execute(
        "INSERT OR REPLACE INTO situaciones (id, categoria_id, numero, texto, generada_por_ia) VALUES (?,?,?,?,1)",
        (sid, categoria_id, numero, texto))
    conn.commit()
    conn.close()
    return sid

def crear_partida(equipo1, equipo2):
    conn = get_db()
    cur = conn.execute("INSERT INTO partidas (equipo1, equipo2) VALUES (?,?)", (equipo1, equipo2))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def guardar_ronda(partida_id, categoria_id, tarjeta_id, tarjeta_tipo, equipo, respuesta, puntaje, resultado):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO rondas (partida_id, categoria_id, tarjeta_id, tarjeta_tipo, equipo, respuesta_texto, puntaje_ia, resultado)
           VALUES (?,?,?,?,?,?,?,?)""",
        (partida_id, categoria_id, tarjeta_id, tarjeta_tipo, equipo, respuesta, puntaje, resultado))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def estado_partida(partida_id):
    conn = get_db()
    p = conn.execute("SELECT * FROM partidas WHERE id=?", (partida_id,)).fetchone()
    if not p:
        conn.close()
        return None
    rondas = conn.execute("SELECT * FROM rondas WHERE partida_id=?", (partida_id,)).fetchall()
    conn.close()
    pts1 = sum(r["puntaje_ia"] for r in rondas if r["equipo"] == 1)
    pts2 = sum(r["puntaje_ia"] for r in rondas if r["equipo"] == 2)
    return {
        "id": p["id"], "equipo1": p["equipo1"], "equipo2": p["equipo2"],
        "fecha": p["fecha"],
        "puntaje_equipo1": pts1, "puntaje_equipo2": pts2,
        "rondas": [dict(r) for r in rondas],
        "total_rondas": len(rondas),
    }
