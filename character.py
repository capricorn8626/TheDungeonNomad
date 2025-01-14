import pygame
import constants
import math
import weapon 
class Character():
    def __init__(self,x,y,health, mob_anmations,char_type,boss,size):
        self.health = health
        self.boss = boss
        self.alive = True
        self.coin_score = 0
        self.char_type = char_type
        self.flip = False
        self.animation_list = mob_anmations[char_type]
        self.frame_index = 0
        self.running = False
        self.action =  0 #0:idle 1:run
        self.update_time = pygame.time.get_ticks()
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.last_attack = pygame.time.get_ticks()
        self.stunned = False
        self.rect = pygame.Rect(0,0,constants.TILE_SIZE*size,constants.TILE_SIZE*size)
        self.rect.center = (x,y)
        self.image = self.animation_list[self.action][self.frame_index]
    def move(self,dx,dy,obstacle_tiles,exit_tiles = None):
        screen_scroll = [0,0]
        level_complete = False
        self.running = False
        if dx != 0 or dy != 0:
            self.running = True
        if dx < 0:
            self.flip=True
        if dx > 0:
            self.flip=False
        if dx !=0 and dy!=0:
            dx = dx * (math.sqrt(2)/2)
            dy = dy * (math.sqrt(2)/2)
        # check collision with map with x direction
        self.rect.x += dx
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                # check which side the collision from
                if dx>0:
                    self.rect.right = obstacle[1].left
                if dx<0:
                    self.rect.left = obstacle[1].right
        # check collision with map with y direction
        self.rect.y += dy
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                # check which side the collision from
                if dy>0:
                    self.rect.bottom = obstacle[1].top
                if dy<0:
                    self.rect.top = obstacle[1].bottom
  
        # logic only applicable to player
        if self.char_type == 0:
            # check collision with exit door
            for exit in exit_tiles:
                if exit[1].colliderect(self.rect):
                    #ensure player close enough to exit
                    exit_dist = math.sqrt(((self.rect.centerx - exit[1].centerx) ** 2)+((self.rect.centery - exit[1].centery) **2 ))
                    if exit_dist < 20:
                        level_complete = True
            # update scroll based on player position
            # move camera left and right
            if self.rect.right > (constants.SCREEN_WIDTH - constants.SCROLL_THRESH):
                screen_scroll[0]= (constants.SCREEN_WIDTH - constants.SCROLL_THRESH) - self.rect.right
                self.rect.right = constants.SCREEN_WIDTH - constants.SCROLL_THRESH
            if self.rect.left < constants.SCROLL_THRESH:
                screen_scroll[0]= constants.SCROLL_THRESH - self.rect.left
                self.rect.left = constants.SCROLL_THRESH
            # move camera up and down
            if self.rect.bottom > (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH):
                screen_scroll[1]= (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH) - self.rect.bottom
                self.rect.bottom = constants.SCREEN_HEIGHT - constants.SCROLL_THRESH
            if self.rect.top < constants.SCROLL_THRESH:
                screen_scroll[1]= constants.SCROLL_THRESH - self.rect.top
                self.rect.top = constants.SCROLL_THRESH
        
        return screen_scroll,level_complete
    
    def ai(self,player,obstacle_tiles, screen_scroll,fireball_image):
        ai_dx =0
        ai_dy = 0
        fireball = None
        clipline = ()
        stun_cooldown = 100
        # reposition the mobs based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        line_of_sight = ((self.rect.centerx,self.rect.centery),(player.rect.centerx,player.rect.centery))
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                clipline = obstacle[1].clipline(line_of_sight)
        # check distance 
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx) ** 2)+((self.rect.centery - player.rect.centery) **2 ))
        if not clipline and dist > constants.RANGE:
            if self.rect.centerx > player.rect.centerx:
                ai_dx =-constants.ENEMY_SPEED
            if self.rect.centerx < player.rect.centerx:
                ai_dx =+constants.ENEMY_SPEED
            if self.rect.centery > player.rect.centery:
                ai_dy =-constants.ENEMY_SPEED
            if self.rect.centery < player.rect.centery:
                ai_dy =+constants.ENEMY_SPEED
        if self.alive:
            if not self.stunned:
                self.move(ai_dx,ai_dy,obstacle_tiles)
                # attack
                if dist < constants.ATTACK_RANGE and player.hit ==False:
                    player.health -=10
                    player.hit = True
                    player.last_hit = pygame.time.get_ticks()
                # boss attack
                fireball_cooldown = 700
                if self.boss:
                    if dist < 500:
                        if pygame.time.get_ticks() - self.last_attack >= fireball_cooldown:
                            fireball = weapon.Fireball(fireball_image,self.rect.centerx,self.rect.centery,player.rect.centerx,player.rect.centery)
                            self.last_attack = pygame.time.get_ticks()

            if self.hit ==  True:
                self.hit =False
                self.last_hit = pygame.time.get_ticks()
                self.stunned = True
                self.running = False
                self.update_action(0)
            if (pygame.time.get_ticks() - self.last_hit > stun_cooldown):
                self.stunned = False
        return fireball

    def update(self):
        # check if character has died
        if self.health <= 0:
            self.health = 0
            self.alive = False
        # reset hit_cooldown
        hit_cooldown = 1000
        if self.char_type == 0:
            if self.hit == True and (pygame.time.get_ticks()-self.last_hit > hit_cooldown):
                self.hit =False
                self.last_hit = pygame.time.get_ticks()
        # check if player running or idle
        if self.running == True:
            self.update_action(1)
        else:
            self.update_action(0)
        animation_cooldown = 70
        # handle animtion
        # image update
        self.image = self.animation_list[self.action][self.frame_index]
        # check if time enough to update next frame
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        # check if the animation had finished
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0
    def update_action(self,new_action):
        if self.action != new_action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
    def draw(self,surface):
        flipped_image = pygame.transform.flip(self.image,self.flip,False)
        if self.char_type == 0:
            surface.blit(flipped_image,(self.rect.x,self.rect.y - constants.OFFSETY*constants.SCALE))  
        else:
            surface.blit(flipped_image,self.rect)