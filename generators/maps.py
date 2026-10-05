import unreal

from common import ROOT, create_asset, editor_assets, editor_level, find_asset, load, material_editing

SUB_LEVEL = "/Game/Lib/Map/SubLevel"
SPACING = 200
ROW_SPACING = 400


class Row:
    def __init__(self, label, index):
        self.y = index * ROW_SPACING
        self.count = 0
        text = editor_level.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-SPACING, self.y, 150), unreal.Rotator(0, 180, 0))
        text.text_render.set_text(label)

    def next_location(self, z=50):
        location = unreal.Vector(self.count * SPACING, self.y, z)
        self.count += 1
        return location


def assets_in(folder, asset_class):
    paths = editor_assets.list_assets(f"{ROOT}/{folder}")
    return [asset for asset in map(unreal.load_asset, paths) if isinstance(asset, asset_class)]


def texture_material(texture):
    name = f"MT_{texture.get_name()}"
    material = create_asset("Material", name, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    is_cube = isinstance(texture, unreal.TextureCube)
    sample = material_editing.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameterCube if is_cube else unreal.MaterialExpressionTextureSample, -400, 0)
    sample.set_editor_property("texture", texture)
    if is_cube:
        sample.set_editor_property("parameter_name", "Cube")
    material_editing.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    material_editing.recompile_material(material)
    return material


def spawn_mesh(row, mesh, material=None, scale=1.0):
    actor = editor_level.spawn_actor_from_object(mesh, row.next_location())
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if material:
        actor.static_mesh_component.set_material(0, material)
    return actor


def place_meshes(row):
    for mesh in assets_in("StaticMesh", unreal.StaticMesh):
        spawn_mesh(row, mesh)


def place_materials(row):
    sphere = load("StaticMesh", "SM_Sphere")
    surface = unreal.MaterialDomain.MD_SURFACE
    for material in assets_in("Material", unreal.MaterialInterface):
        base = material.get_base_material() if isinstance(material, unreal.MaterialInstance) else material
        domain = base.get_editor_property("material_domain")
        if domain == surface:
            spawn_mesh(row, sphere, material)
        elif domain == unreal.MaterialDomain.MD_DEFERRED_DECAL:
            decal = editor_level.spawn_actor_from_class(unreal.DecalActor, row.next_location(100), unreal.Rotator(0, -90, 0))
            decal.set_decal_material(material)


def place_textures(row):
    plane = load("StaticMesh", "SM_Plane")
    for texture in assets_in("Texture", unreal.Texture):
        if isinstance(texture, unreal.TextureRenderTarget2D):
            continue
        actor = spawn_mesh(row, plane, texture_material(texture), 0.4)
        actor.set_actor_rotation(unreal.Rotator(90, 0, 0), False)


def place_skeletal(row):
    mesh = find_asset("SkeletalMesh", unreal.SkeletalMesh)
    animation = find_asset("SkeletalMesh", unreal.AnimSequence)
    actor = editor_level.spawn_actor_from_object(mesh, row.next_location(0))
    component = actor.skeletal_mesh_component
    component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    component.set_animation(animation)


def place_blueprints(row):
    for blueprint in assets_in("Blueprint", unreal.Blueprint):
        editor_level.spawn_actor_from_object(blueprint, row.next_location())


def place_audio(row):
    for wave in assets_in("Audio", unreal.SoundWave):
        actor = editor_level.spawn_actor_from_class(unreal.AmbientSound, row.next_location())
        actor.get_editor_property("audio_component").set_editor_property("sound", wave)


def place_environment(row):
    for actor_class in (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.ExponentialHeightFog, unreal.PointLight, unreal.SpotLight, unreal.RectLight, unreal.SphereReflectionCapture):
        editor_level.spawn_actor_from_class(actor_class, row.next_location(300))
    editor_level.spawn_actor_from_class(unreal.PostProcessVolume, row.next_location()).set_editor_property("unbound", True)


def grid_transforms(count, spacing, scale_step=0.0):
    return [unreal.Transform(unreal.Vector(x * spacing, y * spacing, 0), unreal.Rotator(0, (x * 17 + y * 31) % 360, 0),
                             unreal.Vector(*[1 + scale_step * ((x + y) % 3)] * 3))
            for x in range(count) for y in range(count)]


def instanced_actor(component_class, mesh, transforms, location):
    actor = editor_level.spawn_actor_from_class(unreal.Actor, location)
    component = unreal.new_object(component_class, actor, component_class.__name__)
    component.set_static_mesh(mesh)
    for transform in transforms:
        component.add_instance(transform)
    actor.set_editor_property("root_component", component)
    actor.set_actor_location(location, False, False)
    return actor


def place_instancing(row):
    start = row.next_location(0)
    instanced_actor(unreal.InstancedStaticMeshComponent, load("StaticMesh", "SM_Cube"), grid_transforms(5, 120), start)
    row.count += 3
    instanced_actor(unreal.HierarchicalInstancedStaticMeshComponent, load("StaticMesh", "SM_Sphere"), grid_transforms(8, 110, 0.25), row.next_location(0))
    row.count += 4
    foliage_location = row.next_location(0)
    sphere = load("StaticMesh", "SM_Sphere")
    transforms = grid_transforms(6, 120, 0.2)
    if hasattr(unreal.InstancedFoliageActor, "add_instances"):
        foliage_type = create_asset("Foliage", "FT_Sphere", unreal.FoliageType_InstancedStaticMesh, unreal.FoliageType_InstancedStaticMeshFactory())
        foliage_type.set_editor_property("mesh", sphere)
        offset = foliage_location
        unreal.InstancedFoliageActor.add_instances(editor_level.get_editor_world(), foliage_type, [
            unreal.Transform(t.translation + offset, t.rotation.rotator(), t.scale3d) for t in transforms])
    else:
        instanced_actor(unreal.FoliageInstancedStaticMeshComponent, sphere, transforms, foliage_location)


def generate():
    editor_level.new_level(SUB_LEVEL)
    editor_level.spawn_actor_from_object(load("StaticMesh", "SM_Sphere"), unreal.Vector(0, 0, 50))
    editor_level.save_current_level()

    editor_level.new_level(f"{ROOT}/Map/Showcase")
    placers = (("StaticMesh", place_meshes), ("Material", place_materials), ("Texture", place_textures), ("SkeletalMesh", place_skeletal),
               ("Blueprint", place_blueprints), ("Audio", place_audio), ("Instancing", place_instancing), ("Environment", place_environment))
    for index, (label, place) in enumerate(placers):
        place(Row(label, index))
    unreal.EditorLevelUtils.add_level_to_world(editor_level.get_editor_world(), SUB_LEVEL, unreal.LevelStreamingDynamic)
    editor_level.save_all_dirty_levels()
