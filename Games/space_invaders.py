import tkinter as tk
import random

WIDTH, HEIGHT = 500, 600
SHIP_SPEED = 20
BULLET_SPEED = -10
ENEMY_SPEED = 5
ENEMY_DROP = 30

class SpaceInvaders:
    def __init__(self, root):
        self.root = root
        self.root.title("Space Invaders")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()

        # Player ship
        self.ship = self.canvas.create_rectangle(WIDTH//2 - 20, HEIGHT - 40,
                                                 WIDTH//2 + 20, HEIGHT - 20,
                                                 fill="cyan")

        self.bullets = []
        self.enemies = []
        self.enemy_dir = 1
        self.game_over = False

        # Bind controls
        root.bind("<Left>", self.move_left)
        root.bind("<Right>", self.move_right)
        root.bind("<space>", self.shoot)

        self.create_enemies()
        self.update_game()

    def create_enemies(self):
        rows, cols = 3, 6
        for r in range(rows):
            for c in range(cols):
                x = 60 + c * 70
                y = 50 + r * 50
                enemy = self.canvas.create_rectangle(x-20, y-20, x+20, y+20,
                                                     fill="red")
                self.enemies.append(enemy)

    def move_left(self, event):
        if not self.game_over:
            self.canvas.move(self.ship, -SHIP_SPEED, 0)

    def move_right(self, event):
        if not self.game_over:
            self.canvas.move(self.ship, SHIP_SPEED, 0)

    def shoot(self, event):
        if not self.game_over:
            x1, y1, x2, y2 = self.canvas.coords(self.ship)
            bullet = self.canvas.create_rectangle((x1+x2)//2 - 3, y1 - 10,
                                                  (x1+x2)//2 + 3, y1,
                                                  fill="yellow")
            self.bullets.append(bullet)

    def update_game(self):
        if self.game_over:
            return

        # Move bullets
        for b in self.bullets[:]:
            self.canvas.move(b, 0, BULLET_SPEED)
            if self.canvas.coords(b)[1] < 0:
                self.canvas.delete(b)
                self.bullets.remove(b)

        # Move enemies
        shift = ENEMY_SPEED * self.enemy_dir
        drop = False
        for e in self.enemies:
            self.canvas.move(e, shift, 0)
            x1, y1, x2, y2 = self.canvas.coords(e)
            if x1 <= 0 or x2 >= WIDTH:
                drop = True
        if drop:
            for e in self.enemies:
                self.canvas.move(e, 0, ENEMY_DROP)
            self.enemy_dir *= -1

        # Bullet-enemy collision
        for b in self.bullets[:]:
            bx1, by1, bx2, by2 = self.canvas.coords(b)
            for e in self.enemies[:]:
                ex1, ey1, ex2, ey2 = self.canvas.coords(e)
                if not (bx2 < ex1 or bx1 > ex2 or by2 < ey1 or by1 > ey2):
                    self.canvas.delete(b)
                    self.bullets.remove(b)
                    self.canvas.delete(e)
                    self.enemies.remove(e)
                    break

        # Enemy reaching ship
        sx1, sy1, sx2, sy2 = self.canvas.coords(self.ship)
        for e in self.enemies:
            ex1, ey1, ex2, ey2 = self.canvas.coords(e)
            if ey2 >= sy1:
                self.end_game("Game Over! Invaders reached you!")
                return

        # Win
        if not self.enemies:
            self.end_game("You win!")

        self.root.after(50, self.update_game)

    def end_game(self, msg):
        self.game_over = True
        self.canvas.create_text(WIDTH//2, HEIGHT//2, text=msg,
                                fill="white", font=("Arial", 20))

def main():
    root = tk.Tk()
    game = SpaceInvaders(root)
    root.mainloop()

if __name__ == "__main__":
    main()
