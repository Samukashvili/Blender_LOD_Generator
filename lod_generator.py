bl_info = {
    "name": "LOD Generator",
    "author": "Your Name",
    "version": (1, 9),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > LOD Tools",
    "description": "Advanced LOD generation with robust texture handling",
    "warning": "",
    "category": "Object",
}

import bpy
import os
from bpy.types import Operator, Panel
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

class LODGeneratorProperties(bpy.types.PropertyGroup):
    num_lods: IntProperty(
        name="Number of LODs",
        default=3,
        min=1,
        max=10
    )
    face_reduction: FloatProperty(
        name="Reduction per LOD (%)",
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
        layout.prop(props, "num_lods")
        layout.prop(props, "face_reduction")
        layout.prop(props, "process_textures")
        layout.operator("object.generate_lods")

class OBJECT_OT_GenerateLODs(Operator):
    bl_label = "Generate LODs"
    bl_idname = "object.generate_lods"
    bl_options = {'REGISTER', 'UNDO'}

    texture_action: EnumProperty(
        items=[('REPLACE', "Replace", "Overwrite existing textures"),
               ('SKIP', "Skip", "Keep existing textures")],
        default='REPLACE'
    )

    def invoke(self, context, event):
        # Show initial warning
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        if not hasattr(self, 'existing_files'):
            # First dialog: Warning message
            layout.label(text="This operation may freeze Blender!", icon='ERROR')
            layout.label(text="Recommended:", icon='BLANK1')
            layout.label(text="1. Save your work first")
            layout.label(text="2. Close other applications")
            layout.label(text="3. Be patient during processing")
        else:
            # Second dialog: Texture replacement
            layout.label(text="Existing textures found:", icon='ERROR')
            col = layout.column(align=True)
            col.scale_y = 0.7
            for f in self.existing_files[:3]:
                col.label(text=os.path.basename(f))
            if len(self.existing_files) > 3:
                col.label(text=f"...and {len(self.existing_files)-3} more")
            layout.separator()
            layout.prop(self, "texture_action", expand=True)

    def check_existing_files(self, context):
        props = context.scene.lod_props
        blend_path = bpy.path.abspath("//")
        existing_files = []

        for lod in range(1, props.num_lods + 1):
            lod_folder = os.path.join(blend_path, f"LOD{lod}")
            if os.path.exists(lod_folder):
                for file in os.listdir(lod_folder):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        existing_files.append(os.path.join(lod_folder, file))
        return existing_files

    def execute(self, context):
        if not hasattr(self, 'existing_files'):
            # First execution: Show texture replacement dialog
            self.existing_files = self.check_existing_files(context)
            if self.existing_files and context.scene.lod_props.process_textures:
                return context.window_manager.invoke_props_dialog(self, width=400)
            else:
                return self._process_lods(context)
        else:
            # Second execution: Process LODs
            return self._process_lods(context)

    def _process_lods(self, context):
        props = context.scene.lod_props
        original_obj = context.active_object
        reduction = props.face_reduction / 100.0

        if context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        current_base = original_obj
        for lod in range(1, props.num_lods + 1):
            # Duplicate object
            current_base.select_set(True)
            context.view_layer.objects.active = current_base
            bpy.ops.object.duplicate()
            lod_obj = context.active_object
            lod_obj.name = f"{original_obj.name}_LOD{lod}"

            # Apply decimate modifier
            mod = lod_obj.modifiers.new(name="Decimate", type='DECIMATE')
            mod.ratio = 1 - reduction
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                self.report({'ERROR'}, f"Modifier error: {str(e)}")
                return {'CANCELLED'}

            # Process textures
            if props.process_textures:
                self._process_textures(lod_obj, lod, reduction)

            current_base = lod_obj

        self.report({'INFO'}, "LOD generation completed!")
        return {'FINISHED'}

    def _process_textures(self, lod_obj, lod_level, reduction):
        blend_path = bpy.path.abspath("//")
        lod_folder = os.path.join(blend_path, f"LOD{lod_level}")
        os.makedirs(lod_folder, exist_ok=True)

        for mat_slot in lod_obj.material_slots:
            if not mat_slot.material or not mat_slot.material.use_nodes:
                continue

            # Duplicate material
            new_mat = mat_slot.material.copy()
            new_mat.name = f"{mat_slot.material.name}_LOD{lod_level}"
            mat_slot.material = new_mat

            # Process texture nodes
            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    self._resize_texture(node.image, lod_folder, lod_level, reduction)

    def _resize_texture(self, img, lod_folder, lod_level, reduction):
        # Handle packed textures and special names
        try:
            # Get base name from image name instead of filepath
            base_name = img.name
            
            # Sanitize filename (remove special characters)
            valid_chars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            sanitized_name = ''.join(c for c in base_name if c in valid_chars)
            if not sanitized_name:
                sanitized_name = f"texture_{lod_level}"

            # Handle different image sources
            if img.source == 'TILED':
                # Special handling for UV-tiled textures
                sanitized_name = f"uvtile_{sanitized_name}"
                ext = ".png"  # default for tiled textures
            else:
                # Get extension from original file or default to PNG
                ext = os.path.splitext(img.filepath)[1].lower() if img.filepath else ".png"
                if ext not in ('.png', '.jpg', '.jpeg'):
                    ext = ".png"

            # Create target filename
            target_name = f"{sanitized_name}_LOD{lod_level}{ext}"
            target_path = os.path.join(lod_folder, target_name)

            # Skip existing files if requested
            if os.path.exists(target_path) and self.texture_action == 'SKIP':
                return

            # Calculate dimensions with aspect ratio preservation
            orig_width, orig_height = img.size
            new_width = max(512, int(orig_width * (1 - reduction)))
            new_height = max(512, int(orig_height * (1 - reduction)))

            # Maintain aspect ratio
            aspect = orig_width / orig_height
            if new_width / new_height > aspect:
                new_height = max(512, int(new_width / aspect))
            else:
                new_width = max(512, int(new_height * aspect))

            # Create new image
            new_img = bpy.data.images.new(
                name=f"{sanitized_name}_LOD{lod_level}",
                width=new_width,
                height=new_height
            )

            # Copy and scale pixel data
            img.scale(new_width, new_height)
            new_img.pixels = img.pixels[:]
            img.reload()

            # Save settings
            new_img.filepath_raw = target_path
            new_img.file_format = 'PNG' if ext == '.png' else 'JPEG'
            new_img.save()

            # Replace reference in material
            return new_img

        except Exception as e:
            print(f"Error processing texture {img.name}: {str(e)}")
            self.report({'WARNING'}, f"Skipped {img.name} (see console for details)")
            return None

classes = (LODGeneratorProperties, LODGeneratorPanel, OBJECT_OT_GenerateLODs)

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