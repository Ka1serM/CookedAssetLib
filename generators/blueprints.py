import unreal

from common import create_asset


def generate():
    for name, parent in (("BP_Actor", unreal.Actor), ("BP_Pawn", unreal.Pawn), ("BP_Character", unreal.Character), ("BP_GameMode", unreal.GameModeBase), ("BP_Controller", unreal.PlayerController)):
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent)
        create_asset("Blueprint", name, unreal.Blueprint, factory)
