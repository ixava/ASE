import configparser
import signal
from app import App


signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
	config = configparser.ConfigParser()
	config.read('pudf.ini')
	app = App(config)
	app.start()
