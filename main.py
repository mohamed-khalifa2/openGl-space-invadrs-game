import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random  

# Constants
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

# --- Helpers ---
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
        self.x = WIDTH//2 - PLAYER_WIDTH//2 #X coords 
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
        draw_rect(self.x, self.y, self.w, self.h, (1, 0, 0))  # Red color for enemy bullets

# --- Game Functions ---

def main_game_loop():
    global current_difficulty
    clock = pygame.time.Clock()

    player_texture= load_texture('assets/player.png')
    enemy_texture= load_texture('assets/enemy.png')

    player = Player(player_texture)
    bullets = []
    enemies = []
    enemy_direction = ENEMY_SPEED_X

    enemy_bullets = []  
    if current_difficulty == 'Easy':
        min_cooldown, max_cooldown = 60, 120
    elif current_difficulty == 'Normal':
        min_cooldown, max_cooldown = 30, 90
    elif current_difficulty == 'Hard':
        min_cooldown, max_cooldown = 15, 45

    enemy_shoot_cooldown = random.randint(min_cooldown, max_cooldown)

    for row in range(4):
        for col in range(7):
            enemies.append(Enemy(100 + col*80, HEIGHT-100 - row*60, enemy_texture))

    running = True
    game_over = False
    win = False

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            player.move(-PLAYER_SPEED)
        if keys[K_RIGHT]:
            player.move(PLAYER_SPEED)
        if keys[K_SPACE]:
            if len(bullets)< 4:
                bullets.append(Bullet(player.x + player.w/2 - BULLET_WIDTH/2, player.y + player.h))

        if not game_over:
            for b in bullets:
                b.update()
            bullets = [b for b in bullets if b.y < HEIGHT]

            # Update enemy bullets
            for eb in enemy_bullets:
                eb.update()
            enemy_bullets = [eb for eb in enemy_bullets if eb.y > 0]

            move_down = False
            for e in enemies:
                e.move(enemy_direction, 0)
                if e.x <= 0 or e.x+e.w >= WIDTH:
                    move_down = True

            if move_down:
                enemy_direction *= -1
                for e in enemies:
                    e.move(enemy_direction, -ENEMY_SPEED_Y)

            # Enemy shooting logic
            enemy_shoot_cooldown -= 1
            if enemy_shoot_cooldown <= 0 and enemies:
                shooter = random.choice(enemies)
                enemy_bullets.append(EnemyBullet(shooter.x + shooter.w/2 - BULLET_WIDTH/2, shooter.y))
                enemy_shoot_cooldown = random.randint(min_cooldown, max_cooldown)

            # Bullet and enemy collision
            for bullet in bullets:
                for enemy in enemies:
                    if (bullet.x < enemy.x+enemy.w and bullet.x+bullet.w > enemy.x and
                        bullet.y < enemy.y+enemy.h and bullet.y+bullet.h > enemy.y):
                        try:
                            bullets.remove(bullet)
                            enemies.remove(enemy)
                        except:
                            pass
                        break

            # Enemy bullet hitting player
            for eb in enemy_bullets:
                if (eb.x < player.x + player.w and eb.x + eb.w > player.x and
                    eb.y < player.y + player.h and eb.y + eb.h > player.y):
                    game_over = True
                    break

            # Enemy reaching player
            for e in enemies:
                if e.y <= player.y+player.h:
                    game_over = True
                    break

            if not enemies:
                win = True
                game_over = True

        draw_background()

        player.draw()
        for b in bullets:
            b.draw()
        for e in enemies:
            e.draw()
        for eb in enemy_bullets:
            eb.draw()
        red = (255,0,0)
        green = (0,255,0)
        if game_over:
            if win:
                draw_text(WIDTH/2-100, HEIGHT/2+40, "YOU WIN!", size=48,color = green)
            else:
                draw_text(WIDTH/2-100, HEIGHT/2+40, "GAME OVER", size=48,color = red)

            draw_text(WIDTH/2-105, HEIGHT/2-20, "Press SPACE to Play Again", size=24)

            keys = pygame.key.get_pressed()
            if keys[K_SPACE]:
                main_game_loop() 
                return

        pygame.display.flip()

def difficulty_screen():
    global current_difficulty
    difficulties = ['Easy', 'Normal', 'Hard']
    selected = 1
    running = True
    while running:
        glClear(GL_COLOR_BUFFER_BIT)
        draw_background()
        draw_text(WIDTH/2-120, HEIGHT-100, "Select Difficulty", size=48)

        for i in range(len(difficulties)):
            color = (255,255,0) if selected == i else (255,255,255)
            draw_text(WIDTH/2-50, HEIGHT/2-40*(i+1), difficulties[i], size=32, color=color)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected-1)%3
                if event.key == K_DOWN:
                    selected = (selected+1)%3
                if event.key == K_RETURN:
                    current_difficulty = difficulties[selected]
                    running = False

def menu_screen():
    selected = 0
    running = True
    while running:
        glClear(GL_COLOR_BUFFER_BIT)
        draw_background()
        draw_text(WIDTH/2-120, HEIGHT-100, "SPACE INVADERS", size=48)

        color1 = (255,255,0) if selected==0 else (255,255,255)
        color2 = (255,255,0) if selected==1 else (255,255,255)
        draw_text(WIDTH/2-50, HEIGHT/2+30, "Start Game", size=32, color=color1)
        draw_text(WIDTH/2-60, HEIGHT/2-10, "Set Difficulty", size=32, color=color2)
        draw_text(WIDTH/2-53, HEIGHT/2-50, f"Current: {current_difficulty}", size=24)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected-1)%2
                if event.key == K_DOWN:
                    selected = (selected+1)%2
                if event.key == K_RETURN:
                    if selected == 0:
                        running = False
                        main_game_loop()
                    else:
                        difficulty_screen()

# --- Main Program ---

def main():
    pygame.init()
    glutInit()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Space Invaders OpenGL")
    pygame.font.init()
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    menu_screen()

if __name__ == "__main__":
    main()
