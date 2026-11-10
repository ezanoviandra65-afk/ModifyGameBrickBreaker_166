import math
import random
import tkinter as tk
 
# ---------------- Pengaturan ----------------
W, H = 640, 480
TOP = 36                      # batas atas area bermain (di bawah HUD)
PADDLE_Y = H - 48
PADDLE_W = 90
PADDLE_H = 12
BALL_R = 8
TRAIL_LEN = 6
FONT = 'Forte'
 
BG = '#0f1226'
HIT_COLORS = {1: '#ff6b6b', 2: '#4dabf7', 3: '#a78bfa'}
TRAIL_COLORS = ['#1d2240', '#262d52', '#323b6a', '#42508a', '#5a6cb0', '#7d90d8']
 
# kode: (warna, teks pop-up)
POWERUPS = {
    'W': ('#51cf66', 'WIDE PADDLE!'),
    'M': ('#ffa94d', 'MULTI BALL!'),
    'S': ('#22d3ee', 'SLOW BALL!'),
    'L': ('#f783ac', 'EXTRA LIFE!'),
}
 
 
# ---------------- Objek game ----------------
class Ball:
    def __init__(self, canvas, x, y, vx=0.0, vy=0.0):
        self.canvas = canvas
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.trail = []
        self.glow = canvas.create_oval(0, 0, 0, 0, fill='#3b4a8a',
                                       outline='', tags='ball')
        self.body = canvas.create_oval(0, 0, 0, 0, fill='white',
                                       outline='', tags='ball')
        self.draw()
 
    def draw(self, with_trail=False):
        c, r = self.canvas, BALL_R
        c.coords(self.glow, self.x - r - 4, self.y - r - 4,
                 self.x + r + 4, self.y + r + 4)
        c.coords(self.body, self.x - r, self.y - r,
                 self.x + r, self.y + r)
        if with_trail:
            tid = c.create_oval(0, 0, 0, 0, outline='', tags='trail')
            c.tag_lower(tid, self.glow)
            self.trail.append([tid, self.x, self.y])
            if len(self.trail) > TRAIL_LEN:
                c.delete(self.trail.pop(0)[0])
            n = len(self.trail)
            for i, (t, tx, ty) in enumerate(self.trail):
                s = r * (i + 1) / (n + 1)
                c.coords(t, tx - s, ty - s, tx + s, ty + s)
                c.itemconfig(t, fill=TRAIL_COLORS[i + TRAIL_LEN - n])
 
    def delete(self):
        self.canvas.delete(self.glow)
        self.canvas.delete(self.body)
        for t in self.trail:
            self.canvas.delete(t[0])
        self.trail = []
 
 
class Paddle:
    def __init__(self, canvas):
        self.canvas = canvas
        self.x = W / 2
        self.w = PADDLE_W
        self.id = canvas.create_rectangle(0, 0, 0, 0, fill='#ffd43b',
                                          outline='#f59f00', width=2,
                                          tags='paddle')
        self.draw()
 
    @property
    def x1(self):
        return self.x - self.w / 2
 
    @property
    def x2(self):
        return self.x + self.w / 2
 
    def set_x(self, x):
        half = self.w / 2
        self.x = max(half, min(W - half, x))
        self.draw()
 
    def set_width(self, w):
        self.w = w
        self.set_x(self.x)
 
    def draw(self):
        self.canvas.coords(self.id, self.x1, PADDLE_Y,
                           self.x2, PADDLE_Y + PADDLE_H)
 
 
class Brick:
    def __init__(self, canvas, x1, y1, x2, y2, hits):
        self.canvas = canvas
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.hits = hits
        self.max_hits = hits
        self.id = canvas.create_rectangle(x1, y1, x2, y2,
                                          fill=HIT_COLORS[hits],
                                          outline=BG, width=2,
                                          tags='brick')
        self.shine = canvas.create_rectangle(x1 + 4, y1 + 4, x2 - 4, y1 + 8,
                                             fill='white', outline='',
                                             stipple='gray50', tags='brick')
 
    def recolor(self):
        self.canvas.itemconfig(self.id, fill=HIT_COLORS[self.hits])
 
    def delete(self):
        self.canvas.delete(self.id)
        self.canvas.delete(self.shine)
 
 
class PowerUp:
    def __init__(self, canvas, x, y, kind):
        self.canvas = canvas
        self.x, self.y, self.kind = x, y, kind
        color = POWERUPS[kind][0]
        self.box = canvas.create_rectangle(x - 14, y - 10, x + 14, y + 10,
                                           fill=color, outline='white',
                                           width=2, tags='powerup')
        self.label = canvas.create_text(x, y, text=kind, fill='black',
                                        font=('Arial', 11, 'bold'),
                                        tags='powerup')
 
    def move(self, dy):
        self.y += dy
        self.canvas.move(self.box, 0, dy)
        self.canvas.move(self.label, 0, dy)
 
    def delete(self):
        self.canvas.delete(self.box)
        self.canvas.delete(self.label)
 
 
# ---------------- Game ----------------
class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.canvas = tk.Canvas(self, bg=BG, width=W, height=H,
                                highlightthickness=0)
        self.canvas.pack()
        self.pack()
 
        self.keys = {'left': False, 'right': False}
        self.best = 0
        self.frame = 0
        self.state = 'ready'
 
        self.draw_background()
        self.canvas.bind('<KeyPress>', self.on_key_down)
        self.canvas.bind('<KeyRelease>', self.on_key_up)
        self.canvas.bind('<Motion>', self.on_motion)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.focus_set()
 
        self.reset_game()
        self.tick()
 
    # ----- tampilan statis -----
    def draw_background(self):
        for _ in range(70):
            x, y = random.randint(0, W), random.randint(TOP, H)
            s = random.choice((1, 1, 2))
            shade = random.choice(('#242a52', '#2f3766', '#3b4580'))
            self.canvas.create_oval(x, y, x + s, y + s, fill=shade,
                                    outline='', tags='bg')
        self.canvas.create_line(0, TOP, W, TOP, fill='#323b6a', width=2,
                                tags='bg')
 
    def text(self, x, y, txt, size=30, fill='white', tag='msg', anchor='center'):
        return self.canvas.create_text(x, y, text=txt, fill=fill,
                                       font=(FONT, size), tags=tag,
                                       anchor=anchor)
 
    # ----- mulai / reset -----
    def reset_game(self):
        for tag in ('brick', 'ball', 'trail', 'paddle', 'powerup',
                    'particle', 'ui', 'msg', 'popup', 'status'):
            self.canvas.delete(tag)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.combo = 1
        self.bricks = []
        self.balls = []
        self.powerups = []
        self.particles = []
        self.popups = []
        self.wide_until = 0
        self.slow_until = 0
        self.paddle = Paddle(self.canvas)
        self.build_ui()
        self.build_level()
        self.enter_ready()
 
    def build_ui(self):
        self.lives_txt = self.text(12, TOP / 2, '', 15, tag='ui', anchor='w')
        self.level_txt = self.text(W / 2, TOP / 2, '', 15, tag='ui')
        self.score_txt = self.text(W - 12, TOP / 2, '', 15, tag='ui',
                                   anchor='e')
        self.status_txt = self.text(W / 2, H - 14, '', 11, fill='#8fa0cc',
                                    tag='status')
        self.update_hud()
 
    def update_hud(self):
        self.canvas.itemconfig(self.lives_txt, text='Lives: %d' % self.lives)
        combo = '   x%d' % self.combo if self.combo > 1 else ''
        self.canvas.itemconfig(self.level_txt,
                               text='Level %d%s' % (self.level, combo))
        self.canvas.itemconfig(self.score_txt, text='Score: %d' % self.score)
 
    def layout(self, level):
        """Pola bata per level: daftar (baris, kolom, jumlah_pukulan)."""
        cells = []
        pattern = (level - 1) % 4
        if pattern == 0:
            for r in range(4):
                for c in range(8):
                    cells.append((r, c, 2 if r == 0 else 1))
        elif pattern == 1:
            for r in range(5):
                for c in range(8):
                    if (r + c) % 2 == 0:
                        cells.append((r, c, 2 if r < 2 else 1))
        elif pattern == 2:
            for r in range(4):
                for c in range(r, 8 - r):
                    cells.append((r, c, 3 if r == 0 else (2 if r < 3 else 1)))
        else:
            hits = (3, 2, 2, 1, 1)
            for r in range(5):
                for c in range(8):
                    cells.append((r, c, hits[r]))
        extra = (level - 1) // 4
        return [(r, c, min(3, h + extra)) for r, c, h in cells]
 
    def build_level(self):
        for b in self.bricks:
            b.delete()
        self.bricks = []
        for r, c, hits in self.layout(self.level):
            x1 = 20 + c * 75
            y1 = 70 + r * 26
            self.bricks.append(Brick(self.canvas, x1, y1, x1 + 70, y1 + 22,
                                     hits))
 
    def enter_ready(self):
        self.state = 'ready'
        self.combo = 1
        for b in self.balls:
            b.delete()
        self.balls = []
        for p in self.powerups:
            p.delete()
        self.powerups = []
        self.wide_until = 0
        self.slow_until = 0
        self.paddle.set_width(PADDLE_W)
        self.canvas.delete('msg')
        ball = Ball(self.canvas, self.paddle.x, PADDLE_Y - BALL_R)
        self.balls.append(ball)
        self.text(W / 2, 300, 'Level %d' % self.level, 44)
        self.text(W / 2, 345, 'Space / klik untuk meluncurkan', 16,
                  fill='#8fa0cc')
        self.update_hud()
 
    def launch(self):
        if self.state != 'ready':
            return
        self.canvas.delete('msg')
        angle = math.radians(random.uniform(-20, 20))
        speed = self.current_speed()
        ball = self.balls[0]
        ball.vx = speed * math.sin(angle)
        ball.vy = -speed * math.cos(angle)
        self.state = 'playing'
 
    # ----- input -----
    def on_key_down(self, e):
        k = e.keysym.lower()
        if k in ('left', 'a'):
            self.keys['left'] = True
        elif k in ('right', 'd'):
            self.keys['right'] = True
        elif k == 'space':
            self.launch()
        elif k == 'p':
            self.toggle_pause()
        elif k == 'r':
            self.reset_game()
 
    def on_key_up(self, e):
        k = e.keysym.lower()
        if k in ('left', 'a'):
            self.keys['left'] = False
        elif k in ('right', 'd'):
            self.keys['right'] = False
 
    def on_motion(self, e):
        if self.state in ('ready', 'playing'):
            self.paddle.set_x(e.x)
 
    def on_click(self, e):
        self.canvas.focus_set()
        self.launch()
 
    def toggle_pause(self):
        if self.state == 'playing':
            self.state = 'paused'
            self.text(W / 2, 260, 'Paused', 44, tag='pause')
            self.text(W / 2, 305, 'Tekan P untuk lanjut', 16,
                      fill='#8fa0cc', tag='pause')
        elif self.state == 'paused':
            self.state = 'playing'
            self.canvas.delete('pause')
 
    # ----- fisika -----
    def current_speed(self):
        base = min(5.0 + 0.6 * (self.level - 1), 9.5)
        if self.frame < self.slow_until:
            base *= 0.65
        return base
 
    def normalize(self, b, target):
        sp = math.hypot(b.vx, b.vy) or 1.0
        k = target / sp
        b.vx *= k
        b.vy *= k
        min_vy = target * 0.3
        if abs(b.vy) < min_vy:
            b.vy = math.copysign(min_vy, b.vy if b.vy else -1)
            b.vx = math.copysign(math.sqrt(max(target ** 2 - b.vy ** 2, 0)),
                                 b.vx if b.vx else 1)
 
    def collide_walls(self, b):
        r = BALL_R
        if b.x - r <= 0:
            b.x = r
            b.vx = abs(b.vx)
        elif b.x + r >= W:
            b.x = W - r
            b.vx = -abs(b.vx)
        if b.y - r <= TOP:
            b.y = TOP + r
            b.vy = abs(b.vy)
 
    def collide_paddle(self, b, target):
        r, p = BALL_R, self.paddle
        if (b.vy > 0 and b.y + r >= PADDLE_Y
                and b.y <= PADDLE_Y + PADDLE_H / 2
                and p.x1 - r <= b.x <= p.x2 + r):
            off = max(-1.0, min(1.0, (b.x - p.x) / (p.w / 2)))
            ang = off * math.radians(62)
            b.vx = target * math.sin(ang)
            b.vy = -target * math.cos(ang)
            b.y = PADDLE_Y - r
            if self.combo != 1:
                self.combo = 1
                self.update_hud()
 
    def collide_bricks(self, b):
        r = BALL_R
        for br in self.bricks:
            if (br.x1 - r <= b.x <= br.x2 + r
                    and br.y1 - r <= b.y <= br.y2 + r):
                dl = b.x + r - br.x1
                dr = br.x2 - (b.x - r)
                dt = b.y + r - br.y1
                db = br.y2 - (b.y - r)
                m = min(dl, dr, dt, db)
                if m == dl:
                    b.x -= dl
                    b.vx = -abs(b.vx)
                elif m == dr:
                    b.x += dr
                    b.vx = abs(b.vx)
                elif m == dt:
                    b.y -= dt
                    b.vy = -abs(b.vy)
                else:
                    b.y += db
                    b.vy = abs(b.vy)
                self.hit_brick(br)
                break
 
    def hit_brick(self, br):
        br.hits -= 1
        if br.hits <= 0:
            self.score += 10 * br.max_hits * self.combo
            self.spawn_particles((br.x1 + br.x2) / 2, (br.y1 + br.y2) / 2,
                                 HIT_COLORS[br.max_hits])
            if random.random() < 0.18:
                self.powerups.append(PowerUp(self.canvas,
                                             (br.x1 + br.x2) / 2,
                                             (br.y1 + br.y2) / 2,
                                             random.choice('WMSL')))
            br.delete()
            self.bricks.remove(br)
        else:
            self.score += 5 * self.combo
            br.recolor()
        self.combo = min(self.combo + 1, 8)
        self.update_hud()
 
    # ----- efek -----
    def spawn_particles(self, x, y, color):
        for _ in range(10):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(1.5, 4.5)
            pid = self.canvas.create_rectangle(x, y, x + 4, y + 4,
                                               fill=color, outline='',
                                               tags='particle')
            self.particles.append([pid, x, y, math.cos(ang) * sp,
                                   math.sin(ang) * sp - 1, 28])
 
    def popup(self, txt, color):
        pid = self.text(self.paddle.x, PADDLE_Y - 30, txt, 16, fill=color,
                        tag='popup')
        self.popups.append([pid, 45])
 
    def update_effects(self):
        for p in self.particles[:]:
            p[1] += p[3]
            p[2] += p[4]
            p[4] += 0.18
            p[5] -= 1
            if p[5] <= 0:
                self.canvas.delete(p[0])
                self.particles.remove(p)
            else:
                self.canvas.coords(p[0], p[1], p[2], p[1] + 4, p[2] + 4)
        for p in self.popups[:]:
            self.canvas.move(p[0], 0, -1.2)
            p[1] -= 1
            if p[1] <= 0:
                self.canvas.delete(p[0])
                self.popups.remove(p)
 
    def update_status(self):
        parts = []
        if self.frame < self.wide_until:
            parts.append('WIDE %ds' % math.ceil((self.wide_until - self.frame) / 60))
        if self.frame < self.slow_until:
            parts.append('SLOW %ds' % math.ceil((self.slow_until - self.frame) / 60))
        self.canvas.itemconfig(self.status_txt, text='    '.join(parts))
 
    # ----- power-up -----
    def apply_powerup(self, kind):
        color, label = POWERUPS[kind]
        if kind == 'W':
            self.wide_until = self.frame + 600
            self.paddle.set_width(PADDLE_W * 1.6)
        elif kind == 'S':
            self.slow_until = self.frame + 480
        elif kind == 'M':
            for b in self.balls[:]:
                if len(self.balls) >= 6:
                    break
                for turn in (-0.45, 0.45):
                    c, s = math.cos(turn), math.sin(turn)
                    nb = Ball(self.canvas, b.x, b.y,
                              b.vx * c - b.vy * s, b.vx * s + b.vy * c)
                    self.balls.append(nb)
        elif kind == 'L':
            self.lives = min(self.lives + 1, 5)
        self.popup(label, color)
        self.update_hud()
 
    def update_powerups(self):
        p = self.paddle
        for pu in self.powerups[:]:
            pu.move(2.6)
            if (pu.y + 10 >= PADDLE_Y and pu.y - 10 <= PADDLE_Y + PADDLE_H
                    and p.x1 - 14 <= pu.x <= p.x2 + 14):
                self.apply_powerup(pu.kind)
                pu.delete()
                self.powerups.remove(pu)
            elif pu.y > H + 20:
                pu.delete()
                self.powerups.remove(pu)
 
    # ----- alur game -----
    def move_paddle_keys(self):
        dx = (self.keys['right'] - self.keys['left']) * 9
        if dx:
            self.paddle.set_x(self.paddle.x + dx)
 
    def update_ready(self):
        self.move_paddle_keys()
        b = self.balls[0]
        b.x = self.paddle.x
        b.y = PADDLE_Y - BALL_R
        b.draw()
 
    def update_playing(self):
        self.move_paddle_keys()
        if self.wide_until and self.frame >= self.wide_until:
            self.wide_until = 0
            self.paddle.set_width(PADDLE_W)
 
        target = self.current_speed()
        for b in self.balls[:]:
            b.x += b.vx
            b.y += b.vy
            self.collide_walls(b)
            self.collide_paddle(b, target)
            self.collide_bricks(b)
            self.normalize(b, target)
            b.draw(with_trail=True)
            if b.y - BALL_R > H:
                b.delete()
                self.balls.remove(b)
 
        self.update_powerups()
 
        if not self.balls:
            self.lose_life()
        elif not self.bricks:
            self.level_clear()
 
    def lose_life(self):
        self.lives -= 1
        self.combo = 1
        self.update_hud()
        if self.lives <= 0:
            self.game_over()
        else:
            self.enter_ready()
 
    def level_clear(self):
        self.state = 'levelup'
        bonus = 100 * self.level
        self.score += bonus
        for b in self.balls:
            b.delete()
        self.balls = []
        for p in self.powerups:
            p.delete()
        self.powerups = []
        self.update_hud()
        self.text(W / 2, 250, 'Level Clear!', 44)
        self.text(W / 2, 300, 'Bonus +%d' % bonus, 22, fill='#ffd43b')
        self.levelup_until = self.frame + 100
 
    def game_over(self):
        self.state = 'over'
        self.best = max(self.best, self.score)
        self.canvas.delete('msg')
        self.text(W / 2, 220, 'Game Over', 48, fill='#ff6b6b')
        self.text(W / 2, 275, 'Score: %d    Best: %d' % (self.score, self.best),
                  22)
        self.text(W / 2, 320, 'Tekan R untuk main lagi', 16, fill='#8fa0cc')
 
    def tick(self):
        self.frame += 1
        if self.state == 'ready':
            self.update_ready()
        elif self.state == 'playing':
            self.update_playing()
        elif self.state == 'levelup':
            if self.frame >= self.levelup_until:
                self.level += 1
                self.build_level()
                self.enter_ready()
        if self.state != 'paused':
            self.update_effects()
            self.update_status()
        self.after(16, self.tick)
 
 
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Brick Breaker')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()
