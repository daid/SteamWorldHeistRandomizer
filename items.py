from bundle import Bundle
import itertools
import collections
from typing import Optional, List


Item = collections.namedtuple("Item", ["name", "tier", "rtype"])


class Items:
    def __init__(self, bundle: Bundle):
        self.__items = []
        for item in itertools.chain(bundle.getNodes("Weapon"), bundle.getNodes("Utility")):
            rarity = item.subNode("Rarity")
            if rarity:
                self.__items.append(Item(item["Name"], int(rarity.attr("Tier")), rarity.attr("Type")))

    def find(self, name: str) -> Optional[Item]:
        for item in self.__items:
            if item[0] == name:
                return item
        return None

    def listAccordingToMathingConfig(self, item, config) -> List[Item]:
        result = []
        for i in self.__items:
            if config == "type":
                if i.tier != item.tier or i.rtype != item.rtype:
                    continue
            elif config == "tier":
                if i.tier != item.tier:
                    continue
            else:
                diff = int(config)
                if abs(i.tier - item.tier) > diff:
                    continue
            result.append(i)
        return result
