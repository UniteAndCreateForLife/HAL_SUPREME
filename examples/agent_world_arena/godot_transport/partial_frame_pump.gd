class_name HALPartialFramePump
extends RefCounted
## Additive transport component. The arena still owns request identity,
## terminal outcomes, scheduling, physics and action validation.
## Signals carry sanitized codes, never raw worker content.
signal protocol_fault(event: Dictionary)

const FRAME_LIMIT: int = 256000
const IO_BYTES: int = 8192
const FRAME_BUDGET: int = 4

var peer: Variant = null
var generation: int = 0
var rx: PackedByteArray = PackedByteArray()
var tx: PackedByteArray = PackedByteArray()
var stopped: bool = true
var fault_events: int = 0

func bind(connected_peer: Variant) -> Error:
	if not stopped or peer != null:
		return ERR_ALREADY_IN_USE
	if connected_peer == null:
		return ERR_INVALID_PARAMETER
	peer = connected_peer
	generation += 1
	rx.clear()
	tx.clear()
	stopped = false
	return OK

func queue_request(frame: PackedByteArray) -> Error:
	if stopped or peer == null:
		return ERR_UNAVAILABLE
	if not tx.is_empty():
		return ERR_BUSY
	if frame.is_empty() or frame.size() > FRAME_LIMIT + 1 or frame[-1] != 10:
		return ERR_INVALID_DATA
	tx = frame.duplicate()
	return OK

func _fault(code: String) -> Dictionary:
	if stopped:
		return {"frames": [], "fault": "", "closed": false}
	stopped = true
	rx.clear()
	tx.clear()
	fault_events += 1
	protocol_fault.emit({
		"schema": "hal.agent_world.transport_fault.v1",
		"generation": generation, "code": code,
		"scope": "transport_event_not_request_outcome"
	})
	return {"frames": [], "fault": code, "closed": false}

func poll_response() -> Dictionary:
	var result: Dictionary = {"frames": [], "fault": "", "closed": false,
		"sent_bytes": 0, "received_bytes": 0}
	if stopped or peer == null:
		return result
	if peer.poll() != OK:
		return _fault("socket_poll_error")
	var status: int = peer.get_status()
	if status == StreamPeerTCP.STATUS_CONNECTING:
		return result
	var disconnected: bool = status != StreamPeerTCP.STATUS_CONNECTED
	# Never put_data()/get_data(): both can block a Godot engine thread.
	if not disconnected and not tx.is_empty():
		var sent: Array = peer.put_partial_data(tx.slice(0, mini(IO_BYTES, tx.size())))
		if sent.size() != 2 or sent[0] != OK:
			return _fault("partial_send_error")
		var count: int = int(sent[1])
		if count < 0 or count > mini(IO_BYTES, tx.size()):
			return _fault("invalid_send_count")
		tx = tx.slice(count)
		result["sent_bytes"] = count
	# Drain bounded complete frames before admitting more input.
	if not disconnected and rx.find(10) < 0:
		var available: int = mini(IO_BYTES, peer.get_available_bytes())
		if available > 0:
			var received: Array = peer.get_partial_data(available)
			if received.size() != 2 or received[0] != OK:
				return _fault("partial_receive_error")
			var chunk: PackedByteArray = received[1]
			if chunk.size() > available:
				return _fault("invalid_receive_count")
			rx.append_array(chunk)
			result["received_bytes"] = chunk.size()
	for _index in range(FRAME_BUDGET):
		var ending: int = rx.find(10)
		if ending < 0:
			if rx.size() > FRAME_LIMIT:
				return _fault("frame_too_large")
			break
		if ending > FRAME_LIMIT:
			return _fault("frame_too_large")
		result["frames"].append(rx.slice(0, ending + 1))
		rx = rx.slice(ending + 1)
	if disconnected:
		if not rx.is_empty() and rx.find(10) < 0:
			return _fault("truncated_frame")
		if rx.is_empty():
			stopped = true
			result["closed"] = true
	return result

func close() -> void:
	if peer != null:
		peer.disconnect_from_host()
	peer = null
	stopped = true
	rx.clear()
	tx.clear()
