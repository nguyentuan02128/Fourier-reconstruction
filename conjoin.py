with open('coordinates.txt', 'r') as file:
    lines = file.readlines()

def getCoordinatesList(line: str) -> list[float]:
    coordinatesList = []
    for number in line:
        coordinatesList.append(float(number[:-1]))
    return coordinatesList

def getCoordFromList(coordinatesList: list[float]) -> list:
    if len(coordinatesList) == 4:
        return [(coordinatesList[0], coordinatesList[2]), (coordinatesList[1], coordinatesList[3])]
    elif len(coordinatesList) == 16:
        return [(coordinatesList[0], coordinatesList[8]), (coordinatesList[7], coordinatesList[15])]
    return coordinatesPairs
        
for line in lines:
    coordinatesPairs = []
    line = line[1:-3]
    line = line.split(' ')
    coordinatesList = getCoordinatesList(line)
    coordinatesPairs.append(getCoordFromList(coordinatesList))

def getDistance(pointA: tuple, pointB: tuple) -> float:
    return ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)