extends SceneTree
const Pump = preload("res://partial_frame_pump.gd")
var checks: int = 0
var failures: Array[String] = []

class FakePeer extends RefCounted:
	var incoming: PackedByteArray = PackedByteArray()
	var sent: PackedByteArray = PackedByteArray()
	var limit: int = 8192
	var state: int = StreamPeerTCP.STATUS_CONNECTED
	var send_calls: int = 0
	var read_calls: int = 0
	func poll() -> Error:
		return OK
	func get_status() -> int:
		return state
	func get_available_bytes() -> int:
		return incoming.size()
	func put_partial_data(data: PackedByteArray) -> Array:
		send_calls += 1
		var count: int = mini(data.size(), limit)
		sent.append_array(data.slice(0, count))
		return [OK, count]
	func get_partial_data(size: int) -> Array:
		read_calls += 1
		var data: PackedByteArray = incoming.slice(0, size)
		incoming = incoming.slice(size)
		return [OK, data]
	func disconnect_from_host() -> void:
		state = StreamPeerTCP.STATUS_NONE

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)

func _initialize() -> void:
	for repeat_index in range(20):
		run_tests(repeat_index)
	print(JSON.stringify({"schema": "hal.godot.transport_tests.v1",
		"engine": Engine.get_version_info()["string"],
		"repeat_runs": 20, "assertions": checks, "failures": failures,
		"scope": "new standalone transport component; fake peer; no model; not external R1-R9"}))
	quit(0 if failures.is_empty() else 1)

func run_tests(repeat_index: int) -> void:
	var p = Pump.new()
	var peer = FakePeer.new()
	check(p.bind(peer) == OK, "bind")
	check(p.bind(peer) == ERR_ALREADY_IN_USE, "double bind")
	peer.limit = 2
	check(p.queue_request("{\"a\":1}\n".to_utf8_buffer()) == OK, "queue")
	check(p.queue_request("{}\n".to_utf8_buffer()) == ERR_BUSY, "pending send")
	for _i in range(4):
		p.poll_response()
	check(peer.sent.get_string_from_utf8() == "{\"a\":1}\n", "partial send")
	check(peer.send_calls == 4, "bounded sends")
	peer.limit = 0
	p.queue_request("{}\n".to_utf8_buffer())
	p.poll_response()
	check(peer.send_calls == 5, "backpressure returns")
	check(p.tx.size() == 3, "backpressure retains bytes")
	peer.limit = 8192
	var unicode_frame: PackedByteArray = "{\"x\":\"你好\"}\n".to_utf8_buffer()
	peer.incoming = unicode_frame.slice(0, 8)
	check(p.poll_response()["frames"].is_empty(), "partial UTF-8 not decoded")
	peer.incoming = unicode_frame.slice(8)
	check(p.poll_response()["frames"][0] == unicode_frame, "UTF-8 reconstructed")
	peer.incoming = "{}\n{}\n{}\n{}\n{}\n{}\n".to_utf8_buffer()
	check(p.poll_response()["frames"].size() == 4, "frame budget")
	var before: int = peer.read_calls
	check(p.poll_response()["frames"].size() == 2, "remaining frames")
	check(peer.read_calls == before, "receive backpressure")
	p.close()
	check(p.rx.is_empty() and p.tx.is_empty(), "close clears buffers")
	var peer2 = FakePeer.new()
	check(p.bind(peer2) == OK and p.generation == 2, "explicit rebind generation")
	peer2.incoming.resize(9000)
	peer2.incoming.fill(120)
	p.poll_response()
	check(p.rx.size() == 8192, "receive byte budget")
	p.close()
	p.bind(FakePeer.new())
	p.rx.resize(Pump.FRAME_LIMIT + 1)
	p.rx.fill(120)
	var seen: Array = []
	p.protocol_fault.connect(func(event: Dictionary): seen.append(event))
	check(p.poll_response()["fault"] == "frame_too_large", "oversized partial frame")
	for _i in range(100):
		p.poll_response()
	check(seen.size() == 1 and p.fault_events == 1, "one fault signal, not 100 polls")
	check(not JSON.stringify(seen).contains("xxxx"), "raw bytes not leaked")
	check(p.bind(FakePeer.new()) == ERR_ALREADY_IN_USE, "fault requires close")
	p.close()
	var peer3 = FakePeer.new()
	p.bind(peer3)
	peer3.incoming = "partial".to_utf8_buffer()
	p.poll_response()
	peer3.state = StreamPeerTCP.STATUS_NONE
	check(p.poll_response()["fault"] == "truncated_frame", "partial EOF signal")
	p.close()
	check(p.poll_response()["frames"].is_empty(), "closed idle")
	check(p.queue_request("{}\n".to_utf8_buffer()) == ERR_UNAVAILABLE, "closed cannot send")
	var peer4 = FakePeer.new()
	p.bind(peer4)
	p.rx = "{}\n{}\n{}\n{}\n{}\n".to_utf8_buffer()
	peer4.state = StreamPeerTCP.STATUS_NONE
	check(p.poll_response()["frames"].size() == 4, "closed peer drains full frames")
	var last: Dictionary = p.poll_response()
	check(last["frames"].size() == 1 and last["closed"], "EOF after frame budget drained")
	p.close()
	if repeat_index == 19:
		print("20 strict native component passes completed")
