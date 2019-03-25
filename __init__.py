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
import subprocess
from bpy.props import BoolProperty, StringProperty, PointerProperty


bl_info = {
    "name": "Taper",
    "author": "BennyKok",
    "description": "Mostly speed up the workflow across different tools.",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "View 3D",
    "panel_id_name_export": "Taper_Export_Panel",
    "panel_label_export": "Export",
    "panel_id_name_substance_link": "Taper_Substance_Link_Panel",
    "panel_label_substance_link": "Substance Link",
    "operator_id_prefix": "taper"
}


class Configs(bpy.types.PropertyGroup):

    # adding our custom property to the Scene type
    export_to_folder = BoolProperty(
        name="Export to Folder",
        description="Export the files to targeted destination.",
        default=False
    )

    folder_export_path = StringProperty(
        name="Folder Export Path",
        default="",
        description="Define the export path to the folder.",
        subtype='DIR_PATH'
    )

    substance_painter_path = StringProperty(
        name="Substance Painter path",
        default="",
        description="The .exe file path of Substance Painter.",
        subtype='FILE_PATH'
    )


class Utils(object):

    @staticmethod
    def getExportPath(configs: Configs, filename=None):
        if not bpy.data.is_saved:
            return None, "File not saved"

        folderName = os.path.splitext(
            bpy.path.basename(bpy.context.blend_data.filepath))[0]
        folderPath = os.path.join(os.path.dirname(
            bpy.context.blend_data.filepath), folderName, "")

        if (configs.export_to_folder):
            if configs.folder_export_path:
                folderPath = configs.folder_export_path
            else:
                return None, "Unspecificed folder path"

        print("Exporting at : " + folderPath)
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        if not (filename == None):
            folderPath = os.path.join(folderPath, filename)
            folderPath = bpy.path.ensure_ext(folderPath, ".fbx")

        return folderPath, None

    @staticmethod
    def getSubstancePainterPath(configs: Configs):
        return configs.substance_painter_path

    @staticmethod
    def getActiveCollectionName(context):
        return bpy.path.clean_name(context.view_layer.active_layer_collection.name)


class ExportFBXCollectionsOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".export_fbx_collections"
    bl_label = "Export FBX Collections"
    button_label = "All"

    def execute(self, context):
        path, error = Utils.getExportPath(
            configs=context.scene.ocd_configs
        )
        if not path == None:
            bpy.ops.export_scene.fbx(
                filepath=path,
                # SCENE_COLLECTION
                batch_mode='COLLECTION',
                use_batch_own_dir=False
            )
        else:
            self.report({'ERROR'}, error)

        print(error)
        return {'FINISHED'}


class ExportFBXActiveCollectionOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".export_fbx_active_collection"
    bl_label = "Export Active FBX Collection"
    button_label = "Active"

    def execute(self, context):
        path, error = Utils.getExportPath(
            configs=context.scene.ocd_configs,
            filename=Utils.getActiveCollectionName(context)
        )
        if not path == None:
            bpy.ops.export_scene.fbx(
                filepath=path,
                use_active_collection=True,
                batch_mode='OFF',
                use_batch_own_dir=False
            )
        else:
            self.report({'ERROR'}, error)
        return {'FINISHED'}


class TaperExportPanel(bpy.types.Panel):
    bl_idname = bl_info["panel_id_name_export"]
    bl_label = bl_info["panel_label_export"]
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

        layout.prop(configs, "export_to_folder")
        if (configs.export_to_folder):
            layout.prop(configs, "folder_export_path", text="")


class SubstanceLinkOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".substance_link"
    bl_label = "Substance Painter Link"

    update_mesh = BoolProperty(default=False)

    def execute(self, context):
        painter_path = Utils.getSubstancePainterPath(
            context.scene.ocd_configs
        )
        mesh_path, error = Utils.getExportPath(
            context.scene.ocd_configs,
            filename=Utils.getActiveCollectionName(context)
        )

        if not self.update_mesh:
            subprocess.Popen(
                [
                    painter_path,
                    '--mesh',
                    mesh_path
                ]
            )
            
        return {'FINISHED'}


class TaperSubstanceLinkPanel(bpy.types.Panel):
    bl_idname = bl_info["panel_id_name_substance_link"]
    bl_label = bl_info["panel_label_substance_link"]
    bl_category = bl_info["name"]
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        configs = scene.ocd_configs

        layout.label(text="Painter Path")
        layout.prop(configs, "substance_painter_path", text="")

        layout.label(text="Active Collection")
        row = layout.row()
        linkOperator = row.operator(
            SubstanceLinkOperator.bl_idname,
            text="Send to Painter"
        )
        linkOperator.update_mesh = False


classes = (
    Configs,
    ExportFBXCollectionsOperator,
    ExportFBXActiveCollectionOperator,
    SubstanceLinkOperator,
    TaperExportPanel,
    TaperSubstanceLinkPanel
)

m_register, m_unregister = bpy.utils.register_classes_factory(classes)


def register():
    m_register()
    bpy.types.Scene.ocd_configs = PointerProperty(type=Configs)


def unregister():
    del bpy.types.Scene.ocd_configs
    m_unregister()
