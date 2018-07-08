from tabulate import tabulate

def command(lvl=0, chan_allow=[]):
  def decorator(fn):
    async def wrapped(self, channel, user, args):
      user_lvl = self.app.auth.getRank(user['user'])
      if not int(user_lvl) > lvl:
        self.app.ircHandle.privmsg(notice, "You do not have permission to use this command")
      elif len(chan_allow) > 0 and channel not in [getattr(self.app.ircHandle, v) for v in chan_allow]:
        self.app.ircHandle.privmsg(notice, "You cannot use this command in this channel")
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
      'modlist'
    ]
    self.irc = None

  @command(lvl=0, chan_allow=['logChannel', 'adminChannel', 'ipdbChannel'])
  async def ipdb(self, channel, user, args):
    self.app.ircHandle.privmsg(channel, 'user:{}, args:{}'.format(user, args))

  @command(lvl=0)
  async def help(self, channel, user, args):
    result = [*[[] for x in range(len(self.app.auth.ranks))]]
    rank = self.app.auth.getRank(user['user'])

    for cmd in self.enabledCommands:
      lvl = eval('self.{}.lvl'.format(cmd))
      result[lvl].append("{}{}".format(self.app.config['IRC']['cmd-sign'], cmd))
    result = result[:(lvl + 1)]
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

  def makeTable(self, data, headers):
    for k, category in enumerate(data):
      if len(category) > 0:
        data[k] = [*['-' for x in range(len(headers) - len(category))], *category]
    table = tabulate(data, headers=headers)
    return table.split('\n')