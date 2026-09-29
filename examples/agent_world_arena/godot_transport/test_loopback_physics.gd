extends SceneTree
const Pump = preload("res://partial_frame_pump.gd")

class MovingBody extends CharacterBody3D:
	var ticks: int = 0
	func _physics_process(delta: float) -> void:
		ticks += 1
		velocity.x = 2.0
		velocity.y -= 9.8 * delta
		move_and_slide()

func _initialize() -> void:
	call_deferred("run_probe")

func run_probe() -> void:
	Engine.max_fps = 120
	var world := Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	var floor_shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(20, 1, 20)
	floor_shape.shape = box
	floor_body.position.y = -0.5
	floor_body.add_child(floor_shape)
	world.add_child(floor_body)
	var body := MovingBody.new()
	var body_shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.0
	capsule.radius = 0.2
	body_shape.shape = capsule
	body.add_child(body_shape)
	body.position.y = 0.6
	world.add_child(body)
	var server := TCPServer.new()
	if server.listen(0, "127.0.0.1") != OK:
		quit(2)
		return
	var client := StreamPeerTCP.new()
	if client.connect_to_host("127.0.0.1", server.get_local_port()) != OK:
		server.stop()
		quit(3)
		return
	var worker: StreamPeerTCP = null
	var deadline: int = Time.get_ticks_msec() + 3000
	while Time.get_ticks_msec() < deadline:
		client.poll()
		if worker == null and server.is_connection_available():
			worker = server.take_connection()
		if worker != null and client.get_status() == StreamPeerTCP.STATUS_CONNECTED:
			break
		await process_frame
	if worker == null:
		client.disconnect_from_host()
		server.stop()
		quit(4)
		return
	var pump = Pump.new()
	pump.bind(client)
	var frame: PackedByteArray = "{\"request_id\":\"probe\",\"action\":{\"kind\":\"idle\"}}\n".to_utf8_buffer()
	pump.queue_request(frame)
	var received := PackedByteArray()
	var reply := PackedByteArray()
	var start: int = Time.get_ticks_msec()
	var physics_start: int = body.ticks
	var start_x: float = body.position.x
	var first_sent: bool = false
	var second_sent: bool = false
	var valid: bool = false
	var physics_before_reply: int = 0
	var error_code: String = ""
	while Time.get_ticks_msec() - start < 2500:
		worker.poll()
		var available: int = mini(8192, worker.get_available_bytes())
		if available > 0:
			var read_result: Array = worker.get_partial_data(available)
			if read_result[0] != OK:
				error_code = "worker_read"
				break
			received.append_array(read_result[1])
		var elapsed: int = Time.get_ticks_msec() - start
		if received == frame and elapsed >= 350 and not first_sent:
			physics_before_reply = body.ticks - physics_start
			reply = frame.slice(0, 17)
			first_sent = true
		if first_sent and reply.is_empty() and elapsed >= 450 and not second_sent:
			reply = frame.slice(17)
			second_sent = true
		if not reply.is_empty():
			var written: Array = worker.put_partial_data(reply)
			if written[0] != OK:
				error_code = "worker_write"
				break
			reply = reply.slice(int(written[1]))
		var result: Dictionary = pump.poll_response()
		if not result["fault"].is_empty():
			error_code = result["fault"]
			break
		if not result["frames"].is_empty():
			valid = result["frames"][0] == frame and second_sent
			break
		await process_frame
	var displacement: float = body.position.x - start_x
	var passed: bool = valid and error_code.is_empty() and physics_before_reply >= 10 and displacement > 0.4
	print(JSON.stringify({"schema":"hal.godot.loopback_physics.v1", "passed":passed,
		"scope":"new transport component; scripted delayed peer, not an AI model or existing game runner",
		"physics_ticks_before_first_reply":physics_before_reply,
		"body_displacement_m":displacement,"partial_reply_reassembled":valid,
		"wall_duration_ms":Time.get_ticks_msec()-start, "fault":error_code,
		"rendered_video":false, "paid_provider_calls":0}))
	pump.close()
	worker.disconnect_from_host()
	server.stop()
	world.queue_free()
	await process_frame
	quit(0 if passed else 1)
