from aiomysql.sa import create_engine
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
import asyncio
from sqlalchemy.schema import CreateTable



async def go(loop):
	engine = await create_engine(user='root',
																			db='ipdb2',
																			host='localhost',
																			password='',
																			port=3306,
																			loop=loop)
	
	async with engine.acquire() as conn:
		for table in [ips, hostnames, steamids, hwids, names, users]:
			try:
				await conn.execute(CreateTable(table))
			except Exception as e:
				print(e)

		
if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(go(loop))
		