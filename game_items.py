import random, copy

# ═══════════════════════════════════════════════════════════════
# STATUS EFFECTS
# ═══════════════════════════════════════════════════════════════

class StatusEffect:
    def __init__(self, name, duration):
        self.name = name; self.duration = duration
    def on_turn_start(self, target): pass
    def on_turn_end(self, target): self.duration -= 1
    def is_active(self): return self.duration > 0
    def __repr__(self): return f"{self.name}({self.duration})"
    def to_dict(self): return {"type": self.__class__.__name__, "duration": self.duration}

class Poison(StatusEffect):
    def __init__(self, duration=3, damage=5):
        super().__init__("Poison", duration); self.damage = damage
    def on_turn_start(self, target):
        target.hp = max(0, target.hp - self.damage)
        print(f"  [X] {target.name} takes {self.damage} poison damage!")
    def to_dict(self): return {"type":"Poison","duration":self.duration,"damage":self.damage}

class Burn(StatusEffect):
    def __init__(self, duration=3, damage=4):
        super().__init__("Burn", duration); self.damage = damage
    def on_turn_start(self, target):
        target.hp = max(0, target.hp - self.damage)
        print(f"  [~] {target.name} burns for {self.damage} damage!")
    def to_dict(self): return {"type":"Burn","duration":self.duration,"damage":self.damage}

class Regen(StatusEffect):
    def __init__(self, duration=3, heal=6):
        super().__init__("Regen", duration); self.heal = heal
    def on_turn_start(self, target):
        old = target.hp; target.hp = min(target.max_hp, target.hp + self.heal)
        print(f"  [+] {target.name} regenerates {target.hp - old} HP!")
    def to_dict(self): return {"type":"Regen","duration":self.duration,"heal":self.heal}

class Stun(StatusEffect):
    def __init__(self, duration=1): super().__init__("Stun", duration)
    def to_dict(self): return {"type":"Stun","duration":self.duration}

def status_from_dict(d):
    t = d["type"]
    if t=="Poison": return Poison(d["duration"],d.get("damage",5))
    if t=="Burn":   return Burn(d["duration"],d.get("damage",4))
    if t=="Regen":  return Regen(d["duration"],d.get("heal",6))
    if t=="Stun":   return Stun(d["duration"])
    return StatusEffect(t,d["duration"])


# ═══════════════════════════════════════════════════════════════
# SKILLS
# ═══════════════════════════════════════════════════════════════

class Skill:
    def __init__(self, name, damage=0, heal=0, mana_cost=0,
                 status_effect=None, status_chance=0, description="",
                 heal_ally=False):
        self.name=name; self.damage=damage; self.heal=heal
        self.mana_cost=mana_cost; self.status_effect=status_effect
        self.status_chance=status_chance; self.description=description
        self.heal_ally = heal_ally   # True = healer will use this on party members

    def can_use(self, user):
        return user.mp >= self.mana_cost or user.hp > (self.mana_cost - user.mp)

    def pay_cost(self, user):
        if user.mp >= self.mana_cost:
            user.mp -= self.mana_cost
        else:
            overflow = self.mana_cost - user.mp
            user.mp = 0; user.hp -= overflow
            try:
                from game_term import C as _pC
            except ImportError:
                _pC = lambda x: x
            print(_pC(f"[!] {user.name} force-casts {self.name}, burning {overflow} HP!"))

    def use(self, user, target=None):
        try:
            from game_term import C as _C
        except ImportError:
            _C = lambda x: x
        if not self.can_use(user):
            print(_C(f"Not enough MP to use {self.name}!")); return False
        self.pay_cost(user)
        if self.damage > 0 and target:
            if target.try_dodge():
                print(_C(f"{target.name} dodged {self.name}!")); return True
            base = self.damage + user.atk + user.job.skill_power_bonus + user.get_equip_atk_bonus()
            crit, dmg = user.calc_crit(base)
            target.take_damage(dmg)
            tag = " [CRIT!]" if crit else ""
            print(_C(f"(*) {user.name} used {self.name}{tag} → {dmg} damage!"))
            if self.status_effect and random.randint(1,100) <= self.status_chance:
                target.add_status(copy.deepcopy(self.status_effect))
        elif self.heal > 0:
            amount = self.heal + user.job.heal_power_bonus
            old = user.hp; user.hp = min(user.max_hp, user.hp + amount)
            healed = user.hp - old
            print(_C(f"(+) {user.name} used {self.name} → healed {healed} HP!"))
            if self.status_effect and random.randint(1,100) <= self.status_chance:
                user.add_status(copy.deepcopy(self.status_effect))
            try:
                from game_customise import tick_legendary_quest as _tlq
                _tlq(user,"hp_healed",healed)
                if user.hp >= user.max_hp: _tlq(user,"full_heal")
            except Exception: pass
        return True

    def __repr__(self):
        base = f"DMG {self.damage}" if self.damage else f"HEAL {self.heal}" if self.heal else "?"
        fx = f" +{self.status_effect.name}({self.status_chance}%)" if self.status_effect else ""
        return f"{self.name} [{base}{fx}] MP:{self.mana_cost}"


# ═══════════════════════════════════════════════════════════════
# INVENTORY — STACKED ITEMS
# ═══════════════════════════════════════════════════════════════

INVENTORY_LIMIT = 30    # max distinct stacks in bag
STORAGE_LIMIT   = 80    # guild storage slots
MAX_STACK       = 64    # max items per stack for stackable types

STACKABLE_TYPES = {"heal", "mana", "god", "material", "bomb", "antidote", "buff"}


class ItemStack:
    """Wraps an Item with a quantity for inventory display/logic."""
    def __init__(self, item, qty=1):
        self.item = item
        self.qty  = max(1, int(qty))

    @property
    def name(self): return self.item.name
    @property
    def item_type(self): return self.item.item_type
    @property
    def sell_value(self): return self.item.sell_value
    @property
    def value(self): return self.item.value

    def is_stackable(self):
        return self.item.item_type in STACKABLE_TYPES

    def total_sell(self):
        return self.sell_value * self.qty

    def use(self, player):
        result = self.item.use(player)
        if result:
            self.qty -= 1
        return result

    def to_dict(self):
        return {"stack": True, "item": self.item.to_dict(), "qty": self.qty}

    @staticmethod
    def from_dict(d):
        item = item_from_dict(d["item"])
        return ItemStack(item, d.get("qty", 1))

    def __repr__(self):
        if self.qty > 1:
            return f"{self.item.name} x{self.qty}"
        return self.item.name


class Item:
    def __init__(self, name, item_type, value=0, sell_value=0):
        self.name=name; self.item_type=item_type
        self.value=value; self.sell_value=sell_value or max(1,value//2)

    def use(self, player):
        try:
            from game_term import C as _C
        except ImportError:
            _C = lambda x: x
        if self.item_type == "heal":
            old=player.hp; player.hp=min(player.max_hp,player.hp+self.value)
            print(_C(f"Used {self.name}: restored {player.hp-old} HP.")); return True
        if self.item_type == "mana":
            old=player.mp; player.mp=min(player.max_mp,player.mp+self.value)
            print(_C(f"Used {self.name}: restored {player.mp-old} MP.")); return True
        if self.item_type == "god":
            print(_C(f"{self.name} activates automatically at 0 HP!")); return False
        if self.item_type == "antidote":
            cured = [s for s in player.status_effects if s.name in ("Poison","Burn")]
            for s in cured: player.status_effects.remove(s)
            print(_C(f"Used {self.name}: cured {len(cured)} status effect(s).")); return True
        if self.item_type == "bomb":
            # Returns True so caller knows it was used; actual dmg applied by combat
            print(_C(f"Threw {self.name}!")); return True
        if self.item_type == "buff":
            # Short ATK/DEF buff stored on player flags
            player.temp_atk_buff  = getattr(player,"temp_atk_buff",0)  + self.value
            player.temp_atk_turns = getattr(player,"temp_atk_turns",0) + 3
            print(_C(f"Used {self.name}: ATK+{self.value} for 3 turns!")); return True
        print(_C("Can't use that here.")); return False

    def to_dict(self):
        return {"cls":"Item","name":self.name,"item_type":self.item_type,
                "value":self.value,"sell_value":self.sell_value}

    @staticmethod
    def from_dict(d):
        return Item(d["name"],d["item_type"],d["value"],d.get("sell_value",0))

    def __repr__(self): return self.name


class Equipment(Item):
    """Wearable gear with stat bonuses."""
    def __init__(self, name, slot, hp_bonus=0, atk_bonus=0, mp_bonus=0,
                 def_bonus=0, sell_value=0, stealth_bonus=0,
                 allowed_classes=None, rarity="common", description=""):
        super().__init__(name,"equipment",sell_value=sell_value)
        self.slot=slot; self.hp_bonus=hp_bonus; self.atk_bonus=atk_bonus
        self.mp_bonus=mp_bonus; self.def_bonus=def_bonus
        self.stealth_bonus=stealth_bonus
        self.allowed_classes = allowed_classes
        self.rarity = rarity
        self.description = description

    def can_equip(self, player_class):
        if self.allowed_classes is None: return True
        return player_class in self.allowed_classes

    def stat_line(self):
        p=[]
        if self.hp_bonus:      p.append(f"HP+{self.hp_bonus}")
        if self.atk_bonus:     p.append(f"ATK+{self.atk_bonus}")
        if self.mp_bonus:      p.append(f"MP+{self.mp_bonus}")
        if self.def_bonus:     p.append(f"DEF+{self.def_bonus}")
        if self.stealth_bonus: p.append(f"STL+{self.stealth_bonus}")
        return ", ".join(p) if p else "no bonuses"

    def rarity_col(self):
        def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
        return {
            "common":    fg(160,160,160),
            "uncommon":  fg(80,200,80),
            "rare":      fg(80,130,220),
            "legendary": fg(255,165,0),
        }.get(self.rarity, fg(160,160,160))

    def to_dict(self):
        return {"cls":"Equipment","name":self.name,"slot":self.slot,
                "hp_bonus":self.hp_bonus,"atk_bonus":self.atk_bonus,
                "mp_bonus":self.mp_bonus,"def_bonus":self.def_bonus,
                "stealth_bonus":self.stealth_bonus,"sell_value":self.sell_value,
                "allowed_classes":self.allowed_classes,"rarity":self.rarity,
                "description":self.description}

    @staticmethod
    def from_dict(d):
        return Equipment(d["name"],d["slot"],d.get("hp_bonus",0),
                         d.get("atk_bonus",0),d.get("mp_bonus",0),
                         d.get("def_bonus",0),d.get("sell_value",0),
                         d.get("stealth_bonus",0),
                         d.get("allowed_classes"),d.get("rarity","common"),
                         d.get("description",""))

    def __repr__(self):
        return f"{self.name} [{self.slot}] ({self.stat_line()})"


def item_from_dict(d):
    if d.get("stack"):  return ItemStack.from_dict(d)
    if d.get("cls") == "Equipment": return Equipment.from_dict(d)
    return Item.from_dict(d)


# ═══════════════════════════════════════════════════════════════
# INVENTORY HELPERS — stacking logic
# ═══════════════════════════════════════════════════════════════

def inventory_add(inventory, item):
    """
    Add item to inventory. Stacks stackable items up to MAX_STACK.
    Returns True on success, False if bag is full and item won't stack.
    item can be a plain Item/Equipment or an ItemStack.
    """
    # Unwrap qty if already a stack
    if isinstance(item, ItemStack):
        raw, qty = item.item, item.qty
    else:
        raw, qty = item, 1

    if raw.item_type in STACKABLE_TYPES:
        # Try to add to existing stack
        for stack in inventory:
            if isinstance(stack, ItemStack) and stack.item.name == raw.name and stack.qty < MAX_STACK:
                can_add = min(qty, MAX_STACK - stack.qty)
                stack.qty += can_add
                qty -= can_add
                if qty <= 0:
                    return True
        # Remaining qty goes into new stacks
        while qty > 0:
            if len(inventory) >= INVENTORY_LIMIT:
                return False
            batch = min(qty, MAX_STACK)
            inventory.append(ItemStack(raw, batch))
            qty -= batch
        return True
    else:
        # Equipment — one per slot
        if len(inventory) >= INVENTORY_LIMIT:
            return False
        inventory.append(item)
        return True


def inventory_remove(inventory, index, qty=1):
    """Remove qty from stack at index. Returns removed item or None."""
    if not (0 <= index < len(inventory)):
        return None
    entry = inventory[index]
    if isinstance(entry, ItemStack):
        take = min(qty, entry.qty)
        entry.qty -= take
        removed = ItemStack(entry.item, take)
        if entry.qty <= 0:
            inventory.pop(index)
        return removed
    else:
        return inventory.pop(index)


def sell_all_materials(inventory, player):
    """Sell all material-type stacks. Returns total gold earned."""
    total = 0
    to_remove = []
    for i, entry in enumerate(inventory):
        if isinstance(entry, ItemStack) and entry.item.item_type == "material":
            total += entry.total_sell()
            to_remove.append(i)
        elif isinstance(entry, Item) and entry.item_type == "material":
            total += entry.sell_value
            to_remove.append(i)
    for i in reversed(to_remove):
        inventory.pop(i)
    player.gold += total
    return total


def sell_all_consumables(inventory, player):
    """Sell all consumable stacks. Returns total gold earned."""
    total = 0
    to_remove = []
    consumable_types = {"heal","mana","antidote","bomb","buff"}
    for i, entry in enumerate(inventory):
        if isinstance(entry, ItemStack) and entry.item.item_type in consumable_types:
            total += entry.total_sell()
            to_remove.append(i)
        elif isinstance(entry, Item) and entry.item_type in consumable_types:
            total += entry.sell_value
            to_remove.append(i)
    for i in reversed(to_remove):
        inventory.pop(i)
    player.gold += total
    return total


# ═══════════════════════════════════════════════════════════════
# GUILD STORAGE
# ═══════════════════════════════════════════════════════════════

class GuildStorage:
    DEPOSIT_FEE = 5

    def __init__(self):
        self.items = []

    def deposit(self, item, player):
        if len(self.items) >= STORAGE_LIMIT:
            return False, "Storage is full!"
        if player.gold < self.DEPOSIT_FEE:
            return False, f"Need {self.DEPOSIT_FEE}g deposit fee."
        player.gold -= self.DEPOSIT_FEE
        self.items.append(item)
        return True, f"Deposited {item.name} (-{self.DEPOSIT_FEE}g fee)"

    def withdraw(self, idx, player):
        if not (0 <= idx < len(self.items)):
            return False, "Invalid slot."
        item = self.items.pop(idx)
        ok = inventory_add(player.inventory, item)
        if not ok:
            self.items.insert(idx, item)
            return False, "Your bag is full!"
        return True, f"Withdrew {item.name}"

    def to_dict(self):
        return {"items": [it.to_dict() if hasattr(it,'to_dict') else it.item.to_dict() for it in self.items]}

    @classmethod
    def from_dict(cls, d):
        gs = cls()
        gs.items = [item_from_dict(i) for i in d.get("items",[])]
        return gs


# ═══════════════════════════════════════════════════════════════
# EXPANDED ITEM POOL
# ═══════════════════════════════════════════════════════════════

ITEM_POOL = {
    # ── Healing Potions ──────────────────────────────────────────
    "Potion":           lambda: Item("Potion",          "heal",  40,   5),
    "Hi-Potion":        lambda: Item("Hi-Potion",       "heal",  80,  15),
    "Full Potion":      lambda: Item("Full Potion",     "heal", 200,  50),
    "Mega Potion":      lambda: Item("Mega Potion",     "heal", 400, 120),   # NEW
    "Elixir of Life":   lambda: Item("Elixir of Life",  "heal", 999, 350),   # NEW full heal
    "Regen Tonic":      lambda: Item("Regen Tonic",     "heal",  60,  20),   # NEW (heal + regen effect via combat)

    # ── Mana Potions ─────────────────────────────────────────────
    "Ether":            lambda: Item("Ether",            "mana",  25,   8),
    "Hi-Ether":         lambda: Item("Hi-Ether",         "mana",  50,  20),
    "Elixir":           lambda: Item("Elixir",           "mana", 120,  60),
    "Mega Ether":       lambda: Item("Mega Ether",       "mana", 250, 130),  # NEW
    "Mana Crystal":     lambda: Item("Mana Crystal",     "mana", 500, 300),  # NEW

    # ── Combo Potions ────────────────────────────────────────────
    "Tincture":         lambda: Item("Tincture",         "heal",  50,  25),  # NEW heal+mana combo (handled in use())
    "Hero's Brew":      lambda: Item("Hero's Brew",      "heal", 150,  80),  # NEW big combo

    # ── Special ──────────────────────────────────────────────────
    "God Potion":       lambda: Item("God Potion",       "god",    5, 500),
    "Antidote":         lambda: Item("Antidote",         "antidote", 0, 10),  # NEW cure poison/burn
    "Holy Water":       lambda: Item("Holy Water",       "antidote", 0, 25),  # NEW clears all status
    "Fire Bomb":        lambda: Item("Fire Bomb",        "bomb",   35, 18),   # NEW throwable
    "Smoke Bomb":       lambda: Item("Smoke Bomb",       "bomb",    0, 20),   # NEW escape/stealth
    "Strength Draught": lambda: Item("Strength Draught", "buff",   10, 40),   # NEW temp ATK+10

    # ── Materials ────────────────────────────────────────────────
    "Wolf Pelt":        lambda: Item("Wolf Pelt",        "material", 0, 20),
    "Bone Shard":       lambda: Item("Bone Shard",       "material", 0, 15),
    "Iron Ore":         lambda: Item("Iron Ore",         "material", 0, 25),
    "Feather":          lambda: Item("Feather",          "material", 0, 12),
    "Frost Crystal":    lambda: Item("Frost Crystal",    "material", 0, 35),
    "Scale Fragment":   lambda: Item("Scale Fragment",   "material", 0, 40),
    "Dark Shard":       lambda: Item("Dark Shard",       "material", 0, 60),
    "Dragon Scale":     lambda: Item("Dragon Scale",     "material", 0,200),
    "Mana Stone":       lambda: Item("Mana Stone",       "material", 0, 45),
    "Shadow Cloth":     lambda: Item("Shadow Cloth",     "material", 0, 55),
    "Holy Relic":       lambda: Item("Holy Relic",       "material", 0, 80),
    "Venom Fang":       lambda: Item("Venom Fang",       "material", 0, 30),  # NEW — from scorpions
    "Runic Stone":      lambda: Item("Runic Stone",      "material", 0, 70),  # NEW — from cultists
    "Phoenix Feather":  lambda: Item("Phoenix Feather",  "material", 0,150),  # NEW — rare drop
    "Obsidian Shard":   lambda: Item("Obsidian Shard",   "material", 0, 90),  # NEW — from golems

    # ── Weapons — Warrior ────────────────────────────────────────
    "Iron Sword":       lambda: Equipment("Iron Sword",      "weapon", atk_bonus=5,  sell_value=40,  rarity="common"),
    "Steel Sword":      lambda: Equipment("Steel Sword",     "weapon", atk_bonus=9,  sell_value=75,  rarity="uncommon",  allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),
    "Broad Sword":      lambda: Equipment("Broad Sword",     "weapon", atk_bonus=13, sell_value=120, rarity="uncommon",  allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),
    "Dragon Sword":     lambda: Equipment("Dragon Sword",    "weapon", atk_bonus=22, sell_value=280, rarity="rare",      allowed_classes=["Swordsman","Blade Master"]),
    "Runic Greatsword": lambda: Equipment("Runic Greatsword","weapon", atk_bonus=18, def_bonus=5, sell_value=220, rarity="rare", allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),  # NEW

    # ── Weapons — Mage ───────────────────────────────────────────
    "Iron Staff":       lambda: Equipment("Iron Staff",      "weapon", atk_bonus=3,  mp_bonus=15,  sell_value=45,  rarity="common",   allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
    "Crystal Staff":    lambda: Equipment("Crystal Staff",   "weapon", atk_bonus=5,  mp_bonus=30,  sell_value=90,  rarity="uncommon", allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
    "Arcane Rod":       lambda: Equipment("Arcane Rod",      "weapon", atk_bonus=8,  mp_bonus=50,  sell_value=160, rarity="rare",     allowed_classes=["Mage","Archmage"]),
    "Void Staff":       lambda: Equipment("Void Staff",      "weapon", atk_bonus=12, mp_bonus=70,  sell_value=240, rarity="legendary",allowed_classes=["Mage","Archmage"]),  # NEW

    # ── Weapons — Rogue ──────────────────────────────────────────
    "Short Sword":      lambda: Equipment("Short Sword",     "weapon", atk_bonus=6,  stealth_bonus=2, sell_value=50,  rarity="common",   allowed_classes=["Rogue","Shadow Assassin"]),
    "Shadow Blade":     lambda: Equipment("Shadow Blade",    "weapon", atk_bonus=11, stealth_bonus=5, sell_value=100, rarity="uncommon", allowed_classes=["Rogue","Shadow Assassin"]),
    "Assassin Dagger":  lambda: Equipment("Assassin Dagger", "weapon", atk_bonus=16, stealth_bonus=8, sell_value=180, rarity="rare",     allowed_classes=["Rogue","Shadow Assassin"]),
    "Twin Fang Blades": lambda: Equipment("Twin Fang Blades","weapon", atk_bonus=20, stealth_bonus=10,sell_value=260, rarity="legendary",allowed_classes=["Rogue","Shadow Assassin"]),  # NEW

    # ── Weapons — Tank ───────────────────────────────────────────
    "War Hammer":       lambda: Equipment("War Hammer",      "weapon", atk_bonus=10, def_bonus=3,  sell_value=80,  rarity="common",   allowed_classes=["Tank","War Titan"]),
    "Tower Shield":     lambda: Equipment("Tower Shield",    "shield", def_bonus=18, hp_bonus=30,  sell_value=110, rarity="uncommon", allowed_classes=["Tank","War Titan"]),
    "Titan Axe":        lambda: Equipment("Titan Axe",       "weapon", atk_bonus=15, hp_bonus=20,  sell_value=160, rarity="rare",     allowed_classes=["Tank","War Titan"]),  # NEW

    # ── Weapons — Healer ─────────────────────────────────────────
    "Holy Mace":        lambda: Equipment("Holy Mace",       "weapon", atk_bonus=6,  mp_bonus=10,  sell_value=70,  rarity="common",   allowed_classes=["Healer","Arch Priest"]),
    "Angel's Sceptre":  lambda: Equipment("Angel's Sceptre","weapon", atk_bonus=4,  mp_bonus=40, hp_bonus=20, sell_value=150, rarity="rare",   allowed_classes=["Healer","Arch Priest"]),
    "Sacred Tome":      lambda: Equipment("Sacred Tome",     "weapon", atk_bonus=2,  mp_bonus=55, hp_bonus=30, sell_value=200, rarity="legendary", allowed_classes=["Healer","Arch Priest"]),  # NEW

    # ── Armor ─────────────────────────────────────────────────────
    "Leather Armor":        lambda: Equipment("Leather Armor",       "armor", hp_bonus=20, def_bonus=4,  sell_value=20,  rarity="common"),
    "Chain Mail":           lambda: Equipment("Chain Mail",          "armor", hp_bonus=35, def_bonus=8,  sell_value=60,  rarity="uncommon", allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),
    "Plate Armor":          lambda: Equipment("Plate Armor",         "armor", hp_bonus=60, def_bonus=15, sell_value=130, rarity="rare",     allowed_classes=["Tank","War Titan"]),
    "Dragon Scale Armor":   lambda: Equipment("Dragon Scale Armor",  "armor", hp_bonus=80, def_bonus=22, sell_value=300, rarity="legendary"),
    "Obsidian Plate":       lambda: Equipment("Obsidian Plate",      "armor", hp_bonus=70, def_bonus=18, sell_value=200, rarity="rare",     allowed_classes=["Tank","Swordsman","War Titan","Blade Master"]),  # NEW
    "Mage Robe":            lambda: Equipment("Mage Robe",           "armor", hp_bonus=10, mp_bonus=40,  sell_value=55,  rarity="common",   allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
    "Archmage Vestment":    lambda: Equipment("Archmage Vestment",   "armor", hp_bonus=20, mp_bonus=70,  sell_value=130, rarity="rare",     allowed_classes=["Mage","Archmage"]),
    "Celestial Robe":       lambda: Equipment("Celestial Robe",      "armor", hp_bonus=30, mp_bonus=90,  sell_value=220, rarity="legendary",allowed_classes=["Mage","Archmage"]),  # NEW
    "Shadow Suit":          lambda: Equipment("Shadow Suit",         "armor", hp_bonus=25, stealth_bonus=6, sell_value=80,  rarity="uncommon", allowed_classes=["Rogue","Shadow Assassin"]),
    "Void Wraps":           lambda: Equipment("Void Wraps",          "armor", hp_bonus=35, stealth_bonus=10,sell_value=160, rarity="rare",     allowed_classes=["Rogue","Shadow Assassin"]),  # NEW
    "Priest Vestment":      lambda: Equipment("Priest Vestment",     "armor", hp_bonus=30, mp_bonus=25,  sell_value=75,  rarity="uncommon", allowed_classes=["Healer","Arch Priest"]),

    # ── Helmets ───────────────────────────────────────────────────
    "Iron Helm":        lambda: Equipment("Iron Helm",       "helmet", hp_bonus=10, def_bonus=3,  sell_value=25,  rarity="common"),
    "Steel Helm":       lambda: Equipment("Steel Helm",      "helmet", hp_bonus=20, def_bonus=6,  sell_value=55,  rarity="uncommon", allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),
    "Mage Hood":        lambda: Equipment("Mage Hood",       "helmet", hp_bonus=5,  mp_bonus=20,  sell_value=40,  rarity="common",   allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
    "Rogue Hood":       lambda: Equipment("Rogue Hood",      "helmet", stealth_bonus=4, hp_bonus=8, sell_value=45, rarity="common",  allowed_classes=["Rogue","Shadow Assassin"]),
    "Dragon Skull Helm":lambda: Equipment("Dragon Skull Helm","helmet",hp_bonus=40, def_bonus=10, sell_value=180, rarity="rare"),  # NEW

    # ── Cloaks ────────────────────────────────────────────────────
    "Travel Cloak":     lambda: Equipment("Travel Cloak",    "cloak",  hp_bonus=8,  stealth_bonus=1,  sell_value=15,  rarity="common"),
    "Shadow Cloak":     lambda: Equipment("Shadow Cloak",    "cloak",  hp_bonus=15, mp_bonus=15, stealth_bonus=6, sell_value=80, rarity="uncommon"),
    "Frost Cloak":      lambda: Equipment("Frost Cloak",     "cloak",  hp_bonus=30, mp_bonus=10, stealth_bonus=2, sell_value=60, rarity="uncommon"),
    "Mage Shroud":      lambda: Equipment("Mage Shroud",     "cloak",  mp_bonus=30, sell_value=70,  rarity="uncommon", allowed_classes=["Mage","Archmage"]),
    "Phantom Shroud":   lambda: Equipment("Phantom Shroud",  "cloak",  hp_bonus=20, mp_bonus=20, stealth_bonus=12, sell_value=200, rarity="legendary"),  # NEW

    # ── Shields ───────────────────────────────────────────────────
    "Wooden Shield":    lambda: Equipment("Wooden Shield",   "shield", def_bonus=5,  hp_bonus=5,   sell_value=20,  rarity="common"),
    "Iron Shield":      lambda: Equipment("Iron Shield",     "shield", def_bonus=10, hp_bonus=10,  sell_value=50,  rarity="common"),
    "Steel Shield":     lambda: Equipment("Steel Shield",    "shield", def_bonus=14, hp_bonus=20,  sell_value=90,  rarity="uncommon"),
    "Holy Shield":      lambda: Equipment("Holy Shield",     "shield", def_bonus=12, hp_bonus=25, mp_bonus=10, sell_value=110, rarity="rare",   allowed_classes=["Tank","Healer","War Titan","Arch Priest"]),
    "Mirror Shield":    lambda: Equipment("Mirror Shield",   "shield", def_bonus=16, hp_bonus=15, sell_value=140, rarity="rare"),  # NEW

    # ── Rings & Amulets ───────────────────────────────────────────
    "Iron Ring":        lambda: Equipment("Iron Ring",       "ring",   atk_bonus=2, sell_value=20,  rarity="common"),
    "Mana Ring":        lambda: Equipment("Mana Ring",       "ring",   mp_bonus=20, sell_value=35,  rarity="common"),
    "Power Ring":       lambda: Equipment("Power Ring",      "ring",   atk_bonus=5, hp_bonus=10, sell_value=60,  rarity="uncommon"),
    "Dragon Ring":      lambda: Equipment("Dragon Ring",     "ring",   atk_bonus=8, hp_bonus=20, mp_bonus=15, sell_value=150, rarity="rare"),
    "Titan Ring":       lambda: Equipment("Titan Ring",      "ring",   hp_bonus=40, def_bonus=8, sell_value=180, rarity="rare"),   # NEW
    "Amulet of Life":   lambda: Equipment("Amulet of Life",  "amulet", hp_bonus=30, sell_value=50,  rarity="uncommon"),
    "Mana Amulet":      lambda: Equipment("Mana Amulet",     "amulet", mp_bonus=30, sell_value=50,  rarity="uncommon"),
    "Hero Amulet":      lambda: Equipment("Hero Amulet",     "amulet", atk_bonus=5, hp_bonus=20, mp_bonus=20, sell_value=130, rarity="rare"),
    "Phoenix Pendant":  lambda: Equipment("Phoenix Pendant", "amulet", hp_bonus=50, mp_bonus=25, sell_value=220, rarity="legendary"),  # NEW

    # ── Crafted ───────────────────────────────────────────────────
    "Wolf Fang Blade":  lambda: Equipment("Wolf Fang Blade", "weapon", atk_bonus=8,  sell_value=60,  rarity="uncommon"),
    "Hunter Vest":      lambda: Equipment("Hunter Vest",     "armor",  hp_bonus=25, def_bonus=5, sell_value=50, rarity="uncommon"),
    "Frost Blade":      lambda: Equipment("Frost Blade",     "weapon", atk_bonus=12, sell_value=90,  rarity="rare"),
    "Bone Staff":       lambda: Equipment("Bone Staff",      "weapon", atk_bonus=4, mp_bonus=25, sell_value=70, rarity="uncommon", allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
    "Venom Dagger":     lambda: Equipment("Venom Dagger",    "weapon", atk_bonus=9, stealth_bonus=4, sell_value=80, rarity="uncommon", allowed_classes=["Rogue","Shadow Assassin"]),  # NEW
    "Runic Shield":     lambda: Equipment("Runic Shield",    "shield", def_bonus=15, hp_bonus=20, mp_bonus=15, sell_value=130, rarity="rare"),  # NEW
    "Obsidian Armor":   lambda: Equipment("Obsidian Armor",  "armor",  hp_bonus=65, def_bonus=16, sell_value=180, rarity="rare"),  # NEW
}


# ═══════════════════════════════════════════════════════════════
# LOOT TABLES
# ═══════════════════════════════════════════════════════════════

LOOT_TABLE = {
    "Goblin":        [("Potion",0.50),("Wolf Pelt",0.20),("Iron Ring",0.05)],
    "Slime":         [("Potion",0.30)],
    "Wolf":          [("Wolf Pelt",0.65),("Potion",0.25)],
    "Bandit":        [("Potion",0.40),("Iron Sword",0.10),("Iron Ring",0.06)],
    "Skeleton":      [("Bone Shard",0.55),("Ether",0.20),("Iron Shield",0.05)],
    "Stone Golem":   [("Iron Ore",0.65),("Obsidian Shard",0.25),("Steel Helm",0.04)],
    "Harpy":         [("Feather",0.55),("Ether",0.20),("Travel Cloak",0.06)],
    "Sand Wyrm":     [("Scale Fragment",0.45),("Ether",0.30),("Shadow Blade",0.04),("Venom Fang",0.35)],
    "Scorpion":      [("Venom Fang",0.60),("Scale Fragment",0.30),("Antidote",0.20)],
    "Ice Wolf":      [("Frost Crystal",0.50),("Potion",0.25),("Frost Cloak",0.04)],
    "Shadow Beast":  [("Dark Shard",0.55),("God Potion",0.03),("Shadow Cloth",0.30)],
    "Cultist":       [("Ether",0.45),("Dark Shard",0.25),("Runic Stone",0.30),("Mana Stone",0.20)],
    "Desert Raider": [("Potion",0.40),("Strength Draught",0.15),("Fire Bomb",0.10)],
    "Dragon":        [("Dragon Scale",0.90),("God Potion",0.12),("Dragon Ring",0.06),("Phoenix Feather",0.08)],
    "Frost Wraith":  [("Frost Crystal",0.60),("Hi-Ether",0.20),("Mage Shroud",0.05)],
    "Armored Knight":[("Iron Ore",0.50),("Obsidian Shard",0.20),("Iron Shield",0.10)],
    "Frost Dragon":  [("Frost Crystal",0.90),("Dragon Scale",0.50),("Phoenix Feather",0.10)],
    "Goblin King":   [("Bone Shard",1.0),("Iron Ore",0.80),("Power Ring",0.15)],
    "Shadow Lord":   [("Dark Shard",1.0),("Dragon Scale",0.40),("Phoenix Pendant",0.05)],
}

def roll_drops(enemy_name):
    table = LOOT_TABLE.get(enemy_name,[("Potion",0.20)])
    return [ITEM_POOL[n]() for n,c in table if random.random()<c and n in ITEM_POOL]


# ═══════════════════════════════════════════════════════════════
# CRAFTING RECIPES  (expanded)
# ═══════════════════════════════════════════════════════════════

CRAFTING_RECIPES = [
    # ── Consumables ───────────────────────────────────────────────
    {"name":"Antidote",          "needs":{"Feather":1,"Venom Fang":1},
     "result":lambda:Item("Antidote","antidote",0,10),
     "classes":None,"desc":"Cures poison and burn","qty":3},
    {"name":"Fire Bomb",         "needs":{"Mana Stone":1,"Iron Ore":1},
     "result":lambda:Item("Fire Bomb","bomb",35,18),
     "classes":None,"desc":"Throwable fire explosive","qty":3},
    {"name":"Mega Potion",       "needs":{"Wolf Pelt":1,"Frost Crystal":1},
     "result":lambda:Item("Mega Potion","heal",400,120),
     "classes":None,"desc":"Restores 400 HP","qty":2},
    {"name":"Mana Crystal",      "needs":{"Mana Stone":3,"Runic Stone":1},
     "result":lambda:Item("Mana Crystal","mana",500,300),
     "classes":None,"desc":"Fully restores MP","qty":1},
    {"name":"Hero's Brew",       "needs":{"Holy Relic":1,"Frost Crystal":1,"Wolf Pelt":1},
     "result":lambda:Item("Hero's Brew","heal",150,80),
     "classes":None,"desc":"Heals 150 HP and 50 MP","qty":2},
    {"name":"Strength Draught",  "needs":{"Venom Fang":2,"Mana Stone":1},
     "result":lambda:Item("Strength Draught","buff",10,40),
     "classes":None,"desc":"ATK+10 for 3 turns","qty":2},

    # ── Weapons ──────────────────────────────────────────────────
    {"name":"Wolf Fang Blade",   "needs":{"Wolf Pelt":2,"Iron Ore":1},
     "result":lambda:Equipment("Wolf Fang Blade","weapon",atk_bonus=8,sell_value=60,rarity="uncommon"),
     "classes":None,"desc":"Savage blade from wolf remains"},
    {"name":"Frost Blade",       "needs":{"Frost Crystal":2,"Iron Ore":2},
     "result":lambda:Equipment("Frost Blade","weapon",atk_bonus=12,sell_value=90,rarity="rare"),
     "classes":["Swordsman","Tank","Blade Master","War Titan"],"desc":"Chills enemies on contact"},
    {"name":"Bone Staff",        "needs":{"Bone Shard":3,"Iron Ore":1},
     "result":lambda:Equipment("Bone Staff","weapon",atk_bonus=4,mp_bonus=25,sell_value=70,rarity="uncommon",allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),
     "classes":["Mage","Healer","Archmage","Arch Priest"],"desc":"Bone-carved focus for mages"},
    {"name":"Shadow Blade",      "needs":{"Dark Shard":2,"Iron Ore":1},
     "result":lambda:Equipment("Shadow Blade","weapon",atk_bonus=11,stealth_bonus=5,sell_value=100,rarity="uncommon",allowed_classes=["Rogue","Shadow Assassin"]),
     "classes":["Rogue","Shadow Assassin"],"desc":"Strikes from the dark"},
    {"name":"Venom Dagger",      "needs":{"Venom Fang":3,"Shadow Cloth":1},
     "result":lambda:Equipment("Venom Dagger","weapon",atk_bonus=9,stealth_bonus=4,sell_value=80,rarity="uncommon",allowed_classes=["Rogue","Shadow Assassin"]),
     "classes":["Rogue","Shadow Assassin"],"desc":"Poisons on every hit"},
    {"name":"Runic Greatsword",  "needs":{"Runic Stone":2,"Iron Ore":4},
     "result":lambda:Equipment("Runic Greatsword","weapon",atk_bonus=18,def_bonus=5,sell_value=220,rarity="rare",allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),
     "classes":["Swordsman","Tank","Blade Master","War Titan"],"desc":"Ancient runes amplify power"},
    {"name":"Void Staff",        "needs":{"Dark Shard":4,"Mana Stone":3,"Feather":2},
     "result":lambda:Equipment("Void Staff","weapon",atk_bonus=12,mp_bonus=70,sell_value=240,rarity="legendary",allowed_classes=["Mage","Archmage"]),
     "classes":["Mage","Archmage"],"desc":"Channels the void itself"},

    # ── Armor ─────────────────────────────────────────────────────
    {"name":"Hunter Vest",       "needs":{"Wolf Pelt":3},
     "result":lambda:Equipment("Hunter Vest","armor",hp_bonus=25,def_bonus=5,sell_value=50,rarity="uncommon"),
     "classes":None,"desc":"Hardened wolf leather"},
    {"name":"Shadow Cloak",      "needs":{"Dark Shard":2,"Feather":1},
     "result":lambda:Equipment("Shadow Cloak","cloak",hp_bonus=15,mp_bonus=15,stealth_bonus=6,sell_value=80,rarity="uncommon"),
     "classes":None,"desc":"Fades into shadows"},
    {"name":"Dragon Scale Armor","needs":{"Dragon Scale":2,"Iron Ore":3},
     "result":lambda:Equipment("Dragon Scale Armor","armor",hp_bonus=80,def_bonus=22,sell_value=300,rarity="legendary"),
     "classes":None,"desc":"Near-impervious to damage"},
    {"name":"Mage Shroud",       "needs":{"Shadow Cloth":2,"Feather":2},
     "result":lambda:Equipment("Mage Shroud","cloak",mp_bonus=30,sell_value=70,rarity="uncommon",allowed_classes=["Mage","Archmage"]),
     "classes":["Mage","Archmage"],"desc":"Woven with arcane thread"},
    {"name":"Holy Shield",       "needs":{"Holy Relic":1,"Iron Ore":2},
     "result":lambda:Equipment("Holy Shield","shield",def_bonus=12,hp_bonus=25,mp_bonus=10,sell_value=110,rarity="rare",allowed_classes=["Tank","Healer","War Titan","Arch Priest"]),
     "classes":["Tank","Healer","War Titan","Arch Priest"],"desc":"Blessed by divine power"},
    {"name":"Obsidian Armor",    "needs":{"Obsidian Shard":3,"Iron Ore":4},
     "result":lambda:Equipment("Obsidian Armor","armor",hp_bonus=65,def_bonus=16,sell_value=180,rarity="rare"),
     "classes":None,"desc":"Forged from volcanic rock"},
    {"name":"Runic Shield",      "needs":{"Runic Stone":2,"Iron Ore":3},
     "result":lambda:Equipment("Runic Shield","shield",def_bonus=15,hp_bonus=20,mp_bonus=15,sell_value=130,rarity="rare"),
     "classes":None,"desc":"Runic inscriptions absorb damage"},
    {"name":"Phoenix Pendant",   "needs":{"Phoenix Feather":1,"Mana Stone":2},
     "result":lambda:Equipment("Phoenix Pendant","amulet",hp_bonus=50,mp_bonus=25,sell_value=220,rarity="legendary"),
     "classes":None,"desc":"Reborn from the flame"},

    # ── Rings & Accessories ───────────────────────────────────────
    {"name":"Power Ring",        "needs":{"Iron Ore":2,"Mana Stone":1},
     "result":lambda:Equipment("Power Ring","ring",atk_bonus=5,hp_bonus=10,sell_value=60,rarity="uncommon"),
     "classes":None,"desc":"Amplifies physical strength"},
    {"name":"Mana Amulet",       "needs":{"Mana Stone":2,"Feather":1},
     "result":lambda:Equipment("Mana Amulet","amulet",mp_bonus=30,sell_value=50,rarity="uncommon"),
     "classes":None,"desc":"Expands arcane reservoir"},
    {"name":"Titan Ring",        "needs":{"Obsidian Shard":2,"Iron Ore":3},
     "result":lambda:Equipment("Titan Ring","ring",hp_bonus=40,def_bonus=8,sell_value=180,rarity="rare"),
     "classes":None,"desc":"Forged for titans"},
]


# ═══════════════════════════════════════════════════════════════
# SHOP STOCK PRESETS
# ═══════════════════════════════════════════════════════════════

def town_shop_stock(region_name=""):
    base = [
        # ── Potions — full tiered lineup ─────────────────────────
        (Item("Potion",         "heal",  40,   5),   8),
        (Item("Hi-Potion",      "heal",  80,  15),  20),
        (Item("Full Potion",    "heal", 200,  50),  50),
        (Item("Mega Potion",    "heal", 400, 120), 120),
        (Item("Ether",          "mana",  25,   8),  10),
        (Item("Hi-Ether",       "mana",  50,  20),  35),
        (Item("Elixir",         "mana", 120,  60),  80),
        (Item("Antidote",       "antidote", 0, 10),  12),
        (Item("Fire Bomb",      "bomb",  35,  18),  18),
        (Item("Smoke Bomb",     "bomb",   0,  20),  20),
        (Item("Strength Draught","buff", 10,  40),  40),
        # ── Universal weapons ─────────────────────────────────────
        (Equipment("Iron Sword","weapon",atk_bonus=5,sell_value=40,rarity="common"),                                              60),
        (Equipment("Iron Staff","weapon",atk_bonus=3,mp_bonus=15,sell_value=45,rarity="common",allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),  55),
        (Equipment("Short Sword","weapon",atk_bonus=6,stealth_bonus=2,sell_value=50,rarity="common",allowed_classes=["Rogue","Shadow Assassin"]),            50),
        (Equipment("War Hammer","weapon",atk_bonus=10,def_bonus=3,sell_value=80,rarity="common",allowed_classes=["Tank","War Titan"]),                       75),
        (Equipment("Holy Mace","weapon",atk_bonus=6,mp_bonus=10,sell_value=70,rarity="common",allowed_classes=["Healer","Arch Priest"]),                     65),
        # ── Universal armor ───────────────────────────────────────
        (Equipment("Leather Armor","armor",hp_bonus=20,def_bonus=4,sell_value=20,rarity="common"),                               50),
        (Equipment("Mage Robe","armor",hp_bonus=10,mp_bonus=40,sell_value=55,rarity="common",allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),    60),
        # ── Accessories ───────────────────────────────────────────
        (Equipment("Iron Ring","ring",atk_bonus=2,sell_value=20,rarity="common"),                                                 25),
        (Equipment("Wooden Shield","shield",def_bonus=5,hp_bonus=5,sell_value=20,rarity="common"),                                30),
        (Equipment("Travel Cloak","cloak",hp_bonus=8,stealth_bonus=1,sell_value=15,rarity="common"),                              20),
        (Equipment("Iron Helm","helmet",hp_bonus=10,def_bonus=3,sell_value=25,rarity="common"),                                   30),
    ]
    extras = {
        "IRONSPIRE": [
            (Equipment("Steel Sword","weapon",atk_bonus=9,sell_value=75,rarity="uncommon",allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),120),
            (Equipment("Chain Mail","armor",hp_bonus=35,def_bonus=8,sell_value=60,rarity="uncommon",allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),95),
            (Equipment("Steel Shield","shield",def_bonus=14,hp_bonus=20,sell_value=90,rarity="uncommon"),110),
            (Equipment("Titan Axe","weapon",atk_bonus=15,hp_bonus=20,sell_value=160,rarity="rare",allowed_classes=["Tank","War Titan"]),190),
        ],
        "FROSTHEIM": [
            (Equipment("Frost Cloak","cloak",hp_bonus=30,mp_bonus=10,stealth_bonus=2,sell_value=60,rarity="uncommon"),130),
            (Equipment("Crystal Staff","weapon",atk_bonus=5,mp_bonus=30,sell_value=90,rarity="uncommon",allowed_classes=["Mage","Healer","Archmage","Arch Priest"]),140),
            (Item("Mega Ether","mana",250,130),150),
            (Item("Mana Crystal","mana",500,300),350),
        ],
        "AELORIA": [
            (Equipment("Steel Helm","helmet",hp_bonus=20,def_bonus=6,sell_value=55,rarity="uncommon",allowed_classes=["Swordsman","Tank","Blade Master","War Titan"]),80),
            (Equipment("Shadow Suit","armor",hp_bonus=25,stealth_bonus=6,sell_value=80,rarity="uncommon",allowed_classes=["Rogue","Shadow Assassin"]),90),
            (Equipment("Mana Ring","ring",mp_bonus=20,sell_value=35,rarity="common"),45),
            (Item("Regen Tonic","heal",60,20),25),
        ],
        "ASH SANDS": [
            (Equipment("Assassin Dagger","weapon",atk_bonus=16,stealth_bonus=8,sell_value=180,rarity="rare",allowed_classes=["Rogue","Shadow Assassin"]),200),
            (Equipment("Priest Vestment","armor",hp_bonus=30,mp_bonus=25,sell_value=75,rarity="uncommon",allowed_classes=["Healer","Arch Priest"]),95),
            (Item("Antidote","antidote",0,10),12),
        ],
        "SOUTH ISLES": [
            (Equipment("Iron Shield","shield",def_bonus=10,hp_bonus=10,sell_value=50,rarity="common"),65),
            (Equipment("Amulet of Life","amulet",hp_bonus=30,sell_value=50,rarity="uncommon"),70),
            (Item("Elixir of Life","heal",999,350),400),
            (Item("Hero's Brew","heal",150,80),100),
        ],
    }
    return base + extras.get(region_name.upper(),[])
