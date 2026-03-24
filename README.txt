=== ANIME DUNGEON CHRONICLES ===
         Terminal RPG — Open World Edition

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO INSTALL & RUN:
  1. Clone or download the repository
  2. Run: pip install -r requirements.txt
  3. Run: python main.py 
         - if you are using (WSL)
         - use (python3 main.py not python main.py

  One-line install (Linux/Mac/Windows):
  git clone https://github.com/Intersepter/terminal-rpg.git && cd terminal-rpg && pip install -r requirements.txt && python main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILES:
  main.py              - Game launcher, main menu, world loop
  game_world.py        - Procedural world map, WASD movement, continents
  game_systems.py      - Towns, shops, quests, dungeons, combat engine
  game_player.py       - Player class, leveling, inventory, quests, evolution
  game_jobs.py         - All 10 classes (5 base + 5 evolved)
  game_items.py        - Items, equipment, skills, status effects, loot, crafting
  game_enemies.py      - Enemy definitions, boss system, scaling
  game_party.py        - Party system, 20 companions, clan system
  game_dungeon.py      - Multi-floor dungeons with bosses and chests
  game_mining.py       - Mine locations and mining mini-game
  game_customise.py    - Character customisation, styles, legendary skins
  game_saves.py        - Multi-slot save system with autosave
  game_stories.py      - Story events and main quests
  game_base.py         - Player base building system
  game_trading.py      - Barter/trading system with merchants
  game_sell.py         - Fast item selling interface
  game_codex.py        - In-game encyclopedia and bestiary
  game_art.py          - ASCII combat sprites
  game_lang.py         - 20-language translation system
  game_term.py         - Terminal sizing and centred layout
  game_input.py        - Cross-platform raw keyboard input

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLASSES:
  Swordsman  ->  Blade Master
  Mage       ->  Archmage
  Rogue      ->  Shadow Assassin
  Tank       ->  War Titan
  Healer     ->  Arch Priest

CLASS EVOLUTION:
  1. Go to Quest Board in any town
  2. Choose "Start class awakening quest"
  3. Complete the quest objectives
  4. Turn in at Quest Board
  5. Go to Adventurers Guild -> "Awaken class"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHARACTER CUSTOMISATION (new):
  Available in every town via [C] Customise.
  Each class has 4 unique styles — each gives a different look
  and a real passive bonus (ATK, DEF, Stealth, Crit, MP, HP etc.)
  Switch any time in any town for free.

  LEGENDARY SKINS:
  Each class has a secret golden legendary skin locked behind
  a difficult 2-part quest. Complete it to unlock:
    - A golden skin with a powerful buff
    - A trophy for your base
    - Gold + EXP reward
  Start the quest via [C] Customise -> [Q] Start legendary quest.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAVE SYSTEM (new):
  5 manual save slots + 1 autosave slot (slot 0).
  Saves are stored in the saves/ folder.
  Autosave triggers every 30 steps automatically.

  From world map:  [P] Save  ->  pick a slot
  On quit:         Choose save slot, autosave, or quit without saving
  From main menu:  [2] Load Game  ->  pick any slot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORLD MAP CONTROLS:
  WASD / Arrow keys = Move
  E = Enter city / dungeon / mine / ruins
  F = Fast travel (costs gold by distance)
  P = Save game
  I = Inventory
  C = Encyclopedia / Codex
  J = Quest journal
  B = Base menu
  N = Party menu
  M = Show discovered locations
  ? = Help
  Q = Quit / save

TOWN MENU OPTIONS:
  1 = Inn (rest, heal, save)
  2 = Shop (buy & sell)
  3 = Quest Board
  4 = Adventurers Guild (rank up, awaken class, clan)
  5 = Talk to NPCs
  6 = Crafting bench
  7 = Character status
  8 = Inventory
  R = Recruit party members
  T = Trader (barter system)
  C = Customise character
  K = Encyclopedia
  H = Base menu
  S = Quick save

COMBAT OPTIONS:
  1 = Attack
  2 = Use Skill (costs MP)
  3 = Use Item
  4 = Defend (reduce incoming damage)
  5 = Run

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARTY SYSTEM:
  Recruit up to 3 companions across all 5 continents.
  20 total companions available — warriors, rogues, mages, healers.
  Companions fight alongside you in combat automatically.
  Healers auto-heal when your HP drops below 60%.

CLAN SYSTEM:
  Found a clan at the Adventurers Guild for 1000 gold.
  Upgrade your clan hall to earn passive daily gold income.
  Clan rank rises automatically: Bronze -> Silver -> ... -> Legend.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DUNGEONS:
  5 floors per dungeon — each floor harder than the last.
  Floor 3 and 5 have mini-bosses.
  Chests, traps, teleport pads and stairs on every floor.
  Use [E] to interact with stairs, exits and chests.

MINES:
  Scattered across the world map.
  Move through tunnels and mine ore nodes [O].
  Ore is used for crafting. Watch out for cave-ins and monsters.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOD POTION:
  You start with 1. Auto-activates when you hit 0 HP.
  Very hard to restock — rarely drops from Shadow Beasts and Dragons.
  Can also be traded for a Dragon Scale at certain merchants.
  Sells for 500 gold if desperate.

LANGUAGES:
  20 languages supported.
  Change at main menu via [L] Language.
  Supported: EN DE FR ES PT IT RU PL NL SV JA ZH KO AR TR CS HU RO FI NO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
