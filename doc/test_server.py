import multiprocessing, subprocess, time, random
import plac
from ishelve2 import ShelveInterface

i = plac.Interpreter(ShelveInterface(configfile=None))

COMMANDS = ['''\
.help
set a 1
''',
'''\
set b 1
wrong command
showall
''']

def telnet(commands, port):
    time.sleep(.5) # wait a bit for the server to start
    po = subprocess.Popen(['telnet', 'localhost', str(port)],
                          stdin=subprocess.PIPE)
    try:
        for cmd in commands.splitlines():
            po.stdin.write(cmd + '\n')
            time.sleep(.1) # wait a bit for the server to answer
    finally:
        po.stdin.close()

def test():
    port = random.choice(range(2000, 20000))
    clients = []
    for cmds in COMMANDS:
        cl = multiprocessing.Process(target=telnet, args=(cmds, port))
        clients.append(cl)
        cl.start()

    i.start_server(port, timeout=.5)
    for cl in clients:
        cl.join()
    i.stop_server()
