import uvicorn

if __name__ == "__main__":
    print("🚀 Iniciando PerezBoost Pro Backend API en http://127.0.0.1:8000...")
    print("📚 Documentación Swagger interactiva disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
