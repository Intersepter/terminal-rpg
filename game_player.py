import random, json, os
from game_term import C, P, div, clr, W, H, hpbar, mpbar, box_top, box_mid, box_bot, get_size
from game_items import Item, Equipment, item_from_dict, status_from_dict, roll_drops, ITEM_POOL
from game_jobs import create_job, STARTER_JOBS

_R="[0m"; _B="[1m"
def _fg(r,g,b): return f"[38;2;{r};{g};{b}m"
_GOLD=_fg(255,215,0); _WHITE=_fg(255,255,255); _DIM=_fg(120,120,120)
_GREEN=_fg(80,200,80); _RED=_fg(220,60,60); _CYAN=_fg(80,220,220)
_BLUE=_fg(80,130,220); _YELL=_fg(240,200,60); _ORAN=_fg(220,140,40)
_PURP=_fg(180,80,220)
def _hpb(c,m,w=16):
    f=c/m if m else 0; fi=int(w*f); cl=_GREEN if f>0.5 else _YELL if f>0.25 else _RED
    return f"{cl}{chr(9608)*fi}{_DIM}{chr(9617)*(w-fi)}{_R} {cl}{c}/{m}{_R}"
def _mpb(c,m,w=10):
    f=c/m if m else 0; fi=int(w*f)
    return f"{_BLUE}{chr(9608)*fi}{_DIM}{chr(9617)*(w-fi)}{_R} {_BLUE}{c}/{m}{_R}"
def _clr(): import os
from game_lang import T, set_language, LANG, LANGUAGE_NAMES
def _div(w=52): return f"  {_DIM}{"-"*w}{_R}"

SAVE_FILE = "savegame.json"

RANKS = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS", "Legend"]
RANK_COST = {"F": 0, "E": 100, "D": 250, "C": 500, "B": 1000,
             "A": 2500, "S": 5000, "SS": 10000, "SSS": 25000}

# Quest definitions — unlocked per class and used for class evolution
EVOLUTION_QUESTS = {
    "quest_swordsman_awakening": {
        "title": "Trial of the Blade",
        "desc":  "Slay 5 Bandits to prove your mastery of the sword.",
        "type":  "kill", "target": "Bandit", "required": 5, "progress": 0,
        "reward_gold": 300, "reward_exp": 400,
    },
    "quest_mage_awakening": {
        "title": "Arcane Initiation",
        "desc":  "Defeat 5 Stone Golems using magic.",
        "type":  "kill", "target": "Stone Golem", "required": 5, "progress": 0,
        "reward_gold": 300, "reward_exp": 400,
    },
    "quest_rogue_awakening": {
        "title": "Into the Shadows",
        "desc":  "Eliminate 5 Cultists lurking in dungeons.",
        "type":  "kill", "target": "Cultist", "required": 5, "progress": 0,
        "reward_gold": 300, "reward_exp": 400,
    },
    "quest_tank_awakening": {
        "title": "Unbreakable",
        "desc":  "Survive 5 battles without using any potions.",
        "type":  "survive", "target": "", "required": 5, "progress": 0,
        "reward_gold": 300, "reward_exp": 400,
    },
    "quest_healer_awakening": {
        "title": "The Light Within",
        "desc":  "Heal yourself 8 times using Holy Light or Mend.",
        "type":  "heal_skill", "target": "", "required": 8, "progress": 0,
        "reward_gold": 300, "reward_exp": 400,
    },
}

GUILD_QUEST_TARGETS = ["Wolf", "Goblin", "Skeleton", "Bandit", "Harpy",
                       "Stone Golem", "Sand Wyrm", "Ice Wolf", "Cultist"]


class Player:
    def __init__(self, name="Hero", job_name="Swordsman"):
        self.name = name
        self.job  = create_job(job_name)

        # Core stats — base + job bonus
        base_hp  = 100 + self.job.hp_bonus
        base_mp  = 30  + self.job.mp_bonus
        base_atk = 10  + self.job.atk_bonus

        self.max_hp = base_hp
        self.hp     = base_hp
        self.max_mp = base_mp
        self.mp     = base_mp
        self.atk    = base_atk
        self.defense= 5 + self.job.defend_bonus

        self.level      = 1
        self.exp        = 0
        self.exp_to_next= 50
        self.gold       = 100
        self.rank       = "F"
        self.clan       = None
        self.title      = None

        self.skills     = list(self.job.skills)  # copy
        self.status_effects = []

        # Equipment slots
        self.equipped = {"weapon":None,"armor":None,"helmet":None,"shield":None,"cloak":None,"ring":None,"amulet":None}

        # Inventory: stacked items via inventory_add
        from game_items import inventory_add as _ia
        self.inventory = []
        _ia(self.inventory, Item("Potion", "heal", 40, 10))
        _ia(self.inventory, Item("Potion", "heal", 40, 10))
        _ia(self.inventory, Item("Ether", "mana", 25, 15))
        _ia(self.inventory, Item("God Potion", "god", 5, 500))   # starts with 1 god potion

        self.active_quests    = []
        self.completed_quests = []
        self.evolution_quest  = None   # active class quest dict or None
        self.awakened         = False

        self.location_name = "Starting Town"
        self.flags = {}
        self.movement_mode = "wasd"   # "wasd" or "numpad"
        self.god_immunity_turns = 0   # moves of invulnerability after god potion

        # Party system
        from game_party import Party
        self.party = Party()

        # Story manager
        from game_stories import StoryManager
        self.stories = StoryManager()

        # Base manager
        from game_base import BaseManager
        self.bases = BaseManager()

        # Guild storage
        from game_items import GuildStorage
        self.guild_storage = GuildStorage()

        # Stealth stat — reduces enemy detection range, enables sneak attacks
        # Base per job is set in jobs.py via stealth_bonus
        self.stealth = 5 + getattr(self.job, "stealth_bonus", 0)
        self.active_trait    = None    # current customisation trait
        self.gold_drop_bonus = 0       # % extra gold from kills (Thief trait)
        self.in_stealth = False   # True if player hasn't moved or attacked recently
        self.stealth_turns = 0    # turns remaining in stealth window

    # ----------------------------------------------------------
    # COMBAT HELPERS
    # ----------------------------------------------------------

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg):
        actual = max(1, dmg - self.defense // 3)
        self.hp = max(0, self.hp - actual)
        from game_customise import tick_legendary_quest as _tlq
        _tlq(self,"damage_taken",actual)
        return actual

    def try_dodge(self):
        return random.randint(1, 100) <= (self.job.dodge_bonus + self.level // 2)

    def calc_crit(self, base_damage):
        crit_chance = (self.job.crit_bonus + self.level // 3
                       + getattr(self, "_crit_bonus_custom", 0))
        if random.randint(1, 100) <= crit_chance:
            return True, int(base_damage * 1.75)
        return False, base_damage

    # ── STEALTH ──────────────────────────────────────────────
    def get_stealth(self):
        """Total stealth score including equipment and party bonuses."""
        bonus = 0
        for eq in self.equipped.values():
            if eq and hasattr(eq, "stealth_bonus"):
                bonus += eq.stealth_bonus
        party_bonus = self.party.total_stealth_bonus() if hasattr(self,"party") else 0
        return self.stealth + bonus + party_bonus

    def party_atk_bonus(self):
        return self.party.total_atk_bonus() if hasattr(self,"party") else 0

    def party_def_bonus(self):
        return self.party.total_def_bonus() if hasattr(self,"party") else 0

    def party_heal_bonus(self):
        return self.party.total_heal_bonus() if hasattr(self,"party") else 0

    def party_skill_power(self):
        return self.party.total_skill_power() if hasattr(self,"party") else 0

    def stealth_first_strike(self, base_damage):
        """If attacking from stealth, deal 1.5x damage and print message."""
        if self.in_stealth:
            from game_customise import tick_legendary_quest as _tlq
            _tlq(self,"stealth_kill")
            self.in_stealth = False
            self.stealth_turns = 0
            mult = 1.5 + self.get_stealth() * 0.02   # higher stealth = better bonus
            dmg = int(base_damage * mult)
            print(C(f"{_PURP}{_B}SNEAK ATTACK!{_R} {_YELL}×{mult:.1f} multiplier → {dmg} damage!{_R}"))
            return dmg
        return base_damage

    def try_stealth_evade(self):
        """
        Called when an enemy would trigger an encounter.
        Returns True if stealth lets you slip past silently.
        """
        evade_chance = max(5, self.get_stealth() * 4)   # 5–60%
        return random.randint(1, 100) <= evade_chance

    def tick_stealth(self):
        """Called every move step. Stealth fades after a few turns."""
        if self.in_stealth:
            self.stealth_turns -= 1
            if self.stealth_turns <= 0:
                self.in_stealth = False

    def defend(self):
        bonus = 8 + self.job.defend_bonus // 2
        old = self.defense
        self.defense += bonus
        print(C(f"[{self.name} defends! DEF temporarily +{bonus}]"))
        return bonus

    def get_equip_atk_bonus(self):
        from game_items import Equipment as _Eq
        eq_bonus = sum(e.atk_bonus for e in self.equipped.values() if isinstance(e,_Eq))
        return eq_bonus + self.party_atk_bonus()

    def get_equip_def_bonus(self):
        from game_items import Equipment as _Eq
        return sum(e.def_bonus for e in self.equipped.values() if isinstance(e,_Eq))

    def get_equip_hp_bonus(self):
        return sum(
            e.hp_bonus for e in self.equipped.values()
            if isinstance(e, Equipment)
        )

    def add_status(self, effect):
        # Don't stack same effect
        for e in self.status_effects:
            if e.name == effect.name:
                e.duration = max(e.duration, effect.duration)
                return
        self.status_effects.append(effect)
        print(C(f"[{self.name} is afflicted: {effect.name}!]"))

    def process_status_start(self):
        for e in self.status_effects[:]:
            e.on_turn_start(self)

    def process_status_end(self):
        for e in self.status_effects[:]:
            e.on_turn_end(self)
            if not e.is_active():
                print(C(f"[{e.name} on {self.name} has worn off.]"))
                self.status_effects.remove(e)

    def check_god_potion(self):
        """If HP hits 0, auto-trigger god potion if carried.
        Sets god_immunity_turns=30 so the world map skips encounters for 30 moves.
        Returns True if triggered."""
        if self.hp <= 0:
            for i, item in enumerate(self.inventory):
                if item.item_type == "god":
                    self.inventory.pop(i)
                    self.hp = max(5, self.max_hp // 5)
                    self.mp = min(self.max_mp, self.mp + self.max_mp // 2)
                    self.status_effects.clear()
                    self.god_immunity_turns = 30   # 30 moves of safety
                    print(C(f"\n{_PURP}{_B}★★★ {T('god.activated')} ★★★{_R}"))
                    print(C(f"{_GREEN}{T('god.rises', name=self.name, hp=self.hp)}{_R}"))
                    print(C(f"{_DIM}Enemies will avoid you for 30 moves.{_R}\n"))
                    return True
        return False

    # ----------------------------------------------------------
    # LEVELING
    # ----------------------------------------------------------

    def gain_exp(self, amount):
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.4)

            # Level-up stat growth varies by job
            hp_gain  = 15 + self.job.hp_bonus // 5
            atk_gain = 2  + self.job.atk_bonus // 6
            mp_gain  = 4  + self.job.mp_bonus // 8

            self.max_hp  += hp_gain
            self.max_mp  += mp_gain
            self.atk     += atk_gain
            self.defense += 1
            self.hp       = self.max_hp
            self.mp       = self.max_mp
            leveled = True
            print(C(f"\n*** LEVEL UP! {self.name} is now Level {self.level}! ***"))
            print(C(f"    HP+{hp_gain}  ATK+{atk_gain}  MP+{mp_gain}"))
        return leveled

    # ----------------------------------------------------------
    # INVENTORY
    # ----------------------------------------------------------

    def add_item(self, item):
        from game_items import inventory_add
        inventory_add(self.inventory, item)

    def show_inventory(self):
        if not self.inventory:
            print(C(f"{_DIM}Your bag is empty.{_R}"))
            return
        print(C(f"\n{_CYAN}{_B}#{'':<3} {'Item':<26} {'Type':<12} Value{_R}"))
        print(C(f"{_DIM}{'-'*52}{_R}"))
        for i, it in enumerate(self.inventory, 1):
            vstr = str(it.value) if it.value else "-"
            it_col = _GOLD if it.item_type == "god" else _WHITE
            print(C(f"{_GOLD}{i:<4}{_R} {it_col}{it.name:<26}{_R} {_DIM}{it.item_type:<12}{_R} {vstr}"))

    def use_inventory_item(self):
        usable = [(i, it) for i, it in enumerate(self.inventory)
                  if it.item_type in ("heal", "mana")]
        if not usable:
            print(C("No usable items."))
            return False

        print(C("\n--- Use Item ---"))
        for num, (i, it) in enumerate(usable, 1):
            vstr = f"+{it.value}" if it.item_type == "heal" else f"+{it.value} MP"
            print(C(f"{num}. {it.name} ({vstr})"))
        print(C(f"{len(usable)+1}. Cancel"))

        try:
            choice = int(input(C("> ")))
        except ValueError:
            return False

        if choice == len(usable) + 1:
            return False
        if not (1 <= choice <= len(usable)):
            print(C("Invalid."))
            return False

        idx, item = usable[choice - 1]
        result = item.use(self)
        if result:
            self.inventory.pop(idx)
            # Track healer quest
            if item.name in ("Holy Light", "Mend"):
                self._tick_evolution_quest("heal_skill")
        return result

    def equip_item(self):
        from game_items import Equipment as _Eq
        equippable = [(i,it) for i,it in enumerate(self.inventory) if isinstance(it,_Eq)]
        if not equippable:
            print(C(f"\n{_DIM}No equipment in bag.{_R}")); return
        while True:
            print(C(f"\n{_CYAN}{_B}── EQUIP ──{_R}"))
            for num,(i,it) in enumerate(equippable,1):
                ac = getattr(it,'allowed_classes',None)
                ok_cls = (ac is None or self.job.name in ac)
                rcol = it.rarity_col() if hasattr(it,'rarity_col') else _WHITE
                cls_note = f"  {_RED}({self.job.name} cannot equip){_R}" if not ok_cls else ""
                curr = self.equipped.get(it.slot)
                curr_note = f"  {_DIM}(replaces {curr.name}){_R}" if curr else ""
                print(C(f"  {_GOLD}[{num}]{_R} {rcol}{it.name:<22}{_R}  {_DIM}[{it.slot}]{_R}  {_DIM}{it.stat_line()}{_R}{cls_note}{curr_note}"))
            print(C(f"  {_GOLD}[0]{_R}{_DIM} Cancel{_R}"))
            try: choice = int(input(C(f"\n{_GOLD}>{_R} Equip # ")))
            except ValueError: break
            if choice == 0: break
            if not (1 <= choice <= len(equippable)): print(C(f"{_RED}Invalid.{_R}")); continue
            _, item = equippable[choice-1]
            # Class check
            ac = getattr(item,'allowed_classes',None)
            if ac and self.job.name not in ac:
                allowed = ', '.join(ac)
                print(C(f"\n{_RED}Cannot equip — requires: {allowed}{_R}"))
                input(C(f"{_DIM}(Press Enter){_R}")); continue
            # Swap out old
            old = self.equipped.get(item.slot)
            if old:
                self.inventory.append(old)
                self.max_hp  -= old.hp_bonus
                self.max_mp  -= old.mp_bonus
                self.atk     -= old.atk_bonus
                self.defense -= getattr(old,'def_bonus',0)
                self.stealth -= getattr(old,'stealth_bonus',0)
            # Equip new
            self.equipped[item.slot] = item
            self.inventory.remove(item)
            self.max_hp  += item.hp_bonus
            self.max_mp  += item.mp_bonus
            self.atk     += item.atk_bonus
            self.defense += getattr(item,'def_bonus',0)
            self.stealth += getattr(item,'stealth_bonus',0)
            self.hp = min(self.hp, self.max_hp)
            print(C(f"\n{_GREEN}Equipped {item.name}!  {_DIM}{item.stat_line()}{_R}"))
            input(C(f"{_DIM}(Press Enter){_R}"))
            break
    # ----------------------------------------------------------
    # QUESTS
    # ----------------------------------------------------------

    def show_quests(self):
        print(C("\n=== ACTIVE QUESTS ==="))
        if not self.active_quests and not self.evolution_quest:
            print(C("No active quests."))
        for q in self.active_quests:
            prog = q.get("progress", 0)
            req  = q.get("required", q.get("required_kills", 1))
            print(C(f"[{prog}/{req}] {q['title']} — {q['desc']}"))
        if self.evolution_quest and not self.evolution_quest.get("done"):
            q = self.evolution_quest
            print(C(f"[CLASS] [{q['progress']}/{q['required']}] {q['title']} — {q['desc']}"))

        if self.completed_quests:
            print(C(f"\nCompleted: {len(self.completed_quests)} quest(s)"))

    def update_quests_on_kill(self, enemy_name):
        for q in self.active_quests:
            if q.get("type") == "kill" and q.get("target") == enemy_name:
                q["progress"] = q.get("progress", 0) + 1
                print(C(f"Quest [{q['title']}]: {q['progress']}/{q['required']}"))
        # Evolution quest
        if (self.evolution_quest
                and not self.evolution_quest.get("done")
                and self.evolution_quest.get("type") == "kill"
                and self.evolution_quest.get("target") == enemy_name):
            self.evolution_quest["progress"] += 1
            p = self.evolution_quest["progress"]
            r = self.evolution_quest["required"]
            print(C(f"[CLASS QUEST] {self.evolution_quest['title']}: {p}/{r}"))

    def _tick_evolution_quest(self, quest_type):
        if (self.evolution_quest
                and not self.evolution_quest.get("done")
                and self.evolution_quest.get("type") == quest_type):
            self.evolution_quest["progress"] += 1

    def turn_in_quests(self):
        earned_gold = 0
        earned_exp  = 0
        done = []
        for q in self.active_quests:
            req = q.get("required", q.get("required_kills", 1))
            if q.get("progress", 0) >= req:
                earned_gold += q.get("reward_gold", 0)
                earned_exp  += q.get("reward_exp", 0)
                done.append(q)
                print(C(f"Quest complete: {q['title']}!"))
        for q in done:
            self.active_quests.remove(q)
            self.completed_quests.append(q["title"])
            from game_customise import tick_legendary_quest as _tlq
            _tlq(self,"guild_quest")

        if earned_gold:
            self.gold += earned_gold
            self.gain_exp(earned_exp)
            print(C(f"Rewards: +{earned_gold} gold, +{earned_exp} EXP"))
        elif not done:
            print(C("No quests ready to turn in."))

        # Check evolution quest
        if (self.evolution_quest
                and not self.evolution_quest.get("done")
                and self.evolution_quest["progress"] >= self.evolution_quest["required"]):
            self.evolution_quest["done"] = True
            g = self.evolution_quest.get("reward_gold", 300)
            e = self.evolution_quest.get("reward_exp", 400)
            self.gold += g
            self.gain_exp(e)
            print(C(f"\n*** CLASS QUEST COMPLETE: {self.evolution_quest['title']} ***"))
            print(C(f"You are ready to awaken! Visit a trainer NPC to evolve your class."))
            print(C(f"Rewards: +{g} gold, +{e} EXP"))

    def start_evolution_quest(self):
        quest_id = self.job.evolution_quest
        if not quest_id:
            print(C("Your class has no evolution quest."))
            return
        if self.evolution_quest:
            print(C(f"Class quest already active: {self.evolution_quest['title']}"))
            return
        import copy
        q = copy.deepcopy(EVOLUTION_QUESTS.get(quest_id))
        if q:
            self.evolution_quest = q
            print(C(f"Class quest started: {q['title']}"))
            print(C(f"{q['desc']}"))
        else:
            print(C("Could not find that class quest."))

    def can_awaken(self):
        return (self.evolution_quest is not None
                and self.evolution_quest.get("done", False)
                and not self.awakened
                and self.job.evolution is not None)

    def awaken(self):
        if not self.can_awaken():
            print(C("You are not ready to awaken yet."))
            return False
        old = self.job.name
        new = self.job.evolution
        from game_jobs import create_job
        self.job     = create_job(new)
        self.skills  = list(self.job.skills)
        self.awakened = True

        # Apply stat bonuses from new job
        self.max_hp  += self.job.hp_bonus
        self.max_mp  += self.job.mp_bonus
        self.atk     += self.job.atk_bonus
        self.defense += self.job.defend_bonus
        self.hp = self.max_hp
        self.mp = self.max_mp

        print(C(f"\n*** AWAKENING! {self.name} evolves from {old} to {new}! ***"))
        print(C(f"New skills unlocked!"))
        for sk in self.skills:
            print(C(f"  -> {sk}"))
        return True

    # ----------------------------------------------------------
    # RANK / TITLE
    # ----------------------------------------------------------

    def promote_rank(self):
        idx = RANKS.index(self.rank)
        if idx >= len(RANKS) - 1:
            print(C("You are already at the highest rank!"))
            return False
        next_rank = RANKS[idx + 1]
        cost = RANK_COST.get(next_rank, 9999)
        if self.gold >= cost:
            self.gold -= cost
            self.rank = next_rank
            # Rank-up bonus
            self.max_hp += 10
            self.max_mp += 5
            print(C(f"\n{_GOLD}{_B}★ Promoted to Rank {self.rank}! +10 max HP, +5 max MP{_R}"))
            return True
        else:
            print(C(f"\n{_RED}{T('ui.not_enough_gold')} Need {cost}g for Rank {next_rank}.{_R}"))
            return False

    # ----------------------------------------------------------
    # DISPLAY
    # ----------------------------------------------------------

    def show_status(self):
        try:
            from game_art import print_sprite
            print_sprite(self.job.name, label=f"{self.name} — {self.job.name}")
        except Exception:
            pass
        effects   = ", ".join(str(e) for e in self.status_effects) or "None"
        evo_tag   = f" {_YELL}{_B}★ READY TO AWAKEN!{_R}" if self.can_awaken() else ""
        RANK_COL  = {"S":_GOLD,"SS":_GOLD,"SSS":_GOLD,"Legend":_ORAN,"A":_CYAN,"B":_GREEN}
        rc        = RANK_COL.get(self.rank, _WHITE)
        print()
        print(C(f"{_CYAN}{_B}════  CHARACTER STATUS  ════{_R}"))
        print()
        print(C(f"{_DIM}Name  :{_R} {_WHITE}{_B}{self.name}{_R}"))
        print(C(f"{_DIM}Class :{_R} {_PURP}{self.job.name}{_R}{evo_tag}"))
        print(C(f"{_DIM}Level :{_R} {_YELL}{self.level}{_R}   {_DIM}EXP{_R} {_CYAN}{self.exp}/{self.exp_to_next}{_R}"))
        print(C(f"{_DIM}Rank  :{_R} {rc}{_B}{self.rank}{_R}   {_DIM}Clan:{_R} {_CYAN}{self.clan or 'None'}{_R}"))
        print(C(f"{_DIM}Gold  :{_R} {_GOLD}{self.gold}{_R}"))
        print(C(f"{_DIM}{'-'*40}{_R}"))
        print(C(f"{_DIM}HP    :{_R} {_hpb(self.hp, self.max_hp)}"))
        print(C(f"{_DIM}MP    :{_R} {_mpb(self.mp, self.max_mp)}"))
        print(C(f"{_DIM}ATK   :{_R} {_RED}{self.atk}{_R}   {_DIM}DEF:{_R} {_BLUE}{self.defense}{_R}   {_DIM}STL:{_R} {_PURP}{self.get_stealth()}{_R}"))
        print(C(f"{_DIM}{'-'*40}{_R}"))
        SLOT_LABELS = {"weapon":"Weapon","armor":"Armor","helmet":"Helmet",
                       "shield":"Shield","cloak":"Cloak","ring":"Ring","amulet":"Amulet"}
        for sl, lb in SLOT_LABELS.items():
            eq = self.equipped.get(sl)
            val = f"{_WHITE}{eq.name}{_R}  {_DIM}{eq.stat_line()}{_R}" if eq else f"{_DIM}—{_R}"
            print(C(f"{_DIM}{lb:<7}:{_R} {val}"))
        print(C(f"{_DIM}Status:{_R} {_YELL}{effects}{_R}"))
        # Party summary
        if hasattr(self,"party") and self.party.members:
            print(C(f"\n{_CYAN}{_B}Party:{_R}"))
            for m in self.party.members:
                print(m.status_line())

    def to_dict(self):
        # Temporarily remove active trait so stats are saved as BASE values
        # from_dict will re-apply the trait on load (no double-stacking)
        active = getattr(self, "active_trait", None)
        if active:
            from game_customise import _remove_trait as _rt
            _rt(self, active)
        result = {
            "name": self.name,
            "job":  self.job.name,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "max_hp": self.max_hp, "hp": self.hp,
            "max_mp": self.max_mp, "mp": self.mp,
            "atk": self.atk, "defense": self.defense,
            "gold": self.gold,
            "rank": self.rank,
            "clan": self.clan,
            "title": self.title,
            "awakened": self.awakened,
            "equipped": {
                slot: (eq.to_dict() if eq else None)
                for slot, eq in self.equipped.items()
            },
            "inventory": [it.to_dict() for it in self.inventory],
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "evolution_quest": self.evolution_quest,
            "status_effects": [e.to_dict() for e in self.status_effects],
            "location_name": self.location_name,
            "flags": self.flags,
            "active_trait":    getattr(self, "active_trait", None),
            "gold_drop_bonus": getattr(self, "gold_drop_bonus", 0),
            "stealth": self.stealth,
            "movement_mode": self.movement_mode,
            "god_immunity_turns": self.god_immunity_turns,
            "language": __import__("game_lang").LANG,
            "party": self.party.to_dict() if hasattr(self,"party") else {"members":[]},
            "stories": self.stories.to_dict() if hasattr(self,"stories") else {},
            "bases": self.bases.to_dict() if hasattr(self,"bases") else {},
            "custom_style_id":     getattr(self,"_custom_style_id",None),
            "custom_style_label":  getattr(self,"_custom_style_label",None),
            "custom_style_colour": getattr(self,"_custom_style_colour",None),
            "custom_sprite_tag":   getattr(self,"_custom_sprite_tag",None),
            "custom_perk_delta":   getattr(self,"_custom_perk_delta",{}),

            "guild_storage": self.guild_storage.to_dict() if hasattr(self,"guild_storage") else {"items":[]},
        }
        # Re-apply trait so player object is restored after serialisation
        if active:
            from game_customise import _apply_trait as _at
            _at(self, active)
        return result

    @classmethod
    def from_dict(cls, d):
        p = cls.__new__(cls)
        p.name  = d["name"]
        from game_jobs import create_job
        p.job   = create_job(d.get("job", "Swordsman"))
        p.level = d.get("level", 1)
        p.exp   = d.get("exp", 0)
        p.exp_to_next = d.get("exp_to_next", 50)
        p.max_hp = d.get("max_hp", 100); p.hp = d.get("hp", p.max_hp)
        p.max_mp = d.get("max_mp", 30);  p.mp = d.get("mp", p.max_mp)
        p.atk    = d.get("atk", 10)
        p.defense= d.get("defense", 5)
        p.gold   = d.get("gold", 100)
        p.rank   = d.get("rank", "F")
        p.clan   = d.get("clan")
        p.title  = d.get("title")
        p.awakened = d.get("awakened", False)
        p.skills = list(p.job.skills)

        equipped_raw = d.get("equipped", {})
        p.equipped = {}
        for slot in ("weapon", "armor", "helmet", "shield", "cloak", "ring", "amulet"):
            raw = equipped_raw.get(slot)
            p.equipped[slot] = item_from_dict(raw) if raw else None

        from game_items import inventory_add
        p.inventory = []
        for i in d.get("inventory", []):
            inventory_add(p.inventory, item_from_dict(i))
        p.active_quests    = d.get("active_quests", [])
        p.completed_quests = d.get("completed_quests", [])
        p.evolution_quest  = d.get("evolution_quest")
        p.status_effects   = [status_from_dict(e) for e in d.get("status_effects", [])]
        p.location_name    = d.get("location_name", "Unknown")
        p.flags            = d.get("flags", {})
        p.active_trait    = d.get("active_trait", None)
        p.gold_drop_bonus = d.get("gold_drop_bonus", 0)
        p.stealth               = d.get("stealth", 5 + getattr(p.job, "stealth_bonus", 0))
        p.movement_mode         = d.get("movement_mode", "wasd")
        p.in_stealth            = False
        p.stealth_turns         = 0
        p.god_immunity_turns    = d.get("god_immunity_turns", 0)
        saved_lang = d.get("language")
        if saved_lang:
            from game_lang import set_language as _sl, LANGUAGE_NAMES as _LN
            if saved_lang in _LN: _sl(saved_lang)
        from game_party import Party
        p.party = Party.from_dict(d.get("party", {"members":[]}))
        from game_stories import StoryManager
        p.stories = StoryManager.from_dict(d.get("stories", {}))
        from game_base import BaseManager
        p.bases = BaseManager.from_dict(d.get("bases", {}))
        from game_items import GuildStorage
        p.guild_storage = GuildStorage.from_dict(d.get("guild_storage", {"items":[]}))
        # Restore custom style (stats already baked into saved stats)
        p._custom_style_id     = d.get("custom_style_id")
        p._custom_style_label  = d.get("custom_style_label")
        p._custom_style_colour = d.get("custom_style_colour")
        p._custom_sprite_tag   = d.get("custom_sprite_tag", "")
        p._custom_perk_delta   = d.get("custom_perk_delta", {})
        # Re-apply active trait bonuses (must be last — all stats must exist)
        if p.active_trait:
            from game_customise import _apply_trait
            _apply_trait(p, p.active_trait)
        return p

    def save(self, filename=SAVE_FILE):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(C(f"Game saved to {filename}."))

    @classmethod
    def load(cls, filename=SAVE_FILE):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
