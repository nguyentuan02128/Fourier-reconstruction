import elkai

with open('coordinates.txt', 'r') as file:
    lines = file.readlines() 

def getCoordinatesList(line: list[str]) -> list[float]:
    coordinatesList = []
    for number in line:
        coordinatesList.append(float(number[:-1]))
    return coordinatesList

def getCoordFromList(coordinatesList: list[float]) -> list:
    if len(coordinatesList) == 4:
        return [(coordinatesList[0], coordinatesList[2]), (coordinatesList[1], coordinatesList[3])]
    elif len(coordinatesList) == 16:
        return [(coordinatesList[0], coordinatesList[8]), (coordinatesList[7], coordinatesList[15])]

def getDistance(pointA: tuple, pointB: tuple) -> float:
    return ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)

def CoordinatesPairs(n):
    a = lines[n]
    b = a[1:-1]
    c = b.split(' ')
    coordinatesList = getCoordinatesList(c)
    return getCoordFromList(coordinatesList)

def distance_line(i, j):   # nhận vào đường cong thứ i, j, trả về d(i,j)
    return getDistance(CoordinatesPairs(i)[1], CoordinatesPairs(j)[0])

def list_distances(n):
    A = []
    i = 0
    while i < len(lines):
        A.append(distance_line(n, i))
        i = i+1
    return A

S = []
i = 0
while i < len(lines):
    S.append(list_distances(i))
    i = i+1

points = elkai.DistanceMatrix(S)

process = points.solve_tsp()

with open('result.txt', 'w') as file:
    file.write(str(process) + "\n")

print("Kết quả đã được ghi vào tệp result.txt")


