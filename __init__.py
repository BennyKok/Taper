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
        default="C:\\Program Files\\Allegorithmic\\Substance Painter\\Substance Painter.exe",
        description="The .exe file path of Substance Painter.",
        subtype='FILE_PATH'
    )


class Utils(object):

    @staticmethod
    def get_export_path(configs: Configs, filename=None):
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

        print("Getting path at : " + folderPath)
        Utils.ensure_path(folderPath)

        if not (filename == None):
            folderPath = os.path.join(folderPath, filename)
            folderPath = bpy.path.ensure_ext(folderPath, ".fbx")

        return folderPath, None

    @staticmethod
    def get_textures_export_path(context, configs: Configs):
        export_path, error = Utils.get_export_path(configs)
        textures_path = os.path.join(
            export_path,
            Utils.get_active_collection_name(context)
        )

        Utils.ensure_path(textures_path)

        return textures_path

    @staticmethod
    def ensure_path(folderPath):
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

    @staticmethod
    def get_substance_painter_path(configs: Configs):
        return configs.substance_painter_path

    @staticmethod
    def get_active_collection_name(context):
        return bpy.path.clean_name(context.view_layer.active_layer_collection.name)


class ExportFBXCollectionsOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".export_fbx_collections"
    bl_label = "Export FBX Collections"
    button_label = "All"

    def execute(self, context):
        path, error = Utils.get_export_path(
            configs=context.scene.taper_configs
        )
        if not path == None:
            bpy.ops.export_scene.fbx(
                filepath=path,
                # SCENE_COLLECTION
                batch_mode='COLLECTION',
                use_batch_own_dir=False
            )
            self.report({'INFO'}, "FBX Exported")
        else:
            self.report({'ERROR'}, error)

        print(error)
        return {'FINISHED'}


class ExportFBXActiveCollectionOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".export_fbx_active_collection"
    bl_label = "Export Active FBX Collection"
    button_label = "Active"

    def execute(self, context):
        path, error = Utils.get_export_path(
            configs=context.scene.taper_configs,
            filename=Utils.get_active_collection_name(context)
        )
        if not path == None:
            bpy.ops.export_scene.fbx(
                filepath=path,
                use_active_collection=True,
                batch_mode='OFF',
                use_batch_own_dir=False
            )
            self.report({'INFO'}, "FBX Exported")
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
        configs = scene.taper_configs

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

    # update_mesh: BoolProperty(default=False)

    def execute(self, context):
        bpy.ops.taper.export_fbx_active_collection()

        painter_path = Utils.get_substance_painter_path(
            context.scene.taper_configs
        )
        mesh_path, error = Utils.get_export_path(
            context.scene.taper_configs,
            filename=Utils.get_active_collection_name(context)
        )
        texture_export_path = Utils.get_textures_export_path(
            context,
            context.scene.taper_configs
        )
        sp_project_path, error = Utils.get_export_path(
            context.scene.taper_configs
        )
        sp_project_path = sp_project_path + \
            Utils.get_active_collection_name(context) + ".spp"

        subprocess.Popen(
            [
                painter_path,
                "--disable-version-checking",
                '--mesh',
                mesh_path,
                "--export-path",
                texture_export_path,
                sp_project_path
            ]
        )

        self.report({'INFO'}, "Opening Substance Painter")

        return {'FINISHED'}


class SubstancePullTexturesOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".substance_pull_textures"
    bl_label = "Pull Substance Painter Textures"

    gloss_tag = 'gloss glossy glossyness'
    bump_tag = 'bump bmp'
    socketnames = [
        [
            'Base Color',
            'diffuse diff albedo base col color'.split(' ')
        ],
        [
            'Subsurface Color',
            'sss subsurface'.split(' ')
        ],
        [
            'Metallic',
            'metallic metalness metal mtl'.split(' ')
        ],
        [
            'Specular',
            'specularity specular spec spc'.split(' ')
        ],
        [
            'Roughness',
            ('roughness rough rgh ' + gloss_tag).split(' ')
        ],
        [
            'Normal',
            ('normal nor nrm nrml norm ' + bump_tag).split(' ')
        ],
        [
            'Displacement',
            'displacement displace disp dsp height heightmap'.split(' ')
        ]
    ]

    @classmethod
    def get_image(self, texture_export_path, file_name):
        path_to_texture = os.path.join(
            texture_export_path,
            file_name
        )

        return bpy.data.images.load(path_to_texture)

    @classmethod
    def get_matched_image(self, texture_export_path, image_files, socket):
        for tag in socket[1]:
            for image in image_files:
                image_name = image['name'].lower()
                if tag in image_name:
                    file_name = image['name']
                    extra = None

                    if socket[0] == 'Roughness':
                        for special_tag in self.gloss_tag.split(' '):
                            if special_tag in image_name:
                                extra = 'IS_GLOSS'
                                break
                    elif socket[0] == 'Normal':
                        for special_tag in self.bump_tag.split(' '):
                            if special_tag in image_name:
                                extra = 'IS_BUMP'
                                break

                    return self.get_image(texture_export_path, file_name), extra

        return None, None

    @classmethod
    def match_material_slot_with_textures(self, context, texture_export_path, material_name: str):
        m_files = []
        for filename in os.listdir(texture_export_path):
            if filename.endswith(".png") and filename.split('_')[0] == material_name:
                m_files.append({'name': filename})
                continue
            else:
                continue

        # print(m_files)

        # We get all the node tree for current material
        node_tree = bpy.data.materials[material_name].node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        target_shader_node = [
            n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'
        ][0]
        output_node = [
            n for n in nodes if n.bl_idname == 'ShaderNodeOutputMaterial'
        ][0]

        mapping = None
        texture_input = None
        index = 0

        for socket in self.socketnames:
            img, extra = self.get_matched_image(
                texture_export_path, m_files, socket)
            socket_name = socket[0]

            if (not img == None) and not (not socket_name == 'Displacement' and target_shader_node.inputs[socket_name].is_linked) and not (socket_name == 'Displacement' and output_node.inputs[2].is_linked):
                node = nodes.new(type='ShaderNodeTexImage')
                node.location = (target_shader_node.location.x -
                                 400, target_shader_node.location.y + -300 * index)
                index += 1
                node.label = socket_name
                node.image = img

                if not mapping and not texture_input:
                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (target_shader_node.location.x - 850, 0)

                    # Link texture coord to mapping node
                    texture_input = nodes.new(type='ShaderNodeTexCoord')
                    texture_input.location = (
                        target_shader_node.location.x - 1050, 0)
                    links.new(mapping.inputs[0], texture_input.outputs[2])

                # Link mapping node
                links.new(node.inputs[0], mapping.outputs[0])

                if not socket_name == 'Base Color':
                    node.color_space = 'NONE'

                if not socket_name in ['Displacement', 'Normal']:
                    links.new(
                        target_shader_node.inputs[socket_name], node.outputs[0])

                if socket_name == 'Displacement':
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (
                        node.location.x + 400, node.location.y)
                    # We link the tex node to the displacement node
                    links.new(disp_node.inputs[0], node.outputs[0])
                    # We link the displacement node to the material output node
                    links.new(output_node.inputs[2], disp_node.outputs[0])

                elif socket_name == 'Normal':
                    if extra == 'IS_BUMP':
                        normal_node = nodes.new(type='ShaderNodeBump')
                        links.new(normal_node.inputs[2], node.outputs[0])
                    else:
                        normal_node = nodes.new(type='ShaderNodeNormalMap')
                        links.new(normal_node.inputs[1], node.outputs[0])

                    normal_node.location = (
                        node.location.x + 400, node.location.y)
                    links.new(
                        target_shader_node.inputs[socket_name], normal_node.outputs[0])

                elif socket_name == 'Roughness':
                    if extra == 'IS_GLOSS':
                        invert_node = nodes.new(type='ShaderNodeInvert')
                        links.new(invert_node.inputs[1], node.outputs[0])
                        links.new(
                            target_shader_node.inputs[socket_name], invert_node.outputs[0])

                        invert_node.location = (
                            node.location.x + 400, node.location.y)
                    else:
                        links.new(
                            target_shader_node.inputs[socket_name], node.outputs[0])

    def execute(self, context):
        texture_export_path = Utils.get_textures_export_path(
            context,
            context.scene.taper_configs
        )

        active_obj = bpy.context.view_layer.objects.active
        if len(active_obj.data.materials) == 0:
            self.report({'ERROR'}, "No material found in this selected object")
        else:
            for slot in active_obj.material_slots:
                self.match_material_slot_with_textures(
                    context,
                    texture_export_path,
                    slot.material.name
                )

        return {'FINISHED'}


class SubstanceUpdateTexturesOperator(bpy.types.Operator):
    bl_idname = bl_info["operator_id_prefix"] + ".substance_update_textures"
    bl_label = "Update Substance Painter Textures"

    image_types = ["IMAGE", "TEX_IMAGE", "TEX_ENVIRONMENT", "TEXTURE"]

    @classmethod
    def reload_node_images(self, material_name):
        node_tree = bpy.data.materials[material_name].node_tree
        nodes = node_tree.nodes

        num_reloaded = 0

        for node in nodes:
            if node.type in self.image_types:
                if node.type == "TEXTURE":
                    if node.texture:  # node has texture assigned
                        if node.texture.type in ['IMAGE', 'ENVIRONMENT_MAP']:
                            if node.texture.image:  # texture has image assigned
                                node.texture.image.reload()
                                num_reloaded += 1
                else:
                    if node.image:
                        node.image.reload()
                        num_reloaded += 1

        return num_reloaded

    def execute(self, context):
        active_obj = bpy.context.view_layer.objects.active
        if len(active_obj.data.materials) == 0:
            self.report({'ERROR'}, "No material found in this selected object")
        else:
            for slot in active_obj.material_slots:
                num_reloaded = self.reload_node_images(
                    slot.material.name
                )

                if num_reloaded:
                    self.report({'INFO'}, "Reloaded images")
                    print("Reloaded " + str(num_reloaded) + " images")
                else:
                    self.report(
                        {'WARNING'}, "No images found to reload in this node tree")

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
        configs = scene.taper_configs

        layout.label(text="Painter Path")
        layout.prop(configs, "substance_painter_path", text="")

        layout.label(text="Active Collection")
        row = layout.row()
        row.operator(
            SubstanceLinkOperator.bl_idname,
            text="Send to Painter"
        )
        layout.label(text="Active Selection")
        row = layout.row()
        row.operator(
            SubstancePullTexturesOperator.bl_idname,
            text="Pull Textures"
        )
        row = layout.row()
        row.operator(
            SubstanceUpdateTexturesOperator.bl_idname,
            text="Update Textures"
        )


classes = (
    Configs,
    ExportFBXCollectionsOperator,
    ExportFBXActiveCollectionOperator,
    SubstanceLinkOperator,
    SubstancePullTexturesOperator,
    SubstanceUpdateTexturesOperator,
    TaperExportPanel,
    TaperSubstanceLinkPanel
)

m_register, m_unregister = bpy.utils.register_classes_factory(classes)


def register():
    m_register()
    bpy.types.Scene.taper_configs = PointerProperty(type=Configs)


def unregister():
    del bpy.types.Scene.taper_configs
    m_unregister()
