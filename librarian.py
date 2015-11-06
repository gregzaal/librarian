# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Librarian",
    "description": "View what datablocks are coming from which linked libraries",
    "author": "Greg Zaal",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "Properties Editor > Scene > Librarian panel",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Scene"}


import bpy

'''
TODO:
    Clicking on datablocks should do something (select object, go to material, particle settings, etc...)
    Lists should be collapsed by default and expanded if user wants to see details.
    Collapse panel by default
    Avoid iterating over all objects on every redraw (maybe)
    Maybe make list into a bit of a heirarchy? Nest materials & mesh data under the objects they belong to...
'''

def get_linked_data():
    # Warning: Gets run for every redraw
    type_iter = type(bpy.data.objects)

    for attr in dir(bpy.data):
        data_iter = getattr(bpy.data, attr, None)
        if type(data_iter) == type_iter:
            for id_data in data_iter:
                if id_data.library:
                    yield id_data

def count_type(data, rna_type):
    c = 0
    for d in data:
        if d.bl_rna.name == rna_type:
            c += 1
    return c

def count_types(data):
    rna_types = {}
    for d in data:
        t = d.rna_type.name

        if 'Node Tree' in t:
            t = 'Node Tree'
        elif 'Lamp' in t:
            t = 'Lamp'
        elif 'Texture' in t:
            t = 'Texture'

        if t in rna_types:
            rna_types[t] += 1
        else:
            rna_types[t] = 1
    return rna_types

def type_icon(t):

    # Special cases:
    if "Node Tree" in t:
        return "NODETREE"  # Shader/Composite etc have different types, but all include "Node Tree"
    elif "Lamp" in t:
        return "LAMP"  # Point/Sun etc have different types, but all include "Lamp"
    elif "Texture" in t:
        return "TEXTURE"  # Image/Cloud etc have different types, but all include "Texture"

    d = {
    'Action': 'ACTION',
    'Armature': 'ARMATURE_DATA',
    'Brush': 'BRUSH_DATA',
    'Camera': 'CAMERA_DATA',
    'Curve': 'CURVE_DATA',
    'Grease Pencil': 'GREASEPENCIL',
    'Group': 'GROUP',
    'Image': 'IMAGE_DATA',
    'Lattice': 'LATTICE_DATA',
    'Mask': 'MOD_MASK',
    'Material': 'MATERIAL',
    'Mesh': 'MESH_DATA',
    'MetaBall': 'META_DATA',
    'MovieClip': 'CLIP',
    'Object': 'OBJECT_DATAMODE',
    'Particle Settings': 'PARTICLES',
    'Scene': 'SCENE_DATA',
    'Speaker': 'SPEAKER',
    'Surface Curve': 'SURFACE_DATA',
    'Text': 'TEXT',
    'Text Curve': 'FONT_DATA',
    'Vector Font': 'FONT_DATA',
    'World': 'WORLD'
    }
    if t in d:
        return d[t]
    else:
        return "QUESTION"  # default icon



class LibrarianImagePathsPanel(bpy.types.Panel):
    bl_label = "Librarian"
    bl_idname = "OBJECT_PT_Librarian"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        linked_data = get_linked_data()

        libs = {}  # Dictionary of libraries, with items being lists of linked assets
        for lib in bpy.data.libraries:
            libs[lib] = []

        for g in linked_data:
            libs[g.library] += [g]

        maincol = layout.column(align=True)
        for lib in libs:
            box = maincol.box()
            col = box.column(align=True)
            row = col.row()
            row.label(bpy.path.basename(lib.filepath))
            col.separator()
            row = col.row(align=True)
            row.alignment = 'CENTER'
            type_counts = count_types(libs[lib])
            for t in type_counts:
                row.label(str(type_counts[t]), icon=type_icon(t))
            col.separator()
            for d in libs[lib]:
                col.label(d.name, icon=type_icon(d.rna_type.name))
        


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
