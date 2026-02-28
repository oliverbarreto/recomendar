# The best and more documented approach to build a FastAPI with async capabilities with sqlite... use SQLAlchemy or SQLModel as ORM ?

Para construir una API en FastAPI con capacidades asíncronas usando SQLite, la mejor aproximación documentada implica combinar **SQLModel** (para integración con Pydantic) o **SQLAlchemy Core** (para mayor flexibilidad), usando el driver `aiosqlite`. Aquí tienes una guía estructurada:

---

### 1. **Elección de ORM**

#### **SQLModel** (Recomendado para FastAPI)

- **Ventajas**:
    - Combina SQLAlchemy Core con Pydantic, ideal para validación y serialización automática en FastAPI[^1_5][^1_6].
    - Documentación oficial de FastAPI lo utiliza como ejemplo[^1_5].
- **Configuración asíncrona**:

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///database.db"
engine = create_async_engine(DATABASE_URL, echo=True)
```


#### **SQLAlchemy Core** (Para necesidades avanzadas)

- **Ventajas**:
    - Mayor control sobre consultas y transacciones[^1_4][^1_7].
    - Soporta patrones avanzados como conexiones agrupadas (`AsyncAdaptedQueuePool`)[^1_4].
- **Ejemplo de sesión asíncrona**:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///database.db")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```


---

### 2. **Gestión de sesiones asíncronas**

- **Patrón recomendado**: Usar `async_sessionmaker` y dependencias inyectables[^1_4][^1_6]:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/items")
async def read_items(session: AsyncSession = Depends(get_db)):
    result = await session.execute("SELECT * FROM items")
    return result.scalars().all()
```


---

### 3. **Migraciones con Alembic (Opcional)**

Para manejar cambios en esquemas:

1. Instala `alembic` y configura `alembic.ini`:

```ini
sqlalchemy.url = sqlite+aiosqlite:///database.db
```

2. Usa `async_` en los scripts de migración:

```python
# migrations/env.py
from sqlalchemy.ext.asyncio import create_async_engine
```

```bash
alembic revision --autogenerate -m "create tables"
alembic upgrade head
```


---

### 4. **Consideraciones clave**

- **Driver asíncrono**: Siempre usa `sqlite+aiosqlite://` en la URL[^1_1][^1_6].
- **Transacciones**:
    - En operaciones CRUD, usa `await session.commit()` tras modificaciones[^1_4][^1_7].
    - Evita mantener sesiones abiertas innecesariamente.
- **Testing**: Para pruebas, usa bases de datos en memoria (`sqlite+aiosqlite:///:memory:`)[^1_1].

---

### 5. **Ejemplo completo con SQLModel**

```python
from fastapi import FastAPI
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///database.db")

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_db)):
    result = await session.exec(select(User))
    return result.all()
```


---

**Documentación recomendada**:

- [Guía oficial de FastAPI con SQLModel](https://fastapi.tiangolo.com/tutorial/sql-databases/)[^1_5]
- [SQLAlchemy asíncrono en producción](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e)[^1_4]

Ambos enfoques son válidos, pero **SQLModel** ofrece una integración más fluida con FastAPI, mientras que **SQLAlchemy Core** brinda mayor flexibilidad para casos complejos[^1_7][^1_8].

<div style="text-align: center">⁂</div>

[^1_1]: https://www.reddit.com/r/Python/comments/vm2qxe/async_inmemory_sqlitesqlalchemy_database_for/

[^1_2]: https://timothy.hashnode.dev/from-zero-to-production-setting-up-a-sql-database-with-async-engine-in-fastapi

[^1_3]: https://testdriven.io/blog/fastapi-sqlmodel/

[^1_4]: https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e

[^1_5]: https://fastapi.tiangolo.com/tutorial/sql-databases/

[^1_6]: https://www.aritro.in/post/local-development-environment-with-fast-api-sqlmodel-sqlite-alembic-sync-async-version/

[^1_7]: https://stackoverflow.com/questions/68793314/what-is-the-best-approach-to-hooking-up-database-in-fastapi

[^1_8]: https://www.linkedin.com/pulse/moving-from-sync-async-fastapi-sqlmodelwhat-you-need-know-vertrees-eowtc

[^1_9]: https://dev.to/dhrumitdk/asynchronous-programming-with-fastapi-building-efficient-apis-nj1

[^1_10]: https://fastapi.tiangolo.com/es/async/

[^1_11]: https://fastapi.tiangolo.com

[^1_12]: https://www.reddit.com/r/Python/comments/1br19x3/sqlmodel_vs_native_sql_alchemy_orm_for_a_web/

[^1_13]: https://github.com/fastapi/fastapi/discussions/8615

[^1_14]: https://arunanshub.hashnode.dev/async-database-operations-with-sqlmodel

[^1_15]: https://gpttutorpro.com/fastapi-asynchronous-async-await-and-async-sql/

[^1_16]: https://www.youtube.com/watch?v=jLoAuKo2tm0

[^1_17]: https://www.youtube.com/watch?v=Z0jbO8WT0Jc

[^1_18]: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/

[^1_19]: https://www.youtube.com/watch?v=cH0immwfykI

