"""
game_dungeon.py — Multi-floor dungeon system for Terminal-RPG.

Features:
  • Multiple dungeon floors (up to 5) — enemies get harder each floor
  • Floor transitions via staircases (▼ go down, ▲ go up)
  • Teleport pads (T) return player to surface instantly
  • Floor boss encounters at the end of floors 3 and 5
  • Treasure rooms on every floor (★)
  • Integrates with game_enemies.generate_dungeon_enemy()
"""

import random, os, time
from game_term import C, W, H, div, clr, _pad
from game_lang import T, LANG

_R="\033[0m"; _B="\033[1m"
def _fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
_GOLD=_fg(255,215,0);  _WHITE=_fg(255,255,255); _DIM=_fg(100,100,100)
_GREEN=_fg(80,200,80); _RED=_fg(220,60,60);     _CYAN=_fg(80,220,220)
_YELL=_fg(240,200,60); _ORAN=_fg(220,140,40);   _PURP=_fg(180,80,220)

MAX_FLOORS = 5

# Tile legend
TILE_WALL    = "#"
TILE_FLOOR   = "."
TILE_ENTRY   = "E"   # entrance / exit to surface
TILE_STAIRS_D= "▼"   # go deeper
TILE_STAIRS_U= "▲"   # go back up
TILE_TELEPORT= "T"   # teleport to surface
TILE_CHEST   = "C"   # treasure chest
TILE_TRAP    = "!"   # damage trap

TILE_COLOURS = {
    TILE_WALL:    _fg(70,50,35),
    TILE_FLOOR:   _fg(50,40,30),
    TILE_ENTRY:   _fg(80,220,80),
    TILE_STAIRS_D:_fg(200,160,60),
    TILE_STAIRS_U:_fg(100,200,255),
    TILE_TELEPORT:_fg(180,80,220),
    TILE_CHEST:   _fg(255,215,0),
    TILE_TRAP:    _fg(220,60,60),
}

# Encounter chance per floor (increases)
ENCOUNTER_BASE = [0.08, 0.10, 0.13, 0.16, 0.20]
# Danger per floor
FLOOR_DANGER   = [1,    2,    3,    4,    5]
# Has a boss at end
BOSS_FLOORS    = {3, 5}


class DungeonFloor:
    W_MAP = 40
    H_MAP = 18

    def __init__(self, floor_num: int, dungeon_name: str):
        self.floor_num   = floor_num
        self.dungeon_name= dungeon_name
        self.grid        = [["#"]*self.W_MAP for _ in range(self.H_MAP)]
        self.px, self.py = 2, 2
        self.chests_opened = set()
        self.traps_triggered = set()
        self.boss_defeated = False
        self.msg         = ""
        self._generate()

    def _generate(self):
        """Carve a dungeon floor with rooms, corridors, and special tiles."""
        # Fill with walls first
        for y in range(self.H_MAP):
            for x in range(self.W_MAP):
                self.grid[y][x] = TILE_WALL

        # Carve rooms
        rooms = []
        for _ in range(random.randint(5, 9)):
            w = random.randint(4, 8)
            h = random.randint(3, 6)
            x = random.randint(1, self.W_MAP - w - 2)
            y = random.randint(1, self.H_MAP - h - 2)
            # Carve room
            for ry in range(y, y+h):
                for rx in range(x, x+w):
                    self.grid[ry][rx] = TILE_FLOOR
            rooms.append((x, y, w, h))

        # Connect rooms with corridors
        random.shuffle(rooms)
        for i in range(len(rooms)-1):
            ax = rooms[i][0] + rooms[i][2]//2
            ay = rooms[i][1] + rooms[i][3]//2
            bx = rooms[i+1][0] + rooms[i+1][2]//2
            by = rooms[i+1][1] + rooms[i+1][3]//2
            # Horizontal then vertical
            cx = min(ax, bx); ex = max(ax, bx)
            for x in range(cx, ex+1):
                if 0 < x < self.W_MAP-1:
                    self.grid[ay][x] = TILE_FLOOR
            cy = min(ay, by); ey = max(ay, by)
            for y in range(cy, ey+1):
                if 0 < y < self.H_MAP-1:
                    self.grid[y][bx] = TILE_FLOOR

        # Place player in first room
        r0 = rooms[0]
        self.px = r0[0] + r0[2]//2
        self.py = r0[1] + r0[3]//2

        # Entry/exit (floor 1 entry, all floors have stairs)
        if self.floor_num == 1:
            self.grid[self.py][self.px] = TILE_ENTRY  # start on entry
            # Surface exit nearby
            self.grid[self.py][max(1, self.px-1)] = TILE_ENTRY

        # Stairs down (unless last floor)
        if self.floor_num < MAX_FLOORS and len(rooms) > 1:
            last = rooms[-1]
            sx = last[0] + last[2]//2
            sy = last[1] + last[3]//2
            self.grid[sy][sx] = TILE_STAIRS_D

        # Stairs up (not on floor 1)
        if self.floor_num > 1 and len(rooms) > 1:
            second = rooms[1]
            self.grid[second[1]+1][second[0]+1] = TILE_STAIRS_U

        # Teleport pad (floors 2+, one per floor in a mid room)
        if self.floor_num >= 2 and len(rooms) >= 3:
            mid = rooms[len(rooms)//2]
            tx = mid[0] + mid[2]//2
            ty = mid[1] + mid[3]//2
            if self.grid[ty][tx] == TILE_FLOOR:
                self.grid[ty][tx] = TILE_TELEPORT

        # Chests — 2-4 per floor
        floor_tiles = [(x,y) for y in range(self.H_MAP) for x in range(self.W_MAP)
                       if self.grid[y][x] == TILE_FLOOR]
        random.shuffle(floor_tiles)
        n_chests = random.randint(2, 4)
        for x, y in floor_tiles[:n_chests]:
            self.grid[y][x] = TILE_CHEST

        # Traps — more on deeper floors
        n_traps = random.randint(1, self.floor_num + 1)
        for x, y in floor_tiles[n_chests:n_chests+n_traps]:
            self.grid[y][x] = TILE_TRAP

    def render(self, player, floor_enemies_killed, total_killed):
        clr()
        map_pad = " " * _pad()

        # Header
        depth_col = [_GREEN, _YELL, _ORAN, _RED, _PURP][self.floor_num-1]
        print(C(f"{depth_col}{_B}{self.dungeon_name}{_R}  {_DIM}Floor {self.floor_num}/{MAX_FLOORS}{_R}  "
                f"{_DIM}Enemies slain: {_GOLD}{floor_enemies_killed}{_R}"))

        # Player HP/MP bar
        hp_frac = player.hp / max(1, player.max_hp)
        hp_col  = _GREEN if hp_frac > .5 else _YELL if hp_frac > .25 else _RED
        mp_frac = player.mp / max(1, player.max_mp)
        mp_col  = _CYAN
        bar_w   = 12
        hp_fill = int(bar_w * hp_frac)
        mp_fill = int(bar_w * mp_frac)
        hp_bar  = f"{hp_col}{'█'*hp_fill}{_DIM}{'░'*(bar_w-hp_fill)}{_R}"
        mp_bar  = f"{mp_col}{'█'*mp_fill}{_DIM}{'░'*(bar_w-mp_fill)}{_R}"
        print(C(f"HP [{hp_bar}] {hp_col}{player.hp}/{player.max_hp}{_R}   "
                f"MP [{mp_bar}] {mp_col}{player.mp}/{player.max_mp}{_R}   "
                f"Gold: {_GOLD}{player.gold}{_R}"))

        print(C(f"{_DIM}{'─'*self.W_MAP}{_R}"))

        # Map rows
        for y in range(self.H_MAP):
            row = map_pad
            for x in range(self.W_MAP):
                if x == self.px and y == self.py:
                    row += f"{_RED}{_B}@{_R}"
                else:
                    ch  = self.grid[y][x]
                    col = TILE_COLOURS.get(ch, "")
                    # Opened chests show as floor
                    if ch == TILE_CHEST and (x, y) in self.chests_opened:
                        col = TILE_COLOURS[TILE_FLOOR]
                        ch  = "·"
                    # Triggered traps
                    if ch == TILE_TRAP and (x, y) in self.traps_triggered:
                        col = TILE_COLOURS[TILE_FLOOR]
                        ch  = "·"
                    row += f"{col}{ch}{_R}"
            print(row)

        print(C(f"{_DIM}{'─'*self.W_MAP}{_R}"))

        # Legend
        tc = TILE_COLOURS
        print(C(f"{_RED}@{_R}You  "
                f"{tc[TILE_ENTRY]}E{_R}Exit  "
                f"{tc[TILE_STAIRS_D]}▼{_R}Deeper  "
                f"{tc[TILE_STAIRS_U]}▲{_R}Shallower  "
                f"{tc[TILE_TELEPORT]}T{_R}Teleport  "
                f"{tc[TILE_CHEST]}C{_R}Chest  "
                f"{tc[TILE_TRAP]}!{_R}Trap"))

        if self.msg:
            print(C(f"\n{self.msg}"))

        # Controls
        _mhint = f"{_GOLD}WASD{_R}" if getattr(player,"movement_mode","wasd")=="wasd" else f"{_GOLD}Numpad{_R}"
        print(C(f"\n{_mhint}{_DIM}=move  {_R}"
                f"{_GOLD}[E]{_R}{_DIM}Use/Enter  {_R}"
                f"{_GOLD}[I]{_R}{_DIM}Bag  {_R}"
                f"{_GOLD}[C]{_R}{_DIM}Codex  {_R}"
                f"{_GOLD}[?]{_R}{_DIM}Help  {_R}"
                f"{_GOLD}[Q]{_R}{_DIM}Retreat{_R}"))

    def move(self, dx, dy):
        nx, ny = self.px + dx, self.py + dy
        if not (0 <= nx < self.W_MAP and 0 <= ny < self.H_MAP):
            return "blocked"
        ch = self.grid[ny][nx]
        if ch == TILE_WALL:
            return "blocked"
        self.px, self.py = nx, ny
        if ch == TILE_ENTRY:
            return "surface"
        if ch == TILE_STAIRS_D:
            return "stairs_down"
        if ch == TILE_STAIRS_U:
            return "stairs_up"
        if ch == TILE_TELEPORT:
            return "teleport"
        if ch == TILE_CHEST and (nx, ny) not in self.chests_opened:
            return "chest"
        if ch == TILE_TRAP and (nx, ny) not in self.traps_triggered:
            return "trap"
        return "moved"

    def open_chest(self, player):
        """Open chest at current position. Returns list of items."""
        from game_items import ITEM_POOL, inventory_add
        self.chests_opened.add((self.px, self.py))
        # Better loot on deeper floors
        pool_weights = {
            1: [("Potion",0.5),("Ether",0.3),("Iron Ring",0.1)],
            2: [("Hi-Potion",0.4),("Hi-Ether",0.3),("Potion",0.3),("Mana Stone",0.2)],
            3: [("Full Potion",0.35),("Elixir",0.25),("Frost Crystal",0.2),("Power Ring",0.1)],
            4: [("Mega Potion",0.3),("Mega Ether",0.25),("Dark Shard",0.3),("Hero Amulet",0.08)],
            5: [("Mega Potion",0.4),("Mana Crystal",0.3),("Dragon Scale",0.15),("Phoenix Pendant",0.05)],
        }
        table = pool_weights.get(self.floor_num, pool_weights[1])
        found = []
        gold  = random.randint(10, 20 * self.floor_num)
        player.gold += gold
        for name, chance in table:
            if random.random() < chance and name in ITEM_POOL:
                item = ITEM_POOL[name]()
                inventory_add(player.inventory, item)
                found.append(item.name)
        return gold, found

    def trigger_trap(self, player):
        self.traps_triggered.add((self.px, self.py))
        dmg = random.randint(8, 12 + self.floor_num * 4)
        player.hp = max(1, player.hp - dmg)
        return dmg


# =============================================================
# DUNGEON MANAGER — runs the full multi-floor dungeon loop
# =============================================================

class DungeonManager:
    def __init__(self, name, danger=2):
        self.name          = name
        self.danger        = danger
        self.floors        = {}   # floor_num → DungeonFloor
        self.current_floor = 1
        self.total_killed  = 0
        self.floor_killed  = 0
        self._ensure_floor(1)

    def _ensure_floor(self, n):
        if n not in self.floors:
            self.floors[n] = DungeonFloor(n, self.name)
        return self.floors[n]

    def current(self) -> DungeonFloor:
        return self.floors[self.current_floor]

    def enter(self, player):
        """Main dungeon loop. Returns 'exit', 'defeat', or 'complete'."""
        from game_input import InputHandler
        from game_enemies import generate_dungeon_enemy, get_floor_miniboss, create_boss
        from game_systems import run_combat
        from game_items import ITEM_POOL, inventory_add

        inp = InputHandler(mode=getattr(player, "movement_mode", "wasd"))
        self.floor_killed = 0
        floor = self.current()
        floor.msg = f"{_DIM}Welcome to {self.name}. Explore carefully.{_R}"

        while True:
            floor.render(player, self.floor_killed, self.total_killed)
            action = inp.get_action()

            if action[0] == "cmd":
                cmd = action[1]
                if cmd in ("quit", "save"):
                    floor.msg = f"{_DIM}You retreat from the dungeon.{_R}"
                    return "exit"
                elif cmd == "inventory":
                    try:
                        from main import _quick_inventory
                        _quick_inventory(player)
                    except Exception:
                        pass
                elif cmd == "codex":
                    from game_codex import open_encyclopedia
                    open_encyclopedia(player)
                elif cmd == "help":
                    self._show_help()
                elif cmd == "enter":
                    result = self._handle_interact(player, floor)
                    if result in ("exit", "defeat", "complete"):
                        return result
                floor.msg = ""

            elif action[0] == "move":
                _, dx, dy = action
                result = floor.move(dx, dy)
                floor.msg = self._handle_move_result(
                    result, player, floor, inp,
                    generate_dungeon_enemy, get_floor_miniboss, create_boss,
                    run_combat, inventory_add, ITEM_POOL
                )
                if floor.msg in ("EXIT", "DEFEAT", "COMPLETE"):
                    return {"EXIT":"exit","DEFEAT":"defeat","COMPLETE":"complete"}[floor.msg]

            if not player.is_alive():
                return "defeat"

    def _handle_move_result(self, result, player, floor, inp,
                            gen_enemy, get_boss_name, create_boss,
                            run_combat, inventory_add, ITEM_POOL):
        danger     = FLOOR_DANGER[self.current_floor - 1]
        enc_chance = ENCOUNTER_BASE[self.current_floor - 1]

        if result == "blocked":
            return f"{_DIM}Solid wall.{_R}"

        elif result == "moved":
            if random.random() < enc_chance:
                e = gen_enemy(danger=danger + self.danger, player_level=player.level,
                              floor=self.current_floor)
                return self._do_combat(e, player, floor, run_combat)
            return ""

        elif result == "surface":
            floor.msg = f"{_GREEN}You return to the surface.{_R}"
            floor.render(player, self.floor_killed, self.total_killed)
            time.sleep(0.5)
            return "EXIT"

        elif result == "teleport":
            floor.msg = f"{_PURP}Teleport pad activated — warping to surface!{_R}"
            floor.render(player, self.floor_killed, self.total_killed)
            time.sleep(0.8)
            return "EXIT"

        elif result == "stairs_down":
            if self.current_floor >= MAX_FLOORS:
                return f"{_DIM}No deeper floors.{_R}"
            self.current_floor += 1
            self._ensure_floor(self.current_floor)
            floor = self.current()
            self.floor_killed = 0
            depth_msg = ["", "Getting darker...", "The air grows cold.", "Something stirs below.", "This is where legends die."]
            return f"{_GOLD}[Floor {self.current_floor}] {depth_msg[self.current_floor-1]}{_R}"

        elif result == "stairs_up":
            if self.current_floor <= 1:
                return f"{_DIM}Use the entrance to leave.{_R}"
            self.current_floor -= 1
            floor = self.current()
            return f"{_DIM}Climbed back to floor {self.current_floor}.{_R}"

        elif result == "chest":
            gold, items = floor.open_chest(player)
            parts = [f"{_GOLD}+{gold}g{_R}"]
            parts += [f"{_YELL}{n}{_R}" for n in items]
            return f"{_GOLD}★ Chest! {_R}" + "  ".join(parts)

        elif result == "trap":
            dmg = floor.trigger_trap(player)
            return f"{_RED}!! TRAP! Took {dmg} damage!{_R}"

        return ""

    def _do_combat(self, enemy, player, floor, run_combat):
        """Trigger a combat, update counters, handle party."""
        floor.msg = f"{_RED}!! {enemy.name} appears!{_R}"
        floor.render(player, self.floor_killed, self.total_killed)
        time.sleep(0.3)

        party = getattr(player, "party", None)
        outcome = run_combat(player, enemy, party=party)

        if outcome == "defeat":
            return "DEFEAT"
        self.floor_killed  += 1
        self.total_killed  += 1
        # Check for floor boss trigger after clearing enough enemies
        if (self.current_floor in {3, 5}
                and self.floor_killed >= 5
                and not floor.boss_defeated):
            return self._trigger_floor_boss(player, floor, run_combat)
        return f"{_GREEN}Victory!{_R}"

    def _trigger_floor_boss(self, player, floor, run_combat):
        from game_enemies import get_floor_miniboss, create_boss
        boss_name = get_floor_miniboss(self.current_floor)
        boss = create_boss(boss_name)

        floor.msg = f"{_RED}{_B}★ FLOOR BOSS: {boss_name} blocks the path! ★{_R}"
        floor.render(player, self.floor_killed, self.total_killed)
        time.sleep(0.8)

        party = getattr(player, "party", None)
        outcome = run_combat(player, boss, party=party)
        if outcome == "defeat":
            return "DEFEAT"
        floor.boss_defeated = True
        return f"{_GOLD}★ Floor boss defeated! The path clears.{_R}"

    def _handle_interact(self, player, floor):
        """[E] key pressed — interact with tile at current position."""
        ch = floor.grid[floor.py][floor.px]
        if ch == TILE_ENTRY:
            floor.msg = f"{_GREEN}Exiting dungeon...{_R}"
            floor.render(player, self.floor_killed, self.total_killed)
            time.sleep(0.4)
            return "exit"
        if ch == TILE_STAIRS_D:
            floor.msg = "Step onto the stairs to descend (move into them)."
        if ch == TILE_TELEPORT:
            floor.msg = "Step onto the teleport pad to use it (move into it)."
        return None

    def _show_help(self):
        clr()
        print(C(f"\n{_CYAN}{_B}DUNGEON CONTROLS{_R}\n"))
        print(C(f"{_GOLD}WASD{_R}{_DIM}/Arrows = move{_R}"))
        print(C(f"{_GOLD}[E]{_R}{_DIM} Use entrance/exit tile{_R}"))
        print(C(f"{_GOLD}[I]{_R}{_DIM} Quick bag — use potions, equip gear{_R}"))
        print(C(f"{_GOLD}[C]{_R}{_DIM} Encyclopedia — enemies, crafting guide{_R}"))
        print(C(f"{_GOLD}[Q]{_R}{_DIM} Retreat to surface{_R}"))
        print(C(f"\n{_GOLD}Tiles:{_R}"))
        print(C(f"  {TILE_COLOURS[TILE_ENTRY]}E{_R}  Entrance/Exit to surface"))
        print(C(f"  {TILE_COLOURS[TILE_STAIRS_D]}▼{_R}  Stairs going deeper"))
        print(C(f"  {TILE_COLOURS[TILE_STAIRS_U]}▲{_R}  Stairs going shallower"))
        print(C(f"  {TILE_COLOURS[TILE_TELEPORT]}T{_R}  Teleport pad (instant surface)"))
        print(C(f"  {TILE_COLOURS[TILE_CHEST]}C{_R}  Treasure chest (step on it)"))
        print(C(f"  {TILE_COLOURS[TILE_TRAP]}!{_R}  Trap (ouch)"))
        print(C(f"\n{_DIM}Floors get progressively harder. Floor 3 and 5 have bosses!{_R}"))
        input(C(f"\n{_DIM}(Press Enter){_R}"))
