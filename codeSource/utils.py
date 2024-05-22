def isDigit(char: str) -> bool:
    "Check if a string (a character) is a digit (from 0 to 9)."

    digitList = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    return char in digitList

def getDistance(pointA: tuple[float], pointB: tuple[float]) -> float:
    "Return the distance of 2 points A(x_A, y_A) and B(x_B, y_B)."

    distance = ((pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2)**(0.5)
    return round(distance, 6)

def getRefinedCurve(curve: str) -> str:
    "Add necessary operators so that the curve parametrization become understandable for Python eval() function."

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

def getConnectLine(startPoint: tuple[float], endPoint: tuple[float]) -> str:
    "Return the equation f(t) of the line that connects the given points. f(0, 1) is the segment between the points."

    x_0, x_1 = startPoint[0], endPoint[0]
    y_0, y_1 = startPoint[1], endPoint[1]

    return f'((1-t){x_0}+t{x_1}, (1-t){y_0}+t{y_1})'