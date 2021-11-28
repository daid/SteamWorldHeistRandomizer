from bundle import Bundle
import random
import sys
import os
import argparse
from items import Items


def find_steam():
    if sys.platform == "win32":
        import winreg
        for keyname in (r"SOFTWARE\Valve\Steam", r"SOFTWARE\Wow6432Node\Valve\Steam"):
            try:
                with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, keyname) as key:
                    return winreg.QueryValueEx(key, "SteamPath")[0]
            except FileNotFoundError:
                pass
    # Check for linux install path
    if os.path.isdir(os.path.expanduser("~/.steam/root")):
        return os.path.expanduser("~/.steam/root")
    return None


def find_game():
    steam = find_steam()
    if not steam:
        return None
    path = os.path.normpath(os.path.join(steam, "steamapps/common/SteamWorld Heist"))
    if os.path.isdir(path):
        return path
    return None


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("install_path", nargs="?")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--stripquests", action="store_true")
    parser.add_argument("--charweapon", choices=["default", "basic", "wild"], default="default")
    parser.add_argument("--charlevelup", choices=["default", "basic", "wild"], default="default")
    parser.add_argument("--epicswag", choices=["default", "type", "tier", "1", "2"], default="default")
    parser.add_argument("--shop", choices=["default", "type", "tier", "1", "2"], default="default")
    parser.add_argument("--seed")
    conf = parser.parse_args(args)
    print(conf)

    if conf.install_path is None:
        conf.install_path = find_game()
    if conf.install_path is None:
        print("Install path not supplied and not found from search, cannot continue")
        exit(1)
    if conf.seed is None:
        conf.seed = "SEED"
    rnd = random.Random(conf.seed)

    game_path = find_game()
    bundle = Bundle(game_path)
    bundle.load("Bundle")
    has_dlc = bundle.load("DLC/dlc01")
    bundle.clean()
    if conf.clean:  # Our work is done, do nothing else.
        return

    CAST = ["piper", "sea_brass", "ivanski", "sally_bolt", "valentine", "beatrix", "dora", "payroll", "billy_gill"]
    if has_dlc:
        CAST += ["ghost"]
    WEAPON_PERKS = ["handgun", "marksman", "assault", "heavy"]
    WEAPON_PERK_SETS = [
        ("handgun",),
        ("handgun", "marksman"),
        ("handgun", "assault"),
        ("handgun", "heavy"),
    ]
    MAIN_PERKS = [
        ("damaging_shot", "damaging_shot_lower_cd", "damaging_shot_upgrade", "damaging_shot_upgrade_2"),
        ("leader", "area_heal", "leader_inc_area", "leader_upgrade"), # area_heal_more_uses
        ("soaker", "wrath_of_the_sea", "wrath_of_the_sea_02"),
        ("double_shot", "double_shot_reduced_cooldown"),
        ("abs_of_steel", "abs_of_steel_taunt", "abs_of_steel_more_uses"),
        ("killer", "mad_dog", "mad_dog_more_uses"),
        ("berserker", "berserker_upgraded"),
        ("camper", "camper_upgrade", "camper_upgrade_02"),
        ("piercing_shot", "piercing_shot_reduced_cooldown"),
        ("beatrix_launcher", "beatrix_launcher_uses", "beatrix_launcher_damage"),
        ("beatrix_explosion_resistance",),
        ("flanker", "flanker_crit", "backstabber", "back_breaker"),
        ("boot_boost", "boot_boost_reduced_cooldown"),
        ("run_n_gun", "run_n_gun_reduced_cooldown"),
        ("double_melee", "double_melee_reduced_cooldown"),
        ("mend", ),
        ("guts", ),
        ("war_cry",),
        ("soot_screen",),
        ("reduce_sway",),
        ("loose_gun",),
        ("sprint_after_kill",),
        ("dora_stun_gun",),
    ]
    if has_dlc:
        MAIN_PERKS += [("ghost_charge_beam", "ghost_charge_self_heal", "ghost_charge_beam_upgrade_1", "ghost_charge_self_heal_free", "ghost_charge_beam_upgrade_2", "ghost_charge_beam_upgrade_3", "ghost_charge_self_heal_upgrade")]
    FILLER_PERKS = ["health", "health2", "speed", "melee_damage", "melee_damage2"]
    ITEMS = Items(bundle)

    if conf.stripquests:
        # Remove all the quests, this generates a more streamlined experience without
        # too much story to get in the way of the action.
        for quest in bundle.getNodes("Quest"):
            # tutorial_start is needed or else the game crashes on startup
            if quest["Name"] not in {"MAIN", "tutorial_start"}:
                quest.delete()

        # Remove all the conversations before/after missions, to speed up the game.
        for encounter in bundle.getNodes("Encounter"):
            del encounter["StartConversation"]
            del encounter["EndConversation"]
    for cast in CAST:
        starting = bundle.getNode("Persona", cast).subNode("LevelCategories").subNode("Levels", Type="starting")
        for level in starting:
            if level.attr("Perk") in WEAPON_PERKS and conf.charweapon != "default":
                level.delete()
            elif conf.charlevelup != "default":
                level.delete()
        if conf.charweapon == "basic":  # basic weapon, select one of the random weapon sets.
            for weapon in rnd.choice(WEAPON_PERK_SETS):
                starting.newChild("Level").attr("Perk", weapon)
        elif conf.charweapon == "wild":  # wild weapons, select to give one or two weapon types at random
            perks = WEAPON_PERKS.copy()
            rnd.shuffle(perks)
            for perk in perks[:1 if rnd.random() < 0.25 else 2]:
                starting.newChild("Level").attr("Perk", perk)

        if conf.charlevelup == "basic":
            upgrade_perks = [None] * 10
            done_perks = set()
            while len([p for p in upgrade_perks if p is not None]) < 5:
                perk = rnd.choice(MAIN_PERKS)
                if perk in done_perks:
                    continue
                done_perks.add(perk)
                index_list = [n for n in range(10)]
                rnd.shuffle(index_list)
                index_list = index_list[:len(perk)]
                index_list.sort()
                skip = False
                for idx in index_list:
                    if upgrade_perks[idx] is not None:
                        skip = True
                if skip:
                    continue
                for idx, p in zip(index_list, perk):
                    upgrade_perks[idx] = p
            upgrade_perks = [perk if perk is not None else rnd.choice(FILLER_PERKS) for perk in upgrade_perks]
            upgrades = bundle.getNode("Persona", cast).subNode("LevelCategories").subNode("Levels", Type="upgrades")
            for upgrade in upgrades:
                upgrade.delete()
            for perk in upgrade_perks:
                upgrades.newChild("Level").attr("Perk", perk)

        if conf.charlevelup == "wild":
            upgrade_perks = []
            while len(upgrade_perks) < 10:
                perk = rnd.choice(MAIN_PERKS + [(f,) for f in FILLER_PERKS])
                n = 0
                while n < len(perk) and perk[n] in upgrade_perks:
                    n += 1
                if n < len(perk):
                    upgrade_perks.append(perk[n])
            upgrades = bundle.getNode("Persona", cast).subNode("LevelCategories").subNode("Levels", Type="upgrades")
            for upgrade in upgrades:
                upgrade.delete()
            for perk in upgrade_perks:
                upgrades.newChild("Level").attr("Perk", perk)

    for encounter in bundle.getNodes("Encounter"):
        master_loot = encounter.subNode("MasterLoot")
        if master_loot:
            node = encounter
            while node is not None and node["MissionType"] is None:
                node = bundle.getNode("Encounter", node["Template"])
            if node is None:  # DLC overrides existing shops so we need to get the template from the original shop.
                node = bundle.getNode("Encounter", encounter["Name"])
                while node is not None and node["MissionType"] is None:
                    node = bundle.getNode("Encounter", node["Template"])

            if node["MissionType"] == "heist" and conf.epicswag != "default":  # Mission type is "heist" or "bar", "heist" for battles, "bar" for shops.
                for child in master_loot:
                    item = ITEMS.find(child.text)
                    if item:
                        child.text = rnd.choice(ITEMS.listAccordingToMathingConfig(item, conf.epicswag)).name

            if node["MissionType"] == "bar" and conf.shop != "default":  # Mission type is "heist" or "bar", "heist" for battles, "bar" for shops.
                for child in master_loot:
                    item = ITEMS.find(child.text)
                    if item:
                        child.text = rnd.choice(ITEMS.listAccordingToMathingConfig(item, conf.shop)).name


    bundle.getCSV("Language/en.csv.z").set("menu_extras", "SEED: %s" % (conf.seed))
    bundle.save()


if __name__ == '__main__':
    main(sys.argv[1:])
