# context.area: VIEW_3D
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
import os
from bpy.props import BoolProperty, StringProperty, PointerProperty


bl_info = {
    "name": "Taper",
    "author": "BennyKok",
    "description": "Mostly speed up the workflow across different tools.",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "View 3D",
    "panel_id_name": "Tapert_Panel",
    "operator_id_prefix": "taper"
}


class Configs(bpy.types.PropertyGroup):

    # adding our custom property to the Scene type
    export_to_unity_project = BoolProperty(
        name="Export to Unity",
        description="Export the files to targeted destination.",
        default=False
    )

    unity_export_path = StringProperty(
        name="Unity Export Path",
        default="",
        description="Define the export path to the Unity project.",
        subtype='DIR_PATH'
    )


class Utils(object):

    @staticmethod
    def getExportPath(filename=None):
        folderName = os.path.splitext(
            bpy.path.basename(bpy.context.blend_data.filepath))[0]
        folderPath = os.path.join(os.path.dirname(
            bpy.context.blend_data.filepath), folderName, "")

        print("Exporting at : " + folderPath)
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        if not (filename == None):
            folderPath = os.path.join(folderPath, filename)
            folderPath = bpy.path.ensure_ext(folderPath, ".fbx")

        return folderPath


class ExportFBXCollectionsOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".fbx_collections"
    bl_label = "Export FBX Collections"
    button_label = "All"

    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.export_scene.fbx(
                filepath=Utils.getExportPath(),
                # SCENE_COLLECTION
                batch_mode='COLLECTION',
                use_batch_own_dir=False
            )
        return {'FINISHED'}


class ExportFBXActiveCollectionOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".fbx_activecollection"
    bl_label = "Export Active FBX Collection"
    button_label = "Active"

    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.export_scene.fbx(
                filepath=Utils.getExportPath(
                    filename=bpy.context.view_layer.active_layer_collection.name),
                use_active_collection=True,
                batch_mode='OFF',
                use_batch_own_dir=False
            )
        return {'FINISHED'}


class QuickExportPanel(bpy.types.Panel):
    bl_idname = bl_info["panel_id_name"]
    bl_label = bl_info["name"]
    bl_category = bl_info["name"]
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        configs = scene.ocd_configs

        if not bpy.data.is_saved:
            layout.label(text="File not saved")

        layout.label(text="Export Collection to FBX")
        row = layout.row()
        row.operator(
            ExportFBXCollectionsOperator.bl_idname,
            text=ExportFBXCollectionsOperator.button_label
        )
        row = layout.row()
        row.operator(
            ExportFBXActiveCollectionOperator.bl_idname,
            text=ExportFBXActiveCollectionOperator.button_label
        )

        layout.prop(configs, "export_to_unity_project")
        if (configs.export_to_unity_project):
            layout.label(text="Path to export")
            layout.prop(configs, "unity_export_path", text="")


classes = (
    Configs,
    ExportFBXCollectionsOperator,
    ExportFBXActiveCollectionOperator,
    QuickExportPanel
)

m_register, m_unregister = bpy.utils.register_classes_factory(classes)

def register():
    m_register()
    bpy.types.Scene.ocd_configs = PointerProperty(type=Configs)

def unregister():
    del bpy.types.Scene.ocd_configs
    m_unregister()