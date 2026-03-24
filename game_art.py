"""
game_art.py — ASCII art sprites for Terminal-RPG.

Usage:
    from game_art import get_sprite, print_sprite, combat_layout

    print_sprite("Wolf")           # prints centred enemy sprite
    print_sprite("Swordsman")      # prints centred player sprite
    combat_layout(player, enemy)   # prints full combat art panel
"""

from game_term import C, W

_R  = "\033[0m"
_B  = "\033[1m"
def _fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"

# Colour palette
_RED   = _fg(220,60,60);   _GRN = _fg(80,200,80)
_BLUE  = _fg(80,130,220);  _CYN = _fg(80,220,220)
_GOLD  = _fg(255,215,0);   _WHT = _fg(255,255,255)
_DIM   = _fg(100,100,100); _PURP= _fg(180,80,220)
_ORAN  = _fg(220,140,40);  _YELL= _fg(240,200,60)
_TEAL  = _fg(60,180,180);  _PINK= _fg(220,100,160)
_GREY  = _fg(150,150,160); _BRN = _fg(160,100,60)


# ═══════════════════════════════════════════════════════════════
# SPRITES — each is a list of (colour_code, line_text) tuples
# ═══════════════════════════════════════════════════════════════

def _s(col, lines):
    """Helper: apply one colour to all lines."""
    return [(col, l) for l in lines]

def _ms(tuples):
    """Multi-colour sprite: list of (col, line) tuples already."""
    return tuples


SPRITES = {

    # ── ENEMIES ──────────────────────────────────────────────────

    "Slime": _ms([
        (_GRN,  "  .-~~~-.  "),
        (_GRN,  " (  o  o ) "),
        (_GRN,  "  `~-~~~'  "),
        (_DIM,  "  ~~~~~~~  "),
    ]),

    "Goblin": _ms([
        (_GRN,  "   ,-._.   "),
        (_GRN,  "  ( ^  ^ ) "),
        (_GRN,  "   > == <  "),
        (_GRN,  "  /|_||_|\\ "),
        (_BRN,  "  (`)(`)   "),
    ]),

    "Wolf": _ms([
        (_GREY, "    ^  ^   "),
        (_GREY, "  /( oo )/ "),
        (_GREY, " /  `--'   "),
        (_GREY, "/ /~~~~~\\ \\"),
        (_DIM,  "  `' UU `' "),
    ]),

    "Bandit": _ms([
        (_DIM,  "  _______  "),
        (_WHT,  " / _|_|_ \\ "),
        (_WHT,  "|   ===   |"),
        (_BRN,  " \\ |_X_| / "),
        (_BRN,  "  |  |  |  "),
        (_DIM,  "  (_) (_)  "),
    ]),

    "Harpy": _ms([
        (_YELL, "  >===<=   "),
        (_YELL, " /( o  o)\\ "),
        (_YELL, "< ( beak ) >"),
        (_BRN,  "  |/ \\ /|  "),
        (_BRN,  "  `~   ~'  "),
    ]),

    "Stone Golem": _ms([
        (_GREY, " [#######] "),
        (_GREY, " [# O  O #]"),
        (_GREY, " [#  --  #]"),
        (_GREY, " [#######] "),
        (_GREY, " [##] [##] "),
        (_DIM,  " (##) (##) "),
    ]),

    "Rock Wolf": _ms([
        (_GREY, "   /\\  /\\  "),
        (_GREY, "  (oO)(oO) "),
        (_GREY, " ##~~~~~## "),
        (_GREY, "/##/   \\##\\"),
        (_DIM,  "  `'   `'  "),
    ]),

    "Sand Wyrm": _ms([
        (_YELL, "  ~~~~__   "),
        (_ORAN, " (X) (X) ) "),
        (_ORAN, "  )~~==~~( "),
        (_ORAN, " (  JAWS  )"),
        (_YELL, "  ~~~|~~~  "),
        (_DIM,  "    |_|    "),
    ]),

    "Scorpion": _ms([
        (_ORAN, " \\\\  //    "),
        (_ORAN, " (o--o)>== "),
        (_ORAN, " /======\\  "),
        (_ORAN, "  \\====\\   "),
        (_ORAN, "    )====/ "),
        (_YELL, "   //  \\\\  "),
    ]),

    "Desert Raider": _ms([
        (_BRN,  "  ,-----,  "),
        (_WHT,  " | *   * | "),
        (_WHT,  " |  \\ /  | "),
        (_BRN,  " /|--===--|\\ "),
        (_BRN,  "  |  | |  | "),
        (_DIM,  "  (_) (_)  "),
    ]),

    "Dust Imp": _ms([
        (_PURP, "   ~ ~ ~   "),
        (_PURP, "  (>.<  )  "),
        (_PURP, " { () () } "),
        (_PURP, "  \\\\^^^//  "),
        (_DIM,  "  (( ^ ))  "),
    ]),

    "Ice Wolf": _ms([
        (_BLUE, "   *  *    "),
        (_CYN,  "  /(**)/   "),
        (_CYN,  " /~~~~~\\   "),
        (_BLUE, "/*~~~~~*\\  "),
        (_DIM,  "  '   '    "),
    ]),

    "Frost Wraith": _ms([
        (_CYN,  " *  *  *   "),
        (_CYN,  " (  O  O ) "),
        (_BLUE, " (  === )  "),
        (_CYN,  "  \\~~~~~/ "),
        (_BLUE, "   ~~~~    "),
        (_DIM,  "    ~~~    "),
    ]),

    "Snow Beast": _ms([
        (_WHT,  "   /\\ /\\   "),
        (_WHT,  "  (oo)(oo) "),
        (_WHT,  "  /======\\ "),
        (_WHT,  " /|XXXXXX|\\ "),
        (_DIM,  "   '    '  "),
    ]),

    "Ice Golem": _ms([
        (_CYN,  " [*******] "),
        (_CYN,  " [* 0  0 *]"),
        (_BLUE, " [*  ~~  *]"),
        (_CYN,  " [*******] "),
        (_CYN,  " [**] [**] "),
        (_DIM,  " (**) (**) "),
    ]),

    "Skeleton": _ms([
        (_WHT,  "   _____   "),
        (_WHT,  "  (O) (O)  "),
        (_WHT,  "   \\ ^ /   "),
        (_WHT,  "  /|___|\\  "),
        (_DIM,  " / |   | \\ "),
        (_DIM,  "   |   |   "),
    ]),

    "Cultist": _ms([
        (_PURP, "  /\\___/\\  "),
        (_PURP, " ( o   o ) "),
        (_RED,  " ( -=X=- ) "),
        (_PURP, "  \\|___|/  "),
        (_DIM,  "   | | |   "),
        (_DIM,  "  (_) (_)  "),
    ]),

    "Shadow Beast": _ms([
        (_DIM,  " .~~~~~~~~~. "),
        (_PURP, "(  )(> <)(  )"),
        (_PURP, " ( ======= ) "),
        (_DIM,  "  )~~~~~~~(  "),
        (_DIM,  " ~~~~~~~~~~~~"),
    ]),

    "Armored Knight": _ms([
        (_GREY, "  [======]  "),
        (_GREY, "  | X  X |  "),
        (_GREY, "  |  --  |  "),
        (_GREY, " [|======|] "),
        (_BRN,  "  |      |  "),
        (_GREY, "  [#]  [#]  "),
    ]),

    # ── BOSSES ───────────────────────────────────────────────────

    "Goblin King": _ms([
        (_GOLD, "   ,-._.    "),
        (_GOLD, "  (>^  ^<)  "),
        (_GOLD, "   [KING]   "),
        (_GRN,  "  /|====|\\  "),
        (_GRN,  " / | () | \\ "),
        (_BRN,  "   |_||_|   "),
    ]),

    "Frost Dragon": _ms([
        (_CYN,  "  /\\ * * /\\ "),
        (_BLUE, " /  (O)(O)  \\ "),
        (_CYN,  "/   ~~~~~~   \\"),
        (_BLUE, "|  DRAGON!!!  |"),
        (_CYN,  "\\  /~~~~~~\\  /"),
        (_BLUE, " \\/____X___\\/ "),
        (_DIM,  "  ~|~  ~|~   "),
    ]),

    "Shadow Lord": _ms([
        (_DIM,  " ~~~~~~~~~~~~~~ "),
        (_PURP, "(   O     O   ) "),
        (_PURP, "(  >=====<    ) "),
        (_RED,  "( SHADOW LORD ) "),
        (_PURP, "(   \\=====/)  ) "),
        (_DIM,  " ~~~~~~~~~~~~~~~ "),
    ]),

    "Dragon": _ms([
        (_RED,  "    /\\   /\\    "),
        (_RED,  "   /  \\ /  \\   "),
        (_ORAN, "  ( (o) (o) )  "),
        (_RED,  "   \\  ~~~  /   "),
        (_ORAN, "  VAELTHARION  "),
        (_RED,  "  /===========\\ "),
        (_ORAN, " / /  DRAGON \\ \\"),
        (_RED,  "/__|______|__\\ "),
        (_DIM,  "   ~||~  ~||~  "),
    ]),

    "Vaeltharion": _ms([
        (_RED,  "       /\\       "),
        (_RED,  "      /  \\      "),
        (_ORAN, "   /\\ \\  / /\\   "),
        (_RED,  "  /  \\ \\/ /  \\  "),
        (_ORAN, " ( (X)>~~<(X) ) "),
        (_RED,  "  \\ ~~=====~~ /  "),
        (_ORAN, "   VAELTHARION   "),
        (_RED,  "  /=============\\ "),
        (_ORAN, " / ANCIENT EVIL \\ "),
        (_RED,  "/__|_________|__\\ "),
        (_DIM,  "    ~||~  ~||~    "),
    ]),

    # ── PLAYER CLASSES ───────────────────────────────────────────

    "Swordsman": _ms([
        (_YELL, "    ( O )    "),
        (_WHT,  "   /|___|\\   "),
        (_WHT,  "  / |===| \\  "),
        (_YELL, "   /  |  \\   "),
        (_BRN,  "  /   |   \\  "),
        (_BRN,  "  |___|___|  "),
    ]),

    "Mage": _ms([
        (_CYN,  "  *  *  *   "),
        (_PURP, "   /\\___     "),
        (_PURP, "  /( o o)\\   "),
        (_CYN,  " / |=====| \\ "),
        (_PURP, "   |     |   "),
        (_DIM,  "   |_____|   "),
    ]),

    "Rogue": _ms([
        (_DIM,  "  (- - -)   "),
        (_PURP, "   \\|_|/    "),
        (_DIM,  "  >|   |<   "),
        (_PURP, "   |   |    "),
        (_DIM,  "  /     \\   "),
        (_DIM,  " (_) (_)    "),
    ]),

    "Tank": _ms([
        (_GREY, "  [#####]   "),
        (_GREY, "  [X   X]   "),
        (_GREY, "  [#####]   "),
        (_GREY, " [#######]  "),
        (_GREY, " [##] [##]  "),
        (_DIM,  " (##) (##)  "),
    ]),

    "Healer": _ms([
        (_GRN,  "  * ( ) *   "),
        (_WHT,  "   /|+|\\    "),
        (_GRN,  "  / |+| \\   "),
        (_GRN,  "   /   \\    "),
        (_WHT,  "  /     \\   "),
        (_DIM,  " (_)   (_)  "),
    ]),

    "Blade Master": _ms([
        (_GOLD, "  ~( O )~   "),
        (_GOLD, "  /|___|\\   "),
        (_YELL, " //|===|\\\\ "),
        (_GOLD, " / |   | \\ "),
        (_YELL, "/==|   |==\\ "),
        (_BRN,  "   |___|    "),
    ]),

    "Archmage": _ms([
        (_GOLD, " * * * * *  "),
        (_PURP, "   /\\_____  "),
        (_PURP, "  /( * * )\\ "),
        (_CYN,  " / |=====| \\"),
        (_PURP, "   |_____| "),
        (_GOLD, "  *  ~~~  * "),
    ]),

    "Shadow Assassin": _ms([
        (_DIM,  " ~~ ~~~ ~~  "),
        (_PURP, "  (@ . @)   "),
        (_DIM,  "  /|___|\\   "),
        (_PURP, " >|     |<  "),
        (_DIM,  "  |_____|   "),
        (_DIM,  " /  ~~~  \\  "),
    ]),

    "War Titan": _ms([
        (_GREY, " [#######]  "),
        (_RED,  " [X     X]  "),
        (_GREY, " [#######]  "),
        (_GREY, "[#########] "),
        (_GREY, "[###] [###] "),
        (_DIM,  "(###) (###) "),
    ]),

    "Arch Priest": _ms([
        (_GOLD, " * (+) (+) *"),
        (_WHT,  "  /\\___/\\   "),
        (_GOLD, " / |+++| \\  "),
        (_WHT,  "   |   |    "),
        (_GOLD, "  /|   |\\   "),
        (_DIM,  " (_)   (_)  "),
    ]),

    # ── ITEMS (used in status / shop screens) ────────────────────

    "sword": _ms([
        (_GREY, "    /       "),
        (_WHT,  "   /        "),
        (_GREY, "  /         "),
        (_GREY, "   ===      "),
    ]),

    "staff": _ms([
        (_CYN,  "   * * *    "),
        (_PURP, "    |||      "),
        (_PURP, "    |||      "),
        (_BRN,  "    |_|      "),
    ]),

    "dagger": _ms([
        (_GREY, "   /        "),
        (_WHT,  "  /         "),
        (_DIM,  "  ===       "),
    ]),

    "shield": _ms([
        (_GREY, "  ,-----.   "),
        (_GREY, " /  [ ]  \\  "),
        (_GREY, "|         | "),
        (_GREY, " \\       /  "),
        (_GREY, "  '-----'   "),
    ]),

    "helmet": _ms([
        (_GREY, "  ,-----,   "),
        (_GREY, " /  [ ]  \\  "),
        (_GREY, "|   | |   | "),
        (_GREY, " \\=======/ "),
    ]),

    "armor": _ms([
        (_GREY, " ,-------.  "),
        (_GREY, "| [#] [#] | "),
        (_GREY, "|  \\ = /  | "),
        (_GREY, "|   |=|   | "),
        (_GREY, " '-'   '-'  "),
    ]),

    "ring": _ms([
        (_GOLD, "   .---.    "),
        (_GOLD, "  / o o \\   "),
        (_GOLD, "  \\     /   "),
        (_GOLD, "   '---'    "),
    ]),

    "potion": _ms([
        (_GRN,  "   ,---,    "),
        (_GRN,  "  ( ~~~ )   "),
        (_WHT,  " (       )  "),
        (_GRN,  "  (     )   "),
        (_DIM,  "   '---'    "),
    ]),
}

# Fallback generic sprites for unknown names
_FALLBACK_ENEMY = _ms([
    (_RED,  "  /~~~~~\\  "),
    (_RED,  " ( ? ? ? ) "),
    (_RED,  "  \\_____/  "),
    (_DIM,  "  |     |  "),
])

_FALLBACK_PLAYER = _ms([
    (_WHT,  "   ( O )   "),
    (_WHT,  "  /|___|\\  "),
    (_WHT,  "   |   |   "),
    (_DIM,  "  (_) (_)  "),
])


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

# All player class names
PLAYER_CLASSES = {"Swordsman","Mage","Rogue","Tank","Healer",
                  "Blade Master","Archmage","Shadow Assassin","War Titan","Arch Priest"}

# Item slot → sprite key
SLOT_SPRITE = {
    "weapon": "sword", "armor": "armor", "helmet": "helmet",
    "shield": "shield", "ring": "ring", "amulet": "ring",
    "cloak": "armor",
}


def get_sprite(name: str) -> list:
    """Return list of (colour, line) tuples for the named sprite."""
    if name in SPRITES:
        return SPRITES[name]
    # Weapon-type fallback by name keywords
    nl = name.lower()
    if any(k in nl for k in ("sword","blade","dagger","mace","hammer")): return SPRITES["sword"]
    if any(k in nl for k in ("staff","rod","sceptre","wand")):           return SPRITES["staff"]
    if "shield" in nl:  return SPRITES["shield"]
    if "helm" in nl or "hood" in nl: return SPRITES["helmet"]
    if "armor" in nl or "mail" in nl or "robe" in nl or "vest" in nl or "suit" in nl:
        return SPRITES["armor"]
    if "ring" in nl or "amulet" in nl: return SPRITES["ring"]
    if "potion" in nl or "ether" in nl or "elixir" in nl: return SPRITES["potion"]
    # Default by context
    return _FALLBACK_PLAYER if name in PLAYER_CLASSES else _FALLBACK_ENEMY


def render_sprite(name: str) -> list[str]:
    """Return list of coloured strings ready to print."""
    sprite = get_sprite(name)
    return [f"{col}{line}{_R}" for col, line in sprite]


def sprite_width(name: str) -> int:
    """Visible width of the sprite (longest line, without ANSI)."""
    sprite = get_sprite(name)
    return max(len(line) for _, line in sprite)


def print_sprite(name: str, label: str = "", indent: int = 0):
    """Print a centred sprite with optional label underneath."""
    lines = render_sprite(name)
    prefix = " " * indent if indent else ""
    for l in lines:
        print(C(prefix + l))
    if label:
        print(C(f"{prefix}{_GOLD}{_B}{label:^{sprite_width(name)}}{_R}"))


def side_by_side(left_name: str, right_name: str,
                 left_label: str = "", right_label: str = "",
                 gap: int = 6) -> list[str]:
    """
    Return a list of centred strings showing two sprites side by side.
    Left sprite on left, right sprite on right, gap chars between.
    """
    L = render_sprite(left_name)
    R = render_sprite(right_name)
    lw = sprite_width(left_name)
    rw = sprite_width(right_name)
    height = max(len(L), len(R))

    # Pad shorter sprite with blank lines
    while len(L) < height: L.append(" " * lw)
    while len(R) < height: R.append(" " * rw)

    # Add labels as final row
    if left_label or right_label:
        LL = f"{_GOLD}{_B}{left_label:^{lw}}{_R}"
        RL = f"{_GOLD}{_B}{right_label:^{rw}}{_R}"
        L.append(LL); R.append(RL)

    spacer = " " * gap
    result = []
    for l, r in zip(L, R):
        result.append(C(l + spacer + r))
    return result


def combat_layout(player_name: str, enemy_name: str,
                  player_label: str = "", enemy_label: str = "") -> list[str]:
    """
    Full combat art row: player sprite  VS  enemy sprite.
    Returns list of printable lines.
    """
    vs = f"  {_RED}{_B}VS{_R}  "
    lines = side_by_side(
        player_name, enemy_name,
        player_label or player_name,
        enemy_label or enemy_name,
        gap=8,
    )
    # Insert VS marker in the middle row
    mid = len(lines) // 2
    lines[mid] = C(f"{_WHT}{get_sprite(player_name)[0][1]}{_R}"
                   + " " * 3 + f"{_RED}{_B}⚔ VS ⚔{_R}" + " " * 3
                   + f"{_RED}{get_sprite(enemy_name)[0][1]}{_R}") if False else lines[mid]
    return lines


def equipped_row(equipped: dict, max_cols: int = 120) -> list[str]:
    """
    Show small sprite icons for each equipped item in a horizontal row.
    equipped = player.equipped dict  {slot: Equipment|None}
    """
    from game_items import Equipment as _Eq
    items = [(sl, it) for sl, it in equipped.items() if it is not None and isinstance(it, _Eq)]
    if not items:
        return [C(f"  {_DIM}No equipment worn.{_R}")]

    result = []
    for sl, it in items:
        sprite_key = SLOT_SPRITE.get(sl, "armor")
        sp = render_sprite(sprite_key)
        sw = sprite_width(sprite_key)
        label = f"{_GOLD}{it.name[:sw]}{_R}"
        stat  = f"{_DIM}{it.stat_line()[:sw]}{_R}" if hasattr(it,"stat_line") else ""
        for line in sp:
            result.append(C(line))
        result.append(C(label))
        if stat: result.append(C(stat))
        result.append("")
    return result
