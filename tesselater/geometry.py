"""
Geometric primitives for printability evaluation.

Mathematical resolution (toppling / base contact)
=================================================

Previous code used (1) the average of mesh *vertices* as center of mass and
(2) axis-aligned bounding-box tests for "is the stability circle inside the
first layer". Both are incorrect for general STL geometry.

1) Volumetric center of mass for a closed triangular polyhedron
--------------------------------------------------------------
Assume uniform density. Decompose the solid into tetrahedra from the origin
to each oriented surface triangle (a, b, c). With

    V_i = (1/6) a · (b × c)

the signed volume and mass-centroid contributions are

    V   = Σ V_i
    C_x = (1/(24 V)) Σ (a_x + b_x + c_x) (a · (b × c))
        = (1/(4 V))  Σ V_i (a_x + b_x + c_x)     (since a·(b×c) = 6 V_i)

and cyclic for y, z. If the mesh is not closed or V ≈ 0, fall back to
area-weighted face centroids (thin-shell approximation):

    C = (Σ A_i c_i) / (Σ A_i),  c_i = (a+b+c)/3,  A_i = (1/2)||(b-a)×(c-a)||.

2) First-layer footprint and circle containment
-----------------------------------------------
Let B be the set of mesh points with z ≤ z_min + h_layer (the contact slab).
Project B to the XY plane and take its convex hull H = conv({(x,y)}).

The tip-stability circle at a lean angle θ is the set of bed points whose
horizontal offset from the COM projection C_xy equals

    r = H_mesh · tan(θ)

(with H_mesh = z_max - z_min). Under a quasi-static lean of angle θ about an
arbitrary horizontal axis, the vertical through the COM intersects the bed
on that circle; if the entire circle lies in H, every such lean keeps the
support force inside the contact set (conservative convex-hull criterion).

Containment is tested by requiring every sample point on the circle to lie
inside H (ray-crossing point-in-polygon on the hull ring). Contact area is
the polygonal area of H (shoelace), not the AABB product Δx·Δy.

3) Dimensionless stability margin
---------------------------------
    m = Area(H) / (H_mesh · d²)

where d is the nozzle diameter. Large m ⇒ wide, short parts; small m ⇒ tall,
narrow bases. This replaces the previous dimensional threshold 9.67 (mm).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv


@dataclass(frozen=True)
class Footprint:
    """XY convex contact footprint of the first layer."""

    hull_xy: np.ndarray  # (n, 2) CCW ring, not closed
    area: float
    z_min: float
    thickness: float

    @property
    def closed_ring(self) -> np.ndarray:
        if len(self.hull_xy) == 0:
            return self.hull_xy
        return np.vstack([self.hull_xy, self.hull_xy[:1]])


def _triangle_soup(mesh: pv.PolyData) -> np.ndarray:
    """Return (n_tri, 3, 3) array of triangle vertex coordinates."""
    surf = mesh
    if mesh.n_cells == 0:
        return np.zeros((0, 3, 3), dtype=float)
    # Triangulate to guarantee 3-vertex faces.
    if not mesh.is_all_triangles:
        surf = mesh.triangulate()
    faces = surf.faces.reshape(-1, 4)
    if faces.size == 0:
        return np.zeros((0, 3, 3), dtype=float)
    pts = surf.points
    return pts[faces[:, 1:4]]


def volume_center_of_mass(mesh: pv.PolyData) -> np.ndarray:
    """
    Uniform-density COM of a triangular mesh.

    Prefers the closed-polyhedron tetrahedral formula; falls back to
    area-weighted face centroids when volume is negligible.
    See module docstring for the derivation.
    """
    tris = _triangle_soup(mesh)
    if len(tris) == 0:
        return np.asarray(mesh.center, dtype=float)

    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    triple = np.einsum("ij,ij->i", a, np.cross(b, c))
    triple_sum = float(triple.sum())

    if abs(triple_sum) > 1e-9:
        # V = triple_sum/6, C = Σ triple(a+b+c)/(24 V) = Σ triple(a+b+c)/(4 triple_sum)
        weighted = (triple[:, None] * (a + b + c)).sum(axis=0)
        return weighted / (4.0 * triple_sum)

    cross = np.cross(b - a, c - a)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    total_area = float(areas.sum())
    if total_area <= 1e-15:
        return np.asarray(mesh.center, dtype=float)
    centroids = (a + b + c) / 3.0
    return (areas[:, None] * centroids).sum(axis=0) / total_area


def convex_hull_xy(points_xy: np.ndarray) -> np.ndarray:
    """Monotone-chain convex hull. Returns CCW vertices without repeating the first."""
    pts = np.asarray(points_xy, dtype=float)
    if len(pts) == 0:
        return pts.reshape(0, 2)
    # Deduplicate
    pts = np.unique(np.round(pts, decimals=9), axis=0)
    if len(pts) <= 1:
        return pts
    if len(pts) == 2:
        return pts

    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[np.ndarray] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: list[np.ndarray] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    hull = np.asarray(lower[:-1] + upper[:-1], dtype=float)
    return hull


def polygon_area(xy: np.ndarray) -> float:
    """Shoelace area of a simple polygon (CCW or CW; returns absolute value)."""
    if len(xy) < 3:
        return 0.0
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def point_in_convex_polygon(point_xy: np.ndarray, hull_xy: np.ndarray, eps: float = 1e-9) -> bool:
    """Point-in-convex-polygon via consistent half-plane tests (CCW hull)."""
    if len(hull_xy) < 3:
        return False
    x, y = float(point_xy[0]), float(point_xy[1])
    n = len(hull_xy)
    for i in range(n):
        x1, y1 = hull_xy[i]
        x2, y2 = hull_xy[(i + 1) % n]
        # Cross product (edge × op) should be >= 0 for CCW hull
        cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if cross < -eps:
            return False
    return True


def circle_inside_footprint(
    center_xy: np.ndarray,
    radius: float,
    hull_xy: np.ndarray,
    samples: int = 64,
) -> bool:
    """True iff the circle of given radius about center_xy lies in conv(hull)."""
    if radius <= 0:
        return point_in_convex_polygon(center_xy, hull_xy)
    if not point_in_convex_polygon(center_xy, hull_xy):
        return False
    theta = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    pts = np.column_stack(
        [center_xy[0] + radius * np.cos(theta), center_xy[1] + radius * np.sin(theta)]
    )
    return all(point_in_convex_polygon(p, hull_xy) for p in pts)


def first_layer_footprint(mesh: pv.PolyData, layer_height: float) -> Footprint:
    """
    Contact footprint: convex hull of points in the slab
    z ∈ [z_min, z_min + layer_height] (with a small fallback expansion).
    """
    z = mesh.points[:, 2]
    z_min = float(z.min())
    thickness = max(float(layer_height), 1e-6)
    mask = z <= z_min + thickness
    # Expand slab until we capture some geometry (warped / floating bases).
    expand = 1
    while mask.sum() < 3 and expand <= 20:
        mask = z <= z_min + thickness * expand
        expand += 1
    pts = mesh.points[mask][:, :2]
    if len(pts) < 3:
        # Last resort: lowest 5% of vertices by z
        cutoff = np.quantile(z, 0.05)
        pts = mesh.points[z <= cutoff][:, :2]
    hull = convex_hull_xy(pts)
    area = polygon_area(hull)
    return Footprint(hull_xy=hull, area=area, z_min=z_min, thickness=thickness * expand)


def mesh_height(mesh: pv.PolyData) -> float:
    bounds = mesh.bounds
    return float(bounds[5] - bounds[4])


def stability_circle_points(
    center_xy: np.ndarray,
    radius: float,
    samples: int = 100,
) -> np.ndarray:
    """Return (samples, 3) XYZ points of the tip-stability circle on z=0."""
    theta = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    xy = np.column_stack(
        [center_xy[0] + radius * np.cos(theta), center_xy[1] + radius * np.sin(theta)]
    )
    return np.column_stack([xy, np.zeros(samples)])


def tip_radius(height: float, tip_angle_deg: float) -> float:
    """r = H tan(θ) — bed locus of the COM vertical under lean θ."""
    return float(height * np.tan(np.radians(tip_angle_deg)))


def dimensionless_stability_margin(
    contact_area: float,
    height: float,
    nozzle_size: float,
) -> float:
    """m = A_contact / (H · d²)."""
    denom = max(height * nozzle_size * nozzle_size, 1e-12)
    return float(contact_area / denom)


def clamp_unit(value: float) -> float:
    return float(np.clip(value, -1.0, 1.0))


def face_angles_to_build(
    mesh: pv.PolyData,
    build_direction: np.ndarray | None = None,
) -> np.ndarray:
    """Angle in degrees between each cell normal and the build direction."""
    build = np.asarray(build_direction if build_direction is not None else [0.0, 0.0, 1.0], dtype=float)
    build = build / max(np.linalg.norm(build), 1e-15)
    work = mesh.copy()
    work.compute_normals(cell_normals=True, point_normals=False, inplace=True)
    normals = np.asarray(work.cell_normals, dtype=float)
    norms = np.linalg.norm(normals, axis=1)
    norms[norms < 1e-15] = 1.0
    normals = normals / norms[:, None]
    dots = np.einsum("ij,j->i", normals, build)
    return np.degrees(np.arccos(np.clip(dots, -1.0, 1.0)))


def hull_polydata(footprint: Footprint, z: float = 0.0) -> pv.PolyData:
    """Visual helper: closed polygon of the footprint at height z."""
    if len(footprint.hull_xy) == 0:
        return pv.PolyData()
    ring = footprint.closed_ring
    pts = np.column_stack([ring, np.full(len(ring), z)])
    # Polyline
    n = len(pts)
    lines = np.hstack([[n], np.arange(n)])
    return pv.PolyData(pts, lines=lines)
