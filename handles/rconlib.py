from lib.wrappers import ClientWrapper
import asyncio

class RconHandle(ClientWrapper):
  def __init__(self, app):
    super().__init__(sockcfg=app.config['RCON'], app=app, decoding='unicode-escape')
    self.playerBuffer = {}

  async def onConnect(self):
    self.app.ircHandle.broadcast('Connected to RenX')

  async def parseMessage(self, message):
    typeID = message[0]

    if typeID == 'v':
      self.sock.send("a"+self.sockcfg['pass'])
    elif typeID == 'a':
      self.sock.send("s")
    # elif typeID == 'l':
    #   data = message[1:].split('\x02')
    #   logType = data[0]
    #   if len(data) < 2:
    #     print("Not enough data?!?!?!?!     "+' '.join(data))
    #     return
    #   event = data[1][:-1]
    #   data = data[2:]
    #   if logType == 'PLAYER':
    #     if event == 'Enter':
    #       pteam, pid, pname = data[0].split(',', 2)
    #       pIP = data[2]
    #       data = data[5:]
    #       phost = await self.app.getHost(pIP)
    #       if data[0] == 'nosteam':
    #         psteamID = '-'
    #       elif data[0] == 'steamid':
    #         psteamID = data[1]
    #       print('Player {} {} added'.format(pid, pname))
    #       self.playerBuffer[pid] = {
    #         'name': pname,
    #         'ip': pIP,
    #         'steamid': psteamID,
    #         'hostname': phost
    #       }
    #     elif event == 'HWID':
    #       hwid = data[-1]
    #       pid = data[1].split(',', 2)[1]
    #       if pid not in self.playerBuffer:
    #         await asyncio.sleep(1)
    #       if pid in self.playerBuffer:
    #         item = self.playerBuffer[pid]
    #         item['hwid'] = hwid
    #         print('\n')
    #         print(item)
    #         print('\n')
    #         res = await self.app.db.user_get(**item)
    #         if res:
    #           print(res)
    #         del self.playerBuffer[pid]
    #     elif event == 'ChangeID':
    #       oldID = data[3]
    #       newID = data[1]
    #       if oldID in self.playerBuffer:
    #         self.playerBuffer[newID] = self.playerBuffer[oldID]
    #         del self.playerBuffer[oldID]
    #     print('\n')
    #     print(self.playerBuffer)
    #     print('\n')
    # self.app.ircHandle.privmsg(self.app.ircHandle.logChannel, '<>'.join(message.split('\x02')))    


# lPLAYER<>HWID;<>player<>Nod,4476,"GDK" Fireman<>hwid<>91F6973400004FFA
# lPLAYER<>HWID;<>player<>GDI,4466,fantasia<>hwid<>31D278100000C1D4

# lPLAYER<>Enter;<>GDI,4466,fantasia<>from<>37.23.183.6<>hwid<><>nosteam
# lPLAYER<>Enter;<>Nod,4476,"GDK" Fireman<>from<>79.233.168.99<>hwid<><>steamid<>0x011000010138E6D2