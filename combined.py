# lunaris_final_merged.py
# Merged: Alien invasion + Meteor storm game
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

# =========================
# GLOBAL STATE
# =========================

# Window & Core
WIDTH, HEIGHT = 1000, 800
random.seed(423)
game_level = 1

# Moon / world scale
BASE_RADIUS = 1500
SURFACE_RADIUS = BASE_RADIUS / 4
NUM_CRATERS = 20
craters = []
NUM_STARS = 300
stars = []

# Player / Game state
player_pos = [0.0, 0.0, SURFACE_RADIUS + 20.0]
gun_angle = 45.0
PLAYER_SPEED = 10.0

# Player stats (for both levels)
health = 100
max_health = 100.0
energy = 100.0
max_energy = 100.0
hit_count = 0
MAX_HITS = 3  # New: Player dies after 3 hits
score = 0
game_over = False
oxygen = 100.0
OXYGEN_DECAY_RATE = 0.5
missed_shots_count = 0 # New: Counter for missed shots
MAX_MISSED_SHOTS = 10 # New: Player dies after 10 missed shots

# Camera (third-person orbit & FPV toggle)
first_person_mode = False
camera_angle = 45.0
camera_height = 150.0
camera_radius = 520.0
camera_pos = [camera_radius, 0.0, camera_height]

# Bullets (shared between levels)
bullets = []
BULLET_SPEED = 50.0
BULLET_SIZE = 20.0
BULLET_COOLDOWN_MS = 120
last_shot_time = -100000

# Level 1 (teammategame.py) specifics
aliens = []
MAX_ALIENS_L1 = 1
total_aliens_to_spawn_L1 = 10
aliens_spawned_count_L1 = 0
ALIEN_SPAWN_INTERVAL = 5.0
last_alien_spawn_time = time.time()
INITIAL_ALIEN_SPEED = 3.0
ALIEN_SPEED_INCREASE_RATE = 0.5
ALIEN_SPAWN_HEIGHT = 1000
ALIEN_SPAWN_RADIUS_OFFSET = 500

# Coins (Level 1)
coins = []
MAX_COINS = 5
COIN_SPAWN_INTERVAL = 10.0
last_coin_spawn_time = time.time()
COIN_HEALTH_RESTORE = 20
COIN_OXYGEN_RESTORE = 20
collected_coins = 0
collision_message = ""
message_display_time = 0

# Level 2 (mygame.py) specifics
level_L2 = 1
SCORE_PER_LEVEL = 50
meteors = []
last_spawn_time = 0.0
storm_intensity = 1.0
TARGET_COOLDOWN = 0.3
last_target_time = 0.0
TARGET_SCORE = 10
ENERGY_RESTORE = 6
umbrella_active = False
umbrella_energy_cost = 0.5

# Visual constants (player model from mygame.py)
HEAD_R = 21
TORSO_W, TORSO_D, TORSO_H = 33.0, 21.0, 57.0
SHOULDER_R = 7.5
ARM_R, ARM_L = 6.0, 33.0
LEG_R_TOP, LEG_R_BOT, LEG_L = 10.5, 6.75, 42.0
GUN_BODY_L, GUN_BODY_W, GUN_BODY_H = 18.0, 8.0, 7.0
GUN_BARREL_R, GUN_BARREL_L = 3.0, 15.0

# Timing
FRAME_DT = 1.0 / 60.0

# =========================
# STAR & MOON FUNCTIONS
# =========================
def generate_stars(count=NUM_STARS):
    global stars
    stars = []
    for _ in range(count):
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(-math.pi / 2, math.pi / 2)
        radius = random.uniform(1200, 2500)
        x = radius * math.cos(phi) * math.cos(theta)
        y = radius * math.cos(phi) * math.sin(theta)
        z = radius * math.sin(phi)
        stars.append((x, y, z))

def draw_stars():
    glPointSize(2)
    glBegin(GL_POINTS)
    for i, (x, y, z) in enumerate(stars):
        blink_speed = 200.0 + (i % 3) * 50
        brightness = 0.6 + 0.4 * math.sin(glutGet(GLUT_ELAPSED_TIME) / blink_speed + i)
        glColor3f(brightness, brightness, brightness)
        glVertex3f(x, y, z)
    glEnd()

def init_craters():
    global craters
    craters = []
    moon_radius = SURFACE_RADIUS
    SAFE_ZONE_RADIUS = 200.0
    attempts = 0
    while len(craters) < NUM_CRATERS and attempts < NUM_CRATERS * 6:
        attempts += 1
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(0, math.pi)
        x = moon_radius * math.sin(phi) * math.cos(theta)
        y = moon_radius * math.sin(phi) * math.sin(theta)
        z = moon_radius * math.cos(phi)
        if math.hypot(x, y) < SAFE_ZONE_RADIUS:
            continue
        r = random.uniform(20, 50)
        craters.append({'pos': [x, y, z], 'radius': r})

def draw_moon():
    glPushMatrix()
    glColor3f(0.7, 0.7, 0.7)
    glutSolidSphere(SURFACE_RADIUS, 60, 60)
    glPopMatrix()
    for crater in craters:
        crater_pos = crater['pos']
        crater_radius = crater['radius']
        glPushMatrix()
        glColor3f(0.42, 0.42, 0.45)
        glTranslatef(crater_pos[0], crater_pos[1], crater_pos[2])
        dx, dy, dz = crater_pos
        angle_xy = math.degrees(math.atan2(dy, dx))
        hypot_xy = math.sqrt(dx*dx + dy*dy)
        angle_z = math.degrees(math.atan2(hypot_xy, dz)) if dz != 0 else 0.0
        glRotatef(angle_xy, 0, 0, 1)
        glRotatef(angle_z, 0, 1, 0)
        glTranslatef(0, 0, -2)
        glutSolidSphere(crater_radius, 20, 20)
        glPopMatrix()

# =========================
# HUD & CAMERA
# =========================
def draw_text(x, y, text, rgb=(1,1,1), font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(*rgb)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_targeting_reticle():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(2.0)
    cx, cy = WIDTH/2, HEIGHT/2
    glBegin(GL_LINES)
    glVertex2f(cx - 12, cy)
    glVertex2f(cx + 12, cy)
    glVertex2f(cx, cy - 12)
    glVertex2f(cx, cy + 12)
    glEnd()
    glLineWidth(1.0)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    draw_text(18, HEIGHT - 40, f"SCORE:{score:04d}")
    if game_level == 1:
        draw_text(18, HEIGHT - 64, f"Health: {health}   Oxygen: {int(oxygen)}%")
        draw_text(18, HEIGHT - 88, f"Aliens Remaining: {total_aliens_to_spawn_L1 - aliens_spawned_count_L1 + len(aliens)}")
    elif game_level == 2:
        draw_text(18, HEIGHT - 64, f"LEVEL:{level_L2}   LIVES:{max(0, MAX_HITS - hit_count)}")
        energy_percent = energy / max_energy if max_energy > 0 else 0
        energy_color = (1.0,1.0,1.0) if energy_percent>0.5 else (1.0,0.6,0.4) if energy_percent>0.2 else (1.0,0.3,0.3)
        draw_text(18, HEIGHT - 88, f"ENERGY:{int(energy)}", rgb=energy_color)
        draw_text(18, HEIGHT-112, f"MISSED SHOTS: {missed_shots_count}") # New: Missed shots counter
        if umbrella_active:
            draw_text(WIDTH - 240, HEIGHT - 40, "☂ UMBRELLA ACTIVE", rgb=(0.95,0.95,0.2))
    draw_text(WIDTH-120, HEIGHT-40, "Press 'x' to switch level", rgb=(0.9,0.9,0.9), font=GLUT_BITMAP_HELVETICA_12)


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(110, WIDTH/float(HEIGHT), 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person_mode:
        eye_x = player_pos[0] + 8.0*math.cos(math.radians(gun_angle))
        eye_y = player_pos[1] + 8.0*math.sin(math.radians(gun_angle))
        eye_z = player_pos[2] + TORSO_H * 0.92
        at_x = eye_x + 200.0 * math.cos(math.radians(gun_angle))
        at_y = eye_y + 200.0 * math.sin(math.radians(gun_angle))
        at_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z, at_x, at_y, at_z, 0, 0, 1)
    else:
        x = camera_pos[0]
        y = camera_pos[1]
        z = camera_pos[2]
        gluLookAt(x, y, z, 0.0, 0.0, SURFACE_RADIUS*0.18, 0, 0, 1)

# =========================
# PLAYER & UMBRELLA
# =========================
def draw_umbrella():
    if not umbrella_active:
        return
    px, py, pz = player_pos
    canopy_height = pz + TORSO_H + HEAD_R * 0.2 + 6.0
    canopy_radius = max(TORSO_W, TORSO_D) * 1.8
    energy_factor = max(0.35, min(1.0, energy / max_energy))
    glColor3f(0.85 * energy_factor, 0.15, 0.2 * energy_factor)
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(px, py, canopy_height)
    glPushMatrix()
    glScalef(1.0, 1.0, 0.55)
    gluSphere(quad, canopy_radius, 28, 12)
    glPopMatrix()
    glPopMatrix()
    glColor3f(0.45, 0.33, 0.2)
    glPushMatrix()
    glTranslatef(px, py, canopy_height)
    glRotatef(-90, 1, 0, 0)
    length = canopy_height - (pz - 10.0)
    if length < 1.0: length = 1.0
    gluCylinder(quad, 2.5, 2.5, length, 12, 1)
    glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    if game_over and game_level == 2:  # New: Player death animation
        glRotatef(90, 1, 0, 0)
    else:
        glRotatef(gun_angle, 0, 0, 1)

    if first_person_mode:
        glPushMatrix()
        glTranslatef(TORSO_W * 0.6, 0, TORSO_H * 0.72)
        glColor3f(0.22, 0.22, 0.22)
        glPushMatrix()
        glTranslatef(GUN_BODY_L * 0.5, 0, 0)
        glScalef(GUN_BODY_L, GUN_BODY_W, GUN_BODY_H)
        glutSolidCube(1.0)
        glPopMatrix()
        glColor3f(0.85, 0.0, 0.0)
        glRotatef(90, 0, 1, 0)
        quad = gluNewQuadric()
        gluCylinder(quad, GUN_BARREL_R, GUN_BARREL_R, GUN_BARREL_L, 20, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0, TORSO_H*0.42)
        glScalef(TORSO_W*0.5, TORSO_D*0.5, TORSO_H*0.45)
        glColor3f(0.4, 0.65, 0.4)
        glutSolidCube(1.0)
        glPopMatrix()
    else:
        glColor3f(0.4, 0.65, 0.4)
        glPushMatrix()
        glTranslatef(0,0, TORSO_H/2.0)
        glScalef(TORSO_W, TORSO_D, TORSO_H)
        glutSolidCube(1.0)
        glPopMatrix()
        glColor3f(0.9, 0.8, 0.7)
        glPushMatrix()
        glTranslatef(0, 0, TORSO_H + HEAD_R)
        glutSolidSphere(HEAD_R, 20, 20)
        glPopMatrix()
        glColor3f(0.9,0.8,0.7)
        for side in (-1,1):
            glPushMatrix()
            glTranslatef(0, side*(TORSO_D/2.0 + SHOULDER_R*0.3), TORSO_H*0.74)
            glutSolidSphere(SHOULDER_R, 12,12)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, side*(TORSO_D/2.0 + 1.0), TORSO_H*0.74)
            glRotatef(90,0,1,0)
            quad = gluNewQuadric()
            gluCylinder(quad, ARM_R, ARM_R, ARM_L, 12,1)
            glPopMatrix()
        glColor3f(1.0, 0.0, 0.0)
        leg_width = 12.0
        leg_depth = 12.0
        LEG_L = 42.0
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(side * (TORSO_W * 0.25), 0, -(LEG_L / 2.0))
            glScalef(leg_width, leg_depth, LEG_L)
            glutSolidCube(1.0)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(TORSO_W*0.6, 0, TORSO_H*0.72)
        glColor3f(0.22, 0.22, 0.22)
        glPushMatrix()
        glTranslatef(GUN_BODY_L*0.5, 0, 0)
        glScalef(GUN_BODY_L, GUN_BODY_W, GUN_BODY_H)
        glutSolidCube(1.0)
        glPopMatrix()
        glColor3f(0.85,0.0,0.0)
        glRotatef(90,0,1,0)
        quad = gluNewQuadric()
        gluCylinder(quad, GUN_BARREL_R, GUN_BARREL_R, GUN_BARREL_L, 20,1)
        glPopMatrix()
    draw_umbrella()
    glPopMatrix()


# =========================
# BULLET FUNCTIONS
# =========================
def get_gun_tip_world():
    forward = TORSO_W * 0.6 + GUN_BODY_L + GUN_BARREL_L * 0.5
    up = TORSO_H * 0.72
    gx = player_pos[0] + forward * math.cos(math.radians(gun_angle))
    gy = player_pos[1] + forward * math.sin(math.radians(gun_angle))
    gz = player_pos[2] + up
    return gx, gy, gz

def fire_bullet():
    global last_shot_time
    if game_over: return
    now = glutGet(GLUT_ELAPSED_TIME)
    if now - last_shot_time < BULLET_COOLDOWN_MS:
        return
    last_shot_time = now
    vx = math.cos(math.radians(gun_angle)) * BULLET_SPEED
    vy = math.sin(math.radians(gun_angle)) * BULLET_SPEED
    gun_x, gun_y, gun_z = get_gun_tip_world()
    bullets.append({'pos':[gun_x, gun_y, gun_z], 'vel':[vx,vy,0.0], 'active':True, 'is_from_player': True})

def update_bullets():
    global bullets, missed_shots_count, game_over
    for b in bullets[:]:
        b['pos'][0] += b['vel'][0] * (FRAME_DT*60.0)
        b['pos'][1] += b['vel'][1] * (FRAME_DT*60.0)
        if abs(b['pos'][0]) > SURFACE_RADIUS + 800 or abs(b['pos'][1]) > SURFACE_RADIUS + 800:
            if b['is_from_player']: # New: Check if the bullet missed
                missed_shots_count += 1
                if missed_shots_count >= MAX_MISSED_SHOTS:
                    game_over = True
            try:
                bullets.remove(b)
            except ValueError:
                pass

def draw_bullet(b):
    # New: Draw laser beam instead of bullet
    glPushMatrix()
    glColor3f(0.0, 0.6, 1.0) # Blue laser color
    glLineWidth(2.5)
    glBegin(GL_LINES)
    glVertex3f(b['pos'][0] - b['vel'][0]*0.2, b['pos'][1] - b['vel'][1]*0.2, b['pos'][2] - b['vel'][2]*0.2)
    glVertex3f(b['pos'][0], b['pos'][1], b['pos'][2])
    glEnd()
    glLineWidth(1.0)
    glPopMatrix()

# =========================
# LEVEL 1 LOGIC (ALIENS, COINS, OXYGEN)
# =========================
def draw_alien(alien_pos):
    glPushMatrix()
    glTranslatef(alien_pos[0], alien_pos[1], alien_pos[2])
    glColor3f(0.0, 1.0, 0.0)
    glPushMatrix()
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    glutSolidCone(20, 50, 20, 20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-10, 0, -30)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    glutSolidCone(10, 25, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10, 0, -30)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    glutSolidCone(10, 25, 10, 10)
    glPopMatrix()
    glPopMatrix()

def spawn_alien():
    global aliens, aliens_spawned_count_L1
    if len(aliens) < MAX_ALIENS_L1 and aliens_spawned_count_L1 < total_aliens_to_spawn_L1:
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(200, 500)
        x = player_pos[0] + dist * math.cos(angle)
        y = player_pos[1] + dist * math.sin(angle)
        z = player_pos[2] + ALIEN_SPAWN_HEIGHT
        aliens.append({
            'pos': [x, y, z],
            'speed': INITIAL_ALIEN_SPEED + (aliens_spawned_count_L1 * ALIEN_SPEED_INCREASE_RATE),
            'spawn_time': time.time()
        })
        aliens_spawned_count_L1 += 1

def update_aliens_L1(dt):
    global health, game_over, score, aliens
    aliens_to_remove = []
    for alien in aliens:
        dx = player_pos[0] - alien['pos'][0]
        dy = player_pos[1] - alien['pos'][1]
        dz = player_pos[2] - alien['pos'][2]
        dist_to_player = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist_to_player > 10:
            dir_x = dx / dist_to_player
            dir_y = dy / dist_to_player
            dir_z = dz / dist_to_player
            alien['pos'][0] += dir_x * alien['speed'] * dt
            alien['pos'][1] += dir_y * alien['speed'] * dt
            alien['pos'][2] += dir_z * alien['speed'] * dt
        else:
            aliens_to_remove.append(alien)
            health -= 25
            if health <= 0:
                game_over = True
    aliens[:] = [a for a in aliens if a not in aliens_to_remove]

def update_bullets_L1():
    global bullets, aliens, score
    bullets_to_remove = []
    aliens_to_remove = []
    for bullet in bullets:
        hit = False
        for alien in aliens:
            distance = math.sqrt((bullet['pos'][0] - alien['pos'][0])**2 + (bullet['pos'][1] - alien['pos'][1])**2 + (bullet['pos'][2] - alien['pos'][2])**2)
            if distance < 20: # Collision distance
                aliens_to_remove.append(alien)
                hit = True
                score += 10
                break
        if hit:
            bullets_to_remove.append(bullet)
        elif (time.time() - glutGet(GLUT_ELAPSED_TIME)/1000) > 1.5:
            bullets_to_remove.append(bullet)
        else:
            bullet['pos'][0] += bullet['vel'][0] * FRAME_DT * 60.0
            bullet['pos'][1] += bullet['vel'][1] * FRAME_DT * 60.0
    bullets[:] = [b for b in bullets if b not in bullets_to_remove]
    aliens[:] = [a for a in aliens if a not in aliens_to_remove]

def draw_coin(coin_pos):
    glPushMatrix()
    glColor3f(1.0, 0.84, 0.0)
    glTranslatef(coin_pos[0], coin_pos[1], coin_pos[2])
    glutSolidSphere(5.0, 20, 20)
    glPopMatrix()

def spawn_coin():
    global coins
    if len(coins) < MAX_COINS:
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, 200)
        x = player_pos[0] + dist * math.cos(angle)
        y = player_pos[1] + dist * math.sin(angle)
        dist_from_origin_sq = x**2 + y**2
        moon_radius = SURFACE_RADIUS
        if dist_from_origin_sq > moon_radius**2:
            dist_from_origin = math.sqrt(dist_from_origin_sq)
            x = (x / dist_from_origin) * moon_radius
            y = (y / dist_from_origin) * moon_radius
            dist_from_origin_sq = x**2 + y**2
        z = math.sqrt(moon_radius**2 - dist_from_origin_sq) + 2.0
        coins.append({'pos': [x, y, z]})

def check_coin_collision():
    global player_pos, coins, health, oxygen, collected_coins, collision_message, message_display_time
    coins_to_remove = []
    for coin in coins:
        distance = math.sqrt((player_pos[0] - coin['pos'][0])**2 + (player_pos[1] - coin['pos'][1])**2 + (player_pos[2] - coin['pos'][2])**2)
        if distance < 20:
            health = min(100, health + COIN_HEALTH_RESTORE)
            oxygen = min(100, oxygen + COIN_OXYGEN_RESTORE)
            collected_coins += 1
            collision_message = f"Coin collected! Total: {collected_coins}"
            message_display_time = time.time()
            coins_to_remove.append(coin)
    coins[:] = [c for c in coins if c not in coins_to_remove]

def manage_oxygen(dt):
    global oxygen, game_over
    if oxygen > 0:
        oxygen -= OXYGEN_DECAY_RATE * dt
        if oxygen <= 0:
            oxygen = 0
            game_over = True

# =========================
# LEVEL 2 LOGIC (METEORS, UMBRELLA)
# =========================
def get_storm_parameters(lvl):
    base_interval = max(0.5, 3.0 - (lvl * 0.2)) # Slower spawn interval
    meteors_per_wave = min(16, 1 + lvl) # Start with 1, increase with level
    base_speed = min(15.0, 4.0 + (lvl * 0.5)) # Slower initial speed
    storm_variance = 0.25 + (lvl * 0.04)
    return base_interval, meteors_per_wave, base_speed, storm_variance

def calculate_dynamic_spawn_interval(lvl):
    base_interval, _, _, variance = get_storm_parameters(lvl)
    random_factor = random.uniform(1.0 - variance, 1.0 + variance)
    return base_interval * random_factor * storm_intensity

def spawn_meteor_storm():
    global storm_intensity
    _, count, base_speed, _ = get_storm_parameters(level_L2)
    if level_L2 >= 3 and random.random() < 0.18:
        count = int(count * 1.4)
        storm_intensity = min(2.0, storm_intensity * 1.1)
    for _ in range(count):
        ang = random.uniform(0, 2*math.pi)
        dist = random.uniform(50, SURFACE_RADIUS - 50)
        x = dist * math.cos(ang)
        y = dist * math.sin(ang)
        z = random.uniform(350, 900)
        vx = random.uniform(-1.2, 1.2)
        vy = random.uniform(-1.2, 1.2)
        vz = -random.uniform(base_speed * 0.8, base_speed * 1.1)
        r = random.uniform(10, 34) if level_L2 <= 3 else random.uniform(9, 28)
        meteors.append({"x":x,"y":y,"z":z,"vx":vx,"vy":vy,"vz":vz,"r":r,"is_hit":False,"hit_timer":0.0})

def update_meteors_and_collisions():
    global meteors, score, hit_count, energy, game_over
    new_meteors = []
    for m in meteors:
        if not m["is_hit"]:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            m["z"] += m["vz"]
        else:
            m["hit_timer"] += FRAME_DT
            m["x"] += m["vx"]*0.15
            m["y"] += m["vy"]*0.15
            m["z"] += m["vz"]*0.15
        if m["z"] <= 0:
            if umbrella_active:
                px,py,pz = player_pos
                canopy_z = pz + TORSO_H + HEAD_R * 0.2 + 6.0
                dx = m["x"] - px; dy = m["y"] - py; dz = 0 - canopy_z
                horiz = math.hypot(dx, dy)
                if horiz <= max(TORSO_W, TORSO_D) * 1.0 and abs(dz) <= 30:
                    continue
            dx = m["x"] - player_pos[0]; dy = m["y"] - player_pos[1]
            horiz = math.hypot(dx, dy)
            if horiz < (m["r"] + 18):
                hit_count += 1
                energy -= 15
                score = max(0, score - 8)
                if hit_count >= MAX_HITS or energy <= 0:
                    game_over = True
            continue
        if m["is_hit"]:
            if m["hit_timer"] >= 0.45:
                continue
            new_meteors.append(m)
            continue
        collided = False
        for b in bullets[:]:
            dx = m["x"] - b['pos'][0]; dy = m["y"] - b['pos'][1]; dz = m["z"] - b['pos'][2]
            dist3 = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist3 <= (m["r"] + 3.0):
                m["is_hit"] = True
                m["hit_timer"] = 0.0
                try:
                    bullets.remove(b)
                except ValueError:
                    pass
                score += 1
                energy = min(max_energy, energy + 1.0)
                collided = True
                break
        if collided:
            new_meteors.append(m)
            continue
        if umbrella_active:
            px,py,pz = player_pos
            canopy_z = pz + TORSO_H + HEAD_R * 0.2 + 6.0
            dx = m["x"] - px; dy = m["y"] - py; dz = m["z"] - canopy_z
            horiz = math.hypot(dx, dy)
            if horiz <= max(TORSO_W, TORSO_D) * 1.0 and abs(dz) <= 25 and m["vz"] < 0:
                continue
        dx = m["x"] - player_pos[0]; dy = m["y"] - player_pos[1]
        horiz = math.hypot(dx, dy)
        if horiz < (m["r"] + 15) and m["z"] <= 30:
            hit_count += 1
            energy -= 15
            score = max(0, score - 8)
            if hit_count >= MAX_HITS or energy <= 0:
                game_over = True
            continue
        new_meteors.append(m)
    meteors = new_meteors

def draw_meteors():
    for m in meteors:
        glPushMatrix()
        glTranslatef(m["x"], m["y"], m["z"])
        if m["is_hit"]:
            if int(m["hit_timer"] * 25) % 2 == 0:
                glColor3f(1.0, 0.9, 0.5)
                glutSolidSphere(m["r"]*1.1, 12, 12)
        else:
            intensity = min(1.0, 0.5 + (level_L2*0.04))
            glColor3f(1.0, intensity*0.6, intensity*0.1)
            glutSolidSphere(m["r"], 14, 14)
        glPopMatrix()

def update_umbrella_energy():
    # Umbrella no longer drains energy as requested.
    pass

def check_level_progression_L2():
    global level_L2, storm_intensity
    target_score = level_L2 * SCORE_PER_LEVEL
    if score >= target_score:
        level_L2 += 1
        storm_intensity = 1.0
        return True
    return False

# =========================
# GAME MANAGEMENT & CONTROLS
# =========================
def restart():
    global game_level, health, oxygen, score, game_over, aliens, coins, collected_coins, last_alien_spawn_time, aliens_spawned_count_L1, level_L2, hit_count, energy, umbrella_active, meteors, last_spawn_time, storm_intensity, missed_shots_count
    
    # Resetting Level 1 specific variables
    health = 100
    oxygen = 100.0
    aliens = []
    coins = []
    collected_coins = 0
    last_alien_spawn_time = time.time()
    aliens_spawned_count_L1 = 0
    
    # Resetting Level 2 specific variables
    level_L2 = 1
    hit_count = 0
    energy = 100.0
    umbrella_active = False
    meteors = []
    last_spawn_time = time.time()
    storm_intensity = 1.0
    missed_shots_count = 0 # New: Reset missed shots counter
    if hasattr(idle, 'next_spawn_interval'):
        delattr(idle, 'next_spawn_interval')
    
    # Resetting common variables
    score = 0
    game_over = False
    player_pos[0] = 0.0
    player_pos[1] = 0.0
    player_pos[2] = SURFACE_RADIUS + 20.0
    gun_angle = 45.0
    init_craters()

def keyboardListener(key, x, y):
    global player_pos, gun_angle, game_over, umbrella_active, game_level
    if game_over and key != b'r':
        return
    
    angle_rad = math.radians(gun_angle)
    forward_x = math.cos(angle_rad)
    forward_y = math.sin(angle_rad)
    
    new_x, new_y = player_pos[0], player_pos[1]
    
    if key == b'w':
        new_x += forward_x * PLAYER_SPEED
        new_y += forward_y * PLAYER_SPEED
    elif key == b's':
        new_x -= forward_x * PLAYER_SPEED
        new_y -= forward_y * PLAYER_SPEED
    elif key == b'a':
        gun_angle = (gun_angle + 6) % 360
    elif key == b'd':
        gun_angle = (gun_angle - 6) % 360
    elif key == b'u' and game_level == 2:
        umbrella_active = not umbrella_active
    elif key == b'r':
        restart()
    elif key == b'x':
        if game_level == 1:
            game_level = 2
        else:
            game_level = 1
        restart() # Reset the game to the initial state of the new level
    elif key == b' ': # New: Spacebar special attack
        if game_level == 2 and not game_over:
            destroy_nearest_meteor()
    elif key == b'\x1b':
        glutLeaveMainLoop()
        return

    dist_xy = math.hypot(new_x, new_y)
    if dist_xy <= SURFACE_RADIUS - 18:
        player_pos[0], player_pos[1] = new_x, new_y
        player_pos[2] = math.sqrt(SURFACE_RADIUS**2 - dist_xy**2) + 20.0
    
    glutPostRedisplay()

def destroy_nearest_meteor():
    global meteors, score
    if not meteors:
        return
    
    nearest_meteor = None
    min_dist_sq = float('inf')
    
    px, py, pz = player_pos
    for meteor in meteors:
        dx = meteor["x"] - px
        dy = meteor["y"] - py
        dz = meteor["z"] - pz
        dist_sq = dx**2 + dy**2 + dz**2
        
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest_meteor = meteor
            
    if nearest_meteor:
        nearest_meteor['is_hit'] = True
        nearest_meteor['hit_timer'] = 0.0
        score += 1 # Add score for destroying with special attack
        
def specialKeyListener(key, x, y):
    global camera_angle, camera_height, camera_radius, camera_pos
    if key == GLUT_KEY_UP:
        camera_height = min(900.0, camera_height + 20.0)
    elif key == GLUT_KEY_DOWN:
        camera_height = max(120.0, camera_height - 20.0)
    elif key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle + 4.0) % 360.0
    elif key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle - 4.0) % 360.0
    dist = camera_radius
    camera_pos[0] = dist * math.cos(math.radians(camera_angle))
    camera_pos[1] = dist * math.sin(math.radians(camera_angle))
    camera_pos[2] = camera_height
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global first_person_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        fire_bullet()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glClearColor(0.01, 0.01, 0.03, 1)
    setupCamera()
    draw_stars()
    draw_moon()
    draw_player()
    
    if game_level == 1:
        for alien in aliens:
            draw_alien(alien['pos'])
        for coin in coins:
            draw_coin(coin['pos'])
    elif game_level == 2:
        draw_meteors()
        draw_umbrella()
    
    for b in bullets:
        draw_bullet(b)

    draw_hud()
    draw_targeting_reticle()

    if game_over:
        draw_text(WIDTH/2 - 120, HEIGHT/2 + 20, "GAME OVER", rgb=(1,0.3,0.3))
        draw_text(WIDTH/2 - 140, HEIGHT/2 - 10, f"Final Score: {score} | Level: {'1' if game_level == 1 else '2'}", rgb=(1,1,1), font=GLUT_BITMAP_HELVETICA_12)
        draw_text(WIDTH/2 - 90, HEIGHT/2 - 40, "Press R to restart", rgb=(0.9,0.9,0.9), font=GLUT_BITMAP_HELVETICA_12)

    glutSwapBuffers()

def idle():
    global last_alien_spawn_time, last_coin_spawn_time, game_level, last_spawn_time
    
    now = time.time()
    if not hasattr(idle, 'last_tick'):
        idle.last_tick = now
    dt = now - idle.last_tick
    idle.last_tick = now

    if game_over:
        glutPostRedisplay()
        return

    if game_level == 1:
        if now - last_alien_spawn_time > ALIEN_SPAWN_INTERVAL and len(aliens) < MAX_ALIENS_L1 and aliens_spawned_count_L1 < total_aliens_to_spawn_L1:
            spawn_alien()
            last_alien_spawn_time = now
        
        if now - last_coin_spawn_time > COIN_SPAWN_INTERVAL and len(coins) < MAX_COINS:
            spawn_coin()
            last_coin_spawn_time = now
        
        manage_oxygen(dt)
        update_aliens_L1(dt)
        update_bullets_L1()
        check_coin_collision()

    elif game_level == 2:
        if not hasattr(idle, 'next_spawn_interval'):
            idle.next_spawn_interval = calculate_dynamic_spawn_interval(level_L2)
        if now - last_spawn_time >= idle.next_spawn_interval:
            spawn_meteor_storm()
            last_spawn_time = now
            idle.next_spawn_interval = calculate_dynamic_spawn_interval(level_L2)
        update_meteors_and_collisions()
        update_umbrella_energy()
        check_level_progression_L2()
        update_bullets()
    
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(40, 40)
    glutCreateWindow(b"LUNARIS: The Last Outpost")
    glEnable(GL_DEPTH_TEST)
    generate_stars(NUM_STARS)
    init_craters()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
