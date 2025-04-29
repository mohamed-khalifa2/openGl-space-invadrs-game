import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import sys

# --- Constants ---
WIDTH, HEIGHT = 800, 600
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 30
BULLET_WIDTH, BULLET_HEIGHT = 5, 10
ENEMY_WIDTH, ENEMY_HEIGHT = 40, 30

PLAYER_SPEED = 6
BULLET_SPEED = 7
ENEMY_SPEED_X = 2
ENEMY_SPEED_Y = 20


FPS = 60
current_difficulty = 'Normal'
current_screen = 'menu'

# Game State
player = None
bullets = []
enemies = []
enemy_bullets = []
enemy_direction = ENEMY_SPEED_X
enemy_shoot_cooldown = 60
game_over = False
win = False
keys_held = {}

# --- Helper Functions ---

def load_texture(filename):
    surface = pygame.image.load(filename)
    surface = pygame.transform.flip(surface, False, True)
    image_data = pygame.image.tostring(surface, "RGBA", True)
    width, height = surface.get_size()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    return texture_id

def draw_text(x, y, text_string, size=32, color=(255, 255, 255)):
    font = pygame.font.SysFont("PixelifySans-Medium", size)
    text_surface = font.render(text_string, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_size()

    glEnable(GL_TEXTURE_2D)
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, y)
    glTexCoord2f(1, 0); glVertex2f(x + text_width, y)
    glTexCoord2f(1, 1); glVertex2f(x + text_width, y + text_height)
    glTexCoord2f(0, 1); glVertex2f(x, y + text_height)
    glEnd()

    glDeleteTextures(tex_id)
    glDisable(GL_TEXTURE_2D)

def draw_background():
    glClearColor(0, 0, 0.1, 1)
    glClear(GL_COLOR_BUFFER_BIT)

def draw_rect(x, y, w, h, color=(1,1,1)):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x+w, y)
    glVertex2f(x+w, y+h)
    glVertex2f(x, y+h)
    glEnd()

def draw_textured_rect(x, y, w, h, texture_id):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor3f(1,1,1)
    glBegin(GL_QUADS)
    glTexCoord2f(0,1); glVertex2f(x, y)
    glTexCoord2f(1,1); glVertex2f(x+w, y)
    glTexCoord2f(1,0); glVertex2f(x+w, y+h)
    glTexCoord2f(0,0); glVertex2f(x, y+h)
    glEnd()
    glDisable(GL_TEXTURE_2D)

# --- Classes ---

class Player:
    def __init__(self, texture_id):
        self.x = WIDTH//2 - PLAYER_WIDTH//2
        self.y = 50
        self.w = PLAYER_WIDTH
        self.h = PLAYER_HEIGHT
        self.texture_id = texture_id

    def move(self, dx):
        self.x += dx
        self.x = max(0, min(WIDTH-self.w, self.x))

    def draw(self):
        draw_textured_rect(self.x, self.y, self.w, self.h, self.texture_id)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = BULLET_WIDTH
        self.h = BULLET_HEIGHT

    def update(self):
        self.y += BULLET_SPEED

    def draw(self):
        draw_rect(self.x, self.y, self.w, self.h, (1,1,0))

class Enemy:
    def __init__(self, x, y, texture_id):
        self.x = x
        self.y = y
        self.w = ENEMY_WIDTH
        self.h = ENEMY_HEIGHT
        self.texture_id = texture_id

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def draw(self):
        draw_textured_rect(self.x, self.y, self.w, self.h, self.texture_id)

class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = BULLET_WIDTH
        self.h = BULLET_HEIGHT

    def update(self):
        self.y -= BULLET_SPEED

    def draw(self):
        draw_rect(self.x, self.y, self.w, self.h, (1, 0, 0))

# --- Game Functions ---

def init_game():
    global player, bullets, enemies, enemy_bullets, enemy_direction, enemy_shoot_cooldown, game_over, win
    player_texture = load_texture('assets/player.png')
    enemy_texture = load_texture('assets/enemy.png')
    player = Player(player_texture)
    bullets.clear()
    enemies.clear()
    enemy_bullets.clear()
    enemy_direction = ENEMY_SPEED_X

    if current_difficulty == 'Easy':
        min_cooldown, max_cooldown = 60, 120
    elif current_difficulty == 'Normal':
        min_cooldown, max_cooldown = 30, 90
    else:
        min_cooldown, max_cooldown = 15, 45

    enemy_shoot_cooldown = random.randint(min_cooldown, max_cooldown)

    for row in range(4):
        for col in range(7):
            enemies.append(Enemy(100 + col*80, HEIGHT-100 - row*60, enemy_texture))

    game_over = False
    win = False

def update(value):
    global enemy_direction, enemy_shoot_cooldown, game_over, win

    if not game_over:
        if keys_held.get(b'a') or keys_held.get(b'A') or keys_held.get(GLUT_KEY_LEFT):
            player.move(-PLAYER_SPEED)
        if keys_held.get(b'd') or keys_held.get(b'D') or keys_held.get(GLUT_KEY_RIGHT):
            player.move(PLAYER_SPEED)

        for b in bullets:
            b.update()
        for eb in enemy_bullets:
            eb.update()

        bullets[:] = [b for b in bullets if b.y < HEIGHT]
        enemy_bullets[:] = [eb for eb in enemy_bullets if eb.y > 0]

        move_down = False
        for e in enemies:
            e.move(enemy_direction, 0)
            if e.x <= 0 or e.x + e.w >= WIDTH:
                move_down = True

        if move_down:
            enemy_direction *= -1
            for e in enemies:
                e.move(enemy_direction, -ENEMY_SPEED_Y)

        enemy_shoot_cooldown -= 1
        if enemy_shoot_cooldown <= 0 and enemies:
            shooter = random.choice(enemies)
            enemy_bullets.append(EnemyBullet(shooter.x + shooter.w/2 - BULLET_WIDTH/2, shooter.y))
            reset_enemy_cooldown()

        # Check collisions
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                if (bullet.x < enemy.x+enemy.w and bullet.x+bullet.w > enemy.x and
                    bullet.y < enemy.y+enemy.h and bullet.y+bullet.h > enemy.y):
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    break

        for eb in enemy_bullets:
            if (eb.x < player.x + player.w and eb.x + eb.w > player.x and
                eb.y < player.y + player.h and eb.y + eb.h > player.y):
                game_over = True

        for e in enemies:
            if e.y <= player.y + player.h:
                game_over = True

        if not enemies:
            win = True
            game_over = True

    glutPostRedisplay()
    glutTimerFunc(int(1000/FPS), update, 0)

def reset_enemy_cooldown():
    global enemy_shoot_cooldown
    if current_difficulty == 'Easy':
        enemy_shoot_cooldown = random.randint(60, 120)
    elif current_difficulty == 'Normal':
        enemy_shoot_cooldown = random.randint(30, 90)
    else:
        enemy_shoot_cooldown = random.randint(15, 45)

def display():
    draw_background()

    if current_screen == 'menu':
        draw_text(WIDTH/2-150, HEIGHT/2+40, "SPACE INVADERS", size=48)
        draw_text(WIDTH/2-170, HEIGHT/2-20, "1-Easy2-Normal3-Hard", size=24)
    elif current_screen == 'playing':
        player.draw()
        for b in bullets:
            b.draw()
        for e in enemies:
            e.draw()
        for eb in enemy_bullets:
            eb.draw()

        if game_over:
            color = (0,255,0) if win else (255,0,0)
            draw_text(WIDTH/2-100, HEIGHT/2+40, "YOU WIN!" if win else "GAME OVER", size=48, color=color)
            draw_text(WIDTH/2-105, HEIGHT/2-20, "Press SPACE to Play Again", size=24)

    glutSwapBuffers()

def key_pressed(key, x, y):
    global keys_held, current_difficulty, current_screen

    if current_screen == 'menu':
        if key == b'1':
            current_difficulty = 'Easy'
            current_screen = 'playing'
            init_game()
        elif key == b'2':
            current_difficulty = 'Normal'
            current_screen = 'playing'
            init_game()
        elif key == b'3':
            current_difficulty = 'Hard'
            current_screen = 'playing'
            init_game()
    elif current_screen == 'playing':
        keys_held[key] = True

        if key == b' ':
            if game_over:
                init_game()
            else:
                # Fire bullet from center of player
                bullet_x = player.x + player.w // 2 - BULLET_WIDTH // 2
                bullet_y = player.y + player.h
                bullets.append(Bullet(bullet_x, bullet_y))

    if key == b'\x1b':  # ESC key
        sys.exit()

def key_released(key, x, y):
    global keys_held
    if key in keys_held:
        del keys_held[key]

def special_pressed(key, x, y):
    keys_held[key] = True

def special_released(key, x, y):
    if key in keys_held:
        del keys_held[key]

# --- Main Program ---

def main():
    pygame.init()
    pygame.display.set_mode((1,1), pygame.NOFRAME)
    pygame.font.init()
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"Space Invaders OpenGL GLUT")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    init_game()

    glutDisplayFunc(display)
    glutKeyboardFunc(key_pressed)
    glutKeyboardUpFunc(key_released)
    glutSpecialFunc(special_pressed)
    glutSpecialUpFunc(special_released)
    glutTimerFunc(int(1000/FPS), update, 0)

    glutMainLoop()

if __name__ == "__main__":
    main()
