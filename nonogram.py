from csp import Constraint, CSP
from typing import Dict, List, Optional

def generate_domain(var: str, line: List[int], cells_num: int, domains: Dict[str, List[List[str]]], possibility: List[str] = [], start_index: int = 0) -> None:
    if not line:
        for i in range(start_index, cells_num):
            possibility.append('.')
        domains[var].append(possibility)
        return

    min_fields_num: int = sum(line) + len(line) - 1
    val: int = line.pop(0)

    for i in range(start_index, cells_num):
        if i + min_fields_num <= cells_num:
            local_possibility = possibility.copy()
            for j in range(start_index, i):
                local_possibility.append('.')
            last_index: int = 0
            for j in range(val):
                local_possibility.append('#')
                last_index = i + j
            if last_index + 1 < cells_num:
                local_possibility.append('.')
                generate_domain(var, line.copy(), cells_num, domains, local_possibility, last_index + 2)
            else:
                domains[var].append(local_possibility)
                return


input_txt: List[str] = []
rows: List[str] = []
cols: List[str] = []
variables: List[str] = []
domains: Dict[str, List[List[str]]] = {}
i = 0
with open("zad_input.txt") as file: 
    input_txt = file.readlines()

rows_num = int(input_txt[0].split(' ')[0])
cols_num = int(input_txt[0].rstrip('\n').split(' ')[1])
input_txt = input_txt[1:]

for i in range(rows_num):
    line: List[str] = input_txt[i].rstrip('\n').split(' ')
    row: List[int] = []
    for val in line:
        row.append(int(val))
    var: str = 'row' + str(i)
    variables.append(var)
    rows.append(var)
    if var not in domains:
        domains[var] = []
    generate_domain(var, row, cols_num, domains)

for i in range(cols_num):
    line: List[str] = input_txt[i+rows_num].rstrip('\n').split(' ')
    col: List[int] = []
    for val in line:
        col.append(int(val))
    var: str = 'col' + str(i)
    variables.append(var)
    cols.append(var)
    if var not in domains:
        domains[var] = []
    generate_domain(var, col, rows_num, domains)

class NonogramArc(Constraint[str, List[str]]):
    def __init__(self, row: str, column: str):
        super().__init__([row, column])
    
    def satisfied(self, assignment: Dict[str, List[str]]) -> bool:
        row: str = self.variables[0]
        column: str = self.variables[1]

        # If either variable is not in the assignment then it is not
        # yet possible for them to conflict
        if row not in assignment or column not in assignment:
            return True
        
        row_num: int = int(row[3:])
        col_num: int = int(column[3:])
        # print('assignment: ', assignment)
        # print('rows: ', row, row_num)
        # print('cols: ', column, col_num)
        return assignment[row][col_num] == assignment[column][row_num]


csp: CSP[str, List[str]] = CSP(variables, domains)

for i in rows:
    for j in cols:
        csp.add_constraint(NonogramArc(i, j))

ac3 = csp.AC3()
solution: Optional[Dict[str, List[str]]]
if csp.is_network_consistent():
    print('AC3 found solution!')
    solution = csp.solution_domain_to_solution()
else:
    print('backtracking...')
    solution = csp.backtracking_search()

with open('zad_output.txt', 'w') as file:
    if solution is None:
        file.write("No solution found!")
    else:
        solution_sorted = []
        for i in range(rows_num):
            key = 'row' + str(i)
            solution_sorted.append(solution[key])

        for row in solution_sorted:
            line = ''
            for val in row:
                line += val
            file.write(line)
            file.write('\n')