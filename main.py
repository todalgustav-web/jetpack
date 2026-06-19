import pygame
import random
import sys
import json
import os
import math

# Initialize Pygame
pygame.init()

# --- CONSTANTS & CONFIG ---
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
SAVE_FILE = "save_data.json"

# Color Palette
WHITE = (255, 255, 255)
BG_TOP = (12, 18, 30)      
BG_BOTTOM = (35, 48, 70)   
FLOOR_COLOR = (20, 24, 32)
ZAPPER_YELLOW = (255, 240, 100)
ZAPPER_ORANGE = (255, 140, 0)
COIN_GOLD = (255, 215, 0)
COIN_SHINE = (255, 255, 200)

# LEVEL DEFINITIONS
LEVELS_DATA = {
    1: {"target_distance": 300, "base_speed": 11.0, "spawn_rate": 140, "name": "Sector 1: Takeoff"},
    2: {"target_distance": 500, "base_speed": 13.0, "spawn_rate": 120, "name": "Sector 2: Electro-Lab"},
    3: {"target_distance": 750, "base_speed": 15.5, "spawn_rate": 100, "name": "Sector 3: Thermal Core"},
    4: {"target_distance": 1000, "base_speed": 18.0, "spawn_rate": 85, "name": "Sector 4: Neon Station"},
    5: {"target_distance": 1500, "base_speed": 21.0, "spawn_rate": 70, "name": "Sector 5: Hyperdrive Void"}
}

def load_game_data():
    defaults = {
        "total_coins": 0,
        "max_fps": 60,
        "unlocked_level": 1,  
        "booster_unlocked": False,
        "magnet_unlocked": False,
        "shield_unlocked": False,
        "fuel_unlocked": False,
        "gravity_unlocked": False,
        "unlocked_skins": ["cyan"],  
        "equipped_skin": "cyan",
        "unlocked_textures": ["none"], 
        "equipped_texture": "none"     
    }
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as file:
                data = json.load(file)
                for key in defaults:
                    if key not in data:
                        data[key] = defaults[key]
                return data
        except (json.JSONDecodeError, KeyError):
            return defaults
    return defaults

def save_game_data(config_dict):
    with open(SAVE_FILE, "w") as file:
        json.dump(config_dict, file)

def draw_background_gradient(surface, top_color, bottom_color):
    width, height = surface.get_size()
    for y in range(height):
        t = y / height
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

# --- CLASSES ---

class Particle:
    def __init__(self, x, y, is_victory=False):
        self.x = x + random.randint(-10, 10)
        self.y = y
        if is_victory:
            self.vx = random.uniform(-10, 10) * 60
            self.vy = random.uniform(-15, -5) * 60
            self.lifetime = random.uniform(1.0, 2.0)
            self.color = random.choice([(255, 50, 50), (50, 255, 50), (50, 100, 255), (255, 215, 0)])
            self.radius = random.randint(8, 16)
        else:
            self.vx = random.uniform(-6, -2) * 60
            self.vy = random.uniform(4, 12) * 60
            self.lifetime = random.uniform(0.15, 0.35)
            self.color = random.choice([(255, 90, 0), (255, 200, 0), (255, 255, 255)])
            self.radius = random.randint(6, 12)

    def update(self, dt, slow_grav=False):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if slow_grav:
            self.vy += 400 * dt  
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

class Player:
    def __init__(self):
        self.width = 81    
        self.height = 108  
        self.has_shield = False
        self.texture_anim_tick = 0.0
        self.reset()
        
    def reset(self):
        self.x = 225
        self.y = BASE_HEIGHT // 2
        self.velocity = 0
        
    def update(self, is_flying, dt, particles, upgrades, state_frozen=False):
        self.texture_anim_tick += dt
        if state_frozen:
            self.x += 350 * dt
            self.velocity = 0
            return

        fly_speed = -4525 if upgrades["fuel_unlocked"] else -3935
        gravity_pull = 3365 if upgrades["gravity_unlocked"] else 2925
        
        if is_flying:
            self.velocity += fly_speed * dt
            if self.velocity < -1125: self.velocity = -1125
            if random.random() < 0.6: 
                particles.append(Particle(self.x + 10, self.y + self.height - 20))
        else:
            self.velocity += gravity_pull * dt
            if self.velocity > 1395: self.velocity = 1395
                
        self.y += self.velocity * dt
        
        if self.y > BASE_HEIGHT - self.height - 90:
            self.y = BASE_HEIGHT - self.height - 90
            self.velocity = 0
        elif self.y < 0:
            self.y = 0
            self.velocity = 0

    def draw(self, surface, skin_style, texture_style):
        if skin_style == "gold": base_color, glow_color, visor_color = (255, 215, 0), (200, 140, 0), WHITE
        elif skin_style == "ruby": base_color, glow_color, visor_color = (220, 20, 60), (130, 0, 30), WHITE
        elif skin_style == "emerald": base_color, glow_color, visor_color = (46, 204, 113), (27, 120, 65), WHITE
        elif skin_style == "shadow": base_color, glow_color, visor_color = (25, 25, 25), (5, 5, 5), (255, 240, 150)
        else: base_color, glow_color, visor_color = (0, 235, 255), (0, 100, 255), WHITE

        if self.has_shield:
            pygame.draw.rect(surface, (255, 255, 255), (self.x - 18, self.y - 18, self.width + 36, self.height + 36), width=4, border_radius=18)
            pygame.draw.rect(surface, (0, 180, 255), (self.x - 14, self.y - 14, self.width + 28, self.height + 28), width=2, border_radius=14)

        pygame.draw.rect(surface, glow_color, (self.x - 8, self.y - 8, self.width + 16, self.height + 16), border_radius=12)
        
        char_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(char_surf, base_color, (0, 0, self.width, self.height), border_radius=8)

        if texture_style == "tiger":
            for i in range(-2, 8):
                offset = i * 25
                pygame.draw.line(char_surf, (15, 15, 15), (-10, offset), (self.width + 10, offset - 25), width=7)
        elif texture_style == "camo":
            for gx in range(0, self.width, 16):
                for gy in range(0, self.height, 16):
                    if (gx // 16 + gy // 16) % 3 == 0:
                        pygame.draw.rect(char_surf, (40, 55, 45, 160), (gx, gy, 16, 16))
        elif texture_style == "zebra":
            shift = int((self.texture_anim_tick * 80) % 40)
            for lx in range(-40, self.width + 40, 20):
                pygame.draw.line(char_surf, (240, 240, 240), (lx + shift, 0), (lx + shift - 30, self.height), width=6)
        elif texture_style == "circuit":
            pygame.draw.line(char_surf, (0, 255, 110), (15, 10), (15, 90), width=3)
            pygame.draw.line(char_surf, (0, 255, 110), (15, 45), (65, 45), width=3)
            pygame.draw.line(char_surf, (0, 255, 110), (50, 20), (50, 75), width=3)
            pygame.draw.circle(char_surf, WHITE, (15, 10), 5)
            pygame.draw.circle(char_surf, WHITE, (50, 75), 5)
            pygame.draw.circle(char_surf, WHITE, (65, 45), 5)

        surface.blit(char_surf, (self.x, self.y))
        pygame.draw.rect(surface, visor_color, (self.x + 40, self.y + 18, 30, 22), border_radius=4)

class Zapper:
    def __init__(self, speed):
        self.speed = speed * 60
        self.x = BASE_WIDTH + 100
        self.orientation = random.choice(["vertical", "horizontal"])
        self.pulse_timer = 0
        
        if self.orientation == "vertical":
            self.width = 45
            self.height = random.randint(270, 450)
        else:
            self.width = random.randint(315, 600)
            self.height = 45
            
        self.y = random.randint(20, BASE_HEIGHT - self.height - 110)

    def update(self, dt):
        self.x -= self.speed * dt
        self.pulse_timer += dt * 12

    def draw(self, surface):
        pulse_val = (math.sin(self.pulse_timer) + 1) / 2
        core_color = (
            int(ZAPPER_YELLOW[0] * pulse_val + WHITE[0] * (1 - pulse_val)),
            int(ZAPPER_YELLOW[1] * pulse_val + WHITE[1] * (1 - pulse_val)),
            int(ZAPPER_YELLOW[2] * pulse_val + WHITE[2] * (1 - pulse_val))
        )
        pygame.draw.rect(surface, ZAPPER_ORANGE, (self.x, self.y, self.width, self.height), border_radius=8)
        pygame.draw.rect(surface, core_color, (self.x + 6, self.y + 6, self.width - 12, self.height - 12), border_radius=4)

class Coin:
    def __init__(self, x, y, speed, anim_offset):
        self.x = x
        self.y = y
        self.radius = 24  
        self.speed = speed * 60
        self.anim_timer = anim_offset

    def update(self, dt, player_x, player_y, magnet_unlocked):
        if magnet_unlocked:
            dx = player_x + 40 - self.x
            dy = player_y + 54 - self.y
            dist = math.hypot(dx, dy)
            if dist < 450:
                pull = (450 - dist) * 2.2
                self.x += (dx / dist) * pull * dt * 60
                self.y += (dy / dist) * pull * dt * 60
                
        self.x -= self.speed * dt
        self.anim_timer += dt * 5

    def draw(self, surface):
        scale_x = abs(math.cos(self.anim_timer))
        width = int(self.radius * 2 * scale_x)
        if width < 1: width = 1
            
        coin_rect = pygame.Rect(int(self.x - width // 2), int(self.y - self.radius), width, self.radius * 2)
        pygame.draw.ellipse(surface, COIN_GOLD, coin_rect)
        inner_rect = pygame.Rect(int(self.x - width // 4), int(self.y - self.radius // 2), max(1, width // 2), self.radius)
        pygame.draw.ellipse(surface, COIN_SHINE, inner_rect)

class Button:
    def __init__(self, x, y, width, height, text, font, base_color=(30, 45, 70), hover_color=(45, 70, 110)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color

    def draw(self, surface, mouse_pos):
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, self.rect, width=3, border_radius=15)
        
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# --- MAIN GAME ENGINE ---

def main():
    game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
    game_data = load_game_data()
    
    # MOBILE INITIALIZATION: Auto-detects mobile screen limits natively
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if pygame.display.get_init() else pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
    pygame.display.set_caption("Jetpack Joyride: Mobile Edition")
    clock = pygame.time.Clock()
    
    title_font = pygame.font.SysFont("Impact", 90)
    font = pygame.font.SysFont("Arial", 36, bold=True)
    small_font = pygame.font.SysFont("Arial", 24, bold=True)
    
    player = Player()
    zappers, coins, particles = [], [], []
    
    active_mode = "CAMPAIGN" 
    selected_level = 1
    score = 0
    run_coins = 0
    hazard_timer = 0
    coin_group_timer = 0
    victory_timer = 0.0
    bonus_added = False
    
    state = 'START_MENU' 
    shop_tab = "UPGRADES" 

    # --- GUI INTERACTIVE BUTTONS ---
    campaign_btn = Button(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 - 170, 500, 75, "CAMPAIGN LEVEL MAP", font, (38, 145, 95), (50, 185, 120))
    infinite_btn = Button(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 - 75, 500, 75, "INFINITE ENDURANCE MODE", font, (140, 50, 160), (180, 70, 210))
    shop_btn = Button(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 + 20, 500, 75, "THE ELITE SHOP", font, (200, 140, 20), (235, 175, 40))
    settings_btn = Button(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 + 115, 500, 75, "SETTINGS", font)
    quit_btn = Button(BASE_WIDTH // 2 - 250, BASE_HEIGHT // 2 + 210, 500, 75, "QUIT GAME", font)
    
    fps_btn = Button(BASE_WIDTH // 2 - 300, BASE_HEIGHT // 2 - 60, 600, 100, f"MAX FPS TARGET: {game_data['max_fps']}", font)
    back_btn = Button(BASE_WIDTH // 2 - 200, BASE_HEIGHT // 2 + 100, 400, 90, "BACK TO MENU", font)

    retry_btn = Button(BASE_WIDTH // 2 - 420, BASE_HEIGHT // 2 + 50, 400, 90, "REDEPLOY (RETRY)", font, (38, 145, 95), (50, 185, 120))
    menu_btn = Button(BASE_WIDTH // 2 + 20, BASE_HEIGHT // 2 + 50, 400, 90, "MAIN HUB MENU", font)
    map_back_btn = Button(50, 50, 300, 70, "MAIN MENU", font)

    tab_upgrades_btn = Button(150, 260, 340, 70, "PERMANENT PERKS", font)
    tab_skins_btn = Button(520, 260, 340, 70, "SUIT COLORS", font)
    tab_textures_btn = Button(890, 260, 340, 70, "SUIT TEXTURES", font)
    shop_exit_btn = Button(BASE_WIDTH - 400, 260, 260, 70, "EXIT SHOP", font, (180, 50, 50))

    shop_item_btns = [
        Button(150, 800, 360, 70, "", font), Button(570, 800, 360, 70, "", font),
        Button(990, 800, 360, 70, "", font), Button(1410, 800, 360, 70, "", font)
    ]

    level_nodes = {1: (300, 600), 2: (650, 450), 3: (1000, 650), 4: (1350, 400), 5: (1700, 550)}

    while True:
        dt = min(clock.tick(game_data["max_fps"]) / 1000.0, 0.1)
        
        # --- MOBILE TOUCH INTERPOLATION ---
        # Instead of raw mouse positions, we grab the layout aspect ratio dynamically and project touch to 1920x1080 canvas coordinates
        real_mx, real_my = pygame.mouse.get_pos()
        scr_w, scr_h = screen.get_size()
        mouse_pos = (int(real_mx * (BASE_WIDTH / scr_w)), int(real_my * (BASE_HEIGHT / scr_h)))
        
        is_flying = False
        # On mobile, holding down on any part of the screen activates flight mechanics
        if state == 'PLAYING' and pygame.mouse.get_pressed()[0]:
            is_flying = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == 'START_MENU':
                    if campaign_btn.is_clicked(mouse_pos): state = 'LEVEL_MAP'
                    elif infinite_btn.is_clicked(mouse_pos):
                        active_mode = "INFINITE"
                        player.reset()
                        player.has_shield = game_data["shield_unlocked"]
                        zappers.clear(); coins.clear(); particles.clear()
                        score, run_coins, hazard_timer, coin_group_timer = 0, 0, 0, 0
                        state = 'PLAYING'
                    elif shop_btn.is_clicked(mouse_pos): state = 'SHOP'
                    elif settings_btn.is_clicked(mouse_pos): state = 'SETTINGS'
                    elif quit_btn.is_clicked(mouse_pos): pygame.quit(); sys.exit()
                        
                elif state == 'SETTINGS':
                    if fps_btn.is_clicked(mouse_pos):
                        fps_opts = [30, 60, 120, 144, 244]
                        idx = (fps_opts.index(game_data["max_fps"]) + 1) % len(fps_opts)
                        game_data["max_fps"] = fps_opts[idx]
                        fps_btn.text = f"MAX FPS TARGET: {game_data['max_fps']}"
                        save_game_data(game_data)
                    elif back_btn.is_clicked(mouse_pos): state = 'START_MENU'

                elif state == 'LEVEL_MAP':
                    if map_back_btn.is_clicked(mouse_pos): state = 'START_MENU'
                    for lvl_id, pos in level_nodes.items():
                        if lvl_id <= game_data["unlocked_level"]:
                            if math.hypot(mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]) < 60:
                                active_mode = "CAMPAIGN"
                                selected_level = lvl_id
                                player.reset()
                                player.has_shield = game_data["shield_unlocked"]
                                zappers.clear(); coins.clear(); particles.clear()
                                score, run_coins, hazard_timer, coin_group_timer, victory_timer = 0, 0, 0, 0, 0.0
                                bonus_added = False
                                state = 'PLAYING'
                    
                elif state == 'SHOP':
                    if tab_upgrades_btn.is_clicked(mouse_pos): shop_tab = "UPGRADES"
                    elif tab_skins_btn.is_clicked(mouse_pos): shop_tab = "COSMETICS"
                    elif tab_textures_btn.is_clicked(mouse_pos): shop_tab = "TEXTURES"
                    elif shop_exit_btn.is_clicked(mouse_pos): state = 'START_MENU'
                    
                    for idx, btn in enumerate(shop_item_btns):
                        if btn.is_clicked(mouse_pos):
                            if shop_tab == "UPGRADES":
                                if idx == 0 and not game_data["booster_unlocked"] and game_data["total_coins"] >= 25:
                                    game_data["total_coins"] -= 25; game_data["booster_unlocked"] = True
                                elif idx == 1 and not game_data["magnet_unlocked"] and game_data["total_coins"] >= 35:
                                    game_data["total_coins"] -= 35; game_data["magnet_unlocked"] = True
                                elif idx == 2 and not game_data["shield_unlocked"] and game_data["total_coins"] >= 50:
                                    game_data["total_coins"] -= 50; game_data["shield_unlocked"] = True
                                elif idx == 3 and game_data["total_coins"] >= 30:
                                    if not game_data["fuel_unlocked"]:
                                        game_data["total_coins"] -= 30; game_data["fuel_unlocked"] = True
                                    elif not game_data["gravity_unlocked"]:
                                        game_data["total_coins"] -= 30; game_data["gravity_unlocked"] = True
                                save_game_data(game_data)
                            elif shop_tab == "COSMETICS":
                                skins_map = {0: ("gold", 150), 1: ("ruby", 350), 2: ("emerald", 500), 3: ("shadow", 800)}
                                if idx in skins_map:
                                    name, cost = skins_map[idx]
                                    if name not in game_data["unlocked_skins"] and game_data["total_coins"] >= cost:
                                        game_data["total_coins"] -= cost; game_data["unlocked_skins"].append(name)
                                        game_data["equipped_skin"] = name
                                    elif name in game_data["unlocked_skins"]:
                                        game_data["equipped_skin"] = "cyan" if game_data["equipped_skin"] == name else name
                                save_game_data(game_data)
                            elif shop_tab == "TEXTURES":
                                tex_map = {0: ("tiger", 120), 1: ("camo", 250), 2: ("zebra", 450), 3: ("circuit", 700)}
                                if idx in tex_map:
                                    name, cost = tex_map[idx]
                                    if name not in game_data["unlocked_textures"] and game_data["total_coins"] >= cost:
                                        game_data["total_coins"] -= cost; game_data["unlocked_textures"].append(name)
                                        game_data["equipped_texture"] = name
                                    elif name in game_data["unlocked_textures"]:
                                        game_data["equipped_texture"] = "none" if game_data["equipped_texture"] == name else name
                                save_game_data(game_data)
                                    
                elif state == 'GAME_OVER':
                    if retry_btn.is_clicked(mouse_pos):
                        player.reset(); player.has_shield = game_data["shield_unlocked"]
                        zappers.clear(); coins.clear(); particles.clear()
                        score, run_coins, hazard_timer, coin_group_timer, victory_timer = 0, 0, 0, 0, 0.0
                        bonus_added = False
                        state = 'PLAYING'
                    elif menu_btn.is_clicked(mouse_pos): 
                        state = 'LEVEL_MAP' if active_mode == "CAMPAIGN" else 'START_MENU'

        # --- UPDATE GAME STATE ENGINE ---
        if state == 'PLAYING':
            if active_mode == "CAMPAIGN":
                lvl_conf = LEVELS_DATA[selected_level]
                base_spd = lvl_conf["base_speed"]
                spw_rate = lvl_conf["spawn_rate"]
                if int(score // 10) >= lvl_conf["target_distance"]:
                    state = 'VICTORY_SCENE'; zappers.clear()
            else: 
                inf_lvl = int(math.floor(math.sqrt(score // 10))) + 1
                base_spd = 12.0 + (inf_lvl * 0.5)
                spw_rate = max(45, 140 - (inf_lvl * 6))

            player.update(is_flying, dt, particles, game_data)
            score += 65 * dt
            
            for p in particles[:]:
                p.update(dt)
                if p.lifetime <= 0: particles.remove(p)
            
            hazard_timer += 60 * dt
            if hazard_timer > random.randint(int(spw_rate * 0.8), int(spw_rate * 1.2)):
                zappers.append(Zapper(base_spd)); hazard_timer = 0
                
            coin_group_timer += 60 * dt
            if coin_group_timer > random.randint(160, 240):
                cluster_y = random.randint(100, BASE_HEIGHT - 220)
                for i in range(random.randint(5, 9)):
                    coins.append(Coin(BASE_WIDTH + 80 + (i * 60), cluster_y, base_spd, i * 0.2))
                coin_group_timer = 0
                
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            for zapper in zappers[:]:
                zapper.update(dt)
                if player_rect.colliderect(pygame.Rect(zapper.x, zapper.y, zapper.width, zapper.height)):
                    if player.has_shield:
                        player.has_shield = False; zappers.remove(zapper)
                    else: state = 'GAME_OVER'
                elif zapper.x < -zapper.width: zappers.remove(zapper)
                    
            for coin in coins[:]:
                coin.update(dt, player.x, player.y, game_data["magnet_unlocked"])
                if player_rect.colliderect(pygame.Rect(coin.x - coin.radius, coin.y - coin.radius, coin.radius*2, coin.radius*2)):
                    mult = 2 if game_data["booster_unlocked"] else 1
                    run_coins += mult; game_data["total_coins"] += mult
                    save_game_data(game_data); coins.remove(coin)
                elif coin.x < -coin.radius * 2: coins.remove(coin)

        elif state == 'VICTORY_SCENE':
            victory_timer += dt
            player.update(False, dt, particles, game_data, state_frozen=True)
            
            if not bonus_added:
                game_data["total_coins"] += 150
                bonus_added = True
                save_game_data(game_data)

            if random.random() < 0.3: particles.append(Particle(player.x + 40, player.y + 50, is_victory=True))
            for p in particles[:]:
                p.update(dt, slow_grav=True)
                if p.lifetime <= 0: particles.remove(p)
                
            if victory_timer >= 3.8:
                if selected_level == game_data["unlocked_level"] and game_data["unlocked_level"] < 5:
                    game_data["unlocked_level"] += 1
                save_game_data(game_data); state = 'LEVEL_MAP'

        # --- SHOP CONFIG LABELS ---
        if state == 'SHOP':
            tab_upgrades_btn.base_color = (40, 90, 130) if shop_tab == "UPGRADES" else (20, 30, 45)
            tab_skins_btn.base_color = (40, 90, 130) if shop_tab == "COSMETICS" else (20, 30, 45)
            tab_textures_btn.base_color = (40, 90, 130) if shop_tab == "TEXTURES" else (20, 30, 45)
            
            if shop_tab == "UPGRADES":
                labels = [
                    ("DOUBLE GOLD", "2x Credits Multiplier", "UNLOCKED" if game_data["booster_unlocked"] else "BUY FOR 25 C"),
                    ("COIN MAGNET", "Vacuum pull coins", "UNLOCKED" if game_data["magnet_unlocked"] else "BUY FOR 35 C"),
                    ("CAPACITOR SHIELD", "Survive 1 Zapper blast", "UNLOCKED" if game_data["shield_unlocked"] else "BUY FOR 50 C"),
                    ("ENGINE BOOSTERS", "Agile Propulsion Thruster", "MAXED" if (game_data["fuel_unlocked"] and game_data["gravity_unlocked"]) else ("BUY GRAV (30 C)" if game_data["fuel_unlocked"] else "BUY FUEL (30 C)"))
                ]
            elif shop_tab == "COSMETICS":
                labels = [
                    ("GOLD SKIN", "Pure gold plating suit", "EQUIPPED" if game_data["equipped_skin"] == "gold" else ("EQUIP" if "gold" in game_data["unlocked_skins"] else "BUY: 150 C")),
                    ("RUBY SKIN", "Sleek red crystal mesh", "EQUIPPED" if game_data["equipped_skin"] == "ruby" else ("EQUIP" if "ruby" in game_data["unlocked_skins"] else "BUY: 350 C")),
                    ("EMERALD SKIN", "Neon matrix fiber layer", "EQUIPPED" if game_data["equipped_skin"] == "emerald" else ("EQUIP" if "emerald" in game_data["unlocked_skins"] else "BUY: 500 C")),
                    ("VOID SHADOW", "Dark anti-matter composite", "EQUIPPED" if game_data["equipped_skin"] == "shadow" else ("EQUIP" if "shadow" in game_data["unlocked_skins"] else "BUY: 800 C"))
                ]
            else: 
                labels = [
                    ("TIGER STRIPES", "Aggressive slash lines", "EQUIPPED" if game_data["equipped_texture"] == "tiger" else ("EQUIP" if "tiger" in game_data["unlocked_textures"] else "BUY: 120 C")),
                    ("DIGITAL CAMO", "Tactical combat pixel tiles", "EQUIPPED" if game_data["equipped_texture"] == "camo" else ("EQUIP" if "camo" in game_data["unlocked_textures"] else "BUY: 250 C")),
                    ("ZEBRA MATRIX", "Animated scrolling waves", "EQUIPPED" if game_data["equipped_texture"] == "zebra" else ("EQUIP" if "zebra" in game_data["unlocked_textures"] else "BUY: 450 C")),
                    ("CIRCUIT LINES", "Tech neon node pathing", "EQUIPPED" if game_data["equipped_texture"] == "circuit" else ("EQUIP" if "circuit" in game_data["unlocked_textures"] else "BUY: 700 C"))
                ]
            for idx, btn in enumerate(shop_item_btns):
                btn.text = labels[idx][2]
                btn.base_color = (35, 95, 55) if "EQUIPPED" in btn.text or "UNLOCKED" in btn.text or "MAXED" in btn.text else (30, 45, 70)

        # --- RENDERING ROUTINES ---
        draw_background_gradient(game_surface, BG_TOP, BG_BOTTOM)
        
        if state == 'START_MENU':
            title_text = title_font.render("JETPACK MOBILE SYSTEM", True, ZAPPER_YELLOW)
            game_surface.blit(title_text, (BASE_WIDTH // 2 - title_text.get_width() // 2, BASE_HEIGHT // 4 - 120))
            campaign_btn.draw(game_surface, mouse_pos)
            infinite_btn.draw(game_surface, mouse_pos)
            shop_btn.draw(game_surface, mouse_pos)
            settings_btn.draw(game_surface, mouse_pos)
            quit_btn.draw(game_surface, mouse_pos)
            
        elif state == 'SETTINGS':
            sett_title = title_font.render("SETTINGS ENGINE", True, WHITE)
            game_surface.blit(sett_title, (BASE_WIDTH // 2 - sett_title.get_width() // 2, BASE_HEIGHT // 4 - 50))
            fps_btn.draw(game_surface, mouse_pos); back_btn.draw(game_surface, mouse_pos)

        elif state == 'LEVEL_MAP':
            map_title = title_font.render("CAMPAIGN STAGE PROGRESSION", True, ZAPPER_YELLOW)
            wallet_surf = font.render(f"WALLET: {game_data['total_coins']} COINS  [REWARDS: +150 COINS PER WIN BONUS]", True, COIN_GOLD)
            game_surface.blit(map_title, (BASE_WIDTH // 2 - map_title.get_width() // 2, 60))
            game_surface.blit(wallet_surf, (BASE_WIDTH // 2 - wallet_surf.get_width() // 2, 160))
            
            points_list = [level_nodes[i] for i in sorted(level_nodes.keys())]
            pygame.draw.lines(game_surface, (50, 70, 100), False, points_list, width=8)
            
            for lvl_id, pos in level_nodes.items():
                is_unlocked = lvl_id <= game_data["unlocked_level"]
                pygame.draw.circle(game_surface, (46, 204, 113) if is_unlocked else (70, 80, 95), pos, 60)
                pygame.draw.circle(game_surface, WHITE if is_unlocked else (40, 45, 55), pos, 60, width=4)
                lbl = font.render(str(lvl_id), True, WHITE)
                game_surface.blit(lbl, (pos[0] - lbl.get_width()//2, pos[1] - lbl.get_height()//2))
                meta = small_font.render(LEVELS_DATA[lvl_id]["name"], True, (200, 210, 225) if is_unlocked else (100, 110, 120))
                game_surface.blit(meta, (pos[0] - meta.get_width()//2, pos[1] + 75))
            map_back_btn.draw(game_surface, mouse_pos)

        elif state == 'SHOP':
            shop_title = title_font.render("THE PREMIUM NEXUS BOUTIQUE", True, ZAPPER_YELLOW)
            wallet_surf = font.render(f"BALANCE: {game_data['total_coins']} COINS", True, COIN_GOLD)
            game_surface.blit(shop_title, (BASE_WIDTH // 2 - shop_title.get_width() // 2, 70))
            game_surface.blit(wallet_surf, (BASE_WIDTH // 2 - wallet_surf.get_width() // 2, 170))
            
            tab_upgrades_btn.draw(game_surface, mouse_pos); tab_skins_btn.draw(game_surface, mouse_pos)
            tab_textures_btn.draw(game_surface, mouse_pos); shop_exit_btn.draw(game_surface, mouse_pos)

            for i, btn in enumerate(shop_item_btns):
                card_x = 120 + (i * 420)
                pygame.draw.rect(game_surface, FLOOR_COLOR, (card_x, 380, 400, 520), border_radius=15)
                pygame.draw.rect(game_surface, WHITE, (card_x, 380, 400, 520), width=2, border_radius=15)
                h_text = font.render(labels[i][0], True, ZAPPER_YELLOW if shop_tab == "UPGRADES" else COIN_GOLD)
                d_text = small_font.render(labels[i][1], True, WHITE)
                game_surface.blit(h_text, (card_x + 200 - h_text.get_width()//2, 440))
                game_surface.blit(d_text, (card_x + 200 - d_text.get_width()//2, 540))
                btn.draw(game_surface, mouse_pos)

        else: 
            pygame.draw.rect(game_surface, FLOOR_COLOR, (0, BASE_HEIGHT - 90, BASE_WIDTH, 90))
            pygame.draw.rect(game_surface, ZAPPER_ORANGE, (0, BASE_HEIGHT - 90, BASE_WIDTH, 8), width=0)
            
            for p in particles: p.draw(game_surface)
            for coin in coins: coin.draw(game_surface)
            for zapper in zappers: zapper.draw(game_surface)
            player.draw(game_surface, game_data["equipped_skin"], game_data["equipped_texture"])
                
            if active_mode == "CAMPAIGN":
                target_goal = LEVELS_DATA[selected_level]["target_distance"]
                current_meters = min(target_goal, int(score // 10))
                score_surf = font.render(f"DISTANCE: {current_meters}m / {target_goal}m", True, WHITE)
                mode_surf = font.render(LEVELS_DATA[selected_level]["name"].upper(), True, ZAPPER_YELLOW)
            else:
                score_surf = font.render(f"DISTANCE: {int(score // 10)}m", True, WHITE)
                mode_surf = font.render(f"INFINITE SECTOR (LVL {int(math.floor(math.sqrt(score // 10))) + 1})", True, (180, 70, 210))
                
            coins_surf = font.render(f"COINS: {run_coins}", True, COIN_GOLD)
            game_surface.blit(score_surf, (40, 40)); game_surface.blit(coins_surf, (40, 100))
            game_surface.blit(mode_surf, (BASE_WIDTH - mode_surf.get_width() - 40, 40))
            
            if state == 'VICTORY_SCENE':
                vic_surf = title_font.render("STAGE CLEARED!", True, (50, 255, 120))
                bonus_surf = font.render("+150 VICTORY COINS BONUS ACQUIRED", True, COIN_GOLD)
                game_surface.blit(vic_surf, (BASE_WIDTH // 2 - vic_surf.get_width() // 2, BASE_HEIGHT // 2 - 120))
                game_surface.blit(bonus_surf, (BASE_WIDTH // 2 - bonus_surf.get_width() // 2, BASE_HEIGHT // 2 + 10))
            elif state == 'GAME_OVER':
                go_surf = title_font.render("RUN TERMINATED", True, (255, 60, 60))
                game_surface.blit(go_surf, (BASE_WIDTH // 2 - go_surf.get_width() // 2, BASE_HEIGHT // 2 - 100))
                retry_btn.draw(game_surface, mouse_pos); menu_btn.draw(game_surface, mouse_pos)

        # Dynamic screen fit to stretch content beautifully across any smartphone aspect ratio
        real_window_size = screen.get_size()
        scaled_final_surface = pygame.transform.scale(game_surface, real_window_size)
        screen.blit(scaled_final_surface, (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    main()