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
        self.test = 0
        pass

    def updateTileInfo(self, info: int, x: int, y: int):
        # information of the tile
        # 0-8: # of mines around the tile
        # -1: covered
        # -2: flagged

        if info == -1:
            self.tileInfo[self.rowTotal-1-y][x] = -2  # need to take care of UNFLAG action
        else:
            self.tileInfo[self.rowTotal-1-y][x] = info
        return

    # check if the tile were inside boundary
    def _isInBound(self, x: int, y: int) -> bool:
        if 0 <= x < self.colTotal and 0 <= y < self.rowTotal:
            return True
        return False

    # count how many covered tiles around position(x, y)
    def countCoveredTiles(self, x: int, y: int):
        coveredTiles = 0
        for i, j in self.dirs:
            nx, ny = x+i, y+j
            if self._isInBound(nx, ny) and self.tileInfo[self.rowTotal-1-ny][nx] == -1:
                coveredTiles += 1
            else:
                continue
        return coveredTiles

    # count how many flagged tiles around position(x, y)
    def countFlaggedTiles(self, x: int, y: int):
        flaggedTiles = 0
        for i, j in self.dirs:
            nx, ny = x+i, y+j
            if self._isInBound(nx, ny) and self.tileInfo[self.rowTotal-1-ny][nx] == -2:
                flaggedTiles += 1
            else:
                continue
        return flaggedTiles

    # try to flag all determined mines around tile (rowY, colX)
    def tryFlag(self):
        success = False
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] > 0:
                    curMines = self.tileInfo[self.rowTotal-1-j][i]
                    curCoveredTiles = self.countCoveredTiles(i, j)
                    curFlaggedTiles = self.countFlaggedTiles(i, j)
                    if curMines - curFlaggedTiles == curCoveredTiles:
                        for ni, nj in self.dirs:
                            if self._isInBound(i+ni, j+nj) and self.tileInfo[self.rowTotal-1-j-nj][i+ni] == -1:
                                self.colX, self.rowY = i+ni, j+nj
                                self.nextAction = AI.Action.FLAG
                                success = True
        return success

    # try to uncover all determined empty tiles around tile (rowY, colX)
    def tryMove(self):
        success = False
        for i in range(self.colTotal):
            for j in range(self.rowTotal):
                if self.tileInfo[self.rowTotal-1-j][i] >= 0:
                    self.test = 0
                    curMines = self.tileInfo[self.rowTotal-1-j][i]
                    curCoveredTiles = self.countCoveredTiles(i, j)
                    curFlaggedTiles = self.countFlaggedTiles(i, j)
                    if curMines == curFlaggedTiles and curCoveredTiles > 0:
                        print("position of tryMove: ", i, j)
                        for ni, nj in self.dirs:
                            if self._isInBound(i+ni, j+nj) and self.tileInfo[self.rowTotal-1-j-nj][i+ni] == -1:
                                self.colX, self.rowY = i+ni, j+nj
                                self.nextAction = AI.Action.UNCOVER
                                success = True
        return success

    def getAction(self, number: int) -> "Action Object":
        self.updateTileInfo(number, self.colX, self.rowY)
        for ii in range(self.rowTotal):
            print(self.tileInfo[ii])

        # Try Move
        moveSuccess = self.tryMove()
        if moveSuccess:
            return Action(self.nextAction, self.colX, self.rowY)

        # Try Flag
        flagSuccess = self.tryFlag()
        if flagSuccess:
            return Action(self.nextAction, self.colX, self.rowY)

        return Action(AI.Action.LEAVE)  # return(Action, x, y)
