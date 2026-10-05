"""Loads /Game/Lib/Map/Showcase and logs actor counts per class and instance counts per instanced component. Runs inside the editor."""
import collections

import unreal

unreal.EditorLevelLibrary.load_level("/Game/Lib/Map/Showcase")
counts = collections.Counter()
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    counts[actor.get_class().get_name()] += 1
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        unreal.log(f"VALIDATE {actor.get_name()} {component.get_class().get_name()} instances={component.get_instance_count()}")
for name, count in sorted(counts.items()):
    unreal.log(f"VALIDATE actors {name}: {count}")
