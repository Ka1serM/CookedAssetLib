import unreal

from common import editor_assets, editor_level, load

SUB_LEVEL = "/Game/Lib/Map/SubLevel"


def spawn(asset, x, y=0, z=50):
    return editor_level.spawn_actor_from_object(asset, unreal.Vector(x, y, z))


def generate():
    editor_level.new_level(SUB_LEVEL)
    spawn(load("StaticMesh", "SM_Sphere"), 0)
    editor_level.save_current_level()

    editor_level.new_level("/Game/Lib/Map/TestMap")
    spawn(load("StaticMesh", "SM_Cube"), 0)
    spawn(load("StaticMesh", "SM_Sphere"), 300)
    spawn(load("StaticMesh", "SM_DenseSphere"), 600)
    spawn(load("StaticMesh", "SM_Lods"), 900)
    spawn(load("StaticMesh", "SM_Plane"), 0, 0, 0)
    spawn(load("SkeletalMesh", "SK_Tower"), -300, 0, 0)
    spawn(load("Blueprint", "BP_Actor"), -600)
    editor_level.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500))
    editor_level.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
    editor_level.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
    editor_level.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
    editor_level.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0)).set_editor_property("unbound", True)
    decal = editor_level.spawn_actor_from_class(unreal.DecalActor, unreal.Vector(0, 0, 100), unreal.Rotator(0, -90, 0))
    decal.set_decal_material(load("Material", "M_Decal"))
    unreal.EditorLevelUtils.add_level_to_world(editor_level.get_editor_world(), SUB_LEVEL, unreal.LevelStreamingDynamic)
    editor_level.save_all_dirty_levels()
