import asyncpg
import config

connection = None


async def start():
    global connection
    try:
        connection = await asyncpg.create_pool(
            user=config.DB_USER, password=config.DB_PSWD,
            database=config.DB_NAME, host=config.DB_HOST
        )
    except:
        print("\033[91m" + "Error connecting to Postgres database" + "\033[0m")
        exit(-1)


def postgres(func):
    async def inner(*args, **kwargs):
        if connection is None:
            return
        return await func(*args, **kwargs, conn=connection)
    return inner
