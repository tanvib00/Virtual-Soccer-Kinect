# functions for different game screens and text placement
# all screens shown in game defined here, except for gameplay mode (see 'visuals.py')

import pygame

def message_display(screen, text, centered, size, color=(155,155,155)):  # this and above function adapted from https://pythonprogramming.net/displaying-text-pygame-screen/
    msg = pygame.font.Font('freesansbold.ttf',size)
    textSurface = msg.render(text, True, color)
    TextSurf, TextRect = textSurface, textSurface.get_rect()
    TextRect.center = (centered)
    screen.blit(TextSurf, TextRect)

def offFrameScreen(screen):
# https://www.google.com/url?sa=i&source=images&cd=&ved=2ahUKEwjV6Net-_jeAhUFneAKHSw7AhwQjRx6BAgBEAU&url=https%3A%2F%2Fwww.pngarts.com%2Fexplore%2F27224&psig=AOvVaw0hkT3KUxxZvFeHYyjC0r3G&ust=1543558956993050
    screen.fill((155,155,155))
    pauseImg = pygame.image.load("images/pause_.png")
    screen.blit(pauseImg.convert_alpha(), (69,244))
    message_display(screen, 'Please move into frame!', (500,325), 40)

def startScreen(screen):
    screen.fill((69,23,81))
    screen.set_alpha(150)
    pygame.draw.rect(screen, (255,255,255), (100, 100, 500, 500), 0)
    message_display(screen, 'Press Enter to Begin! (\'r\' to Restart)', (500,325), 40)

def goalScoredScreen(screen):
    screen.fill((155,102,80))
    message_display(screen, 'GOAL!!!', (500,325), 40)
    message_display(screen, 'Press Enter to Resume Play', (500,365), 40)

def halftimeScreen(screen):
    screen.fill((20,20,20))
    message_display(screen, 'Halftime!', (500,325), 40)
    message_display(screen, 'Press Enter to Resume Play', (500,365), 40)

def gameoverScreen(screen, winner):
    screen.fill((0,0,0))
    text = 'Game Over, %s Wins!' % (winner)
    if winner == 0:
        text = 'It\'s a tie!'
    message_display(screen, text, (500,325), 40)
    message_display(screen, 'Press \'r\' to play again', (500,365), 40)
# make them look pretty - put in images, moving ones

def helpScreen(screen):
    screen.fill((255,255,255))
    black = (0,0,0)
    red = (255,0,0)
    green = (0,255,0)
    blue = (0,0,255)
    message_display(screen, 'CONTROLS FOR GAMEPLAY', (500,100), 30, black)
    # kinect instructions: you are playing from the left side. If ball goes out, you can take a throw in or goalkick. You can win the ball from opposing team by kicking it away from them once close enough. shoot in front of the goal to score!
    message_display(screen, 'Player 1 Kinect Controls', (500,160), 25, black)
    message_display(screen, 'Left-Hand Swipe: Switch Player', (300,185), 20, blue)
    message_display(screen, 'Right-Hand Swipe (Up/Down/Left/Right): Move Player', (500,210), 20, blue)
    message_display(screen, 'Right-Hand Fist: Stop Player Movement', (700,185), 20, blue)
    message_display(screen, 'Possible Actions if close enough to the ball:', (500,245), 20, black)
    message_display(screen, 'Left-Foot Forward Kick: Shoot!', (500,270), 20, blue)
    message_display(screen, 'Right-Foot Pass: Pass to Nearest Player', (500,295), 20, blue)
    # keypress player instructions: you are playing from the right side. If ball goes out, you can take a throw in or goalkick. You can win the ball from opposing team by kicking it away from them or running across the ball's path. shoot in front of the goal to score! 
    message_display(screen, 'Player 2 Keyboard Controls', (500,350), 25, black)
    message_display(screen, 'Comma Key: Switch Player', (300,375), 20, green)
    message_display(screen, 'Arrow Keys: Move Player', (500,400), 20, green)
    message_display(screen, 'Period Key: Stop Player Movement', (700,375), 20, green)
    message_display(screen, 'Possible Actions if close enough to the ball:', (500,435), 20, black)
    message_display(screen, 'Spacebar: Shoot!', (500,460), 20, green)
    message_display(screen, 'Shift Key: Pass to Nearest Player', (500,485), 20, green)
    message_display(screen, 'r key: Restart', (200,530), 20, red)
    message_display(screen, 'h key: Controls Page', (470,530), 20, red)
    message_display(screen, 'Return key: Exit Screen', (750,530), 20, red)
