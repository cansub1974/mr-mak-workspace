import unreal, json
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); assert w
s = next(x for x in unreal.ObjectIterator(unreal.WhispersLifeSubsystem) if x.get_outer() == w)
read = json.loads(s.development("read", "npc.meredith", {}))
keep = {k: v for k, v in read.items() if k not in ("needs", "personality", "roster")}
a = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith"), None)
b = a.get_component_by_class(unreal.WhispersBodyComponent) if a else None
keep["body_full"] = b.get_activity_readback() if b else None
mv = a.get_component_by_class(unreal.CharacterMovementComponent) if a else None
keep["movement"] = {"mode": str(mv.movement_mode), "vel": a.get_velocity().length()} if mv else None
print("FULL", json.dumps(keep, default=str)[:6000])
