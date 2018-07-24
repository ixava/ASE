import asyncio, aiohttp, time
from datetime import datetime
from aiomysql.sa import create_engine
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
from sqlalchemy import select, and_

from socket import inet_aton, inet_ntoa
import struct

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
                                      charset='utf8mb4',
                                      loop=self.app.loop)
    
  def select_users_from_join(self):
    return select(metadata.tables.values(), use_labels=True).\
      select_from(users.join(hostnames).join(hwids).join(names).join(ips).join(steamids))

  async def search_exactly(self, conditions):
    stmt = self.select_users_from_join().where(and_(*conditions))

    async with self.engine.acquire() as conn:
      res = await conn.execute(stmt)

      if res.rowcount < 1:
        return {}
      return await res.fetchall()

  async def search_ips(self, ip):
    start_ip, end_ip = [self.longIP(v) for v in self.getIPRange(ip)]
    stmt = self.select_users_from_join().where(ips.c.ip_int.between(start_ip, end_ip))

    async with self.engine.acquire() as conn:
      res = await conn.execute(stmt)

      if res.rowcount < 1:
        return {}
      return await res.fetchall()

  async def search_property(self, column, val):
    table = column.table
    stmt = self.select_users_from_join().where(column.like("%{}%".format(val)))
    async with self.engine.acquire() as conn:
      res = await conn.execute(stmt)

      if res.rowcount < 1:
        return {}
      return await res.fetchall()

  async def user_update(self, uID, values):
    stmt = users.update().where(users.c.id == uID).values(**values)
    async with self.engine.acquire() as conn:
      res = await conn.execute(stmt)

  async def ip_check(self, ip):
    async with aiohttp.ClientSession() as session:
      def_params = "&contact=tgh.bakker@gmail.com&format=json&flags=m"
      async with session.get(
        'http://check.getipintel.net/check.php?ip={}{}'.format(ip,def_params)
      ) as res:
        if res.status != 200:
          print('failed ip vpn check')
          return False
        result = await res.json()
        if result['status'] != 'success':
          print('failed ip vpn check')
          return False
        return result['result']


  async def process_user(self, user):
    checkuser_stmt = self.select_users_from_join().\
                      where(
                        and_(
                          ips.c.ip_int == user['ip_int'],
                          steamids.c.steamid ==  user['steamid'],
                          hwids.c.hwid ==  user['hwid'],
                          names.c.name ==  user['name']
                        )
                      )

    async with self.engine.acquire() as conn:
      res = await conn.execute(checkuser_stmt)
      user_id = None

      if res.rowcount < 1:
        prop_ids = {}
        for column, val in user.items():
          table = eval(column.rstrip('_int') + 's')
          select_stmt = select([table.c.id],use_labels=True).where(table.c[column] == val)
          res = await conn.execute(select_stmt)

          if res.rowcount < 1:
            if column == 'ip_int':
              continue

            data = {} if not column == 'ip' else {'ip_int': user['ip_int']}

            insert_stmt = table.insert().values(**{column: val, **data})
            res = await conn.execute(insert_stmt)
            prop_id = res.lastrowid

            if column == 'ip':
              risk = await self.ip_check(user['ip'])
              if risk:
                risk = risk[:4]
                update_stmt = ips.update().where(ips.c.ip_int == user['ip_int']).values(risk=risk)
                await conn.execute(update_stmt)

          else:
            prop = await res.fetchone()
            prop_id = prop[table.name +'_id']
          prop_ids[table.name.rstrip('s')+'_id'] = prop_id

        user_insert_stmt = users.insert().values(**prop_ids)
        res = await conn.execute(user_insert_stmt)
        user_id = res.lastrowid

      else:
        user_data = await res.fetchone()
        user_id = user_data['users_id']

        last_seen_stmt = users.update().where(users.c.id == user_id).values(last_seen=datetime.now())
        await conn.execute(last_seen_stmt)

        if user_data['hostnames_hostname'] != user['hostname']:
          result = await conn.execute(self.hostname_get_id(user['hostname']))
          if hostname_id.rowcount > 0:
            hostname_id = await result.fetchone()
            hostname_id = hostname_id['id']
          else:
            hostname_ins = hostnames.insert().values(hostname=user['hostname'])
            hostname_q = conn.execute(hostname_ins)
            hostname_id = hostname_q.lastrowid
          await self.user_update(user_data['users_id'],{'hostname_id': hostname_id})

      res = await conn.execute(self.select_users_from_join().where(users.c.id == user_id))
      user_data = await res.fetchone()

      return user_data

  def hostname_get_id(self, hostname):
    return hostnames.select([hostnames.c.id]).where(hostnames.c.hostname == hostname)

  def longIP(self, ip):
    pack = inet_aton(ip)
    longIP = struct.unpack("!L", pack)[0]
    return longIP

  def stringIP(self, long):
    pack = struct.pack('!I', long)
    addr = inet_ntoa(pack)
    return addr

  def getIPRange(self, input):
      input = input.rstrip('.')
      start = input.split('.')
      end = input.split('.')
      for addOctetCount in range(4 - len(start)):
        start.append('0')
        end.append('255')
      return ['.'.join(start), '.'.join(end)]