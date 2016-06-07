from __future__ import with_statement
from __future__ import division
import math
from random import random
import multiprocessing
import plac


class PiCalculator(object):
    """Compute pi in parallel with threads or processes"""

    @plac.annotations(
        npoints=('number of integration points', 'positional', None, int),
        mode=('sequential|parallel|threaded', 'option', 'm', str, 'SPT'))
    def __init__(self, npoints, mode='S'):
        self.npoints = npoints
        if mode == 'P':
            self.mpcommands = ['calc_pi']
        elif mode == 'T':
            self.thcommands = ['calc_pi']
        elif mode == 'S':
            self.commands = ['calc_pi']
        self.n_cpu = multiprocessing.cpu_count()

    def submit_tasks(self):
        npoints = math.ceil(self.npoints / self.n_cpu)
        self.i = plac.Interpreter(self).__enter__()
        return [self.i.submit('calc_pi %d' % npoints)
                for _ in range(self.n_cpu)]

    def close(self):
        self.i.close()

    @plac.annotations(npoints=('npoints', 'positional', None, int))
    def calc_pi(self, npoints):
        counts = 0
        for j in range(npoints):
            n, r = divmod(j, 1000000)
            if r == 0:
                yield '%dM iterations' % n
            x, y = random(), random()
            if x*x + y*y < 1:
                counts += 1
        yield (4.0 * counts) / npoints

    def run(self):
        tasks = self.i.tasks()
        for t in tasks:
            t.run()
        try:
            total = 0
            for task in tasks:
                total += task.result
        except:  # the task was killed
            print(tasks)
            return
        return total / self.n_cpu

if __name__ == '__main__':
    pc = plac.call(PiCalculator)
    pc.submit_tasks()
    try:
        import time
        t0 = time.time()
        print('%f in %f seconds ' % (pc.run(), time.time() - t0))
    finally:
        pc.close()
