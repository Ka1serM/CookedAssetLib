import unreal

from common import create_asset, load, material_editing

domain = unreal.MaterialDomain
blend = unreal.BlendMode
shading = unreal.MaterialShadingModel


def new_material(name, **properties):
    material = create_asset("Material", name, unreal.Material, unreal.MaterialFactoryNew())
    for key, value in properties.items():
        material.set_editor_property(key, value)
    return material


def node(owner, expression_class, x=-400, y=0, **properties):
    expression = material_editing.create_material_expression(owner, expression_class, x, y)
    for key, value in properties.items():
        expression.set_editor_property(key, value)
    return expression


def color(owner, rgb, x=-400, y=0):
    return node(owner, unreal.MaterialExpressionConstant3Vector, x, y, constant=unreal.LinearColor(*rgb, 1))


def scalar(owner, value, x=-400, y=0):
    return node(owner, unreal.MaterialExpressionConstant, x, y, r=value)


def finish(material, **connections):
    for property_name, expression in connections.items():
        material_editing.connect_material_property(expression, "", getattr(unreal.MaterialProperty, property_name))
    material_editing.recompile_material(material)


def textured(material, texture_name, x=-700, y=0, parameter=None):
    texture = load("Texture", texture_name)
    if parameter:
        return node(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=parameter, texture=texture)
    return node(material, unreal.MaterialExpressionTextureSample, x, y, texture=texture)


def connect_output(expression, output, material, property_name):
    material_editing.connect_material_property(expression, output, getattr(unreal.MaterialProperty, property_name))


def generate():
    material = new_material("M_Opaque")
    finish(material, MP_BASE_COLOR=color(material, (0.8, 0.2, 0.1)), MP_ROUGHNESS=scalar(material, 0.4), MP_METALLIC=scalar(material, 0.0))

    material = new_material("M_Checker")
    connect_output(textured(material, "T_Checker"), "RGB", material, "MP_BASE_COLOR")
    material_editing.recompile_material(material)

    material = new_material("M_CheckerVirtual")
    connect_output(textured(material, "T_CheckerVirtual"), "RGB", material, "MP_BASE_COLOR")
    material_editing.recompile_material(material)

    material = new_material("M_Tiled")
    coordinates = node(material, unreal.MaterialExpressionTextureCoordinate, -900, 0, u_tiling=4.0, v_tiling=4.0)
    sample = textured(material, "T_Checker")
    material_editing.connect_material_expressions(coordinates, "", sample, "UVs")
    connect_output(sample, "RGB", material, "MP_BASE_COLOR")
    material_editing.recompile_material(material)

    material = new_material("M_Masked", blend_mode=blend.BLEND_MASKED)
    sample = textured(material, "T_Checker")
    connect_output(sample, "RGB", material, "MP_BASE_COLOR")
    connect_output(sample, "A", material, "MP_OPACITY_MASK")
    material_editing.recompile_material(material)

    material = new_material("M_Translucent", blend_mode=blend.BLEND_TRANSLUCENT)
    finish(material, MP_BASE_COLOR=color(material, (0.2, 0.5, 1.0)), MP_OPACITY=scalar(material, 0.5))

    material = new_material("M_Additive", blend_mode=blend.BLEND_ADDITIVE, shading_model=shading.MSM_UNLIT)
    finish(material, MP_EMISSIVE_COLOR=color(material, (1.0, 0.6, 0.1)))

    material = new_material("M_Unlit", shading_model=shading.MSM_UNLIT)
    finish(material, MP_EMISSIVE_COLOR=color(material, (0.1, 1.0, 0.3)))

    material = new_material("M_TwoSidedFoliage", two_sided=True, shading_model=shading.MSM_TWO_SIDED_FOLIAGE)
    finish(material, MP_BASE_COLOR=color(material, (0.1, 0.5, 0.1)), MP_SUBSURFACE_COLOR=color(material, (0.6, 0.9, 0.2), y=200))

    material = new_material("M_Subsurface", shading_model=shading.MSM_SUBSURFACE)
    finish(material, MP_BASE_COLOR=color(material, (0.9, 0.7, 0.6)), MP_SUBSURFACE_COLOR=color(material, (1.0, 0.2, 0.1), y=200))

    material = new_material("M_ClearCoat", shading_model=shading.MSM_CLEAR_COAT)
    finish(material, MP_BASE_COLOR=color(material, (0.5, 0.0, 0.0)))

    material = new_material("M_NormalMapped")
    connect_output(textured(material, "T_Normal"), "RGB", material, "MP_NORMAL")
    finish(material, MP_BASE_COLOR=color(material, (0.5, 0.5, 0.5)))

    material = new_material("M_PackedMask")
    sample = textured(material, "T_Mask")
    connect_output(sample, "R", material, "MP_ROUGHNESS")
    connect_output(sample, "G", material, "MP_METALLIC")
    connect_output(sample, "B", material, "MP_AMBIENT_OCCLUSION")
    material_editing.recompile_material(material)

    material = new_material("M_VertexColor")
    connect_output(node(material, unreal.MaterialExpressionVertexColor), "RGB", material, "MP_BASE_COLOR")
    material_editing.recompile_material(material)

    material = new_material("M_AnimatedEmissive", shading_model=shading.MSM_UNLIT)
    wave = node(material, unreal.MaterialExpressionSine, -600, 200)
    material_editing.connect_material_expressions(node(material, unreal.MaterialExpressionTime, -800, 200), "", wave, "")
    scaled = node(material, unreal.MaterialExpressionMultiply, -300, 200)
    material_editing.connect_material_expressions(wave, "", scaled, "A")
    material_editing.connect_material_expressions(color(material, (0.2, 0.4, 1.0), -600, 400), "", scaled, "B")
    finish(material, MP_EMISSIVE_COLOR=scaled)

    material = new_material("M_CustomHlsl")
    custom = node(material, unreal.MaterialExpressionCustom, -400, 0, code="return 0.25 + 0.5 * frac(Parameters.AbsoluteWorldPosition.x * 0.01);", output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    finish(material, MP_BASE_COLOR=color(material, (0.7, 0.7, 0.7)), MP_ROUGHNESS=custom)

    material = new_material("M_Fresnel", shading_model=shading.MSM_UNLIT)
    connect_output(node(material, unreal.MaterialExpressionFresnel), "", material, "MP_EMISSIVE_COLOR")
    material_editing.recompile_material(material)

    material = new_material("M_Decal", material_domain=domain.MD_DEFERRED_DECAL, blend_mode=blend.BLEND_TRANSLUCENT)
    finish(material, MP_BASE_COLOR=color(material, (1, 0, 0)), MP_OPACITY=scalar(material, 0.8))

    material = new_material("M_PostProcess", material_domain=domain.MD_POST_PROCESS)
    finish(material, MP_EMISSIVE_COLOR=color(material, (0.1, 0.1, 0.4)))

    material = new_material("M_UserInterface", material_domain=domain.MD_UI)
    finish(material, MP_EMISSIVE_COLOR=color(material, (1, 1, 0)))

    material = new_material("M_Parameters")
    roughness = node(material, unreal.MaterialExpressionScalarParameter, -400, 100, parameter_name="Roughness", default_value=0.5)
    tint = node(material, unreal.MaterialExpressionVectorParameter, -400, 0, parameter_name="Tint", default_value=unreal.LinearColor(1, 0.5, 0, 1))
    finish(material, MP_BASE_COLOR=tint, MP_ROUGHNESS=roughness)
    instance = create_asset("Material", "MI_Parameters", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", material)
    material_editing.set_material_instance_scalar_parameter_value(instance, "Roughness", 0.9)
    material_editing.set_material_instance_vector_parameter_value(instance, "Tint", unreal.LinearColor(0, 0.5, 1, 1))

    material = new_material("M_TextureParameter")
    connect_output(textured(material, "T_Checker", parameter="BaseTexture"), "RGB", material, "MP_BASE_COLOR")
    material_editing.recompile_material(material)
    instance = create_asset("Material", "MI_TextureParameter", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", material)
    material_editing.set_material_instance_texture_parameter_value(instance, "BaseTexture", load("Texture", "T_Targa"))

    function = create_asset("Material", "MF_Gradient", unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    function_input = material_editing.create_material_expression_in_function(function, unreal.MaterialExpressionFunctionInput, -600, 0)
    function_input.set_editor_property("input_name", "Value")
    function_output = material_editing.create_material_expression_in_function(function, unreal.MaterialExpressionFunctionOutput, 0, 0)
    function_output.set_editor_property("output_name", "Result")
    ramp = material_editing.create_material_expression_in_function(function, unreal.MaterialExpressionSaturate, -300, 0)
    material_editing.connect_material_expressions(function_input, "", ramp, "")
    material_editing.connect_material_expressions(ramp, "", function_output, "")
    material = new_material("M_UsesFunction")
    call = node(material, unreal.MaterialExpressionMaterialFunctionCall, -400, 0, material_function=function)
    finish(material, MP_BASE_COLOR=call)

    collection = create_asset("Material", "MPC_Parameters", unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    wetness = unreal.CollectionScalarParameter()
    wetness.set_editor_properties({"parameter_name": "Wetness", "default_value": 0.5})
    collection.set_editor_property("scalar_parameters", [wetness])
    material = new_material("M_UsesCollection")
    reference = node(material, unreal.MaterialExpressionCollectionParameter, -400, 0, collection=collection, parameter_name="Wetness")
    finish(material, MP_ROUGHNESS=reference)
