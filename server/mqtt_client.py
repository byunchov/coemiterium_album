import paho.mqtt.client as mqtt
from time import sleep
import signal
import sys
import notify2

if len(sys.argv) == 1:
    print("No arguments passed")
    TOPIC = "test"
else:
    TOPIC = sys.argv[1]


def signal_handler(sig, frame):
    print('\nTerminating server...')
    client.disconnect()
    client.loop_stop()
    sys.exit(0)


def on_connect(client, userdata, flags, rc):
    print(f'Connected with result code {rc}')
    # Subscribe (or renew if reconnect).
    client.subscribe(f'coemiterium/notification/{TOPIC}')


def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    print("MSG:", message)
    notif.update('Coemiterium Album Notifier', message)
    notif.show()


signal.signal(signal.SIGINT, signal_handler)

notify2.init('Coemiterium Client')

notif = notify2.Notification(None, icon='/home/bobiyu/Documents/UNI/SP/KP/db/icon.png')
notif.set_urgency(notify2.URGENCY_NORMAL)
notif.set_timeout(15000)

client = mqtt.Client("sub_coemiterium_125")
client.on_connect = on_connect  # Specify on_connect callback
client.on_message = on_message  # Specify on_message callback
client.connect('localhost', 1883, 60)

client.loop_forever()
