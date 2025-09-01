import pygame, random, sys
from collections import deque

# ----------------- Config -----------------
pygame.init()
WIDTH, HEIGHT = 600, 600
CELL = 20
COLS = WIDTH // CELL
ROWS = HEIGHT // CELL
FPS = 10

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Battle (Smarter AI)")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 22, bold=True)

# ----------------- Helpers -----------------
DIRS = [(1,0), (-1,0), (0,1), (0,-1)]

def in_bounds(pos):
    x,y = pos
    return 0 <= x < COLS and 0 <= y < ROWS

def add(a,b): return (a[0]+b[0], a[1]+b[1])

def neighbors(pos):
    for d in DIRS:
        np = (pos[0]+d[0], pos[1]+d[1])
        if in_bounds(np):
            yield np

def bfs_path(start, goal, blocked):
    """Return path list from start to goal (inclusive) or None if no path.
       blocked is a set of blocked coordinates."""
    if start == goal:
        return [start]
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        for d in DIRS:
            nxt = (cur[0]+d[0], cur[1]+d[1])
            if not in_bounds(nxt): 
                continue
            if nxt in blocked:
                continue
            if nxt in prev:
                continue
            prev[nxt] = cur
            if nxt == goal:
                # reconstruct
                path = [goal]
                p = cur
                while p is not None:
                    path.append(p)
                    p = prev[p]
                path.reverse()
                return path
            q.append(nxt)
    return None

def flood_fill_count(start, blocked):
    """Count reachable cells from start without stepping into 'blocked'."""
    if start in blocked: return 0
    q = deque([start])
    seen = {start}
    while q:
        cur = q.popleft()
        for n in neighbors(cur):
            if n in blocked or n in seen: continue
            seen.add(n)
            q.append(n)
    return len(seen)

# ----------------- Game objects -----------------
class Snake:
    def __init__(self, color, body, is_ai=False):
        self.color = color
        self.body = list(body)   # list of (x,y), head first
        self.dir = (1,0)
        self.is_ai = is_ai
        self.score = 0
        self.lives = 3

    def head(self): return self.body[0]

    def will_crash_at(self, move, other):
        nxt = (self.head()[0] + move[0], self.head()[1] + move[1])
        # boundary
        if not in_bounds(nxt):
            return True
        # self collision (allow tail because it will move unless eating)
        if nxt in self.body[:-1]:
            return True
        # other snake collision (treat other body except its tail as blocked)
        if nxt in other.body[:-1]:
            return True
        return False

    def move(self, grow=False):
        nxt = (self.head()[0] + self.dir[0], self.head()[1] + self.dir[1])
        self.body.insert(0, nxt)
        if not grow:
            self.body.pop()

    def set_dir(self, new_dir):
        # prevent reverse
        if (new_dir[0] == -self.dir[0] and new_dir[1] == -self.dir[1]):
            return
        self.dir = new_dir

    def draw(self, surf):
        for i,(x,y) in enumerate(self.body):
            rect = pygame.Rect(x*CELL, y*CELL, CELL, CELL)
            pygame.draw.rect(surf, self.color, rect)
            if i==0:
                pygame.draw.rect(surf, (255,255,255), rect, 2)

# ----------------- Game functions -----------------
def random_food(s1, s2):
    while True:
        pos = (random.randrange(COLS), random.randrange(ROWS))
        if pos not in s1.body and pos not in s2.body:
            return pos

def respawn(snake, start_pos):
    snake.body = [start_pos]
    snake.dir = (1,0)

# AI routine using BFS + flood-fill fallback
def ai_choose_direction(ai_snake, player_snake, food):
    head = ai_snake.head()

    # Build blocked set: treat both snakes' bodies as blocked except their tails
    blocked = set(ai_snake.body[:-1]) | set(player_snake.body[:-1])

    # Try BFS to food
    path = bfs_path(head, food, blocked)
    if path and len(path) >= 2:
        next_cell = path[1]
        desired = (next_cell[0]-head[0], next_cell[1]-head[1])
        # do not reverse
        if (desired[0] == -ai_snake.dir[0] and desired[1] == -ai_snake.dir[1]):
            # fallback to safe move
            pass
        else:
            return desired

    # No path or reversing — pick safe neighbor with largest reachable area,
    # prefer nearer to food when equal.
    candidates = []
    for d in DIRS:
        if (d[0] == -ai_snake.dir[0] and d[1] == -ai_snake.dir[1]):
            continue  # no reverse
        nxt = (head[0]+d[0], head[1]+d[1])
        if not in_bounds(nxt):
            continue
        if nxt in blocked:
            continue
        # measure reachable area from nxt
        # assume moving to nxt frees tail, so block sets use body[:-1]
        blocked_after = set(ai_snake.body[:-1]) | set(player_snake.body[:-1])
        # simulate that our head moves to nxt and tail moves forward (so remove last)
        # remove last segment from our blocked set (simulate tail moving)
        if ai_snake.body:
            blocked_after.discard(ai_snake.body[-1])
        # but add nxt as occupied
        blocked_after.add(nxt)
        area = flood_fill_count(nxt, blocked_after)
        dist_to_food = abs(nxt[0]-food[0]) + abs(nxt[1]-food[1])
        candidates.append((area, -dist_to_food, d))

    if candidates:
        # choose highest area then closer to food
        candidates.sort(reverse=True)
        return candidates[0][2]

    # As last resort, if no safe moves, keep current direction (may crash)
    return ai_snake.dir

# ----------------- Main game loop -----------------
def run():
    # initial snakes (start with a short body so game is engaging)
    player = Snake((0,200,0), [(5,5),(4,5),(3,5)], is_ai=False)
    ai = Snake((200,0,0), [(15,15),(14,15),(13,15)], is_ai=True)
    food = random_food(player, ai)

    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP: player.set_dir((0,-1))
                if ev.key == pygame.K_DOWN: player.set_dir((0,1))
                if ev.key == pygame.K_LEFT: player.set_dir((-1,0))
                if ev.key == pygame.K_RIGHT: player.set_dir((1,0))
                if ev.key == pygame.K_r:
                    return "restart"
                if ev.key == pygame.K_q:
                    pygame.quit(); sys.exit()

        # AI decision
        new_dir = ai_choose_direction(ai, player, food)
        ai.set_dir(new_dir)

        # Move snakes, check if they will eat food
        player_next = (player.head()[0] + player.dir[0], player.head()[1] + player.dir[1])
        ai_next = (ai.head()[0] + ai.dir[0], ai.head()[1] + ai.dir[1])

        player_eat = (player_next == food)
        ai_eat = (ai_next == food and not player_eat)  # if both move into food, player gets it (tie-break)

        player.move(grow=player_eat)
        ai.move(grow=ai_eat)

        if player_eat:
            player.score += 1
            food = random_food(player, ai)
        elif ai_eat:
            ai.score += 1
            food = random_food(player, ai)

        # Collision checks
        def check_crash(snk, other, start_pos):
            head = snk.head()
            # boundary
            if not in_bounds(head):
                snk.lives -= 1
                if snk.lives > 0:
                    respawn(snk, start_pos)
                    return False
                return True  # dead
            # self collision
            if head in snk.body[1:]:
                snk.lives -= 1
                if snk.lives > 0:
                    respawn(snk, start_pos)
                    return False
                return True
            # collision with other (if head collides with any of other's body)
            if head in other.body:
                snk.lives -= 1
                if snk.lives > 0:
                    respawn(snk, start_pos)
                    return False
                return True
            return False

        player_dead = check_crash(player, ai, (5,5))
        ai_dead     = check_crash(ai, player, (15,15))

        # If one side out of lives -> show result and allow restart or quit
        if player_dead or ai_dead:
            winner = "AI" if player_dead and not ai_dead else ("Player" if ai_dead and not player_dead else "Draw")
            # show game over screen
            screen.fill((0,0,0))
            msg = FONT.render(f"Game Over: {winner} wins!", True, (255,255,255))
            hint = FONT.render("Press R to Restart or Q to Quit", True, (200,200,200))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 30))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 10))
            pygame.display.flip()
            # wait for user action
            waiting = True
            while waiting:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_r:
                            return "restart"
                        if ev.key == pygame.K_q:
                            pygame.quit(); sys.exit()
                clock.tick(10)

        # Draw
        screen.fill((10,10,10))
        # grid (subtle)
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(screen, (20,20,20), (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(screen, (20,20,20), (0,y), (WIDTH,y))

        player.draw(screen)
        ai.draw(screen)

        # food
        pygame.draw.rect(screen, (255,255,0), (food[0]*CELL, food[1]*CELL, CELL, CELL))

        # HUD
        hud = FONT.render(f"Player: {player.score} (Lives {player.lives})  |  AI: {ai.score} (Lives {ai.lives})", True, (255,255,255))
        screen.blit(hud, (10,10))
        pygame.display.flip()

# run loop handles restart
while True:
    action = run()
    if action == "restart":
        continue
    else:
        break
