import nuke

a = nuke.createNode('Read'   ,r'file {R:\filmServe\RnD\matchmove\98_pipeline\shoot_Tool\2048x1152_JPG\ERD_0090.####.JPG}')
a.knob('first').setValue(1001)
a.knob('last').setValue(1109)

b = nuke.createNode('Camera2',r'file {R:\filmServe\RnD\matchmove\98_pipeline\shoot_Tool\JZZ_SJG29_trk_test_wire_Kiro_v001.nk}')
b.knob('frame_rate').setValue(25)
b.knob('read_from_file').setValue(1)
b.knob('use_frame_rate').setValue(1)
c = nuke.createNode('Wireframe')
c.knob('line_color_panelDropped').setValue(1)

d = nuke.createNode('ReadGeo2',r'file {R:\filmServe\RnD\matchmove\98_pipeline\shoot_Tool\JZZ_SJG29_trk_test_wire_Kiro_v001.abc}')
d.setInput(0,c)
d.knob('frame_rate').setValue(25)
d.knob('range_first').setValue(1001)
d.knob('range_last').setValue(1109)

e = nuke.createNode('ScanlineRender')
e.setInput(0,b)
e.setInput(1,d)
e.setInput(2,a)

nuke.scriptSaveAs(r'R:\filmServe\RnD\matchmove\98_pipeline\shoot_Tool\111.nk')