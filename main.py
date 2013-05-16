__author__ = 'Stanislav Ushakov'

import math
import time

from expression import Expression
from immune import ExpressionsImmuneSystem, FitnessFunction, DataFileStorageHelper, ExpressionsImmuneSystemConfig
from exchanger import SimpleRandomExchanger


def update_progress(progress):
    """
    Shows progress bar. Progress is passed in percent.
    """
    print '\r[{0}] {1}%'.format('#' * (progress // 10), progress)


if __name__ == "__main__":
    number_of_lymphocytes = 100
    max_height = 4

    DataFileStorageHelper.save_to_file('test_x_y.txt', ['x', 'y'], lambda x, y: x * x + x * y * math.sin(x * y), 100)

    variables, values = DataFileStorageHelper.load_from_file('test_x_y.txt')

    f = FitnessFunction(values)
    exchanger = SimpleRandomExchanger(
        lambda: [Expression.generate_random(max_height=max_height, variables=variables)
                 for i in range(0, number_of_lymphocytes // 2)])

    config = ExpressionsImmuneSystemConfig()

    results = []
    iterations = 5
    start = time.clock()
    for i in range(0, iterations):
        immuneSystem = ExpressionsImmuneSystem(exact_values=values,
                                               variables=variables,
                                               exchanger=exchanger,
                                               config=config)
        best = immuneSystem.solve()
        results.append((f(best), str(best)))
        update_progress(int((i + 1) / iterations * 100))
    end = time.clock()
    print('\n{0} seconds'.format(end - start))
    for result in sorted(results):
        print result