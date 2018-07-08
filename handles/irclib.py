import asyncio, re, time
from lib.wrappers import ClientWrapper
from lib.irc_commands import Commands

class IRCObj:
  def __init__(self, message):
    prefix = ''
    trailing = []
    if not message:
      return False
    if message[0] == ':':
      prefix, message =  message.split(' ', 1)
    if message.find(' :') != -1:
      message, trailing = message.split(' :', 1)
      args = message.split()
      args.append(trailing)
    else:
      args = message.split()
    command = args.pop(0)
    self.prefix = prefix
    self.command = command
    self.args = args
    # print("prefix:{}, args:{}, command:{}".format(prefix, args, command))
        
class IRCHandle(ClientWrapper):
  def __init__(self, app):
    self.inChannels = []
    self.logChannel = app.config['IRC'].get('log-channel', False)
    self.normalChannel = app.config['IRC'].get('normal-channel', False)
    self.adminChannel = app.config['IRC'].get('admin-channel', False)
    self.ipdbChannel = False #'renx-admin'
    self.commands = Commands(app)
    super().__init__(sockcfg=app.config['IRC'], encoding='utf-8', app=app)


  async def onConnect(self):
    cfg = self.sockcfg
    self.sock.send("NICK {}".format(cfg['nick']) )
    self.sock.send("USER {} derpy ekt :{}".format(cfg['nick'], cfg['realname']))


  async def parseMessage(self, message):
    irc_obj = IRCObj(message)
    command = irc_obj.command
    if command == 'PING':
      self.pong(irc_obj.args[0])
    elif command == '001':
      await self.identify()
    elif command == 'PRIVMSG':
      await self.onPrivmsg(irc_obj)

  async def onPrivmsg(self, ircObj):
    channel, message = ircObj.args
    channel = channel.lstrip('#')
    if message[0] != self.app.config['IRC']['cmd-sign']:
      print('wrong cmd char')
      return
    if message.find(' ') != -1:
      command, args = message[1:].split(' ')
    else:
      command = message[1:]
      args = []

    nick, s = ircObj.prefix[1:].split('!', 1)
    user, host = s.split('@', 1)
    userDict = {'nick': nick, 'user': user, 'host': host}
    
    if command in self.commands.enabledCommands:
      func = eval('self.commands.{}'.format(command))
      await func(channel, userDict, args)

  async def identify(self):
    cfg = self.sockcfg
    self.sock.send("PASS {}".format(cfg['password']))
    if 'oper' in cfg:
      self.sock.send("OPER {}".format(cfg['oper']))
    await asyncio.sleep(0.1)
    if self.adminChannel:
      self.join(self.adminChannel)
    if self.normalChannel:
      self.join(self.normalChannel)
    if self.logChannel:
      self.join(self.logChannel)
    if self.ipdbChannel:
      self.join(self.ipdbChannel)

  def join(self, channel):
    self.inChannels.append(channel)
    self.sock.send("JOIN #{}".format(channel))

  def pong(self, message):
    self.sock.send("PONG {} {}".format(self.app.config['IRC']['host'], message))

  def privmsg(self, target, msg):
    self.sock.send("PRIVMSG #{} {}".format(target, msg))

  def broadcast(self, message):
    for channel in self.inChannels:
      self.privmsg(channel, message)

  def notice(self, nick, message):
    self.sock.send("NOTICE {} {}".format(nick, message))





