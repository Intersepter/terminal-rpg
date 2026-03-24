"""
encyclopedia.py — In-game encyclopedia / codex.
Tabs: Enemies (what they drop), Shops (what each town sells),
      Crafting (all recipes + materials needed), Trading (barter offers).
"""

import os
from game_term import C, P, div, clr, W, H, hpbar, mpbar, box_top, box_mid, box_bot, get_size
from game_lang import T, set_language, LANG, LANGUAGE_NAMES

_R="\033[0m"; _B="\033[1m"
def _fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
_GOLD =_fg(255,215,0);  _WHITE=_fg(255,255,255); _DIM  =_fg(100,100,100)
_GREEN=_fg(80,200,80);  _RED  =_fg(220,60,60);   _CYAN =_fg(80,220,220)
_YELL =_fg(240,200,60); _PURP =_fg(180,80,220);  _ORAN =_fg(220,140,40)
_TEAL =_fg(60,200,180)

def _clear(): os.system("cls" if os.name == "nt" else "clear")
def _div(w=60): return f"  {_DIM}{'─'*w}{_R}"
def _opt(k,l,h=""): return f"    {_GOLD}{_B}[{k}]{_R} {_WHITE}{l}{_R}" + (f"  {_DIM}{h}{_R}" if h else "")
def _pause(): input(f"\n  {_DIM}(Press Enter){_R}")

# ── Enemy drop data (mirrors items.py LOOT_TABLE) ────────────────
ENEMY_CODEX = {
    # name: {zone, desc, drops: [(item, chance_pct)], special}
    "Slime":         {"zone":"Plains","desc":"Weak gelatinous creature.",
                      "drops":[("Potion","30%")],"special":"None"},
    "Goblin":        {"zone":"Plains/Forest","desc":"Small, sneaky scavenger.",
                      "drops":[("Potion","50%"),("Wolf Pelt","20%")],"special":"None"},
    "Wolf":          {"zone":"Forest","desc":"Pack hunter, high dodge.",
                      "drops":[("Wolf Pelt","65%"),("Potion","25%")],"special":"High dodge (10%)"},
    "Bandit":        {"zone":"Plains","desc":"Armoured thug, high crit.",
                      "drops":[("Potion","40%"),("Iron Sword","12%")],"special":"High crit (12%)"},
    "Skeleton":      {"zone":"Dungeon","desc":"Undead warrior.",
                      "drops":[("Bone Shard","55%"),("Ether","20%")],"special":"None"},
    "Harpy":         {"zone":"Mountain","desc":"Flying creature, high dodge.",
                      "drops":[("Feather","55%"),("Ether","20%")],"special":"High dodge (14%)"},
    "Stone Golem":   {"zone":"Mountain","desc":"Massive stone construct, very tanky.",
                      "drops":[("Iron Ore","65%"),("Potion","25%")],"special":"High DEF"},
    "Sand Wyrm":     {"zone":"Desert","desc":"Burrowing desert predator.",
                      "drops":[("Scale Fragment","45%"),("Ether","30%")],"special":"None"},
    "Scorpion":      {"zone":"Desert","desc":"Venomous giant scorpion.",
                      "drops":[("Scale Fragment","30%")],"special":"Poison chance"},
    "Desert Raider": {"zone":"Desert","desc":"Nomadic desert warrior.",
                      "drops":[("Potion","35%")],"special":"High crit"},
    "Ice Wolf":      {"zone":"Snow","desc":"Frost-touched wolf pack.",
                      "drops":[("Frost Crystal","50%"),("Potion","25%")],"special":"Dodge (8%)"},
    "Frost Wraith":  {"zone":"Snow","desc":"Ethereal ice spirit, very evasive.",
                      "drops":[("Frost Crystal","60%"),("Hi-Ether","20%")],"special":"Dodge (15%)"},
    "Snow Beast":    {"zone":"Snow","desc":"Massive arctic predator.",
                      "drops":[("Frost Crystal","30%")],"special":"High HP"},
    "Shadow Beast":  {"zone":"Dungeon","desc":"Demon of darkness.",
                      "drops":[("Dark Shard","55%"),("God Potion","3%")],"special":"High crit+dodge"},
    "Cultist":       {"zone":"Dungeon","desc":"Servant of dark forces.",
                      "drops":[("Ether","45%"),("Dark Shard","25%")],"special":"None"},
    "Armored Knight":{"zone":"Dungeon","desc":"Undead knight in heavy armour.",
                      "drops":[("Iron Ore","40%")],"special":"Very high DEF"},
    "Goblin King":   {"zone":"Boss","desc":"Boss — leads goblin armies.",
                      "drops":[("Bone Shard","100%"),("Iron Ore","80%")],"special":"Phase 2 rage"},
    "Frost Dragon":  {"zone":"Boss","desc":"Boss — winged ice dragon.",
                      "drops":[("Frost Crystal","100%"),("Dragon Scale","50%")],"special":"Venom+drain"},
    "Shadow Lord":   {"zone":"Boss","desc":"Boss — ruler of darkness.",
                      "drops":[("Dark Shard","100%"),("Dragon Scale","40%")],"special":"Drain+venom"},
    "Dragon/Vaeltharion":{"zone":"Final Boss","desc":"The ancient dragon terrorising the world.",
                      "drops":[("Dragon Scale","90%"),("God Potion","12%")],"special":"Phase 2, all skills"},
}

# ── Shop codex (what towns sell and where) ────────────────────────
SHOP_CODEX = {
    "All towns": {
        "sells": [
            ("Potion",        "heal +40 HP",   "8g"),
            ("Hi-Potion",     "heal +80 HP",   "20g"),
            ("Ether",         "restore +25 MP","10g"),
            ("Leather Armor", "HP+20 DEF+4",   "50g"),
            ("Iron Sword",    "ATK+5",         "60g"),
        ],
    },
    "AELORIA (Greenveil etc.)": {
        "sells": [("Hunter Bow","ATK+7","110g")],
    },
    "IRONSPIRE (Ironmoor etc.)": {
        "sells": [("Steel Shield","HP+10 DEF+12","140g"),("Hi-Ether","MP+50","60g")],
    },
    "FROSTHEIM (Frostheim etc.)": {
        "sells": [("Frost Cloak","HP+30 MP+10 STL+2","130g")],
    },
    "ASH SANDS (Sandreach etc.)": {
        "sells": [("Desert Blade","ATK+9","120g")],
    },
    "SOUTH ISLES (Seaview etc.)": {
        "sells": [("Hi-Ether","MP+50","60g"),("Sea Shield","HP+25 DEF+6","120g")],
    },
}

# ── Crafting codex (basic + advanced) ────────────────────────────
CRAFTING_CODEX = [
    # Basic (town bench)
    {"name":"Wolf Fang Blade",  "bench":"Town",    "needs":"Wolf Pelt×2  Iron Ore×1",  "result":"Weapon ATK+8"},
    {"name":"Hunter Vest",      "bench":"Town",    "needs":"Wolf Pelt×3",              "result":"Armor HP+25 DEF+5"},
    {"name":"Frost Blade",      "bench":"Town",    "needs":"Frost Crystal×2  Iron Ore×2","result":"Weapon ATK+12"},
    {"name":"Shadow Cloak",     "bench":"Town",    "needs":"Dark Shard×2  Feather×1",  "result":"Armor HP+15 MP+15 STL+6"},
    {"name":"Dragon Scale Armor","bench":"Town",   "needs":"Dragon Scale×2  Iron Ore×3","result":"Armor HP+60 DEF+20"},
    # Advanced (Base Workshop Tier 1)
    {"name":"Reinforced Blade", "bench":"Workshop T1","needs":"Iron Ore×3  Wolf Pelt×1",  "result":"Weapon ATK+12"},
    {"name":"Scale Mail",       "bench":"Workshop T1","needs":"Scale Fragment×3  Iron Ore×2","result":"Armor HP+35 DEF+8"},
    {"name":"Frost Amulet",     "bench":"Workshop T1","needs":"Frost Crystal×2",          "result":"Accessory MP+20"},
    {"name":"Bone Shield",      "bench":"Workshop T1","needs":"Bone Shard×4  Iron Ore×2", "result":"Armor HP+20 DEF+10"},
    {"name":"Shadow Dagger",    "bench":"Workshop T1","needs":"Dark Shard×2  Feather×1",  "result":"Weapon ATK+9 STL+4"},
    # Advanced (Workshop Tier 2)
    {"name":"Dragonbone Spear", "bench":"Workshop T2","needs":"Dragon Scale×1  Iron Ore×4","result":"Weapon ATK+18"},
    {"name":"Frost Plate",      "bench":"Workshop T2","needs":"Frost Crystal×4  Iron Ore×4","result":"Armor HP+50 DEF+14"},
    {"name":"Shadow Crown",     "bench":"Workshop T2","needs":"Dark Shard×4  Feather×2",  "result":"Accessory MP+25 STL+8"},
    {"name":"Phoenix Elixir",   "bench":"Workshop T2","needs":"Frost Crystal×2  Scale Frag×2  Feather×2","result":"Heal +150 HP"},
    # Advanced (Workshop Tier 3)
    {"name":"Dragon Emperor Sword","bench":"Workshop T3","needs":"Dragon Scale×3  Dark Shard×3  Iron Ore×5","result":"Weapon ATK+28"},
    {"name":"Void Cloak",       "bench":"Workshop T3","needs":"Dark Shard×5  Feather×3  Frost Crystal×2","result":"Armor HP+30 MP+30 STL+12"},
    {"name":"War Titan Plate",  "bench":"Workshop T3","needs":"Dragon Scale×4  Iron Ore×10  Dark Shard×3","result":"Armor HP+100 DEF+25"},
]

# ── Material source reference ──────────────────────────────────────
MATERIAL_SOURCES = {
    "Iron Ore":       "Stone Golem (65%), Mines (common), Stone Golem kills",
    "Wolf Pelt":      "Wolf (65%), Goblin (20%)",
    "Bone Shard":     "Skeleton (55%)",
    "Feather":        "Harpy (55%)",
    "Frost Crystal":  "Ice Wolf (50%), Frost Wraith (60%), Snow mines",
    "Scale Fragment": "Sand Wyrm (45%), Scorpion (30%), Desert mines",
    "Dark Shard":     "Shadow Beast (55%), Cultist (25%)",
    "Dragon Scale":   "Frost Dragon boss (50%), Vaeltharion boss (90%), Dragon mines",
    "God Potion":     "Shadow Beast (3% rare), Dragon boss (12%)",
}


# ── MAIN ENCYCLOPEDIA SCREEN ──────────────────────────────────────

def open_encyclopedia(player=None):
    while True:
        _clear()
        print(C(f"\n{_GOLD}{_B}╔══════════════════════════════════════════════╗"))
        print(C(f"║  📖  ENCYCLOPEDIA & CODEX                    ║"))
        print(C(f"╚══════════════════════════════════════════════╝{_R}\n"))
        print(C(f"{_opt('1','Enemy Bestiary',     'What enemies drop and their traits')}"))
        print(C(f"{_opt('2','Shop Directory',     'What each city/continent sells')}"))
        print(C(f"{_opt('3','Crafting Guide',     'All recipes, benches and materials')}"))
        print(C(f"{_opt('4','Material Sources',   'Where to farm each crafting material')}"))
        if player:
            print(C(f"{_opt('5','My Discoveries',    'Enemies/locations you have encountered')}"))
        print(C(f"{_opt('0','Close',              '')}"))
        ch = input(f"\n  {_GOLD}>{_R} ").strip()
        if ch == "0": return
        elif ch == "1": _bestiary()
        elif ch == "2": _shop_directory()
        elif ch == "3": _crafting_guide()
        elif ch == "4": _material_sources()
        elif ch == "5" and player: _my_discoveries(player)


def _bestiary():
    _clear()
    print(C(f"\n{_CYAN}{_B}════  ENEMY BESTIARY  ════{_R}\n"))
    enemies = list(ENEMY_CODEX.items())
    # Paginate: 10 per page
    page = 0; per_page = 10
    while True:
        start = page * per_page
        chunk = enemies[start:start+per_page]
        _clear()
        print(f"\n  {_CYAN}{_B}════  ENEMY BESTIARY  ════{_R}  "
              f"{_DIM}Page {page+1}/{(len(enemies)-1)//per_page+1}{_R}\n")
        for name, data in chunk:
            zone_col = {
                "Plains":C_GREEN if False else _fg(100,180,100),
                "Forest":_fg(40,140,40),"Mountain":_fg(140,130,110),
                "Desert":_fg(200,170,60),"Snow":_fg(180,210,255),
                "Dungeon":_fg(140,80,180),"Boss":_RED,"Final Boss":_RED,
            }.get(data["zone"].split("/")[0], _WHITE)
            drops_str = "  ".join(f"{n} {_DIM}({c}){_R}" for n,c in data["drops"])
            print(C(f"{_WHITE}{_B}{name:<22}{_R} {zone_col}{data['zone']:<14}{_R}"))
            print(C(f"  {_DIM}Drops:{_R} {_YELL}{drops_str}{_R}"))
            if data["special"] != "None":
                print(C(f"  {_DIM}Special:{_R} {_ORAN}{data['special']}{_R}"))
            print()
        print(_div())
        print(C(f"{_opt('N','Next page')}  {_opt('P','Prev page')}  {_opt('0','Back')}"))
        ch = input(f"  {_GOLD}>{_R} ").strip().lower()
        if ch == "0": return
        elif ch == "n" and start + per_page < len(enemies): page += 1
        elif ch == "p" and page > 0: page -= 1


def _shop_directory():
    _clear()
    print(C(f"\n{_CYAN}{_B}════  SHOP DIRECTORY  ════{_R}\n"))
    for region, data in SHOP_CODEX.items():
        print(C(f"{_GOLD}{_B}{region}{_R}"))
        for item_name, stat, price in data["sells"]:
            print(C(f"  {_WHITE}{item_name:<28}{_R} {_DIM}{stat:<20}{_R} {_GOLD}{price}{_R}"))
        print()
    _pause()


def _crafting_guide():
    _clear()
    print(C(f"\n{_CYAN}{_B}════  CRAFTING GUIDE  ════{_R}\n"))
    benches = {}
    for rec in CRAFTING_CODEX:
        benches.setdefault(rec["bench"], []).append(rec)
    for bench, recs in benches.items():
        col = _TEAL if "Town" in bench else _ORAN if "T1" in bench else _PURP if "T2" in bench else _RED
        print(C(f"{col}{_B}{bench}{_R}"))
        for rec in recs:
            print(C(f"  {_WHITE}{rec['name']:<28}{_R} {_DIM}{rec['needs']}{_R}"))
            print(C(f"  {_DIM}→ {_GREEN}{rec['result']}{_R}"))
        print()
    _pause()


def _material_sources():
    _clear()
    print(C(f"\n{_CYAN}{_B}════  MATERIAL SOURCES  ════{_R}\n"))
    for mat, source in MATERIAL_SOURCES.items():
        print(C(f"{_YELL}{mat:<20}{_R}  {_DIM}{source}{_R}"))
    _pause()


def _my_discoveries(player):
    _clear()
    print(C(f"\n{_CYAN}{_B}════  YOUR DISCOVERIES  ════{_R}\n"))
    completed = getattr(player, "completed_quests", [])
    flags     = getattr(player, "flags", {})
    trophies  = []
    for base in getattr(player, "bases", None).bases.values() if hasattr(player,"bases") else []:
        trophies.extend(t["name"] for t in base.trophies)

    print(C(f"{_WHITE}Quests completed:{_R} {_GOLD}{len(completed)}{_R}"))
    for q in completed[:10]:
        print(C(f"  {_DIM}✓ {q}{_R}"))
    if len(completed) > 10:
        print(C(f"  {_DIM}... and {len(completed)-10} more{_R}"))

    print(C(f"\n{_WHITE}Boss trophies:{_R}"))
    if trophies:
        for t in trophies:
            print(C(f"  {_GOLD}🏆 {t}{_R}"))
    else:
        print(C(f"  {_DIM}None yet. Defeat bosses!{_R}"))

    dragon_slain = flags.get("dragon_slain", False)
    print(C(f"\n{_WHITE}Dragon slain:{_R} {(_GREEN+'Yes'+_R) if dragon_slain else (_DIM+'No'+_R)}"))
    _pause()
