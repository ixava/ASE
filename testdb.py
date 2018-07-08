from aiomysql.sa import create_engine
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
import asyncio
from sqlalchemy import select, and_



async def addProp(conn, table, data):
	stmt = table.insert().values(**data)
	await conn.execute(stmt)

async def main(loop):
	engine = await create_engine(host='localhost',user='root',db='ipdb2',loop=loop)
	async with engine.acquire() as conn:
		# await addProp(conn, ips, {'ip': '192.168.5'})
		# await addProp(conn, names, {'name': 'eric'})
		# await addProp(conn, steamids, {'steamid': '0X9323299dfs'})
		# await addProp(conn, hostnames, {'hostname': 'yom'})
		# await addProp(conn, hwids, {'hwid': 'ASDASKHJDAJKD'})
		# stmt = users.insert().values(ip_id=1,name_id=1,hostname_id=1,steamid_id=1,hwid_id=1)
		# stmt = select([users.c.id,
		#  							 ips.c.ip,
		#  							 hwids.c.hwid,
		#  							 hostnames.c.hostname,
		#  							 ips.c.ip, names.c.name,
		#  							 steamids.c.steamid]
		#  				).where(and_(
		# 					ips.c.ip == '192.168.5',
		# 					hostnames.c.hostname == 'yom',
		# 					steamids.c.steamid == '0X9323299dfs',
		# 					hwids.c.hwid == 'ASDASKHJDAJKD',
		# 					names.c.name == 'ersic'
		# 					) 
		# 				)
		# res = await conn.execute(stmt)
		# rows = await res.fetchall()
		# print(rows)
		# stmt = users.insert()
		print(str(users))

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main(loop))