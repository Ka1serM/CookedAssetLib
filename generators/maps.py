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


def generate():
    editor_level.new_level(SUB_LEVEL)
    editor_level.spawn_actor_from_object(load("StaticMesh", "SM_Sphere"), unreal.Vector(0, 0, 50))
    editor_level.save_current_level()

    editor_level.new_level(f"{ROOT}/Map/Showcase")
    placers = (("StaticMesh", place_meshes), ("Material", place_materials), ("Texture", place_textures), ("SkeletalMesh", place_skeletal),
               ("Blueprint", place_blueprints), ("Audio", place_audio), ("Environment", place_environment))
    for index, (label, place) in enumerate(placers):
        place(Row(label, index))
    unreal.EditorLevelUtils.add_level_to_world(editor_level.get_editor_world(), SUB_LEVEL, unreal.LevelStreamingDynamic)
    editor_level.save_all_dirty_levels()
