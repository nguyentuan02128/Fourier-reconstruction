import gurobipy as gp
from gurobipy import GRB

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

k = len(lines) - 1550

model = gp.Model('modelName')

I = range(0, k)
r = model.addVars(I, lb=0, ub=k-1, name="r", vtype=GRB.INTEGER)
c = model.addVars(I, I, name="c", vtype=GRB.BINARY)

'''
r(i) = j nếu đường cong thứ i trong danh sách ban đầu được sắp lại thành đường cong thứ j trong danh sách mới
c(i,j) = 1 nếu ta nối điểm cuối của đường cong thứ i với điểm đầu của đường cong thứ j, tức là, tồn tại l sao cho r(i)=l và r(j)=l+1
           hoặc r(i)=k-1 và r(j)=0
       = 0 nếu ngược lại
'''
'''
# Hai đường cong thứ i, j sẽ không được xếp vào cùng vị trí trong danh sách mới với mọi i khác j
for i in I:
    for j in I:
        if j != i:
            model.addConstr((r[i]-r[j])*(r[i]-r[j]) >= 1)
'''
# Với mọi i cố định, không thể nối điểm cuối đường cong thứ i với điểm đầu của chính nó
for i in I:
    model.addConstr(c[i, i] == 0)
# Với i cố định, điểm cuối của đường cong thứ i chỉ được nối với duy nhất điểm đầu của đường cong nào đó
for i in range(0,k):
    model.addConstr(gp.quicksum(c[i, j] for j in I) == 1)
# Với j cố định, tồn tại duy nhất điểm cuối của đường cong thứ i nào đó nối với điểm đầu của đường cong thứ j
for j in range(0,k):    
    model.addConstr(gp.quicksum(c[i, j] for i in I) == 1)
'''
# Với mọi (i,j), c(i,j) và c(j,i) không thể đồng thời bằng 1 khi len(lines)>=3
for i in I:
    for j in I:
        model.addConstr((c[i, j] + c[j, i] <= 1)) 
'''
model.addConstr(r[0] == 0)
# Mối liên hệ giữa r(i,j) với c(i,j)
for i in range(0,k):
    for j in range(1,k):
        if j != i:
            model.addConstr(r[i]-r[j]+1-(k-1)*(1-c[i, j])<=0)
  

sum_distance = gp.quicksum((c[i, j])*getDistance(CoordinatesPairs(i)[1], CoordinatesPairs(j)[0]) for i in I for j in I)

model.setObjective(sum_distance, sense=GRB.MINIMIZE)

model.optimize()
all_vars = model.getVars()
values = model.getAttr("X", all_vars)
names = model.getAttr("VarName", all_vars)

for name, val in zip(names, values):
    print(f"{name} = {val}")