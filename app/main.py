from fastapi import FastAPI 

app = FastAPI() 

@app.get("/") 
async def root(): 
    return {"message": "Projeto finalizado com sucesso! deu tudo certo (: "} 