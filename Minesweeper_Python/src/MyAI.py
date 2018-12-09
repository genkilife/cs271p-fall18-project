# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#               agent in this file. You will write the 'getAction' function,
#               the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#               - DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action
import time
import random
class Term():
    def __init__(self, coff=None, var=None):
        self.coefficient = coff
        self.var = var
    def __le__(self, other):
        return self.coefficient < other.coefficient

class PolynomialEqation():
    def __init__(self, numOfBomb=None, terms=None):
        self.numOfBomb = numOfBomb
        self.terms = terms
    
    def __le__(self, other):
        if len(self.terms) < len(other.terms):
            return True
        elif len(self.terms) > len(other.terms):
            return False
        else:
            for i in range(len(self.terms)):
                if self.terms[i] < other.terms[i]:
                    return True
                elif self.terms[i] > other.terms[i]:
                    return False
        return False

# todo: solve the scenario when we couldn't make sure any tiles which are mines or empty

class MyAI(AI):
    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        self.rowTotal = rowDimension
        self.colTotal = colDimension
        self.minesTotal = totalMines

        self.tileInfo = [[-1 for _ in range(colDimension)] for _ in range(rowDimension)]
        self.dirs = [[-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1], [-1, -1], [0, -1], [1, -1]]
        self.colX = startX
        self.rowY = startY
        self.nextAction = AI.Action.LEAVE
        self.uncoveredNum = 0
        self.flagNum = 0

        self.trySolutions = []
        self.knownMine = [[-5 for _ in range(colDimension)] for _ in range(rowDimension)]
        self.knownEmpty = [[-5 for _ in range(colDimension)] for _ in range(rowDimension)]
        self.knownMineQueue = []
        self.knownEmptyQueue = []
        self.borderTiles = []
        self.uncertainTile = []
        pass

    def updateTileInfo(self, info: int, x: int, y: int):
        # information of the tile
        # 0-8: # of mines around the tile
        # -1: covered
        # -2: flagged
        if info == -1:
            self.tileInfo[self.rowTotal-1-y][x] = -2  # need to take care of UNFLAG action
            self.knownMine[self.rowTotal - 1 - y][x] = True
        else:
            self.tileInfo[self.rowTotal-1-y][x] = info
            self.knownEmpty[self.rowTotal - 1 - y][x] = True
        return

    # check if the tile were the boundary so far
    def _isBorder(self, x: int, y: int) -> bool:
        if self.tileInfo[self.rowTotal-1-y][x] != -1:
            return False

        for i, j in self.dirs:
            nx, ny = x+i, y+j
            if self._isBoardBound(nx, ny) and self.tileInfo[self.rowTotal-1-ny][nx] != -1:
                return True
        return False

    # check if the tile were inside boarder boundary
    def _isBoardBound(self, x: int, y: int) -> bool:
        if 0 <= x < self.colTotal and 0 <= y < self.rowTotal:
            return True
        return False

    # count how many covered tiles around position(x, y)
    def countCoveredTiles(self, tileInfo: list, x: int, y: int):
        coveredTiles = 0
        for i, j in self.dirs:
            nx, ny = x+i, y+j
            if self._isBoardBound(nx, ny) and tileInfo[self.rowTotal-1-ny][nx] == -1:
                coveredTiles += 1
            else:
                continue
        return coveredTiles

    # count how many flagged tiles around position(x, y)
    def countFlaggedTiles(self, tileInfo: list, x: int, y: int):
        flaggedTiles = 0
        for i, j in self.dirs:
            nx, ny = x+i, y+j
            if self._isBoardBound(nx, ny) and tileInfo[self.rowTotal-1-ny][nx] == -2:
                flaggedTiles += 1
            else:
                continue
        return flaggedTiles

    # try to flag all determined mines around tile (rowY, colX)
    def tryFlag(self):
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] > 0:
                    curMines = self.tileInfo[self.rowTotal-1-j][i]
                    curCoveredTiles = self.countCoveredTiles(self.tileInfo, i, j)
                    curFlaggedTiles = self.countFlaggedTiles(self.tileInfo, i, j)
                    if curMines - curFlaggedTiles == curCoveredTiles:
                        for ni, nj in self.dirs:
                            if self._isBoardBound(i+ni, j+nj) and self.tileInfo[self.rowTotal-1-j-nj][i+ni] == -1:
                                if (i+ni, j+nj) in self.knownMineQueue:
                                    self.knownMineQueue.remove((i+ni, j+nj))
                                self.colX, self.rowY = i+ni, j+nj
                                self.nextAction = AI.Action.FLAG
                                return True
        return False

    # try to uncover all determined empty tiles around tile (rowY, colX)
    def tryMove(self):
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0:
                    curMines = self.tileInfo[self.rowTotal-1-j][i]
                    curCoveredTiles = self.countCoveredTiles(self.tileInfo, i, j)
                    curFlaggedTiles = self.countFlaggedTiles(self.tileInfo, i, j)
                    if curMines == curFlaggedTiles and curCoveredTiles > 0:
                        for ni, nj in self.dirs:
                            if self._isBoardBound(i+ni, j+nj) and self.tileInfo[self.rowTotal-1-j-nj][i+ni] == -1:
                                if (i+ni, j+nj) in self.knownEmptyQueue:
                                    self.knownEmptyQueue.remove((i+ni, j+nj))
                                self.colX, self.rowY = i+ni, j+nj
                                self.nextAction = AI.Action.UNCOVER
                                return True
        return False

    #
    def trySolver(self):

        borderEmptyTiles = []
        # emptyTiles = []

        # check how many empty tiles under dilemma scenario
        # for i in range(self.colTotal):
        #     for j in range(self.rowTotal):
        #         if self.tileInfo[self.rowTotal-1-j][i] == -1:
        #             emptyTiles.append((i, j))  # need to sync the format

        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self._isBorder(i, j):
                    borderEmptyTiles.append((i, j))

        if len(borderEmptyTiles) > 20:
            return

        self.borderTiles.clear()
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0 and self.countCoveredTiles(self.tileInfo, i, j) > 0:
                    self.borderTiles.append((i, j))

        # skip optimized method
        # borderEmptyTiles = emptyTiles

        segregated = []
        segregated.append(borderEmptyTiles)

        # complex part
        totalMultCases = 1
        for i in range(len(segregated)):

            # copy everything into temporary objects
            try_TileInfo = self.tileInfo.copy()

            self.trySolutions.clear()
            self.knownMine = [[-1 for _ in range(self.colTotal)] for _ in range(self.rowTotal)]
            self.knownEmpty = [[-1 for _ in range(self.colTotal)] for _ in range(self.rowTotal)]
            for s in range(self.colTotal):
                for t in range(self.rowTotal):
                    if try_TileInfo[self.rowTotal-1-t][s] >= 0:
                        self.knownEmpty[self.rowTotal-1-t][s] = 0
                    elif try_TileInfo[self.rowTotal-1-t][s] == -2:
                        self.knownEmpty[self.rowTotal-1-t][s] = 0
                        self.knownMine[self.rowTotal-1-t][s] = -2

            startTime = time.time()
            self.tryRecursive(segregated[i], 0)
            endTime = time.time()

            # print("Total tryRecursion time: ", endTime - startTime)

            # something wrong during tryRecursive
            if len(self.trySolutions) == 0:
                return

            # check for solved tiles
            for j in range(len(segregated[i])):
                allMine = True
                allEmpty = True
                for sln in self.trySolutions:
                    if sln[j] is False:
                        allMine = False
                    if sln[j]:
                        allEmpty = False

                qi, qj = segregated[i][j]

                if allMine:
                    self.knownMineQueue.append((qi, qj))
                if allEmpty:
                    self.knownEmptyQueue.append((qi, qj))

            totalMultCases += len(self.trySolutions)

            # calculate probabilities in case we need it

        return

    def tryRecursive(self, borderTile, k):
        # possible combination found
        if k == len(borderTile):
            for i, j in self.borderTiles:
                num = self.tileInfo[self.rowTotal - 1 - j][i]
                numFlags = self.countFlaggedTiles(self.knownMine, i, j)
                if num >= 0 and numFlags != num:
                    return

            solution = [False for _ in range(len(borderTile))]
            for i in range(len(borderTile)):
                posX, posY = borderTile[i]
                solution[i] = True if self.knownMine[self.rowTotal-1-posY][posX] == -2 else False
            self.trySolutions.append(solution)
            return

        qx, qy = borderTile[k]

        # recurse two possibilities: mine and no mine
        assert(self.knownMine[self.rowTotal-1-qy][qx] == -1)
        self.knownMine[self.rowTotal-1-qy][qx] = -2
        self.tryRecursive(borderTile, k+1)
        self.knownMine[self.rowTotal-1-qy][qx] = -1

        assert(self.knownEmpty[self.rowTotal-1-qy][qx] == -1)
        self.knownEmpty[self.rowTotal-1-qy][qx] = 0
        self.tryRecursive(borderTile, k+1)
        self.knownEmpty[self.rowTotal-1-qy][qx] = -1
    
    def createPolynimialRule(self, col, row):
        assert(self.tileInfo[self.rowTotal-1-row][col] != -1)
        polynomialEquation = PolynomialEqation(self.tileInfo[self.rowTotal-1-row][col], [])

        for i, j in self.dirs:
            nx, ny = col+i, row+j
            if self._isBoardBound(nx, ny):
                if self.tileInfo[self.rowTotal-1-ny][nx] == -2:
                    # add one bomnum
                    polynomialEquation.numOfBomb = polynomialEquation.numOfBomb - 1
                elif self.tileInfo[self.rowTotal-1-ny][nx] == -1:
                    # if covered, add one term
                    term = Term((nx, ny), True)
                    polynomialEquation.terms.append(term)
            else:
                continue
                
        polynomialEquation.terms.sort()
                
        assert(polynomialEquation.numOfBomb > 0)
        assert(len(polynomialEquation.terms) > 0)
        assert(len(polynomialEquation.terms) >= polynomialEquation.numOfBomb)
                
        return polynomialEquation     

    def gaussianElimination(self, poly=None):
        pass

    def trySolverGaussaion(self):
        ruleLists = list()
        
        # Create rules based on the existing uncovered boarder flag
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0 and self.countFlaggedTiles(self.tileInfo, i, j) != self.tileInfo[self.rowTotal-1-j][i]:
                    # This current tile has arounding covered tiles.
                    # We can generate one polynomial based on this information
                    rule = self.createPolynimialRule(i, j)
                    ruleLists.append(rule)
        
                    
        # Sort polynomial rule list
        ruleLists.sort()
        
        # Gaussian elimination
        self.gaussianEliminate(ruleLists)
        # Push unary variables into known mine / non-mine queue

        return
        
    def getAction(self, number: int) -> "Action Object":
        # print("X: ", self.colX, "Y: ", self.rowY)
        self.updateTileInfo(number, self.colX, self.rowY)
        # for ii in range(self.rowTotal):
            # print(self.tileInfo[ii])

        # if all mines are flagged, and there were still uncovered tiles
        if self.flagNum == self.minesTotal and self.uncoveredNum != self.rowTotal * self.colTotal:
            for i in range(self.colTotal):
                for j in range(self.rowTotal):
                    if self.tileInfo[self.rowTotal-1-j][i] == -1:
                        self.colX, self.rowY = i, j
                        self.nextAction = AI.Action.UNCOVER
                        self.uncoveredNum += 1
                        return Action(self.nextAction, self.colX, self.rowY)
        elif self.uncoveredNum != self.rowTotal * self.colTotal:
            # Try Move
            moveSuccess = self.tryMove()
            if moveSuccess:
                self.uncoveredNum += 1
                return Action(self.nextAction, self.colX, self.rowY)

            # Try Flag
            flagSuccess = self.tryFlag()
            if flagSuccess:
                self.flagNum += 1
                self.uncoveredNum += 1
                return Action(self.nextAction, self.colX, self.rowY)


            # print("test")
            if flagSuccess is False and moveSuccess is False and not self.knownMineQueue and not self.knownEmptyQueue:
                # print("trySolver start!!!")
                self.trySolver()
                # print("Known Mine: ", self.knownMineQueue)
                # print("Known Empty: ", self.knownEmptyQueue)

            while self.knownMineQueue:
                self.colX, self.rowY = self.knownMineQueue.pop()
                self.nextAction = AI.Action.FLAG
                self.flagNum += 1
                self.uncoveredNum += 1
                return Action(self.nextAction, self.colX, self.rowY)

            while self.knownEmptyQueue:
                self.colX, self.rowY = self.knownEmptyQueue.pop()
                self.nextAction = AI.Action.UNCOVER
                self.uncoveredNum += 1
                return Action(self.nextAction, self.colX, self.rowY)

            # todo: implement probabilities
            if self.uncoveredNum != self.colTotal*self.rowTotal:
                self.uncertainTile.clear()
                for i in range(self.colTotal):
                    for j in range(self.rowTotal):
                        if self.tileInfo[self.rowTotal-1-j][i] == -1:
                            self.uncertainTile.append((i, j))
                idx = random.randrange(len(self.uncertainTile))
                self.colX, self.rowY = self.uncertainTile[idx]
                self.nextAction = AI.Action.UNCOVER
                self.uncoveredNum += 1
                return Action(self.nextAction, self.colX, self.rowY)

        return Action(AI.Action.LEAVE)

    # while True:
    # need to re-think the break point
    # randomX = random.randrange(self.colTotal)
    # randomY = random.randrange(self.rowTotal)
    # if self.uncoveredNum == self.rowTotal * self.colTotal - 1:
    #     break
    # if self.tileInfo[self.rowTotal-1-randomY][randomX] == -1:
    #     self.uncoveredNum += 1
    #     self.colX, self.rowY = randomX, randomY
    #     return Action(AI.Action.UNCOVER, randomX, randomY)
