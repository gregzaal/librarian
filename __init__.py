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
    "version": (1, 0, 2),
    "blender": (2, 77, 0),
    "location": "Properties Editor > Scene > Librarian panel",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Scene"}


import bpy
import os
from bpy_extras.io_utils import ImportHelper
from . import addon_updater_ops

'''
TODO:
    Clicking on datablocks should do something (select object, go to material, particle settings, etc...)
    Avoid iterating over all objects on every redraw (maybe)
    Maybe make list into a bit of a heirarchy? Nest materials & mesh data under the objects they belong to...
'''

class LibrarianPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    # addon updater preferences
    auto_check_update = bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = True,
        )
    updater_intrval_months = bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0,
        min=0
        )
    updater_intrval_days = bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7,
        min=0,
        )
    updater_intrval_hours = bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
        )
    updater_intrval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
        )

    def draw(self, context):
        layout=self.layout
        addon_updater_ops.update_settings_ui(self, context)

class LibrarianSettings(bpy.types.PropertyGroup):
    expanded = bpy.props.StringProperty()  # Used to keep track of which libs are expanded

#####  Functions  #####
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
    'Key': 'KEY_HLT',
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

def pad_lib_name(lib):
    """ Used to ensure lib names do not match inside each other ('Lib' won't match 'Lib.001') """
    return ("__###_" + lib + "_###__")

#####  Operators #####
class LibrarianToggleExpand(bpy.types.Operator):
    """Show/hide the list of datablocks linked"""
    bl_idname = "librarian.expand"
    bl_label = "Expand"
    lib = bpy.props.StringProperty()  # name of lib to toggle

    def execute(self, context):
        expanded = context.scene.librarian_settings.expanded
        if self.lib in expanded:
            expanded = expanded.replace(self.lib, "")
        else:
            expanded += self.lib

        context.scene.librarian_settings.expanded = expanded

        return {'FINISHED'}

class LibrarianReload(bpy.types.Operator):
    """Refresh this library to fetch any changes made to that file"""
    bl_idname = "librarian.reload"
    bl_label = "Reload"
    lib = bpy.props.StringProperty()
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.data.libraries[self.lib].reload()

        return {'FINISHED'}

class LibrarianImportBlend(bpy.types.Operator, ImportHelper):
    """Import all objects from another file into the current scene, keeping the linked libraries in tact"""
    bl_idname = 'librarian.import'
    bl_label = 'Import Objects from File'
    bl_options = {'REGISTER', 'UNDO'}
    directory = bpy.props.StringProperty(subtype="DIR_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")    
    # files = CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        directory = self.directory
        filename = self.filename

        # DEBUG
        print ("\nDIR:", directory)
        print ("FN:", filename)

        if not filename:
            self.report({'ERROR'}, "No file chosen")
            return {'CANCELLED'}

        filepath = os.path.join(directory, filename)

        if not os.path.exists(filepath):
            self.report({'ERROR'}, filepath+" does not exist!")
            return {'CANCELLED'}

        # Get all the scenes from the selected file
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            data_to.scenes = data_from.scenes
        
        # Add all objects from those scenes into the current scene
        cur_scene = context.scene
        scene_names = []
        for sc in data_to.scenes:
            scene_names.append (sc.name)
            for obj in sc.objects:
                cur_scene.objects.link(obj)
                obj.select = True

        print ("2")
        context.screen.scene = cur_scene
        print ("3")

        # Remove imported scenes
        print ("4")
        for sc in data_to.scenes:
            print ("5:", sc)
            bpy.data.scenes.remove(sc)
            print ("6:", sc)

        return {'FINISHED'}

#####  UI  #####
class LibrarianImagePathsPanel(bpy.types.Panel):
    bl_label = "Librarian"
    bl_idname = "OBJECT_PT_Librarian"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        addon_updater_ops.check_for_update_background(context)

        layout = self.layout
        linked_data = get_linked_data()
        settings = context.scene.librarian_settings

        libs = {}  # Dictionary of libraries, with items being lists of linked assets
        for lib in bpy.data.libraries:
            libs[lib] = []

        for g in linked_data:
            libs[g.library] += [g]

        maincol = layout.column(align=True)
        for lib in libs:
            padded_name = pad_lib_name(lib.name)
            is_expanded = padded_name in settings.expanded
            
            box = maincol.box()
            col = box.column(align=True)
            row = col.row()
            row.operator('librarian.expand', text="", emboss=False, icon='TRIA_RIGHT' if not is_expanded else 'TRIA_DOWN').lib = padded_name
            row.label(bpy.path.basename(lib.filepath))

            if is_expanded:
                row = col.row(align=True)
                row.prop(lib, 'filepath', text="")
                row.operator('librarian.reload', icon='FILE_REFRESH', text="").lib=lib.name
                col.separator()

                type_counts = count_types(libs[lib])
                row = col.row(align=True)
                row.alignment = 'CENTER'
                for t in type_counts:
                    row.label(str(type_counts[t]), icon=type_icon(t))
                    
                    # # Debug: print unidentified types
                    # ti = type_icon(t)
                    # if ti == "QUESTION":
                    #     print (t)

                col.separator()
                for d in libs[lib]:
                    col.label(d.name, icon=type_icon(d.rna_type.name))
        if len(libs) == 0:
            maincol.label("There are no linked libraries :)")
        
        maincol.separator()
        maincol.operator('librarian.import', icon='LIBRARY_DATA_DIRECT')

        addon_updater_ops.update_notice_box_ui(self, context)
        


def register():
    addon_updater_ops.register(bl_info)

    bpy.utils.register_module(__name__)

    bpy.types.Scene.librarian_settings = bpy.props.PointerProperty(type=LibrarianSettings)

def unregister():
    del bpy.types.Scene.librarian_settings

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
