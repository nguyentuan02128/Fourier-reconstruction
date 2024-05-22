import scipy.integrate as sci
from scipy.misc import derivative

from utils import getConnectLine
from readData import getStartEndPoints, readData
from TSP import arrangeTheCurves

def getConnectLine(startPoint: tuple, endPoint: tuple) -> str:
    x_0, x_1 = startPoint[0], endPoint[0]
    y_0, y_1 = startPoint[1], endPoint[1]
    return f'((1-t){x_0}+t{x_1}, (1-t){y_0}+t{y_1})'

def getNewCurvesFile(curvesList: list[str], newCurvesFile: str) -> None:
    curveCoordinatesPairsList = getStartEndPoints(curvesList)
    permutation = arrangeTheCurves(curvesList)

    with open (newCurvesFile, 'w') as newfile:
        for n in range(len(curvesList)):
            newfile.writelines(curvesList[permutation[n]])
            newfile.writelines(getConnectLine(curveCoordinatesPairsList[permutation[n]][1], curveCoordinatesPairsList[permutation[n+1]][0]) + '\n')

# def splitCurve(xCurve, yCurve, n: int) -> list:
#     splitSteps = []
#     splitPoints = []

#     def getDerivative(t: float) -> float:
#         return (xCurve(t)**2 + yCurve(t)**2)**0.5

#     I, R = sci.quad(getDerivative, 0, 1)
#     var = 0
#     current = 0

#     for k in range(n*1000):
#         I_k, R_k = sci.quad(getDerivative, current, current + 1/(n*1000))
#         var += I_k
#         if abs(I/n - var) < 1 and len(splitSteps) < n-1:
#             splitSteps.append(k/(n*1000))
#             var = 0
#         current += 1/(n*1000)
    
#     for t in splitSteps:
#         splitPoints.append((xCurve(t), yCurve(t)))
#     return splitPoints

# def getSplitPoints():
#     curvesSplitPoints = []

#     with open('splitPoints.txt', 'w') as splitPointsFile:
#         for k in range(1732):
#             line = lines[k]
#             # xCurve, yCurve = getxCurveAndyCurveFromLine(line)

#             def xCurveFunction(t: float) -> float:
#                 xCurve = getxCurveAndyCurveFromLine(line)[0]
#                 curve = xCurve
#                 curve = getRefinedCurve(str(curve))
#                 xCurve = curve.replace('t', f'{t}')
#                 return eval(xCurve)
            
#             def yCurveFunction(t: float) -> float:
#                 yCurve = getxCurveAndyCurveFromLine(line)[1]
#                 curve = yCurve
#                 curve = getRefinedCurve(str(curve))
#                 yCurve = curve.replace('t', f'{t}')
#                 return eval(yCurve)
            
#             newPoints = [(xCurveFunction(0), yCurveFunction(0))] + splitCurve(xCurve=xCurveFunction, yCurve=yCurveFunction, n=4) + [(xCurveFunction(1), yCurveFunction(1))]
#             curvesSplitPoints += newPoints
#             splitPointsFile.writelines(f'{newPoints}'[1:-1] + '\n')
#         return curvesSplitPoints