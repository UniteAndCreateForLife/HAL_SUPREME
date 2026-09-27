extends Node3D

var camera: Camera3D
var elapsed := 0.0
var prisms: Array[Node3D] = []
var lenses: Array[Node3D] = []
var orbs: Array[Node3D] = []
var performer_parts: Array[Node3D] = []
var base_rotation := {}
var base_position := {}

func _ready() -> void:
    _collect_nodes(self)
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
    env.ambient_light_color = Color(0.10, 0.13, 0.20)
    env.ambient_light_energy = 0.85
    env.tonemap_mode = Environment.TONE_MAPPER_AGX
    env.tonemap_exposure = 1.22
    env.glow_enabled = true
    env.glow_intensity = 0.75
    env.fog_enabled = true
    env.fog_light_color = Color(0.08, 0.11, 0.18)
    env.fog_density = 0.006
    env.fog_height = -1.0
    env.fog_height_density = 0.15
    world.environment = env
    add_child(world)

func _build_lights() -> void:
    var key := DirectionalLight3D.new()
    key.name = "MoonKey"
    key.light_color = Color(0.78, 0.86, 1.0)
    key.light_energy = 1.15
    key.rotation_degrees = Vector3(-48.0, -28.0, 0.0)
    key.shadow_enabled = true
    add_child(key)

    var colors := [Color(1.0,0.08,0.04), Color(0.08,1.0,0.30), Color(0.08,0.28,1.0)]
    var xs := [-3.5, 0.0, 3.5]
    for i in range(3):
        var light := OmniLight3D.new()
        light.name = "RGBProofLight_%d" % i
        light.light_color = colors[i]
        light.light_energy = 8.0
        light.omni_range = 13.0
        light.shadow_enabled = true
        light.position = Vector3(xs[i], 3.2, 2.8)
        add_child(light)

    for i in range(5):
        var spot := SpotLight3D.new()
        spot.name = "WarmSpot_%d" % i
        spot.light_color = Color(1.0, 0.72, 0.42)
        spot.light_energy = 5.0
        spot.spot_range = 16.0
        spot.spot_angle = 25.0
        spot.shadow_enabled = true
        spot.position = Vector3(-5.5 + i * 2.75, 7.0, 0.4)
        add_child(spot)
        spot.look_at(Vector3((-5.5 + i * 2.75) * 0.25, 0.5, -2.6), Vector3.UP)

func _build_camera() -> void:
    camera = Camera3D.new()
    camera.name = "NativeProofCamera"
    camera.current = true
    camera.fov = 48.0
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
    var angle: float = lerpf(-0.24, 0.26, a)
    var radius: float = lerpf(13.5, 10.2, a)
    camera.position = Vector3(sin(angle) * radius, lerpf(3.9, 3.0, a), cos(angle) * radius + 0.4)
    camera.look_at(Vector3(0.0, 2.45, -2.2), Vector3.UP)

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
