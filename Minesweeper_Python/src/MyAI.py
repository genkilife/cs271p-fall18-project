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
import random

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

        self.trySolutions = []  # all possible solutions for current state
        self.knownMine = [[-5 for _ in range(colDimension)] for _ in range(rowDimension)]
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
        print("trySolver Start!")
        borderEmptyTiles = []

        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self._isBorder(i, j):
                    borderEmptyTiles.append((i, j))

        if len(borderEmptyTiles) > 40:
            return

        self.borderTiles.clear()
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0 and self.countCoveredTiles(self.tileInfo, i, j) > 0:
                    self.borderTiles.append((i, j))

        segregated = []
        segregated.append(borderEmptyTiles)

        # complex part
        totalMultCases = 1
        for i in range(len(segregated)):

            # copy everything into temporary objects
            try_TileInfo = self.tileInfo.copy()

            self.trySolutions.clear()
            self.knownMine = [[-1 for _ in range(self.colTotal)] for _ in range(self.rowTotal)]
            for s in range(self.colTotal):
                for t in range(self.rowTotal):
                    if try_TileInfo[self.rowTotal-1-t][s] == -2:
                        self.knownMine[self.rowTotal-1-t][s] = -2

            self.tryRecursive(segregated[i], 0)

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

            # print("test")
            if flagSuccess is False and moveSuccess is False and not self.knownMineQueue and not self.knownEmptyQueue:
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

