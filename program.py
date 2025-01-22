import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Космические баталии")
clock = pygame.time.Clock()

player_img = pygame.image.load(r"player_ship.png")
asteroid_img = pygame.image.load(r"asteroid.png")
enemy_img = pygame.image.load(r"enemy_ship.png")
bonus_img = pygame.image.load(r"bonus.png")

player_img = pygame.transform.scale(player_img, (50, 50))
asteroid_img = pygame.transform.scale(asteroid_img, (40, 40))
enemy_img = pygame.transform.scale(enemy_img, (50, 50))
bonus_img = pygame.transform.scale(bonus_img, (30, 30))


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 60)
        self.health = 100
        self.speed = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_d] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_s] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)


class Asteroid(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = asteroid_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(-100, -40)
        self.speed = random.randint(3, 7)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.y = random.randint(-100, -40)
            self.rect.x = random.randint(0, WIDTH - self.rect.width)


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -40)
        self.speed = random.randint(4, 6)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.y = random.randint(-150, -40)
            self.rect.x = random.randint(0, WIDTH - self.rect.width)


class Bonus(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = bonus_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(-200, -50)
        self.speed = 2

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.y = random.randint(-200, -50)
            self.rect.x = random.randint(0, WIDTH - self.rect.width)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = -8

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


all_sprites = pygame.sprite.Group()
asteroids = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
bonuses = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

for _ in range(8):
    asteroid = Asteroid()
    all_sprites.add(asteroid)
    asteroids.add(asteroid)

for _ in range(3):
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

for _ in range(2):
    bonus = Bonus()
    all_sprites.add(bonus)
    bonuses.add(bonus)

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    all_sprites.update()

    if pygame.sprite.spritecollide(player, asteroids, True):
        player.health -= 20
        if player.health <= 0:
            running = False

    if pygame.sprite.spritecollide(player, enemies, True):
        player.health -= 30
        if player.health <= 0:
            running = False

    if pygame.sprite.spritecollide(player, bonuses, True):
        player.health = min(100, player.health + 10)

    for enemy in pygame.sprite.groupcollide(enemies, bullets, True, True):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    screen.fill(BLACK)
    all_sprites.draw(screen)

    pygame.draw.rect(screen, RED, (10, 10, 100, 20))
    pygame.draw.rect(screen, GREEN, (10, 10, player.health, 20))

    pygame.display.flip()

pygame.quit()
