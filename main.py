"""main.py — Terminal-RPG launcher with raw-input world loop."""

import os
import json
from game_term import C, P, div, clr, W, H, hpbar, mpbar, box_top, box_mid, box_bot, get_size
from game_player import Player
from game_world import WorldMap, clear, fg, C_GOLD, C_WHITE, C_DIM, C_GREEN, C_RED, C_CYAN, C_PURP, R_, B_
from game_stories import story_selection_screen, MAIN_STORIES
from game_lang import T, set_language, LANG, LANGUAGE_NAMES, pick_language_screen, save_language_pref, load_language_pref
from game_base import BaseMenu, build_base_on_map

from game_saves import (
    save_browser, save_slot, load_slot, slot_exists,
    AutoSave, migrate_legacy_saves, AUTOSAVE_SLOT, MAX_SLOTS
)

# Legacy paths kept only for migration (handled on startup)
_LEGACY_PLAYER = "savegame.json"
_LEGACY_WORLD  = "world_save.json"

# Sentinel raised to go back one step in character creation
class _BackSignal(Exception): pass

def div(w=None):
    w=w or min(W()-4, 120)
    return C(f"{C_DIM}{chr(8212)*w}{R_}")

def opt(key, lbl, hint=""):
    inner = (f"  {C_GOLD}{B_}[{key}]{R_} {C_WHITE}{lbl}{R_}"
             + (f"  {C_DIM}{hint}{R_}" if hint else ""))
    return C(inner)

def back_opt():
    return opt('0', 'Back', 'Return to previous screen')

_BANNER_LINES = [
    f"{C_GOLD}{B_}",
    f"████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗         ██████╗ ██████╗  ██████╗",
    f"╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║         ██╔══██╗██╔══██╗██╔════╝",
    f"   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║         ██████╔╝██████╔╝██║  ███╗",
    f"   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║         ██╔══██╗██╔═══╝ ██║   ██║",
    f"   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗    ██║  ██║██║     ╚██████╔╝",
    f"   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝      ╚═════╝{R_}",
    f"{C_CYAN}Open World  ·  DnD-Style  ·  Anime Progression  ·  Real-Time Movement{R_}",
]

def BANNER():
    return "\n".join(C(l) for l in _BANNER_LINES)

# ── Step 1: Name entry ────────────────────────────────────────────

def _step_name():
    """Ask for character name. Returns name str, or raises _BackSignal."""
    clear()
    print(BANNER())
    print(div())
    print(C(f"\n{C_CYAN}{B_}══════  NEW GAME  ──  Step 1 of 4: NAME  ══════{R_}\n"))
    print(back_opt())
    print(C(f"\n{C_DIM}Enter your character's name (or press Enter for 'Hero'):{R_}"))
    val = input(C(f"\n{C_GOLD}>{R_} ")).strip()
    if val == "0": raise _BackSignal
    return val or "Hero"

# ── Step 2: Class selection ───────────────────────────────────────

def _step_class(name):
    """Ask for class. Returns job_name str, or raises _BackSignal."""
    from game_jobs import STARTER_JOBS
    descs = {
        "Swordsman": ("Balanced melee. Good HP & ATK. Crits often.",  fg(220,180,80),  "STL  0 → Blade Master"),
        "Mage":      ("High magic damage. Low HP. Status effects.",    fg(80,200,220),  "STL +3 → Archmage"),
        "Rogue":     ("Fast, high dodge & crit. Applies poison.",      fg(180,80,220),  "STL +8 → Shadow Assassin"),
        "Tank":      ("Massive HP & DEF. Nearly unkillable.",          fg(160,160,160), "STL -3 → War Titan"),
        "Healer":    ("Support & sustain. Best healing power.",        fg(80,200,120),  "STL +2 → Arch Priest"),
    }
    while True:
        clear()
        print(BANNER())
        print(div())
        print(C(f"\n{C_CYAN}{B_}══════  {name}  ──  Step 2 of 4: CLASS  ══════{R_}\n"))
        for i, job in enumerate(STARTER_JOBS, 1):
            desc, col, evo = descs.get(job, ("", C_WHITE, ""))
            print(C(f"{C_GOLD}{B_}[{i}]{R_} {col}{B_}{job:<16}{R_}  {C_DIM}{desc:<42}{R_}  {C_PURP}{evo}{R_}"))
        print()
        print(back_opt())
        ch = input(C(f"\n{C_GOLD}>{R_} Choose class (1-{len(STARTER_JOBS)}): ")).strip()
        if ch == "0": raise _BackSignal
        if ch.isdigit() and 1 <= int(ch) <= len(STARTER_JOBS):
            return STARTER_JOBS[int(ch)-1]
        print(C(f"{C_RED}Enter a number 1–{len(STARTER_JOBS)}.{R_}"))

# ── Step 3: Movement mode ─────────────────────────────────────────

def _step_movement(name):
    """Ask for movement mode. Returns 'wasd' or 'numpad', or raises _BackSignal."""
    while True:
        clear()
        print(BANNER())
        print(div())
        print(C(f"\n{C_CYAN}{B_}══════  {name}  ──  Step 3 of 4: MOVEMENT  ══════{R_}\n"))
        print(opt('1', T('move.wasd'),  'W/A/S/D — classic cardinal movement'))
        print(opt('2', T('move.8dir'),  'Numpad 1-9 or vi-keys (YUHJKLBN) — includes diagonals'))
        print(C(f"\n{C_DIM}Arrow keys always work in both modes. You can change this in-game later.{R_}"))
        print()
        print(back_opt())
        ch = input(C(f"\n{C_GOLD}>{R_} Choose mode (1/2): ")).strip()
        if ch == "0": raise _BackSignal
        if ch == "1": return "wasd"
        if ch == "2": return "numpad"
        print(C(f"{C_RED}Enter 1 or 2.{R_}"))

# ── Step 4: Story selection ───────────────────────────────────────

def _step_story(name):
    """Ask for main story. Returns story_id, or raises _BackSignal."""
    from game_lang import _GOLD, _B, _R, _DIM, _RED
    stories = list(MAIN_STORIES.items())
    while True:
        clear()
        print(BANNER())
        print(div())
        print(C(f"\n{C_CYAN}{B_}══════  {name}  ──  Step 4 of 4: STORY  ══════{R_}\n"))
        print(C(f"{C_DIM}Side stories will be discovered as you explore.{R_}\n"))
        for i, (sid, s) in enumerate(stories, 1):
            col = s["colour"]
            print(C(f"{C_GOLD}{B_}[{i}]{R_} {col}{B_}{s['title']}{R_}"))
            words = s["intro"].split()
            line = "  "; lines = []
            for w in words:
                if len(line)+len(w)+1 > 62:
                    lines.append(line); line = "  "+w+" "
                else:
                    line += w+" "
            if line.strip(): lines.append(line)
            for l in lines: print(C(f"{C_DIM}{l}{R_}"))
            print()
        print(back_opt())
        ch = input(C(f"{C_GOLD}>{R_} Choose story (1-{len(stories)}): ")).strip()
        if ch == "0": raise _BackSignal
        if ch.isdigit() and 1 <= int(ch) <= len(stories):
            return stories[int(ch)-1][0]
        print(C(f"{C_RED}Enter a number 1–{len(stories)}.{R_}"))

# ── Character creation — orchestrates all 4 steps ─────────────────

def character_creation():
    """
    Walks through 4 steps with full back-navigation.
    Returns a ready Player, or returns None if user backs all the way out.
    """
    descs = {
        "Swordsman": ("Balanced melee. Good HP & ATK. Crits often.",  fg(220,180,80),  ""),
        "Mage":      ("High magic damage. Low HP. Status effects.",    fg(80,200,220),  ""),
        "Rogue":     ("Fast, high dodge & crit. Applies poison.",      fg(180,80,220),  ""),
        "Tank":      ("Massive HP & DEF. Nearly unkillable.",          fg(160,160,160), ""),
        "Healer":    ("Support & sustain. Best healing power.",        fg(80,200,120),  ""),
    }

    step = 1
    name = movement_mode = job_name = story_id = None

    while step <= 4:
        try:
            if step == 1:
                name = _step_name()
                step = 2
            elif step == 2:
                job_name = _step_class(name)
                step = 3
            elif step == 3:
                movement_mode = _step_movement(name)
                step = 4
            elif step == 4:
                story_id = _step_story(name)
                step = 5   # done
        except _BackSignal:
            step -= 1
            if step < 1:
                return None   # backed all the way out to main menu

    # ── Summary screen ────────────────────────────────────────────
    player = Player(name, job_name)
    player.movement_mode = movement_mode
    player.stories.start_main(story_id)

    _, col, _ = descs.get(job_name, ("", C_WHITE, ""))
    story = MAIN_STORIES.get(story_id)
    clear()
    print(BANNER())
    print(div())
    print(C(f"\n{C_GOLD}{B_}╔════════════════════════════════════════╗"))
    print(C(f"║  {name} the {job_name} begins their journey!  ║"))
    print(C(f"╚════════════════════════════════════════╝{R_}\n"))
    print(C(f"{col}HP:{player.max_hp}  ATK:{player.atk}  MP:{player.max_mp}  Stealth:{player.get_stealth()}{R_}"))
    print(C(f"\n{C_WHITE}Starting skills:{R_}"))
    for sk in player.skills:
        base = f"DMG {sk.damage}" if sk.damage else f"HEAL {sk.heal}" if sk.heal else "?"
        print(C(f"  {C_CYAN}→{R_} {C_WHITE}{sk.name}{R_}  {C_DIM}[{base}, MP:{sk.mana_cost}]{R_}"))
    print(C(f"\n{C_GOLD}You carry 1 God Potion.{R_} {C_DIM}Auto-activates at 0 HP. Guard it.{R_}"))
    print(C(f"\n{C_PURP}Movement:{R_} {C_WHITE}{'WASD (4-dir)' if movement_mode=='wasd' else '8-Direction (numpad)'}{R_}"))
    if story:
        print(C(f"\n{story['colour']}{B_}Main Story: {story['title']}{R_}"))
    print(C(f"{C_DIM}[J] to view your story journal anytime. Explore to discover side stories.{R_}"))
    print()
    print(back_opt())
    val = input(C(f"\n{C_GOLD}>{R_} Press Enter to begin (or 0 to go back): ")).strip()
    if val == "0":
        # Back to story selection
        step = 4
        return character_creation.__wrapped__(name, job_name, movement_mode)
    return player


# Attach a small helper so back-from-summary restarts from step 4
def _restart_from_step4(name, job_name, movement_mode):
    """Resume char creation at step 4 (story) keeping name/class/movement."""
    descs = {
        "Swordsman": ("Balanced melee. Good HP & ATK. Crits often.",  fg(220,180,80),  ""),
        "Mage":      ("High magic damage. Low HP. Status effects.",    fg(80,200,220),  ""),
        "Rogue":     ("Fast, high dodge & crit. Applies poison.",      fg(180,80,220),  ""),
        "Tank":      ("Massive HP & DEF. Nearly unkillable.",          fg(160,160,160), ""),
        "Healer":    ("Support & sustain. Best healing power.",        fg(80,200,120),  ""),
    }
    step = 4
    story_id = None
    while step >= 1:
        try:
            if step == 4:
                story_id = _step_story(name)
                break
            elif step == 3:
                movement_mode = _step_movement(name)
                step = 4
            elif step == 2:
                job_name = _step_class(name)
                step = 3
            elif step == 1:
                name = _step_name()
                step = 2
        except _BackSignal:
            step -= 1
            if step < 1:
                return None
    if story_id is None:
        return None

    player = Player(name, job_name)
    player.movement_mode = movement_mode
    player.stories.start_main(story_id)

    _, col, _ = descs.get(job_name, ("", C_WHITE, ""))
    story = MAIN_STORIES.get(story_id)
    clear()
    print(BANNER())
    print(div())
    print(C(f"\n{C_GOLD}{B_}╔════════════════════════════════════════╗"))
    print(C(f"║  {name} the {job_name} begins their journey!  ║"))
    print(C(f"╚════════════════════════════════════════╝{R_}\n"))
    print(C(f"{col}HP:{player.max_hp}  ATK:{player.atk}  MP:{player.max_mp}  Stealth:{player.get_stealth()}{R_}"))
    print(C(f"\n{C_WHITE}Starting skills:{R_}"))
    for sk in player.skills:
        base = f"DMG {sk.damage}" if sk.damage else f"HEAL {sk.heal}" if sk.heal else "?"
        print(C(f"  {C_CYAN}→{R_} {C_WHITE}{sk.name}{R_}  {C_DIM}[{base}, MP:{sk.mana_cost}]{R_}"))
    print(C(f"\n{C_GOLD}You carry 1 God Potion.{R_} {C_DIM}Auto-activates at 0 HP. Guard it.{R_}"))
    print(C(f"\n{C_PURP}Movement:{R_} {C_WHITE}{'WASD (4-dir)' if movement_mode=='wasd' else '8-Direction (numpad)'}{R_}"))
    if story:
        print(C(f"\n{story['colour']}{B_}Main Story: {story['title']}{R_}"))
    print(C(f"{C_DIM}[J] to view your story journal anytime. Explore to discover side stories.{R_}"))
    print()
    print(back_opt())
    val = input(C(f"\n{C_GOLD}>{R_} Press Enter to begin (or 0 to go back): ")).strip()
    if val == "0":
        return _restart_from_step4(name, job_name, movement_mode)
    return player

character_creation.__wrapped__ = _restart_from_step4


# ── Quick inventory ───────────────────────────────────────────────

def _quick_inventory(player, world=None):
    import os
    R_ = "\033[0m"; B_ = "\033[1m"
    def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
    C_GOLD=fg(255,215,0); C_WHITE=fg(255,255,255); C_DIM=fg(90,90,100)
    C_GREEN=fg(80,200,80); C_RED=fg(220,60,60); C_CYAN=fg(80,220,220)

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(C(f"\n{C_CYAN}{B_}════  QUICK BAG  ════{R_}  "
              f"{C_DIM}HP {player.hp}/{player.max_hp}  MP {player.mp}/{player.max_mp}{R_}\n"))
        if not player.inventory:
            print(C(f"{C_DIM}Your bag is empty.{R_}"))
        else:
            for i, it in enumerate(player.inventory, 1):
                t_col = (C_GREEN if it.item_type=="heal" else
                         fg(80,130,220) if it.item_type=="mana" else
                         fg(255,215,0) if it.item_type=="god" else
                         fg(180,80,220) if it.item_type=="equipment" else
                         C_DIM)
                extra = ""
                if it.item_type == "heal":  extra = f"  {C_GREEN}+{it.value} HP{R_}"
                elif it.item_type == "mana": extra = f"  {fg(80,130,220)}+{it.value} MP{R_}"
                elif hasattr(it,"stat_line"): extra = f"  {C_DIM}{it.stat_line()}{R_}"
                print(C(f"{C_GOLD}[{i:>2}]{R_} {t_col}{it.name:<26}{R_}{extra}"))

        print(C(f"\n{C_GOLD}[U]{R_}{C_DIM} Use item  {R_}"
              f"{C_GOLD}[E]{R_}{C_DIM} Equip item  {R_}"
              f"{C_GOLD}[0]{R_}{C_DIM} Close{R_}"))
        ch = input(C(f"\n{C_GOLD}>{R_} ")).strip().lower()
        if ch == "0": return
        elif ch == "u":
            player.use_inventory_item()
        elif ch == "e":
            player.equip_item()
        elif ch.isdigit():
            idx = int(ch)-1
            if 0 <= idx < len(player.inventory):
                it = player.inventory[idx]
                if it.item_type in ("heal","mana"):
                    used = it.use(player)
                    if used:
                        player.inventory.pop(idx)
                elif hasattr(it,"slot"):
                    old = player.equipped.get(it.slot)
                    if old:
                        player.inventory.append(old)
                        player.max_hp -= old.hp_bonus
                        player.max_mp -= old.mp_bonus
                        player.atk    -= old.atk_bonus
                    player.equipped[it.slot] = it
                    player.inventory.pop(idx)
                    player.max_hp += it.hp_bonus
                    player.max_mp += it.mp_bonus
                    player.atk    += it.atk_bonus
                    player.hp = min(player.hp, player.max_hp)
                    print(C(f"{C_GREEN}Equipped {it.name}!{R_}"))
                    input(C(f"{C_DIM}(Enter){R_}"))
                else:
                    print(C(f"{C_DIM}Can't use {it.name} here.{R_}"))
                    input(C(f"{C_DIM}(Enter){R_}"))


# ── World loop ────────────────────────────────────────────────────

def world_loop(player, world, autosave: "AutoSave | None" = None):
    from game_input import InputHandler
    inp = InputHandler(mode=player.movement_mode)
    if autosave is None:
        autosave = AutoSave(interval=30)

    while True:
        world.render(player)

        if not player.is_alive():
            clear()
            print(C(f"\n{C_RED}{B_}You have fallen. Your legend ends here.{R_}\n"))
            input(C(f"{C_DIM}(Press Enter){R_}")); return

        action = inp.get_action()

        if action[0] == 'move':
            _, dx, dy = action
            world.move_player(dx, dy, player)
            if autosave.tick(player, world):
                world.last_msg = f"{C_DIM}[Autosaved]{R_}"

        elif action[0] == 'cmd':
            cmd = action[1]
            if   cmd == 'enter':    world.enter_location(player)
            elif cmd == 'fast':     world.fast_travel(player)
            elif cmd == 'overview': world.show_overview()
            elif cmd == 'map':      world.show_locations()
            elif cmd == 'help':     world.show_help()
            elif cmd == 'journal':  player.stories.show_journal()
            elif cmd == 'inventory':
                _quick_inventory(player, world)
            elif cmd == 'codex':
                from game_codex import open_encyclopedia
                open_encyclopedia(player)
            elif cmd == 'base':
                ter = world.terrain[world.player_y][world.player_x]
                cid = world.cont_map[world.player_y][world.player_x]
                if ter in ('~', ';'):
                    world.last_msg = f"{C_RED}Can't build on water.{R_}"
                else:
                    if hasattr(player,'bases') and player.bases.has_base(cid):
                        player_base = player.bases.get_base(cid)
                        if player_base.x == world.player_x and player_base.y == world.player_y:
                            BaseMenu(player, player_base).enter()
                        else:
                            world.last_msg = f"{C_DIM}Your base on this continent is elsewhere. Enter it via its city.{R_}"
                    else:
                        built = build_base_on_map(player, world.player_x, world.player_y, cid)
                        if built:
                            world.last_msg = f"{C_GREEN}Base built! Enter cities to access base menu.{R_}"
            elif cmd == 'party':
                clear()
                player.party.show()
                input(C(f"\n{C_DIM}(Press Enter){R_}"))
            elif cmd == 'save':
                result = save_browser(mode="save", current_player=player,
                                      current_world=world, autosave=autosave)
                if result:
                    world.last_msg = f"{C_GREEN}Saved to slot {result}!{R_}"
            elif cmd == 'quit':
                clear()
                print(C(f"\n{C_CYAN}Save before quitting?{R_}\n"))
                print(opt('S', 'Save to a slot & quit'))
                print(opt('A', 'Autosave & quit'))
                print(opt('N', 'Quit without saving'))
                print(opt('C', 'Cancel — keep playing'))
                ch = input(C(f"\n{C_GOLD}>{R_} ")).strip().lower()
                if ch == 'c': continue
                if ch == 's':
                    save_browser(mode="save", current_player=player,
                                 current_world=world, autosave=autosave)
                elif ch == 'a':
                    autosave.force(player, world)
                    print(C(f"\n{C_GREEN}Autosaved!{R_}"))
                    input(C(f"{C_DIM}(Press Enter){R_}"))
                return


# ── Main menu ─────────────────────────────────────────────────────

def main():
    import game_lang
    load_language_pref()
    # One-time migration of legacy savegame.json -> saves/slot1
    migrated = migrate_legacy_saves()

    while True:
        clear()
        print(BANNER())
        print(div())
        cur_lang = LANGUAGE_NAMES.get(game_lang.LANG, game_lang.LANG)
        print()
        print(opt('1', T('menu.new_game'),  'Start a fresh adventure'))
        print(opt('2', T('menu.load_game'), 'Continue — choose save slot'))
        print(opt('L', T('menu.language'),  cur_lang))
        print(opt('3', T('menu.quit'),       'Exit Terminal-RPG'))

        if migrated:
            print(C(f"\n  {C_GREEN}✓ Old save migrated to Slot 1!{R_}"))
            migrated = False

        # Show a summary of occupied slots
        from game_saves import _load_meta, MAX_SLOTS, AUTOSAVE_SLOT
        any_save = False
        for s in range(0, MAX_SLOTS + 1):
            meta = _load_meta(s)
            if meta:
                tag  = " [AUTO]" if s == AUTOSAVE_SLOT else f" [Slot {s}]"
                line = (f"{C_DIM}{tag}  {meta['name']} Lv{meta['level']} "
                        f"{meta['job']} — {meta['location']}"
                        f"  {meta['datetime']}{R_}")
                print(C(line))
                any_save = True
        if not any_save:
            print(C(f"  {C_DIM}No saves found.{R_}"))

        ch = input(C(f"\n{C_GOLD}>{R_} ")).strip().lower()

        if ch == "1":
            player = character_creation()
            if player is None:
                continue
            world = WorldMap()
            autosave = AutoSave(interval=30)
            world_loop(player, world, autosave)

        elif ch == "2":
            result = save_browser(mode="load")
            if result is None:
                continue
            player, world = result
            # Restore language preference
            saved_lang = getattr(player, 'language', None)
            if saved_lang:
                set_language(saved_lang)
            world.last_msg = f"{C_GREEN}Welcome back, {player.name}!{R_}"
            print(C(f"\n{C_GREEN}Loaded: {player.name} Lv {player.level} {player.job.name}{R_}"))
            input(C(f"{C_DIM}{T('ui.press_enter')}{R_}"))
            autosave = AutoSave(interval=30)
            world_loop(player, world, autosave)

        elif ch == "l":
            pick_language_screen()
            save_language_pref()

        elif ch == "3":
            clear()
            print(C(f"\n{C_GOLD}Thanks for playing Terminal-RPG!{R_}\n")); break

if __name__ == "__main__":
    main()