import tkinter as tk
import random
import time

class GameModule:
    # ============================== 初始化与窗口适配 ==============================
    def __init__(self, parent_frame, on_score_update):
        """
        类初始化：初始化游戏核心变量、布局常量，适配窗口尺寸
        :param parent_frame: 父容器（主程序传递的游戏区域框架）
        :param on_score_update: 得分同步回调函数（对接主程序存储得分）
        """
        # 核心状态变量
        self.parent_frame = parent_frame  # 父容器，用于挂载UI组件
        self.on_score_update = on_score_update  # 得分同步接口
        self.score = 0  # 当前游戏得分
        self.game_running = False  # 游戏运行状态（True=运行，False=暂停/结束）
        self.sunshine = 5000  # 初始阳光（用于种植植物）
        self.selected_plant = None  # 当前选中的植物（None=未选中）
        self.using_shovel = False  # 是否处于铲子模式（True=可铲植物）
        self.original_geometry = parent_frame.master.geometry()  # 原始窗口尺寸（重置时恢复）
        self.sunshine_timer = None  # 自动增加阳光的定时器ID

        # 游戏元素列表（存储所有动态元素的属性）
        self.zombies = []  # 僵尸列表：每个元素是字典（含id、位置、血量、速度等）
        self.plants = []  # 植物列表：每个元素是字典（含类型、位置、冷却时间等）
        self.weed_whackers = []  # 除草机列表：每个元素是字典（含id、行、使用状态等）

        # 统一布局常量（控制植物/僵尸/除草机中心对齐）
        self.grid_start_y = 40  # 植物网格起始Y坐标（左上角）
        self.grid_height = 80  # 单个植物网格高度
        self.grid_row_spacing = self.grid_height + 30  # 植物网格行间距（80+30=110）
        self.grid_width = 100  # 单个植物网格宽度
        self.grid_col_spacing = self.grid_width + 50  # 植物网格列间距

        # 植物被吃时间配置（秒）
        self.plant_eat_time = {1: 1, 2: 2, 3: 8, 4: 3, 5: 2, 6: 2, 7: 3, 8: 1, 9: 1, 10: 1}
        # 土豆地雷成长时间
        self.potato_mine_arm_time = 10
        # 毁灭菇爆炸倒计时
        self.destroy_time = 3
        # 火爆辣椒燃烧倒计时
        self.chili_burn_time = 3

        # 僵尸吃植物速度
        self.zombie_eat_speed = 0.05

        # 扩大游戏窗口（适配画布和控件）
        parent_frame.master.geometry("1000x700")
        # 初始化UI组件
        self.create_game_ui()

    # ============================== UI组件创建 ==============================
    def create_game_ui(self):
        """创建所有UI组件：标题、主容器、信息区、游戏区、控制区"""
        # 1. 游戏标题
        title_label = tk.Label(
            self.parent_frame,
            text="植物大战僵尸（概念版）",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)

        # 2. 主容器
        main_container = tk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 3. 左侧信息区
        self._create_info_area(main_container)
        # 4. 右侧游戏区
        self._create_game_area(main_container)
        # 5. 底部控制区
        self._create_control_area()

    def _create_info_area(self, parent):
        """创建左侧信息区"""
        info_frame = tk.Frame(parent, width=200)
        info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        info_frame.pack_propagate(False)

        # 阳光显示
        self.sunshine_label = tk.Label(
            info_frame,
            text=f"阳光: {self.sunshine}",
            font=("Arial", 14),
            fg="#FFD700",
            bg="#333",
            pady=5
        )
        self.sunshine_label.pack(fill=tk.X, pady=5)

        # 铲子按钮
        self.shovel_button = tk.Button(
            info_frame,
            text="铲子（点击铲植物）",
            command=self.toggle_shovel_mode,
            font=("Arial", 11),
            bg="#F0E68C",
            relief=tk.RIDGE
        )
        self.shovel_button.pack(fill=tk.X, pady=8, padx=5)

        # 植物选择按钮
        plant_buttons = [
            ("向日葵 (50阳光)", 1, 50),
            ("豌豆射手 (100阳光)", 2, 100),
            ("坚果墙 (50阳光)", 3, 50),
            ("寒冰射手 (150阳光)", 4, 150),
            ("双向豌豆 (125阳光)", 5, 125),
            ("双发豌豆 (200阳光)", 6, 200),
            ("机枪射手 (250阳光)", 7, 250),
            ("土豆地雷 (25阳光)", 8, 25),
            ("毁灭菇 (300阳光)", 9, 300),
            ("火爆辣椒 (150阳光)", 10, 150)
        ]
        self.plant_buttons = []
        for text, plant_type, cost in plant_buttons:
            btn = tk.Button(
                info_frame,
                text=text,
                command=lambda t=plant_type, c=cost: self.select_plant(t, c),
                font=("Arial", 11),
                bg="#90EE90",
                relief=tk.RIDGE
            )
            btn.pack(fill=tk.X, pady=3, padx=5)
            self.plant_buttons.append((btn, cost, plant_type))
            self.parent_frame.after(100, lambda b=btn, c=cost: self.check_sunshine(b, c))

        # 得分显示
        self.score_label = tk.Label(
            info_frame,
            text=f"当前得分: {self.score}",
            font=("Arial", 14),
            bg="#000",
            fg="#FFF",
            pady=5
        )
        self.score_label.pack(fill=tk.X, pady=10, side=tk.BOTTOM)

    def _create_game_area(self, parent):
        """创建右侧游戏区"""
        right_container = tk.Frame(parent)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 游戏画布
        self.canvas = tk.Canvas(right_container, width=800, height=500, bg="#228B22")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 绘制静态元素
        self.draw_room()
        self.plot_grids()
        self.draw_weed_whackers()

        # 结果提示
        self.result_label = tk.Label(
            right_container,
            text="点击植物按钮后选择种植位置",
            font=("Arial", 14),
            fg="#FF0000"
        )
        self.result_label.pack(pady=10)

        # 爆炸效果覆盖层
        self.explosion_overlay = self.canvas.create_rectangle(
            0, 0, 800, 500,
            fill="#FF4500",
            stipple="gray50",
            state=tk.HIDDEN
        )

    def _create_control_area(self):
        """创建底部控制区"""
        control_frame = tk.Frame(self.parent_frame)
        control_frame.pack(pady=10)

        self.start_button = tk.Button(
            control_frame,
            text="开始游戏",
            command=self.start_game,
            font=("Arial", 14),
            width=10,
            bg="#FF6347"
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(
            control_frame,
            text="暂停游戏",
            command=self.pause_game,
            font=("Arial", 14),
            width=10,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = tk.Button(
            control_frame,
            text="重置游戏",
            command=self.reset_game,
            font=("Arial", 14),
            width=10,
            bg="#1E90FF"
        )
        self.reset_button.pack(side=tk.LEFT, padx=10)

    # ============================== 游戏核心逻辑：植物系统 ==============================
    def plot_grids(self):
        """绘制植物种植网格"""
        self.grids = []
        start_x = 150
        for row in range(5):
            for col in range(6):
                x1 = start_x + col * self.grid_col_spacing
                y1 = self.grid_start_y + row * self.grid_row_spacing
                x2 = x1 + self.grid_width
                y2 = y1 + self.grid_height
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#90EE90",
                    width=2,
                    fill="#32CD32"
                )
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                self.grids.append((center_x, center_y, row, col))

    def toggle_shovel_mode(self):
        """切换铲子模式"""
        self.using_shovel = not self.using_shovel
        if self.using_shovel:
            self.shovel_button.config(bg="#FF6347", text="铲子模式（点击铲除）")
            self.result_label.config(text="铲子已激活，请点击要铲除的植物！")
            for btn, _, _ in self.plant_buttons:
                btn.config(state=tk.DISABLED, bg="#D3D3D3")
            self.canvas.bind("<Button-1>", self.shovel_plant)
        else:
            self.shovel_button.config(bg="#F0E68C", text="铲子（点击铲植物）")
            self.result_label.config(text="铲子已关闭，请选择植物种植")
            for btn, cost, _ in self.plant_buttons:
                self.check_sunshine(btn, cost)
            self.canvas.unbind("<Button-1>")
            if self.selected_plant:
                self.canvas.bind("<Button-1>", self.place_plant)

    def shovel_plant(self, event):
        """铲掉植物"""
        click_x, click_y = event.x, event.y
        target_plant = self._find_closest_plant(click_x, click_y)
        if not target_plant:
            self.result_label.config(text="未找到植物，请点击网格内的植物！")
            return

        self.canvas.delete(target_plant["id"])
        self.canvas.delete(target_plant["text"])
        if "countdown_text" in target_plant:
            self.canvas.delete(target_plant["countdown_text"])
        self.plants.remove(target_plant)
        self.result_label.config(text=f"{self._get_plant_name(target_plant['type'])}已铲除！")

    def _find_closest_plant(self, x, y):
        """找到最近的植物"""
        closest_plant = None
        min_distance = float("inf")
        for plant in self.plants:
            distance = (x - plant["x"]) ** 2 + (y - plant["y"]) ** 2
            if distance < min_distance and distance < 50 ** 2:
                min_distance = distance
                closest_plant = plant
        return closest_plant

    def _get_plant_name(self, plant_type):
        """根据ID获取植物名称"""
        plant_names = {1: "向日葵", 2: "豌豆射手", 3: "坚果墙", 4: "寒冰射手", 5: "双向豌豆射手",
                       6: "双发豌豆射手", 7: "机枪射手", 8: "土豆地雷", 9: "毁灭菇", 10: "火爆辣椒"}
        return plant_names.get(plant_type, "植物")

    def select_plant(self, plant_type, cost):
        """选中植物"""
        if not self.game_running:
            self.result_label.config(text="请先点击【开始游戏】！")
            return
        if self.sunshine < cost:
            self.result_label.config(text=f"阳光不足！需要{cost}阳光")
            return

        self.selected_plant = (plant_type, cost)
        self.result_label.config(text=f"请选择种植位置（剩余阳光：{self.sunshine - cost}）")
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", self.place_plant)

    def place_plant(self, event):
        """种植植物"""
        click_x, click_y = event.x, event.y
        target_grid = self._find_closest_grid(click_x, click_y)
        if not target_grid:
            self.result_label.config(text="请点击标绿的种植区域！")
            return
        if self._is_grid_occupied(target_grid):
            self.result_label.config(text="该位置已种植植物，请选择其他位置！")
            return

        center_x, center_y, row, col = target_grid
        plant_type, cost = self.selected_plant

        self.sunshine -= cost
        self.sunshine_label.config(text=f"阳光: {self.sunshine}")
        self._draw_plant(plant_type, center_x, center_y, row, col)

        self.canvas.unbind("<Button-1>")
        self.selected_plant = None
        self.result_label.config(text="植物种植成功！")

    def _find_closest_grid(self, x, y):
        """找到最近的网格"""
        closest_grid = None
        min_distance = float("inf")
        for (cx, cy, row, col) in self.grids:
            distance = (x - cx) ** 2 + (y - cy) ** 2
            if distance < min_distance and distance < 50 ** 2:
                min_distance = distance
                closest_grid = (cx, cy, row, col)
        return closest_grid

    def _is_grid_occupied(self, grid):
        """判断网格是否被占用"""
        center_x, center_y, _, _ = grid
        for plant in self.plants:
            if plant["x"] == center_x and plant["y"] == center_y:
                return True
        return False

    def _draw_plant(self, plant_type, cx, cy, row, col):
        """绘制植物"""
        if plant_type == 1:  # 向日葵
            plant_id = self.canvas.create_oval(cx - 25, cy - 25, cx + 25, cy + 25, fill="#FFD700")
            plant_text = self.canvas.create_text(cx, cy, text="向", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 1, "x": cx, "y": cy, "row": row, "col": col,
                "last_produce": time.time(), "health": 10,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 2:  # 豌豆射手
            plant_id = self.canvas.create_rectangle(cx - 25, cy - 25, cx + 25, cy + 25, fill="#90EE90")
            plant_text = self.canvas.create_text(cx, cy, text="豌", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 2, "x": cx, "y": cy, "row": row, "col": col,
                "last_shot": time.time(), "health": 20,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 3:  # 坚果墙
            plant_id = self.canvas.create_rectangle(cx - 30, cy - 30, cx + 30, cy + 30, fill="#DEB887")
            plant_text = self.canvas.create_text(cx, cy, text="坚", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 3, "x": cx, "y": cy, "row": row, "col": col,
                "health": 900, "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 4:  # 寒冰射手
            plant_id = self.canvas.create_rectangle(cx - 25, cy - 25, cx + 25, cy + 25, fill="#87CEEB")
            plant_text = self.canvas.create_text(cx, cy, text="寒", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 4, "x": cx, "y": cy, "row": row, "col": col,
                "last_shot": time.time(), "health": 30,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 5:  # 双向豌豆
            plant_id = self.canvas.create_rectangle(cx - 25, cy - 25, cx + 25, cy + 25, fill="#006400")
            plant_text = self.canvas.create_text(cx, cy, text="双", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 5, "x": cx, "y": cy, "row": row, "col": col,
                "last_shot": time.time(), "health": 20,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0,
                "target_right": None, "target_left": None
            })
        elif plant_type == 6:  # 双发豌豆
            plant_id = self.canvas.create_rectangle(cx - 25, cy - 25, cx + 25, cy + 25, fill="#90EE90")
            plant_text = self.canvas.create_text(cx, cy, text="双", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 6, "x": cx, "y": cy, "row": row, "col": col,
                "last_shot": time.time(), "health": 25,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 7:  # 机枪射手
            plant_id = self.canvas.create_rectangle(cx - 25, cy - 25, cx + 25, cy + 25, fill="#90EE90")
            plant_text = self.canvas.create_text(cx, cy, text="机", font=("Arial", 16, "bold"))
            self.plants.append({
                "type": 7, "x": cx, "y": cy, "row": row, "col": col,
                "last_shot": time.time(), "health": 25,
                "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0
            })
        elif plant_type == 8:  # 土豆地雷
            points = [cx, cy - 20, cx - 25, cy + 20, cx + 25, cy + 20]
            plant_id = self.canvas.create_polygon(points, fill="#D2B48C")
            plant_text = self.canvas.create_text(cx, cy + 5, text="", font=("Arial", 14, "bold"))
            self.plants.append({
                "type": 8, "x": cx, "y": cy, "row": row, "col": col,
                "health": 10, "id": plant_id, "text": plant_text,
                "being_eaten": False, "eat_timer": 0,
                "is_armed": False, "arm_start_time": time.time()
            })
        elif plant_type == 9:  # 毁灭菇
            plant_id = self.canvas.create_oval(cx - 25, cy - 25, cx + 25, cy + 25, fill="#000000")
            plant_text = self.canvas.create_text(cx, cy, text="毁", font=("Arial", 16, "bold"), fill="white")
            countdown_text = self.canvas.create_text(cx, cy + 40, text=str(self.destroy_time), font=("Arial", 16, "bold"), fill="red")
            self.plants.append({
                "type": 9, "x": cx, "y": cy, "row": row, "col": col, "health": 10,
                "id": plant_id, "text": plant_text, "countdown_text": countdown_text,
                "is_boom": False, "boom_start_time": time.time(),
                "being_eaten": False, "eat_timer": 0,
            })
        elif plant_type == 10:  # 火爆辣椒
            plant_id = self.canvas.create_oval(cx - 25, cy - 25, cx + 25, cy + 25, fill="#FF4500")
            plant_text = self.canvas.create_text(cx, cy, text="辣", font=("Arial", 16, "bold"), fill="white")
            countdown_text = self.canvas.create_text(cx, cy + 40, text=str(self.chili_burn_time), font=("Arial", 16, "bold"), fill="red")
            self.plants.append({
                "type": 10, "x": cx, "y": cy, "row": row, "col": col, "health": 10,
                "id": plant_id, "text": plant_text, "countdown_text": countdown_text,
                "is_burn": False, "burn_start_time": time.time(),
                "being_eaten": False, "eat_timer": 0,
            })

    # ============================== 游戏核心逻辑：僵尸系统 ==============================
    def spawn_zombie(self):
        """生成僵尸"""
        if not self.game_running:
            return

        row = random.randint(0, 4)
        zombie_type = random.choices(["normal", "cone", "bucket"], weights=[5, 3, 2], k=1)[0]
        zombie_center_y = self.grid_start_y + row * self.grid_row_spacing + self.grid_height // 2
        zombie_x1 = 950
        zombie_y1 = zombie_center_y - 25
        zombie_x2 = 990
        zombie_y2 = zombie_center_y + 25
        zombie_color = {"normal": "#A0522D", "cone": "#FF4500", "bucket": "#708090"}[zombie_type]
        zombie_id = self.canvas.create_rectangle(zombie_x1, zombie_y1, zombie_x2, zombie_y2, fill=zombie_color)
        zombie_text = self.canvas.create_text((zombie_x1 + zombie_x2) // 2, zombie_center_y, text="僵",
                                              font=("Arial", 14))

        self.zombies.append({
            "id": zombie_id, "type": zombie_type, "x": (zombie_x1 + zombie_x2) // 2, "y": zombie_center_y,
            "row": row, "health": {"normal": 100, "cone": 180, "bucket": 250}[zombie_type],
            "speed": {"normal": 6.0, "cone": 3, "bucket": 2.6}[zombie_type],
            "is_slowed": False, "slow_end": 0, "text": zombie_text, "target_plant": None
        })



        next_spawn_time = random.randint(50, 500)
        self.parent_frame.after(next_spawn_time, self.spawn_zombie)

    def zombie_behavior(self, current_time):
        """僵尸行为"""
        for zombie in list(self.zombies):
            zombie_speed = self.get_zombie_speed(zombie, current_time)

            if not zombie["target_plant"] or zombie["target_plant"] not in self.plants:
                zombie["target_plant"] = self._find_closest_plant_in_row(zombie["row"], zombie["x"])

            mine_collision = self._check_zombie_mine_collision(zombie)
            if mine_collision:
                continue

            if zombie["target_plant"]:
                target_plant = zombie["target_plant"]
                distance = target_plant["x"] - zombie["x"]
                if distance > 30:
                    self._move_zombie(zombie, zombie_speed)
                else:
                    self._zombie_eat_plant(zombie, target_plant)
                    if target_plant["eat_timer"] >= self.plant_eat_time[target_plant["type"]]:
                        self._destroy_plant(target_plant)
                        zombie["target_plant"] = None
            else:
                self._move_zombie(zombie, zombie_speed)

            if 50 < zombie["x"] <= 70:
                self.trigger_weed_whacker(zombie["row"])
                break

            if zombie["x"] <= 50:
                self.game_over()
                return

    def _check_zombie_mine_collision(self, zombie):
        """检查僵尸是否踩到土豆地雷"""
        for plant in list(self.plants):
            if plant["type"] == 8 and plant["row"] == zombie["row"]:
                if abs(zombie["x"] - plant["x"]) < 30:
                    if plant["is_armed"]:
                        self.result_label.config(text="土豆地雷爆炸！")
                        self._destroy_plant(plant)
                        if zombie in self.zombies:
                            self.canvas.delete(zombie["id"])
                            self.canvas.delete(zombie["text"])
                            self.zombies.remove(zombie)
                            score_map = {"normal": 50, "cone": 100, "bucket": 150}
                            self.score += score_map[zombie["type"]]
                            self.score_label.config(text=f"当前得分: {self.score}")
                            self.on_score_update(self.score)
                    else:
                        self.result_label.config(text="土豆地雷被踩掉了！")
                        self._destroy_plant(plant)
                    return True
        return False

    def _find_closest_plant_in_row(self, row, zombie_x):
        """找到行内最近的植物"""
        closest_plant = None
        min_distance = float("inf")
        for plant in self.plants:
            if plant["row"] == row and plant["x"] > zombie_x:
                distance = plant["x"] - zombie_x
                if distance < min_distance:
                    min_distance = distance
                    closest_plant = plant
        return closest_plant

    def _move_zombie(self, zombie, speed):
        """移动僵尸"""
        self.canvas.move(zombie["id"], -speed, 0)
        self.canvas.move(zombie["text"], -speed, 0)
        zombie["x"] -= speed

    def _zombie_eat_plant(self, zombie, plant):
        """僵尸吃植物"""
        plant["being_eaten"] = True
        plant["eat_timer"] += self.zombie_eat_speed

    def _destroy_plant(self, plant):
        """销毁植物"""
        self.canvas.delete(plant["id"])
        self.canvas.delete(plant["text"])
        if "countdown_text" in plant:
            self.canvas.delete(plant["countdown_text"])
        if plant in self.plants:
            self.plants.remove(plant)

    def get_zombie_speed(self, zombie, current_time):
        """获取僵尸速度（考虑减速）"""
        base_speed = zombie["speed"]
        if zombie["is_slowed"] and current_time < zombie["slow_end"]:
            return base_speed * 0.5
        return base_speed

    # ============================== 游戏核心逻辑：战斗系统 ==============================
    def shoot_pea(self, plant, target_zombie, direction=1):
        """发射豌豆"""
        pea_color = "#00FF00" if plant["type"] != 4 else "#87CEEB"
        pea_radius = 5
        pea_y = plant["y"]

        if direction == 1:
            pea_id = self.canvas.create_oval(
                plant["x"] + 25, pea_y - pea_radius,
                plant["x"] + 25 + 2 * pea_radius, pea_y + pea_radius,
                fill=pea_color
            )
        else:
            pea_id = self.canvas.create_oval(
                plant["x"] - 25 - 2 * pea_radius, pea_y - pea_radius,
                plant["x"] - 25, pea_y + pea_radius,
                fill=pea_color
            )

        def move_pea():
            if not self.game_running or target_zombie not in self.zombies:
                self.canvas.delete(pea_id)
                return

            self.canvas.move(pea_id, 5 * direction, 0)
            pea_coords = self.canvas.coords(pea_id)

            if direction == 1 and pea_coords[2] >= target_zombie["x"] - 20:
                self.canvas.delete(pea_id)
                self.hit_zombie(plant, target_zombie)
                return
            if direction == -1 and pea_coords[0] <= target_zombie["x"] + 20:
                self.canvas.delete(pea_id)
                self.hit_zombie(plant, target_zombie)
                return

            if pea_coords[0] < 0 or pea_coords[2] > 1000:
                self.canvas.delete(pea_id)
                return

            self.parent_frame.after(20, move_pea)

        move_pea()

    def hit_zombie(self, plant, target_zombie):
        """击中僵尸"""
        damage = 25 if plant["type"] != 4 else 20
        target_zombie["health"] -= damage

        if plant["type"] == 4:
            target_zombie["is_slowed"] = True
            target_zombie["slow_end"] = time.time() + 3

        if target_zombie["health"] <= 0:
            self.canvas.delete(target_zombie["id"])
            self.canvas.delete(target_zombie["text"])
            if target_zombie in self.zombies:
                self.zombies.remove(target_zombie)
            score_map = {"normal": 50, "cone": 100, "bucket": 150}
            self.score += score_map[target_zombie["type"]]
            self.score_label.config(text=f"当前得分: {self.score}")
            self.on_score_update(self.score)

    def plant_attack(self, current_time):
        """植物攻击"""
        for plant in self.plants:
            if plant["type"] in [2, 4, 5] and current_time - plant["last_shot"] >= 2:
                if plant["type"] == 5:
                    target_zombie_right = self.find_nearest_zombie(plant["row"], plant["x"])
                    target_zombie_left = self.find_nearest_zombie_left(plant["row"], plant["x"])
                    if target_zombie_right: self.shoot_pea(plant, target_zombie_right, 1)
                    if target_zombie_left: self.shoot_pea(plant, target_zombie_left, -1)
                    if target_zombie_right or target_zombie_left:
                        plant["last_shot"] = current_time
                else:
                    target_zombie = self.find_nearest_zombie(plant["row"], plant["x"])
                    if target_zombie:
                        self.shoot_pea(plant, target_zombie)
                        plant["last_shot"] = current_time
            elif plant["type"] == 6 and current_time - plant["last_shot"] >= 1:
                target_zombie = self.find_nearest_zombie(plant["row"], plant["x"])
                if target_zombie:
                    self.shoot_pea(plant, target_zombie)
                    plant["last_shot"] = current_time
            elif plant["type"] == 7 and current_time - plant["last_shot"] >= 0.2:
                target_zombie = self.find_nearest_zombie(plant["row"], plant["x"])
                if target_zombie:
                    self.shoot_pea(plant, target_zombie)
                    plant["last_shot"] = current_time

    def plant_arm(self, current_time):
        """土豆地雷武装"""
        for plant in self.plants:
            if plant["type"] == 8 and not plant["is_armed"]:
                if current_time - plant["arm_start_time"] >= self.potato_mine_arm_time:
                    plant["is_armed"] = True
                    self.canvas.itemconfig(plant["text"], text="雷", font=("Arial", 14, "bold"))

    def plant_boom(self, current_time):
        """毁灭菇爆炸倒计时与触发"""
        for plant in list(self.plants):
            if plant["type"] == 9 and not plant["is_boom"]:
                # 倒计时逻辑
                if not hasattr(plant, 'last_countdown_update'):
                    plant['last_countdown_update'] = current_time
                    plant['countdown'] = self.destroy_time

                time_since_last_update = current_time - plant['last_countdown_update']
                if time_since_last_update >= 1:
                    plant['countdown'] -= 1
                    plant['last_countdown_update'] = current_time
                    self.canvas.itemconfig(plant["countdown_text"], text=str(plant['countdown']))

                # 爆炸触发
                if current_time - plant["boom_start_time"] >= self.destroy_time:
                    self._doomshroom_explode(plant)

    def _doomshroom_explode(self, plant):
        """毁灭菇爆炸效果"""
        self.result_label.config(text="毁灭菇爆炸！清除所有僵尸！")
        self.canvas.itemconfig(self.explosion_overlay, state=tk.NORMAL)

        total_score = 0
        for zombie in list(self.zombies):
            score_map = {"normal": 50, "cone": 100, "bucket": 150}
            total_score += score_map[zombie["type"]]
            self.canvas.delete(zombie["id"])
            self.canvas.delete(zombie["text"])
            if zombie in self.zombies:
                self.zombies.remove(zombie)

        if total_score > 0:
            self.score += total_score
            self.score_label.config(text=f"当前得分: {self.score}")
            self.on_score_update(self.score)

        plant["is_boom"] = True
        self.parent_frame.after(1000, lambda: self.canvas.itemconfig(self.explosion_overlay, state=tk.HIDDEN))
        self.parent_frame.after(1000, lambda p=plant: self._destroy_plant(p))

    def plant_burn(self, current_time):
        """火爆辣椒燃烧倒计时与触发"""
        for plant in list(self.plants):
            if plant["type"] == 10 and not plant["is_burn"]:
                # 倒计时逻辑
                if not hasattr(plant, 'last_countdown_update'):
                    plant['last_countdown_update'] = current_time
                    plant['countdown'] = self.chili_burn_time

                time_since_last_update = current_time - plant['last_countdown_update']
                if time_since_last_update >= 1:
                    plant['countdown'] -= 1
                    plant['last_countdown_update'] = current_time
                    self.canvas.itemconfig(plant["countdown_text"], text=str(plant['countdown']))

                # 燃烧触发
                if current_time - plant["burn_start_time"] >= self.chili_burn_time:
                    self._chili_burn(plant)

    def _chili_burn(self, plant):
        """火爆辣椒燃烧效果"""
        burn_row = plant["row"]
        self.result_label.config(text=f"火爆辣椒燃烧！清除第{burn_row + 1}行僵尸！")

        flame_id = self.canvas.create_rectangle(
            0, self.grid_start_y + burn_row * self.grid_row_spacing,
            1000, self.grid_start_y + (burn_row + 1) * self.grid_row_spacing,
            fill="#FF4500", stipple="gray50", state=tk.NORMAL
        )

        total_score = 0
        for zombie in list(self.zombies):
            if zombie["row"] == burn_row:
                score_map = {"normal": 50, "cone": 100, "bucket": 150}
                total_score += score_map[zombie["type"]]
                self.canvas.delete(zombie["id"])
                self.canvas.delete(zombie["text"])
                if zombie in self.zombies:
                    self.zombies.remove(zombie)

        if total_score > 0:
            self.score += total_score
            self.score_label.config(text=f"当前得分: {self.score}")
            self.on_score_update(self.score)

        plant["is_burn"] = True
        self.parent_frame.after(1000, lambda: self.canvas.delete(flame_id))
        self.parent_frame.after(1000, lambda p=plant: self._destroy_plant(p))

    def find_nearest_zombie(self, row, plant_x):
        """找到右侧最近的僵尸"""
        nearest_zombie = None
        min_distance = float("inf")
        for zombie in self.zombies:
            if zombie["row"] == row and zombie["x"] > plant_x:
                distance = zombie["x"] - plant_x
                if distance < min_distance:
                    min_distance = distance
                    nearest_zombie = zombie
        return nearest_zombie

    def find_nearest_zombie_left(self, row, plant_x):
        """找到左侧最近的僵尸"""
        nearest_zombie = None
        min_distance = float("inf")
        for zombie in self.zombies:
            if zombie["row"] == row and zombie["x"] < plant_x:
                distance = plant_x - zombie["x"]
                if distance < min_distance:
                    min_distance = distance
                    nearest_zombie = zombie
        return nearest_zombie

    # ============================== 游戏核心逻辑：除草机系统 ==============================
    def draw_weed_whackers(self):
        """绘制除草机"""
        for row in range(5):
            whacker_center_y = self.grid_start_y + row * self.grid_row_spacing + self.grid_height // 2
            whacker_x1 = 50
            whacker_y1 = whacker_center_y - 20
            whacker_x2 = 90
            whacker_y2 = whacker_center_y + 20
            whacker_id = self.canvas.create_rectangle(
                whacker_x1, whacker_y1, whacker_x2, whacker_y2,
                fill="#FF4500", outline="#000", width=2
            )
            self.canvas.create_text(
                (whacker_x1 + whacker_x2) // 2, whacker_center_y,
                text="除", font=("Arial", 16, "bold"), fill="#FFF"
            )
            self.weed_whackers.append({"id": whacker_id, "row": row, "used": False})

    def trigger_weed_whacker(self, row):
        """触发除草机"""
        for whacker in self.weed_whackers:
            if whacker["row"] == row and not whacker["used"]:
                whacker["used"] = True
                self.canvas.itemconfig(whacker["id"], fill="#8B0000")
                self.result_label.config(text=f"第{row + 1}行除草机触发！")
                self._clear_zombies_in_row(row)
                break

    def _clear_zombies_in_row(self, row):
        """清除行内所有僵尸"""
        for zombie in list(self.zombies):
            if zombie["row"] == row:
                self.canvas.delete(zombie["id"])
                self.canvas.delete(zombie["text"])
                self.zombies.remove(zombie)

    # ============================== 游戏核心逻辑：阳光系统 ==============================
    def produce_sunshine(self, current_time):
        """向日葵生产阳光"""
        for plant in self.plants:
            if plant["type"] == 1 and current_time - plant["last_produce"] >= 3:
                self.sunshine += 25
                self.sunshine_label.config(text=f"阳光: {self.sunshine}")
                plant["last_produce"] = current_time
                self._draw_floating_sun(plant["x"], plant["y"])

    def _draw_floating_sun(self, x, y):
        """绘制浮动阳光"""
        sun_id = self.canvas.create_oval(x + 30, y - 20, x + 50, y, fill="#FFD700")
        self.canvas.move(sun_id, 0, -10)
        self.parent_frame.after(1000, lambda: self.canvas.delete(sun_id))

    def auto_add_sunshine(self):
        """自动增加阳光"""
        if self.game_running:
            self.sunshine += 25
            self.sunshine_label.config(text=f"阳光: {self.sunshine}")
            self.sunshine_timer = self.parent_frame.after(10000, self.auto_add_sunshine)

    # ============================== 交互与控制 ==============================
    def start_game(self):
        """开始游戏"""

        self.game_running = True
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.result_label.config(text="游戏开始！僵尸即将入侵！")
        self.plants.clear()
        self.parent_frame.after(10000, self.spawn_zombie)
        self.game_loop()
        self.sunshine_timer = self.parent_frame.after(10000, self.auto_add_sunshine)

    def pause_game(self):
        """暂停游戏"""
        self.game_running = False
        self.start_button.config(state=tk.NORMAL, text="继续游戏")
        self.pause_button.config(state=tk.DISABLED)
        self.result_label.config(text="游戏暂停！点击【继续游戏】恢复")
        if self.sunshine_timer:
            self.parent_frame.after_cancel(self.sunshine_timer)
            self.sunshine_timer = None

    def reset_game(self):
        """重置游戏"""
        self.game_running = False
        self.score = 0
        self.sunshine = 50
        self.selected_plant = None
        self.using_shovel = False

        for plant in self.plants:
            self.canvas.delete(plant["id"])
            self.canvas.delete(plant["text"])
            if "countdown_text" in plant:
                self.canvas.delete(plant["countdown_text"])

        for zombie in self.zombies:
            self.canvas.delete(zombie["id"])
            self.canvas.delete(zombie["text"])

        self.zombies.clear()
        self.plants.clear()
        self.weed_whackers.clear()

        if self.sunshine_timer:
            self.parent_frame.after_cancel(self.sunshine_timer)
            self.sunshine_timer = None

        self.score_label.config(text=f"当前得分: {self.score}")
        self.sunshine_label.config(text=f"阳光: {self.sunshine}")
        self.result_label.config(text="点击植物按钮后选择种植位置")
        self.start_button.config(state=tk.NORMAL, text="开始游戏")
        self.pause_button.config(state=tk.DISABLED)
        self.shovel_button.config(bg="#F0E68C", text="铲子（点击铲植物）")

        for btn, cost, _ in self.plant_buttons:
            btn.config(bg="#90EE90")
            self.check_sunshine(btn, cost)

        self.canvas.delete("all")
        self.draw_room()
        self.plot_grids()
        self.draw_weed_whackers()
        self.parent_frame.master.geometry(self.original_geometry)

    def game_loop(self):
        """游戏主循环"""
        if not self.game_running:
            return

        current_time = time.time()

        self.produce_sunshine(current_time)
        self.plant_attack(current_time)
        self.plant_arm(current_time)
        self.plant_boom(current_time)
        self.plant_burn(current_time)
        self.zombie_behavior(current_time)

        self.parent_frame.after(50, self.game_loop)

    def game_over(self):
        """游戏结束"""
        self.game_running = False
        self.result_label.config(text="僵尸吃掉了你的脑子！游戏结束！")
        self.score = 0
        self.score_label.config(text=f"当前得分: {self.score}")
        self.on_score_update(self.score)
        self.start_button.config(state=tk.NORMAL, text="重新开始")
        self.pause_button.config(state=tk.DISABLED)
        if self.sunshine_timer:
            self.parent_frame.after_cancel(self.sunshine_timer)
            self.sunshine_timer = None
        self.parent_frame.master.geometry(self.original_geometry)

    # ============================== 数据存储与接口 ==============================
    def check_sunshine(self, button, cost):
        """检查阳光并更新按钮状态"""
        if self.game_running and self.sunshine >= cost and not self.using_shovel:
            button.config(state=tk.NORMAL, bg="#90EE90")
        else:
            button.config(state=tk.DISABLED, bg="#D3D3D3")
        self.parent_frame.after(100, lambda b=button, c=cost: self.check_sunshine(b, c))

    def get_score(self):
        """获取当前得分"""
        return self.score

    def draw_room(self):
        """绘制房间和脑子"""
        room_height = self.grid_start_y + 5 * self.grid_row_spacing - 30
        self.canvas.create_rectangle(
            10, self.grid_start_y, 50, room_height,
            outline="#FF0000", width=3, fill="#8B4513"
        )
        self.canvas.create_text(30, self.grid_start_y + 2 * self.grid_row_spacing,
                                text="房间", font=("Arial", 16, "bold"), fill="#FFF")

        brain_y = room_height - 250
        self.brain_id = self.canvas.create_oval(20, brain_y - 15, 40, brain_y + 15, fill="#FFB6C1")
        self.canvas.create_text(30, brain_y, text="脑", font=("Arial", 12, "bold"), fill="#000")

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("植物大战僵尸（测试版）")

    def mock_update_score(score):
        print(f"当前得分：{score}")

    game = GameModule(root, mock_update_score)
    root.mainloop()