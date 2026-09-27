from pathlib import Path
import math
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

OUT = Path(__file__).with_name("cathedral_full_environment_v11.glb")
scene = trimesh.Scene()

materials = {
    "black": PBRMaterial(name="BlackMetal", baseColorFactor=[12,15,22,255], metallicFactor=0.75, roughnessFactor=0.28),
    "gold": PBRMaterial(name="WarmGold", baseColorFactor=[150,72,18,255], metallicFactor=0.92, roughnessFactor=0.18),
    "screen": PBRMaterial(name="ScreenMatte", baseColorFactor=[115,115,120,255], metallicFactor=0.02, roughnessFactor=0.92),
    "glass": PBRMaterial(name="GlassPrism", baseColorFactor=[150,190,230,80], metallicFactor=0.05, roughnessFactor=0.08, alphaMode="BLEND"),
    "red": PBRMaterial(name="RedOptic", baseColorFactor=[255,35,20,190], metallicFactor=0.0, roughnessFactor=0.18, alphaMode="BLEND"),
    "green": PBRMaterial(name="GreenOptic", baseColorFactor=[35,255,90,190], metallicFactor=0.0, roughnessFactor=0.18, alphaMode="BLEND"),
    "blue": PBRMaterial(name="BlueOptic", baseColorFactor=[30,100,255,190], metallicFactor=0.0, roughnessFactor=0.18, alphaMode="BLEND"),
    "performer": PBRMaterial(name="PerformerBlack", baseColorFactor=[8,8,12,255], metallicFactor=0.08, roughnessFactor=0.58),
}

def add(mesh, name, mat="black", transform=None):
    mesh = mesh.copy()
    mesh.visual.material = materials[mat]
    scene.add_geometry(mesh, node_name=name, geom_name=name, transform=np.eye(4) if transform is None else transform)

def box(name, size, pos, mat="black"):
    add(trimesh.creation.box(extents=size), name, mat, trimesh.transformations.translation_matrix(pos))

def cylinder(name, radius, height, pos, mat="black", axis="y", sections=24):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    transform = np.eye(4)
    if axis == "y":
        transform = trimesh.transformations.rotation_matrix(math.pi / 2.0, [1,0,0])
    elif axis == "x":
        transform = trimesh.transformations.rotation_matrix(math.pi / 2.0, [0,1,0])
    transform[:3,3] = pos
    add(mesh, name, mat, transform)

def sphere(name, radius, pos, mat="glass", subdivisions=2):
    add(trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius), name, mat, trimesh.transformations.translation_matrix(pos))

def torus(name, major, minor, pos, mat="gold"):
    mesh = trimesh.creation.torus(major_radius=major, minor_radius=minor, major_sections=64, minor_sections=16)
    transform = trimesh.transformations.euler_matrix(math.pi/2.0, 0, 0, axes="sxyz")
    transform[:3,3] = pos
    add(mesh, name, mat, transform)

def triangular_prism(name, width, height, depth, pos, yaw=0.0):
    vertices = np.array([
        [-width/2,0,-depth/2],[width/2,0,-depth/2],[0,height,-depth/2],
        [-width/2,0,depth/2],[width/2,0,depth/2],[0,height,depth/2]
    ], dtype=float)
    faces = np.array([[0,1,2],[3,5,4],[0,3,4],[0,4,1],[1,4,5],[1,5,2],[2,5,3],[2,3,0]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    transform = trimesh.transformations.rotation_matrix(yaw, [0,1,0])
    transform[:3,3] = pos
    add(mesh, name, "glass", transform)

def beam(name, a, b, radius=0.025, mat="gold"):
    a = np.array(a, float)
    b = np.array(b, float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=12)
    z = np.array([0,0,1.0])
    direction = vec / length
    if np.allclose(z, direction):
        transform = np.eye(4)
    elif np.allclose(z, -direction):
        transform = trimesh.transformations.rotation_matrix(math.pi, [1,0,0])
    else:
        axis = np.cross(z, direction)
        axis /= np.linalg.norm(axis)
        transform = trimesh.transformations.rotation_matrix(math.acos(np.clip(np.dot(z, direction), -1, 1)), axis)
    transform[:3,3] = (a + b) / 2.0
    add(mesh, name, mat, transform)

# Architectural volume.
box("Floor_Main", (20,0.18,16), (0,-0.09,0), "black")
box("Stage_Main", (8.6,0.42,4.9), (0,0.12,-2.15), "black")
for z in (-4.62,0.32):
    box("StageTrimZ_"+str(z), (8.75,0.08,0.08), (0,0.34,z), "gold")
for x in (-4.34,4.34):
    box("StageTrimX_"+str(x), (0.08,0.08,4.86), (x,0.34,-2.15), "gold")

box("RearScreen", (12.0,7.0,0.12), (0,3.55,-6.42), "screen")
box("RearFrameTop", (12.7,0.18,0.28), (0,7.05,-6.45), "gold")
box("RearFrameBottom", (12.7,0.18,0.28), (0,0.06,-6.45), "gold")
for x in (-6.25,6.25):
    box("RearFrameSide_"+str(x), (0.22,7.2,0.28), (x,3.55,-6.45), "gold")

for side in (-1,1):
    x = side * 6.75
    box("Proscenium_"+str(side), (0.55,7.7,0.75), (x,3.75,-3.05), "black")
    for j in range(7):
        box(f"ProBand_{side}_{j}", (0.72,0.08,0.86), (x,0.62+j*1.05,-3.05), "gold")
    balcony_x = side * 7.4
    box("BalconyDeck_"+str(side), (2.8,0.30,5.6), (balcony_x,3.38,-1.2), "black")
    box("BalconyRailTop_"+str(side), (0.08,0.08,5.5), (side*6.02,4.35,-1.2), "gold")
    for index, z in enumerate(np.linspace(-3.7,1.3,9)):
        box(f"BalconyPost_{side}_{index}", (0.06,1.0,0.06), (side*6.02,3.88,float(z)), "gold")
    for step in range(12):
        box(f"Stair_{side}_{step}", (2.0,0.22,0.42), (balcony_x,0.18+step*0.26,3.9-step*0.38), "black")
    for z in (-4.5,2.5):
        box(f"TrussColumn_{side}_{z}", (0.28,7.6,0.28), (side*8.0,3.8,z), "black")

for index, (radius, y) in enumerate(((6.0,6.45),(4.6,6.65),(3.2,6.85))):
    torus(f"CeilingRing_{index}", radius, 0.085, (0,y,-1.0), "gold")
for i in range(24):
    angle = 2.0 * math.pi * i / 24.0
    beam(
        f"CeilingSpoke_{i}",
        (math.cos(angle)*3.25,6.75,-1.0+math.sin(angle)*3.25),
        (math.cos(angle)*5.95,6.55,-1.0+math.sin(angle)*5.95),
        0.035,
        "gold",
    )

# Optical installation.
prisms = [
    (-5.0,-1.6,1.4,3.5,1.0,0.16),(-3.55,0.65,1.1,2.6,0.8,-0.12),
    (5.0,-1.6,1.4,3.5,1.0,-0.16),(3.55,0.65,1.1,2.6,0.8,0.12),
    (-2.25,-3.75,0.9,2.4,0.72,0.06),(2.25,-3.75,0.9,2.4,0.72,-0.06)
]
for i, (x,z,w,h,d,yaw) in enumerate(prisms):
    box(f"PrismPedestal_{i}", (1.6 if i < 4 else 1.2,0.7,1.6 if i < 4 else 1.2), (x,0.35,z), "black")
    triangular_prism(f"PrismCrystal_{i}", w,h,d, (x,0.7,z), yaw)

lenses = [(-4.0,2.0,-0.2,1.0),(4.0,2.0,-0.2,1.0),(-2.9,2.55,-3.7,0.68),(2.9,2.55,-3.7,0.68)]
for i, (x,y,z,radius) in enumerate(lenses):
    box(f"LensPedestal_{i}", (1.1,0.7,1.1), (x,0.35,z), "black")
    torus(f"LensRing_{i}", radius, 0.08, (x,y,z), "gold")
    cylinder(f"LensGlass_{i}", radius*0.84, 0.05, (x,y,z), "glass", "z", 48)

orbs = [(-4.8,4.9,-1.4,0.48),(-2.4,5.55,-2.0,0.38),(0,5.95,-1.5,0.82),(2.4,5.55,-2.0,0.38),(4.8,4.9,-1.4,0.48),(0,4.75,-4.1,0.42)]
for i, (x,y,z,radius) in enumerate(orbs):
    sphere(f"Orb_{i}", radius, (x,y,z), "glass", 2)
    beam(f"OrbCable_{i}", (x,y+radius,z), (x,7.0,z), 0.018, "gold")

for side in (-1,1):
    for i, z in enumerate((-4.3,-2.2,0.0)):
        box(f"GlassPanel_{side}_{i}", (0.12,4.8,1.7), (side*(5.3+0.35*i),2.5,z), "glass")

# Volumetric performer proxy.
capsule = trimesh.creation.capsule(height=1.15, radius=0.28, count=[16,16])
transform = trimesh.transformations.rotation_matrix(math.pi/2.0, [1,0,0])
transform[:3,3] = [0,1.45,-2.1]
add(capsule, "PerformerTorso", "performer", transform)
sphere("PerformerHead", 0.26, (0,2.22,-2.1), "performer", 2)
beam("PerformerArmL", (-0.12,1.75,-2.1), (-0.95,2.35,-2.05), 0.07, "performer")
beam("PerformerArmR", (0.12,1.75,-2.1), (0.88,1.42,-2.0), 0.07, "performer")
beam("PerformerLegL", (-0.12,0.9,-2.1), (-0.25,0.25,-2.1), 0.09, "performer")
beam("PerformerLegR", (0.12,0.9,-2.1), (0.25,0.25,-2.1), 0.09, "performer")
gown = trimesh.creation.cone(radius=1.15, height=1.75, sections=48)
transform = trimesh.transformations.rotation_matrix(-math.pi/2.0, [1,0,0])
transform[:3,3] = [0,0.87,-2.1]
add(gown, "PerformerGown", "performer", transform)

# Physical RGB fixtures and beam geometry.
for i, (x, color) in enumerate(((-3.4,"red"),(0.0,"green"),(3.4,"blue"))):
    cylinder(f"RGBLightHousing_{i}", 0.22, 0.5, (x,2.9,2.7), "black", "z", 24)
    beam(f"RGBBeam_{color}", (x,2.9,2.45), (0,1.55,-5.9), 0.035, color)

# Balcony audience proxies.
for side in (-1,1):
    for i in range(8):
        x = side * (6.5 + 0.2 * (i % 2))
        z = -3.3 + i * 0.7
        y = 3.72
        cylinder(f"AudienceBody_{side}_{i}", 0.08, 0.55, (x,y,z), "performer", "y", 12)
        sphere(f"AudienceHead_{side}_{i}", 0.10, (x,y+0.34,z), "performer", 1)

OUT.write_bytes(trimesh.exchange.gltf.export_glb(scene))
print("generated", OUT, OUT.stat().st_size, "bytes", len(scene.geometry), "mesh nodes")
