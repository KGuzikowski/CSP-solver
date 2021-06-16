from typing import Generic, TypeVar, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from collections import deque

V = TypeVar('T') # variable type
D = TypeVar('D') # domain type

# base class for all constraints
class Constraint(Generic[V, D], ABC):
    # variables that the constraint is between
    def __init__(self, variables: List[V]) -> None:
        self.variables = variables
    
    # the relation
    # must be overriden by subclasses
    @abstractmethod
    def satisfied(self, assignment: Dict[V, D]) -> bool:
        pass


class CSP(Generic[V, D]):
    def __init__(self, variables: List[V], domains: Dict[V, List[D]]) -> None:
        self.variables: List[V] = variables # variables to be constrained
        self.domains: Dict[V, List[D]] = domains # domain of each variable TODO: spróbować set zamiast list / ew mapę bitową
        self.constraints: Dict[V, List[Constraint[V, D]]] = {}
        for variable in self.variables:
            self.constraints[variable] = []
            if variable not in self.domains:
                raise LookupError("Every variable should have a domain assigned to it!")

    def add_constraint(self, constraint: Constraint[V, D]) -> None:
        for variable in constraint.variables:
            if variable not in self.variables:
                raise LookupError("Variable in constraint not in CSP")
            else:
                self.constraints[variable].append(constraint)

    def solution_domain_to_solution(self) -> Dict[V, D]:
        assignment: Dict[V, D] = {}
        for variable, domain in self.domains.items():
            assignment[variable] = domain[0]
        return assignment

    def is_consistent(self, assignment: Dict[V, D]) -> bool:
        for constraint_list in self.constraints.values():
                for constraint in constraint_list:
                    if not constraint.satisfied(assignment):
                        return False
        return True

    def is_network_consistent(self, assignment: Dict[V, D] = None) -> bool:
        if assignment is not None:
            return self.is_consistent(assignment)

        is_every_domain_singleton = True
        for domain in self.domains.values():
            if len(domain) != 1:
                is_every_domain_singleton = False
                break

        if not is_every_domain_singleton:
            return False

        assignment: Dict[V, D] = self.solution_domain_to_solution()
        return self.is_consistent(assignment)

    # Check if the value assignment is consistent by checking all constraints
    # for the given variable against it
    def consistent(self, variable: V, assignment: Dict[V, D]) -> bool:
        for constraint in self.constraints[variable]:
                if not constraint.satisfied(assignment):
                    return False
        return True

    # selects unassigned variable using minimum-remaining-values heuristic
    # and degree heuristic for ties in minimum-remaining-value
    def select_unassigned_variable(self, variables: List[V]) -> Optional[V]:
        min_var: V = variables[0]
        min_domain_size: D = len(self.domains[min_var])

        for i in range(1, len(variables)):
            domain_size = len(self.domains[variables[i]])
            if domain_size == min_domain_size:
                var_constraints_num = len(self.constraints[variables[i]])
                min_var_constraints_num = len(self.constraints[min_var])
                if var_constraints_num > min_var_constraints_num:
                    min_domain_size = domain_size
                    min_var = variables[i]
            elif domain_size < min_domain_size:
                min_domain_size = domain_size
                min_var = variables[i]
        
        if min_domain_size == 0:
            return None
        return min_var 

    def restore_purged_values(self, purged_values: Dict[V, List[D]]) -> None:
        for var, domain in purged_values.items():
            for value in domain:
                self.domains[var].append(value)

    def revise_during_search(self, x: V, y: V, value: D, constraint: Constraint[V, D], purged_values: Dict[V, List[D]]) -> bool:
        revised: bool = False
        for val in self.domains[y]:
            if not constraint.satisfied({x: value, y: val}):
                self.domains[y].remove(val)
                purged_values[y].append(val)
                revised = True
        return revised

    # propagation implemented as forward checking heuristic
    # restores arc consistency for changed variable
    def interference(self, variable: V, value: D, assignment: Dict[V, D]) -> Optional[Dict[V, List[D]]]:
        purged_values: Dict[V, List[D]] = {}

        for constraint in self.constraints[variable]:
            y: V = constraint.variables[1] if constraint.variables[0] == variable else constraint.variables[0]
            if y not in assignment:
                purged_values[y] = []
                if self.revise_during_search(variable, y, value, constraint, purged_values):
                    if not self.domains[y]:
                        self.restore_purged_values(purged_values)
                        return False

        return purged_values


    def backtracking_search(self, assignment: Dict[V, D] = {}) -> Optional[Dict[V, D]]:
        # assignment is complete if every variable is assigned (our base case)
        if len(assignment) == len(self.variables):
            return assignment
        
        unassigned: List[V] = [v for v in self.variables if v not in assignment]
        current_var: Optional[Dict[V, D]] = self.select_unassigned_variable(unassigned)

        if current_var is None:
            return None

        local_assignment: Dict[V, D] = assignment.copy()
        # TODO: least-constraining-value heuristic for ordering values to check
        for value in self.domains[current_var]:
            local_assignment[current_var] = value
            purged_values: Optional[Dict[V, List[D]]] = {}
            # if this value is consistent, we continue
            if self.consistent(current_var, local_assignment):
                purged_values = self.interference(current_var, value, local_assignment)
                if purged_values is not False:
                    result: Optional[Dict[V, D]] = self.backtracking_search(local_assignment)
                    # if we didn't find the result, we will end backtracking
                    if result is not None:
                        return result
                    self.restore_purged_values(purged_values)
                    
        return None

    # revice method for AC-3 algorithm
    def revise_AC3(self, constraint: Constraint[V, D], x: V, y: V) -> Union[bool, Dict[V, List[D]]]:
        revised: bool = False
        for val_x in self.domains[x]:
            satisfy: bool = False
            for val_y in self.domains[y]:
                if constraint.satisfied({x: val_x, y: val_y}):
                    satisfy = True
                    break
            if not satisfy:
                self.domains[x].remove(val_x)
                revised = True
        return revised

    def AC3(self) -> bool:
        queue = deque()

        for var in self.variables:
            for arc in self.constraints[var]:
                if arc not in queue:
                    queue.append(arc)

        while queue:
            arc = queue.pop()
            x: V = arc.variables[0]
            y: V = arc.variables[1]
            if self.revise_AC3(arc, x, y):
                if not self.domains[x]:
                    return False
                for arc in self.constraints[x]:
                    queue.append(arc)

        return True