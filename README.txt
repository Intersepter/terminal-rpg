=== ANIME DUNGEON CHRONICLES ===

HOW TO RUN:
  python main.py

FILES:
  main.py         - Game launcher / main menu / new game / load game
  world_map.py    - Procedural world map, WASD movement, regions
  rpg_systems.py  - Towns, shops, quests, dungeons, combat engine
  player.py       - Player class, leveling, inventory, quests, evolution
  jobs.py         - All 10 classes (5 base + 5 evolved)
  items.py        - Items, equipment, skills, status effects, loot tables, crafting

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

WORLD MAP CONTROLS:
  WASD = Move   E = Enter city/dungeon/ruins
  F = Fast travel (costs gold by distance)
  M = Show discovered locations   ? = Help   Q = Quit/save

COMBAT OPTIONS:
  1. Attack   2. Use Skill   3. Use Item   4. Defend   5. Run

GOD POTION:
  You start with 1. Auto-activates when you hit 0 HP.
  Very hard to restock — rarely drops from Shadow Beasts and Dragons.
  Sells for 500 gold if desperate.

SAVE / LOAD:
  Save from world map (Q), from any town menu (option 0),
  or inside the Adventurers Guild.
