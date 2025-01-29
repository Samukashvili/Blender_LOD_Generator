bl_info = {
    "name": "LOD Generator",
    "author": "Your Name",
    "version": (1, 2),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > LOD Tools",
    "description": "Advanced LOD generation with texture handling",
    "warning": "",
    "category": "Object",
}

import bpy
import os
from bpy.types import Operator, Panel
from bpy.props import IntProperty, FloatProperty, BoolProperty

class LODGeneratorProperties(bpy.types.PropertyGroup):
    num_lods: IntProperty(
        name="Number of LODs",
        default=3,
        min=1,
        max=10
    )
    face_reduction: FloatProperty(
        name="Face Reduction (%)",
        default=50.0,
        min=1.0,
        max=99.0,
        subtype='PERCENTAGE'
    )
    process_textures: BoolProperty(
        name="Resize Textures",
        default=True
    )

class LODGeneratorPanel(Panel):
    bl_label = "LOD Generator"
    bl_idname = "OBJECT_PT_lod_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LOD Tools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.lod_props
        
        col = layout.column()
        col.prop(props, "num_lods")
        col.prop(props, "face_reduction")
        col.prop(props, "process_textures")
        layout.operator("object.generate_lods")

class OBJECT_OT_GenerateLODs(Operator):
    bl_label = "Generate LODs"
    bl_idname = "object.generate_lods"
    bl_options = {'REGISTER', 'UNDO'}

    def create_lod_folder(self, lod_level):
        blend_path = bpy.path.abspath("//")
        if not blend_path:
            self.report({'ERROR'}, "Save your blend file first")
            return None
            
        lod_folder = os.path.join(blend_path, f"LOD{lod_level}")
        os.makedirs(lod_folder, exist_ok=True)
        return lod_folder

    def resize_texture(self, img, lod_folder, lod_level, reduction):
        if img.source != 'FILE' or not img.filepath:
            return None

        original_path = bpy.path.abspath(img.filepath)
        if not original_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return None

        # Calculate new dimensions
        orig_width, orig_height = img.size
        new_width = max(1, int(orig_width * (1 - reduction)))
        new_height = max(1, int(orig_height * (1 - reduction)))

        # Create new image
        new_img = bpy.data.images.new(
            name=f"{img.name}_LOD{lod_level}",
            width=new_width,
            height=new_height
        )
        
        try:
            # Copy and scale original image data
            img.scale(new_width, new_height)
            new_img.pixels = img.pixels[:]
            img.reload()
        except:
            self.report({'WARNING'}, f"Couldn't resize {img.name}")
            return None

        # Save settings
        ext = os.path.splitext(img.filepath)[1].lower()
        new_img.file_format = 'PNG' if ext == '.png' else 'JPEG'
        new_path = os.path.join(lod_folder, f"{img.name}_LOD{lod_level}{ext}")
        new_img.filepath_raw = new_path
        new_img.save()
        
        return new_img

    def execute(self, context):
        props = context.scene.lod_props
        original_obj = context.active_object

        if not original_obj or original_obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}

        if context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        reduction = props.face_reduction / 100.0

        for lod in range(1, props.num_lods + 1):
            # Duplicate object
            bpy.ops.object.select_all(action='DESELECT')
            original_obj.select_set(True)
            context.view_layer.objects.active = original_obj
            bpy.ops.object.duplicate()
            lod_obj = context.active_object
            lod_obj.name = f"{original_obj.name}_LOD{lod}"

            # Apply progressive decimation
            cumulative_ratio = (1 - reduction) ** lod
            mod = lod_obj.modifiers.new(name="Decimate", type='DECIMATE')
            mod.ratio = cumulative_ratio
            
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                self.report({'ERROR'}, f"Modifier error: {str(e)}")
                return {'CANCELLED'}

            # Handle materials and textures
            if props.process_textures:
                lod_folder = self.create_lod_folder(lod)
                if not lod_folder:
                    continue

                for mat_slot in lod_obj.material_slots:
                    if not mat_slot.material:
                        continue

                    # Duplicate material
                    new_mat = mat_slot.material.copy()
                    new_mat.name = f"{mat_slot.material.name}_LOD{lod}"
                    mat_slot.material = new_mat

                    if not new_mat.use_nodes:
                        continue

                    # Process all texture nodes
                    for node in new_mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            original_img = node.image
                            new_img = self.resize_texture(original_img, lod_folder, lod, reduction)
                            if new_img:
                                node.image = new_img

        return {'FINISHED'}

classes = (
    LODGeneratorProperties,
    LODGeneratorPanel,
    OBJECT_OT_GenerateLODs,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lod_props = bpy.props.PointerProperty(type=LODGeneratorProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lod_props

if __name__ == "__main__":
    register()