extends Node3D

var camera: Camera3D
var elapsed := 0.0
var prisms: Array[Node3D] = []
var lenses: Array[Node3D] = []
var orbs: Array[Node3D] = []
var performer_parts: Array[Node3D] = []
var base_rotation := {}
var base_position := {}
var rgb_lights: Array[OmniLight3D] = []
var warm_spots: Array[SpotLight3D] = []

func _ready() -> void:
    _collect_nodes(self)
    _apply_runtime_materials(self)
    _build_environment()
    _build_lights()
    _build_camera()
    print("HAL_CATHEDRAL_NATIVE_READY meshes=", _count_meshes(self), " prisms=", prisms.size(), " lenses=", lenses.size(), " orbs=", orbs.size())

func _collect_nodes(node: Node) -> void:
    if node is Node3D:
        var n := node as Node3D
        var lower := String(n.name).to_lower()
        if lower.begins_with("prismcrystal_"):
            prisms.append(n)
        elif lower.begins_with("lensring_") or lower.begins_with("lensglass_"):
            lenses.append(n)
        elif lower.begins_with("orb_"):
            orbs.append(n)
        elif lower.begins_with("performer"):
            performer_parts.append(n)
        if lower.begins_with("prismcrystal_") or lower.begins_with("lensring_") or lower.begins_with("lensglass_") or lower.begins_with("orb_") or lower.begins_with("performer"):
            base_rotation[n] = n.rotation
            base_position[n] = n.position
    for child in node.get_children():
        _collect_nodes(child)

func _count_meshes(node: Node) -> int:
    var total := 1 if node is MeshInstance3D else 0
    for child in node.get_children():
        total += _count_meshes(child)
    return total

func _build_environment() -> void:
    var world := WorldEnvironment.new()
    world.name = "ProofWorldEnvironment"
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.002, 0.003, 0.008)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.07, 0.09, 0.16)
    env.ambient_light_energy = 0.52
    env.tonemap_mode = Environment.TONE_MAPPER_AGX
    env.tonemap_exposure = 1.08
    env.glow_enabled = true
    env.glow_intensity = 0.55
    env.fog_enabled = true
    env.fog_light_color = Color(0.08, 0.11, 0.18)
    env.fog_density = 0.0035
    env.fog_height = -1.0
    env.fog_height_density = 0.15
    world.environment = env
    add_child(world)

func _build_lights() -> void:
    var key := DirectionalLight3D.new()
    key.name = "MoonKey"
    key.light_color = Color(0.78, 0.86, 1.0)
    key.light_energy = 0.72
    key.rotation_degrees = Vector3(-48.0, -28.0, 0.0)
    key.shadow_enabled = true
    add_child(key)

    var colors := [Color(1.0,0.08,0.04), Color(0.08,1.0,0.30), Color(0.08,0.28,1.0)]
    var xs := [-3.5, 0.0, 3.5]
    for i in range(3):
        var light := OmniLight3D.new()
        light.name = "RGBProofLight_%d" % i
        light.light_color = colors[i]
        light.light_energy = 3.4
        light.omni_range = 11.5
        light.shadow_enabled = true
        light.position = Vector3(xs[i], 3.2, 2.8)
        add_child(light)
        rgb_lights.append(light)

    for i in range(5):
        var spot := SpotLight3D.new()
        spot.name = "WarmSpot_%d" % i
        spot.light_color = Color(1.0, 0.72, 0.42)
        spot.light_energy = 3.1
        spot.spot_range = 16.0
        spot.spot_angle = 25.0
        spot.shadow_enabled = true
        spot.position = Vector3(-5.5 + i * 2.75, 7.0, 0.4)
        add_child(spot)
        warm_spots.append(spot)
        spot.look_at(Vector3((-5.5 + i * 2.75) * 0.25, 0.5, -2.6), Vector3.UP)

    var rim := SpotLight3D.new()
    rim.name = "PerformerRim"
    rim.light_color = Color(0.82, 0.90, 1.0)
    rim.light_energy = 5.0
    rim.spot_range = 12.0
    rim.spot_angle = 28.0
    rim.shadow_enabled = true
    rim.position = Vector3(0.0, 4.8, -5.55)
    add_child(rim)
    warm_spots.append(rim)
    rim.look_at(Vector3(0.0, 1.45, -2.1), Vector3.UP)

func _build_camera() -> void:
    camera = Camera3D.new()
    camera.name = "NativeProofCamera"
    camera.current = true
    camera.fov = 51.0
    camera.near = 0.05
    add_child(camera)
    _update_camera(0.0)

func _process(delta: float) -> void:
    elapsed += delta
    _update_camera(elapsed)
    _animate_environment(elapsed)

func _update_camera(t: float) -> void:
    var duration: float = 5.0
    var a: float = clampf(t / duration, 0.0, 1.0)
    var angle: float = lerpf(-0.32, 0.30, a)
    var radius: float = lerpf(14.3, 10.6, a)
    camera.position = Vector3(sin(angle) * radius, lerpf(3.85, 3.15, a), cos(angle) * radius + 0.7)
    camera.look_at(Vector3(0.0, 2.35, -2.25), Vector3.UP)

func _animate_environment(t: float) -> void:
    for i in range(prisms.size()):
        var node := prisms[i]
        var base: Vector3 = base_rotation[node]
        node.rotation = base + Vector3(0.0, sin(t * 0.85 + float(i) * 0.7) * 0.22, 0.0)
    for i in range(lenses.size()):
        var node := lenses[i]
        var base: Vector3 = base_rotation[node]
        node.rotation = base + Vector3(0.0, sin(t * 0.65 + float(i) * 0.8) * 0.30, 0.0)
    for i in range(orbs.size()):
        var node := orbs[i]
        var p: Vector3 = base_position[node]
        node.position = p + Vector3(0.0, sin(t * 0.9 + float(i) * 0.65) * 0.12, 0.0)
        var base: Vector3 = base_rotation[node]
        node.rotation = base + Vector3(0.05 * sin(t * 0.45 + i), t * 0.16, 0.0)
    for i in range(performer_parts.size()):
        var node := performer_parts[i]
        var lower := String(node.name).to_lower()
        if "arml" in lower:
            var base: Vector3 = base_rotation[node]
            node.rotation = base + Vector3(0.0, 0.0, sin(t * 1.1) * 0.12)
        elif "armr" in lower:
            var base: Vector3 = base_rotation[node]
            node.rotation = base + Vector3(0.0, 0.0, -sin(t * 1.1 + 0.7) * 0.12)

    for i in range(rgb_lights.size()):
        var rgb := rgb_lights[i]
        rgb.light_energy = 2.8 + (0.5 + 0.5 * sin(t * 1.55 + float(i) * 2.1)) * 1.2
        rgb.position.y = 3.15 + sin(t * 0.55 + float(i)) * 0.12
    for i in range(warm_spots.size()):
        var spot := warm_spots[i]
        spot.light_energy = 2.65 + (0.5 + 0.5 * sin(t * 1.05 + float(i) * 0.67)) * 1.15

func _apply_runtime_materials(node: Node) -> void:
    if node is MeshInstance3D:
        var mesh_node := node as MeshInstance3D
        var lower := String(mesh_node.name).to_lower()
        if lower.begins_with("rgbbeam_red"):
            mesh_node.material_override = _beam_material(Color(1.0, 0.045, 0.018, 0.34))
        elif lower.begins_with("rgbbeam_green"):
            mesh_node.material_override = _beam_material(Color(0.03, 1.0, 0.18, 0.30))
        elif lower.begins_with("rgbbeam_blue"):
            mesh_node.material_override = _beam_material(Color(0.025, 0.18, 1.0, 0.34))
        elif "prismcrystal" in lower or "lensglass" in lower or lower.begins_with("orb_") or "glasspanel" in lower:
            mesh_node.material_override = _glass_material()
        elif "rearscreen" in lower:
            mesh_node.material_override = _matte_material(Color(0.095, 0.10, 0.13), 0.86)
        elif "performer" in lower or "audience" in lower:
            mesh_node.material_override = _matte_material(Color(0.006, 0.007, 0.012), 0.64)
        elif "gold" in lower or "trim" in lower or "frame" in lower or "ring" in lower or "cable" in lower or "spoke" in lower or "band" in lower or "rail" in lower or "post" in lower:
            mesh_node.material_override = _metal_material(Color(0.32, 0.14, 0.035), 0.94, 0.18)
        else:
            mesh_node.material_override = _metal_material(Color(0.012, 0.016, 0.025), 0.72, 0.22)
    for child in node.get_children():
        _apply_runtime_materials(child)

func _metal_material(color: Color, metallic: float, roughness: float) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = metallic
    mat.roughness = roughness
    return mat

func _matte_material(color: Color, roughness: float) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.03
    mat.roughness = roughness
    return mat

func _glass_material() -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.albedo_color = Color(0.30, 0.54, 0.82, 0.18)
    mat.metallic = 0.08
    mat.roughness = 0.055
    mat.emission_enabled = true
    mat.emission = Color(0.035, 0.08, 0.14)
    mat.emission_energy_multiplier = 0.55
    return mat

func _beam_material(color: Color) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.albedo_color = color
    mat.emission_enabled = true
    mat.emission = Color(color.r, color.g, color.b)
    mat.emission_energy_multiplier = 3.2
    return mat
