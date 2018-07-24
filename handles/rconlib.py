from lib.wrappers import ClientWrapper
import asyncio
from uuid import uuid4

class RconHandle(ClientWrapper):
  def __init__(self, app):
    super().__init__(sockcfg=app.config['RCON'], app=app, encoding='unicode-escape', decoding='ASCII')
    # self.playerBuffer = {}
    self.response_buffer = []
    self.response_queue = {}
    self.command_response_ids = []
  
  async def run_if_implemented(self, method_name, *args):
    implemented = getattr(self.app.renx, method_name.lower(), False)
    if implemented:
      await implemented(*args)
  
  def authenticate(self):
    self.sock.send('a' + self.sockcfg['pass'])

  def subscribe(self):
    self.sock.send('s')

  async def send_command(self, cmd):
    self.sock.send('c{}'.format(cmd))

    response_event = asyncio.Event()
    response_id = str(uuid4())
    response_ident = [response_id, response_event]

    self.command_response_ids.append(response_ident)

    await response_event.wait()

    q_item = self.response_queue[response_id]
    data = q_item[:]
    del q_item
    return data

  async def message_welcome(self, message):
    self.authenticate()

  async def message_authenticated(self, message):
    self.subscribe()

  async def message_log(self, logType, event, data):
    await self.run_if_implemented(logType + '_' + event, data)

  async def parse_message_type(self, mtype, data):
    # self.app.ircHandle.privmsg(self.app.ircHandle.logChannel, data)
    
    if mtype == 'v':
      await self.message_welcome(data)

    elif mtype == 'a':
      await self.message_authenticated(data)

    elif mtype == 'l':
      data = data[1:].split('\x02')
      if len(data) < 2:
        print(data)
        return

      logType = data[0]
      event = data[1][:-1]
      data = data[2:]

      await self.message_log(logType, event, data)

    elif mtype == 'r':
      self.response_buffer.append(data[1:].split('\x02'))

    elif mtype == 'c':
      cmd_uid, cmd_event = self.command_response_ids.pop(0)

      self.response_queue[cmd_uid] = self.response_buffer[:]
      self.response_buffer = []
      cmd_event.set()

  async def parseMessage(self, message):
    typeID = message[0]
    await self.parse_message_type(typeID, message)
    
  async def onConnect(self):
    pass
    # asyncio.ensure_future(self.app.renx.periodic_playerList_update(), loop=self.app.loop)
  
# lPLAYER<>HWID;<>player<>Nod,4476,"GDK" Fireman<>hwid<>91F6973400004FFA
# lPLAYER<>HWID;<>player<>GDI,4466,fantasia<>hwid<>31D278100000C1D4

# lPLAYER<>Enter;<>GDI,4466,fantasia<>from<>37.23.183.6<>hwid<><>nosteam
# lPLAYER<>Enter;<>Nod,4476,"GDK" Fireman<>from<>79.233.168.99<>hwid<><>steamid<>0x011000010138E6D2
