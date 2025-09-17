# database.py
import asyncpg
from config import DATABASE_URL

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

# async def create_tables():
#     conn = await get_db_connection()
#     # Table creation is disabled for now
#     # await conn.execute('''
#     #     CREATE TABLE IF NOT EXISTS users (
#     #         user_id BIGINT PRIMARY KEY,
#     #         username VARCHAR(255),
#     #         first_name VARCHAR(255),
#     #         last_name VARCHAR(255),
#     #         created_at TIMESTAMP DEFAULT NOW()
#     #     )
#     # ''')
#     # await conn.close()