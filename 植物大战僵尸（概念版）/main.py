import tkinter as tk
from PIL import Image, ImageTk  # 需导入PIL库处理图片
import json


class GameCollection:
    def __init__(self, root):
        self.root = root
        self.root.title("植物大战僵尸(概念版）")
        self.root.geometry("800x600")
        self.scores = self._load_scores()
        self.current_user = None
        self.current_game = None

        # 框架布局：左侧菜单 + 右侧游戏容器（包含背景图）
        self.menu_frame = tk.Frame(root, width=200, bg="#f0f0f0")
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.game_container = tk.Frame(root, bg="white")
        self.game_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 加载并设置背景图片
        self._set_background_image(r"D:\python\project\植物大战僵尸（概念版）\01.jpg")

        # 菜单按钮
        tk.Button(self.menu_frame, text="简单",
                  command=lambda: self._load_game("game1")).pack(pady=70)
        tk.Button(self.menu_frame, text="中等",
                  command=lambda: self._load_game("game2")).pack(pady=70)
        tk.Button(self.menu_frame, text="困难",
                  command=lambda: self._load_game("game3")).pack(pady=70)
        tk.Button(self.menu_frame, text="排行榜",
                  command=self._show_ranking).pack(pady=10)
        tk.Button(self.menu_frame, text="登录/注册",
                  command=self._show_login).pack(pady=10)

    def _set_background_image(self, img_path):
        """在游戏容器中设置背景图片"""
        try:
            # 打开图片并调整尺寸以适应容器
            image = Image.open(img_path)
            image = image.resize((800, 600), Image.LANCZOS)  # 右侧容器宽度约600，高度600
            photo = ImageTk.PhotoImage(image)

            # 创建标签并设置为背景
            bg_label = tk.Label(self.game_container, image=photo)
            bg_label.image = photo  # 保持引用，防止被垃圾回收
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # 铺满容器
        except Exception as e:
            print(f"加载背景图失败：{e}")

    def _load_game(self, game_module_name):
        """根据模块名加载对应小游戏"""
        for widget in self.game_container.winfo_children():
            if widget.winfo_class() != "Label":  # 保留背景标签，销毁其他组件
                widget.destroy()
        if game_module_name == "game1":
            from game1 import GameModule as CurrentGame
        elif game_module_name == "game2":
            from game2 import GameModule as CurrentGame
        elif game_module_name == "game3":
            from game3 import GameModule as CurrentGame
        self.current_game = CurrentGame(self.game_container, self._update_score)
        self.current_game.start_game()

    def _update_score(self, score):
        if self.current_user:
            game_name = self.current_game.__class__.__name__
            if self.current_user not in self.scores:
                self.scores[self.current_user] = {}
            self.scores[self.current_user][game_name] = score
            self._save_scores()

    def _load_scores(self):
        try:
            with open("scores.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_scores(self):
        with open("scores.json", "w", encoding="utf-8") as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)

    def _show_ranking(self):
        rank_win = tk.Toplevel(self.root)
        rank_win.title("排行榜")
        rank_win.geometry("400x300")
        tk.Label(rank_win, text="游戏排行榜", font=("Arial", 16)).pack(pady=10)
        for user, games in self.scores.items():
            tk.Label(rank_win, text=f"{user}: {games}").pack()

    def _show_login(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("登录/注册")
        login_win.geometry("300x200")
        tk.Label(login_win, text="用户名：").grid(row=0, column=0, pady=10, padx=10)
        username = tk.Entry(login_win)
        username.grid(row=0, column=1, pady=10)
        tk.Button(login_win, text="登录",
                  command=lambda: self._set_user(username.get())).grid(row=1, column=0, pady=10)
        tk.Button(login_win, text="注册",
                  command=lambda: self._set_user(username.get())).grid(row=1, column=1, pady=10)

    def _set_user(self, username):
        self.current_user = username
        self.root.title(f"植物大战僵尸 - {username}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameCollection(root)
    root.mainloop()