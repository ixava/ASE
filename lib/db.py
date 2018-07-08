import asyncio
from aiomysql.sa import create_engine
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
from sqlalchemy import select, and_

def query(fn):
	async def decorator(self, *args, **kwargs):
		async with self.engine.acquire() as conn:
			stmt = await fn(self, *args, **kwargs)
			return await conn.execute(stmt)
	return decorator


class DB:
	def __init__(self, app=None):
		self.cfg = app.config
		self.dbcfg = self.cfg['DB']
		self.pw = self.dbcfg.get('password', '')
		self.engine = None
		self.app = app
	
	async def connect(self):
		self.engine = await create_engine(user=self.dbcfg['user'],
																			db=self.dbcfg['database'],
																			host=self.dbcfg['host'],
																			password=self.pw,
																			loop=self.app.loop)
		

	# @query
	# async def user_add(self, **kwargs):
	# 	return users.insert().values(kwargs)

	@query
	async def user_get(self,steamid='-',name=None,ip=None,hwid='-', **kwargs):
		stmt = select([users.c.id,
									 users.c.hostname_id,
		 							 ips.c.ip,
		 							 hwids.c.hwid, 
		 							 names.c.name,
		 							 steamids.c.steamid]
		 				).where(and_(
							ips.c.ip == ip,
							steamids.c.steamid == steamid,
							hwids.c.hwid == hwid,
							names.c.name == name
							) 
						)
		return stmt

	# @query
	# async def prop_get(self, table, value=""):
	# 	return select([table]).where()


