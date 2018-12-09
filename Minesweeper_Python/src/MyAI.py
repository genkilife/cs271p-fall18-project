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
from copy import copy, deepcopy
import random

class Term():
    def __init__(self, coff=None, var=None):
        self.coefficient = coff
        self.var = var
    def __lt__(self, other):
        return self.var < other.var
    def __str__(self):
        return "( " + str(self.coefficient) + " " + str(self.var) + " )"
    def __copy__(self):
        ret = Term()
        ret.coefficient = self.coefficient.copy()
        ret.var = self.var.copy()
        return ret

class PolynomialEqation():
    def __init__(self, numOfBomb=None, terms=None):
        self.numOfBomb = numOfBomb
        self.terms = terms
    
    def __lt__(self, other):
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
    
    def __copy__(self):
        ret = PolynomialEqation()
        ret.numOfBomb = self.numOfBomb.copy()
        ret.terms = self.terms.copy()
        return ret
    
    def waive(self, other):
        termPivot = other.terms[0]
        assert(abs(termPivot.coefficient) == 1)
        
        ratio = None
        for term in self.terms:
            if term.var == termPivot.var:
                ratio = int(term.coefficient / termPivot.coefficient)
                break
        
        self.numOfBomb = self.numOfBomb - other.numOfBomb * ratio
        
        for term in other.terms:
            idxRet = 0
            while idxRet < len(self.terms):
                if self.terms[idxRet].var == term.var:
                    break
                idxRet = idxRet + 1
            
            if idxRet != len(self.terms):
                self.terms[idxRet].coefficient = self.terms[idxRet].coefficient - term.coefficient * ratio
                if self.terms[idxRet].coefficient == 0:
                    del self.terms[idxRet]
            else:
                newTerm = Term(term.coefficient * -1 * ratio, term.var)
                self.terms.append(newTerm)
                
        self.terms.sort()
        
        return
    
    def __str__(self):
        assert(len(self.terms) > 0)
        ret = str(self.terms[0])
        for term in self.terms[1:]:
            ret = ret + " , " + str(term)
        ret = ret + " = " + str(self.numOfBomb)
        return ret

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

        self.magicNum = 16

        self.trySolutions = []  # all possible solutions for current state
        self.knownMine = [[-1 for _ in range(colDimension)] for _ in range(rowDimension)]
        self.knownMineQueue = []
        self.knownEmptyQueue = []
        self.borderTiles = []
        self.uncertainTile = []
        random.seed(0)
        pass

    def updateTileInfo(self, info: int, x: int, y: int):
        # information of the tile
        # 0-8: # of mines around the tile
        # -1: covered
        # -2: flagged
        if info == -1:
            self.tileInfo[self.rowTotal-1-y][x] = -2  # need to take care of UNFLAG action
            self.knownMine[self.rowTotal - 1 - y][x] = -2
        else:
            self.tileInfo[self.rowTotal-1-y][x] = info
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
        # print("trySolver Start!")
        borderEmptyTiles = []

        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self._isBorder(i, j):
                    borderEmptyTiles.append((i, j))

        # if len(borderEmptyTiles) > 40:
        #     return

        self.borderTiles.clear()
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0 and self.countCoveredTiles(self.tileInfo, i, j) > 0:
                    self.borderTiles.append((i, j))

        segregated = []
        partition = len(borderEmptyTiles)//self.magicNum
        for i in range(partition):
            segregated.append(borderEmptyTiles[i*self.magicNum:(i+1)*self.magicNum])

        # print(segregated)
        # print(self.borderTiles)

        # complex part
        for i in range(len(segregated)):

            self.trySolutions.clear()
            self.tryRecursive(segregated[i], 0)

            # something wrong during tryRecursive
            if len(self.trySolutions) == 0:
                return

            # check for solved tiles
            # for j in range(len(segregated[i])):
            for j in range(4, self.magicNum - 4):
                allMine, allEmpty = True, True
                for sln in self.trySolutions:
                    if sln[j] is False:
                        allMine = False
                    if sln[j]:
                        allEmpty = False
                    if allMine is False and allEmpty is False:
                        break

                qi, qj = segregated[i][j]

                if allMine:
                    self.knownMineQueue.append((qi, qj))
                if allEmpty:
                    self.knownEmptyQueue.append((qi, qj))

        return

    def tryRecursive(self, borderTile, k):
        # possible combination found
        if k == len(borderTile):
            for i, j in self.borderTiles[4:self.magicNum-4]:
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
        if self.solutionCheck(borderTile, qx, qy) is True:
            self.tryRecursive(borderTile, k+1)
        else:
            return
        self.knownMine[self.rowTotal-1-qy][qx] = -1
        self.tryRecursive(borderTile, k+1)

    def solutionCheck(self, borderTile, x, y):
        for ni, nj in self.dirs:
            if (x+ni, y+nj) in borderTile:
                num = self.tileInfo[self.rowTotal - 1 - (y+nj)][x+ni]
                numFlags = self.countFlaggedTiles(self.knownMine, x+ni, y+nj)
                if numFlags > num >= 0:
                    return False
        return True
    
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
                    term = Term(1, (nx, ny))
                    polynomialEquation.terms.append(term)
            else:
                continue
                
        polynomialEquation.terms.sort()
                
        assert(polynomialEquation.numOfBomb > 0)
        assert(len(polynomialEquation.terms) > 0)
        assert(len(polynomialEquation.terms) >= polynomialEquation.numOfBomb)
                
        return polynomialEquation     

    def gaussianEliminate(self, polys=None):
        # check every rules should contain more then one terms
        for idxOuter in range(len(polys)):
            assert(len(polys[idxOuter].terms)>1)
        
        # find items in term
        continueFlag = True
        while continueFlag:
            continueFlag = False
            try:
                idxOuter = 0
                while idxOuter < len(polys):
                    assert(len(polys[idxOuter].terms) > 0)
                    term = polys[idxOuter].terms[0]
                    if abs(term.coefficient) != 1:
                        continue
                        
                    idxInner = idxOuter+1
                    while idxInner < len(polys):
                        if idxInner != idxOuter and term.var in list(map(lambda term: term.var, polys[idxInner].terms)) and len(polys[idxInner].terms) > 1:
                            continueFlag = True
                            polys[idxInner].waive(polys[idxOuter])
                            assert(len(polys[idxInner].terms)>=0)
                            if len(polys[idxInner].terms) == 0:
                                del polys[idxInner]
                                idxInner = idxInner-1
                            else:
                                polys[idxInner].terms.sort()
                        idxInner = idxInner + 1
                    idxOuter = idxOuter + 1
                polys.sort()
            except Exception as e:
                if e is not IndexError:
                    print(e)
            
        return
        
    def pushAvailableTerms(self, polys=None):
        for poly in polys:
            # if it is unary variable
            if len(poly.terms) == 1:
                # if no bomb, push into fine queue
                if poly.numOfBomb == 0:
                    if poly.terms[0].var not in self.knownEmptyQueue:
                        self.knownEmptyQueue.append(poly.terms[0].var)
                else:
                    assert(poly.numOfBomb % poly.terms[0].coefficient == 0)
                    if poly.terms[0].var not in self.knownMineQueue:
                        self.knownMineQueue.append(poly.terms[0].var)
        return

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
        self.pushAvailableTerms(ruleLists)

        return
        
    def getAction(self, number: int) -> "Action Object":
        self.updateTileInfo(number, self.colX, self.rowY)

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

            if flagSuccess is False and moveSuccess is False and not self.knownMineQueue and not self.knownEmptyQueue:
                self.trySolverGaussaion()
                pass
                
            # print("test")
            #if flagSuccess is False and moveSuccess is False and not self.knownMineQueue and not self.knownEmptyQueue:
            #    self.trySolver()
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

