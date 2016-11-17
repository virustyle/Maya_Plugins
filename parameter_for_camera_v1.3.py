import maya.cmds as maya

maya.window(title = 'MatchMove Tool  v1.3',w=500,h=170)
maya.rowColumnLayout(numberOfColumns=2,columnAttach=[1,"right",0],columnWidth=[[1,100],[2,400]])

################################################################################################################
####################################################序列路径修改################################################
################################################################################################################

maya.text(label="Input Image File",align = 'right',font = 'boldLabelFont')

file = maya.textField()

commandstr = 'filename = maya.fileDialog2(fileMode=1, caption="Import Image");\
    maya.textField(file,edit=True,w=400,fi=filename[0])'

maya.textField(file,edit=True,w=400,fi='R:/filmServe',dgc = commandstr)

maya.text(label="Frame Cahe")
cacheframe = maya.intSliderGrp(field = True, v = 100 , minValue=0 , maxValue=1000 , fieldMinValue=0 , fieldMaxValue=5000)


maya.text(label="On/Off")
maya.checkBox(l = 'Use Image Sequence',onCommand = 'maya.setAttr(thisImagePlane+".useFrameExtension",1)',\
offCommand = 'maya.setAttr(thisImagePlane+".useFrameExtension",0)')



cameralist = maya.listCameras()                                                                         #获得当前相机列表
cameralist.remove('persp');cameralist.remove('front');cameralist.remove('top');cameralist.remove('side');
cameralist.reverse()
eistr = []
for i in cameralist:
	eistr.append([cameralist.index(i),i])                                                               #获得ei字符串

cameraenum = maya.attrEnumOptionMenu(w = 100, ei = eistr)                                               #建立一个下拉框显示过滤后的camera
cameraindex = maya.attrEnumOptionMenu(cameraenum,q=1,npm=True)

for i in eistr:
	if i[0] == cameraindex:
		thisCamera = i[1]                                                                               #获得当前camera
		break

if maya.imagePlane(thisCamera,q= 1,camera=True):
    thisImagePlane = maya.imagePlane(thisCamera,q = 1,n = True)[0]                                          #获得当前plane
else:
	maya.imagePlane(thisCamera,camera=thisCamera)
	thisImagePlane = maya.imagePlane(thisCamera,q = 1,n = True)[0]                                          #获得当前plane


maya.button(label="Replace sequence",w = 100,command = 'selected_node = maya.ls(sl=1);\
file_value = maya.textField(file,q = 1,tx = 1);\
picture = maya.getFileList(folder = file_value)[1] if file_value.find(".") == -1 else "";\
maya.setAttr(thisImagePlane+".imageName",file_value + picture,type="string");\
framecache_value = maya.intSliderGrp(cacheframe,q=True,v = True);\
maya.setAttr(thisImagePlane+".frameCache",framecache_value);\
imageSizelist = maya.imagePlane(thisCamera,q=1,imageSize=1);\
maya.textField(targetsizewidth,tx = imageSizelist[0] ,w=100,edit=True,enterCommand=("maya.setFocus(\'" + targetsizeheight + "\')"));\
maya.textField(targetsizeheight,tx = imageSizelist[1] ,w=100,edit=True,enterCommand=("maya.setFocus(\'" + sourcesizewidth + "\')"));\
')




################################################################################################################
####################################################具体参数修改################################################
################################################################################################################

maya.text(label="")
maya.text(label="")
maya.text(label="")
maya.text(label="")

maya.text(label="Input Source Size",font = 'boldLabelFont')
maya.text(label="")
sourcesizewidth = maya.textField()
sourcesizeheight = maya.textField()

maya.text(label="")
maya.text(label="")

#maya.text(label="Input Source Aperture(mm)",font = 'boldLabelFont')
#maya.text(label="")
sourceApeH = maya.textField()
sourceApeV = maya.textField()

#maya.text(label="")
#maya.text(label="")

maya.text(label="Input Target Size",font = 'boldLabelFont')
maya.text(label="")
targetsizewidth = maya.textField()
targetsizeheight = maya.textField()



Rwidth = maya.getAttr("defaultResolution.width")
Rheight = maya.getAttr("defaultResolution.height")
horizontalFilmAperture = maya.getAttr(thisCamera+"Shape.horizontalFilmAperture")
verticalFilmAperture = maya.getAttr(thisCamera+"Shape.verticalFilmAperture")


#imageSizelist = maya.imagePlane(thisCamera,q=1,imageSize=1)

maya.textField(sourcesizewidth,tx=Rwidth,w=100,edit=True,enterCommand=('maya.setFocus(\"' + sourcesizeheight + '\")'))
maya.textField(sourcesizeheight,tx=Rheight,w=100,edit=True,enterCommand=('maya.setFocus(\"' + sourceApeH + '\")'))
maya.textField(sourceApeH,tx=horizontalFilmAperture,w=100,edit=True,enterCommand=('maya.setFocus(\"' + sourceApeV + '\")'))
maya.textField(sourceApeV,tx=verticalFilmAperture,w=100,edit=True,enterCommand=('maya.setFocus(\"' + targetsizewidth + '\")'))
maya.textField(targetsizewidth,tx = 'input target width' ,w=100,edit=True,enterCommand=('maya.setFocus(\"' + targetsizeheight + '\")'))
maya.textField(targetsizeheight,tx = 'input target height' ,w=100,edit=True,enterCommand=('maya.setFocus(\"' + sourcesizewidth + '\")'))



              

maya.button(label="Default Size",w=100,command = 'selected_node = maya.ls(sl=1);\
	sourcesizewidth_value = maya.textField(sourcesizewidth,q = 1,tx = 1);\
	sourcesizeheight_value = maya.textField(sourcesizeheight,q = 1,tx = 1);\
    maya.setAttr(thisCamera+"Shape.horizontalFilmAperture",horizontalFilmAperture);\
	maya.setAttr(thisCamera+"Shape.verticalFilmAperture",verticalFilmAperture);\
	maya.setAttr("defaultResolution.width",int(sourcesizewidth_value));\
	maya.setAttr("defaultResolution.height",int(sourcesizeheight_value));\
	maya.setAttr(thisImagePlane+".sizeX",horizontalFilmAperture);\
	maya.setAttr(thisImagePlane+".sizeY",verticalFilmAperture);\
	')

maya.button(label="Go",w = 100,command = 'selected_node = maya.ls(sl=1);\
	sourcesizewidth_value = maya.textField(sourcesizewidth,q = 1,tx = 1);\
	sourcesizeheight_value = maya.textField(sourcesizeheight,q = 1,tx = 1);\
	targetsizewidth_value = maya.textField(targetsizewidth,q = 1,tx = 1);\
	targetsizeheight_value = maya.textField(targetsizeheight,q = 1,tx = 1);\
	maya.setAttr("defaultResolution.width",int(targetsizewidth_value));\
	maya.setAttr("defaultResolution.height",int(targetsizeheight_value));\
	agr_val = float(targetsizewidth_value)/float(sourcesizewidth_value);\
	horizon = maya.getAttr(thisCamera+"Shape.horizontalFilmAperture");\
	vertical = maya.getAttr(thisCamera+"Shape.verticalFilmAperture");\
	maya.setAttr(thisCamera+"Shape.horizontalFilmAperture",horizon*agr_val);\
	maya.setAttr(thisCamera+"Shape.verticalFilmAperture",vertical*agr_val);\
	maya.setAttr(thisImagePlane+".sizeX",horizon*agr_val);\
	maya.setAttr(thisImagePlane+".sizeY",vertical*agr_val);\
	')



maya.text(label="")
maya.text(label="")

maya.text(label="")
maya.text(label="")

maya.text(label="InputAspectRatio",font = 'boldLabelFont')
maya.text(label="")

defaultpixelaspectratio = maya.getAttr("defaultResolution.pixelAspect")
defaultdeviceaspectratio = maya.getAttr("defaultResolution.deviceAspectRatio")

#complete the creating of maintain width/height ratio
maya.text(label="Lock Aspect")
maya.setAttr("defaultResolution.aspectLock",0)
maya.checkBox(l = 'maintain width/height ratio',onCommand = 'maya.setAttr("defaultResolution.aspectLock",1)',\
	offCommand = 'maya.setAttr("defaultResolution.aspectLock",0)')



maya.text(label="Pixel Aspect Ratio")

maya.rowColumnLayout(numberOfColumns=3,columnAttach=[1,"right",0])

PixelAspectRatio = maya.textField()

maya.button(label="SetValue",w = 60,command = 'pixelAspectvalue = maya.textField(PixelAspectRatio,q = 1,tx = 1);\
	maya.setAttr("defaultResolution.pixelAspect",float(pixelAspectvalue));\
	maya.setAttr("defaultResolution.deviceAspectRatio",defaultdeviceaspectratio*float(pixelAspectvalue)/defaultpixelaspectratio)')
maya.button(label="Restore",w = 60,command = 'maya.setAttr("defaultResolution.pixelAspect",defaultpixelaspectratio);\
	maya.setAttr("defaultResolution.deviceAspectRatio",defaultdeviceaspectratio)')

#complete the creating of pixel aspect ratio
#targetsizewidth_value = float(maya.textField(targetsizewidth,q = 1,tx = 1))
#targetsizeheight_value = float(maya.textField(targetsizeheight,q = 1,tx = 1))
#correctvalue = targetsizewidth_value/(targetsizeheight_value*float(defaultdeviceaspectratio))

maya.textField(PixelAspectRatio,tx = float(defaultpixelaspectratio),edit = True,enterCommand = 'pixelAspectvalue = maya.textField(PixelAspectRatio,q = 1,tx = 1);\
	maya.setAttr("defaultResolution.pixelAspect",float(pixelAspectvalue));\
	')




maya.showWindow()

################################################################################################################
################################################################################################################
###################################################################################Write By Sol He##############
################################################################################################################
################################################################################################################