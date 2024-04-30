# with open('coordinates.txt', 'r') as file:
#     lines = file.readlines()

# def getCoordinatesList(line: str) -> list[float]:
#     coordinatesList = []
#     for number in line:
#         coordinatesList.append(float(number[:-1]))
#     return coordinatesList

# def getCoordFromList(coordinatesList: list[float]) -> list:
#     if len(coordinatesList) == 4:
#         return [(coordinatesList[0], coordinatesList[2]), (coordinatesList[1], coordinatesList[3])]
#     elif len(coordinatesList) == 16:
#         return [(coordinatesList[0], coordinatesList[8]), (coordinatesList[7], coordinatesList[15])]
#     return coordinatesPairs
        
# coordinatesPairs = []

# for line in lines:
#     line = line[1:-3]
#     line = line.split(' ')
#     coordinatesList = getCoordinatesList(line)
#     coordinatesPairs.append(getCoordFromList(coordinatesList))

# def getDistance(pointA: tuple, pointB: tuple) -> float:
#     return ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)

# print(coordinatesPairs)

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

curveCoordinatesPairsList = []

for line in lines:
    line = line[1:-2]
    line = line.replace(' ', '')
    line = line.split(',')

    line_xCurve = getRefinedCurve(line[0])
    line_yCurve = getRefinedCurve(line[1])

    x_0, y_0 = eval(line_xCurve.replace('t', '0')), eval(line_yCurve.replace('t', '0'))
    x_1, y_1 = eval(line_xCurve.replace('t', '1')), eval(line_yCurve.replace('t', '1'))
    
    curveCoordinatesPairsList.append([(x_0, y_0), (x_1, y_1)])

def getDistance(pointA: tuple, pointB: tuple) -> float:
    return ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)

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

# print(arrangedPairsList)

def getConnectLine(startPoint: tuple, endPoint: tuple) -> str:
    x_0, x_1 = startPoint[0], endPoint[0]
    y_0, y_1 = startPoint[1], endPoint[1]
    return f'((1-t){x_0}+t{x_1}, (1-t){y_0}+t{y_1})'

with open ('newcurves.txt', 'w') as newfile:
    for n in range(len(lines)):
        newfile.writelines(lines[n])
        if n == len(lines) - 1:
            break
        newfile.writelines(getConnectLine(arrangedPairsList[n][1], arrangedPairsList[n+1][0]) + '\n')