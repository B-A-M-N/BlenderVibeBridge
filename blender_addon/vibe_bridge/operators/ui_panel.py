# BlenderVibeBridge: Vibe Panel (v1.5.0)
import bpy
import os
import json

class VIBE_PT_Panel(bpy.types.Panel):
    bl_label = "Vibe Bridge Control"
    bl_idname = "VIBE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VibeBridge'

    def draw(self, context):
        layout = self.layout
        
        # Intent Display
        activity_path = "/home/bamn/BlenderVibeBridge/metadata/bridge_activity.txt"
        intent = "IDLE"
        if os.path.exists(activity_path):
            with open(activity_path, "r") as f:
                intent = f.read().strip()
        
        box = layout.box()
        box.label(text=f"Current Intent: {intent}", icon='INFO')
        
        # Approval Gates
        row = layout.row(align=True)
        row.operator("vibe.approve_mutation", text="APPROVE", icon='CHECKMARK')
        row.operator("vibe.reject_mutation", text="REJECT", icon='CANCEL')

class VIBE_OT_Approve(bpy.types.Operator):
    bl_idname = "vibe.approve_mutation"
    bl_label = "Approve Mutation"
    
    def execute(self, context):
        with open("/home/bamn/BlenderVibeBridge/vibe_queue/kernel/approval.txt", "w") as f:
            f.write("APPROVED")
        return {'FINISHED'}

class VIBE_OT_Capture(bpy.types.Operator):
    """Captures a high-speed viewport thumbnail for AI feedback."""
    bl_idname = "vibe.capture_viewport"
    bl_label = "Capture Viewport"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        # Off-screen render for non-blocking feedback
        scene = context.scene
        scene.render.filepath = self.filepath
        bpy.ops.render.opengl(write_still=True)
        return {'FINISHED'}

class VIBE_OT_Reject(bpy.types.Operator):
    bl_idname = "vibe.reject_mutation"
    bl_label = "Reject Mutation"
    
    def execute(self, context):
        with open("/home/bamn/BlenderVibeBridge/vibe_queue/kernel/approval.txt", "w") as f:
            f.write("REJECTED")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(VIBE_PT_Panel)
    bpy.utils.register_class(VIBE_OT_Approve)
    bpy.utils.register_class(VIBE_OT_Reject)
    bpy.utils.register_class(VIBE_OT_Capture)

def unregister():
    bpy.utils.unregister_class(VIBE_PT_Panel)
    bpy.utils.unregister_class(VIBE_OT_Approve)
    bpy.utils.unregister_class(VIBE_OT_Reject)
    bpy.utils.unregister_class(VIBE_OT_Capture)
