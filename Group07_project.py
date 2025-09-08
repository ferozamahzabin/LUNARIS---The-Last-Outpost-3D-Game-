from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

# =========================
# Global State Management
# =========================
MODE_MENU = 0
MODE_ALIEN_SHOOTER = 1
MODE_METEOR_SHOOTER = 2
current_mode = MODE_MENU

# General settings
WIDTH, HEIGHT = 1000, 800
BASE_RADIUS = 1500
SURFACE_RADIUS = BASE_RADIUS / 4

# =========================
# Game States for Alien Shooter
# =========================
player_pos_alien = [0.0, 0.0, SURFACE_RADIUS + 4]
player_angle_alien = 0.0
gun_rotation_speed = 240.0
PLAYER_SPEED_ALIEN = 5.0
camera_angle_alien = 45.0
camera_height_alien = 200.0
camera_radius_alien = 600.0
camera_pos_alien = [camera_radius_alien, 0.0, camera_height_alien]
NUM_CRATERS_ALIEN = 20
craters_alien = []
NUM_STARS_ALIEN = 400
stars_alien = []
aliens = []
MAX_ALIENS = 2
total_aliens_to_spawn = 10
aliens_spawned_count = 0
ALIEN_SPAWN_INTERVAL = 5.0
last_alien_spawn_time = time.time()
INITIAL_ALIEN_SPEED = 10.0
ALIEN_SPEED_INCREASE_RATE = 0.5
ALIEN_COLLISION_RADIUS = 15.0
is_paused_alien = False
game_over_alien = False
score_alien = 0
health_alien = 100
oxygen_alien = 100.0
OXYGEN_DECAY_RATE = 0.5
bullets_alien = []
BULLET_SPEED_ALIEN = 100.0
BULLET_LIFETIME = 3.0
BULLET_RADIUS = 1.0
is_firing_alien = False
last_shot_time_alien = time.time()
BULLET_COOLDOWN_ALIEN = 0.1
coins = []
MAX_COINS = 5
COIN_SPAWN_INTERVAL = 10.0
last_coin_spawn_time = time.time()
COIN_HEALTH_RESTORE = 20
COIN_OXYGEN_RESTORE = 20
collected_coins = 0
collision_message = ""
message_display_time = 0
is_shielded = False
shield_duration = 10.0
shield_start_time = 0.0
last_tick_alien = time.time()

# =========================
# Game States for Meteor Shooter
# =========================
player_pos_meteor = [0.0, 0.0, SURFACE_RADIUS + 20.0]
gun_angle = 45.0
PLAYER_SPEED_METEOR = 10.0
energy = 100.0
max_energy = 100.0
hit_count = 0
MAX_HITS = 10
game_over_meteor = False
umbrella_active = False
umbrella_energy_cost = 0.5
first_person_mode = False
score_meteor = 0
level = 1
SCORE_PER_LEVEL = 50
camera_angle_meteor = 45.0
camera_height_meteor = 150.0
camera_radius_meteor = 520.0
camera_pos_meteor = [camera_radius_meteor, 0.0, camera_height_meteor]
meteors = []
last_spawn_time = 0.0
storm_intensity = 1.0
bullets_meteor = []
BULLET_SPEED_METEOR = 50.0
BULLET_SIZE_METEOR = 20.0
BULLET_COOLDOWN_MS_METEOR = 120
last_shot_time_meteor = -100000
TARGET_COOLDOWN = 0.3
last_target_time = 0.0
TARGET_SCORE = 10
ENERGY_RESTORE = 6
HEAD_R = 21
TORSO_W, TORSO_D, TORSO_H = 33.0, 21.0, 57.0
SHOULDER_R = 7.5
ARM_R, ARM_L = 6.0, 33.0
LEG_L = 42.0
GUN_BODY_L, GUN_BODY_W, GUN_BODY_H = 18.0, 8.0, 7.0
GUN_BARREL_R, GUN_BARREL_L = 3.0, 15.0
FRAME_DT = 1.0 / 60.0
craters_meteor = []
stars_meteor = []
NUM_STARS_METEOR = 300
missed_bullets = 0
MAX_MISSED_BULLETS = 10

# =========================
# Common Functions (Stars, Moon, Text)
# =========================

def generate_stars(count, target_list):
    """Generate stars for a specific game mode."""
    target_list.clear()
    for _ in range(count):
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(0, math.pi)
        radius = random.uniform(1000, 2500)
        x = radius * math.cos(theta) * math.sin(phi) if current_mode == MODE_ALIEN_SHOOTER else radius * math.cos(phi) * math.cos(theta)
        y = radius * math.sin(theta) * math.sin(phi) if current_mode == MODE_ALIEN_SHOOTER else radius * math.cos(phi) * math.sin(theta)
        z = radius * math.cos(phi) if current_mode == MODE_ALIEN_SHOOTER else radius * math.sin(phi)
        target_list.append((x, y, z))

def draw_stars(stars_list):
    glPointSize(2)
    glBegin(GL_POINTS)
    for i, (x, y, z) in enumerate(stars_list):
        brightness = 0.5 + 0.5 * math.sin(time.time() * 3 + i)
        glColor3f(brightness, brightness, brightness)
        glVertex3f(x, y, z)
    glEnd()

def init_craters(target_list):
    """Randomly generate crater positions."""
    target_list.clear()
    moon_radius = SURFACE_RADIUS
    SAFE_ZONE_RADIUS = 200.0
    
    attempts = 0
    while len(target_list) < 20 and attempts < 120:
        attempts += 1
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(0, math.pi)
        x = moon_radius * math.sin(phi) * math.cos(theta)
        y = moon_radius * math.sin(phi) * math.sin(theta)
        z = moon_radius * math.cos(phi)

        if math.hypot(x, y) < SAFE_ZONE_RADIUS:
            continue
        
        r = random.uniform(20, 50)
        target_list.append({'pos': [x, y, z], 'radius': r})

def draw_moon(craters_list):
    glPushMatrix()
    glColor3f(0.7, 0.7, 0.7)
    glutSolidSphere(SURFACE_RADIUS, 60, 60)
    glPopMatrix()
    
    for crater in craters_list:
        crater_pos = crater['pos']
        crater_radius = crater['radius']
        
        glPushMatrix()
        glColor3f(0.4, 0.4, 0.4)
        glTranslatef(crater_pos[0], crater_pos[1], crater_pos[2])
        
        direction_vector = [crater_pos[0], crater_pos[1], crater_pos[2]]
        angle_xy = math.degrees(math.atan2(direction_vector[1], direction_vector[0]))
        angle_z = math.degrees(math.atan2(math.sqrt(direction_vector[0]**2 + direction_vector[1]**2), direction_vector[2]))
        
        glRotatef(angle_xy, 0, 0, 1)
        glRotatef(angle_z, 0, 1, 0)
        
        glTranslatef(0, 0, -2)
        glutSolidSphere(crater_radius, 20, 20)
        glPopMatrix()

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

# =========================
# Alien Shooter Logic
# =========================
def draw_gun_alien():
    glPushMatrix()
    glTranslatef(2.5, 0.0, 1.0)
    glRotatef(90, 1, 0, 0)
    glColor3f(0.3, 0.3, 0.3)
    gluCylinder(gluNewQuadric(), 0.3, 0.3, 2.5, 12, 12)
    glPushMatrix()
    glTranslatef(0.0, 0.0, 2.5)
    glColor3f(0.5, 0.5, 0.5)
    glutSolidCone(0.4, 0.8, 12, 12)
    glPopMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(0.0, 0.0, 0.5)
    glScalef(0.6, 1.8, 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    glPopMatrix()

def draw_player_alien():
    global player_pos_alien, player_angle_alien, is_shielded
    glPushMatrix()
    glTranslatef(player_pos_alien[0], player_pos_alien[1], player_pos_alien[2])
    glRotatef(player_angle_alien, 0, 0, 1)

    if is_shielded:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glColor4f(0.2, 0.8, 1.0, 0.5)
        glutSolidSphere(6.0, 20, 20)
        glPopMatrix()
        glDisable(GL_BLEND)

    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glScalef(2.0, 1.6, 3.0)
    glutSolidCube(1.0)
    glPopMatrix()
    glColor3f(1.0, 0.9, 0.6)
    glPushMatrix()
    glTranslatef(0, 0, 1.8)
    glutSolidSphere(1.0, 20, 20)
    glPopMatrix()

    # Arms & Legs
    glColor3f(1.0, 1.0, 1.0)
    for x_offset in (1.3, -1.3):
        glPushMatrix()
        glTranslatef(x_offset, 0, 0.7)
        glRotatef(-45, 1, 0, 0)
        glScalef(0.7, 0.7, 2.0)
        glutSolidCube(1.0)
        glPopMatrix()
    for x_offset in (0.6, -0.6):
        glPushMatrix()
        glTranslatef(x_offset, 0, -2.0)
        glScalef(0.8, 0.8, 2.2)
        glutSolidCube(1.0)
        glPopMatrix()

    draw_gun_alien()
    glPopMatrix()

def draw_bullet_alien(bullet_pos):
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.0)
    glTranslatef(bullet_pos[0], bullet_pos[1], bullet_pos[2])
    glutSolidSphere(BULLET_RADIUS, 8, 8)
    glPopMatrix()

def fire_bullet_alien():
    global bullets_alien, last_shot_time_alien
    now = time.time()
    if now - last_shot_time_alien < BULLET_COOLDOWN_ALIEN:
        return
    
    angle_rad = math.radians(player_angle_alien)
    forward_x = math.cos(angle_rad)
    forward_y = math.sin(angle_rad)
    
    bullet_start_pos = list(player_pos_alien)
    bullet_start_pos[0] += forward_x * 5
    bullet_start_pos[1] += forward_y * 5

    bullets_alien.append({
        'pos': bullet_start_pos,
        'direction': [forward_x, forward_y, 0],
        'spawn_time': time.time()
    })
    last_shot_time_alien = now

def check_collision_alien(pos1, pos2, radius1, radius2):
    distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 + (pos1[2] - pos2[2])**2)
    return distance < (radius1 + radius2)

def draw_alien(alien_pos):
    glPushMatrix()
    glTranslatef(alien_pos[0], alien_pos[1], alien_pos[2])
    
    target_vector = [player_pos_alien[0] - alien_pos[0], player_pos_alien[1] - alien_pos[1]]
    angle_rad = math.atan2(target_vector[1], target_vector[0])
    angle_deg = math.degrees(angle_rad)
    glRotatef(angle_deg, 0, 0, 1)

    glColor3f(0.0, 1.0, 0.0)
    glPushMatrix()
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    glutSolidCone(15, 37.5, 20, 20)
    glPopMatrix()
    
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, 37.5)
    glutSolidSphere(11.25, 20, 20)
    glPopMatrix()
    glPopMatrix()

def spawn_alien():
    global aliens, aliens_spawned_count
    moon_radius = SURFACE_RADIUS
    if len(aliens) < MAX_ALIENS and aliens_spawned_count < total_aliens_to_spawn:
        angle = random.uniform(0, 2 * math.pi)
        spawn_dist_xy = random.uniform(moon_radius/2, moon_radius - 20)
        x = spawn_dist_xy * math.cos(angle)
        y = spawn_dist_xy * math.sin(angle)
        dist_from_origin_sq = x**2 + y**2
        z = math.sqrt(moon_radius**2 - dist_from_origin_sq) + 20.0
        
        aliens.append({
            'pos': [x, y, z],
            'speed': INITIAL_ALIEN_SPEED + (aliens_spawned_count * ALIEN_SPEED_INCREASE_RATE),
            'spawn_time': time.time()
        })
        aliens_spawned_count += 1
        print(f"Spawned alien #{aliens_spawned_count} with speed {aliens[-1]['speed']:.2f}")

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
        x = player_pos_alien[0] + dist * math.cos(angle)
        y = player_pos_alien[1] + dist * math.sin(angle)
        
        moon_radius = SURFACE_RADIUS
        dist_from_origin_sq = x**2 + y**2
        if dist_from_origin_sq > moon_radius**2:
            dist_from_origin = math.sqrt(dist_from_origin_sq)
            x = (x / dist_from_origin) * moon_radius
            y = (y / dist_from_origin) * moon_radius
            dist_from_origin_sq = x**2 + y**2

        z = math.sqrt(moon_radius**2 - dist_from_origin_sq) + 2.0
        coins.append({'pos': [x, y, z]})
        print("Spawned a new coin.")

def check_coin_collision():
    global player_pos_alien, coins, health_alien, oxygen_alien, collected_coins, collision_message, message_display_time
    coins_to_remove = []
    
    for coin in coins:
        distance = math.sqrt((player_pos_alien[0] - coin['pos'][0])**2 + (player_pos_alien[1] - coin['pos'][1])**2 + (player_pos_alien[2] - coin['pos'][2])**2)
        
        if distance < 20:
            health_alien = min(100, health_alien + COIN_HEALTH_RESTORE)
            oxygen_alien = min(100, oxygen_alien + COIN_OXYGEN_RESTORE)
            collected_coins += 1
            collision_message = f"Coin collected! Total: {collected_coins}"
            message_display_time = time.time()
            coins_to_remove.append(coin)
            
    coins[:] = [c for c in coins if c not in coins_to_remove]

def activate_shield():
    global is_shielded, shield_start_time
    if not is_shielded:
        is_shielded = True
        shield_start_time = time.time()
        print("Shield Activated!")

def setup_camera_alien():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, 1.25, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    cam_x = player_pos_alien[0] + camera_radius_alien * math.cos(math.radians(camera_angle_alien) + math.pi)
    cam_y = player_pos_alien[1] + camera_radius_alien * math.sin(math.radians(camera_angle_alien) + math.pi)
    
    gluLookAt(cam_x, cam_y, player_pos_alien[2] + camera_height_alien, 
              player_pos_alien[0], player_pos_alien[1], player_pos_alien[2],
              0, 0, 1)

def show_screen_alien():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glClearColor(0.0, 0.0, 0.05, 1.0)
    setup_camera_alien()
    draw_stars(stars_alien)
    draw_moon(craters_alien)
    draw_player_alien()
    
    for alien in aliens:
        draw_alien(alien['pos'])
    for bullet in bullets_alien:
        draw_bullet_alien(bullet['pos'])
    for coin in coins:
        draw_coin(coin['pos'])

    draw_text(20, 760, "LUNARIS: ALIEN SHOOTER")
    draw_text(20, 730, f"Score: {score_alien}  Health: {health_alien}")
    draw_text(20, 700, f"Oxygen: {int(oxygen_alien)}%")
    draw_text(20, 670, f"Aliens: {len(aliens)} / {total_aliens_to_spawn}") 
    
    draw_text(850, 760, "P: Pause")
    draw_text(850, 730, "R: Restart")
    draw_text(850, 700, "N: Spin")
    draw_text(850, 670, "M: Shield")
    
    if is_shielded:
        remaining_time = max(0, shield_duration - (time.time() - shield_start_time))
        draw_text(20, 640, f"Shield: {int(remaining_time)}s")
    
    if collision_message and time.time() - message_display_time < 3:
        draw_text(20, 640, collision_message)

    if is_paused_alien:
        draw_text(450, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)

    if game_over_alien:
        draw_text(450, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)

    glutSwapBuffers()

def manage_oxygen(dt):
    global oxygen_alien, game_over_alien
    if oxygen_alien > 0:
        oxygen_alien -= OXYGEN_DECAY_RATE * dt
        if oxygen_alien <= 0:
            oxygen_alien = 0
            game_over_alien = True
            print("Oxygen depleted! Game Over.")

def idle_alien():
    global last_alien_spawn_time, aliens, is_paused_alien, bullets_alien, last_tick_alien, is_firing_alien, score_alien, health_alien, game_over_alien, aliens_spawned_count, coins, last_coin_spawn_time, is_shielded, shield_start_time
    
    now = time.time()
    dt = now - last_tick_alien
    last_tick_alien = now

    if is_paused_alien or game_over_alien:
        glutPostRedisplay()
        return
    
    current_time = time.time()
    
    if is_shielded and (now - shield_start_time) > shield_duration:
        is_shielded = False
        print("Shield Expired!")
            
    if is_firing_alien:
        fire_bullet_alien()
        
    manage_oxygen(dt)

    if current_time - last_coin_spawn_time > COIN_SPAWN_INTERVAL and len(coins) < MAX_COINS:
        spawn_coin()
        last_coin_spawn_time = current_time
    check_coin_collision()

    if current_time - last_alien_spawn_time > ALIEN_SPAWN_INTERVAL and len(aliens) < MAX_ALIENS and aliens_spawned_count < total_aliens_to_spawn:
        spawn_alien()
        last_alien_spawn_time = current_time

    bullets_to_remove = []
    aliens_to_remove = []
    for bullet in bullets_alien:
        hit = False
        for alien in aliens:
            if check_collision_alien(bullet['pos'], alien['pos'], BULLET_RADIUS, ALIEN_COLLISION_RADIUS):
                aliens_to_remove.append(alien)
                hit = True
                score_alien += 10
                break
        
        if hit:
            bullets_to_remove.append(bullet)
        elif (current_time - bullet['spawn_time']) > BULLET_LIFETIME:
            bullets_to_remove.append(bullet)
        else:
            bullet['pos'][0] += bullet['direction'][0] * BULLET_SPEED_ALIEN * dt
            bullet['pos'][1] += bullet['direction'][1] * BULLET_SPEED_ALIEN * dt

    bullets_alien[:] = [b for b in bullets_alien if b not in bullets_to_remove]
    aliens[:] = [a for a in aliens if a not in aliens_to_remove]

    aliens_to_remove_after_move = []
    for alien in aliens:
        dx = player_pos_alien[0] - alien['pos'][0]
        dy = player_pos_alien[1] - alien['pos'][1]
        dz = player_pos_alien[2] - alien['pos'][2]
        dist_to_player = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist_to_player > 20:
            dir_x, dir_y, dir_z = dx / dist_to_player, dy / dist_to_player, dz / dist_to_player
            alien['pos'][0] += dir_x * alien['speed'] * dt
            alien['pos'][1] += dir_y * alien['speed'] * dt
            alien['pos'][2] += dir_z * alien['speed'] * dt
        else:
            if not is_shielded:
                health_alien -= 10
                if health_alien <= 0:
                    game_over_alien = True
                print("Alien hit player! Health is now:", health_alien)
            else:
                print("Alien hit shielded player! No damage taken.")
            aliens_to_remove_after_move.append(alien)
                
    aliens[:] = [a for a in aliens if a not in aliens_to_remove_after_move]

    glutPostRedisplay()

def restart_alien():
    global player_pos_alien, player_angle_alien, aliens, is_paused_alien, bullets_alien, last_tick_alien, score_alien, health_alien, aliens_spawned_count, game_over_alien, oxygen_alien, coins, last_coin_spawn_time, collected_coins, collision_message, message_display_time, is_shielded, shield_start_time
    player_pos_alien = [0.0, 0.0, SURFACE_RADIUS + 15]
    player_angle_alien = 0.0
    aliens = []
    bullets_alien = []
    coins = []
    aliens_spawned_count = 0
    score_alien = 0
    health_alien = 100
    oxygen_alien = 100.0
    collected_coins = 0
    collision_message = ""
    message_display_time = 0
    game_over_alien = False
    last_alien_spawn_time = time.time()
    last_coin_spawn_time = time.time()
    is_paused_alien = False
    is_shielded = False
    shield_start_time = 0.0
    last_tick_alien = time.time()
    init_craters(craters_alien)


# =========================
# Meteor Shooter Logic
# =========================

def draw_umbrella():
    global energy, max_energy
    if not umbrella_active:
        return
    px, py, pz = player_pos_meteor
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

def draw_player_meteor():
    global player_pos_meteor, gun_angle, first_person_mode
    glPushMatrix()
    glTranslatef(player_pos_meteor[0], player_pos_meteor[1], player_pos_meteor[2])
    glRotatef(gun_angle, 0, 0, 1)
    
    if first_person_mode:
        draw_gun_meteor(1)
    else:
        # Full body
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
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(side * (TORSO_W * 0.25), 0, -(LEG_L / 2.0))
            glScalef(leg_width, leg_depth, LEG_L)
            glutSolidCube(1.0)
            glPopMatrix()
        draw_gun_meteor()

    draw_umbrella()
    glPopMatrix()
    
def draw_dead_player_meteor():
    glPushMatrix()
    glTranslatef(player_pos_meteor[0], player_pos_meteor[1], player_pos_meteor[2])
    glRotatef(90, 1, 0, 0) # Lay the player flat
    
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
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * (TORSO_W * 0.25), 0, -(LEG_L / 2.0))
        glScalef(leg_width, leg_depth, LEG_L)
        glutSolidCube(1.0)
        glPopMatrix()
        
    draw_gun_meteor()
    glPopMatrix()

def draw_gun_meteor(fpv=0):
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

def get_storm_parameters(lvl):
    base_interval = max(0.3, 1.8 - (lvl * 0.15))
    meteors_per_wave = min(16, 2 + lvl)
    base_speed = min(28.0, 8.0 + (lvl * 1.5))
    storm_variance = 0.25 + (lvl * 0.04)
    return base_interval, meteors_per_wave, base_speed, storm_variance

def calculate_dynamic_spawn_interval(lvl):
    base_interval, _, _, variance = get_storm_parameters(lvl)
    random_factor = random.uniform(1.0 - variance, 1.0 + variance)
    return base_interval * random_factor * storm_intensity

def spawn_meteor_storm():
    global storm_intensity
    _, count, base_speed, _ = get_storm_parameters(level)
    if level >= 3 and random.random() < 0.18:
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
        r = random.uniform(10, 34) if level <= 3 else random.uniform(9, 28)
        meteors.append({"x":x,"y":y,"z":z,"vx":vx,"vy":vy,"vz":vz,"r":r,"is_hit":False,"hit_timer":0.0})

def update_meteors_and_collisions():
    global meteors, score_meteor, hit_count, energy, game_over_meteor
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
                px,py,pz = player_pos_meteor
                canopy_z = pz + TORSO_H + HEAD_R * 0.2 + 6.0
                dx = m["x"] - px; dy = m["y"] - py; dz = 0 - canopy_z
                horiz = math.hypot(dx, dy)
                if horiz <= max(TORSO_W, TORSO_D) * 1.0 and abs(dz) <= 30:
                    continue
            dx = m["x"] - player_pos_meteor[0]; dy = m["y"] - player_pos_meteor[1]
            horiz = math.hypot(dx, dy)
            if horiz < (m["r"] + 18):
                hit_count += 1
                energy -= 15
                score_meteor = max(0, score_meteor - 8)
                if hit_count >= MAX_HITS or energy <= 0:
                    game_over_meteor = True
            continue

        if m["is_hit"]:
            if m["hit_timer"] >= 0.45:
                continue
            new_meteors.append(m)
            continue

        collided = False
        for b in bullets_meteor[:]:
            dx = m["x"] - b['pos'][0]; dy = m["y"] - b['pos'][1]; dz = m["z"] - b['pos'][2]
            dist3 = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist3 <= (m["r"] + 3.0):
                m["is_hit"] = True
                m["hit_timer"] = 0.0
                try:
                    bullets_meteor.remove(b)
                except ValueError:
                    pass
                score_meteor += 1
                energy = min(max_energy, energy + 1.0)
                collided = True
                break
        if collided:
            new_meteors.append(m)
            continue

        if umbrella_active:
            px,py,pz = player_pos_meteor
            canopy_z = pz + TORSO_H + HEAD_R * 0.2 + 6.0
            dx = m["x"] - px; dy = m["y"] - py; dz = m["z"] - canopy_z
            horiz = math.hypot(dx, dy)
            if horiz <= max(TORSO_W, TORSO_D) * 1.0 and abs(dz) <= 25 and m["vz"] < 0:
                continue

        dx = m["x"] - player_pos_meteor[0]; dy = m["y"] - player_pos_meteor[1]
        horiz = math.hypot(dx, dy)
        if horiz < (m["r"] + 15) and m["z"] <= 30:
            hit_count += 1
            energy -= 15
            score_meteor = max(0, score_meteor - 8)
            if hit_count >= MAX_HITS or energy <= 0:
                game_over_meteor = True
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
            intensity = min(1.0, 0.5 + (level*0.04))
            glColor3f(1.0, intensity*0.6, intensity*0.1)
            glutSolidSphere(m["r"], 14, 14)
        glPopMatrix()

def get_gun_tip_world():
    forward = TORSO_W * 0.6 + GUN_BODY_L + GUN_BARREL_L * 0.5
    up = TORSO_H * 0.72
    gx = player_pos_meteor[0] + forward * math.cos(math.radians(gun_angle))
    gy = player_pos_meteor[1] + forward * math.sin(math.radians(gun_angle))
    gz = player_pos_meteor[2] + up
    return gx, gy, gz

def fire_bullet_meteor():
    global last_shot_time_meteor
    if game_over_meteor: return
    now = glutGet(GLUT_ELAPSED_TIME)
    if now - last_shot_time_meteor < BULLET_COOLDOWN_MS_METEOR:
        return
    last_shot_time_meteor = now
    vx = math.cos(math.radians(gun_angle)) * BULLET_SPEED_METEOR
    vy = math.sin(math.radians(gun_angle)) * BULLET_SPEED_METEOR
    gun_x, gun_y, gun_z = get_gun_tip_world()
    bullets_meteor.append({'pos':[gun_x, gun_y, gun_z], 'vel':[vx,vy,0.0], 'active':True})

def update_bullets_meteor():
    global bullets_meteor, missed_bullets, game_over_meteor
    new_bullets = []
    for b in bullets_meteor:
        b['pos'][0] += b['vel'][0] * (FRAME_DT*60.0)
        b['pos'][1] += b['vel'][1] * (FRAME_DT*60.0)
        
        # Check if bullet has gone too far and is considered "missed"
        dist_from_origin = math.hypot(b['pos'][0], b['pos'][1])
        if dist_from_origin > SURFACE_RADIUS + 800:
            missed_bullets += 1
            if missed_bullets >= MAX_MISSED_BULLETS:
                game_over_meteor = True
            continue
        
        # Check for collision with meteors
        collided = False
        for m in meteors:
            if not m["is_hit"]:
                dx = m["x"] - b['pos'][0]
                dy = m["y"] - b['pos'][1]
                dz = m["z"] - b['pos'][2]
                dist3 = math.sqrt(dx*dx + dy*dy + dz*dz)
                if dist3 <= m["r"] + 3.0:
                    collided = True
                    break
        
        if not collided:
            new_bullets.append(b)
    
    bullets_meteor = new_bullets


def draw_bullet_meteor(b):
    glPushMatrix()
    glTranslatef(b['pos'][0], b['pos'][1], b['pos'][2])
    glColor3f(1.0, 0.6, 0.1)
    glutSolidSphere(BULLET_SIZE_METEOR*0.25, 8, 8)
    glPopMatrix()

def find_nearest_meteor():
    if not meteors: return None
    px,py,pz = player_pos_meteor
    nearest = None; md = float('inf')
    for m in meteors:
        if m["is_hit"]: continue
        dx = m["x"]-px; dy = m["y"]-py; dz = m["z"]-pz
        d = math.sqrt(dx*dx + dy*dy + dz*dz)
        if d < md:
            md = d; nearest = m
    return nearest

def target_and_destroy_meteor():
    global score_meteor, energy
    t = find_nearest_meteor()
    if t is None: return False
    t["is_hit"] = True
    t["hit_timer"] = 0.0
    score_meteor += TARGET_SCORE
    energy = min(max_energy, energy + ENERGY_RESTORE)
    return True

def setup_camera_meteor():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(110, WIDTH/float(HEIGHT), 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person_mode:
        eye_x = player_pos_meteor[0] + 8.0*math.cos(math.radians(gun_angle))
        eye_y = player_pos_meteor[1] + 8.0*math.sin(math.radians(gun_angle))
        eye_z = player_pos_meteor[2] + TORSO_H * 0.92
        at_x = eye_x + 200.0 * math.cos(math.radians(gun_angle))
        at_y = eye_y + 200.0 * math.sin(math.radians(gun_angle))
        at_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z, at_x, at_y, at_z, 0, 0, 1)
    else:
        x, y, z = camera_pos_meteor
        gluLookAt(x, y, z, 0.0, 0.0, SURFACE_RADIUS*0.18, 0, 0, 1)

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

def get_level_name(lvl):
    if lvl <= 2: return 'EASY'
    if lvl <= 5: return 'MEDIUM'
    if lvl <= 8: return 'HARD'
    return 'EXTREME'

def draw_hud_meteor():
    lives_left = max(0, MAX_HITS - hit_count)
    level_name = get_level_name(level)
    draw_text(18, HEIGHT - 40, f"SCORE:{score_meteor:04d}   LEVEL:{level}({level_name})   LIVES:{lives_left}")
    e_int = max(0, int(energy))
    energy_percent = energy / max_energy if max_energy > 0 else 0
    energy_color = (1.0,1.0,1.0) if energy_percent>0.5 else (1.0,0.6,0.4) if energy_percent>0.2 else (1.0,0.3,0.3)
    draw_text(18, HEIGHT - 64, f"ENERGY:{e_int:03d}", rgb=energy_color)
    draw_text(18, HEIGHT - 88, f"MISSED BULLETS: {missed_bullets} / {MAX_MISSED_BULLETS}", rgb=(1.0, 0.3, 0.3))
    next_level = level * SCORE_PER_LEVEL
    remaining = next_level - score_meteor
    if remaining > 0:
        draw_text(18, HEIGHT - 112, f"Next Level: {remaining} pts", rgb=(0.8,0.8,0.8))
    if umbrella_active:
        draw_text(WIDTH - 240, HEIGHT - 40, "☂ UMBRELLA ACTIVE", rgb=(0.95,0.95,0.2))

def update_umbrella_energy():
    global energy, game_over_meteor
    if umbrella_active:
        energy -= umbrella_energy_cost
        if energy <= 0:
            energy = 0
            game_over_meteor = True

def check_level_progression():
    global level, storm_intensity
    target_score = level * SCORE_PER_LEVEL
    if score_meteor >= target_score:
        level += 1
        storm_intensity = 1.0
        return True
    return False

def idle_meteor():
    global last_spawn_time
    if game_over_meteor:
        glutPostRedisplay()
        return
    now = time.time()
    if not hasattr(idle_meteor, 'next_spawn_interval'):
        idle_meteor.next_spawn_interval = calculate_dynamic_spawn_interval(level)
    if now - last_spawn_time >= idle_meteor.next_spawn_interval:
        spawn_meteor_storm()
        last_spawn_time = now
        idle_meteor.next_spawn_interval = calculate_dynamic_spawn_interval(level)
    update_bullets_meteor()
    update_meteors_and_collisions()
    update_umbrella_energy()
    check_level_progression()
    glutPostRedisplay()
    time.sleep(max(0.0, FRAME_DT - 0.002))

def draw_game_over_meteor():
    draw_text(WIDTH/2 - 120, HEIGHT/2 + 20, "GAME OVER - You Died!", rgb=(1,0.3,0.3))
    draw_text(WIDTH/2 - 140, HEIGHT/2 - 10, f"Final Score: {score_meteor} | Level: {level}", rgb=(1,1,1), font=GLUT_BITMAP_HELVETICA_12)
    draw_text(WIDTH/2 - 90, HEIGHT/2 - 40, "Press ENTER to restart", rgb=(0.9,0.9,0.9), font=GLUT_BITMAP_HELVETICA_12)

def show_screen_meteor():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glClearColor(0.01, 0.01, 0.03, 1)
    setup_camera_meteor()
    draw_stars(stars_meteor)
    draw_moon(craters_meteor)
    draw_meteors()
    for b in bullets_meteor:
        draw_bullet_meteor(b)
    
    if game_over_meteor:
        draw_dead_player_meteor()
    else:
        draw_player_meteor()
    
    draw_targeting_reticle()
    draw_hud_meteor()
    
    if game_over_meteor:
        draw_game_over_meteor()
    
    glutSwapBuffers()

def restart_meteor():
    global energy, max_energy, score_meteor, level, game_over_meteor, meteors, bullets_meteor, player_pos_meteor, gun_angle, hit_count, umbrella_active, storm_intensity, last_spawn_time, missed_bullets
    energy = 100.0
    max_energy = 100.0
    score_meteor = 0
    level = 1
    game_over_meteor = False
    meteors = []
    bullets_meteor = []
    player_pos_meteor = [0.0, 0.0, SURFACE_RADIUS + 20.0]
    gun_angle = 45.0
    hit_count = 0
    umbrella_active = False
    storm_intensity = 1.0
    missed_bullets = 0
    last_spawn_time = time.time()
    if hasattr(idle_meteor, 'next_spawn_interval'):
        delattr(idle_meteor, 'next_spawn_interval')
    init_craters(craters_meteor)

# =========================
# Main Menu & Controller
# =========================

def draw_menu():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glClearColor(0.0, 0.0, 0.0, 1.0)
    
    draw_text(WIDTH / 2 - 200, HEIGHT / 2 + 100, "LUNARIS: The Last Outpost", font=GLUT_BITMAP_HELVETICA_18)
    draw_text(WIDTH / 2 - 150, HEIGHT / 2 + 20, "1. Alien Shooter", font=GLUT_BITMAP_HELVETICA_12)
    draw_text(WIDTH / 2 - 150, HEIGHT / 2 - 10, "2. Meteor Shooter", font=GLUT_BITMAP_HELVETICA_12)
    draw_text(WIDTH / 2 - 150, HEIGHT / 2 - 40, "Press a number to select", font=GLUT_BITMAP_HELVETICA_12)
    
    glutSwapBuffers()

def show_screen():
    if current_mode == MODE_MENU:
        draw_menu()
    elif current_mode == MODE_ALIEN_SHOOTER:
        show_screen_alien()
    elif current_mode == MODE_METEOR_SHOOTER:
        show_screen_meteor()

def idle():
    if current_mode == MODE_ALIEN_SHOOTER:
        idle_alien()
    elif current_mode == MODE_METEOR_SHOOTER:
        idle_meteor()
    else:
        glutPostRedisplay()

def keyboard_listener_main(key, x, y):
    global current_mode, is_paused_alien, player_pos_alien, player_angle_alien, game_over_alien
    global gun_angle, player_pos_meteor, umbrella_active, last_target_time, game_over_meteor

    # 'x' key to switch between modes
    if key == b'x' or key == b'X':
        if current_mode == MODE_ALIEN_SHOOTER:
            current_mode = MODE_METEOR_SHOOTER
            restart_meteor()
        elif current_mode == MODE_METEOR_SHOOTER:
            current_mode = MODE_ALIEN_SHOOTER
            restart_alien()
        else: # From menu to alien shooter
            current_mode = MODE_ALIEN_SHOOTER
            restart_alien()
        glutDisplayFunc(show_screen)
        glutIdleFunc(idle)
        glutPostRedisplay()
        return

    # Menu key handlers
    if current_mode == MODE_MENU:
        if key == b'1':
            current_mode = MODE_ALIEN_SHOOTER
            restart_alien()
            glutDisplayFunc(show_screen)
            glutIdleFunc(idle)
        elif key == b'2':
            current_mode = MODE_METEOR_SHOOTER
            restart_meteor()
            glutDisplayFunc(show_screen)
            glutIdleFunc(idle)
        elif key == b'\x1b':
            glutLeaveMainLoop()
        glutPostRedisplay()
        return
    
    # Alien Shooter key handlers
    if current_mode == MODE_ALIEN_SHOOTER:
        moon_radius = SURFACE_RADIUS
        player_height = 4 

        angle_rad = math.radians(player_angle_alien)
        
        forward_x = math.cos(angle_rad)
        forward_y = math.sin(angle_rad)
        
        right_x = math.cos(angle_rad - math.pi / 2)
        right_y = math.sin(angle_rad - math.pi / 2)
        left_x = math.cos(angle_rad + math.pi / 2)
        left_y = math.sin(angle_rad + math.pi / 2)

        new_x = player_pos_alien[0]
        new_y = player_pos_alien[1]

        if key == b'w':
            new_x += forward_x * PLAYER_SPEED_ALIEN
            new_y += forward_y * PLAYER_SPEED_ALIEN
        elif key == b's':
            new_x -= forward_x * PLAYER_SPEED_ALIEN
            new_y -= forward_y * PLAYER_SPEED_ALIEN
        elif key == b'e':
            new_x += right_x * PLAYER_SPEED_ALIEN
            new_y += right_y * PLAYER_SPEED_ALIEN
        elif key == b'f':
            new_x += left_x * PLAYER_SPEED_ALIEN
            new_y += left_y * PLAYER_SPEED_ALIEN
        elif key == b'p' or key == b'P':
            is_paused_alien = not is_paused_alien
        elif key == b'r' or key == b'R':
            restart_alien()
        elif key == b'n' or key == b'N':
            player_angle_alien = (player_angle_alien + 30) % 360
        elif key == b'm' or key == b'M':
            activate_shield()
        
        if new_x != player_pos_alien[0] or new_y != player_pos_alien[1]:
            new_dist_xy = math.hypot(new_x, new_y)
            if new_dist_xy < moon_radius - 20:
                player_pos_alien[0] = new_x
                player_pos_alien[1] = new_y
                player_pos_alien[2] = math.sqrt(moon_radius**2 - new_dist_xy**2) + player_height
        glutPostRedisplay()

    # Meteor Shooter key handlers
    elif current_mode == MODE_METEOR_SHOOTER:
        if game_over_meteor and key not in (b'\r', b'\x1b'):
            return
        if key == b'a':
            gun_angle = (gun_angle + 6) % 360
        elif key == b'd':
            gun_angle = (gun_angle - 6) % 360
        elif key == b'w':
            nx = player_pos_meteor[0] + math.cos(math.radians(gun_angle)) * PLAYER_SPEED_METEOR
            ny = player_pos_meteor[1] + math.sin(math.radians(gun_angle)) * PLAYER_SPEED_METEOR
            if math.hypot(nx, ny) <= SURFACE_RADIUS - 18:
                player_pos_meteor[0], player_pos_meteor[1] = nx, ny
        elif key == b's':
            nx = player_pos_meteor[0] - math.cos(math.radians(gun_angle)) * PLAYER_SPEED_METEOR
            ny = player_pos_meteor[1] - math.sin(math.radians(gun_angle)) * PLAYER_SPEED_METEOR
            if math.hypot(nx, ny) <= SURFACE_RADIUS - 18:
                player_pos_meteor[0], player_pos_meteor[1] = nx, ny
        elif key == b'u':
            umbrella_active = not umbrella_active
        elif key == b' ':
            now = time.time()
            if now - last_target_time >= TARGET_COOLDOWN:
                target_and_destroy_meteor()
                last_target_time = now
        elif key == b'\r' and game_over_meteor:
            restart_meteor()
            
    if key == b'\x1b':
        glutLeaveMainLoop()
    glutPostRedisplay()

def special_key_listener_main(key, x, y):
    global camera_angle_alien, camera_height_alien, camera_radius_alien, player_pos_alien
    global camera_angle_meteor, camera_height_meteor, camera_pos_meteor, camera_radius_meteor

    if current_mode == MODE_ALIEN_SHOOTER:
        if key == GLUT_KEY_UP:
            camera_radius_alien = max(5.0, camera_radius_alien - 20.0)
            camera_height_alien = max(5.0, camera_height_alien - 5.0)
        elif key == GLUT_KEY_DOWN:
            camera_radius_alien = min(1500.0, camera_radius_alien + 20.0)
            camera_height_alien = min(600.0, camera_height_alien + 5.0)
        elif key == GLUT_KEY_LEFT:
            camera_angle_alien = (camera_angle_alien + 5.0) % 360.0
        elif key == GLUT_KEY_RIGHT:
            camera_angle_alien = (camera_angle_alien - 5.0) % 360.0
        
    elif current_mode == MODE_METEOR_SHOOTER:
        if key == GLUT_KEY_UP:
            camera_height_meteor = min(900.0, camera_height_meteor + 20.0)
        elif key == GLUT_KEY_DOWN:
            camera_height_meteor = max(120.0, camera_height_meteor - 20.0)
        elif key == GLUT_KEY_LEFT:
            camera_angle_meteor = (camera_angle_meteor + 4.0) % 360.0
        elif key == GLUT_KEY_RIGHT:
            camera_angle_meteor = (camera_angle_meteor - 4.0) % 360.0
        dist = camera_radius_meteor
        camera_pos_meteor[0] = dist * math.cos(math.radians(camera_angle_meteor))
        camera_pos_meteor[1] = dist * math.sin(math.radians(camera_angle_meteor))
        camera_pos_meteor[2] = camera_height_meteor
    glutPostRedisplay()

def mouse_listener_main(button, state, x, y):
    global is_firing_alien, first_person_mode, game_over_meteor

    if current_mode == MODE_ALIEN_SHOOTER:
        if button == GLUT_RIGHT_BUTTON:
            is_firing_alien = (state == GLUT_DOWN)
    elif current_mode == MODE_METEOR_SHOOTER:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over_meteor:
            fire_bullet_meteor()
        elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            first_person_mode = not first_person_mode

# =========================
# Main Loop
# =========================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"LUNARIS: The Last Outpost")
    glEnable(GL_DEPTH_TEST)
    
    init_craters(craters_alien)
    generate_stars(NUM_STARS_ALIEN, stars_alien)
    init_craters(craters_meteor)
    generate_stars(NUM_STARS_METEOR, stars_meteor)
    
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_listener_main)
    glutSpecialFunc(special_key_listener_main)
    glutMouseFunc(mouse_listener_main)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()