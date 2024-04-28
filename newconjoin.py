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

#coordinatesList1 = (1746.4135964754141, 1746.6935987127313, 1746.6935987127313, 1748.9946856979977, 1746.6935987127313, 1748.9946856979977, 1748.9946856979977, 1751.5271231093398, 2685.5, 2684.4, 2684.4, 2675.9210941936776, 2684.4, 2675.9210941936776, 2675.9210941936776, 2666.657987097062)
#coordinatesList2 = (179.03082131552594, 188.8726778912178, 1939.4734640201368, 1930.9999999999998)

def getDistanceTwoLines(curveA: list, curveB: list) -> float:
    d = getDistance(curveA[1], curveB[0])
    return d

#curveA = getCoordFromList(coordinatesList1)
#curveB = getCoordFromList(coordinatesList2)
#print(getDistanceTwoLines(curveA, curveB))

def CoordinatesPairs(n):
    a = lines[n]
    b = a[1:-1]
    c = b.split(' ')
    coordinatesList = getCoordinatesList(c)
    return getCoordFromList(coordinatesList)

def index_curve(curve: str):
    k = len(lines)
    curve = curve[1:-1]
    curve = curve.split(' ')
    coordinatesList = getCoordinatesList(curve)
    a = getCoordFromList(coordinatesList)
    for i in range(0,k):
        if CoordinatesPairs(i) == a:
            return i

SetCoordinatesPairs = [] #List các list mà mỗi list con gồm điểm đầu và cuối của curve
k = len(lines)
for i in range (0,k):
    SetCoordinatesPairs.append(CoordinatesPairs(i)) 
#print(SetCoordinatesPairs[0])
def order_of_curve(n):
    return SetCoordinatesPairs[n]
#print(order_of_curve(1731))

def index1_curve(curve: list):
    n = len(SetCoordinatesPairs)
    for i in range(0, n):
        if curve == SetCoordinatesPairs[i]:
            return i

S = SetCoordinatesPairs.copy()
k = len(S)
A = [order_of_curve(0)]
while len(A)<k:
    for curve in S:
        if curve in A:
            S.remove(curve)
    D = []
    for curve in S:
        D.append(getDistanceTwoLines(A[-1], curve))
    min_distance = min(D)
    for curve in S:
        if getDistanceTwoLines(A[-1], curve) == min_distance:
            A.append(curve)
            break        

def index_curve_inA(curve: list):
    k = len(A)
    for i in range(0,k):
        if curve == A[i]:
            return i
 
def Find_Curve_Form_Intial_End(curve: str) -> list:
    n = index_curve(curve)
    j = index_curve_inA(CoordinatesPairs(n))
    return A[j+1]

def Find_Curve(curve: str) -> str:
    for line in lines:
        h = index_curve(line)
        if CoordinatesPairs(h) == Find_Curve_Form_Intial_End(curve):
            return line
        
#curve = "(1746.4135964754141, 1746.6935987127313, 1746.6935987127313, 1748.9946856979977, 1746.6935987127313, 1748.9946856979977, 1748.9946856979977, 1751.5271231093398, 2685.5, 2684.4, 2684.4, 2675.9210941936776, 2684.4, 2675.9210941936776, 2675.9210941936776, 2666.657987097062) "
#print(Find_Curve(curve))


            






    


    






    
