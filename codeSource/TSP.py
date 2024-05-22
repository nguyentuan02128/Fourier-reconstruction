from tsp_solver.greedy import solve_tsp
from utils import getDistance
from readData import getStartEndPoints, readData

# import numpy as np
# from python_tsp.exact import solve_tsp_dynamic_programming, solve_tsp_branch_and_bound

def getDistanceMatrix(curvesList: list[str]) -> list[list[float]]:
    "Return an assymetric matrix with entry at (i, j) being the distance between i-th curve endpoint and j-th curve startpoint."

    curveCoordinatesPairsList = getStartEndPoints(curvesList)
    n = len(curveCoordinatesPairsList)
    distances = []
    
    for i in range(n):
        row = []
        for j in range(n):
            d_ij = getDistance(curveCoordinatesPairsList[i][1], curveCoordinatesPairsList[j][0])
            row.append(d_ij)
        distances.append(row)
    
    return distances

def arrangeTheCurves(curvesList: list[str]) -> list[int]:
    """
    Return the order of the curves that would give the miminal total of additional length.
    This function uses Python's TSP solver
    """
    
    distances = getDistanceMatrix(curvesList)

    arrangement = solve_tsp(distances)

    return arrangement

# def getDistanceMatrix1(curvesList: list[str]) -> np.ndarray:
#     "Return an assymetric matrix with entry at (i, j) being the distance between i-th curve endpoint and j-th curve startpoint."

#     curveCoordinatesPairsList = getStartEndPoints(curvesList)
#     n = len(curveCoordinatesPairsList)
#     distances = []
    
#     for i in range(n):
#         row = []
#         for j in range(n):
#             if j == i:
#                 row.append(0)
#             else:
#                 d_ij = getDistance(curveCoordinatesPairsList[i][1], curveCoordinatesPairsList[j][0])
#                 row.append(d_ij)
#         distances.append(row)
    
#     return np.array(distances)

# def arrangeTheCurves1(curvesList) -> list[int]:
#     """
#     Return the order of the curves that would give the miminal total of additional length.
#     This function uses Python's TSP solver
#     """
    
#     distances = getDistanceMatrix1(curvesList)

#     arrangement, distance = solve_tsp_dynamic_programming(distances)

#     return arrangement, distance

