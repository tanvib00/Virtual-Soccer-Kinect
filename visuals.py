# contains classes for all the visual objects in the game (players, ball, goals...)
# function for drawing soccer field
# defines object attributes, allowing corner flags to wave, player/ball positions to be redefined, etc.

import pygame
import math
from screens import *
import random


def drawField(screen, width, height, margin):  # soccer field lines, stops flickering
    screen.fill((51,102,0))  # green background for grass
    pygame.draw.rect(screen, (51,102,0), screen.get_rect(), 0)
    white = (240,240,240)  # a little off so ball is more clear
    corners = (margin, margin, width - 2*margin, height - 2*margin)  # top left, bottom right
    pygame.draw.rect(screen, white, corners, 5)  # sidelines
    pygame.draw.line(screen, white, (width//2,margin), (width//2, height - margin), 5)  # https://www.pygame.org/docs/ref/draw.html
    pygame.draw.circle(screen, white, (width//2, height//2), width//10, 5)
    pygame.draw.rect(screen, white, (margin, margin + (height-2*margin)//4, 4*margin, (height-2*margin)//2), 5)
    pygame.draw.rect(screen, white, (width-5*margin, margin + (height-2*margin)//4, 4*margin, (height-2*margin)//2), 5)
    pygame.draw.circle(screen, (0,0,0), (width - 15, 15), 15)
    message_display(screen, '?', (width - 15, 15), 20)
    # draw quarter circles at corners, goal box, penalty box, semicircle @ top of box, dot @ pk spot


class SoccerBall(pygame.sprite.Sprite):  # https://www.pygame.org/docs/ref/sprite.html
    def __init__(self, pos_on_field):  # pos_on_field is top left (x,y)
        super(SoccerBall, self).__init__()
        self.image = pygame.image.load("images/soccerball.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (30,30))
        self.posOnField = pos_on_field
        self.direction = [0,0]  # stationary at first, change from kinect data
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField

    def draw(self, screen):  # need camelCase?
        screen.blit(self.img, self.posOnField)  # maybe make it blit over the field image at certain position (and size, as specified? how? idk)

    def moveKinect(self, plus_x, plus_y):  # get plus_x and plus_y from Kinect info - not in use atm
        self.posOnField = (self.posOnField[0] + plus_x, self.posOnField[1] + plus_y)

    def move(self):
        return (self.posOnField[0] + self.direction[0], self.posOnField[1] + self.direction[1])


class Player(pygame.sprite.Sprite):
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwidsIyb6uLeAhXhlOAKHZyTCUMQjRx6BAgBEAU&url=https%3A%2F%2Ftechflourish.com%2Fcategories%2Fclipart-soccer-player-no-ball.html&psig=AOvVaw1d8zpOPij8SCMVEHSJrlsK&ust=1542798307118373
    def __init__(self, pos_on_field, left=True):
        super(Player, self).__init__()
        self.image = pygame.image.load("images/player.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (45,60))
        if not left:
            self.image = pygame.image.load("images/player2.png")
            self.img = pygame.transform.scale(self.image.convert_alpha(), (45,60))
            self.img = pygame.transform.flip(self.img, True, False)
        self.posOnField = pos_on_field
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField
        self.possess = False
        self.direction = [0,0]
        # two teammates that move with this one automatically
        self.teammate1 = random.randint(0,4)
        self.teammate2 = random.randint(0,4)  # called once

    def draw(self, screen):
        screen.blit(self.img, self.posOnField)

    def move(self):
        return (self.posOnField[0] + self.direction[0], self.posOnField[1] + self.direction[1])

    def dist(self, otherRect):  # input other's top left coordinates
        return math.sqrt((self.rect.topleft[0] - otherRect[0])**2 + (self.rect.topleft[1] - otherRect[1])**2)

    def moveAutomatically(self, dir):  # get dir of movement of selected, move with player in same direction at random speed
        if dir[0] < 0:
            self.movingLeft = True
        elif dir[0] > 0:
            self.movingLeft = False
        elif dir[1] < 0:
            self.movingDown = False
        elif dir[1] > 0:
            self.movingDown = True
        else:  # if dir == [0,0]
            self.movingLeft = None
            self.movingDown = None
        x,y = 2,6
        if self.movingLeft == True:
            newspeed = random.randint(x,y)
            self.direction = [-newspeed,0]
        elif self.movingLeft == False:
            newspeed = random.randint(x,y)
            self.direction = [newspeed,0]
        elif self.movingDown == True:
            newspeed = random.randint(x,y)
            self.direction = [0,newspeed]
        elif self.movingDown == False:
            newspeed = random.randint(x,y)
            self.direction = [0,-newspeed]
        elif self.movingDown == None and self.movingLeft == None:
            self.direction = [0,0]
        return (self.posOnField[0] + self.direction[0], self.posOnField[1] + self.direction[1])


class Referee(pygame.sprite.Sprite):
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwi4tdrT24vfAhXoT98KHTcDAnQQjRx6BAgBEAU&url=https%3A%2F%2Fwww.iconfinder.com%2Ficons%2F2180950%2Fblock_football_obstruct_obstruction_referee_soccer_icon&psig=AOvVaw0_944v1P4MkqcbWidTxYMf&ust=1544203273618433
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwiY55zl24vfAhUDm-AKHfqOAI8QjRx6BAgBEAU&url=http%3A%2F%2Fchittagongit.com%2Ficon%2Freferee-icon-29.html&psig=AOvVaw0_944v1P4MkqcbWidTxYMf&ust=1544203273618433
    def __init__(self, pos_on_field, main=True):
        super(Referee, self).__init__()
        self.image = pygame.image.load("images/mainref.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (35,60))
        if not main:
            self.image = pygame.image.load("images/linesman.png")
            self.img = pygame.transform.scale(self.image.convert_alpha(), (30,30))
            self.img = pygame.transform.flip(self.img, True, False)
        self.posOnField = pos_on_field
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField
        self.direction = [0,0]

    def draw(self, screen):
        screen.blit(self.img, self.posOnField)

    def move(self):
        self.direction = [random.randint(-15,15), random.randint(-15,15)]
        return (self.posOnField[0] + self.direction[0], self.posOnField[1] + self.direction[1])

class Goal(pygame.sprite.Sprite):  # detect collision of ball with goal
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwi2y6jg6uLeAhUQTN8KHY9PDCQQjRx6BAgBEAU&url=https%3A%2F%2Ftechflourish.com%2Fcategories%2Ffootball-goal-clipart.html&psig=AOvVaw3jwemC7j8VaEvc9Dlsv34D&ust=1542798587646639
    def __init__(self, pos_on_field, left=False):  # to flip on left side
        super(Goal, self).__init__()
        self.image = pygame.image.load("images/goal.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (90,45))
        if left:
            self.img = pygame.transform.flip(self.img, True, False)  # mirror image
        self.posOnField = pos_on_field
        self.scoredOn = 0  # keep track of goals!
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField

    def draw(self, screen):
        screen.blit(self.img, self.posOnField)

class Plumbob(pygame.sprite.Sprite):
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwjg5ZOwvePeAhVyk-AKHakeDeMQjRx6BAgBEAU&url=https%3A%2F%2Fwww.pinterest.com%2Fpin%2F35325178312693178%2F&psig=AOvVaw3SLiBg7vQ9ls8jiwhh1f2Z&ust=1542820764214743
    def __init__(self, pos_on_field, left):
        super(Plumbob, self).__init__()
        self.image = pygame.image.load("images/plumbob.png")
        if left:
            self.image = pygame.image.load("images/plumbob2.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (11,22))
        self.posOnField = pos_on_field
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField

    def draw(self, screen):
        screen.blit(self.img, self.posOnField)

class CornerFlag(pygame.sprite.Sprite):
# https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwiHj-KPtfDeAhULhuAKHXIhBN0QjRx6BAgBEAU&url=https%3A%2F%2Fwww.vsathletics.com%2Fstore%2FRubber-Base-Corner-Flags.html&psig=AOvVaw2XkgpQmQiTXJE11LAKT9f0&ust=1543265223856348
    def __init__(self, pos_on_field):
        super(CornerFlag, self).__init__()
        self.image = pygame.image.load("images/cornerflag.png")
        self.img = pygame.transform.scale(self.image.convert_alpha(), (12,38))
        self.posOnField = pos_on_field
        self.rect = self.img.get_rect()
        self.rect.topleft = self.posOnField

    def draw(self, screen, switch=False):
        if switch:
            self.img = pygame.transform.flip(self.img, True, False)
        screen.blit(self.img, self.posOnField)
        # keeps switching back and forth, impression of waving
