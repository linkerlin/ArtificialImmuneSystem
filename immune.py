__author__ = 'Stanislav Ushakov'

import math
import random
import copy
import json

from expression import Expression, Operations


def FitnessFunction(exact_values):
    """
    Used for calculating fitness function for
    given expression.
    Value is simple Euclidean norm for vector.

        Initializes function with the exact values of the needed function.
        Pass exact values in the following form:
        [({'x': 1, 'y': 1}, 0.125),
         ({'x': 2, 'y': 2}, 0.250)]
    """

    def expression_value(expression):#(expression, exact_values):
        """
        Returns value of the fitness function for given
        expression. The less the value - the closer expression to
        the unknown function.
        """
        sum = 0
        for (variables, value) in exact_values:
            sum += ((expression.value_in_point(variables) - value) *
                    (expression.value_in_point(variables) - value))
        return math.sqrt(sum)
    return expression_value#lambda (expression):expression_value(expression, exact_values)

class ExpressionMutator:
    """
    This class encapsulates all logic for mutating selected lymphocytes.
    """

    def __init__(self, expression):
        """
        Initializes mutator with the given expression.
        NOTE: expression itself won't be changed. Instead of its
        changing, the new expression will be returned.
        """
        self.expression = copy.deepcopy(expression)
        self.mutations = [
            self.number_mutation,
            self.variable_mutation,
            self.unary_mutation,
            self.binary_mutation,
            self.subtree_mutation]

    def mutation(self):
        """
        Returns the mutated version of the expression.
        All mutations are of equal possibilities.
        May be change.
        """
        mutation = random.choice(self.mutations)
        mutation()
        return self.expression

    def number_mutation(self):
        """
        USed for mutate number nodes. Adds or subtracts random number from
        the value or
        """
        numbers = self._get_all_nodes_by_filter(lambda n: n.is_number())
        if not numbers: return

        selected_node = random.choice(numbers)
        if random.random() < 0.45:
            selected_node.value += random.random()
        elif random.random() < 0.9:
            selected_node.value -= random.random()
        else:
            selected_node.value = round(selected_node.value)

    def variable_mutation(self):
        """
        Changes one randomly selected variable to another, also
        randomly selected.
        """
        variables = self._get_all_nodes_by_filter(lambda n: n.is_variable())
        if not variables: return

        selected_var = random.choice(variables)
        selected_var.value = random.choice(self.expression.variables)

    def unary_mutation(self):
        """
        Changes one unary operation to another
        """
        unary_operations = self._get_all_nodes_by_filter(lambda n: n.is_unary())
        if not unary_operations: return

        selected_unary = random.choice(unary_operations)
        selected_unary.operation = random.choice(Operations.get_unary_operations())

    def binary_mutation(self):
        """
        Changes one binary operations to another
        """
        binary_operations = self._get_all_nodes_by_filter(lambda n: n.is_binary())
        if not binary_operations: return

        selected_binary = random.choice(binary_operations)
        selected_binary.operation = random.choice(Operations.get_binary_operations())

    def subtree_mutation(self):
        """
        Changes one randomly selected node to the randomly generated subtree.
        The height of the tree isn't changed.
        """
        nodes = self._get_all_nodes_by_filter(lambda n: n.height() > 1 and
                                                        n != self.expression.root)
        if not nodes: return

        selected_node = random.choice(nodes)
        max_height = self.expression.root.height() - selected_node.height()
        new_subtree = Expression.generate_random(max_height, self.expression.variables)
        selected_node.operation = new_subtree.root.operation
        selected_node.value = new_subtree.root.value
        selected_node.left = new_subtree.root.left
        selected_node.right = new_subtree.root.right

    def _get_all_nodes_by_filter(self, filter_func):
        """
        Used for selecting all nodes satisfying the given filter.
        """
        nodes = []

        def traverse_tree(node):
            if filter_func(node):
                nodes.append(node)
            if node.left is not None:
                traverse_tree(node.left)
            if node.right is not None:
                traverse_tree(node.right)

        traverse_tree(self.expression.root)

        return nodes


class ExpressionsImmuneSystemConfig:
    """
    This class is used for storing immune system config.
    Config is stored in json file.
    """

    #config file name
    _filename = "config.json"

    #default values
    _number_of_lymphocytes_default = 100
    _number_of_iterations_default = 100
    _number_of_iterations_to_exchange_default = 25
    _maximal_height_default = 4

    def __init__(self):
        """
        Initializes config object with values retrieved from config file.
        """
        try:
            file = open(ExpressionsImmuneSystemConfig._filename)
            config = json.load(file)
            file.close()
        except IOError:
            config = None
        if config is None:
            self.number_of_lymphocytes = ExpressionsImmuneSystemConfig._number_of_lymphocytes_default
            self.number_of_iterations = ExpressionsImmuneSystemConfig._number_of_iterations_default
            self.number_of_iterations_to_exchange = ExpressionsImmuneSystemConfig._number_of_iterations_to_exchange_default
            self.maximal_height = ExpressionsImmuneSystemConfig._maximal_height_default
        else:
            self.number_of_lymphocytes = config['number_of_lymphocytes']
            self.number_of_iterations = config['number_of_iterations']
            self.number_of_iterations_to_exchange = config['number_of_iterations_to_exchange']
            self.maximal_height = config['maximal_height']

    def save(self):
        """
        Saves current configuration to config file.
        """
        file = open(ExpressionsImmuneSystemConfig._filename, mode='w')
        config = {'number_of_lymphocytes': self.number_of_lymphocytes,
                  'number_of_iterations': self.number_of_iterations,
                  'number_of_iterations_to_exchange': self.number_of_iterations_to_exchange,
                  'maximal_height': self.maximal_height}
        json.dump(config, file)
        file.close()


class ExpressionsImmuneSystem:
    """
    Class represents entire immune system.
    Now - this is simply algorithm, that works for a number of steps.
    On each step the best lymphocytes are selected for the mutation.
    """

    def __init__(self, exact_values, variables, exchanger, config):
        """
        Initializes the immune system with the exact_values, list of variables,
        exchanger object and config object.
        lymphocytes - list that stores current value of the whole system.
        """
        self.exact_values = exact_values
        self.variables = variables
        self.fitness_function = FitnessFunction(exact_values)
        self.exchanger = exchanger

        #config
        self.config = config

        self.lymphocytes = []
        for i in range(0, self.config.number_of_lymphocytes):
            self.lymphocytes.append(Expression.generate_random(
                self.config.maximal_height,
                variables))

        #Initialize Exchanger with the first generated lymphocytes
        self.exchanger.set_lymphocytes_to_exchange(self.lymphocytes[:])

        random.seed()

    def solve(self, accuracy=0.001):
        """
        After defined number of steps returns the best lymphocyte as
        an answer.
        """

        def return_best():
            best = self.best()
            best.simplify()
            return best

        for i in range(0, self.config.number_of_iterations):
            #if we reach exchanging step
            if i != 0 and i % self.config.number_of_iterations_to_exchange == 0:
                self.exchanging_step()
            else:
                self.step()
            best = self.best()
            if self.fitness_function(best) <= accuracy:
                return return_best()

        return return_best()

    def step(self):
        """
        Represents the step of the solution finding.
        The half of the lymphocytes are mutated. The new system
        consists of this half and their mutated 'children'.
        """
        sorted_lymphocytes = self._get_sorted_lymphocytes_index_and_value()
        best = []
        for (i, e) in sorted_lymphocytes[:self.config.number_of_lymphocytes // 2]:
            best.append(self.lymphocytes[i])
        mutated = [ExpressionMutator(e).mutation() for e in best]
        self.lymphocytes = best + mutated

    def exchanging_step(self):
        """
        Represents the step when we're getting lymphocytes from the other node.
        Take some lymphocytes from the exchanger and merge them with current available.
        Also set new lymphocytes to exchange (exactly - copy of them)
        """
        self.exchanger.set_lymphocytes_to_exchange(self.lymphocytes[:])
        others = self.exchanger.get_lymphocytes()
        self.lymphocytes = self.lymphocytes + others

        #get only best - as many as we need
        sorted_lymphocytes = self._get_sorted_lymphocytes_index_and_value()
        best = []
        for (i, e) in sorted_lymphocytes[:self.config.number_of_lymphocytes]:
            best.append(self.lymphocytes[i])

        self.lymphocytes = best

    def best(self):
        """
        Returns the best lymphocyte in the system.
        """
        return self.lymphocytes[self._get_sorted_lymphocytes_index_and_value()[0][0]]

    def _get_sorted_lymphocytes_index_and_value(self):
        """
        Returns list of lymphocytes and their numbers in the original system
        in sorted order.
        """
        fitness_values = []
        for (i, e) in enumerate(self.lymphocytes):
            fitness_values.append((i, self.fitness_function(e)))
        return sorted(fitness_values, key=lambda item: item[1])


class DataFileStorageHelper:
    """
    This helper class is used for storing exact function values in file and
    retrieving them.
    """

    @classmethod
    def save_to_file(cls, filename, variables, function, points_number,
                     min_point=-5.0, max_point=5.0):
        """
        Saves values of the function in randomly generated points.
        """
        values = []
        for i in range(0, points_number):
            arg_dict = {}
            for arg in variables:
                arg_dict[arg] = random.random() * (max_point - min_point) + min_point
            values.append((arg_dict, function(*arg_dict.values())))
        output = open(filename, 'w')
        for arg in variables:
            #print(arg, end=' ', file=output)
            output.write(str(arg) + " ")
            #print(file=output)
        output.write("\n")
        for (arg, f) in values:
            for var in variables:
                #print(arg[var], end=' ', file=output)
                output.write(str(arg[var]) + " ")

            #print(f, file=output)
            output.write(str(f))
        output.close()

    @classmethod
    def load_from_file(cls, filename):
        """
        Loads values of the function from file.
        Returns tuple (variables, values), where
        variables - list of variable names,
        values - list of ({'x': 0, 'y': 0}, 0)
        """
        input = open(filename)
        values = []
        variables = input.readline().split()
        for s in input:
            arg = s.split()[:-1]
            f = s.split()[-1]
            arg_dict = {}
            for i in range(0, len(variables)):
                arg_dict[variables[i]] = float(arg[i])
            values.append((arg_dict, float(f)))
        return variables, values