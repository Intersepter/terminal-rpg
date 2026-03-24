"""
rpg_systems.py — Towns, shops, quests, dungeons, combat.
All screens clear before drawing and use the colour system from game_world.
"""

import random, os
from game_items import roll_drops, town_shop_stock, CRAFTING_RECIPES
from game_enemies import generate_enemy, create_boss
from game_lang import T, set_language, LANG, LANGUAGE_NAMES
from game_term import C, P, div, clr, W, H, hpbar, mpbar, box_top, box_mid, box_bot, get_size
from game_art import print_sprite, side_by_side, render_sprite, combat_layout

# ═══════════════════════════════════════════════════════════════
# RE-IMPORT COLOUR HELPERS  (same palette as world_map)
# ═══════════════════════════════════════════════════════════════

R      = "\033[0m"
B      = "\033[1m"
def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"

C_GOLD   = fg(255,215,0)
C_WHITE  = fg(255,255,255)
C_DIM    = fg(120,120,120)
C_GREEN  = fg(80,200,80)
C_RED    = fg(220,60,60)
C_CYAN   = fg(80,220,220)
C_BLUE   = fg(80,130,220)
C_YELLOW = fg(240,200,60)
C_ORANGE = fg(220,140,40)
C_PURPLE = fg(180,80,220)
C_PINK   = fg(220,80,160)

def clear(): os.system("cls" if os.name == "nt" else "clear")

def divider(w=None, c=C_DIM):
    from game_term import _pad
    _cols=W()
    # Total visible = _pad() + w. Cap so it never exceeds terminal width.
    max_w = max(30, _cols - 2 * _pad() - 2)
    w = w or min(max_w, 120)
    return C(f"{c}{'─'*w}{R}")
def section(title, c=C_CYAN):  return C(f"\n{c}{B}══ {title} ══{R}")
def prompt(text=""):
    print(C(f"\n{C_GOLD}>{R} {C_DIM}{text}{R} "), end="")
    return input().strip()

def menu_opt(key, label, hint=""):
    k = f"{C_GOLD}{B}[{key}]{R}"
    l = f"{C_WHITE}{label}{R}"
    h = f"  {C_DIM}{hint}{R}" if hint else ""
    return f"{k} {l}{h}"   # no leading spaces — C() adds centring

def hp_bar(current, maximum, width=None):
    _cols=W(); width=width or max(12,min(22,_cols//5))
    frac   = current / maximum if maximum else 0
    filled = int(width * frac)
    col    = C_GREEN if frac > 0.5 else C_YELLOW if frac > 0.25 else C_RED
    bar    = f"{col}{'█'*filled}{C_DIM}{'░'*(width-filled)}{R}"
    return f"[{bar}{R}] {col}{current}/{maximum}{R}"

def mp_bar(current, maximum, width=None):
    _cols=W(); width=width or max(8,min(16,_cols//7))
    frac   = current / maximum if maximum else 0
    filled = int(width * frac)
    bar    = f"{C_BLUE}{'█'*filled}{C_DIM}{'░'*(width-filled)}{R}"
    return f"[{bar}{R}] {C_BLUE}{current}/{maximum}{R}"

def status_header(player):
    effects = (f"  {C_YELLOW}Status: " +
               ", ".join(str(e) for e in player.status_effects) + R) if player.status_effects else ""
    return (
        f"{C_WHITE}{B}{player.name}{R}  {C_DIM}Lv{R}{C_GOLD}{B}{player.level}{R}"
        f"  {C_DIM}[{player.job.name}]{R}  {C_DIM}Rank {R}{C_ORANGE}{B}{player.rank}{R}"
        f"  {C_GOLD}Gold {player.gold}{R}{effects}"
    )

# ═══════════════════════════════════════════════════════════════
# COMBAT
# ═══════════════════════════════════════════════════════════════

def run_combat(player, enemy, allow_escape=True, first_strike=False):
    from game_enemies import BossEnemy
    from game_items import roll_drops
    is_boss = isinstance(enemy, BossEnemy)
    base_defense = player.defense

    # ── Sneak attack on first round ──────────────────────────
    if first_strike and player.in_stealth:
        import random as _r
        base = max(1, player.atk + player.get_equip_atk_bonus() + _r.randint(0,3))
        dmg  = player.stealth_first_strike(base)
        enemy.take_damage(dmg)
        clear()
        print(C(f"\n{C_PURPLE}{B}★ {T('combat.sneak_attack')} {enemy.name} → {dmg} damage!{R}\n"))
        if not enemy.is_alive():
            print(C(f"{C_GREEN}{B}★ One-shot takedown! {enemy.name} is defeated!{R}"))
            player.gold += enemy.gold_reward
            player.gain_exp(enemy.exp_reward)
            player.update_quests_on_kill(enemy.name)
            from game_customise import tick_legendary_quest as _tlq
            _tlq(player,"kill",enemy.name)
            from game_enemies import BossEnemy as _BE
            if isinstance(enemy,_BE): _tlq(player,"kill_boss")
            drops = roll_drops(enemy.name)
            for item in drops:
                player.add_item(item)
                print(C(f"{C_GOLD}→ Loot: {item}{R}"))
            input(C(f"\n{C_DIM}(Press Enter){R}"))
            return "victory"
        input(C(f"{C_DIM}(Press Enter — continue fight){R}"))

    while enemy.is_alive() and player.is_alive():
        # ── Status tick (player) ──
        player.process_status_start()
        if not player.is_alive():
            if not player.check_god_potion(): break
        stunned = any(e.name == "Stun" for e in player.status_effects)

        # ── Draw combat screen ──
        clear()
        if is_boss:
            print(C(f"\n{C_RED}{B}╔══════════════════════════════════╗"))
            print(C(f"║   ⚔  BOSS BATTLE: {enemy.name:<14}║"))
            print(C(f"╚══════════════════════════════════╝{R}\n"))
        else:
            print(C(f"\n{C_RED}{B}⚔  BATTLE: {enemy.name}{R}\n"))

        # ── Sprite art row ──────────────────────────────────────
        for art_line in side_by_side(
            player.job.name, enemy.name,
            player.name, enemy.name, gap=10
        ):
            print(art_line)
        print()

        # Enemy row
        eff_str = (" (" + ", ".join(str(e) for e in enemy.status_effects) + ")") if enemy.status_effects else ""
        print(C(f"{C_RED}{B}{enemy.name:<20}{R}  HP {hp_bar(enemy.hp, enemy.max_hp)}{C_DIM}{eff_str}{R}"))
        print()

        # Player row
        p_eff = (" (" + ", ".join(str(e) for e in player.status_effects) + ")") if player.status_effects else ""
        print(C(f"{C_WHITE}{B}{player.name:<20}{R}  HP {hp_bar(player.hp, player.max_hp)}"))
        print(C(f"{'':20}   MP {mp_bar(player.mp, player.max_mp)}{C_DIM}{p_eff}{R}"))

        print(); print(divider())

        if stunned:
            print(C(f"\n{C_YELLOW}⚡ {T('combat.stunned')}{R}"))
        else:
            print(C(f"\n{menu_opt('1', T('combat.attack'), 'Basic weapon strike')}"))
            print(C(f"{menu_opt('2', T('combat.skill'), 'Use a class skill (costs MP)')}"))
            print(C(f"{menu_opt('3', T('combat.item'), 'Use a consumable from your bag')}"))
            print(C(f"{menu_opt('4', T('combat.defend'), 'Brace — reduce incoming damage')}"))
            if allow_escape:
                print(C(f"{menu_opt('5', T('combat.run'), 'Attempt to flee')}"))

        action = prompt("Choose action")

        if not stunned:
            if action == "1":
                if enemy.try_dodge():
                    print(C(f"\n{C_DIM}{T('combat.dodged', name=enemy.name)}{R}"))
                else:
                    base = max(1, player.atk + player.get_equip_atk_bonus() + random.randint(-2,3))
                    crit, dmg = player.calc_crit(base)
                    enemy.take_damage(dmg)
                    tag = f" {C_ORANGE}{B}CRITICAL!{R}" if crit else ""
                    if crit:
                        from game_customise import tick_legendary_quest as _tlq
                        _tlq(player,"crit_hit")
                    print(C(f"\n{C_WHITE}{T('combat.you_strike', crit=tag, dmg=dmg)}{R}"))

            elif action == "2":
                if not player.skills:
                    print(C(f"\n{C_DIM}You have no skills yet.{R}"))
                    input(C(f"{C_DIM}(Press Enter){R}")); continue
                clear()
                print(section("SKILLS"))
                print()
                for i, sk in enumerate(player.skills, 1):
                    enough = C_GREEN if player.mp >= sk.mana_cost else C_RED
                    base   = f"DMG {sk.damage}" if sk.damage else f"HEAL {sk.heal}" if sk.heal else "?"
                    fx     = f" +{sk.status_effect.name}({sk.status_chance}%)" if sk.status_effect else ""
                    print(C(f"{menu_opt(i, sk.name, f'{base}{fx}')}  "
                          f"{enough}MP:{sk.mana_cost}{R}"))
                print(C(f"\n{menu_opt(len(player.skills)+1,'Cancel','')}"))
                sc_raw = prompt("Choose skill")
                try:
                    sc = int(sc_raw)
                    if sc == len(player.skills)+1: continue
                    if not (1 <= sc <= len(player.skills)):
                        print(C(f"{C_RED}Invalid.{R}")); input(); continue
                    sk = player.skills[sc-1]
                    success = sk.use(player, enemy if sk.damage > 0 else None)
                    if success:
                        from game_customise import tick_legendary_quest
                        tick_legendary_quest(player, "skill_cast")
                    if sk.heal > 0: player._tick_evolution_quest("heal_skill")
                    if not success: continue
                except ValueError:
                    continue

            elif action == "3":
                used = player.use_inventory_item()
                if not used: continue

            elif action == "4":
                bonus = player.defend()

            elif action == "5" and allow_escape:
                esc = 40 + player.job.dodge_bonus
                if random.randint(1,100) <= esc:
                    print(C(f"\n{C_GREEN}{T('combat.fled')}{R}"))
                    input(C(f"{C_DIM}(Press Enter){R}"))
                    player.defense = base_defense
                    return "escaped"
                else:
                    print(C(f"\n{C_RED}{T('combat.cant_flee')}{R}"))
            else:
                print(C(f"{C_RED}Invalid choice.{R}")); input(); continue

        input(C(f"\n{C_DIM}(Press Enter — enemy turn){R}"))

        player.process_status_end()

        # ── Party members act ──
        if enemy.is_alive() and hasattr(player, "party") and player.party.alive_members():
            for companion in player.party.alive_members():
                if not enemy.is_alive(): break
                action_str = companion.combat_action(player, enemy, player.party.members)
                print(C(f"{action_str}"))

        # ── Enemy turn ──
        if enemy.is_alive():
            enemy.process_status_start()
            if enemy.is_alive():
                if isinstance(enemy, BossEnemy):
                    enemy.use_boss_skill(player)
                elif enemy.skills and random.randint(1,100) <= 20:
                    sk = random.choice(enemy.skills)
                    if sk == "power_strike":
                        dmg = enemy.atk * 2; actual = player.take_damage(dmg)
                        print(C(f"\n{C_RED}{enemy.name} POWER STRIKES → {actual} damage!{R}"))
                    else:
                        enemy.basic_attack(player)
                else:
                    enemy.basic_attack(player)
            enemy.process_status_end()
            from game_customise import tick_legendary_quest as _tlq
            _tlq(player, "damage_taken", max(0, player.max_hp - player.hp))

        if not player.is_alive():
            if not player.check_god_potion(): break

        player.defense = base_defense
        input(C(f"{C_DIM}(Press Enter){R}"))

    # ── Result ──
    clear()
    if not player.is_alive():
        print_sprite(enemy.name, label=f"✖  DEFEATED  ✖")
        print(C(f"\n{C_RED}{B}╔══════════════════════╗"))
        print(C(f"║   ✖  DEFEATED        ║"))
        print(C(f"╚══════════════════════╝{R}\n"))
        print(C(f"{C_DIM}{enemy.name} bested you...{R}"))
        input(C(f"\n{C_DIM}(Press Enter){R}"))
        return "defeat"

    print_sprite(player.job.name, label=f"★  VICTORY  ★")
    print(C(f"\n{C_GREEN}{B}╔══════════════════════════════╗"))
    print(C(f"║   ★  VICTORY!              ║"))
    print(C(f"╚══════════════════════════════╝{R}\n"))
    print(C(f"{C_GOLD}{T('combat.gold_exp', gold=enemy.gold_reward, exp=enemy.exp_reward)}{R}"))
    player.gold += enemy.gold_reward
    leveled = player.gain_exp(enemy.exp_reward)
    player.update_quests_on_kill(enemy.name)
    from game_customise import tick_legendary_quest as _tlq
    _tlq(player,"kill",enemy.name)
    from game_enemies import BossEnemy as _BE2
    if isinstance(enemy,_BE2): _tlq(player,"kill_boss")
    # Trophy for boss kills
    from game_enemies import BossEnemy as _BE
    if isinstance(enemy, _BE) and hasattr(player,"bases"):
        for base in player.bases.bases.values():
            added = base.add_trophy(enemy.name, "?")
            if added:
                print(C(f"{C_GOLD}🏆 Trophy added: {enemy.name}!{R}"))
                break

    drops = roll_drops(enemy.name)
    if drops:
        print(C(f"\n{C_YELLOW}Loot dropped:{R}"))
        for item in drops:
            player.add_item(item)
            print(C(f"  {C_WHITE}→ {item}{R}"))
    else:
        print(C(f"\n{C_DIM}{T('combat.no_drops')}{R}"))

    input(C(f"\n{C_DIM}(Press Enter){R}"))
    player.defense = base_defense
    return "victory"


# ═══════════════════════════════════════════════════════════════
# NPC DIALOGUE
# ═══════════════════════════════════════════════════════════════

TOWNSFOLK = [
    {"name":"Gruff the Innkeeper","icon":"[INN]","personality":"grumpy but kind",
     "lines":["Rest well traveller. The roads grow more dangerous each day.",
              "Strange creatures spotted near the old fortress last night.",
              "A dragon was seen circling the Iron Peaks. Bold or mad.",
              "I had an adventurer like you once. Now she's a legend. Or dead.",
              "The cellar keeps flooding with something... it's not water."],
     "offer":None},
    {"name":"Elder Voss","icon":"[SCH]","personality":"wise historian",
     "lines":["This land was once ruled by the Dragon Court. Five hundred years ago it fell.",
              "The five continents were once connected. A cataclysm split them apart.",
              "The God Potions — they were not created by alchemy. Something older made them.",
              "Every dungeon has a guardian. Not all of them are monsters.",
              "There are ruins beneath every city. We built on old bones."],
     "offer":"lore"},
    {"name":"Merchant Dalia","icon":"[MRC]","personality":"shrewd trader",
     "lines":["Dragon scales? I'll triple your asking price. Don't tell the guild.",
              "The black market thrives in shadows. Not that I'd know anything about that.",
              "My wares are the finest because I source from the bravest fools — like you.",
              "Gold flows toward the bold. Are you bold enough?",
              "I once sold a god potion back to a god. The markup was divine."],
     "offer":"tip"},
    {"name":"Zara the Blacksmith","icon":"[SMT]","personality":"passionate craftsperson",
     "lines":["Bring me Dragon Scale and Iron Ore. I'll forge you something that sings.",
              "A good blade is like a good friend — reliable when things get bloody.",
              "The secret to great armor: metal, heart, and stubbornness.",
              "I can repair anything. Except bad decisions.",
              "Wolf Pelt makes surprisingly good padding under chain mail."],
     "offer":"crafting_tip"},
    {"name":"Captain Marek","icon":"[CPT]","personality":"battle-hardened soldier",
     "lines":["I've fought in twelve wars. The one coming will be the thirteenth.",
              "Never enter a dungeon without potions. Watched good people die over that.",
              "The Shadow Beasts have been pushing further west. Something drives them.",
              "Your class defines your style, not your fate.",
              "Keep your back to the wall. Always."],
     "offer":"combat_tip"},
    {"name":"Sister Mara","icon":"[HLR]","personality":"gentle healer",
     "lines":["I see wounds in your eyes that potions can't reach. Travel safely.",
              "The light doesn't judge the darkness you've walked through.",
              "A Healer's power is not in their spells but in their resolve.",
              "There is a holy site deep in the Frost Mountains. Ancient power lingers.",
              "Even God Potions have limits. The soul must be willing to survive."],
     "offer":"blessing"},
    {"name":"Riko the Wanderer","icon":"[EXP]","personality":"cheerful explorer",
     "lines":["I mapped every continent. Except the one that maps itself — it changes.",
              "The South Isles have fruits that restore MP just by smelling them!",
              "Found a cave once with walls that whispered. Left. Quickly.",
              "Fast travel saves time but you miss the adventures in between.",
              "There's a ship captain in Greenport who sails without wind or crew."],
     "offer":"map_hint"},
    {"name":"The Masked One","icon":"[???]","personality":"cryptic and unsettling",
     "lines":["There is a dungeon to the east no one has fully cleared...",
              "God Potions were not crafted. They were negotiated.",
              "An awakened warrior once slew a dragon with one strike. Still running.",
              "The world has five regions. One of them is wrong.",
              "I know who you are. Do you?"],
     "offer":"secret"},
]

OFFER_RESPONSES = {
    "lore":         ["Elder Voss traces an ancient map. 'This was all one land, once.'",
                     "The elder's eyes grow distant. The past weighs heavily on him."],
    "tip":          ["Dalia slips you a folded note. 'Don't open it near guards.'",
                     "The merchant whispers a trade route only she knows."],
    "crafting_tip": ["Zara shows a hidden compartment — better tools than she sells.",
                     "'See this seam?' She points at your armor. 'I can reinforce that. This once.'"],
    "combat_tip":   ["Marek demonstrates a feint. Your reflexes feel sharper somehow.",
                     "The captain sketches a dungeon layout. 'Enemy choke points: here, here.'"],
    "blessing":     ["Sister Mara murmurs a quiet prayer. Your HP fully restores!",
                     "The sister presses a warm hand to your shoulder. You feel lighter."],
    "map_hint":     ["Riko marks a hidden path — cuts travel time considerably.",
                     "'Shortcut through the hills,' Riko says, sketching in the air."],
    "secret":       ["The figure vanishes. A gold coin sits where they stood.",
                     "'Remember me when you find it,' echoes from nowhere."],
}

NPC_LINES = {t["name"]: t["lines"] for t in TOWNSFOLK}


CLANS = {
    "Iron Fist":      ("Warrior clan",  C_RED,    "DEF +5, ATK +3"),
    "Shadow Weavers": ("Rogue clan",    C_PURPLE, "DODGE +8, CRIT +5"),
    "Silver Dragons": ("Mage clan",     C_CYAN,   "MP +20, Skill Power +4"),
    "Holy Order":     ("Healer clan",   C_GREEN,  "Heal Power +10, DEF +3"),
}


# ═══════════════════════════════════════════════════════════════
# TOWN
# ═══════════════════════════════════════════════════════════════

class Town:
    def __init__(self, player, town_name, region_name=""):
        self.player      = player
        self.town_name   = town_name
        self.region_name = region_name
        self.shop_stock  = town_shop_stock(region_name)
        self._companion_cb  = None   # set by world map
        self._continent_id  = None
        self._base_x        = 0
        self._base_y        = 0
        self._world_map     = None
        self._ship          = None
        self._ship_player   = None

    def set_companion_callback(self, cb):
        self._companion_cb = cb

    def set_base_info(self, continent_id, x, y):
        self._continent_id = continent_id
        self._base_x = x
        self._base_y = y

    def set_ship(self, world_map, ship, player):
        """Store ship reference so port towns can offer boarding."""
        self._world_map = world_map
        self._ship      = ship
        self._ship_player = player

    def _header(self, subtitle=""):
        clear()
        print(C(f"\n{C_GOLD}{B}╔══════════════════════════════════════════╗"))
        print(C(f"║  {self.town_name.upper():<40}║"))
        if subtitle:
            print(C(f"║  {C_DIM}{subtitle:<40}{C_GOLD}║"))
        print(C(f"╚══════════════════════════════════════════╝{R}"))
        print(C(f"\n{status_header(self.player)}"))
        print(divider())

    # ── INN ──────────────────────────────────────────────────

    def inn(self):
        cost = max(5, 10 + self.player.level * 2)
        self._header(f"{T('town.inn')}  —  {T('town.inn_cost', cost=cost)}")
        print(C(f"\n{C_WHITE}Rest fully? {C_GOLD}HP & MP{R} restored, {C_GREEN}status cleared{R}."))
        print(C(f"\n{menu_opt('Y','Rest & pay')} {C_DIM}({cost} gold){R}"))
        print(C(f"{menu_opt('N','Leave')}"))
        ch = prompt("Choice").lower()
        if ch == "y":
            if self.player.gold >= cost:
                self.player.gold -= cost
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
                self.player.status_effects.clear()
                print(C(f"\n{C_GREEN}You rest deeply. Fully restored!{R}"))
            else:
                print(C(f"\n{C_RED}{T('ui.not_enough_gold')} (have {self.player.gold}g){R}"))
        input(C(f"\n{C_DIM}(Press Enter){R}"))

    # ── SHOP ─────────────────────────────────────────────────

    def shop(self):
        while True:
            self._header("Shop")
            print(C(f"\n{menu_opt('1','Browse & Buy')}"))
            print(C(f"{menu_opt('2','Sell items')}"))
            print(C(f"{menu_opt('0','Leave shop')}"))
            ch = prompt("Choice")
            if ch == "1":   self._buy()
            elif ch == "2": self._sell()
            elif ch == "0": break

    def _buy(self):
        self._header("Shop — Buy")
        pc = self.player.job.name
        print(C(f"\n{C_GOLD}Your gold: {self.player.gold}g{R}  {C_DIM}Class: {C_CYAN}{pc}{R}\n"))
        for i,(item,price) in enumerate(self.shop_stock, 1):
            ac = getattr(item,"allowed_classes",None)
            can_use = (ac is None or pc in ac)
            rcol = item.rarity_col() if hasattr(item,"rarity_col") else C_WHITE
            stat = f"  {C_DIM}{item.stat_line()}{R}" if hasattr(item,"stat_line") else ""
            if not can_use:
                col = C_DIM
                cnote = f"  {C_RED}({', '.join(ac[:2])} only){R}"
            else:
                col = rcol if self.player.gold >= price else C_DIM
                cnote = ""
            print(C(f"{C_GOLD}{B}[{i:>2}]{R} {col}{item.name:<26}{R}{stat}{cnote}  {C_GOLD}{price}g{R}"))
        print(C(f"\n{menu_opt(0,'Cancel')}"))
        ch = prompt("Buy item #")
        if ch == "0" or not ch.isdigit(): return
        idx = int(ch)-1
        if not (0 <= idx < len(self.shop_stock)): return
        import copy
        item,price = self.shop_stock[idx]
        if self.player.gold < price:
            print(C(f"\n{C_RED}Not enough gold!{R}")); input(C(f"{C_DIM}(Enter){R}")); return
        self.player.gold -= price
        self.player.add_item(copy.deepcopy(item))
        print(C(f"\n{C_GREEN}Bought {item.name}!{R}"))
        input(C(f"{C_DIM}(Press Enter){R}"))

    def _sell(self):
        self._header("Shop — Sell")
        if not self.player.inventory:
            print(C(f"\n{C_DIM}Your bag is empty.{R}"))
            input(C(f"{C_DIM}(Press Enter){R}")); return
        print()
        for i,it in enumerate(self.player.inventory, 1):
            print(C(f"{C_GOLD}{B}[{i:>2}]{R} {C_WHITE}{it.name:<26}{R}  {C_DIM}Sell: {C_GOLD}{it.sell_value} gold{R}"))
        print(C(f"\n{menu_opt(0,'Cancel')}"))
        ch = prompt("Sell item #")
        if ch == "0" or not ch.isdigit(): return
        idx = int(ch)-1
        if not (0 <= idx < len(self.player.inventory)): return
        item = self.player.inventory.pop(idx)
        self.player.gold += item.sell_value
        print(C(f"\n{C_GREEN}Sold {item.name} for {item.sell_value} gold.{R}"))
        input(C(f"{C_DIM}(Press Enter){R}"))

    # ── QUEST BOARD ───────────────────────────────────────────

    def quest_board(self):
        while True:
            self._header("Quest Board")
            print(C(f"\n{menu_opt('1','Take a guild quest')}"))
            print(C(f"{menu_opt('2','Turn in completed quests')}"))
            print(C(f"{menu_opt('3','Start class awakening quest')}"))
            print(C(f"{menu_opt('4','View active quests')}"))
            print(C(f"{menu_opt('0','Leave')}"))
            ch = prompt("Choice")
            if ch == "1":   self._offer_guild_quest()
            elif ch == "2": self.player.turn_in_quests(); input(C(f"\n{C_DIM}(Press Enter){R}"))
            elif ch == "3": self.player.start_evolution_quest(); input(C(f"\n{C_DIM}(Press Enter){R}"))
            elif ch == "4": self._show_quests()
            elif ch == "0": break

    def _show_quests(self):
        clear()
        print(section("ACTIVE QUESTS"))
        print()
        any_q = False
        for q in self.player.active_quests:
            prog = q.get("progress",0); req = q.get("required",1)
            bar  = f"{C_GREEN}{'█'*prog}{C_DIM}{'░'*(req-prog)}{R}"
            print(C(f"{C_CYAN}◆{R} {C_WHITE}{q['title']}{R}"))
            print(C(f"  {C_DIM}{q['desc']}{R}"))
            print(C(f"Progress: [{bar}] {C_GOLD}{prog}/{req}{R}  "
                  f"Reward: {C_GOLD}{q['reward_gold']} gold{R}, {C_CYAN}{q['reward_exp']} EXP{R}\n"))
            any_q = True
        eq = self.player.evolution_quest
        if eq and not eq.get("done"):
            prog = eq.get("progress",0); req = eq.get("required",1)
            bar  = f"{C_ORANGE}{'█'*prog}{C_DIM}{'░'*(req-prog)}{R}"
            print(C(f"{C_ORANGE}★{R} {C_WHITE}[CLASS QUEST] {eq['title']}{R}"))
            print(C(f"  {C_DIM}{eq['desc']}{R}"))
            print(C(f"  Progress: [{bar}] {C_GOLD}{prog}/{req}{R}\n"))
            any_q = True
        if not any_q:
            print(C(f"{C_DIM}No active quests.{R}"))
        if self.player.completed_quests:
            print(C(f"\n{C_GREEN}Completed: {len(self.player.completed_quests)} quest(s){R}"))
        input(C(f"\n{C_DIM}(Press Enter){R}"))

    def _offer_guild_quest(self):
        if len(self.player.active_quests) >= 3:
            print(C(f"\n{C_RED}You already have 3 active quests. Turn some in first.{R}"))
            input(C(f"{C_DIM}(Press Enter){R}")); return
        from game_player import GUILD_QUEST_TARGETS
        target   = random.choice(GUILD_QUEST_TARGETS)
        required = random.randint(2,5)
        g,e = required*45, required*35
        quest = {"title":f"Hunt {required}x {target}","desc":f"Eliminate {required} {target}(s) for the guild.",
                 "type":"kill","target":target,"required":required,"progress":0,
                 "reward_gold":g,"reward_exp":e}
        clear()
        print(section("QUEST OFFERED"))
        print(C(f"\n{C_CYAN}◆{R} {C_WHITE}{quest['title']}{R}"))
        print(C(f"{C_DIM}{quest['desc']}{R}"))
        print(C(f"Reward: {C_GOLD}{g} gold{R}  {C_CYAN}{e} EXP{R}"))
        print(C(f"\n{menu_opt('Y','Accept quest')}"))
        print(C(f"{menu_opt('N','Decline')}"))
        if prompt("Choice").lower() == "y":
            self.player.active_quests.append(quest)
            print(C(f"\n{C_GREEN}Quest accepted!{R}"))
        else:
            print(C(f"\n{C_DIM}Declined.{R}"))
        input(C(f"{C_DIM}(Press Enter){R}"))

    # ── GUILD ─────────────────────────────────────────────────

    def adventure_guild(self):
        while True:
            self._header("Adventurers Guild")
            evo_hint = f"  {C_ORANGE}★ READY TO AWAKEN!{R}" if self.player.can_awaken() else ""
            print(C(f"\n{menu_opt('1','Rank up',       f'Current: {self.player.rank}')}"))
            clan_cur = self.player.clan or 'None'
            print(C(f"{menu_opt('2','Join / change clan', f'Current: {clan_cur}')}"))
            print(C(f"{menu_opt('3','Awaken your class', 'Evolve into your next form')}{evo_hint}"))
            print(C(f"{menu_opt('0','Leave')}"))
            ch = prompt("Choice")
            if ch == "1":   self.player.promote_rank(); input(C(f"\n{C_DIM}(Press Enter){R}"))
            elif ch == "2": self._clan_menu()
            elif ch == "3": self.player.awaken(); input(C(f"\n{C_DIM}(Press Enter){R}"))
            elif ch == "0": break

    def _clan_menu(self):
        clear()
        print(section("CLANS"))
        print()
        clan_list = list(CLANS.items())
        for i,(name,(role,col,bonus)) in enumerate(clan_list, 1):
            cur = f"  {C_GREEN}← current{R}" if self.player.clan == name else ""
            print(C(f"{menu_opt(i, name, role)}  {col}{bonus}{R}{cur}"))
        print(C(f"\n{menu_opt(0,'Cancel')}"))
        ch = prompt("Choose clan")
        if ch == "0" or not ch.isdigit(): return
        idx = int(ch)-1
        if 0 <= idx < len(clan_list):
            self.player.clan = clan_list[idx][0]
            col = clan_list[idx][1][1]
            print(C(f"\n{col}Welcome to the {self.player.clan}!{R}"))
            input(C(f"{C_DIM}(Press Enter){R}"))

    # ── NPC DIALOGUE ─────────────────────────────────────────

    def talk_to_npcs(self):
        while True:
            self._header("Talk to Townsfolk")
            print(C(f"\n{C_DIM}The streets are lively. Who catches your eye?{R}\n"))
            for i, npc in enumerate(TOWNSFOLK, 1):
                print(C(f"{C_GOLD}{B}[{i:>2}]{R} {C_WHITE}{npc['icon']} {npc['name']:<24}{R}  {C_DIM}{npc['personality']}{R}"))
            print(C(f"\n{menu_opt(0,'Leave')}"))
            ch = prompt("Talk to")
            if ch == "0": break
            if not ch.isdigit(): continue
            idx = int(ch)-1
            if not (0 <= idx < len(TOWNSFOLK)): continue
            npc = TOWNSFOLK[idx]
            line = random.choice(npc["lines"])
            clear()
            print(C(f"\n{C_GOLD}{B}╔{'═'*36}╗"))
            print(C(f"║  {npc['icon']} {npc['name']:<32}║"))
            print(C(f"╚{'═'*36}╝{R}"))
            print(C(f"  {C_DIM}{npc['personality']}{R}\n"))
            print(C(f"  {C_WHITE}\"{line}\"{R}\n"))
            offer = npc.get("offer")
            if offer and offer in OFFER_RESPONSES:
                print(C(f"\n{C_CYAN}(They seem willing to share more...)"))
                print(C(f"\n{menu_opt('Y','Interact further')}"))
                print(C(f"{menu_opt('N','Just listen')}"))
                ans = input(C(f"\n{C_GOLD}>{R} ")).strip().lower()
                if ans == "y":
                    resp = random.choice(OFFER_RESPONSES[offer])
                    print(C(f"\n{C_CYAN}{resp}{R}"))
                    if offer == "blessing":
                        self.player.hp = self.player.max_hp
                        print(C(f"  {C_GREEN}Your HP is fully restored!{R}"))
            input(C(f"\n{C_DIM}(Press Enter){R}"))


    # ── CRAFTING ─────────────────────────────────────────────

    def crafting_bench(self):
        self._header("Crafting Bench")
        mat_count = {}
        for it in self.player.inventory:
            if it.item_type == "material":
                mat_count[it.name] = mat_count.get(it.name, 0) + 1

        print(C(f"\n{C_CYAN}Your materials:{R}"))
        if not mat_count:
            print(C(f"{C_DIM}None. Defeat monsters to collect materials.{R}"))
        else:
            for m,q in mat_count.items():
                print(C(f"  {C_WHITE}{m:<22}{R}  x{q}"))

        print(C(f"\n{C_CYAN}Recipes:{R}"))
        available = []
        pc = self.player.job.name
        for rec in CRAFTING_RECIPES:
            can = all(mat_count.get(k,0) >= v for k,v in rec["needs"].items())
            cls_ok = (rec.get("classes") is None or pc in rec.get("classes",[]))
            mark = f"{C_GREEN}[OK]{R}" if (can and cls_ok) else (f"{C_YELLOW}[CLS]{R}" if can else f"{C_RED}[--]{R}")
            needs = ", ".join(f"{k}x{v}" for k,v in rec["needs"].items())
            cnote = f"  {C_DIM}({pc} can't craft){R}" if not cls_ok else ""
            desc = f"  {C_DIM}{rec.get('desc','')}{R}"
            print(C(f"{mark} {C_WHITE}{rec['name']:<22}{R}  {C_DIM}{needs}{R}{cnote}{desc}"))
            if can and cls_ok: available.append(rec)

        if not available:
            print(C(f"\n{C_DIM}Nothing you can craft right now.{R}"))
            input(C(f"{C_DIM}(Press Enter){R}")); return

        print(C(f"\n{C_CYAN}Craftable:{R}"))
        for i,rec in enumerate(available, 1):
            print(C(f"{menu_opt(i, rec['name'])}"))
        print(C(f"\n{menu_opt(0,'Cancel')}"))
        ch = prompt("Craft #")
        if ch == "0" or not ch.isdigit(): return
        idx = int(ch)-1
        if not (0 <= idx < len(available)): return
        rec = available[idx]
        for mat_name, qty in rec["needs"].items():
            removed = 0; new_inv = []
            for it in self.player.inventory:
                if it.name == mat_name and removed < qty: removed += 1
                else: new_inv.append(it)
            self.player.inventory = new_inv
        result = rec["result"]()
        self.player.add_item(result)
        print(C(f"\n{C_GREEN}Crafted: {result}!{R}"))
        input(C(f"{C_DIM}(Press Enter){R}"))

    # ── INVENTORY ─────────────────────────────────────────────

    def inventory_screen(self):
        from game_items import INVENTORY_LIMIT, GuildStorage
        player = self.player
        if not hasattr(player, "guild_storage"):
            player.guild_storage = GuildStorage()
        gs = player.guild_storage
        while True:
            self._header("Inventory & Storage")
            inv = player.inventory
            limit = INVENTORY_LIMIT
            print(C(f"\n{C_CYAN}YOUR BAG  {C_DIM}({len(inv)}/{limit} slots){R}\n"))
            if not inv:
                print(C(f"  {C_DIM}Empty. Defeat enemies and open chests to collect items.{R}"))
            else:
                for i, it in enumerate(inv, 1):
                    rcol = it.rarity_col() if hasattr(it,"rarity_col") else C_WHITE
                    slot_tag = f"{C_DIM}[{it.slot}]{R}" if hasattr(it,"slot") else f"{C_DIM}[{it.item_type}]{R}"
                    stat = f"  {C_DIM}{it.stat_line()}{R}" if hasattr(it,"stat_line") else (f"  {C_GREEN}+{it.value}{R}" if it.item_type in ("heal","mana") else "")
                    eq_mark = ""
                    for e_it in player.equipped.values():
                        if e_it and e_it.name == it.name: eq_mark = f" {C_GREEN}[EQ]{R}"; break
                    print(C(f"{C_GOLD}{B}[{i:>2}]{R} {rcol}{it.name:<26}{R} {slot_tag}{eq_mark}{stat}"))
            print()
            print(C(f"  {C_GOLD}[E]{R}{C_DIM} Equip  {C_GOLD}[U]{R} Use  {C_GOLD}[D]{R} Drop  {C_GOLD}[G]{R} Guild Storage  {C_GOLD}[0]{R} Back{R}"))
            ch = prompt("Choice").lower()
            if ch == "0": break
            elif ch == "e": player.equip_item()
            elif ch == "u": player.use_inventory_item()
            elif ch == "d":
                ch2 = prompt("Drop item # (or 0 to cancel)")
                if ch2.isdigit() and 1<=int(ch2)<=len(inv):
                    it = inv.pop(int(ch2)-1)
                    print(C(f"{C_DIM}Dropped {it.name}.{R}")); input(C(f"{C_DIM}(Enter){R}"))
            elif ch == "g":
                self._guild_storage_screen(player, gs)

    def _guild_storage_screen(self, player, gs):
        from game_items import STORAGE_LIMIT
        while True:
            clear()
            print(C(f"\n{C_GOLD}{B}══  GUILD STORAGE  ══{R}  {C_DIM}({len(gs.items)}/{STORAGE_LIMIT} slots  ·  {gs.DEPOSIT_FEE}g/item deposit){R}\n"))
            if not gs.items:
                print(C(f"  {C_DIM}Empty. Store items here to free up bag space.{R}"))
            else:
                for i, it in enumerate(gs.items, 1):
                    rcol = it.rarity_col() if hasattr(it,"rarity_col") else C_WHITE
                    stat = f"  {C_DIM}{it.stat_line()}{R}" if hasattr(it,"stat_line") else ""
                    print(C(f"{C_GOLD}{B}[{i:>2}]{R} {rcol}{it.name:<26}{R}{stat}"))
            print()
            print(C(f"  {C_GOLD}[W]{R}{C_DIM} Withdraw  {C_GOLD}[S]{R} Store from bag  {C_GOLD}[0]{R} Back{R}"))
            ch = prompt("Choice").lower()
            if ch == "0": break
            elif ch == "w":
                ch2 = prompt("Withdraw slot # (0=cancel)")
                if ch2.isdigit() and 1<=int(ch2)<=len(gs.items):
                    ok, msg = gs.withdraw(int(ch2)-1, player)
                    print(C(f"{C_GREEN if ok else C_RED}{msg}{R}")); input(C(f"{C_DIM}(Enter){R}"))
            elif ch == "s":
                if not player.inventory:
                    print(C(f"{C_DIM}Your bag is empty.{R}")); input(C(f"{C_DIM}(Enter){R}")); continue
                for i,it in enumerate(player.inventory,1):
                    print(C(f"  {C_GOLD}[{i}]{R} {it.name}"))
                ch2 = prompt("Store bag slot # (0=cancel)")
                if ch2.isdigit() and 1<=int(ch2)<=len(player.inventory):
                    it = player.inventory[int(ch2)-1]
                    ok, msg = gs.deposit(it, player)
                    if ok: player.inventory.pop(int(ch2)-1)
                    print(C(f"{C_GREEN if ok else C_RED}{msg}{R}")); input(C(f"{C_DIM}(Enter){R}"))


    # ── MAIN LOOP ─────────────────────────────────────────────

    def enter(self):
        self.player.location_name = self.town_name
        while True:
            self._header(f"Region: {self.region_name}")
            print()
            print(C(f"{menu_opt('1', T('town.inn'),        T('town.inn_cost', cost=max(5,10+self.player.level*2)))}"))
            print(C(f"{menu_opt('2', T('town.shop'),       'Buy & sell items')}"))
            print(C(f"{menu_opt('3', T('town.quest_board'), f'Active: {len(self.player.active_quests)}/3')}"))
            print(C(f"{menu_opt('4', T('town.guild'),      'Rank up, clan, awaken')}"))
            print(C(f"{menu_opt('5', T('town.talk'),       'NPC dialogue')}"))
            print(C(f"{menu_opt('6', T('town.crafting'),   'Craft gear from materials')}"))
            print(C(f"{menu_opt('7', T('town.status'),     'View your full character sheet')}"))
            print(C(f"{menu_opt('8', T('town.inventory'),  'Manage your bag')}"))
            print(C(f"{menu_opt('S', T('town.save'),       '')}"))
            print(C(f"{menu_opt('R', T('town.recruit'),    'Hire party members')}"))
            print(C(f"{menu_opt('T', T('town.trade'),      'Trade items')}"))
            print(C(f"{menu_opt('K', T('town.codex'),      'Bestiary, crafting guide')}"))
            print(C(f"{menu_opt('C', 'Customise',        'Choose your class trait')}"))
            print(C(f"{menu_opt('C', 'Customise',          'Change your look & style perk')}"))
            print(C(f"{menu_opt('H', T('town.base'),       'Enter, build, upgrade')}"))
            if self._ship:
                print(C(f"{menu_opt('V', 'Board Ship',     'Sail to another continent')}"))
            print(C(f"{menu_opt('0', T('town.leave'),      '')}"))
            print()

            evo_ready = self.player.can_awaken()
            if evo_ready:
                print(C(f"\n{C_ORANGE}{B}  ★  Your class awakening is ready! Visit the Guild.  ★{R}"))

            ch = prompt("Choice").lower()
            if ch == "1":   self.inn()
            elif ch == "2": self.shop()
            elif ch == "3": self.quest_board()
            elif ch == "4": self.adventure_guild()
            elif ch == "5": self.talk_to_npcs()
            elif ch == "6": self.crafting_bench()
            elif ch == "7":
                clear(); self.player.show_status(); input(C(f"\n{C_DIM}(Press Enter){R}"))
            elif ch == "8": self.inventory_screen()
            elif ch == "s": self.player.save(); input(C(f"{C_DIM}(Press Enter){R}"))
            elif ch == "r":
                if self._companion_cb:
                    self._companion_cb()
                else:
                    print(C(f"\n{C_DIM}No adventurers for hire here.{R}"))
                    input(C(f"{C_DIM}(Press Enter){R}"))
            elif ch == "h":
                self._base_menu()
            elif ch == "t":
                from game_trading import open_trader_in_town
                open_trader_in_town(self.player, self.town_name)
            elif ch == "k":
                from game_codex import open_encyclopedia
                open_encyclopedia(self.player)
            elif ch == "c":
                from game_customise import open_customisation
                open_customisation(self.player)
            elif ch == "c":
                from game_customise import open_customise
                open_customise(self.player)
            elif ch == "v":
                if self._ship and self._world_map and self._ship_player:
                    self._world_map._board_ship(self._ship_player, self._ship)
                else:
                    print(C(f"\n{C_DIM}No ship available here.{R}"))
                    input(C(f"{C_DIM}(Enter){R}"))
            elif ch == "0":
                print(C(f"\n{C_DIM}{T('town.leave')}: {self.town_name}.{R}"))
                input(C(f"{C_DIM}(Press Enter){R}")); return
            else:
                print(C(f"\n{C_RED}Invalid choice.{R}")); input(C(f"{C_DIM}(Press Enter){R}"))


    def _base_menu(self):
        """Open the player base menu for this town's continent."""
        from game_base import BaseMenu, buy_plot_in_city
        player = self.player
        cid = getattr(self, '_continent_id', 'A')
        bx  = getattr(self, '_base_x', 0)
        by  = getattr(self, '_base_y', 0)
        if hasattr(player, 'bases') and player.bases.has_base(cid):
            base = player.bases.get_base(cid)
            BaseMenu(player, base).enter()
        else:
            buy_plot_in_city(player, self.town_name, cid, bx, by)


# ═══════════════════════════════════════════════════════════════
# DUNGEON
# ═══════════════════════════════════════════════════════════════

class Dungeon:
    def __init__(self, name, width=30, height=14, danger=2, player_level=1, has_boss=False, boss_override=None):
        self.name         = name
        self.width        = width
        self.height       = height
        self.danger       = danger
        self.player_level = player_level
        self.has_boss     = has_boss
        self.boss_name    = boss_override   # None = random, string = specific boss
        self.grid = [["#"]*width for _ in range(height)]
        self.px, self.py = 1, 1
        self.ex, self.ey = width-2, height-2
        self._generate()

    def _generate(self):
        for y in range(1,self.height-1):
            for x in range(1,self.width-1):
                self.grid[y][x] = "."
        if self.width >= 6 and self.height >= 6:
            for _ in range((self.width*self.height)//6):
                x = random.randint(2,self.width-3); y = random.randint(2,self.height-3)
                self.grid[y][x] = "#"
        self.grid[self.py][self.px] = "."
        tile = "B" if self.has_boss else "E"
        self.grid[self.ey][self.ex] = tile
        for _ in range(5):
            x = random.randint(2,self.width-3); y = random.randint(2,self.height-3)
            if self.grid[y][x] == ".": self.grid[y][x] = "T"
        if self.has_boss and self.boss_name is None:
            from game_enemies import BOSS_DEFS
            self.boss_name = random.choice(list(BOSS_DEFS.keys()))

    TILE_COLOURS = {
        "#": fg(80,60,60),  ".": fg(60,50,50),  "T": fg(255,215,0),
        "E": fg(80,200,80), "B": fg(220,60,60),
    }

    def render(self, player):
        clear()
        from game_term import _pad
        # Align map rows with all other C()-centred content
        cols = W()
        map_pad = " " * _pad()

        print(C(f"\n{C_RED}{B}DUNGEON: {self.name}{R}  {C_DIM}Danger {self.danger}{R}\n"))
        for y in range(self.height):
            row = map_pad
            for x in range(self.width):
                if x == self.px and y == self.py:
                    row += f"{fg(255,60,60)}{B}@{R}"
                else:
                    ch  = self.grid[y][x]
                    col = self.TILE_COLOURS.get(ch, "")
                    row += f"{col}{ch}{R}"
            print(row)

        # Legend
        print(C(f"\n{fg(255,60,60)}@{R} You  "
                f"{fg(80,60,60)}#{R} Wall  "
                f"{fg(60,50,50)}.{R} Floor  "
                f"{fg(255,215,0)}T{R} Chest  "
                f"{fg(80,200,80)}E{R} Exit  "
                f"{fg(220,60,60)}B{R} Boss"))
        # Status bar with HP/MP bars
        hp_w = max(10, min(18, cols // 8))
        mp_w = max(6,  min(12, cols // 12))
        print(C(f"\n{C_WHITE}{B}{player.name}{R}  "
                f"{C_DIM}Lv{R}{C_GOLD}{B}{player.level}{R}  "
                f"HP {hp_bar(player.hp,player.max_hp,hp_w)}  "
                f"MP {mp_bar(player.mp,player.max_mp,mp_w)}  "
                f"{C_GOLD}G:{player.gold}{R}"))
        # Controls hint
        mhint = f"{C_GOLD}WASD{R}" if (not player or getattr(player,"movement_mode","wasd")=="wasd") else f"{C_GOLD}Numpad{R}"
        print(C(f"\n{mhint}{C_DIM}=move  {R}"
                f"{C_GOLD}[E]{R}{C_DIM}Enter/chest  {R}"
                f"{C_GOLD}[I]{R}{C_DIM}Bag  {R}"
                f"{C_GOLD}[C]{R}{C_DIM}Codex  {R}"
                f"{C_GOLD}[?]{R}{C_DIM}Help  {R}"
                f"{C_GOLD}[Q]{R}{C_DIM}Retreat{R}"))

    def move(self, dx, dy):
        nx,ny = self.px+dx, self.py+dy
        if not (0<=nx<self.width and 0<=ny<self.height): return "blocked"
        tile = self.grid[ny][nx]
        if tile == "#": return "blocked"
        self.px,self.py = nx,ny
        if tile == "T": self.grid[ny][nx] = "."; return "chest"
        if tile == "E": return "exit"
        if tile == "B": return "boss"
        base_enc = 0.12 + self.danger*0.03
        if random.random() < base_enc: return "encounter"
        return "moved"

    def enter(self, player):
        from game_items import ITEM_POOL
        from game_input import InputHandler
        inp = InputHandler(mode=getattr(player, "movement_mode", "wasd"))
        self._last_msg = ""
        while True:
            self.render(player)
            action = inp.get_action()
            if action[0] == "cmd":
                cmd = action[1]
                if cmd in ("quit", "save"):
                    print(C(f"\n{C_DIM}You retreat from the dungeon.{R}"))
                    import time; time.sleep(0.4); return "left"
                elif cmd == "inventory":
                    from main import _quick_inventory
                    _quick_inventory(player)
                elif cmd == "codex":
                    from game_codex import open_encyclopedia
                    open_encyclopedia(player)
                elif cmd == "help":
                    clear()
                    print(C(f"\n{C_CYAN}{B}DUNGEON CONTROLS{R}\n"))
                    print(C(f"{C_GOLD}WASD{R}{C_DIM}/Arrows = move{R}"))
                    print(C(f"{C_GOLD}[E]{R}{C_DIM} Enter/open chest when standing on it{R}"))
                    print(C(f"{C_GOLD}[I]{R}{C_DIM} Quick bag — use potions, equip gear{R}"))
                    print(C(f"{C_GOLD}[C]{R}{C_DIM} Encyclopedia — enemies, crafting guide{R}"))
                    print(C(f"{C_GOLD}[Q]{R}{C_DIM} Retreat from the dungeon{R}"))
                    input(C(f"\n{C_DIM}(Press Enter){R}"))
                continue
            if action[0] != "move":
                continue
            _, dx, dy = action
            result = self.move(dx, dy)

            if result == "blocked":
                pass  # just re-render

            elif result == "chest":
                gold = random.randint(20,60)
                player.gold += gold
                loot = random.choice(list(ITEM_POOL.values()))()
                player.add_item(loot)
                print(C(f"\n{C_GOLD}Chest opened! +{gold} gold{R}, found {C_WHITE}{loot}{R}!"))
                input(C(f"{C_DIM}(Press Enter){R}"))

            elif result == "encounter":
                enemy = generate_enemy("dungeon", self.danger, player.level)
                # Stealth evasion in dungeon
                if player.try_stealth_evade():
                    print(C(f"\n{C_PURPLE}You hear {enemy.name} nearby... and press yourself into the shadows.{R}"))
                    input(C(f"{C_DIM}(Press Enter){R}"))
                    continue
                first_strike = player.in_stealth
                print()
                print_sprite(enemy.name)
                print(C(f"\n{C_RED}!! {enemy.name} emerges from the shadows!{R}"))
                input(C(f"{C_DIM}(Press Enter to fight){R}"))
                outcome = run_combat(player, enemy, first_strike=first_strike)
                if outcome == "defeat": return "defeat"

            elif result == "boss":
                boss = create_boss(self.boss_name)
                print()
                print_sprite(boss.name)
                print(C(f"\n{C_RED}{B}*** THE BOSS AWAITS: {boss.name} ***{R}"))
                input(C(f"{C_DIM}(Press Enter to fight){R}"))
                outcome = run_combat(player, boss, allow_escape=False)
                if outcome == "defeat": return "defeat"
                clear()
                print(C(f"\n{C_GOLD}{B}★★★  DUNGEON CLEARED: {self.name}  ★★★{R}\n"))
                player.flags[f"dungeon_cleared_{self.name}"] = True
                input(C(f"{C_DIM}(Press Enter){R}")); return "cleared"

            elif result == "exit":
                print(C(f"\n{C_GREEN}You escaped from {self.name}.{R}"))
                input(C(f"{C_DIM}(Press Enter){R}")); return "escaped"

            if not player.is_alive(): return "defeat"
