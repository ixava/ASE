import asyncio
from functools import partial

def executor_fun(fn):
  def decorator(self, *args, **kwargs):
    partfn = partial(fn, self, *args, **kwargs)
    self.app.loop.run_in_executor(self.app.iopool, partfn)
  return decorator

def reconnect_async(fn):
    async def decorator(self, *args, **kwargs):
        if not self.isConnected:
            return false
        try:
            return await fn(self, *args, **kwargs)
        except IOError as e:
            print("Error: {}".format(e))
            await self.reconnect()
            return False
    return decorator

def reconnect_sync(fn):
    def decorator(self, *args, **kwargs):
        if not self.isConnected:
            return
        try:
            return fn(self, *args, **kwargs)
        except IOError as e:
            print("Error: {}".format(e))
            asyncio.ensure_future(self.reconnect(), loop=self.app.loop)
    return decorator

class TCPWrapper:
    def __init__(self, host=None, port=None, handle=None, decoding=None, encoding="iso-8859-1", app=None, **kwargs):
      self.host = host
      self.port = port
      self.app = app
      self.handle = handle
      self.encoding = encoding
      self.decoding = decoding if decoding else self.encoding
      self.writer = None
      self.reader = None
      self.isConnected = False

    async def connect(self):
        while True:
            try:
                print("Trying to connect {}:{}".format(self.host,self.port))
                self.reader, self.writer = await asyncio.open_connection(host=self.host, port=self.port, loop=self.app.loop)
            except OSError as e:
                print('Connection failed to host:{} port:{}, retrying in 5 sec'.format(self.host, self.port))
                await asyncio.sleep(5)
            else:
                self.isConnected = True
                print("Connected to {}:{}".format(self.host,self.port))
                await self.handle.onConnect()
                break

    @reconnect_async
    async def readLine(self):
        line = await self.reader.readline()
        if not line:
            return False
        return line.decode(self.decoding)

    @executor_fun
    @reconnect_sync
    def send(self, message):
        self.writer.write((message + '\n').encode(self.encoding))

    async def reconnect(self):
        self.isConnected = False
        print("Lost connection to {}:{}, trying to reconnect".format(self.host,self.port))
        await self.connect()

    async def run(self):
        data = await self.readLine()
        print(data)
        if data:
            asyncio.ensure_future(self.handle.parseMessage(data.rstrip()))

class ClientWrapper:
    def __init__(self, app=None, sockcfg=None, **kwargs):
        self.app = app
        self.sockcfg = sockcfg

        self.sock = TCPWrapper(**sockcfg, app=self.app, handle=self)
        if 'encoding' in kwargs:
            self.sock.encoding = kwargs['encoding']
        if 'decoding' in kwargs:
            self.sock.encoding = kwargs['decoding']