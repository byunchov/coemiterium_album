import notify2

notify2.init('Coemiterium Client')

notif = notify2.Notification(None, icon='/home/bobiyu/Documents/UNI/SP/KP/db/icon.png')
notif.set_urgency(notify2.URGENCY_NORMAL)
notif.set_timeout(10000)

txt = input('Enter message: ')

notif.update("Test", message=txt)
notif.show()