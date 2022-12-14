import pygame
import math
from random import randrange
import random
import copy
import config
import IO
import RPi.GPIO as GPIO
import time

class Game:
    def __init__(self, level, score):
        self.paused = True
        self.ghostUpdateDelay = 1
        self.ghostUpdateCount = 0
        self.pacmanUpdateDelay = 1
        self.pacmanUpdateCount = 0
        self.tictakChangeDelay = 10
        self.tictakChangeCount = 0
        self.ghostsAttacked = False
        self.highScore = self.getHighScore ()
        self.score = score
        self.level = level
        self.lives = 3
        self.ghosts = [Ghost (14.0, 13.5, "red", 0), Ghost (17.0, 11.5, "blue", 1), Ghost (17.0, 13.5, "pink", 2),
                       Ghost (17.0, 15.5, "orange", 3)]
        self.pacman = Pacman (26.0, 13.5)  # Center of Second Last Row
        self.total = self.getCount ()
        self.ghostScore = 200
        self.levels = [[350, 250], [150, 450], [150, 450], [0, 600]]
        random.shuffle (self.levels)
        # Level index and Level Progress
        self.ghostStates = [[1, 0], [0, 0], [1, 0], [0, 0]]
        index = 0
        for state in self.ghostStates:
            state[0] = randrange (2)
            state[1] = randrange (self.levels[index][state[0]] + 1)
            index += 1
        self.collected = 0
        self.started = False
        self.gameOver = False
        self.gameOverCounter = 0
        self.points = []
        self.pointsTimer = 10
        # Berry Spawn Time, Berry Death Time, Berry Eaten
        self.berryState = [200, 400, False]
        self.berryLocation = [20.0, 13.5]
        self.berries = ["tile080.png", "tile081.png", "tile082.png", "tile083.png", "tile084.png", "tile085.png",
                        "tile086.png", "tile087.png"]
        self.berriesCollected = []
        self.levelTimer = 0
        self.berryScore = 100
        self.lockedInTimer = 100
        self.lockedIn = True
        self.extraLifeGiven = False
        self.onLaunchScreen = True
        self.running = True

    # Driver method: The games primary update method
    def update(self):
        # pygame.image.unload()
        if self.gameOver:
            self.gameOverFunc ()
            return
        if self.paused or not self.started:
            self.drawTilesAround (21, 10)
            self.drawTilesAround (21, 11)
            self.drawTilesAround (21, 12)
            self.drawTilesAround (21, 13)
            self.drawTilesAround (21, 14)
            self.drawReady ()
            pygame.display.update ()
            return

        self.levelTimer += 1
        self.ghostUpdateCount += 1
        self.pacmanUpdateCount += 1
        self.tictakChangeCount += 1
        self.ghostsAttacked = False

        if self.score >= 10000 and not self.extraLifeGiven:
            self.lives += 1
            self.extraLifeGiven = True

        # Draw tiles around ghosts and pacman
        self.clearBoard ()
        for ghost in self.ghosts:
            if ghost.attacked:
                self.ghostsAttacked = True

        # Check if the ghost should case pacman
        index = 0
        for state in self.ghostStates:
            state[1] += 1
            if state[1] >= self.levels[index][state[0]]:
                state[1] = 0
                state[0] += 1
                state[0] %= 2
            index += 1

        index = 0
        for ghost in self.ghosts:
            if not ghost.attacked and not ghost.dead and self.ghostStates[index][0] == 0:
                ghost.target = [self.pacman.row, self.pacman.col]
            index += 1

        if self.levelTimer == self.lockedInTimer:
            self.lockedIn = False

        self.checkSurroundings
        if self.ghostUpdateCount == self.ghostUpdateDelay:
            for ghost in self.ghosts:
                ghost.update ()
            self.ghostUpdateCount = 0

        if self.tictakChangeCount == self.tictakChangeDelay:
            # Changes the color of special Tic-Taks
            self.flipColor ()
            self.tictakChangeCount = 0

        if self.pacmanUpdateCount == self.pacmanUpdateDelay:
            self.pacmanUpdateCount = 0
            self.pacman.update ()
            self.pacman.col %= len (config.gameBoard[0])
            if self.pacman.row % 1.0 == 0 and self.pacman.col % 1.0 == 0:
                if config.gameBoard[int (self.pacman.row)][int (self.pacman.col)] == 2:
                    config.gameBoard[int (self.pacman.row)][int (self.pacman.col)] = 1
                    self.score += 10
                    self.collected += 1
                    # Fill tile with black
                    pygame.draw.rect (config.screen, (0, 0, 0),
                                      (int(self.pacman.col * config.square), int(self.pacman.row * config.square), int(config.square), int(config.square)))
                elif config.gameBoard[int (self.pacman.row)][int (self.pacman.col)] == 5 or config.gameBoard[int (self.pacman.row)][
                    int (self.pacman.col)] == 6:
                    config.gameBoard[int (self.pacman.row)][int (self.pacman.col)] = 1
                    self.collected += 1
                    # Fill tile with black
                    pygame.draw.rect (config.screen, (0, 0, 0),
                                      (self.pacman.col * config.square, self.pacman.row * config.square, config.square, config.square))
                    self.score += 50
                    self.ghostScore = 200
                    for ghost in self.ghosts:
                        ghost.attackedCount = 0
                        ghost.setAttacked (True)
                        ghost.setTarget ()
                        self.ghostsAttacked = True
        self.checkSurroundings ()
        self.highScore = max (self.score, self.highScore)

        global running
        if self.collected == self.total:
            print ("New Level")
            self.level += 1
            self.newLevel ()

        if self.level - 1 == 8:  # (self.levels[0][0] + self.levels[0][1]) // 50:
            print ("You win", self.level, len (self.levels))
            running = False
        self.softRender ()

    # Render method
    def render(self):
        config.screen.fill ((0, 0, 0))  # Flushes the config.screen
        # Draws game elements
        currentTile = 0
        self.displayLives ()
        self.displayScore ()
        for i in range (3, len (config.gameBoard) - 2):
            for j in range (len (config.gameBoard[0])):
                if config.gameBoard[i][j] == 3:  # Draw wall
                    imageName = str (currentTile)
                    if len (imageName) == 1:
                        imageName = "00" + imageName
                    elif len (imageName) == 2:
                        imageName = "0" + imageName
                    # Get image of desired tile
                    imageName = "tile" + imageName + ".png"
                    tileImage = pygame.image.load (config.boardPath + imageName).convert()
                    tileImage = pygame.transform.scale (tileImage, (config.square, config.square))

                    # Display image of tile
                    config.screen.blit (tileImage, (j * config.square, i * config.square, config.square, config.square))

                    # pygame.draw.rect(config.screen, (0, 0, 255),(j * config.square, i * config.square, config.square, config.square)) # (x, y, width, height)
                elif config.gameBoard[i][j] == 2:  # Draw Tic-Tak
                    pygame.draw.circle (config.screen, config.pelletColor, (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                        config.square // 4)
                elif config.gameBoard[i][j] == 5:  # Black Special Tic-Tak
                    pygame.draw.circle (config.screen, (0, 0, 0), (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                        config.square // 2)
                elif config.gameBoard[i][j] == 6:  # White Special Tic-Tak
                    pygame.draw.circle (config.screen, config.pelletColor, (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                        config.square // 2)

                currentTile += 1
        # Draw Sprites
        for ghost in self.ghosts:
            ghost.draw ()
        self.pacman.draw ()
        # Updates the config.screen
        pygame.display.update ()

    def softRender(self):
        pointsToDraw = []
        for point in self.points:
            if point[3] < self.pointsTimer:
                pointsToDraw.append ([point[2], point[0], point[1]])
                point[3] += 1
            else:
                self.points.remove (point)
                self.drawTilesAround (point[0], point[1])

        for point in pointsToDraw:
            self.drawPoints (point[0], point[1], point[2])

        # Draw Sprites
        for ghost in self.ghosts:
            ghost.draw ()
        self.pacman.draw ()
        self.displayScore ()
        self.displayBerries ()
        self.displayLives ()
        # for point in pointsToDraw:
        #     self.drawPoints(point[0], point[1], point[2])
        self.drawBerry ()
        # Updates the config.screen
        pygame.display.update ()

    def clearBoard(self):
        # Draw tiles around ghosts and pacman
        for ghost in self.ghosts:
            self.drawTilesAround (ghost.row, ghost.col)
        self.drawTilesAround (self.pacman.row, self.pacman.col)
        self.drawTilesAround (self.berryLocation[0], self.berryLocation[1])
        # Clears Ready! Label
        self.drawTilesAround (20, 10)
        self.drawTilesAround (20, 11)
        self.drawTilesAround (20, 12)
        self.drawTilesAround (20, 13)
        self.drawTilesAround (20, 14)

    def checkSurroundings(self):
        # Check if pacman got killed
        for ghost in self.ghosts:
            if self.touchingPacman (ghost.row, ghost.col) and not ghost.attacked:
                if self.lives == 1:
                    print ("You lose")
                    self.gameOver = True
                    # Removes the ghosts from the config.screen
                    for ghost in self.ghosts:
                        self.drawTilesAround (ghost.row, ghost.col)
                    self.drawTilesAround (self.pacman.row, self.pacman.col)
                    self.pacman.draw ()
                    pygame.display.update ()
                    pause (10000000)
                    return
                self.started = False
                reset ()
            elif self.touchingPacman (ghost.row, ghost.col) and ghost.isAttacked () and not ghost.isDead ():
                ghost.setDead (True)
                ghost.setTarget ()
                ghost.ghostSpeed = 1
                ghost.row = math.floor (ghost.row)
                ghost.col = math.floor (ghost.col)
                self.score += self.ghostScore
                self.points.append ([ghost.row, ghost.col, self.ghostScore, 0])
                self.ghostScore *= 2
                pause (10000000)
        if self.touchingPacman (self.berryLocation[0], self.berryLocation[1]) and not self.berryState[
            2] and self.levelTimer in range (self.berryState[0], self.berryState[1]):
            self.berryState[2] = True
            self.score += self.berryScore
            self.points.append ([self.berryLocation[0], self.berryLocation[1], self.berryScore, 0])
            self.berriesCollected.append (self.berries[(self.level - 1) % 8])

    # Displays the current score
    def displayScore(self):
        textOneUp = ["tile033.png", "tile021.png", "tile016.png"]
        textHighScore = ["tile007.png", "tile008.png", "tile006.png", "tile007.png", "tile015.png", "tile019.png",
                         "tile002.png", "tile014.png", "tile018.png", "tile004.png"]
        index = 0
        scoreStart = 5
        highScoreStart = 11
        for i in range (scoreStart, scoreStart + len (textOneUp)):
            tileImage = pygame.image.load (config.textPath + textOneUp[index]).convert()
            tileImage = pygame.transform.scale (tileImage, (config.square, config.square))
            config.screen.blit (tileImage, (int(i * config.square), int(4), int(config.square), int(config.square)))
            index += 1
        score = str (self.score)
        if score == "0":
            score = "00"
        index = 0
        for i in range (0, len (score)):
            digit = int (score[i])
            tileImage = pygame.image.load (config.textPath + "tile0" + str (32 + digit) + ".png").convert()
            tileImage = pygame.transform.scale (tileImage, (config.square, config.square))
            config.screen.blit (tileImage, (int((scoreStart + 2 + index) * config.square), int(config.square + 4), int(config.square), int(config.square)))
            index += 1

        index = 0
        for i in range (highScoreStart, highScoreStart + len (textHighScore)):
            tileImage = pygame.image.load (config.textPath + textHighScore[index]).convert()
            tileImage = pygame.transform.scale (tileImage, (config.square, config.square))
            config.screen.blit (tileImage, (int(i * config.square),int(4), int(config.square), int(config.square)))
            index += 1

        highScore = str (self.highScore)
        if highScore == "0":
            highScore = "00"
        index = 0
        for i in range (0, len (highScore)):
            digit = int (highScore[i])
            tileImage = pygame.image.load (config.textPath + "tile0" + str (32 + digit) + ".png").convert()
            tileImage = pygame.transform.scale (tileImage, (config.square, config.square))
            config.screen.blit (tileImage, (int((highScoreStart + 6 + index) * config.square), int(config.square + 4), int(config.square), int(config.square)))
            index += 1

    def drawBerry(self):
        if self.levelTimer in range (self.berryState[0], self.berryState[1]) and not self.berryState[2]:
            berryImage = pygame.image.load (config.elementPath + self.berries[(self.level - 1) % 8]).convert()
            berryImage = pygame.transform.scale (berryImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
            config.screen.blit (berryImage, (int(self.berryLocation[1] * config.square), int(self.berryLocation[0] * config.square),int(config.square), int(config.square)))

    def drawPoints(self, points, row, col):
        pointStr = str (points)
        index = 0
        for i in range (len (pointStr)):
            digit = int (pointStr[i])
            tileImage = pygame.image.load (config.textPath + "tile" + str (224 + digit) + ".png").convert()
            tileImage = pygame.transform.scale (tileImage, (config.square // 2, config.square // 2))
            config.screen.blit (tileImage,
                         ((col) * config.square + (config.square // 2 * index), row * config.square - 20, config.square // 2, config.square // 2))
            index += 1

    def drawReady(self):
        ready = ["tile274.png", "tile260.png", "tile256.png", "tile259.png", "tile281.png", "tile283.png"]
        for i in range (len (ready)):
            letter = pygame.image.load (config.textPath + ready[i]).convert()
            letter = pygame.transform.scale (letter, (int (config.square), int (config.square)))
            config.screen.blit (letter, ((11 + i) * config.square, 20 * config.square, config.square, config.square))

    def gameOverFunc(self):
        global running
        if self.gameOverCounter == 12:
            running = False
            self.recordHighScore ()
            return
        # Resets the config.screen around pacman
        self.drawTilesAround (self.pacman.row, self.pacman.col)

        # Draws new image
        pacmanImage = pygame.image.load (config.elementPath + "tile" + str (116 + self.gameOverCounter) + ".png").convert()
        pacmanImage = pygame.transform.scale (pacmanImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
        config.screen.blit (pacmanImage,
                     (int(self.pacman.col * config.square + config.spriteOffset), int(self.pacman.row * config.square + config.spriteOffset), int(config.square), int(config.square)))
        pygame.display.update ()
        pause (5000000)
        self.gameOverCounter += 1;

    def displayLives(self):
        # 33 rows || 28 cols
        # Lives[[31, 5], [31, 3], [31, 1]]
        livesLoc = [[34, 3], [34, 1]]
        for i in range (self.lives - 1):
            lifeImage = pygame.image.load (config.elementPath + "tile054.png").convert()
            lifeImage = pygame.transform.scale (lifeImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
            config.screen.blit (lifeImage, (int(livesLoc[i][1] * config.square), int(livesLoc[i][0] * config.square) - int(config.spriteOffset),
                                     int(config.square), int(config.square)))

    def displayBerries(self):
        firstBerrie = [34, 26]
        for i in range (len (self.berriesCollected)):
            berrieImage = pygame.image.load (config.elementPath + self.berriesCollected[i]).convert()
            berrieImage = pygame.transform.scale (berrieImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
            config.screen.blit (berrieImage,
                         ((firstBerrie[1] - (2 * i)) * config.square, firstBerrie[0] * config.square + 5, config.square, config.square))

    def touchingPacman(self, row, col):
        if row - 0.5 <= self.pacman.row and row >= self.pacman.row and col == self.pacman.col:
            return True
        elif row + 0.5 >= self.pacman.row and row <= self.pacman.row and col == self.pacman.col:
            return True
        elif row == self.pacman.row and col - 0.5 <= self.pacman.col and col >= self.pacman.col:
            return True
        elif row == self.pacman.row and col + 0.5 >= self.pacman.col and col <= self.pacman.col:
            return True
        elif row == self.pacman.row and col == self.pacman.col:
            return True
        return False

    def newLevel(self):
        reset ()
        self.lives += 1
        self.collected = 0
        self.started = False
        self.berryState = [200, 400, False]
        self.levelTimer = 0
        self.lockedIn = True
        for level in self.levels:
            level[0] = min ((level[0] + level[1]) - 100, level[0] + 50)
            level[1] = max (100, level[1] - 50)
        random.shuffle (self.levels)
        index = 0
        for state in self.ghostStates:
            state[0] = randrange (2)
            state[1] = randrange (self.levels[index][state[0]] + 1)
            index += 1
        self.render ()

    def drawTilesAround(self, row, col):
        row = math.floor (row)
        col = math.floor (col)
        for i in range (row - 2, row + 3):
            for j in range (col - 2, col + 3):
                if i >= 3 and i < len (config.gameBoard) - 2 and j >= 0 and j < len (config.gameBoard[0]):
                    imageName = str (((i - 3) * len (config.gameBoard[0])) + j)
                    if len (imageName) == 1:
                        imageName = "00" + imageName
                    elif len (imageName) == 2:
                        imageName = "0" + imageName
                    # Get image of desired tile
                    imageName = "tile" + imageName + ".png"
                    tileImage = pygame.image.load (config.boardPath + imageName).convert()
                    tileImage = pygame.transform.scale (tileImage, (config.square, config.square))
                    # Display image of tile
                    config.screen.blit (tileImage, (j * config.square, i * config.square, config.square, config.square))

                    if config.gameBoard[i][j] == 2:  # Draw Tic-Tak
                        pygame.draw.circle (config.screen, config.pelletColor, (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                            config.square // 4)
                    elif config.gameBoard[i][j] == 5:  # Black Special Tic-Tak
                        pygame.draw.circle (config.screen, (0, 0, 0), (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                            config.square // 2)
                    elif config.gameBoard[i][j] == 6:  # White Special Tic-Tak
                        pygame.draw.circle (config.screen, config.pelletColor, (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                            config.square // 2)

    # Flips Color of Special Tic-Taks
    def flipColor(self):
        for i in range (3, len (config.gameBoard) - 2):
            for j in range (len (config.gameBoard[0])):
                if config.gameBoard[i][j] == 5:
                    config.gameBoard[i][j] = 6
                    pygame.draw.circle (config.screen, config.pelletColor, (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                        config.square // 2)
                elif config.gameBoard[i][j] == 6:
                    config.gameBoard[i][j] = 5
                    pygame.draw.circle (config.screen, (0, 0, 0), (j * config.square + config.square // 2, i * config.square + config.square // 2),
                                        config.square // 2)

    def getCount(self):
        total = 0
        for i in range (3, len (config.gameBoard) - 2):
            for j in range (len (config.gameBoard[0])):
                if config.gameBoard[i][j] == 2 or config.gameBoard[i][j] == 5 or config.gameBoard[i][j] == 6:
                    total += 1
        return total

    def getHighScore(self):
        file = open (config.dataPath + "HighScore.txt", "r")
        highScore = int (file.read ())
        file.close ()
        return highScore

    def recordHighScore(self):
        file = open (config.dataPath + "HighScore.txt", "w").close ()
        file = open (config.dataPath + "HighScore.txt", "w+")
        file.write (str (self.highScore))
        file.close ()


class Pacman:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.mouthOpen = False
        self.pacSpeed = 1 / 4
        self.mouthChangeDelay = 5
        self.mouthChangeCount = 0
        self.dir = 0  # 0: North, 1: East, 2: South, 3: West
        self.newDir = 0

    def update(self):
        if self.newDir == 0:
            if canMove (math.floor (self.row - self.pacSpeed), self.col) and self.col % 1.0 == 0:
                self.row -= self.pacSpeed
                self.dir = self.newDir
                return
        elif self.newDir == 1:
            if canMove (self.row, math.ceil (self.col + self.pacSpeed)) and self.row % 1.0 == 0:
                self.col += self.pacSpeed
                self.dir = self.newDir
                return
        elif self.newDir == 2:
            if canMove (math.ceil (self.row + self.pacSpeed), self.col) and self.col % 1.0 == 0:
                self.row += self.pacSpeed
                self.dir = self.newDir
                return
        elif self.newDir == 3:
            if canMove (self.row, math.floor (self.col - self.pacSpeed)) and self.row % 1.0 == 0:
                self.col -= self.pacSpeed
                self.dir = self.newDir
                return

        if self.dir == 0:
            if canMove (math.floor (self.row - self.pacSpeed), self.col) and self.col % 1.0 == 0:
                self.row -= self.pacSpeed
        elif self.dir == 1:
            if canMove (self.row, math.ceil (self.col + self.pacSpeed)) and self.row % 1.0 == 0:
                self.col += self.pacSpeed
        elif self.dir == 2:
            if canMove (math.ceil (self.row + self.pacSpeed), self.col) and self.col % 1.0 == 0:
                self.row += self.pacSpeed
        elif self.dir == 3:
            if canMove (self.row, math.floor (self.col - self.pacSpeed)) and self.row % 1.0 == 0:
                self.col -= self.pacSpeed

    # Draws pacman based on his current state
    def draw(self):
        if not game.started:
            pacmanImage = pygame.image.load (config.elementPath + "tile112.png").convert()
            pacmanImage = pygame.transform.scale (pacmanImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
            config.screen.blit (pacmanImage,
                         (int(self.col * config.square + config.spriteOffset), int(self.row * config.square + config.spriteOffset), int(config.square), int(config.square)))
            return

        if self.mouthChangeCount == self.mouthChangeDelay:
            self.mouthChangeCount = 0
            self.mouthOpen = not self.mouthOpen
        self.mouthChangeCount += 1
        # pacmanImage = pygame.image.load("Sprites/tile049.png")
        if self.dir == 0:
            if self.mouthOpen:
                pacmanImage = pygame.image.load (config.elementPath + "tile049.png").convert()
            else:
                pacmanImage = pygame.image.load (config.elementPath + "tile051.png").convert()
        elif self.dir == 1:
            if self.mouthOpen:
                pacmanImage = pygame.image.load (config.elementPath + "tile052.png").convert()
            else:
                pacmanImage = pygame.image.load (config.elementPath + "tile054.png").convert()
        elif self.dir == 2:
            if self.mouthOpen:
                pacmanImage = pygame.image.load (config.elementPath + "tile053.png").convert()
            else:
                pacmanImage = pygame.image.load (config.elementPath + "tile055.png").convert()
        elif self.dir == 3:
            if self.mouthOpen:
                pacmanImage = pygame.image.load (config.elementPath + "tile048.png").convert()
            else:
                pacmanImage = pygame.image.load (config.elementPath + "tile050.png").convert()

        pacmanImage = pygame.transform.scale (pacmanImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
        config.screen.blit (pacmanImage, (int(self.col * config.square + config.spriteOffset), int(self.row * config.square + config.spriteOffset), int(config.square), int(config.square)))


class Ghost:
    def __init__(self, row, col, color, changeFeetCount):
        self.row = row
        self.col = col
        self.attacked = False
        self.color = color
        self.dir = randrange (4)
        self.dead = False
        self.changeFeetCount = changeFeetCount
        self.changeFeetDelay = 5
        self.target = [-1, -1]
        self.ghostSpeed = 1 / 4
        self.lastLoc = [-1, -1]
        self.attackedTimer = 240
        self.attackedCount = 0
        self.deathTimer = 120
        self.deathCount = 0

    def update(self):
        # print(self.row, self.col)
        if self.target == [-1, -1] or (self.row == self.target[0] and self.col == self.target[1]) or \
                config.gameBoard[int (self.row)][int (self.col)] == 4 or self.dead:
            self.setTarget ()
        self.setDir ()
        self.move ()

        if self.attacked:
            self.attackedCount += 1

        if self.attacked and not self.dead:
            self.ghostSpeed = 1 / 8

        if self.attackedCount == self.attackedTimer and self.attacked:
            if not self.dead:
                self.ghostSpeed = 1 / 4
                self.row = math.floor (self.row)
                self.col = math.floor (self.col)

            self.attackedCount = 0
            self.attacked = False
            self.setTarget ()

        if self.dead and config.gameBoard[self.row][self.col] == 4:
            self.deathCount += 1
            self.attacked = False
            if self.deathCount == self.deathTimer:
                self.deathCount = 0
                self.dead = False
                self.ghostSpeed = 1 / 4

    def draw(self):  # Ghosts states: Alive, Attacked, Dead Attributes: Color, Direction, Location
        ghostImage = pygame.image.load (config.elementPath + "tile152.png").convert()
        currentDir = ((self.dir + 3) % 4) * 2
        if self.changeFeetCount == self.changeFeetDelay:
            self.changeFeetCount = 0
            currentDir += 1
        self.changeFeetCount += 1
        if self.dead:
            tileNum = 152 + currentDir
            ghostImage = pygame.image.load (config.elementPath + "tile" + str (tileNum) + ".png").convert()
        elif self.attacked:
            if self.attackedTimer - self.attackedCount < self.attackedTimer // 3:
                if (self.attackedTimer - self.attackedCount) % 31 < 26:
                    ghostImage = pygame.image.load (
                        config.elementPath + "tile0" + str (70 + (currentDir - (((self.dir + 3) % 4) * 2))) + ".png").convert()
                else:
                    ghostImage = pygame.image.load (
                        config.elementPath + "tile0" + str (72 + (currentDir - (((self.dir + 3) % 4) * 2))) + ".png").convert()
            else:
                ghostImage = pygame.image.load (
                    config.elementPath + "tile0" + str (72 + (currentDir - (((self.dir + 3) % 4) * 2))) + ".png").convert()
        else:
            if self.color == "blue":
                tileNum = 136 + currentDir
                ghostImage = pygame.image.load (config.elementPath + "tile" + str (tileNum) + ".png").convert()
            elif self.color == "pink":
                tileNum = 128 + currentDir
                ghostImage = pygame.image.load (config.elementPath + "tile" + str (tileNum) + ".png").convert()
            elif self.color == "orange":
                tileNum = 144 + currentDir
                ghostImage = pygame.image.load (config.elementPath + "tile" + str (tileNum) + ".png").convert()
            elif self.color == "red":
                tileNum = 96 + currentDir
                if tileNum < 100:
                    ghostImage = pygame.image.load (config.elementPath + "tile0" + str (tileNum) + ".png").convert()
                else:
                    ghostImage = pygame.image.load (config.elementPath + "tile" + str (tileNum) + ".png").convert()

        ghostImage = pygame.transform.scale (ghostImage, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
        config.screen.blit (ghostImage, (int(self.col * config.square + config.spriteOffset), int(self.row * config.square + config.spriteOffset), int(config.square), int(config.square)))

    def isValidTwo(self, cRow, cCol, dist, visited):
        if cRow < 3 or cRow >= len (config.gameBoard) - 5 or cCol < 0 or cCol >= len (config.gameBoard[0]) or config.gameBoard[cRow][
            cCol] == 3:
            return False
        elif visited[cRow][cCol] <= dist:
            return False
        return True

    def isValid(self, cRow, cCol):
        if cCol < 0 or cCol > len (config.gameBoard[0]) - 1:
            return True
        for ghost in game.ghosts:
            if ghost.color == self.color:
                continue
            if ghost.row == cRow and ghost.col == cCol and not self.dead:
                return False
        if not ghostGate.count ([cRow, cCol]) == 0:
            if self.dead and self.row < cRow:
                return True
            elif self.row > cRow and not self.dead and not self.attacked and not game.lockedIn:
                return True
            else:
                return False
        if config.gameBoard[cRow][cCol] == 3:
            return False
        return True

    def setDir(self):  # Very inefficient || can easily refactor
        # BFS search -> Not best route but a route none the less
        dirs = [[0, -self.ghostSpeed, 0],
                [1, 0, self.ghostSpeed],
                [2, self.ghostSpeed, 0],
                [3, 0, -self.ghostSpeed]
                ]
        random.shuffle (dirs)
        best = 10000
        bestDir = -1
        for newDir in dirs:
            if self.calcDistance (self.target, [self.row + newDir[1], self.col + newDir[2]]) < best:
                if not (self.lastLoc[0] == self.row + newDir[1] and self.lastLoc[1] == self.col + newDir[2]):
                    if newDir[0] == 0 and self.col % 1.0 == 0:
                        if self.isValid (math.floor (self.row + newDir[1]), int (self.col + newDir[2])):
                            bestDir = newDir[0]
                            best = self.calcDistance (self.target, [self.row + newDir[1], self.col + newDir[2]])
                    elif newDir[0] == 1 and self.row % 1.0 == 0:
                        if self.isValid (int (self.row + newDir[1]), math.ceil (self.col + newDir[2])):
                            bestDir = newDir[0]
                            best = self.calcDistance (self.target, [self.row + newDir[1], self.col + newDir[2]])
                    elif newDir[0] == 2 and self.col % 1.0 == 0:
                        if self.isValid (math.ceil (self.row + newDir[1]), int (self.col + newDir[2])):
                            bestDir = newDir[0]
                            best = self.calcDistance (self.target, [self.row + newDir[1], self.col + newDir[2]])
                    elif newDir[0] == 3 and self.row % 1.0 == 0:
                        if self.isValid (int (self.row + newDir[1]), math.floor (self.col + newDir[2])):
                            bestDir = newDir[0]
                            best = self.calcDistance (self.target, [self.row + newDir[1], self.col + newDir[2]])
        self.dir = bestDir

    def calcDistance(self, a, b):
        dR = a[0] - b[0]
        dC = a[1] - b[1]
        return math.sqrt ((dR * dR) + (dC * dC))

    def setTarget(self):
        if config.gameBoard[int (self.row)][int (self.col)] == 4 and not self.dead:
            self.target = [ghostGate[0][0] - 1, ghostGate[0][1] + 1]
            return
        elif config.gameBoard[int (self.row)][int (self.col)] == 4 and self.dead:
            self.target = [self.row, self.col]
        elif self.dead:
            self.target = [14, 13]
            return

        # Records the quadrants of each ghost's target
        quads = [0, 0, 0, 0]
        for ghost in game.ghosts:
            # if ghost.target[0] == self.row and ghost.col == self.col:
            #     continue
            if ghost.target[0] <= 15 and ghost.target[1] >= 13:
                quads[0] += 1
            elif ghost.target[0] <= 15 and ghost.target[1] < 13:
                quads[1] += 1
            elif ghost.target[0] > 15 and ghost.target[1] < 13:
                quads[2] += 1
            elif ghost.target[0] > 15 and ghost.target[1] >= 13:
                quads[3] += 1

        # Finds a target that will keep the ghosts dispersed
        while True:
            self.target = [randrange (31), randrange (28)]
            quad = 0
            if self.target[0] <= 15 and self.target[1] >= 13:
                quad = 0
            elif self.target[0] <= 15 and self.target[1] < 13:
                quad = 1
            elif self.target[0] > 15 and self.target[1] < 13:
                quad = 2
            elif self.target[0] > 15 and self.target[1] >= 13:
                quad = 3
            if not config.gameBoard[self.target[0]][self.target[1]] == 3 and not config.gameBoard[self.target[0]][
                                                                              self.target[1]] == 4:
                break
            elif quads[quad] == 0:
                break

    def move(self):
        # print(self.target)
        self.lastLoc = [self.row, self.col]
        if self.dir == 0:
            self.row -= self.ghostSpeed
        elif self.dir == 1:
            self.col += self.ghostSpeed
        elif self.dir == 2:
            self.row += self.ghostSpeed
        elif self.dir == 3:
            self.col -= self.ghostSpeed

        # Incase they go through the middle tunnel
        self.col = self.col % len (config.gameBoard[0])
        if self.col < 0:
            self.col = len (config.gameBoard[0]) - 0.5

    def setAttacked(self, isAttacked):
        self.attacked = isAttacked

    def isAttacked(self):
        return self.attacked

    def setDead(self, isDead):
        self.dead = isDead

    def isDead(self):
        return self.dead

def canMove(row, col):
    if col == -1 or col == len (config.gameBoard[0]):
        return True
    if config.gameBoard[int (row)][int (col)] != 3:
        return True
    return False


# Reset after death
def reset():
    global game
    game.ghosts = [Ghost (14.0, 13.5, "red", 0), Ghost (17.0, 11.5, "blue", 1), Ghost (17.0, 13.5, "pink", 2),
                   Ghost (17.0, 15.5, "orange", 3)]
    for ghost in game.ghosts:
        ghost.setTarget ()
    game.pacman = Pacman (26.0, 13.5)
    game.lives -= 1
    game.paused = True
    game.render ()


def displayLaunchScreen():
    # Draw Pacman Title
    pacmanTitle = ["tile016.png", "tile000.png", "tile448.png", "tile012.png", "tile000.png", "tile013.png"]
    for i in range (len (pacmanTitle)):
        letter = pygame.image.load (config.textPath + pacmanTitle[i]).convert()
        letter = pygame.transform.scale (letter, (int (config.square * 4), int (config.square * 4)))
        config.screen.blit (letter, ((2 + 4 * i) * config.square, 2 * config.square, config.square, config.square))

    # Draw Character / Nickname
    characterTitle = [
        # Character
        "tile002.png", "tile007.png", "tile000.png", "tile018.png", "tile000.png", "tile002.png", "tile020.png",
        "tile004.png", "tile018.png",
        # /
        "tile015.png", "tile042.png", "tile015.png",
        # Nickname
        "tile013.png", "tile008.png", "tile002.png", "tile010.png", "tile013.png", "tile000.png", "tile012.png",
        "tile004.png"
    ]
    for i in range (len (characterTitle)):
        letter = pygame.image.load (config.textPath + characterTitle[i]).convert()
        letter = pygame.transform.scale (letter, (int (config.square), int (config.square)))
        config.screen.blit (letter, ((4 + i) * config.square, 10 * config.square, config.square, config.square))

    # Draw Characters and their Nickname
    characters = [
        # Red Ghost
        [
            "tile449.png", "tile015.png", "tile107.png", "tile015.png", "tile083.png", "tile071.png", "tile064.png",
            "tile067.png", "tile078.png", "tile087.png",
            "tile015.png", "tile015.png", "tile015.png", "tile015.png",
            "tile108.png", "tile065.png", "tile075.png", "tile072.png", "tile077.png", "tile074.png", "tile089.png",
            "tile108.png"
        ],
        # Pink Ghost
        [
            "tile450.png", "tile015.png", "tile363.png", "tile015.png", "tile339.png", "tile336.png", "tile324.png",
            "tile324.png", "tile323.png", "tile345.png",
            "tile015.png", "tile015.png", "tile015.png", "tile015.png",
            "tile364.png", "tile336.png", "tile328.png", "tile333.png", "tile330.png", "tile345.png", "tile364.png"
        ],
        # Blue Ghost
        [
            "tile452.png", "tile015.png", "tile363.png", "tile015.png", "tile193.png", "tile192.png", "tile211.png",
            "tile199.png", "tile197.png", "tile213.png", "tile203.png",
            "tile015.png", "tile015.png", "tile015.png",
            "tile236.png", "tile200.png", "tile205.png", "tile202.png", "tile217.png", "tile236.png"
        ],
        # Orange Ghost
        [
            "tile451.png", "tile015.png", "tile363.png", "tile015.png", "tile272.png", "tile270.png", "tile266.png",
            "tile260.png", "tile281.png",
            "tile015.png", "tile015.png", "tile015.png", "tile015.png", "tile015.png",
            "tile300.png", "tile258.png", "tile267.png", "tile281.png", "tile259.png", "tile260.png", "tile300.png"
        ]
    ]
    for i in range (len (characters)):
        for j in range (len (characters[i])):
            if j == 0:
                letter = pygame.image.load (config.textPath + characters[i][j]).convert()
                letter = pygame.transform.scale (letter, (int (config.square * config.spriteRatio), int (config.square * config.spriteRatio)))
                config.screen.blit (letter,
                             ((2 + j) * config.square - config.square // 2, (12 + 2 * i) * config.square - config.square // 3, config.square, config.square))
            else:
                letter = pygame.image.load (config.textPath + characters[i][j]).convert()
                letter = pygame.transform.scale (letter, (int (config.square), int (config.square)))
                config.screen.blit (letter, ((2 + j) * config.square, (12 + 2 * i) * config.square, config.square, config.square))
    # Draw Pacman and Ghosts
    event = ["tile449.png", "tile015.png", "tile452.png", "tile015.png", "tile015.png", "tile448.png", "tile453.png",
             "tile015.png", "tile015.png", "tile015.png", "tile453.png"]
    for i in range (len (event)):
        character = pygame.image.load (config.textPath + event[i]).convert()
        character = pygame.transform.scale (character, (int (config.square * 2), int (config.square * 2)))
        config.screen.blit (character, ((4 + i * 2) * config.square, 24 * config.square, config.square, config.square))
    # Draw PlatForm from Pacman and Ghosts
    wall = ["tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png",
            "tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png", "tile454.png",
            "tile454.png"]
    for i in range (len (wall)):
        platform = pygame.image.load (config.textPath + wall[i]).convert()
        platform = pygame.transform.scale (platform, (int (config.square * 2), int (config.square * 2)))
        config.screen.blit (platform, ((i * 2) * config.square, 26 * config.square, config.square, config.square))
    # Credit myself and zack
    credit = ["tile001.png", "tile025.png", "tile015.png",  "tile007.png", "tile000.png", "tile013.png", "tile013.png",
              "tile000.png", "tile007.png", "tile015.png", "tile000.png", "tile013.png", "tile003.png", "tile015.png",
              "tile026.png", "tile000.png", "tile002.png", "tile010.png", "tile015.png", "tile418.png", "tile416.png",
              "tile418.png", "tile418.png"]
    for i in range (len (credit)):
        letter = pygame.image.load (config.textPath + credit[i]).convert()
        letter = pygame.transform.scale (letter, (int (config.square), int (config.square)))
        config.screen.blit (letter, ((2 + i) * config.square, 30 * config.square, config.square, config.square))
    # Press Green to Play
    instructions = ["tile016.png", "tile018.png", "tile004.png", "tile019.png", "tile019.png", "tile015.png",
                    "tile006.png", "tile018.png", "tile004.png", "tile004.png", "tile013.png", "tile015.png",
                    "tile020.png", "tile014.png", "tile015.png", "tile016.png", "tile011.png", "tile000.png",
                    "tile025.png"]
    for i in range (len (instructions)):
        letter = pygame.image.load (config.textPath + instructions[i]).convert()
        letter = pygame.transform.scale (letter, (int (config.square), int (config.square)))
        config.screen.blit(letter, (int((4.5 + i) * config.square), int(35 * config.square - 10), int(config.square), int(config.square)))

    pygame.display.update ()


def pause(time):
    cur = 0
    while not cur == time:
        cur += 1

def greenPressed(channel):
    if GPIO.input(5):
        GPIO.output (11, GPIO.HIGH)
        if game.onLaunchScreen:
            game.onLaunchScreen = False
            game.paused = True
            game.started = False
            game.render()
            game.paused = False
            game.started = True
    else:
        GPIO.output(11, GPIO.LOW)

def upPressed(channel):
    if GPIO.input (21):
        GPIO.output (20, GPIO.HIGH)
        if not game.onLaunchScreen:
            game.pacman.newDir = 0
            game.paused = False
            game.started = True
    else:
        GPIO.output (20, GPIO.LOW)

def downPressed(channel):
    if GPIO.input (26):
        GPIO.output (19, GPIO.HIGH)
        if not game.onLaunchScreen:
            game.pacman.newDir = 2
            game.paused = False
            game.started = True
    else:
        GPIO.output (19, GPIO.LOW)

def rightPressed(channel):
    if GPIO.input (16):
        GPIO.output (13, GPIO.HIGH)
        if not game.onLaunchScreen:
            game.pacman.newDir = 1
            game.paused = False
            game.started = True
    else:
        GPIO.output (13, GPIO.LOW)

def leftPressed(channel):
    if GPIO.input (6):
        GPIO.output (12, GPIO.HIGH)
        if not game.onLaunchScreen:
            game.pacman.newDir = 3
            game.paused = False
            game.started = True
    else:
        GPIO.output (12, GPIO.LOW)

def redPressed(channel):
    if GPIO.input (9):
        GPIO.output (25, GPIO.HIGH)
        game.running = False
        game.recordHighScore()
    else:
        GPIO.output(25, GPIO.LOW)

game = Game (1, 0)
ghostGate = [[15, 13], [15, 14]]
pygame.event.set_allowed([pygame.QUIT])
pygame.init ()
IO.intialization ()
pygame.display.flip ()
GPIO.add_event_detect(5, GPIO.BOTH, callback=greenPressed, bouncetime=50)
GPIO.add_event_detect(21, GPIO.BOTH, callback=upPressed, bouncetime=50)
GPIO.add_event_detect(26, GPIO.BOTH, callback=downPressed, bouncetime=50)
GPIO.add_event_detect(16, GPIO.BOTH, callback=rightPressed, bouncetime=50)
GPIO.add_event_detect(6, GPIO.BOTH, callback=leftPressed, bouncetime=50)
GPIO.add_event_detect(9, GPIO.BOTH, callback=redPressed, bouncetime=50)

while 1:
    for event in pygame.event.get ():
        if event.type == pygame.QUIT:
            game.recordHighScore ()
            exit ()
    game.__init__ (1, 0)
    config.screen.fill ((0, 0, 0))
    pygame.display.update ()
    displayLaunchScreen ()
    string = "BEAT THE HIGH SCORE " + str (game.getHighScore ())
    string_padded = config.padding + string + config.padding
    count_string_max = len (string_padded) - config.cols + 1
    count = 0
    count_string = 0
    while game.running:
        if count_string == count_string_max:
            count_string=0
        config.lcd.home()
        string_display = string_padded[count_string:count_string + config.cols]
        config.lcd.cursor_pos = (1, 0)
        config.lcd.write_string (string_display)
        time.sleep (0.2)
        count_string+=1
        for event in pygame.event.get ():
            if event.type == pygame.QUIT:
                game.recordHighScore ()
                exit ()
        if game.onLaunchScreen:
            count = IO.buttonWaitingPattern (count)
        else:
            game.update ()
