from __future__ import with_statement
import plac

class Hello(object):
    mpcommands = ['hello', 'quit']
    def hello(self):
        yield 'hello'
    def quit(self):
        raise plac.Interpreter.Exit

if __name__ == '__main__':
    i = plac.Interpreter(Hello())
    i.add_monitor(plac.TkMonitor('tkmon'))
    i.interact()
