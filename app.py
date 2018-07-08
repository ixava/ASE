import asyncio, configparser
from handles.irclib import IRCHandle
from handles.rconlib import RconHandle
from lib.db import DB
from concurrent.futures import ThreadPoolExecutor
import aiodns
from ipaddress import ip_address

class Modlist:
	def __init__(self, app):
		self.app = app
		self.modList = self.app.config['MODLIST']
		self.ranks = {str(v): k for k,v in self.app.config['RANKS'].items()}

	def getRank(self, nick):
		return self.modList[nick.lower()] if nick.lower() in self.modList else 0

	def getRankName(self, id):
		return self.ranks[id]

class App:
	def __init__(self, config):
		self.config = config
		self.loop = asyncio.get_event_loop()
		self.ircHandle = IRCHandle(app=self)
		self.rconHandle = RconHandle(app=self)
		self.auth = Modlist(self)
		self.db = DB(app=self)
		self.iopool = ThreadPoolExecutor()
		self.dnsresolver = aiodns.DNSResolver(loop=self.loop)

	async def runIrc(self):
		while True:
			await self.ircHandle.sock.run()

	async def runRcon(self):
		while True:
			await self.rconHandle.sock.run()

	async def run(self):
		while True:
			await self.rconHandle.sock.run()

	async def getHost(self, ip):
		try:
			ip = ip_address(ip).reverse_pointer
			return (await self.dnsresolver.query(ip, 'PTR'))[0]
		except Exception as e:
			return '-'


	def start(self):
		self.loop.run_until_complete(self.ircHandle.sock.connect())
		self.loop.run_until_complete(self.rconHandle.sock.connect())
		self.loop.run_until_complete(self.db.connect())
		asyncio.async(self.runIrc(), loop=self.loop)
		asyncio.async(self.runRcon(), loop=self.loop)
		try:
			self.loop.run_forever()
		except KeyboardInterrupt:
			exit()