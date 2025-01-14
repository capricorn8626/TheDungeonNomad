import pygame
from pygame import mixer
import csv
import constants
from character import Character
from weapon import Weapon
from items import Item
from world import World
from button import Button
mixer.init()
pygame.init()
screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
pygame.display.set_caption("The Dungeon Nomad")
icon_game = pygame.image.load("icon.ico")
pygame.display.set_icon(icon_game)
# create clock for maintaining frame rate
clock = pygame.time.Clock()

# define game variables
level = 1
start_intro = True
start_game = False
pause_game = False
screen_scroll = [0,0]

# define player movement variable 
going_left = False
going_right = False
going_up = False
going_down = False

# define font
font = pygame.font.Font("assets/fonts/AtariClassic.ttf",20)

# helper function to scale images
def scale_img(image,scale):
    w = image.get_width()
    h = image.get_height()
    return pygame.transform.scale(image,(w*scale,h*scale))

# load music and sound
pygame.mixer.music.load("assets/audio/bg-music.wav")
pygame.mixer.music.set_volume(0.25)
pygame.mixer.music.play(-1,0.0,5000)

shot_fx = pygame.mixer.Sound("assets/audio/arrow_shot.mp3")
shot_fx.set_volume(0.5)
hit_fx = pygame.mixer.Sound("assets/audio/arrow_hit.wav")
hit_fx.set_volume(0.5)
coin_pick_fx = pygame.mixer.Sound("assets/audio/coin.wav")
coin_pick_fx.set_volume(0.5)
heal_fx = pygame.mixer.Sound("assets/audio/heal.wav")
heal_fx.set_volume(0.5)
# load button images
restart_img = scale_img(pygame.image.load("assets/images/buttons/button_restart.png").convert_alpha(),constants.BUTTON_SCALE)
exit_img = scale_img(pygame.image.load("assets/images/buttons/button_exit.png").convert_alpha(),constants.BUTTON_SCALE)
resume_img = scale_img(pygame.image.load("assets/images/buttons/button_resume.png").convert_alpha(),constants.BUTTON_SCALE)
start_img = scale_img(pygame.image.load("assets/images/buttons/button_start.png").convert_alpha(),constants.BUTTON_SCALE)

#load heart images 
heart_empty = scale_img(pygame.image.load("assets/images/items/heart_empty.png").convert_alpha(),constants.ITEM_SCALE)
heart_half = scale_img(pygame.image.load("assets/images/items/heart_half.png").convert_alpha(),constants.ITEM_SCALE)
heart_full = scale_img(pygame.image.load("assets/images/items/heart_full.png").convert_alpha(),constants.ITEM_SCALE)

# load coin images
coin_images = []
for x in range(4):
    img = scale_img(pygame.image.load(f"assets/images/items/coin_f{x}.png").convert_alpha(),constants.ITEM_SCALE)
    coin_images.append(img)

# load health potion images
health_potion_image = scale_img(pygame.image.load("assets/images/items/potion_red.png").convert_alpha(),constants.POTION_SCALE)

item_images = []
item_images.append(coin_images)
item_images.append(health_potion_image)

#load image weapon
bow_image = scale_img(pygame.image.load("assets/images/weapons/bow.png").convert_alpha(),constants.WEAPON_SCALE)
arrow_image = scale_img(pygame.image.load("assets/images/weapons/arrow.png").convert_alpha(),constants.WEAPON_SCALE)
fireball_image = scale_img(pygame.image.load("assets/images/weapons/fireball.png").convert_alpha(),constants.FIREBALL_SCALE)
# load tile_list image 
tile_list = []
for x in range(constants.TILE_TYPES):
    tile_image = pygame.image.load(f"assets/images/tiles/{x}.png").convert_alpha()
    tile_image = pygame.transform.scale(tile_image,(constants.TILE_SIZE,constants.TILE_SIZE))
    tile_list.append(tile_image)

#load character
mob_animations = []
mob_types =["elf", "imp", "skeleton","goblin","muddy","tiny_zombie","big_demon"] 
for mob_type in mob_types:
    animation_types = ["idle", "run"]
    # load image character
    animation_list = []
    for animation in animation_types:
        # reset temporary list
        temp_list = []
        for i in range(4):
            img = pygame.image.load(f"assets/images/characters/{mob_type}/{animation}/{i}.png").convert_alpha()
            img = scale_img(img,constants.SCALE)
            temp_list.append(img)
        animation_list.append(temp_list)
    mob_animations.append(animation_list)

# function for outputting text onto the screen
def draw_text(text,font,text_color,x,y):
    img = font.render(text,True,text_color)
    screen.blit(img,(x,y))

# function for displaying game info
def draw_info():
    pygame.draw.rect(screen,constants.PANEL,(0,0,constants.SCREEN_WIDTH,50))
    pygame.draw.line(screen,constants.WHITE,(0,50),(constants.SCREEN_WIDTH,50))
    half_heart_drawned = False

    #draw lives
    for i in range(5):
        if player.health >= ((i+1)*20):
            screen.blit(heart_full,(10+i*50,0))
        elif (player.health % 20 >0) and half_heart_drawned == False:
            screen.blit(heart_half,(10+i*50,0))
            half_heart_drawned = True
        else: 
            screen.blit(heart_empty,(10+i*50,0))
    # show level
    draw_text("LEVEL: "+str(level),font,constants.WHITE,constants.SCREEN_WIDTH/2,15)
    # show score
    draw_text(f"X{player.coin_score}",font,constants.WHITE,constants.SCREEN_WIDTH - 100,15)

def reset_level():
    damage_text_group.empty()
    arrow_group.empty()
    item_group.empty()
    fireball_group.empty()
    data = []
    for row in range(constants.ROWS):
        r = [-1]* constants.COLS
        data.append(r)
    return data
# damage text class
class DamageText(pygame.sprite.Sprite):
    def __init__(self,x,y,damage,color):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage,True,color)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0
    def update(self,screen_scroll):
        # reposition based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        # move damage text up
        self.rect.y -=1
        self.counter +=1
        # delete damage text after a few secs
        if self.counter > 30:
            self.kill()

# screen fade effect
class ScreenFade():
    def __init__(self,direction,color,speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0
    
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1: #fade out
            pygame.draw.rect(screen,self.color,(0 - self.fade_counter,0,constants.SCREEN_WIDTH // 2,constants.SCREEN_HEIGHT))
            pygame.draw.rect(screen,self.color,(constants.SCREEN_WIDTH // 2 + self.fade_counter,0,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT))
            pygame.draw.rect(screen,self.color,(0,0-self.fade_counter,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT//2))
            pygame.draw.rect(screen,self.color,(0,constants.SCREEN_HEIGHT//2 +self.fade_counter,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT))
        elif self.direction == 2: #curtain down
            pygame.draw.rect(screen,self.color,(0,0,constants.SCREEN_WIDTH,0+self.fade_counter))
            if self.fade_counter >= constants.SCREEN_HEIGHT:
                fade_complete = True
                return fade_complete
        if self.fade_counter >= constants.SCREEN_WIDTH:
            fade_complete = True
        return fade_complete


# create empty tile_list
world_data = []
for row in range(constants.ROWS):
    r = [-1]* constants.COLS
    world_data.append(r)
# load data and create world
with open(f"levels/level{level}_data.csv",newline="") as csvfile:
    reader = csv.reader(csvfile)
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y]= int(tile)
world = World()
world.processData(world_data,tile_list,item_images,mob_animations)

# create Player
player = world.player

# create Player'weapon
bow = Weapon(bow_image,arrow_image)

# extract enemy from world data
enemy_list = world.enemy_list

# create sprite group
arrow_group = pygame.sprite.Group()
damage_text_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()
score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
item_group.add(score_coin)
# add the items from the level to the game
for item in world.item_list:
    item_group.add(item)

# create screen fade
intro_fade = ScreenFade(1, constants.BLACK,10)
death_fade = ScreenFade(2, constants.RED,10)

# create button
start_button = Button(constants.SCREEN_WIDTH//2-145,constants.SCREEN_HEIGHT//2 - 50,start_img)
exit_button = Button(constants.SCREEN_WIDTH//2-110,constants.SCREEN_HEIGHT//2 + 50,exit_img)
restart_button = Button(constants.SCREEN_WIDTH//2-188,constants.SCREEN_HEIGHT//2 - 50,restart_img)
resume_button = Button(constants.SCREEN_WIDTH//2-175,constants.SCREEN_HEIGHT//2 - 150,resume_img)
button_clicked = False
# Main game loop
run = True


while run == True:
    # control frame rate
    clock.tick(constants.FPS)

    # start menu
    if start_game == False:
        screen.fill(constants.MENU_BG)
        if start_button.draw(screen):
            start_game = True
            button_clicked = True
        if exit_button.draw(screen):
            run = False
    else:
        if pause_game == True:
            screen.fill(constants.MENU_BG)
            if resume_button.draw(screen):
                pause_game = False
                button_clicked = True
            if restart_button.draw(screen):
                        pause_game = False
                        button_clicked = True
                        start_intro = True
                        level = 1
                        world_data = reset_level()
                        # load data and create world
                        with open(f"levels/level{level}_data.csv",newline="") as csvfile:
                            reader = csv.reader(csvfile)
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y]= int(tile)
                        world = World()
                        world.processData(world_data,tile_list,item_images,mob_animations)
                        player = world.player
                        enemy_list = world.enemy_list
                        score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
                        item_group.add(score_coin)
                        # add the items from the level to the game
                        for item in world.item_list:
                            item_group.add(item)
            if exit_button.draw(screen):
                run = False
        else:
            screen.fill(constants.BG)
            if player.alive:
                # calculate player movement
                dx = 0
                dy = 0
                if going_left == True:
                    dx = -constants.SPEED
                if going_right == True:
                    dx = constants.SPEED
                if going_up == True:
                    dy = -constants.SPEED
                if going_down == True:
                    dy = constants.SPEED
                # player move
                screen_scroll, level_complete = player.move(dx,dy,world.obstacle_tiles,world.exit)

                # update all object
                world.update(screen_scroll)
                for e in enemy_list:
                    fireball = e.ai(player,world.obstacle_tiles,screen_scroll,fireball_image)
                    if fireball:
                        fireball_group.add(fireball)
                    if e.alive:
                        e.update()
                player.update()
                if button_clicked == False:
                    arrow = bow.update(player)
                    if arrow:                        
                        arrow_group.add(arrow)
                        shot_fx.play()
                for arrow in arrow_group:
                    damage,damage_pos = arrow.update(screen_scroll,world.obstacle_tiles,enemy_list)
                    if damage:
                        damage_text = DamageText(damage_pos.centerx,damage_pos.y,str(damage),constants.RED)
                        damage_text_group.add(damage_text)
                        hit_fx.play()
                fireball_group.update(screen_scroll,player)
                damage_text_group.update(screen_scroll)
                item_group.update(screen_scroll,player,coin_pick_fx,heal_fx) 


            # draw player on screen
            world.draw(screen)
            for e in enemy_list:
                e.draw(screen)
            player.draw(screen)  
            bow.draw(screen)
            for arrow in arrow_group:
                arrow.draw(screen)
            for fireball in fireball_group:
                fireball.draw(screen)
            damage_text_group.draw(screen)
            item_group.draw(screen)
            draw_info()
            score_coin.draw(screen)

            # check level complete
            if level_complete == True:
                start_intro = True
                level+=1
                world_data = reset_level()
                # load data and create world
                with open(f"levels/level{level}_data.csv",newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y]= int(tile)
                world = World()
                world.processData(world_data,tile_list,item_images,mob_animations)
                temp_hp = player.health
                temp_score = player.coin_score
                player = world.player
                player.health = temp_hp
                player.coin_score = temp_score
                enemy_list = world.enemy_list
                score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
                item_group.add(score_coin)
                # add the items from the level to the game
                for item in world.item_list:
                    item_group.add(item)
            # show intro
            if start_intro == True:
                if intro_fade.fade():
                    start_intro = False
                    intro_fade.fade_counter = 0
            # show death scene
            if player.alive == False:
                if death_fade.fade():
                    if restart_button.draw(screen):
                        button_clicked = True
                        death_fade.fade_counter = 0
                        start_intro = True
                        level = 1
                        world_data = reset_level()
                        # load data and create world
                        with open(f"levels/level{level}_data.csv",newline="") as csvfile:
                            reader = csv.reader(csvfile)
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y]= int(tile)
                        world = World()
                        world.processData(world_data,tile_list,item_images,mob_animations)
                        player = world.player
                        enemy_list = world.enemy_list
                        score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
                        item_group.add(score_coin)
                        # add the items from the level to the game
                        for item in world.item_list:
                            item_group.add(item)
                    if exit_button.draw(screen):
                        run = False
            
    if button_clicked and not pygame.mouse.get_pressed()[0]:
            button_clicked = False   
    # event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        # taking keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                going_left = True
            if event.key == pygame.K_d:
                going_right = True
            if event.key == pygame.K_w:
                going_up = True
            if event.key == pygame.K_s:
               going_down = True
            if event.key == pygame.K_ESCAPE:
                pause_game = True
        # taking keyboard released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                going_left = False
            if event.key == pygame.K_d:
                going_right = False
            if event.key == pygame.K_w:
                going_up = False
            if event.key == pygame.K_s:
               going_down = False
    pygame.display.update()
pygame.quit()
