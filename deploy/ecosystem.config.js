module.exports = {
  apps: [{
    name: "juego-ruleta",
    cwd: "/opt/juego-ruleta/backend",
    script: "venv/bin/python",
    args: "-m uvicorn main:app --host 0.0.0.0 --port 8090",
    interpreter: "none",
    env: {
      DEEPSEEK_API_KEY: "",
      OPENAI_API_KEY: ""
    },
    max_memory_restart: "400M",
    autorestart: true
  }]
}
