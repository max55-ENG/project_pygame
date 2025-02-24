import pygame
import random
import sys
import os
import time

pygame.init()


def load_image(name, color_key=None):
    fullname = os.path.join(r'C:\Users\ivan\PycharmProjects\project_pygame', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


SIZE = WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
LIGHT_BLUE = (100, 149, 237)
DARK_BLUE = (70, 130, 180)
GRAY = (128, 128, 128)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Космические баталии")
clock = pygame.time.Clock()

background = pygame.image.load("background.jpg")
player_img = pygame.image.load("player_ship.png")
asteroid_img = pygame.image.load("asteroid.png")
enemy_img = pygame.image.load("enemy_ship.png")
bonus_img = pygame.image.load("bonus.png")

player_img = pygame.transform.scale(player_img, (50, 50))
asteroid_img = pygame.transform.scale(asteroid_img, (40, 40))
enemy_img = pygame.transform.scale(enemy_img, (50, 50))
bonus_img = pygame.transform.scale(bonus_img, (30, 30))

shoot_sound = pygame.mixer.Sound("shoot.mp3")
explosion_sound = pygame.mixer.Sound("explosion.mp3")
pygame.mixer.music.load("background_music.mp3")

# Параметры уровней
levels = {
    1: {'speed_min_a': 3, 'speed_max_a': 7, 'speed_min_e': 4, 'speed_max_e': 6,
        'hp': 20, 'asteroid_score': 5, 'enemy_score': 10},
    2: {'speed_min_a': 4, 'speed_max_a': 8, 'speed_min_e': 5, 'speed_max_e': 7,
        'hp': 35, 'asteroid_score': 7, 'enemy_score': 15},
    3: {'speed_min_a': 5, 'speed_max_a': 9, 'speed_min_e': 6, 'speed_max_e': 8,
        'hp': 45, 'asteroid_score': 10, 'enemy_score': 20},
    4: {'speed_min_a': 6, 'speed_max_a': 10, 'speed_min_e': 7, 'speed_max_e': 9,
        'hp': 55, 'asteroid_score': 12, 'enemy_score': 25},
    5: {'speed_min_a': 7, 'speed_max_a': 11, 'speed_min_e': 8, 'speed_max_e': 10,
        'hp': 65, 'asteroid_score': 15, 'enemy_score': 30, 'infinite': True},
}

upgrades = {
    'speed': {'level': 0, 'cost': 120, 'max_level': 5},
    'health': {'level': 0, 'cost': 160, 'max_level': 5},
    'damage': {'level': 0, 'cost': 180, 'max_level': 5}
}

unlocked_levels = 1
stars = 0
current_user = None
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(1)


class Player(pygame.sprite.Sprite):
    def __init__(self, current_level=1):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 60)
        self.max_health = 100 + 10 * upgrades['health']['level']
        self.health = self.max_health
        self.speed = 5 + upgrades['speed']['level']
        self.score = 0
        self.current_level = current_level
        self.asteroids_destroyed = 0
        self.enemies_destroyed = 0

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
        shoot_sound.play()


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, speed_min, speed_max):
        super().__init__()
        self.image = asteroid_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(-100, -40)
        self.speed = random.randint(speed_min, speed_max)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
            spawn_asteroid()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed_min, speed_max, hp, player_ref):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -40)
        self.speed = random.randint(speed_min, speed_max)
        self.health = hp
        self.max_health = hp
        self.player = player_ref

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
            spawn_enemy()

    def take_damage(self):
        self.health -= Bullet.damage
        if self.health <= 0:
            score = levels[self.player.current_level]['enemy_score']
            self.player.score += score
            self.player.enemies_destroyed += 1
            self.kill()
            spawn_enemy()

    def draw_health_bar(self, surface):
        bar_width = 50
        bar_height = 5
        health_percentage = self.health / self.max_health
        pygame.draw.rect(surface, RED, (self.rect.centerx - bar_width // 2, self.rect.top - 10, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (
            self.rect.centerx - bar_width // 2, self.rect.top - 10, bar_width * health_percentage, bar_height))


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
            self.kill()


class Bullet(pygame.sprite.Sprite):
    damage = 15

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


all_sprites = pygame.sprite.Group()
asteroids = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
bonuses = pygame.sprite.Group()


def spawn_asteroid():
    level_params = levels[current_level]
    asteroid = Asteroid(level_params['speed_min_a'], level_params['speed_max_a'])
    all_sprites.add(asteroid)
    asteroids.add(asteroid)


def spawn_enemy():
    level_params = levels[current_level]
    enemy = Enemy(
        level_params['speed_min_e'],
        level_params['speed_max_e'],
        level_params['hp'],
        player
    )
    all_sprites.add(enemy)
    enemies.add(enemy)


def spawn_bonus():
    bonus = Bonus()
    all_sprites.add(bonus)
    bonuses.add(bonus)


def draw_button(text, x, y, width, height, color, hover_color):
    font = pygame.font.Font(None, 50)
    button_rect = pygame.Rect(x, y, width, height)
    mouse_pos = pygame.mouse.get_pos()

    if button_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, button_rect)
    else:
        pygame.draw.rect(screen, color, button_rect)

    pygame.draw.rect(screen, BLACK, button_rect, 2)

    label = font.render(text, True, WHITE)
    screen.blit(label, (button_rect.x + (button_rect.width - label.get_width()) // 2,
                        button_rect.y + (button_rect.height - label.get_height()) // 2))

    return button_rect


def level_select_screen():
    global unlocked_levels, current_level
    running = True
    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        buttons = []
        y_offset = HEIGHT // 2 - 150
        for level in range(1, 6):
            if level <= unlocked_levels:
                color = LIGHT_BLUE
                hover_color = DARK_BLUE
            else:
                color = GRAY
                hover_color = GRAY
            btn = draw_button(f"Уровень {level}", WIDTH // 2 - 100, y_offset, 200, 50, color, hover_color)
            buttons.append((btn, level))
            y_offset += 70

        back_button = draw_button("Назад", 30, 30, 150, 50, LIGHT_BLUE, DARK_BLUE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    main_menu()
                    return
                for btn, level in buttons:
                    if btn.collidepoint(pygame.mouse.get_pos()) and level <= unlocked_levels:
                        current_level = level
                        game_screen(level)
                        running = False
                        break


def game_screen(level):
    global unlocked_levels, player
    player = Player(current_level=level)
    player.score = 0
    all_sprites.empty()
    asteroids.empty()
    enemies.empty()
    bullets.empty()
    bonuses.empty()
    pygame.mixer.music.play(-1)

    all_sprites.add(player)
    level_params = levels[level]

    game_duration = 90 if level != 5 else float('inf')
    infinite_mode = level == 5

    for _ in range(8):
        spawn_asteroid()
    for _ in range(3):
        spawn_enemy()
    for _ in range(2):
        spawn_bonus()

    start_time = time.time()
    running = True
    hp_lvl = player.health
    flag_bonus = True

    while running:
        clock.tick(FPS)
        elapsed_time = time.time() - start_time
        if not infinite_mode:
            remaining_time = max(0, game_duration - int(elapsed_time))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()

        all_sprites.update()

        if pygame.sprite.spritecollide(player, asteroids, True):
            spawn_asteroid()
            player.health -= 20
            explosion_sound.play()
            if player.health <= 0 and not infinite_mode:
                show_results(player, remaining_time, False, level)
                running = False
            if player.health <= 30:
                spawn_bonus()

        if int(elapsed_time) == 45 and flag_bonus:
            spawn_bonus()
            flag_bonus = False

        if pygame.sprite.spritecollide(player, enemies, True):
            spawn_enemy()
            player.health -= 30
            explosion_sound.play()
            if player.health <= 0 and not infinite_mode:
                show_results(player, remaining_time, False, level)
                running = False
            if player.health <= 30:
                spawn_bonus()

        for asteroid in pygame.sprite.groupcollide(asteroids, bullets, True, True):
            spawn_asteroid()
            score = levels[player.current_level]['asteroid_score']
            player.score += score
            player.asteroids_destroyed += 1

        if pygame.sprite.spritecollide(player, bonuses, True):
            player.health = min(hp_lvl, player.health + 10)

        for bullet in bullets:
            for enemy in enemies:
                if bullet.rect.colliderect(enemy.rect):
                    enemy.take_damage()
                    bullet.kill()
                    break

        screen.blit(background, (0, 0))
        all_sprites.draw(screen)

        for enemy in enemies:
            enemy.draw_health_bar(screen)

        pygame.draw.rect(screen, RED, (10, 10, hp_lvl, 20))
        pygame.draw.rect(screen, GREEN, (10, 10, player.health, 20))
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Монеты: {player.score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 150, 10))

        if infinite_mode:
            timer_text = font.render(f"Время: {int(elapsed_time)}", True, WHITE)
        else:
            timer_text = font.render(f"Время: {remaining_time}", True, WHITE)
        screen.blit(timer_text, (WIDTH // 2 - 50, 10))

        pygame.display.flip()

        if not infinite_mode and remaining_time <= 0:
            show_results(player, elapsed_time, True, level)
            running = False
        elif infinite_mode and player.health <= 0:
            show_results(player, elapsed_time, False, level)
            running = False


def show_results(player, elapsed_time, survived, level):
    global unlocked_levels, stars
    if survived and level != 5:  # Для обычных уровней
        stars += player.score
    running = True

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        font = pygame.font.SysFont(None, 50)
        title_font = pygame.font.SysFont(None, 70)

        # Заголовок в зависимости от результата
        if survived:
            title_text = title_font.render("Победа!", True, GREEN)
            if level == unlocked_levels and level != 5:
                unlocked_levels = min(unlocked_levels + 1, 5)
        else:
            title_text = title_font.render("Поражение", True, RED)

        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

        # Формирование статистики
        results = [
            f"Уничтожено астероидов: {player.asteroids_destroyed}",
            f"Уничтожено врагов: {player.enemies_destroyed}",
            f"Время: {int(elapsed_time)} сек" if level == 5 else f"Осталось времени: {int(elapsed_time)} сек",
            f"Монеты: {player.score}",
        ]

        #рекорд для 5 уровня
        if level == 5:
            results.insert(2, f"Рекорд: {load_high_score()} сек")

        y_offset = 150
        for result in results:
            result_text = font.render(result, True, WHITE)
            screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, y_offset))
            y_offset += 50

        back_button = draw_button("Назад", WIDTH // 2 - 75, y_offset + 50, 150, 50, LIGHT_BLUE, DARK_BLUE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    running = False

    if level == 5 and current_user:
        update_highscore(current_user, int(elapsed_time))
    elif level == 5 and not current_user:
        ask_register = True
        while ask_register:
            fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
            screen.blit(fon, (0, 0))

            text = font.render("Хотите сохранить рекорд?", True, WHITE)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 200))

            yes_btn = draw_button("Да", WIDTH // 2 - 120, 300, 100, 50, LIGHT_BLUE, DARK_BLUE)
            no_btn = draw_button("Нет", WIDTH // 2 + 20, 300, 100, 50, LIGHT_BLUE, DARK_BLUE)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_btn.collidepoint(pygame.mouse.get_pos()):
                        login_screen()
                        if current_user:
                            update_highscore(current_user, int(elapsed_time))
                        ask_register = False
                    elif no_btn.collidepoint(pygame.mouse.get_pos()):
                        ask_register = False
    main_menu()


def load_high_score():
    try:
        with open("accounts.txt", "r") as f:
            rec = sorted([i.strip().split(":") for i in f.readlines()], key=lambda x: int(x[2]), reverse=True)
            return rec[0][2]
    except FileNotFoundError:
        return "0"


def shop_screen():
    global stars, upgrades
    running = True
    font = pygame.font.Font(None, 40)

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))
        title = font.render("Магазин улучшений", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        ship_image = pygame.transform.scale(player_img, (100, 100))
        screen.blit(ship_image, (50, HEIGHT // 2 - 50))

        # Кнопка скорости
        speed_level = upgrades['speed']['level']
        speed_cost = upgrades['speed']['cost']
        speed_color = LIGHT_BLUE if speed_level < 5 and stars >= speed_cost else GRAY
        speed_button = draw_button(f"Скорость {speed_level + 1} ({speed_cost})",
                                   WIDTH // 2 - 175, 150, 350, 50, speed_color, DARK_BLUE)
        if speed_level >= 5:
            max_text = font.render("MAX", True, RED)
            screen.blit(max_text, (WIDTH // 2 + 180, 165))

        # Кнопка здоровья
        health_level = upgrades['health']['level']
        health_cost = upgrades['health']['cost']
        health_color = LIGHT_BLUE if health_level < 5 and stars >= health_cost else GRAY
        health_button = draw_button(f"Здоровье {health_level + 1} ({health_cost})",
                                    WIDTH // 2 - 175, 220, 350, 50, health_color, DARK_BLUE)
        if health_level >= 5:
            max_text = font.render("MAX", True, RED)
            screen.blit(max_text, (WIDTH // 2 + 180, 235))

        # Кнопка урона
        damage_level = upgrades['damage']['level']
        damage_cost = upgrades['damage']['cost']
        damage_color = LIGHT_BLUE if damage_level < 5 and stars >= damage_cost else GRAY
        damage_button = draw_button(f"Урон {damage_level + 1} ({damage_cost})",
                                    WIDTH // 2 - 175, 290, 350, 50, damage_color, DARK_BLUE)
        if damage_level >= 5:
            max_text = font.render("MAX", True, RED)
            screen.blit(max_text, (WIDTH // 2 + 180, 305))

        back_button = draw_button("Назад", WIDTH // 2 - 75, 400, 150, 50, LIGHT_BLUE, DARK_BLUE)

        score_text = font.render(f"Ваши монеты: {stars}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 500))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    running = False
                elif speed_button.collidepoint(pygame.mouse.get_pos()) and speed_level < 5 and stars >= speed_cost:
                    stars -= speed_cost
                    upgrades['speed']['level'] += 1
                    upgrades['speed']['cost'] += 50
                    player.speed += 1
                elif health_button.collidepoint(pygame.mouse.get_pos()) and health_level < 5 and stars >= health_cost:
                    stars -= health_cost
                    upgrades['health']['level'] += 1
                    upgrades['health']['cost'] += 50
                    player.max_health += 10
                    player.health = player.max_health
                elif damage_button.collidepoint(pygame.mouse.get_pos()) and damage_level < 5 and stars >= damage_cost:
                    stars -= damage_cost
                    upgrades['damage']['level'] += 1
                    upgrades['damage']['cost'] += 50
                    Bullet.damage += 3


def main_menu():
    global current_user
    running = True
    font = pygame.font.Font(None, 40)
    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        # Кнопка входа пользователя
        if current_user:
            user_nik = pygame.draw.rect(screen, LIGHT_BLUE, (WIDTH - 180, 20, 160, 40))
            label_us = font.render(current_user, True, WHITE)
            screen.blit(label_us, (user_nik.x + (user_nik.width - label_us.get_width()) // 2,
                                   user_nik.y + (user_nik.height - label_us.get_height()) // 2))

            with open("accounts.txt", "r") as f:
                rec = [i.strip().split(":") for i in f.readlines() if i.split(':')[0] == current_user][0][2]
            label_rec = font.render(f"Ваш рекорд - {rec} сек", True, WHITE)
            user_rec = pygame.draw.rect(screen, LIGHT_BLUE, (50, 50, 300, 40))
            screen.blit(label_rec, (user_rec.x + (user_rec.width - label_rec.get_width()) // 2,
                                    user_rec.y + (user_rec.height - label_rec.get_height()) // 2))

            user_button = draw_button("Выйти", WIDTH - 180, 70, 160, 40, LIGHT_BLUE, DARK_BLUE)
        else:
            user_button = draw_button("Войти", WIDTH - 180, 20, 160, 40, LIGHT_BLUE, DARK_BLUE)

        # кнопки главного меню
        play_button = draw_button("Играть", WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50, LIGHT_BLUE, DARK_BLUE)
        shop_button = draw_button("Магазин", WIDTH // 2 - 100, HEIGHT // 2, 200, 50, LIGHT_BLUE, DARK_BLUE)
        settings_button = draw_button("Настройки", WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50, LIGHT_BLUE, DARK_BLUE)
        records_button = draw_button("Рекорды", WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50, LIGHT_BLUE, DARK_BLUE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if user_button.collidepoint(pygame.mouse.get_pos()):
                    if not current_user:
                        login_screen()
                    else:
                        current_user = None
                elif play_button.collidepoint(pygame.mouse.get_pos()):
                    level_select_screen()
                elif shop_button.collidepoint(pygame.mouse.get_pos()):
                    shop_screen()
                elif settings_button.collidepoint(pygame.mouse.get_pos()):
                    settings_screen()
                elif records_button.collidepoint(pygame.mouse.get_pos()):
                    records_screen()


def settings_screen():
    global music_volume, sound_volume
    running = True
    font = pygame.font.Font(None, 40)

    # Начальные значения громкости
    music_volume = pygame.mixer.music.get_volume()
    sound_volume = shoot_sound.get_volume()

    # Позиции
    music_slider_x = WIDTH // 2 - 100
    sound_slider_x = WIDTH // 2 - 100
    slider_y = 150
    slider_width = 200
    slider_height = 20

    music_slider_active = False
    sound_slider_active = False

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))
        title = font.render("Настройки", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        # Отображение слайдера для музыки
        music_text = font.render(f"Громкость музыки: {int(music_volume * 100)}%", True, WHITE)
        screen.blit(music_text, (WIDTH // 2 - music_text.get_width() // 2, 100))
        pygame.draw.rect(screen, WHITE, (music_slider_x, slider_y, slider_width, slider_height))
        pygame.draw.rect(screen, LIGHT_BLUE,
                         (music_slider_x, slider_y, int(music_volume * slider_width), slider_height))

        # Отображение слайдера для звуковых эффектов
        sound_text = font.render(f"Громкость звуков: {int(sound_volume * 100)}%", True, WHITE)
        screen.blit(sound_text, (WIDTH // 2 - sound_text.get_width() // 2, 200))
        pygame.draw.rect(screen, WHITE, (sound_slider_x, slider_y + 100, slider_width, slider_height))
        pygame.draw.rect(screen, LIGHT_BLUE,
                         (sound_slider_x, slider_y + 100, int(sound_volume * slider_width), slider_height))

        # Кнопка назад
        back_button = draw_button("Назад", WIDTH // 2 - 75, 400, 150, 50, LIGHT_BLUE, DARK_BLUE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    running = False
                # Проверка, нажата ли кнопка мыши на слайдере музыки
                if music_slider_x <= pygame.mouse.get_pos()[0] <= music_slider_x + slider_width and slider_y <= \
                        pygame.mouse.get_pos()[1] <= slider_y + slider_height:
                    music_slider_active = True
                # Проверка, нажата ли кнопка мыши на слайдере звуковых эффектов
                if sound_slider_x <= pygame.mouse.get_pos()[0] <= sound_slider_x + slider_width and slider_y + 100 <= \
                        pygame.mouse.get_pos()[1] <= slider_y + 100 + slider_height:
                    sound_slider_active = True
            elif event.type == pygame.MOUSEBUTTONUP:
                # Отпускание кнопки мыши деактивирует слайдеры
                music_slider_active = False
                sound_slider_active = False
            elif event.type == pygame.MOUSEMOTION:
                if music_slider_active:
                    mouse_x = pygame.mouse.get_pos()[0]
                    music_volume = (mouse_x - music_slider_x) / slider_width
                    music_volume = max(0, min(1, music_volume))
                    pygame.mixer.music.set_volume(music_volume)
                if sound_slider_active:
                    mouse_x = pygame.mouse.get_pos()[0]
                    sound_volume = (mouse_x - sound_slider_x) / slider_width
                    sound_volume = max(0, min(1, sound_volume))
                    shoot_sound.set_volume(sound_volume)
                    explosion_sound.set_volume(sound_volume)


def load_accounts():
    try:
        with open("accounts.txt", "r") as f:
            return [line.strip().split(":") for line in f.readlines()]
    except FileNotFoundError:
        return []


def save_account(login, password, highscore=0):
    with open("accounts.txt", "a") as f:
        f.write(f"{login}:{password}:{highscore}\n")


def update_highscore(login, new_score):
    accounts = load_accounts()
    updated = False
    for i, acc in enumerate(accounts):
        if acc[0] == login:
            if int(acc[2]) < new_score:
                accounts[i][2] = str(new_score)
                updated = True
            break
    if updated:
        with open("accounts.txt", "w") as f:
            for acc in accounts:
                f.write(f"{':'.join(acc)}\n")


def get_highscores():
    accounts = load_accounts()
    return sorted([(acc[0], int(acc[2])) for acc in accounts], key=lambda x: -x[1])


def login_screen():
    global current_user
    login = ""
    password = ""
    error_msg = ""
    input_mode = "login"  # login/password
    running = True
    font = pygame.font.Font(None, 40)

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        # Текстовые поля
        login_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 150, 300, 50))

        password_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 90, 300, 50))

        label = font.render(login, True, BLACK)
        label_p = font.render(password, True, BLACK)
        screen.blit(label, (login_rect.x + (login_rect.width - label.get_width()) // 2,
                            login_rect.y + (login_rect.height - label.get_height()) // 2))

        screen.blit(label_p, (password_rect.x + (password_rect.width - label_p.get_width()) // 2,
                              password_rect.y + (password_rect.height - label_p.get_height()) // 2))

        # Кнопки
        login_btn = draw_button("Вход", WIDTH // 2 - 125, 300, 250, 50, LIGHT_BLUE, DARK_BLUE)
        register_btn = draw_button("Регистрация", WIDTH // 2 - 125, 370, 250, 50, LIGHT_BLUE, DARK_BLUE)
        back_btn = draw_button("Назад", WIDTH // 2 - 125, 440, 250, 50, LIGHT_BLUE, DARK_BLUE)

        # Ошибки
        error_text = font.render(error_msg, True, RED)
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, 500))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if login_rect.collidepoint(pygame.mouse.get_pos()):
                    input_mode = "login"
                elif password_rect.collidepoint(pygame.mouse.get_pos()):
                    input_mode = "password"
                elif login_btn.collidepoint(pygame.mouse.get_pos()):
                    accounts = load_accounts()
                    for acc in accounts:
                        if acc[0] == login and acc[1] == password:
                            current_user = login
                            running = False
                            break
                    else:
                        error_msg = "Неверный логин или пароль!"
                elif register_btn.collidepoint(pygame.mouse.get_pos()):
                    registration_screen(login, password)
                    running = False
                elif back_btn.collidepoint(pygame.mouse.get_pos()):
                    running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if input_mode == "login" and len(login) > 0:
                        login = login[:-1]
                    elif input_mode == "password" and len(password) > 0:
                        password = password[:-1]
                else:
                    char = event.unicode
                    if input_mode == "login":
                        login += char
                    elif input_mode == "password":
                        password += char


def registration_screen(login, password):
    global current_user
    login = ""
    password = ""
    confirm = ""
    error_msg = ""
    input_mode = "login"
    running = True
    font = pygame.font.Font(None, 40)

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        login_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 210, 300, 50))

        password_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 150, 300, 50))

        confirm_rect = pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 90, 300, 50))

        label = font.render(login, True, BLACK)
        label_p = font.render(password, True, BLACK)
        label_pp = font.render(confirm, True, BLACK)
        screen.blit(label, (login_rect.x + (login_rect.width - label.get_width()) // 2,
                            login_rect.y + (login_rect.height - label.get_height()) // 2))

        screen.blit(label_p, (password_rect.x + (password_rect.width - label_p.get_width()) // 2,
                              password_rect.y + (password_rect.height - label_p.get_height()) // 2))

        screen.blit(label_pp, (confirm_rect.x + (confirm_rect.width - label_pp.get_width()) // 2,
                               confirm_rect.y + (confirm_rect.height - label_pp.get_height()) // 2))

        # Кнопки
        register_btn = draw_button("Создать", WIDTH // 2 - 100, 360, 200, 50, LIGHT_BLUE, DARK_BLUE)
        back_btn = draw_button("Назад", WIDTH // 2 - 100, 430, 200, 50, LIGHT_BLUE, DARK_BLUE)

        # Ошибки
        error_text = font.render(error_msg, True, RED)
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, 500))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if login_rect.collidepoint(pygame.mouse.get_pos()):
                    input_mode = "login"
                elif password_rect.collidepoint(pygame.mouse.get_pos()):
                    input_mode = "password"
                elif confirm_rect.collidepoint(pygame.mouse.get_pos()):
                    input_mode = "confirm"
                elif register_btn.collidepoint(pygame.mouse.get_pos()):
                    if password != confirm:
                        error_msg = "Пароли не совпадают!"
                    elif len(login) < 3:
                        error_msg = "Логин слишком короткий!"
                    elif any(acc[0] == login for acc in load_accounts()):
                        error_msg = "Логин уже занят!"
                    else:
                        save_account(login, password)
                        current_user = login
                        running = False
                elif back_btn.collidepoint(pygame.mouse.get_pos()):
                    running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if input_mode == "login":
                        login = login[:-1]
                    elif input_mode == "password":
                        password = password[:-1]
                    elif input_mode == "confirm":
                        confirm = confirm[:-1]
                else:
                    char = event.unicode
                    if input_mode == "login":
                        login += char
                    elif input_mode == "password":
                        password += char
                    elif input_mode == "confirm":
                        confirm += char


def records_screen():
    running = True
    font = pygame.font.Font(None, 40)
    highscores = get_highscores()

    while running:
        fon = pygame.transform.scale(load_image("background.jpg"), SIZE)
        screen.blit(fon, (0, 0))

        title = font.render("Таблица рекордов", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        y = 150
        count = 0
        for i, (user, score) in enumerate(highscores[:10]):
            text = font.render(f"{i + 1}. {user}: {score} сек", True, WHITE)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
            y += 50
            count += 1
            if count == 5:
                break

        back_btn = draw_button("Назад", WIDTH // 2 - 75, y + 50, 150, 50, LIGHT_BLUE, DARK_BLUE)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(pygame.mouse.get_pos()):
                    running = False


if __name__ == "__main__":
    main_menu()
