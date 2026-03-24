from game_items import Skill, Poison, Burn, Regen

# =============================================================
# JOB BASE
# =============================================================

class Job:
    def __init__(self, name, hp_bonus, atk_bonus, mp_bonus,
                 crit_bonus=0, dodge_bonus=0, skill_power_bonus=0,
                 heal_power_bonus=0, defend_bonus=0, skills=None,
                 evolution=None, evolution_quest=None, stealth_bonus=0):
        self.name              = name
        self.hp_bonus          = hp_bonus
        self.atk_bonus         = atk_bonus
        self.mp_bonus          = mp_bonus
        self.crit_bonus        = crit_bonus
        self.dodge_bonus       = dodge_bonus
        self.skill_power_bonus = skill_power_bonus
        self.heal_power_bonus  = heal_power_bonus
        self.defend_bonus      = defend_bonus
        self.stealth_bonus     = stealth_bonus    # added to player stealth stat
        self.skills            = skills or []
        self.evolution         = evolution
        self.evolution_quest   = evolution_quest

    def description(self):
        return f"{self.name} | HP+{self.hp_bonus} ATK+{self.atk_bonus} MP+{self.mp_bonus}"


# =============================================================
# BASE CLASSES
# =============================================================

class Swordsman(Job):
    def __init__(self):
        super().__init__(
            "Swordsman", hp_bonus=30, atk_bonus=5, mp_bonus=10,
            crit_bonus=10, dodge_bonus=4, skill_power_bonus=2,
            defend_bonus=6, stealth_bonus=0,
            skills=[
                Skill("Power Slash", damage=10, mana_cost=5,
                      description="A powerful sword strike."),
                Skill("Guard Break", damage=14, mana_cost=8,
                      description="Breaks through defenses."),
                Skill("Battle Cry",  damage=0, heal=0, mana_cost=3,
                      status_effect=Regen(duration=3, heal=5),
                      status_chance=100, description="Pumps up your spirit, starts regen."),
            ],
            evolution="Blade Master",
            evolution_quest="quest_swordsman_awakening",
        )


class Mage(Job):
    def __init__(self):
        super().__init__(
            "Mage", hp_bonus=0, atk_bonus=12, mp_bonus=40,
            crit_bonus=6, dodge_bonus=6, skill_power_bonus=10, stealth_bonus=3,
            skills=[
                Skill("Fireball",    damage=16, mana_cost=10,
                      status_effect=Burn(duration=2, damage=5),
                      status_chance=35, description="Deals fire damage, chance to Burn."),
                Skill("Ice Spike",   damage=14, mana_cost=9,
                      status_effect=Poison(duration=2, damage=4),
                      status_chance=25, description="Cold spike, chance to Chill/Slow."),
                Skill("Arcane Blast",damage=22, mana_cost=16,
                      description="Pure arcane explosion."),
            ],
            evolution="Archmage",
            evolution_quest="quest_mage_awakening",
        )


class Rogue(Job):
    def __init__(self):
        super().__init__(
            "Rogue", hp_bonus=10, atk_bonus=8, mp_bonus=15,
            crit_bonus=20, dodge_bonus=18, skill_power_bonus=4,
            defend_bonus=3, stealth_bonus=8,
            skills=[
                Skill("Backstab",    damage=16, mana_cost=7,
                      description="High crit chance attack from the shadows."),
                Skill("Quick Strike", damage=11, mana_cost=5,
                      description="Fast twin hit."),
                Skill("Venom Blade", damage=10, mana_cost=8,
                      status_effect=Poison(duration=3, damage=6),
                      status_chance=70, description="Poisons the target."),
            ],
            evolution="Shadow Assassin",
            evolution_quest="quest_rogue_awakening",
        )


class Tank(Job):
    def __init__(self):
        super().__init__(
            "Tank", hp_bonus=70, atk_bonus=2, mp_bonus=5,
            crit_bonus=3, dodge_bonus=2, skill_power_bonus=1,
            defend_bonus=25, stealth_bonus=-3,
            skills=[
                Skill("Shield Bash", damage=12, mana_cost=4,
                      description="Bash with shield, may stun."),
                Skill("Iron Slam",   damage=15, mana_cost=7,
                      description="Massive overhead slam."),
                Skill("Taunt",       damage=0, heal=0, mana_cost=3,
                      status_effect=Regen(duration=2, heal=8),
                      status_chance=100, description="Taunts enemies, triggers regen."),
            ],
            evolution="War Titan",
            evolution_quest="quest_tank_awakening",
        )


class Healer(Job):
    def __init__(self):
        super().__init__(
            "Healer", hp_bonus=20, atk_bonus=4, mp_bonus=35,
            crit_bonus=4, dodge_bonus=8, heal_power_bonus=12,
            defend_bonus=5, stealth_bonus=2,
            skills=[
                Skill("Holy Light",  damage=0, heal=25, mana_cost=8,
                      description="Heals yourself with holy energy."),
                Skill("Smite",       damage=12, mana_cost=7,
                      description="Holy damage strike."),
                Skill("Mend",        damage=0, heal=15, mana_cost=5,
                      status_effect=Regen(duration=3, heal=7),
                      status_chance=100, description="Heals and starts regen."),
            ],
            evolution="Arch Priest",
            evolution_quest="quest_healer_awakening",
        )


# =============================================================
# EVOLVED / AWAKENED CLASSES
# =============================================================

class BladeMaster(Job):
    def __init__(self):
        super().__init__(
            "Blade Master", hp_bonus=55, atk_bonus=16, mp_bonus=20,
            crit_bonus=16, dodge_bonus=10, skill_power_bonus=8,
            defend_bonus=10, stealth_bonus=1,
            skills=[
                Skill("Cyclone Slash", damage=26, mana_cost=14,
                      description="Spinning blade hits all."),
                Skill("Sword Aura",    damage=32, mana_cost=20,
                      description="Release sword energy in a burst."),
                Skill("Dragon Slash",  damage=42, mana_cost=28,
                      status_effect=Burn(duration=2, damage=8),
                      status_chance=40, description="Legendary technique. Burns target."),
            ],
        )


class Archmage(Job):
    def __init__(self):
        super().__init__(
            "Archmage", hp_bonus=10, atk_bonus=20, mp_bonus=75,
            crit_bonus=10, dodge_bonus=10, skill_power_bonus=20, stealth_bonus=4,
            skills=[
                Skill("Meteor Burst",  damage=34, mana_cost=22,
                      status_effect=Burn(duration=3, damage=6), status_chance=50,
                      description="Rains meteors. Burns target."),
                Skill("Mana Storm",    damage=45, mana_cost=30,
                      description="Unleash pure mana destruction."),
                Skill("Time Freeze",   damage=18, mana_cost=18,
                      status_effect=Poison(duration=4, damage=8), status_chance=60,
                      description="Slows time, poisons the enemy."),
            ],
        )


class ShadowAssassin(Job):
    def __init__(self):
        super().__init__(
            "Shadow Assassin", hp_bonus=25, atk_bonus=22, mp_bonus=28,
            crit_bonus=30, dodge_bonus=25, skill_power_bonus=10,
            defend_bonus=5, stealth_bonus=12,
            skills=[
                Skill("Phantom Strike", damage=30, mana_cost=16,
                      description="Strike from the void."),
                Skill("Nightfall",      damage=38, mana_cost=24,
                      status_effect=Poison(duration=3, damage=8), status_chance=55,
                      description="Cover the world in darkness."),
                Skill("Shadow Realm",   damage=50, mana_cost=35,
                      description="Drag enemy into shadow dimension."),
            ],
        )


class WarTitan(Job):
    def __init__(self):
        super().__init__(
            "War Titan", hp_bonus=130, atk_bonus=8, mp_bonus=10,
            crit_bonus=8, dodge_bonus=5, skill_power_bonus=5,
            defend_bonus=40, heal_power_bonus=5, stealth_bonus=-4,
            skills=[
                Skill("Titan Crush",    damage=20, mana_cost=8,
                      description="Devastating ground slam."),
                Skill("Fortress Wall",  damage=0,  heal=20, mana_cost=10,
                      status_effect=Regen(duration=4, heal=12),
                      status_chance=100, description="Heal and regen — become a fortress."),
                Skill("Rage Quake",     damage=35, mana_cost=22,
                      description="Earth-shaking war cry strike."),
            ],
        )


class ArchPriest(Job):
    def __init__(self):
        super().__init__(
            "Arch Priest", hp_bonus=35, atk_bonus=6, mp_bonus=65,
            crit_bonus=8, dodge_bonus=12, heal_power_bonus=25,
            defend_bonus=8, stealth_bonus=3,
            skills=[
                Skill("Divine Heal",    damage=0, heal=45, mana_cost=15,
                      description="Massive holy restoration."),
                Skill("Holy Nova",      damage=25, mana_cost=14,
                      description="Burst of holy light."),
                Skill("Resurrection",   damage=0, heal=60, mana_cost=25,
                      status_effect=Regen(duration=5, heal=10),
                      status_chance=100, description="The ultimate heal. Triggers long regen."),
            ],
        )


# =============================================================
# JOB REGISTRY
# =============================================================

JOB_CLASSES = {
    "Swordsman":       Swordsman,
    "Mage":            Mage,
    "Rogue":           Rogue,
    "Tank":            Tank,
    "Healer":          Healer,
    "Blade Master":    BladeMaster,
    "Archmage":        Archmage,
    "Shadow Assassin": ShadowAssassin,
    "War Titan":       WarTitan,
    "Arch Priest":     ArchPriest,
}

STARTER_JOBS = ["Swordsman", "Mage", "Rogue", "Tank", "Healer"]

def create_job(name):
    cls = JOB_CLASSES.get(name)
    if cls:
        return cls()
    raise ValueError(f"Unknown job: {name}")
