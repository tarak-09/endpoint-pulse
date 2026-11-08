import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://google.com") as response:
            conn = response.connection
            if conn and conn.transport:
                cert = conn.transport.get_extra_info('peercert')
                print(cert)

asyncio.run(main())
