from utils import getRefinedCurve

def readData(filename: str) -> list[str]:
    with open (filename, 'r') as file:
        curvesList = file.readlines()
    return curvesList

def getxCurvesAndyCurvesFromCurvesList(curve: str) -> list[str]:
    curve = curve[1:-2]
    curve = curve.replace(' ', '')
    xCurve, yCurve = curve.split(',')
    xCurve, yCurve = getRefinedCurve(xCurve), getRefinedCurve(yCurve)

    return xCurve, yCurve

def getStartEndPoints(curvesList: list[str]):
    curveCoordinatesPairsList = []

    for curve in curvesList:
        xCurve, yCurve = getxCurvesAndyCurvesFromCurvesList(curve)
        
        x_0, y_0 = eval(xCurve.replace('t', '0')), eval(yCurve.replace('t', '0'))
        x_1, y_1 = eval(xCurve.replace('t', '1')), eval(yCurve.replace('t', '1'))
        
        curveCoordinatesPairsList.append([(x_0, y_0), (x_1, y_1)])
    
    return curveCoordinatesPairsList


