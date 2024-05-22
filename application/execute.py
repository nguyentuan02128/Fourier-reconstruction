from codeSource import readData, getNewCurvesFile

curvesList = readData(filename='dataFolder\\curves.txt')
getNewCurvesFile(curvesList,newCurvesFile= 'dataFolder\\newCurves.txt')