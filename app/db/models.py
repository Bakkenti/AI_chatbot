import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, String, select, or_, inspect, cast

project_root = os.path.join(os.path.dirname(__file__), "..", "..")
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
metadata = MetaData()

async def test_db_connection() -> bool:
    try:
        async with engine.begin() as conn:
            def _check(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            await conn.run_sync(_check)
        return True
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return False

async def fetch_table_preview(table_name: str, limit: int = 10):
    async with engine.begin() as conn:
        def _load_table(sync_conn):
            return Table(table_name, metadata, autoload_with=sync_conn)
        table = await conn.run_sync(_load_table)

    async with async_session() as session:
        stmt = select(table).limit(limit)
        result = await session.execute(stmt)
        rows = result.fetchall()
        columns = table.columns.keys()
        return columns, [dict(row._mapping) for row in rows]

async def search_keyword_global(keyword: str, limit_per_table: int = 5):
    async with async_session() as session:
        results = []
        async with engine.begin() as conn:
            def _get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            tables = await conn.run_sync(_get_tables)

        for table_name in tables:
            async with engine.begin() as conn:
                def _load_table(sync_conn):
                    return Table(table_name, metadata, autoload_with=sync_conn)
                table = await conn.run_sync(_load_table)

            def escape_like(s: str) -> str:
                return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

            escaped_keyword = escape_like(keyword)
            text_cols = [c for c in table.c]
            conditions = [
                cast(c, String).ilike(f"%{escaped_keyword}%", escape='\\')
                for c in text_cols
            ]
            stmt = select(*text_cols).where(or_(*conditions)).limit(limit_per_table)
            result = await session.execute(stmt)
            rows = result.fetchall()

            if rows:
                results.append((table_name, [dict(r._mapping) for r in rows]))

        return results
