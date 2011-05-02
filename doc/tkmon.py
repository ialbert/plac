from __future__ import with_statement
import plac

class Hello(object):
    mpcommands = ['hello']
    def hello(self):
        yield 'hello'

if __name__ == '__main__':
    i = plac.Interpreter(Hello())
    i.add_monitor(plac.TkMonitor('tkmon'))
    with i:
        i.interact()
        
