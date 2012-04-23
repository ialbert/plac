import multiprocessing, subprocess, random, time
import plac
from ishelve2 import ShelveInterface

i = plac.Interpreter(ShelveInterface(configfile=None))

COMMANDS = ['''\
help
set a 1
''',
'''\
set b 1
wrong command
showall
''']

def telnet(commands, port):
    po = subprocess.Popen(['telnet', 'localhost', str(port)],
                          stdin=subprocess.PIPE)
    try:
        for cmd in commands.splitlines():
            po.stdin.write((cmd + '\n').encode('ascii'))
            time.sleep(.1) # wait a bit for the server to answer
    finally:
        po.stdin.close()

def test():
    port = random.choice(range(2000, 20000))
    server = multiprocessing.Process(target=i.start_server, args=(port,))
    server.start()
    clients = []
    for cmds in COMMANDS:
        cl = multiprocessing.Process(target=telnet, args=(cmds, port))
        clients.append(cl)
        cl.start()
    for cl in clients:
        cl.join()
    server.terminate()
    # should trap the output and check it
