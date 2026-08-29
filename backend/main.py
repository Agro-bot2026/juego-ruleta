# JuegoRuleta - API FastAPI (contrato exacto del dueño)
import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import db
import ia
from config import WEB_DIR

app = FastAPI(title="JuegoRuleta API", version="2.0.0")

# ─── Modelos ───
class GirarReq(BaseModel):
    categoria_id: Optional[int] = None
    tipo: Optional[str] = None        # "pregunta" | "situacion" | None (random)
    con_audio: bool = False           # generar audio ya (lento) o después

class GenerarReq(BaseModel):
    categoria_id: int

class EvaluarReq(BaseModel):
    partida_id: int
    categoria_id: int
    tarjeta_id: int
    tarjeta_tipo: str
    equipo: int
    respuesta: str

class PartidaReq(BaseModel):
    equipo1: str
    equipo2: str

# ─── Datos completos (contrato: categorias + preguntas + situaciones) ───
def _pregunta_json(r):
    return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "pregunta",
            "texto": r["texto"], "generada_por_ia": bool(r["generada_por_ia"])}

def _situacion_json(r):
    return {"id": r["id"], "categoria_id": r["categoria_id"], "tipo": "situacion",
            "numero": r["numero"], "texto": f"Situación: {r['texto']}",
            "generada_por_ia": bool(r["generada_por_ia"])}

# ─── Endpoints ───
@app.get("/api")
def root():
    return {"app": "JuegoRuleta", "version": "2.0.0",
            "endpoints": ["/datos", "/categorias", "/girar", "/situacion/generar", "/evaluar", "/partida/{id}"]}

@app.get("/datos")
def datos():
    """Devuelve TODO el contenido del juego (categorias, preguntas, situaciones)."""
    conn = db.get_db()
    cats = conn.execute("SELECT * FROM categorias ORDER BY id").fetchall()
    pregs = conn.execute("SELECT * FROM preguntas ORDER BY id").fetchall()
    sits = conn.execute("SELECT * FROM situaciones ORDER BY id").fetchall()
    conn.close()
    return {
        "categorias": [{"id": c["id"], "nombre": c["nombre"], "color": c["color"]} for c in cats],
        "preguntas": [_pregunta_json(r) for r in pregs],
        "situaciones": [_situacion_json(r) for r in sits],
    }

@app.get("/categorias")
def categorias():
    conn = db.get_db()
    cats = conn.execute("SELECT * FROM categorias ORDER BY id").fetchall()
    conn.close()
    return [{"id": c["id"], "nombre": c["nombre"], "color": c["color"]} for c in cats]

@app.post("/girar")
def girar(req: GirarReq):
    """Gira la ruleta: devuelve la categoría + una tarjeta (pregunta o situación)."""
    cats = db.listar_categorias()
    if not cats:
        raise HTTPException(500, "sin categorías")
    if req.categoria_id:
        cat = next((c for c in cats if c["id"] == req.categoria_id), None)
        if not cat:
            raise HTTPException(404, "categoría no encontrada")
    else:
        cat = random.choice(cats)

    tipo = req.tipo or random.choice(["pregunta", "situacion"])
    tarjeta = db.tarjeta_random(cat["id"], tipo)
    if not tarjeta:
        # fallback al otro tipo
        otro = "situacion" if tipo == "pregunta" else "pregunta"
        tarjeta = db.tarjeta_random(cat["id"], otro)
    if not tarjeta:
        raise HTTPException(500, "sin tarjetas para la categoría")

    audio = ia.guardar_audio(tarjeta["texto"], cat["id"]) if req.con_audio else None
    return {"categoria": cat, "tarjeta": tarjeta, "audio_url": audio}

@app.post("/audio")
def audio_generar(texto: str, categoria_id: int = 0):
    """Genera el audio de un texto (edge-tts gratis) y devuelve la URL."""
    if not texto.strip():
        raise HTTPException(400, "texto vacío")
    url = ia.guardar_audio(texto, categoria_id)
    return {"audio_url": url}

@app.post("/situacion/generar")
def situacion_generar(req: GenerarReq):
    """La IA genera una situación clínica nueva para la categoría."""
    cat = next((c for c in db.listar_categorias() if c["id"] == req.categoria_id), None)
    if not cat:
        raise HTTPException(404, "categoría no encontrada")
    texto = ia.generar_situacion(cat["nombre"])
    sid = db.guardar_situacion_ia(cat["id"], texto)
    audio = ia.guardar_audio(f"Situación: {texto}", cat["id"])
    return {"situacion": {"id": sid, "categoria_id": cat["id"], "tipo": "situacion",
                          "texto": f"Situación: {texto}", "generada_por_ia": True},
            "audio_url": audio}

@app.post("/evaluar")
def evaluar(req: EvaluarReq):
    """Evalúa la respuesta del alumno con IA → resultado + puntaje + feedback."""
    if not req.respuesta.strip():
        raise HTTPException(400, "respuesta vacía")
    tarjeta = db.tarjeta_por_id(req.tarjeta_id, req.tarjeta_tipo)
    if not tarjeta:
        raise HTTPException(404, "tarjeta no encontrada")

    resultado = ia.evaluar_respuesta(tarjeta["texto"], req.respuesta)
    db.guardar_ronda(req.partida_id, req.categoria_id, req.tarjeta_id, req.tarjeta_tipo,
                     req.equipo, req.respuesta, resultado["puntaje"], resultado["resultado"])
    audio = ia.guardar_audio(resultado["feedback"], req.categoria_id)
    return {"resultado": resultado, "audio_url": audio, "partida": db.estado_partida(req.partida_id)}

@app.post("/partida")
def partida_nueva(req: PartidaReq):
    """Crea una partida nueva entre dos equipos."""
    pid = db.crear_partida(req.equipo1, req.equipo2)
    return db.estado_partida(pid)

@app.get("/partida/{partida_id}")
def partida_estado(partida_id: int):
    """Estado y puntajes de los equipos."""
    estado = db.estado_partida(partida_id)
    if not estado:
        raise HTTPException(404, "partida no encontrada")
    return estado

# ─── Frontend estático (WebView / navegador) ───
if os.path.isdir(WEB_DIR):
    app.mount("/audio", StaticFiles(directory=os.path.join(WEB_DIR, "audio")), name="audio")
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    db.init_db()
    uvicorn.run(app, host="0.0.0.0", port=8090)
