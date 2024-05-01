import scipy.integrate as sci
from scipy.misc import derivative

with open ('curves.txt', 'r') as file:
    lines = file.readlines()

def isDigit(char: str) -> bool:
    digitList = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    return char in digitList

def getRefinedCurve(curve: str) -> str:
    for pos in range(1, len(curve)):
        if curve[pos] == '(':
            if curve[pos-1] == ')' or isDigit(curve[pos-1]) or curve[pos-1] == 't':
                curve = curve[:pos] + '*' + curve[pos:]

    for pos in range(1, len(curve)):
        if curve[pos] == ')':
            if curve[pos+1] == '(' or isDigit(curve[pos+1]) or curve[pos+1] == 't':
                curve = curve[:(pos+1)] + '*' + curve[(pos+1):]

    for pos in range(1, len(curve)):
        if curve[pos] == 't':
            if isDigit(curve[pos-1]):
                curve = curve[:pos] + '*' + curve[pos:]
            elif isDigit(curve[pos+1]):
                curve = curve[:(pos+1)] + '*' + curve[(pos+1):]
    
    return curve

def getxCurveAndyCurveFromLine(line):
    line = line[1:-2]
    line = line.replace(' ', '')
    line = line.split(',')
    return line

def getConnectLine(startPoint: tuple, endPoint: tuple) -> str:
    x_0, x_1 = startPoint[0], endPoint[0]
    y_0, y_1 = startPoint[1], endPoint[1]
    return f'((1-t){x_0}+t{x_1}, (1-t){y_0}+t{y_1})'

def getStartEndPoints():
    curveCoordinatesPairsList = []

    for line in lines:
        line_xCurve, line_yCurve = getxCurveAndyCurveFromLine(line)

        x_0, y_0 = eval(line_xCurve.replace('t', '0')), eval(line_yCurve.replace('t', '0'))
        x_1, y_1 = eval(line_xCurve.replace('t', '1')), eval(line_yCurve.replace('t', '1'))
        
        curveCoordinatesPairsList.append([(x_0, y_0), (x_1, y_1)])
    
    return curveCoordinatesPairsList

def getDistance(pointA: tuple, pointB: tuple) -> float:
    return ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)

def connectTheCurves(curveCoordinatesPairsList: list):
    arrangedPairsList = [curveCoordinatesPairsList[0]]
    curveCoordinatesPairsList.pop(0)

    for _ in range(len(curveCoordinatesPairsList)):
        d = getDistance(arrangedPairsList[-1][1], curveCoordinatesPairsList[0][0])
        currentBest = curveCoordinatesPairsList[0]

        for coordinatesPair in curveCoordinatesPairsList:
            if getDistance(arrangedPairsList[-1][1], coordinatesPair[0]) < d:
                d = getDistance(arrangedPairsList[-1][1], coordinatesPair[0])
                currentBest = coordinatesPair
        arrangedPairsList.append(currentBest)
        curveCoordinatesPairsList.remove(currentBest)
    
    return arrangedPairsList

def getNewCurvesFile(arrangedPairsList: list) -> None:
    with open ('newcurves.txt', 'w') as newfile:
        for n in range(len(lines)):
            newfile.writelines(lines[n])
            if n == len(lines) - 1:
                break
            newfile.writelines(getConnectLine(arrangedPairsList[n][1], arrangedPairsList[n+1][0]) + '\n')

def splitCurve(xCurve, yCurve, n: int) -> list:
    splitSteps = []
    splitPoints = []

    def getDerivative(t: float) -> float:
        return (xCurve(t)**2 + yCurve(t)**2)**0.5

    I, R = sci.quad(getDerivative, 0, 1)
    var = 0
    current = 0

    for k in range(n*1000):
        I_k, R_k = sci.quad(getDerivative, current, current + 1/(n*1000))
        var += I_k
        if abs(I/n - var) < 1 and len(splitSteps) < n-1:
            splitSteps.append(k/(n*1000))
            var = 0
        current += 1/(n*1000)
    
    for t in splitSteps:
        splitPoints.append((xCurve(t), yCurve(t)))
    return splitPoints

def getSplitPoints():
    curvesSplitPoints = []

    with open('splitPoints.txt', 'w') as splitPointsFile:
        for k in range(1732):
            line = lines[k]
            # xCurve, yCurve = getxCurveAndyCurveFromLine(line)

            def xCurveFunction(t: float) -> float:
                xCurve = getxCurveAndyCurveFromLine(line)[0]
                curve = xCurve
                curve = getRefinedCurve(str(curve))
                xCurve = curve.replace('t', f'{t}')
                return eval(xCurve)
            
            def yCurveFunction(t: float) -> float:
                yCurve = getxCurveAndyCurveFromLine(line)[1]
                curve = yCurve
                curve = getRefinedCurve(str(curve))
                yCurve = curve.replace('t', f'{t}')
                return eval(yCurve)
            
            newPoints = [(xCurveFunction(0), yCurveFunction(0))] + splitCurve(xCurve=xCurveFunction, yCurve=yCurveFunction, n=4) + [(xCurveFunction(1), yCurveFunction(1))]
            curvesSplitPoints += newPoints
            splitPointsFile.writelines(f'{newPoints}'[1:-1] + '\n')
        return curvesSplitPoints

print(getSplitPoints())