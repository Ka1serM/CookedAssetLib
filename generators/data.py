import unreal

from common import create_asset


def generate():
    create_asset("Data", "CF_Ramp", unreal.CurveFloat, unreal.CurveFloatFactory())
    create_asset("Data", "CV_Vector", unreal.CurveVector, unreal.CurveVectorFactory())
    create_asset("Data", "CL_Gradient", unreal.CurveLinearColor, unreal.CurveLinearColorFactory())
    create_asset("Data", "PM_Rubber", unreal.PhysicalMaterial, unreal.PhysicalMaterialFactoryNew()).set_editor_properties({"friction": 1.2, "restitution": 0.8})
    create_asset("Data", "LS_Sequence", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    create_asset("Data", "Struct_Item", unreal.UserDefinedStruct, unreal.StructureFactory())
