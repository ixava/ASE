import asyncio, time, copy

class Renx:
  def __init__(self, app):
    self.playerList = {}
    self.ipdb_queue = {}
    self.app = app

  def playerList_update(self, newDict):
    self.playerList = newDict

  async def player_enter(self, data):
    pteam, pid, pname = data[0].split(',', 2)
    pIP = data[2]
    # data = data[5:]
    # phost = await self.app.getHost(pIP)
    self.ipdb_queue_add(pid)

  def ipdb_queue_add(self, id):
    if id in self.ipdb_queue:
      print('WARNING: tried to add duplicate player to ipdb_queue ')
    else:
      self.ipdb_queue[id] = time.time()

  async def process_ipdb_queue(self):
    q = self.ipdb_queue
    pl = self.playerList

    processed = []

    for pid, added in copy.deepcopy(q).items():
      should_delete = False
      if pid in pl:
        user_values = {k: v for k, v in pl[pid].items() if k in ['ip_int','hwid','name','steamid','ip', 'hostname']}
        if user_values['hwid'] == '':
          continue
        user = await self.app.db.process_user(user_values)
        self.app.ircHandle.privmsg(self.app.ircHandle.logChannel, "User: {}, Risk:{}".format(user['names_name'], user['ips_risk']))
        if user['ips_risk'] > 0.90:
          self.app.ircHandle.privmsg(self.app.ircHandle.alertsChannel, 
            "{} joined the game from a flagged IP address; Risk: {}".format(user['names_name'],user['ips_risk'])
          )
        should_delete = True
      else:
        if time.time() - added > 30:
          should_delete = True
      if should_delete:
        processed.append(pid)
    self.ipdb_queue = {k: v for k, v in self.ipdb_queue.items() if not k in processed }

  async def user_check(self, user):
    pass

  async def player_changeid(self, data):
    q = self.ipdb_queue
    newID, oldID = data[1::2]

    if oldID in q:
      q[newID] = q[oldID]
      del q[oldID]
    else:
      print('player changed id but old id was not found in playerlist, adding anyway')
      self.ipdb_queue_add(newID)

  async def update_playerList(self, data):
    processed_players = {k: v for k, v in self.playerList.items() if k in data}
    players_buffer = {}

    for pID, pData in data.items():
      unicode_name = pData['name'].encode('ascii').decode('unicode-escape')

      if pID not in processed_players:
        ref = {}
        ref['steamid'] = pData['steam']
        ref['hostname'] = await self.app.getHost(pData['ip'])
        ref['ip_int'] = self.app.db.longIP(pData['ip'])
        ref['name'] = unicode_name
        players_buffer[pID] = {**pData, **ref}
      else:
        if pID not in self.playerList:
          return
        players_buffer[pID] = {**self.playerList[pID], **pData, 'name': unicode_name}

    self.playerList = players_buffer
    await self.process_ipdb_queue()

  async def periodic_playerList_update(self):
    data = await self.app.rconHandle.send_command('clientvarlist id name ip hwid steam score ping')
    headers = data[0][1:]
    data = data[1:]
    player_data = {v[0]: (dict(zip(headers, v[1:]))) for v in data}
    await self.update_playerList(player_data)

    return




