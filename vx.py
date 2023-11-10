import pyvista as pv
import numpy as np
import pymeshfix as fix
import trimesh

mesh = pv.read("blade.stl")

voxels = pv.voxelize(mesh,density=mesh.length / 300,)
voxels.plot()

