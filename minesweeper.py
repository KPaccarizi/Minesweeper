from tkinter import *
from tkinter import messagebox as tkMessageBox
from collections import deque
import random
import platform
from datetime import datetime

SIZE_X = 15
SIZE_Y = 15

STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

BTN_CLICK = "<Button-1>"
BTN_FLAG = "<Button-2>" if platform.system() == 'Darwin' else "<Button-3>"

class Minesweeper:
    def __init__(self, tk):
        self.tk = tk
        self.images = {
            "plain": PhotoImage(file="images/tile_plain.gif"),
            "clicked": PhotoImage(file="images/tile_clicked.gif"),
            "mine": PhotoImage(file="images/tile_mine.gif"),
            "flag": PhotoImage(file="images/tile_flag.gif"),
            "wrong": PhotoImage(file="images/tile_wrong.gif"),
            "numbers": [PhotoImage(file=f"images/tile_{i}.gif") for i in range(1, 9)]
        }
        
        self.setup_ui()
        self.restart()
        self.update_timer()

    def setup_ui(self):
        self.frame = Frame(self.tk)
        self.frame.pack()
        
        self.labels = {
            "time": Label(self.frame, text="00:00:00"),
            "mines": Label(self.frame, text="Mines: 0"),
            "flags": Label(self.frame, text="Flags: 0")
        }
        self.labels["time"].grid(row=0, column=0, columnspan=SIZE_Y) 
        self.labels["mines"].grid(row=SIZE_X+1, column=0, columnspan=int(SIZE_Y/2)) 
        self.labels["flags"].grid(row=SIZE_X+1, column=int(SIZE_Y/2)-1, columnspan=int(SIZE_Y/2)) 

    def setup_game(self):
        self.flagCount = 0
        self.correctFlagCount = 0
        self.clickedCount = 0
        self.startTime = None

        self.tiles = {}
        self.mines = 0
        for x in range(SIZE_X):
            self.tiles[x] = {}
            for y in range(SIZE_Y):
                id = f"{x}_{y}"
                isMine = random.uniform(0.0, 1.0) < 0.1
                gfx = self.images["plain"]

                tile = {
                    "id": id,
                    "isMine": isMine,
                    "state": STATE_DEFAULT,
                    "coords": {"x": x, "y": y},
                    "button": Button(self.frame, image=gfx),
                    "mines": 0
                }

                tile["button"].bind(BTN_CLICK, self.on_click_wrapper(x, y))
                tile["button"].bind(BTN_FLAG, self.on_right_click_wrapper(x, y))
                tile["button"].grid(row=x+1, column=y)
                
                self.tiles[x][y] = tile

        for x in range(SIZE_X):
            for y in range(SIZE_Y):
                mc = sum(1 for n in self.get_neighbors(x, y) if n["isMine"])
                self.tiles[x][y]["mines"] = mc

    def restart(self):
        self.setup_game()
        self.refresh_labels()

    def refresh_labels(self):
        self.labels["flags"].config(text=f"Flags: {self.flagCount}")
        self.labels["mines"].config(text=f"Mines: {self.mines}")

    def game_over(self, won):
        for x in range(SIZE_X):
            for y in range(SIZE_Y):
                if not self.tiles[x][y]["isMine"] and self.tiles[x][y]["state"] == STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image=self.images["wrong"])
                if self.tiles[x][y]["isMine"] and self.tiles[x][y]["state"] != STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image=self.images["mine"])

        self.tk.update()
        msg = "You Win! Play again?" if won else "You Lose! Play again?"
        res = tkMessageBox.askyesno("Game Over", msg)
        if res:
            self.restart()
        else:
            self.tk.quit()

    def update_timer(self):
        ts = "00:00:00"
        if self.startTime:
            delta = datetime.now() - self.startTime
            ts = str(delta).split('.')[0]
            if delta.total_seconds() < 36000:
                ts = "0" + ts
        self.labels["time"].config(text=ts)
        self.frame.after(100, self.update_timer)

    def get_neighbors(self, x, y):
        neighbors = []
        coords = [
            {"x": x-1, "y": y-1}, {"x": x-1, "y": y}, {"x": x-1, "y": y+1},
            {"x": x,   "y": y-1},                 {"x": x,   "y": y+1},
            {"x": x+1, "y": y-1}, {"x": x+1, "y": y}, {"x": x+1, "y": y+1}
        ]
        for n in coords:
            try:
                neighbors.append(self.tiles[n["x"]][n["y"]])
            except KeyError:
                pass
        return neighbors

    def on_click_wrapper(self, x, y):
        return lambda Button: self.on_click(self.tiles[x][y])

    def on_right_click_wrapper(self, x, y):
        return lambda Button: self.on_right_click(self.tiles[x][y])

    def on_click(self, tile):
        if not self.startTime:
            self.startTime = datetime.now()

        if tile["isMine"]:
            self.game_over(False)
            return

        if tile["mines"] == 0:
            tile["button"].config(image=self.images["clicked"])
            self.clear_surrounding_tiles(tile["id"])
        else:
            tile["button"].config(image=self.images["numbers"][tile["mines"]-1])

        if tile["state"] != STATE_CLICKED:
            tile["state"] = STATE_CLICKED
            self.clickedCount += 1
        if self.clickedCount == (SIZE_X * SIZE_Y) - self.mines:
            self.game_over(True)

    def on_right_click(self, tile):
        if not self.startTime:
            self.startTime = datetime.now()

        if tile["state"] == STATE_DEFAULT:
            tile["button"].config(image=self.images["flag"])
            tile["state"] = STATE_FLAGGED
            tile["button"].unbind(BTN_CLICK)

            if tile["isMine"]:
                self.correctFlagCount += 1
            self.flagCount += 1
            self.refresh_labels()

        elif tile["state"] == STATE_FLAGGED:
            tile["button"].config(image=self.images["plain"])
            tile["state"] = STATE_DEFAULT
            tile["button"].bind(BTN_CLICK, self.on_click_wrapper(tile["coords"]["x"], tile["coords"]["y"]))

            if tile["isMine"]:
                self.correctFlagCount -= 1
            self.flagCount -= 1
            self.refresh_labels()

    def clear_surrounding_tiles(self, id):
        queue = deque([id])

        while queue:
            key = queue.popleft()
            x, y = map(int, key.split("_"))

            for tile in self.get_neighbors(x, y):
                if tile["state"] == STATE_DEFAULT:
                    if tile["mines"] == 0:
                        tile["button"].config(image=self.images["clicked"])
                        queue.append(tile["id"])
                    else:
                        tile["button"].config(image=self.images["numbers"][tile["mines"]-1])

                tile["state"] = STATE_CLICKED
                self.clickedCount += 1


def main():
    window = Tk()
    window.title("Minesweeper")
    minesweeper = Minesweeper(window)
    window.mainloop()

if __name__ == "__main__":
    main()

