from picalculator import PiCalculator


def test():
    pc = PiCalculator(10, 'T')
    tasks = pc.submit_tasks()
    for task in tasks:
        task.run()
    print(sum(task.result for task in tasks) / pc.n_cpu)
    pc.close()
