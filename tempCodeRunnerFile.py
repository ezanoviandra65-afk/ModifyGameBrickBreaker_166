import tkinter as tk


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

class Ball(GameObject):
    def __init__(self, canvas, x, y, speed=8):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = speed
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()

class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='yellow')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

class Brick(GameObject):
    COLORS = {1: '#e74c3c', 2: '#3498db', 3: '#222222'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])

class Game(tk.Frame):
    START_LIVES = 3
    POINTS_PER_HIT = 10
    PADDLE_STEP = 20

    def __init__(self, master):
        super(Game, self).__init__(master)
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#aaaaff',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        # Kontrol keyboard
        self.canvas.focus_set()
        for key in ('<Left>', '<a>', '<A>'):
            self.canvas.bind(key, lambda _: self.paddle.move(-self.PADDLE_STEP))
        for key in ('<Right>', '<d>', '<D>'):
            self.canvas.bind(key, lambda _: self.paddle.move(self.PADDLE_STEP))
        self.canvas.bind('<p>', lambda _: self.toggle_pause())
        self.canvas.bind('<P>', lambda _: self.toggle_pause())
        self.canvas.bind('<r>', lambda _: self.reset_game())
        self.canvas.bind('<R>', lambda _: self.reset_game())

        self.loop_id = None
        self.reset_game()

    # ---------- Persiapan game ----------
    def reset_game(self):
        """Mulai game dari awal (dipanggil saat pertama kali dan saat tekan R)."""
        if self.loop_id is not None:
            self.after_cancel(self.loop_id)
            self.loop_id = None
        self.canvas.delete('all')

        self.lives = self.START_LIVES
        self.score = 0
        self.level_speed = 8
        self.running = False
        self.paused = False
        self.items = {}
        self.ball = None
        self.hud = None
        self.score_hud = None

        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)   # baris hitam: 3 pukulan
            self.add_brick(x + 37.5, 70, 2)   # baris biru: 2 pukulan
            self.add_brick(x + 37.5, 90, 1)   # baris merah: 1 pukulan

        self.setup_game()

    def setup_game(self):
        self.running = False
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(300, 200, 'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310, self.level_speed)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    # ---------- Tampilan ----------
    def draw_text(self, x, y, text, size=40, tag=None):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font, tags=tag)

    def update_hud(self):
        lives_text = 'Lives: %s' % self.lives
        score_text = 'Score: %s' % self.score
        if self.hud is None:
            self.hud = self.draw_text(50, 20, lives_text, 15)
            self.score_hud = self.draw_text(self.width - 70, 20,
                                            score_text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=lives_text)
            self.canvas.itemconfig(self.score_hud, text=score_text)

    # ---------- Alur game ----------
    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.running = True
        self.game_loop()

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.draw_text(300, 200, 'Paused', tag='pause_text')
        else:
            self.canvas.delete('pause_text')

    def game_loop(self):
        if self.paused:
            self.loop_id = self.after(100, self.game_loop)
            return

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))

        if num_bricks == 0:
            self.running = False
            self.draw_text(300, 200, 'You win!')
            self.draw_text(300, 250, 'Press R to play again', 20)
        elif self.ball.get_position()[3] >= self.height:
            self.running = False
            self.lives -= 1
            self.update_hud()
            if self.lives <= 0:
                self.draw_text(300, 200, 'Game Over!')
                self.draw_text(300, 250, 'Press R to play again', 20)
            else:
                self.loop_id = self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.loop_id = self.after(30, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]

        # Tambah skor untuk setiap bata yang terkena
        bricks_hit = sum(1 for o in objects if isinstance(o, Brick))
        if bricks_hit:
            self.score += bricks_hit * self.POINTS_PER_HIT
            self.update_hud()

        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Brick Breaker')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()

