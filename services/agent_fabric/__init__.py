"""Provider-neutral HAL agent engineering fabric.

Import concrete contract helpers from services.agent_fabric.contract. Keeping the
package initializer side-effect free also allows the contract module to run as a
CLI without Python's runpy duplicate-import warning.
"""
