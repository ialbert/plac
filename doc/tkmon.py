from __future__ import with_statement
import plac, multiprocessing

tkmon = plac.TkMonitor('tkmon', multiprocessing.Queue())

class Hello(object):
    mpcommands = ['hello', 'quit']
    def hello(self):
        yield 'hello'
    def quit(self):
        raise plac.Interpreter.Exit

if __name__ == '__main__':
    i = plac.Interpreter(Hello())
    i.add_monitor(tkmon)
    i.interact()

    
