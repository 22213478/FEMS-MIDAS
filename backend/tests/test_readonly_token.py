# backend/tests/test_readonly_token.py

import asyncio
from pprint import pprint

from database.connection import AsyncSessionLocal
from repositories.readonly_token_repository import get_readonly_token


async def main():
    async with AsyncSessionLocal() as db:
        token = await get_readonly_token(db, "rdonly_test_1")
        pprint(token)


asyncio.run(main())