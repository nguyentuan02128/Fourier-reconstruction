with open('coordinates.txt', 'r') as file:
    lines = file.readlines() 

with open('result.txt', 'r') as file:
    newlines = file.readline()

newlines = newlines[1:-2]
newlines = newlines.split(', ')

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

def equation_newline(i):
    if distance_line(int(newlines[i]), int(newlines[i+1])) != 0:
        a = CoordinatesPairs(i)[1]
        b = CoordinatesPairs(i+1)[0]
        return f"((1-t){a[0]}+t{b[0]},(1-t){a[1]}+t{b[1]})"

def all_equations():
    E = []
    for i in range(0, len(newlines)-1):
        if distance_line(int(newlines[i]), int(newlines[i+1])) != 0:
            E.append(equation_newline(i))
    return E

with open('newcurvesversion2.txt', 'a') as file:
    for newline in all_equations():
        file.write(newline + '\n')
    
print("Kết quả đã được ghi")