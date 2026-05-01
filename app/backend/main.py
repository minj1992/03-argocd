from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import redis
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory API - ArgoCD GitOps Lab")

DB_HOST = os.getenv("DB_HOST", "postgres-svc")
DB_NAME = os.getenv("DB_NAME", "inventory_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password123")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-svc")
APP_VERSION = os.getenv("APP_VERSION", "v1")


class InventoryItem(BaseModel):
    sku: str
    name: str
    quantity: int
    warehouse: str


def db_conn():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER,
        password=DB_PASS, connect_timeout=3
    )


@app.on_event("startup")
def init():
    try:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) UNIQUE,
                name VARCHAR(100),
                quantity INT,
                warehouse VARCHAR(50),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Inventory DB initialized")
    except Exception as e:
        logger.warning(f"DB init: {e}")


@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION, "service": "inventory-api"}


@app.get("/ready")
def ready():
    try:
        conn = db_conn()
        conn.close()
        return {"status": "ready", "version": APP_VERSION}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/inventory")
def list_inventory():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, sku, name, quantity, warehouse, updated_at FROM inventory ORDER BY sku")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "sku": r[1], "name": r[2], "quantity": r[3], "warehouse": r[4], "updated_at": str(r[5])} for r in rows]


@app.post("/inventory", status_code=201)
def add_item(item: InventoryItem):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO inventory (sku, name, quantity, warehouse) VALUES (%s, %s, %s, %s) ON CONFLICT (sku) DO UPDATE SET quantity=EXCLUDED.quantity, updated_at=NOW() RETURNING id",
        (item.sku, item.name, item.quantity, item.warehouse)
    )
    item_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        r.lpush("inventory_events", json.dumps({"event": "item_updated", "sku": item.sku, "qty": item.quantity}))
    except Exception as e:
        logger.warning(f"Redis event push failed: {e}")

    return {"message": "Item saved", "id": item_id}


@app.get("/version")
def version():
    return {"version": APP_VERSION, "git_sha": os.getenv("GIT_SHA", "local")}
