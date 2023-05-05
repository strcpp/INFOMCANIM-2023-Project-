class Animation:
    def __init__(self, name, duration,root_bone):
        self.name = name
        self.duration = duration

        #storing bones as a node hierarchy,
        #maybe it's better to store as a list instead? I think this is fine, we have to traverse the hierarchy eventually anyway.
        self.root_bone = root_bone

    #just testing to make sure we're loading the animation data correctly
    def assert_channels_not_empty(self, bone=None):
        if bone is None:
            bone = self.root_bone

        if not bone.rotations:
            raise ValueError("Rotations channel is empty in bone: {}".format(bone.name))
        if not bone.scales:
            raise ValueError("Scales channel is empty in bone: {}".format(bone.name))
        if not bone.translations:
            raise ValueError("Translations channel is empty in bone: {}".format(bone.name))

        if bone.children:
            for child_bone in bone.children:
                self.assert_channels_not_empty(child_bone)