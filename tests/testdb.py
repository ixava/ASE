from aiomysql.sa import create_engine
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
import asyncio
from sqlalchemy import select, and_
from sqlalchemy.dialects.mysql import insert
from collections import namedtuple
from sqlalchemy import func

from socket import inet_aton, inet_ntoa
import struct


class DB:
  def __init__(self):
    self.engine = None

  async def connect(self):
    self.engine = await create_engine(host='localhost',user='root',db='ipdb2')
    hostname = 'sjhpppppppppppp'
    hwid = 'JkddasssddJH'
    name = 'abgdddg'
    ip = '113.168.99.45'
    steamid = 'ksaaaaa'
    self.user = {'hostname': hostname,
      # 'ip': ip,
      'ip_int': self.longIP(ip),
      'name': name,
      'steamid': steamid,
      'hwid': hwid,
    }

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

      if res.rowcount < 1:
        prop_ids = {}

        for column, val in self.user.items():
          table = eval(column.rstrip('_int') + 's')
          select_stmt = self.select_stmt([table.c.id],[table.c[column] == val])
          res = await conn.execute(select_stmt)

          if res.rowcount < 1:
            if column == 'ip_int':
              data = {'ip': self.stringIP(user['ip_int'])}

            else:
              data = {}

            insert_stmt = table.insert().values(**{column: val, **data})
            res = await conn.execute(insert_stmt)
            prop_id = res.lastrowid

          else:
            prop = await res.fetchone()
            prop_id = prop[table.name +'_id']
          prop_ids[table.name.rstrip('s')+'_id'] = prop_id

        user_insert_stmt = users.insert().values(**prop_ids)
        res = await conn.execute(user_insert_stmt)
        user_id = res.lastrowid

        res = await conn.execute(self.select_users_from_join().where(users.c.id == user_id))
        user_data = await res.fetchone()

      else:
        user_data = await res.fetchone()
      for x in user_data:
        print(x)

  async def test_search(self):
    async with self.engine.acquire() as conn:
      result = await self.search_ips('192.168.')
      print(len(result))

      result = await self.search_property(hostnames.c.hostname, self.user['hostname'])
      print(len(result))
      
      result = await self.search_property(names.c.name, self.user['name'])
      print(len(result))
      
      result = await self.search_exactly([hwids.c.hwid == self.user['hwid']])
      print(len(result))



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

if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  db = DB()
  loop.run_until_complete(db.connect())
  loop.run_until_complete(db.process_user(db.user))
  loop.run_until_complete(db.test_search())

# def query(fn):
#   async def decorator(conn, *args, **kwargs):
#     stmt = await fn(conn, *args, **kwargs)
#     print(stmt)
#     return await conn.execute(stmt)
#   return decorator

# @query
# async def insert_prop(conn, tablename, columns, values):
#   table = eval(tablename)
#   return table.insert().values(**dict(zip(columns, values)))

# @query
# async def get_prop_id(conn, tablename, columnname, value):
#   table = eval(tablename)
#   column = table.c[columnname]
#   stmt = select([table.c.id]).where(column == value)
#   return stmt

# @query
# async def insert_user(conn, props):
#   props = {k+'_id': v for k, v in props.items()}
#   return users.insert().values(**props)


# async def main(loop):
#   engine = await create_engine(host='localhost',user='root',db='ipdb2',loop=loop)
#   async with engine.acquire() as conn:
#     hostname = 'sjhhddd@;;@k.com'
#     hwid = 'JkddddJH'
#     name = 'abgdddg'
#     ip = '113.168.99.65'
#     steamid = 'ksaaaaa'

#     user = {'hostname': hostname,
#       'ip': ip,
#       'ip_int': longIP(ip),
#       'name': name,
#       'steamid': steamid,
#       'hwid': hwid,
#     }



#     async def get_row(conn, columns, data):
#       data_count = len(data)
#       conditions = [columns[i] == data[i] for i in range(data_count)]

#       stmt = select([columns[0].table]).where(
#         and_(*conditions)
#       )
#       res = await conn.execute(stmt)

#       if res.rowcount < 1:
#         return False
#       return await res.fetchone()

#     async def add_row(conn, columns, data):
#       table = columns[0].table
#       vals = {columns[i].name: data[i] for i in range(len(data))}
#       stmt = table.insert().values(**vals)

#       res = await conn.execute(stmt)
#       return res.lastrowid

#     async def get_user(conn, name=None, steamid=None, hwid=None, ip=None, **kwargs):
#       stmt = select([users.c.id,
#                    ips,
#                    hwids, 
#                    names,
#                    steamids,
#                    hostnames],use_labels=True
#             ).where(and_(
#               ips.c.ip == ip,
#               steamids.c.steamid == steamid,
#               hwids.c.hwid == hwid,
#               names.c.name == name
#               ) 
#             )
#       res = await conn.execute(stmt)
#       if res.rowcount < 1:
#         return False
#       return await res.fetchone()

#     async def insert_get_prop(conn, columns, data):
#       result = await get_row(conn, columns, data)
#       if result:
#         return result['id']
#       propID = await add_row(conn, columns, data)
#       return propID.lastrowid

#     async def process_user(conn, user):
#       usero = namedtuple('User', user.keys())(*user.values())
#       user_db = await get_user(conn, **user)
#       if not user_db:
#         hwid = await insert_get_prop(conn, [hwids.c.hwid], [usero.hwid])
#         name = await insert_get_prop(conn, [names.c.name], [usero.name])
#         ip = await insert_get_prop(conn, [ips.c.ip, ips.c.ip_int], [usero.ip, usero.ip_int])
#         hostname = await insert_get_prop(conn, [hostnames.c.hostname], [usero.hostname])
#         steamid = await insert_get_prop(conn, [steamids.c.steamid], [usero.steamid])
#         user_columns = [
#           users.c.hwid_id,
#           users.c.name_id,
#           users.c.ip_id,
#           users.c.hostname_id,
#           users.c.steamid_id
#         ]
#         await add_row(conn , user_columns, [hwid, name, ip, hostname, steamid])
#         user_db = await get_user(conn, **user)
#       return user_db  



