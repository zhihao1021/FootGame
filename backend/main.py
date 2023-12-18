from api import run as run_api

from asyncio import get_event_loop, run

async def main():
    loop = get_event_loop()

    await run_api(loop)

if __name__ == "__main__":
    run(main=main())
