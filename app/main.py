from fastapi import FastAPI 

app = FastAPI() 

@app.get("/") 
async def root(): 
    return {"message": "CI/CD com GitHub Actions e ArgoCD! PARA TESTE FINAL"} 