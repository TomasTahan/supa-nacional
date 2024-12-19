from fastapi import FastAPI, Query, HTTPException
import asyncpg
import os

app = FastAPI()

# URL de la base de datos desde variable de entorno (o valor por defecto para local)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.gjriukyuppmdacfxzwsr:PCEesAmDyCegX4QP@aws-0-sa-east-1.pooler.supabase.com:6543/postgres",
)

# Pool de conexiones (inicializado en startup)
db_pool = None


# Evento de inicio: Crear pool de conexiones
@app.on_event("startup")
async def startup():
    global db_pool
    try:
        # Configuración para evitar problemas con pgbouncer
        db_pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)
        print("Database connection pool created.")
    except Exception as e:
        print(f"Error creating database pool: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


# Evento de cierre: Cerrar pool de conexiones
@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Database connection pool closed.")


# Ruta raíz para pruebas
@app.get("/")
async def root():
    return {"message": "FastAPI is working on Vercel!"}


# Ruta con parámetro carrito_id
@app.get("/invetario-nacional")
async def get_vista(carrito_id: int = Query(..., alias="carritoId")):
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database pool not initialized.")
    try:
        async with db_pool.acquire() as connection:
            rows = await connection.fetch(
                'SELECT * FROM VistaCarritoProductos WHERE "carritoId" = $1;', carrito_id
            )
            return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}


# Ruta de prueba para verificar conexión a la base de datos
@app.get("/db-test")
async def db_test():
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database pool not initialized.")
    try:
        async with db_pool.acquire() as connection:
            result = await connection.fetch("SELECT 1;")
            return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e)}


# Ejecutar el servidor Uvicorn (necesario para Vercel y local)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
