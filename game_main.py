# this file gets Kinect data and translates it into actions onscreen
# also includes several gameplay functions that determine rules, whether the ball is out, etc.
# was not broken up into more files as these functions used several game attributes defined in __init__()

from pykinect2 import PyKinectV2, PyKinectRuntime
from pykinect2.PyKinectV2 import *
from visuals import *  # import all classes defined in visuals.py
from screens import *  # import different gameplay screens from separate file

import ctypes
import _ctypes
import pygame
import sys
import math
import random


class GamePlayMode(object):  #some of this template used from Fletcher's notes

    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Virtual Soccer')
        self.width = 1000
        self.height = 650
        self.margin = 30
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.play = True

        # Used to manage how fast the screen updates
        self.clock = pygame.time.Clock()
        self.keydown = False

        self.kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)  # from fletcher's notes
        
        self.frameSurface = pygame.Surface((self.kinect.color_frame_desc.Width, self.kinect.color_frame_desc.Height), 0, 32)  # fletcher's notes

        # here we will store skeleton data
        self.bodies = None

        self.prevRightLegDist = 0
        self.prevLeftLegDist = 0
        self.prevRightHandDist = 0
        self.prevLeftHandDist = 0
        self.origPassPos = (0,0)
        self.prevLHX = 0  # for the swipe
        self.passRight = None
        self.oneswipe = None

        self.gameover = False
        self.goalScored = False
        self.halftime = False
        self.startGame = True  # each of the different screens
        self.help = False
        self.offScreen = None

        self.timeOfGame = 300  # length of game in seconds
        self.timeSubtract = 0
        self.halfTime = self.timeOfGame/2

        self.outOfBoundsThrow = False
        self.outOfBoundsGoalkick = False

        self.ballX = 0
        self.ballHeight = 0
        self.kickPower = 0
        self.throwPower = 0
        self.movingForward = None
        self.leftPass = 0 #just one leg for now
        self.throwIn = 0 #both hands

        self.ball = SoccerBall((self.width//2 - 15, self.height//2 - 15))
        
        # variables used to display on pygame screen
        self.numplayers = 5
        self.players = []
        for i in range(self.numplayers):
            px, py = self.width//(5), self.height - 70*(i+3)
            self.players.append(Player((px, py)))
        self.rightSidePlayers = []
        for i in range(self.numplayers):
            px, py = 3.7*self.width//(5), self.height - 70*(i+3)
            self.rightSidePlayers.append(Player((px, py),False))
        # list of players on opposing team
        self.playerSelected = 2  # may want separate player selected to store actual player instance?
        self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
        self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
        # gets player position and draws plumbob above it
        self.rightPlayerSelected = 2
        self.plum_2x = self.rightSidePlayers[self.rightPlayerSelected].posOnField[0] - 15
        self.plum_2y = self.rightSidePlayers[self.rightPlayerSelected].posOnField[1] - 24
        # gets right side player position and draws plumbob above it
        self.leftGoal = Goal((self.margin, self.height//2 - 45), True)
        self.rightGoal = Goal((self.width - self.margin - 90, self.height//2 - 45))
        # add goals
        self.cornerX = (self.margin, self.width-self.margin)
        self.cornerY = (self.margin, self.height-self.margin)
        self.cornerFlags = []
        for i in range(4):
            x, y = self.cornerX[i%2] - 6, self.cornerY[i//2] - 38
            self.cornerFlags.append(CornerFlag((x,y)))
        # make corner flags
        self.linesmen = [Referee((0,0), False), Referee((self.width - self.margin, self.height - self.margin), False)]
        self.mainRef = Referee((self.width//2, self.height//2 - 100))
        

    def drawColorFrame(self, frame, targetSurface):
        targetSurface.lock()
        address = self.kinect.surface_as_array(targetSurface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        targetSurface.unlock()  # from fletcher's notes
    
    def backgroundSound(self):  # idea from classmate: sydney shirriff
    # sound source: world cup 2014 https://www.youtube.com/watch?v=csh6WBUZMQk
        noise = pygame.mixer.Sound("images/stadiumsound.ogg")
        noise.play(-1)  # plays on repeat
    
    def keyPressed(self, keycode, modifier):  # not using modifier rn
        origPos = self.rightSidePlayers[self.playerSelected].posOnField
        if self.goalScored or self.halftime or self.startGame:
            #only recognize r and enter
            if keycode != pygame.K_RETURN and keycode != pygame.K_r:
                return
        elif self.gameover:
            if keycode != pygame.K_r:
                return
        if keycode == pygame.K_RETURN:
            self.gameover = False
            self.goalScored = False
            self.halftime = False
            self.startGame = False
            self.help = False
            # set to game playing state (use return key to exit from other screens)
        elif keycode == pygame.K_UP:  # up
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,-7]
        elif keycode == pygame.K_DOWN:  # down
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,7]
        elif keycode == pygame.K_LEFT:  # left
            self.rightSidePlayers[self.rightPlayerSelected].direction = [-7,0]
        elif keycode == pygame.K_RIGHT:  # right
            self.rightSidePlayers[self.rightPlayerSelected].direction = [7,0]
        elif keycode == pygame.K_r:
            self.__init__()
        elif keycode == pygame.K_h:
            self.help = True
        elif keycode == pygame.K_PERIOD:
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,0]
        elif keycode == pygame.K_COMMA:
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,0]
            if self.rightPlayerSelected < self.numplayers - 1:
                self.rightPlayerSelected += 1
            else:
                self.rightPlayerSelected = 0
        self.plum_2x = self.rightSidePlayers[self.rightPlayerSelected].posOnField[0] + 25
        self.plum_2y = self.rightSidePlayers[self.rightPlayerSelected].posOnField[1] - 24
        # update positions of ball and player
        self.ball.rect.topleft = self.ball.posOnField
        for p in self.rightSidePlayers:
            p.rect.topleft = p.posOnField
        self.checkGoal()
        self.checkBounceOffPlayers()
    
    def rightValidActions(self, keycode, modifier):
        if keycode == pygame.K_SPACE:  # shoot ball - when press down, power up to 100 or somethin
            self.ball.posOnField = (self.ball.posOnField[0] - 50, self.ball.posOnField[1])
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,0]
        #elif keys for throw in and goalkick
        elif keycode == pygame.K_RSHIFT:  # pass to teammate
            self.rightSidePlayers[self.rightPlayerSelected].direction = [0,0]
            newCo = self.findNearestTeammate(2)
            self.ball.posOnField = newCo
        self.ball.rect.topleft = self.ball.posOnField

    def selectNearest(self):  # select nearest player to the ball
        nearest = self.playerSelected
        for i in range(len(self.players)):
            if self.players[i].dist(self.ball.rect.topleft) < \
             self.players[nearest].dist(self.ball.rect.topleft):
                nearest = i
        self.playerSelected = nearest
        self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
        self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
        #return nearest  # returns index of closest player

    def findNearestTeammate(self, team):  # input which team has the ball
        nearestDist = 40000
        if team == 1:
            tlist = self.players
            selected = self.players[self.playerSelected]
        else:
            tlist = self.rightSidePlayers
            selected = self.rightSidePlayers[self.rightPlayerSelected]
        for i in tlist:
            if i != selected and selected.dist(i.rect.topleft) < nearestDist:
                nearest = i
                nearestDist = selected.dist(i.rect.topleft)
        if team == 1:   self.playerSelected = self.players.index(nearest)
        else:   self.rightPlayerSelected = self.rightSidePlayers.index(nearest)
        return nearest.rect.topleft  # returns position of nearest teammate

    def moveToBall(self):  # select and move nearest player to the ball
        self.selectNearest()
        kicker = self.players[self.playerSelected].rect.topleft
        ballrect = self.ball.rect.topleft
        if not self.isValidBall(1):
            self.players[self.playerSelected].posOnField = (ballrect[0], ballrect[1])
        self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
        self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
        self.players[self.playerSelected].direction = [0,0]
        self.players[self.playerSelected].rect.topleft = self.players[self.playerSelected].posOnField
        self.ball.rect.topleft = self.ball.posOnField

    def checkGoal(self):
        if pygame.sprite.collide_rect(self.rightGoal, self.ball):
            # enters statement only if there is a collision between rects (bounds)
            self.gameover = False
            self.goalScored = True
            self.halftime = False
            self.startGame = False
            self.rightGoal.scoredOn += 1
        elif pygame.sprite.collide_rect(self.leftGoal, self.ball):
            self.gameover = False
            self.goalScored = True
            self.halftime = False
            self.startGame = False
            self.leftGoal.scoredOn += 1
        else:  # do nothing if no goal scored
            return
        self.ball.direction = [0,0]
        self.ball.posOnField = (self.width//2 - 15, self.height//2 - 15)
        # make players return to positions - make specified positions under player class
        self.rightSidePlayers, self.players = [], []
        for i in range(self.numplayers):
            px, py = self.width//(5), self.height - 70*(i+3)
            self.players.append(Player((px, py)))
        for i in range(self.numplayers):
            px, py = 3.7*self.width//(5), self.height - 70*(i+3)
            self.rightSidePlayers.append(Player((px, py),False))
        self.playerSelected = 2
        self.rightPlayerSelected = 2

    def checkBounceOffPlayers(self):
        # not really cool unless ball actually rolls and hits them though
        for player in self.players:
            if pygame.sprite.collide_rect(player, self.ball):
                player.possess = True
                # ball.direction[0] = -ball.direction[0]  # for bounce
                self.ball.direction = [0,0]
                newPos = (player.rect.topleft[0] + 42, player.rect.topleft[1] + 10)
                self.ball.posOnField = newPos  # perfect position for throw in actually
            else:   player.possess = False
        for player in self.rightSidePlayers:
            if pygame.sprite.collide_rect(player, self.ball):
                player.possess = True
                # ball.direction[0] = -ball.direction[0]  # for bounce
                self.ball.direction = [0,0]
                newPos = (player.rect.topleft[0] - 10, player.rect.topleft[1] + 10)
                self.ball.posOnField = newPos  # so opposing team can stop it at least?
            else:   player.possess = False
        self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
        self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
        self.players[self.playerSelected].rect.topleft = self.players[self.playerSelected].posOnField
        self.ball.rect.topleft = self.ball.posOnField

    def isValidBall(self, team):
        # to check if player is near enough to ball
        if team == 1:
            tlist = self.players
            selected = self.playerSelected
        else:
            tlist = self.rightSidePlayers
            selected = self.rightPlayerSelected
        kicker = tlist[selected].rect.topleft
        ball = self.ball.rect.topleft
        #if (kicker[0] - 30 < ball[0] < kicker[0] + 30) and (kicker[1] < ball[1] < kicker[1] + 45):
        if tlist[selected].possess == True:
            return True
        return False

    def keepPlayersInFrame(self, team):  # doesn't let players go offscreen
        for player in team:
            if player.posOnField[0] < -15:
                player.direction = [0,0]
            elif player.posOnField[0] + 45 > self.width + 15:
                player.direction = [0,0]
            elif player.posOnField[1] < -30:
                player.direction = [0,0]
            elif player.posOnField[1] + 60 > self.height + 30:
                player.direction = [0,0]

    def keepRefOnField(self):
        if self.mainRef.posOnField[0] < -15 or self.mainRef.posOnField[0] + 45 > self.width + 15:
            self.mainRef.direction[0] = -self.mainRef.direction[0]
        elif self.mainRef.posOnField[1] < -30 or self.mainRef.posOnField[1] + 60 > self.height + 30:
            self.mainRef.direction[1] = -self.mainRef.direction[1]
    
    def redrawAll(self):
        if self.gameover:
            if self.leftGoal.scoredOn > self.rightGoal.scoredOn:
                winner = "Player 2"
            elif self.rightGoal.scoredOn > self.leftGoal.scoredOn:
                winner = "Player 1"
            else:
                winner = 0
            gameoverScreen(self.screen, winner)
        elif self.goalScored:
            goalScoredScreen(self.screen)
        elif self.halftime:
            halftimeScreen(self.screen)
        elif self.help:
            helpScreen(self.screen)
        elif self.startGame:
            self.getStartActions()
        #elif self.offScreen:
        #    offFrameScreen(self.screen)
        else:
            drawField(self.screen, self.width, self.height, self.margin)
            self.ball.draw(self.screen)
            for player in self.players:
                player.draw(self.screen)
            for player2 in self.rightSidePlayers:
                player2.draw(self.screen)
            self.leftGoal.draw(self.screen)
            self.rightGoal.draw(self.screen)
            Plumbob((self.plum_x, self.plum_y), False).draw(self.screen)
            Plumbob((self.plum_2x, self.plum_2y), True).draw(self.screen)
            for flag in self.cornerFlags:
                flag.draw(self.screen, True)
            for linesman in self.linesmen:
                linesman.draw(self.screen)
            self.mainRef.draw(self.screen)
            # display score
            coordinates = (self.width//2 - 28, self.margin + 5, 56, 30)
            tex = str(self.rightGoal.scoredOn) + ' : ' + str(self.leftGoal.scoredOn)
            pygame.draw.rect(self.screen, (0,0,0), coordinates, 0)
            message_display(self.screen, tex, (self.width//2,self.margin + 22), 25)
            # display time left
            coordtime = (self.width//2 - 26, self.margin - 25, 52, 20)
            timeLeft = self.timeOfGame - int(self.timeSubtract)
            timetex = str(timeLeft//60) + " : " + str(timeLeft%60)
            pygame.draw.rect(self.screen, (50,50,50), coordtime, 0)
            message_display(self.screen, timetex, (self.width//2,self.margin - 13), 18)
            if timeLeft == self.halfTime:
                self.halftime = True
                self.timeSubtract += 1
                self.ball.direction = [0,0]
                self.ball.posOnField = (self.width//2 - 15, self.height//2 - 15)
                # make players return to positions
                self.rightSidePlayers, self.players = [], []
                for i in range(self.numplayers):
                    px, py = self.width//(5), self.height - 70*(i+3)
                    self.players.append(Player((px, py)))
                for i in range(self.numplayers):
                    px, py = 3.7*self.width//(5), self.height - 70*(i+3)
                    self.rightSidePlayers.append(Player((px, py),False))
                self.playerSelected = 2
                self.rightPlayerSelected = 2
            if timeLeft == 0:
                self.gameover = True
            if self.players[self.playerSelected].possess == True:
                text = 'Player 1 has posession!'
                message_display(self.screen, text, (self.width//2,self.margin+45), 20)
            elif self.rightSidePlayers[self.rightPlayerSelected].possess == True:
                text = 'Player 2 has posession!'
                message_display(self.screen, text, (self.width//2,self.margin+45), 20)

    def getStartActions(self):  # allow player to choose to start, back up to proper position
        # Code adapted from Fletcher's notes
        if self.kinect.has_new_color_frame():
            frame = self.kinect.get_last_color_frame()
            self.drawColorFrame(frame, self.frameSurface)
            frame = None
        
        cenX = 3*self.width//4 + 70
        pygame.draw.rect(self.frameSurface, (0,0,0), (cenX, self.height/2 - 200, 300, 150))
        text = 'CONTROLS'
        message_display(self.frameSurface, text, (cenX + 150, self.height/2 - 120), 50, (255,255,255))
        image = pygame.image.load("images/soccerball.png")
        img = pygame.transform.scale(image.convert_alpha(), (300,300))
        self.frameSurface.blit(img, (cenX, self.height/2 + 200))
        text2 = 'PLAY GAME'
        message_display(self.frameSurface, text2, (cenX + 150, self.height/2 + 350), 50, (0,0,0))
        text = 'Kinect Frame Not In This Area'
        message_display(self.screen, text, (self.width//2, self.height - 50), 40)

        if self.kinect.has_new_body_frame(): 
            self.bodies = self.kinect.get_last_body_frame()

            if self.bodies is not None: 
                for i in range(0, self.kinect.max_body_count):
                    body = self.bodies.bodies[i]
                    if not body.is_tracked: 
                        continue 
                
                    joints = body.joints 
                    # care about hand positions
                    if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curRightHandHeight = joints[PyKinectV2.JointType_HandRight].Position.y
                        self.curRightHandX = joints[PyKinectV2.JointType_HandRight].Position.x
                        self.curRightHandDist = joints[PyKinectV2.JointType_HandRight].Position.z
                    if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curLeftHandHeight = joints[PyKinectV2.JointType_HandLeft].Position.y
                        self.curLeftHandX = joints[PyKinectV2.JointType_HandLeft].Position.x
                        self.curLeftHandDist = joints[PyKinectV2.JointType_HandLeft].Position.z
                    if joints[PyKinectV2.JointType_SpineMid].TrackingState == PyKinectV2.TrackingState_NotTracked or \
                        joints[PyKinectV2.JointType_FootLeft].TrackingState == PyKinectV2.TrackingState_NotTracked or \
                        joints[PyKinectV2.JointType_HandRight].TrackingState == PyKinectV2.TrackingState_NotTracked or \
                        joints[PyKinectV2.JointType_Head].TrackingState == PyKinectV2.TrackingState_NotTracked:
                        text = 'Move fully into frame!'
                        message_display(self.frameSurface, text, (self.width//2,self.height//2), 30)
                        pygame.display.update()
                    # display circles on hands
                    if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        LHcoords = self.kinect.body_joint_to_color_space(joints[PyKinectV2.JointType_HandLeft])
                        try:
                            l_x, l_y = int(LHcoords.x), int(LHcoords.y)
                        except: pass  # when too close, may mess up and try to convert infinity to an int
                        pygame.draw.circle(self.frameSurface, (200,109,33), (l_x, l_y), 25)
                    if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        RHcoords = self.kinect.body_joint_to_color_space(joints[PyKinectV2.JointType_HandRight])
                        r_x, r_y = int(RHcoords.x), int(RHcoords.y)
                        pygame.draw.circle(self.frameSurface, (200,109,33), (r_x, r_y), 25)
                    if (cenX < l_x < cenX + 300 and self.height/2 - 200 < l_y < self.height/2 - 50) or \
                        (cenX < r_x < cenX + 300 and self.height/2 - 200 < r_y < self.height/2 - 50):
                        if PyKinectV2.HandState_Closed == body.hand_right_state or PyKinectV2.HandState_Closed == body.hand_left_state:  # much of the joints and hand position code inferred from PyKinect2 source code on Github
                            self.gameover = False
                            self.goalScored = False
                            self.halftime = False
                            self.startGame = False
                            self.help = True
                            # select controls screen
                    elif (cenX < l_x < cenX + 300 and self.height/2 + 200 < l_y < self.height/2 + 500) or \
                        (cenX < r_x < cenX + 300 and self.height/2 + 200 < r_y < self.height/2 + 500):
                        if PyKinectV2.HandState_Closed == body.hand_right_state or PyKinectV2.HandState_Closed == body.hand_left_state:
                            # select game play mode
                            self.gameover = False
                            self.goalScored = False
                            self.halftime = False
                            self.startGame = False
                            self.help = False

    
    def getKick(self):
        if not self.isValidBall(1):
            return
        if self.kinect.has_new_body_frame():
            self.bodies = self.kinect.get_last_body_frame()

            if self.bodies is not None:
                for i in range(0, self.kinect.max_body_count):
                    body = self.bodies.bodies[i]
                    if not body.is_tracked:
                        self.offScreen = True
                        continue

                    self.offScreen = False

                    joints = body.joints

                    # save the foot positions
                    if joints[PyKinectV2.JointType_FootRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curRightLegHeight = joints[PyKinectV2.JointType_FootRight].Position.y
                        self.curRightLegX = joints[PyKinectV2.JointType_FootRight].Position.x
                        self.curRightLegDist = joints[PyKinectV2.JointType_FootRight].Position.z
                    if joints[PyKinectV2.JointType_FootLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curLeftLegHeight = joints[PyKinectV2.JointType_FootLeft].Position.y
                        self.curLeftLegX = joints[PyKinectV2.JointType_FootLeft].Position.x
                        self.curLeftLegDist = joints[PyKinectV2.JointType_FootLeft].Position.z

                    # shoot
                    self.kick = self.prevLeftLegDist - self.curLeftLegDist
                    if self.kick > 0.1 or self.kick < -0.1:
                        message_display(self.screen, 'Powering Up', (self.width-3*self.margin,2*self.margin), 20)
                        pygame.display.update()
                    # for now, shoot is reliant only on z-positions i.e. forward/backward. not proper form.
                    # also only left leg right now.
                    # if self.kick is positive, then is moving forward. when stops moving forward, kick.
                    if self.kick > 0.1:
                        self.movingForward = True
                    elif self.kick < -0.1:
                        if self.movingForward and self.kickPower > 4:  # direction change
                            self.ball.posOnField = (self.ball.posOnField[0] + 20*self.kickPower, self.ball.posOnField[1])
                            message_display(self.screen, 'Shoot!', (self.width-3*self.margin,2*self.margin), 20)
                            pygame.display.update()
                            self.movingForward = None
                            self.kickPower = 0
                        self.movingForward = False
                    else: # if stopped moving
                        if self.movingForward and self.kickPower > 4:
                            self.ball.posOnField = (self.ball.posOnField[0] + 20*self.kickPower, self.ball.posOnField[1])  # base on vectors or coords somehow
                            self.movingForward = None
                        self.kickPower = 0 # reset power after shot is taken

                    if self.movingForward != None:
                        self.kickPower += 1 # for now, kicking back and forward will increase power equally

                    self.prevLeftLegDist = self.curLeftLegDist


    def getThrowIn(self):
        if not self.isValidBall(1):
            return
        if self.kinect.has_new_body_frame():
            self.bodies = self.kinect.get_last_body_frame()

            if self.bodies is not None:
                for i in range(0, self.kinect.max_body_count):
                    body = self.bodies.bodies[i]
                    if not body.is_tracked:
                        self.offScreen = True
                        continue

                    self.offScreen = False

                    joints = body.joints
                    # for throw ins
                    if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curRightHandHeight = joints[PyKinectV2.JointType_HandRight].Position.y
                        self.curRightHandX = joints[PyKinectV2.JointType_HandRight].Position.x
                        self.curRightHandDist = joints[PyKinectV2.JointType_HandRight].Position.z
                    if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curLeftHandHeight = joints[PyKinectV2.JointType_HandLeft].Position.y
                        self.curLeftHandX = joints[PyKinectV2.JointType_HandLeft].Position.x
                        self.curLeftHandDist = joints[PyKinectV2.JointType_HandLeft].Position.z
                    if joints[PyKinectV2.JointType_Head].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curHeadHeight = joints[PyKinectV2.JointType_Head].Position.y
                        self.curHeadX = joints[PyKinectV2.JointType_Head].Position.x
                        self.curHeadDist = joints[PyKinectV2.JointType_Head].Position.z

                    self.rightArmMove = self.prevRightHandDist - self.curRightHandDist
                    self.leftArmMove = self.prevLeftHandDist - self.curLeftHandDist
                    if self.curRightHandHeight > self.curHeadHeight and \
                        self.curLeftHandHeight > self.curHeadHeight:
                        txt = 'Getting Ready To Throw In'
                        message_display(self.screen, txt, (self.width-3*self.margin,2*self.margin), 20)
                        pygame.display.update()
                        if self.leftArmMove > 0: # for debugging purposes: why is this hand not being detected
                            print('yay left arm')
                        if self.rightArmMove > 0:# and self.leftArmMove > 0:
                            throwForward = True
                            self.throwPower += 1
                        #elif self.rightArmMove == 0 and self.leftArmMove == 0 and throwForward:
                         #   print('THROOOOOW', self.throwPower)
                          #  self.throwPower = 0
                        elif self.rightArmMove < 0 and self.leftArmMove < 0:
                            throwForward = False
                            self.throwPower += 1
                    else:
                        if self.throwPower > 4:# and throwForward:
                            txt = 'Throw-In!'
                            message_display(self.screen, txt, (self.width-3*self.margin,2*self.margin), 20)
                            pygame.display.update()
                            # below commented code for throwing into field, not necessarily to a teammate
                            #if self.TIleft:
                             #   self.ball.posOnField = (self.ball.posOnField[0], self.ball.posOnField[1] + 7*self.throwPower)
                            #elif self.TIright:
                             #   self.ball.posOnField = (self.ball.posOnField[0], self.ball.posOnField[1] - 7*self.throwPower)
                            newPossess = self.findNearestTeammate(1)
                            self.ball.posOnField = newPossess
                            self.ball.rect.topleft = self.ball.posOnField
                        self.throwPower = 0

                        #ideally use: if self.curRightHandDist > self.curHeadDist and self.curLeftHandDist > self.curHeadDist:

                    self.prevRightHandDist = self.curRightHandDist

    def getPass(self):
        if not self.isValidBall(1):
            return
        if self.kinect.has_new_body_frame():
            self.bodies = self.kinect.get_last_body_frame()

            if self.bodies is not None:
                for i in range(0, self.kinect.max_body_count):
                    body = self.bodies.bodies[i]
                    if not body.is_tracked:
                        self.offScreen = True
                        continue

                    self.offScreen = False

                    joints = body.joints
                    # save the foot positions
                    if joints[PyKinectV2.JointType_FootRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curRightLegHeight = joints[PyKinectV2.JointType_FootRight].Position.y
                        self.curRightLegX = joints[PyKinectV2.JointType_FootRight].Position.x
                        self.curRightLegDist = joints[PyKinectV2.JointType_FootRight].Position.z
                    if joints[PyKinectV2.JointType_FootLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curLeftLegHeight = joints[PyKinectV2.JointType_FootLeft].Position.y
                        self.curLeftLegX = joints[PyKinectV2.JointType_FootLeft].Position.x
                        self.curLeftLegDist = joints[PyKinectV2.JointType_FootLeft].Position.z

                    if self.origPassPos == (0,0):
                        self.origPassPos = (self.curLeftLegX, self.curRightLegX)
                        self.prevLeftLegX = self.curLeftLegX
                        self.prevRightLegX = self.curRightLegX

                    self.passRightLeg = self.prevRightLegX - self.curRightLegX
                    if self.passRightLeg > 0.1:
                        self.passRight = False
                    elif self.passRightLeg < -0.1:
                        self.passRight = True
                    else:
                        if self.passRight:
                            txt = 'Pass To Teammate'
                            message_display(self.screen, txt, (self.width-3*self.margin,2*self.margin), 20)
                            pygame.display.update()
                            newPossess = self.findNearestTeammate(1)
                            self.ball.posOnField = newPossess
                            self.ball.rect.topleft = self.ball.posOnField
                            self.passRight = None
                            break
                        elif self.passRight == False:
                            txt = 'Pass to Teammate'
                            message_display(self.screen, txt, (self.width-3*self.margin,2*self.margin), 20)
                            pygame.display.update()
                            newPossess = self.findNearestTeammate(1)
                            self.ball.posOnField = newPossess
                            self.ball.rect.topleft = self.ball.posOnField
                            self.passRight = None
                            break
                        #self.passPower = 0
                    #self.passRight = None

                    self.prevRightLegX = self.curRightLegX

    def getPlayerChange(self):  # detects player change and movement
        if self.kinect.has_new_body_frame():
            self.bodies = self.kinect.get_last_body_frame()

            if self.bodies is not None:
                for i in range(0, self.kinect.max_body_count):
                    body = self.bodies.bodies[i]
                    if not body.is_tracked:
                        continue

                    joints = body.joints
                    # for detecting user's motion to change players
                    if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curRightHandHeight = joints[PyKinectV2.JointType_HandRight].Position.y
                        self.curRightHandX = joints[PyKinectV2.JointType_HandRight].Position.x
                        RHcoords = self.kinect.body_joint_to_color_space(joints[PyKinectV2.JointType_HandRight])
                        r_x, r_y = int(RHcoords.x), int(RHcoords.y)
                    if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked:
                        self.curLeftHandX = joints[PyKinectV2.JointType_HandLeft].Position.x

                    if PyKinectV2.HandState_Lasso == body.hand_right_state and self.width - 30 < r_x and r_y < 30:
                        self.help = True  # go to help screen if lasso in top right corner
                        self.gameover = False
                        self.goalScored = False
                        self.halftime = False
                        self.startGame = False
                    
                    if self.prevLHX == 0:
                        self.prevRHH = self.curRightHandHeight
                        self.prevLHX = self.curLeftHandX
                        self.prevRHX = self.curRightHandX
                    moveY = self.prevRHH - self.curRightHandHeight
                    moveX = self.prevRHX - self.curRightHandX
                    swipeLH = self.prevLHX - self.curLeftHandX
                    # for player switch detection
                    if swipeLH > 0.2:
                        self.oneswipe = True
                    elif self.oneswipe:
                            #change player.selected upon left hand swipe (in to out)
                            txt = 'Switching Player Selection'
                            message_display(self.screen, txt, (self.width-3*self.margin,2*self.margin), 20)
                            pygame.display.update()
                            self.oneswipe = False
                            if self.playerSelected < self.numplayers - 1:
                                self.playerSelected += 1
                            else:
                                self.playerSelected = 0
                            self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
                            self.plum_y = self.players[self.playerSelected].posOnField[1] - 24

                    self.prevLHX = self.curLeftHandX

                    origPos = self.players[self.playerSelected].posOnField
                    self.isRHClosed = (PyKinectV2.HandState_Closed == body.hand_right_state)  # detect fist to stop motion
                    if moveX > 0.2:
                        # update player position x
                        # don't know why i decided to use a tuple please change
                        self.players[self.playerSelected].direction = [-7,0]
                    elif moveX < -0.2:
                        self.players[self.playerSelected].direction = [7,0]
                    if moveY > 0.2:
                        # update player position y
                        self.players[self.playerSelected].direction = [0,7]
                    elif moveY < -0.2:
                        self.players[self.playerSelected].direction = [0,-7]
                    if self.isRHClosed:
                        self.players[self.playerSelected].direction = [0,0]  # stop automatic motion
                    self.prevRHH = self.curRightHandHeight
                    self.prevRHX = self.curRightHandX
                self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
                self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
                self.players[self.playerSelected].rect.topleft = self.players[self.playerSelected].posOnField
                self.ball.rect.topleft = self.ball.posOnField
                self.checkGoal()
                self.checkBounceOffPlayers()


    def timerFired(self):
        if self.gameover or self.goalScored or self.halftime or self.startGame:
            return
        elif self.help:
            if self.kinect.has_new_body_frame():
                self.bodies = self.kinect.get_last_body_frame()
    
                if self.bodies is not None:
                    for i in range(0, self.kinect.max_body_count):
                        body = self.bodies.bodies[i]
                        if not body.is_tracked:
                            self.offScreen = True
                            continue
                        if PyKinectV2.HandState_Lasso == body.hand_right_state:
                            self.help = False
                            self.gameover = False
                            self.goalScored = False
                            self.halftime = False
                            if self.timeSubtract != 0:
                                self.startGame = False
                            else:   self.startGame = True
                            break
            return
        else:
            self.timeSubtract += 0.085  # why is this the update rate
        if self.outOfBoundsThrow:
            self.moveToBall()  # makes it valid so no need to check
            self.getThrowIn()
        elif self.outOfBoundsGoalkick:
            self.moveToBall()
            self.getKick()
        else:
            self.getPlayerChange()
            self.getKick()
            self.getPass()
        if self.ball.posOnField[0] + 30 < self.margin:
            message_display(self.screen, 'Goalkick for Player 1', (self.width-3*self.margin,2*self.margin), 20)
            pygame.display.update()
            self.outOfBoundsGoalkick = True
            self.GKleft = True
            self.ball.direction = [0,0]
            self.ball.posOnField = (self.margin - 30, self.ball.posOnField[1])
        elif self.ball.posOnField[0] > self.width - self.margin:
            message_display(self.screen, 'Goalkick for Player 2', (self.width-3*self.margin,2*self.margin), 20)
            pygame.display.update()
            self.outOfBoundsGoalkick = True
            self.GKright = True
            self.ball.direction = [0,0]
            self.ball.posOnField = (self.width - self.margin, self.ball.posOnField[1])
        elif self.ball.posOnField[1] + 30 < self.margin:
            message_display(self.screen, 'Take Throw-In', (self.width-3*self.margin,2*self.margin), 20)
            pygame.display.update()
            self.outOfBoundsThrow = True
            self.TIleft = True
            self.ball.direction = [0,0]
            self.ball.posOnField = (self.ball.posOnField[0], self.margin - 30)
        elif self.ball.posOnField[1] > self.height - self.margin:
            message_display(self.screen, 'Take Throw-In', (self.width-3*self.margin,2*self.margin), 20)
            pygame.display.update()
            self.outOfBoundsThrow = True
            self.TIright = True
            self.ball.direction = [0,0]
            self.ball.posOnField = (self.ball.posOnField[0], self.height - self.margin)
        else:
            self.outOfBoundsGoalkick = False
            self.outOfBoundsThrow = False
        self.ball.posOnField = self.ball.move()  # from speed specified from kinect
        self.ball.rect.topleft = self.ball.posOnField
        self.checkGoal()
        self.checkBounceOffPlayers()
        #self.selectNearest()  # prevents movement of other players
        #self.moveToBall()  # prevents free movement / selection of others brings them to the ball, making teammates somewhat useless
        self.players[self.playerSelected].posOnField = self.players[self.playerSelected].move()
        self.rightSidePlayers[self.rightPlayerSelected].posOnField = self.rightSidePlayers[self.rightPlayerSelected].move()
        for p in range(len(self.players)):
            if p != self.playerSelected and p != self.players[p].teammate1 and p != self.players[p].teammate2:  # and not two other randomly chosen players on the team
                self.players[p].posOnField = self.players[p].moveAutomatically(self.players[self.playerSelected].direction)
            self.players[p].rect.topleft = self.players[p].posOnField
        for p in range(len(self.rightSidePlayers)):
            if p != self.rightPlayerSelected and p != self.rightSidePlayers[p].teammate1 and p != self.rightSidePlayers[p].teammate2:  # and not two other randomly chosen players on the team
                self.rightSidePlayers[p].posOnField = self.rightSidePlayers[p].moveAutomatically(self.rightSidePlayers[self.rightPlayerSelected].direction)
            self.rightSidePlayers[p].rect.topleft = self.rightSidePlayers[p].posOnField
        self.keepPlayersInFrame(self.players)
        self.keepPlayersInFrame(self.rightSidePlayers)
        self.plum_x = self.players[self.playerSelected].posOnField[0] + 25
        self.plum_y = self.players[self.playerSelected].posOnField[1] - 24
        self.plum_2x = self.rightSidePlayers[self.rightPlayerSelected].posOnField[0] + 25
        self.plum_2y = self.rightSidePlayers[self.rightPlayerSelected].posOnField[1] - 24
        self.players[self.playerSelected].rect.topleft = self.players[self.playerSelected].posOnField
        self.rightSidePlayers[self.rightPlayerSelected].rect.topleft = self.rightSidePlayers[self.rightPlayerSelected].posOnField
        self.mainRef.posOnField = self.mainRef.move()
        self.mainRef.rect.topleft = self.mainRef.posOnField
        self.keepRefOnField()

    def run(self): # opens pygame window, draws field
        self._keys = dict()
        while self.play:
            if self.startGame:
                self.getStartActions()
                hToW = float(self.frameSurface.get_height()) / self.frameSurface.get_width()
                targetHeight = int(hToW * self.screen.get_width())
                surfaceToDraw = pygame.transform.scale(self.frameSurface, (self.screen.get_width(), targetHeight));
                self.screen.blit(surfaceToDraw, (0,0))
                surfaceToDraw = None
                pygame.display.update()  # ^also from Fletcher's code
            for event in pygame.event.get():  # part of basic framework from https://qwewy.gitbooks.io/pygame-module-manual/chapter1/framework.html
                if event.type == pygame.KEYDOWN:
                    self._keys[event.key] = True
                    self.keyPressed(event.key, event.mod)
                elif event.type == pygame.QUIT:
                    self.play = False
            if self.isValidBall(2):
                if event.type == pygame.KEYDOWN:
                    self.rightValidActions(event.key, event.mod)
            self.timerFired()
            self.redrawAll()
            pygame.display.flip()
            # 60 frames per second
            self.clock.tick(60)
        self.kinect.close()
        pygame.quit()


game = GamePlayMode()
game.backgroundSound()
game.run()
