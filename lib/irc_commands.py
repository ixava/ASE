from tabulate import tabulate
from lib.tables import metadata, users, ips, hostnames, steamids, hwids, names
import re

def command(lvl=0, chan_allow=[]):
  def decorator(fn):
    async def wrapped(self, channel, user, args):
      user_lvl = self.app.auth.getRank(user['user'])
      if not int(user_lvl) > lvl:
        self.app.ircHandle.notice(user['nick'], "You do not have permission to use this command")
      elif len(chan_allow) > 0 and channel.lower() not in [getattr(self.app.ircHandle, v) for v in chan_allow]:
        self.app.ircHandle.notice(user['nick'], "You cannot use this command in this channel")
      else:
        await fn(self, channel, user, args)
    wrapped.lvl = lvl
    wrapped.chan_allow = chan_allow
    return wrapped
  return decorator

class Commands:
  def __init__(self, app):
    self.app = app
    self.enabledCommands = [
      'ipdb',
      'help',
      'myrank',
      'modlist',
      'sendrcon',
      'hostsearch'
    ]
    self.irc = None

  @command(lvl=0, chan_allow=['logChannel', 'adminChannel', 'ipdbChannel'])
  async def hostsearch(self, channel, user, args):
    result = await self.app.db.search_property(hostnames.c.hostname, ' '.join(args))
    if result:
      await self.print_table(result, user)
    else:
      self.app.ircHandle.notice(user['nick'], 'No results matched')


  @command(lvl=0, chan_allow=['logChannel', 'adminChannel', 'ipdbChannel'])
  async def ipdb(self, channel, user, args):
    search_string = ' '.join(args)
    ip_regex = re.compile('(\d{1,3}\.){1,3}(\d{1,3})?')
    steamid_regex = re.compile('0[xX][0-9a-fA-F]+')
    hwid_regex = re.compile('[0-9a-fA-F]{16}')

    if ip_regex.match(search_string):
        result = await self.app.db.search_ips(search_string)
    elif steamid_regex.match(search_string):
        result = await self.app.db.search_property(steamids.c.steamid, search_string)
    elif hwid_regex.match(search_string):
        result = await self.app.db.search_exactly([hwids.c.hwid == search_string])
    else:
        result = await self.app.db.search_property(names.c.name, search_string)

    if result:
      await self.print_table(result,user)
      # table = self.makeTable(result)
      # for msg in table:
      #   self.app.ircHandle.notice(user['nick'], msg)
    else:
      self.app.ircHandle.notice(user['nick'], 'No results matched')

  async def print_table(self, data, user):
    headers = ['name', 'ip', 'hostname', 'hwid', 'steamid', 'ipRisk', 'seen']
    result = []
    for row in data:
      result.append([row['names_name'],
        row['ips_ip'],
        row['hostnames_hostname'],
        row['hwids_hwid'],
        row['steamids_steamid'],
        row['ips_risk'],
        row['users_last_seen']
      ])
    table = tabulate(result, headers=headers)
    for msg in table.split('\n'):
      self.app.ircHandle.notice(user['nick'], msg)

  @command(lvl=0)
  async def help(self, channel, user, args):
    result = [*[[] for x in range(len(self.app.auth.ranks))]]
    rank = self.app.auth.getRank(user['user'])

    for cmd in self.enabledCommands:
      lvl = eval('self.{}.lvl'.format(cmd))
      result[lvl].append("{}{}".format(self.app.config['IRC']['cmd-sign'], cmd))
    result = result[:(int(rank) + 1)]
    for cmdlvl, cmds in enumerate(result):
      self.app.ircHandle.notice(user['user'],\
       self.app.auth.ranks[str(cmdlvl)] +":  "+ ' '.join(cmds))

  @command(lvl=1)
  async def myrank(self, channel, user, args):
    nick = user['nick']
    self.app.ircHandle.notice(nick,\
     self.app.auth.getRankName(self.app.auth.getRank(nick)))

  @command(lvl=1)
  async def modlist(self, channel, user, args):
    data = [[] for x in range(len(self.app.auth.ranks))]
    for name, lvl in self.app.auth.modList.items():
      data[int(lvl)].append(name)
    table = self.makeTable(data, self.app.auth.ranks.values())
    for line in table:
      self.app.ircHandle.notice(user['nick'], line)

  @command(lvl=1)
  async def sendrcon(self, channel, user, args):
    data = await self.app.rconHandle.send_command(' '.join(args))
    self.app.ircHandle.notice(user['nick'], data)

  def makeTable(self, data, headers):
    for k, category in enumerate(data):
      if len(category) > 0:
        data[k] = [*['-' for x in range(len(headers) - len(category))], *category]
    table = tabulate(data, headers=headers)
    return table.split('\n')