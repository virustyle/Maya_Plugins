#
#
# 3DE4.script.name: Maya...
#
# 3DE4.script.version:  v1.9
#
# 3DE4.script.gui:  Main Window::3DE4::Export Project
#
# 3DE4.script.comment:  Creates a MEL script file that contains all project data, which can be imported into Autodesk Maya.
#
#

#
# import sdv's python vector lib...

from vl_sdv import *
import os,tde4
#
# functions...

def convertToAngles(r3d):
    rot = rot3d(mat3d(r3d)).angles(VL_APPLY_ZXY)
    rx  = (rot[0]*180.0)/3.141592654
    ry  = (rot[1]*180.0)/3.141592654
    rz  = (rot[2]*180.0)/3.141592654
    return(rx,ry,rz)


def convertZup(p3d,yup):
    if yup==1:
        return(p3d)
    else:
        return([p3d[0],-p3d[2],p3d[1]])


def angleMod360(d0,d):
    dd  = d-d0
    if dd>180.0:
        d   = angleMod360(d0,d-360.0)
    else:
        if dd<-180.0:
            d   = angleMod360(d0,d+360.0)
    return d


def validName(name):
    name    = name.replace(" ","_")
    name    = name.replace("\n","")
    name    = name.replace("\r","")
    return name


def prepareImagePath(path,startframe):
    path    = path.replace("\\","/")
    i   = 0
    n   = 0
    i0  = -1
    while(i<len(path)):
        if path[i]=='#': n += 1
        if n==1: i0 = i
        i   += 1
    if i0!=-1:
        fstring     = "%%s%%0%dd%%s"%(n)
        path2       = fstring%(path[0:i0],startframe,path[i0+n:len(path)])
        path        = path2
    return path
    
#
# main script...
projectPath = tde4.getProjectPath()
projectName = os.path.basename(projectPath)
ShotName    = projectName.split('_')[1]
#
# search for camera point group...

campg   = None
pgl = tde4.getPGroupList()
for pg in pgl:
    if tde4.getPGroupType(pg)=="CAMERA": campg = pg
if campg==None:
    tde4.postQuestionRequester("Export Maya...","Error, there is no camera point group.","Ok")


#
# open requester...

try:
    req = _export_requester_maya
except (ValueError,NameError,TypeError):
    _export_requester_maya  = tde4.createCustomRequester()
    req         = _export_requester_maya
    tde4.addFileWidget(req,"file_browser","Exportfile...","*.mel")
    tde4.addTextFieldWidget(req, "startframe_field", "Startframe", "1")
    # tde4.addOptionMenuWidget(req,"mode_menu","Orientation","Y-Up", "Z-Up")
    tde4.addToggleWidget(req,"hide_ref_frames","Hide Reference Frames",0)

cam = tde4.getCurrentCamera()
offset  = tde4.getCameraFrameOffset(cam)
tde4.setWidgetValue(req,"startframe_field",str(offset))

FootageWidth         = tde4.getCameraImageWidth(cam)
FootageHeight        = tde4.getCameraImageHeight(cam)


lens = tde4.getFirstLens()
CameraApertureWidth  = tde4.getLensFBackWidth(lens)/2.54
CameraApertureHeight = tde4.getLensFBackHeight(lens)/2.54



#about lens distortion.
LensDistortionValid = False
camList = tde4.getCameraList()
for cam in camList:
    lens = tde4.getCameraLens(cam)
    for id in tde4.getLensList():
        focus = tde4.getLensFocalLength(id)
        lensmodel = tde4.getLensLDModel(id)
        focallength = tde4.getLensFocalLength(id)
        paraNumber = tde4.getLDModelNoParameters(lensmodel)
        for i in range(paraNumber):
            paraName = tde4.getLDModelParameterName(lensmodel,i)
            currentValue = tde4.getLensLDAdjustableParameter(id,paraName,focus)
            defaultValue = tde4.getLDModelParameterDefault(lensmodel,paraName)
            if currentValue != defaultValue:
                LensDistortionValid = True
                break
            
        


ret = tde4.postCustomRequester(req,"Export Maya (MEL-Script)...",600,0,"Ok","Cancel")
if ret==1:
    # yup   = tde4.getWidgetValue(req,"mode_menu")
    # if yup==2: yup = 0
    yup = 1
    path    = tde4.getWidgetValue(req,"file_browser")
    frame0  = float(tde4.getWidgetValue(req,"startframe_field"))
    frame0  -= 1
    hide_ref= tde4.getWidgetValue(req,"hide_ref_frames")
    if path!=None:
        if not path.endswith('.mel'): path = path+'.mel' 
        f   = open(path,"w")
        if not f.closed:
            
            #
            # write some comments...
            
            f.write("//\n")
            f.write("// Maya/MEL export data written by %s\n"%tde4.get3DEVersion())
            f.write("//\n")
            f.write("// All lengths are in centimeter, all angles are in degree.\n")
            f.write("//\n\n")

            #
            # write scene group...

            f.write("// create scene group...\n")
            f.write("string $sceneGroupName = `group -em -name \"trk_track\"`;\n")


            f.write("createDisplayLayer -name \"loc_all\" -number 1 -empty;\n")
            f.write("setAttr loc_all.visibility 1; setAttr loc_all.displayType 0; setAttr loc_all.color 6;\n")
            f.write("createDisplayLayer -name \"marker\" -number 1 -empty;\n")
            f.write("setAttr marker.visibility 1; setAttr marker.displayType 0; setAttr marker.color 13;\n")
            f.write("createDisplayLayer -name \"meshMP\" -number 1 -empty;\n")
            f.write("createDisplayLayer -name \"mesh\" -number 1 -empty;\n")
            f.write("createDisplayLayer -name \"ground\" -number 1 -empty;\n")
            f.write("createDisplayLayer -name \"scan\" -number 1 -empty;\n")
            f.write("select -cl;doGroup 0 1 1;\n")
            f.write("rename \"null1\" \"trk_marker\";\n")
            f.write("parent trk_marker trk_track ;\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"trk_marker\" + \"*\" + \".sz\");\n")
            #
            # write cameras...
            
            cl  = tde4.getCameraList()
            index   = 1
            for cam in cl:
                camType     = tde4.getCameraType(cam)
                noframes    = tde4.getCameraNoFrames(cam)
                lens        = tde4.getCameraLens(cam)
                if lens!=None:
                    name        = validName(tde4.getCameraName(cam))
                    if tde4.getCameraStereoOrientation(cam)   == 'STEREO_LEFT' and tde4.getCameraStereoMode(cam) != 'STEREO_OFF':
                        name = ShotName + '_trk_camLeft'
                    elif tde4.getCameraStereoOrientation(cam) == 'STEREO_RIGHT' and tde4.getCameraStereoMode(cam) != 'STEREO_OFF':
                        name = ShotName + '_trk_camRight'
                    else:
                        name = ShotName + '_trk_cam'
                    #name       = "%s_%s_1"%(name,index)
                    index       += 1
                    fback_w     = tde4.getLensFBackWidth(lens)
                    fback_h     = tde4.getLensFBackHeight(lens)
                    p_aspect    = tde4.getLensPixelAspect(lens)
                    focal       = tde4.getCameraFocalLength(cam,1)
                    lco_x       = tde4.getLensLensCenterX(lens)
                    lco_y       = tde4.getLensLensCenterY(lens)

                    # convert filmback to inch...
                    fback_w     = fback_w/2.54
                    fback_h     = fback_h/2.54
                    lco_x       = -lco_x/2.54
                    lco_y       = -lco_y/2.54

                    # convert focal length to mm...
                    focal       = focal*10.0

                    # create camera...
                    f.write("\n")
                    f.write("// create camera %s...\n"%name)
                    f.write("string $cameraNodes[] = `camera -name \"%s\" -hfa %.15f  -vfa %.15f -fl %.15f -ncp 0.01 -fcp 10000 -shutterAngle 180 -ff \"overscan\"`;\n"%(name,fback_w,fback_h,focal))
                    f.write("string $cameraTransform = $cameraNodes[0];\n")
                    f.write("string $cameraShape = $cameraNodes[1];\n")
                    f.write("xform -zeroTransformPivots -rotateOrder zxy $cameraTransform;\n")
                    f.write("setAttr ($cameraShape+\".horizontalFilmOffset\") %.15f;\n"%lco_x)
                    f.write("setAttr ($cameraShape+\".verticalFilmOffset\") %.15f;\n"%lco_y)

                    if LensDistortionValid:
                        f.write("setAttr ($cameraShape+\".horizontalFilmAperture\") %.15f;\n"%(CameraApertureWidth*1.1))
                        f.write("setAttr ($cameraShape+\".verticalFilmAperture\") %.15f;\n"%(CameraApertureHeight*1.1))
                    else:
                        f.write("setAttr ($cameraShape+\".horizontalFilmAperture\") %.15f;\n"%CameraApertureWidth)
                        f.write("setAttr ($cameraShape+\".verticalFilmAperture\") %.15f;\n"%CameraApertureHeight)

                    p3d = tde4.getPGroupPosition3D(campg,cam,1)
                    p3d = convertZup(p3d,yup)
                    f.write("xform -translation %.15f %.15f %.15f $cameraTransform;\n"%(p3d[0],p3d[1],p3d[2]))
                    r3d = tde4.getPGroupRotation3D(campg,cam,1)
                    rot = convertToAngles(r3d)
                    f.write("xform -rotation %.15f %.15f %.15f $cameraTransform;\n"%rot)
                    f.write("xform -scale 1 1 1 $cameraTransform;\n")



                    # image plane...
                    f.write("\n")
                    f.write("// create image plane...\n")
                    f.write("string $imagePlane = `createNode imagePlane`;\n")
                    f.write("cameraImagePlaneUpdate ($cameraShape, $imagePlane);\n")
                    f.write("setAttr ($imagePlane + \".offsetX\") %.15f;\n"%lco_x)
                    f.write("setAttr ($imagePlane + \".offsetY\") %.15f;\n"%lco_y)

                    if camType=="SEQUENCE": f.write("setAttr ($imagePlane+\".useFrameExtension\") 1;\n")
                    else:           f.write("setAttr ($imagePlane+\".useFrameExtension\") 0;\n")

                    f.write("expression -n \"frame_ext_expression\" -s ($imagePlane+\".frameExtension=frame\");\n")
                    path    = tde4.getCameraPath(cam)
                    sattr   = tde4.getCameraSequenceAttr(cam)
                    path    = prepareImagePath(path,sattr[0])
                    f.write("setAttr ($imagePlane + \".imageName\") -type \"string\" \"%s\";\n"%(path))
                    f.write("setAttr ($imagePlane + \".fit\") 4;\n")
                    f.write("setAttr ($imagePlane + \".displayOnlyIfCurrent\") 1;\n")
                    f.write("setAttr ($imagePlane  + \".depth\") (9000/2);\n")

                    # parent camera to scene group...
                    f.write("\n")
                    f.write("// parent camera to scene group...\n")
                    f.write("parent $cameraTransform $sceneGroupName;\n")

                    if camType=="REF_FRAME" and hide_ref:
                        f.write("setAttr ($cameraTransform +\".visibility\") 0;\n")

                    # animate camera...
                    if camType!="REF_FRAME":
                        f.write("\n")
                        f.write("// animating camera %s...\n"%name)
                        f.write("playbackOptions -min %d -max %d;\n"%(1+frame0,noframes+frame0))
                        f.write("\n")
                    
                    

                    frame   = 1
                    while frame<=noframes:
                        # rot/pos...
                        p3d = tde4.getPGroupPosition3D(campg,cam,frame)
                        p3d = convertZup(p3d,yup)
                        r3d = tde4.getPGroupRotation3D(campg,cam,frame)
                        rot = convertToAngles(r3d)
                        if frame>1:
                            rot = [ angleMod360(rot0[0],rot[0]), angleMod360(rot0[1],rot[1]), angleMod360(rot0[2],rot[2]) ]
                        rot0    = rot
                        f.write("setKeyframe -at translateX -t %d -v %.15f $cameraTransform; "%(frame+frame0,p3d[0]))
                        f.write("setKeyframe -at translateY -t %d -v %.15f $cameraTransform; "%(frame+frame0,p3d[1]))
                        f.write("setKeyframe -at translateZ -t %d -v %.15f $cameraTransform; "%(frame+frame0,p3d[2]))
                        f.write("setKeyframe -at rotateX -t %d -v %.15f $cameraTransform; "%(frame+frame0,rot[0]))
                        f.write("setKeyframe -at rotateY -t %d -v %.15f $cameraTransform; "%(frame+frame0,rot[1]))
                        f.write("setKeyframe -at rotateZ -t %d -v %.15f $cameraTransform; "%(frame+frame0,rot[2]))
                        
                        # focal length...
                        focal   = tde4.getCameraFocalLength(cam,frame)
                        focal   = focal*10.0
                        f.write("setKeyframe -at focalLength -t %d -v %.15f $cameraShape;\n"%(frame+frame0,focal))
                        
                        frame   += 1

                    f.write("rename \"%s\" \"%s\";\n"%(name + str(1),name))

                    f.write("select -cl;\n")

                    f.write("setAttr \"%sShape.nearClipPlane\" 1;\n"%name)
                    f.write("setAttr \"%sShape.farClipPlane\" 100000;\n"%name)
                    f.write("setAttr -lock true \"%s.tx\";\n"%name)
                    f.write("setAttr -lock true \"%s.ty\";\n"%name)
                    f.write("setAttr -lock true \"%s.tz\";\n"%name)
                    f.write("setAttr -lock true \"%s.rx\";\n"%name)
                    f.write("setAttr -lock true \"%s.ry\";\n"%name)
                    f.write("setAttr -lock true \"%s.rz\";\n"%name)
                    f.write("setAttr \"%s.sx\" 1;\n"%name)
                    f.write("setAttr \"%s.sy\" 1;\n"%name)
                    f.write("setAttr \"%s.sz\" 1;\n"%name)
                    f.write("setAttr -lock true \"%s.sx\";\n"%name)
                    f.write("setAttr -lock true \"%s.sy\";\n"%name)
                    f.write("setAttr -lock true \"%s.sz\";\n"%name)
                    f.write("setAttr -lock true \"%sShape.fl\";\n"%name)

                    f.write("file -import -type \"mayaBinary\" -mergeNamespacesOnClash false -rpr \"horizon\" -options \"v=0;\" -pr \"R:/filmServe/RnD/matchmove/06_mayaPlugin/asset/horizon.mb\";\n")
                    f.write("float $translateX = `getAttr (\"%s\" + \"*\" + \".translateX\")`;\n"%name)
                    f.write("float $translateY = `getAttr (\"%s\" + \"*\" + \".translateY\")`;\n"%name)
                    f.write("float $translateZ = `getAttr (\"%s\" + \"*\" + \".translateZ\")`;\n"%name)
                    f.write("move -rpr $translateX $translateY $translateZ ;\n")
                    f.write("select -tgl trk_horizon ;\n")
                    f.write("rename \"trk_horizon\" \"trk_horizon%s\";"%(name.split('trk_cam')[-1]))
                    f.write("editDisplayLayerMembers -noRecurse marker `ls -selection`;\n")
                    f.write("parent trk_horizon%s trk_marker ;\n"%(name.split('trk_cam')[-1]))

                    f.write("select -r %s ;\n"%name)
                    f.write("select -tgl trk_horizon%s ;\n"%(name.split('trk_cam')[-1]))
                    f.write("doCreatePointConstraintArgList 1 { \"0\",\"0\",\"0\",\"0\",\"0\",\"0\",\"0\",\"1\",\"\",\"1\" };\n")
                    f.write("pointConstraint -offset 0 0 0 -weight 1;\n")

                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".tx\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".ty\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".tz\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".rx\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".ry\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".rz\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".sx\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".sy\");\n"%(name.split('trk_cam')[-1]))
                    f.write("setAttr -lock true (\"trk_horizon%s\" + \"*\" + \".sz\");\n"%(name.split('trk_cam')[-1]))
                    f.write("select -cl;\n")

                    if name.endswith('trk_camLeft') or name.endswith('trk_cam'):
                        f.write("setAttr \"imagePlaneShape1.depth\" 10000;\n")
                        f.write("setAttr \"imagePlaneShape1.frameCache\" 500;\n")
                    elif name.endswith('trk_camRight'):
                        f.write("setAttr \"imagePlaneShape2.depth\" 10000;\n")
                        f.write("setAttr \"imagePlaneShape2.frameCache\" 500;\n")
            f.write("setAttr \"perspShape.nearClipPlane\" 1;\n")
            f.write("setAttr \"perspShape.farClipPlane\" 100000;\n")
            f.write("setAttr \"topShape.nearClipPlane\" 1;\n")
            f.write("setAttr \"topShape.farClipPlane\" 100000;\n")
            f.write("setAttr \"frontShape.nearClipPlane\" 1;\n")
            f.write("setAttr \"frontShape.farClipPlane\" 100000;\n")
            f.write("setAttr \"sideShape.nearClipPlane\" 1;\n")
            f.write("setAttr \"sideShape.farClipPlane\" 100000;\n")
            f.write("setAttr \"perspShape.nearClipPlane\" 10;\n")
            f.write("setAttr \"perspShape.farClipPlane\" 100000;\n")
            f.write("select -cl;\n")


            f.write("doGroup 0 1 1;\n")
            f.write("rename \"null1\" \"trk_mesh\";\n")
            f.write("parent trk_mesh trk_track ;\n")
            f.write("select -cl  ;\n")
            f.write("doGroup 0 1 1;\n")
            f.write("rename \"null1\" \"trk_meshMP\";\n")
            f.write("parent trk_meshMP trk_track ;\n")
            f.write("select -cl  ;\n")
            f.write("doGroup 0 1 1;\n")
            f.write("rename \"null1\" \"trk_scan\";\n")
            f.write("parent trk_scan trk_track ;\n")
            f.write("select -cl  ;\n")

            
            #
            # write camera point group...
            
            f.write("\n")
            f.write("// create camera point group...\n")
            name    = 'trk_locator'
            f.write("string $pointGroupName = `group -em -name  \"%s\" -parent $sceneGroupName`;\n"%name)
            f.write("$pointGroupName = ($sceneGroupName + \"|\" + $pointGroupName);\n")
            f.write("\n")
            
            # write points...
            l   = tde4.getPointList(campg)
            for p in l:
                if tde4.isPointCalculated3D(campg,p):
                    name    = tde4.getPointName(campg,p)
                    name    = "Tracker%s"%validName(name)
                    p3d = tde4.getPointCalcPosition3D(campg,p)
                    p3d = convertZup(p3d,yup)
                    f.write("\n")
                    f.write("// create point %s...\n"%name)
                    f.write("string $locator = stringArrayToString(`spaceLocator -name %s`, \"\");\n"%name)
                    f.write("$locator = (\"|\" + $locator);\n")
                    f.write("xform -t %.15f %.15f %.15f $locator;\n"%(p3d[0],p3d[1],p3d[2]))
                    f.write("parent $locator $pointGroupName;\n")
            
            f.write("\n")
            f.write("xform -zeroTransformPivots -rotateOrder zxy -scale 1.000000 1.000000 1.000000 $pointGroupName;\n")
            f.write("\n")
            
            
            #
            # write object/mocap point groups...
            
            camera      = tde4.getCurrentCamera()
            noframes    = tde4.getCameraNoFrames(camera)
            pgl     = tde4.getPGroupList()
            index       = 1
            for pg in pgl:
                if tde4.getPGroupType(pg)=="OBJECT" and camera!=None:
                    f.write("\n")
                    f.write("// create object point group...\n")
                    pgname  = "trk_object"
                    index   += 1
                    f.write("string $pointGroupName = `group -em -name  \"%s\" -parent $sceneGroupName`;\n"%pgname)
                    f.write("$pointGroupName = ($sceneGroupName + \"|\" + $pointGroupName);\n")
                    
                    # write points...
                    l   = tde4.getPointList(pg)
                    for p in l:
                        if tde4.isPointCalculated3D(pg,p):
                            name    = tde4.getPointName(pg,p)
                            name    = "Tracker%s"%validName(name)
                            p3d = tde4.getPointCalcPosition3D(pg,p)
                            p3d = convertZup(p3d,yup)
                            f.write("\n")
                            f.write("// create point %s...\n"%name)
                            f.write("string $locator = stringArrayToString(`spaceLocator -name %s`, \"\");\n"%name)
                            f.write("$locator = (\"|\" + $locator);\n")
                            f.write("xform -t %.15f %.15f %.15f $locator;\n"%(p3d[0],p3d[1],p3d[2]))
                            f.write("parent $locator $pointGroupName;\n")
                    
                    f.write("\n")
                    scale   = tde4.getPGroupScale3D(pg)
                    f.write("xform -zeroTransformPivots -rotateOrder zxy -scale %.15f %.15f %.15f $pointGroupName;\n"%(scale,scale,scale))

                    # animate object point group...
                    f.write("\n")
                    f.write("// animating point group %s...\n"%pgname)
                    frame   = 1
                    while frame<=noframes:
                        # rot/pos...
                        p3d = tde4.getPGroupPosition3D(pg,camera,frame)
                        p3d = convertZup(p3d,yup)
                        r3d = tde4.getPGroupRotation3D(pg,camera,frame)
                        rot = convertToAngles(r3d)
                        if frame>1:
                            rot = [ angleMod360(rot0[0],rot[0]), angleMod360(rot0[1],rot[1]), angleMod360(rot0[2],rot[2]) ]
                        rot0    = rot
                        f.write("setKeyframe -at translateX -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[0]))
                        f.write("setKeyframe -at translateY -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[1]))
                        f.write("setKeyframe -at translateZ -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[2]))
                        f.write("setKeyframe -at rotateX -t %d -v %.15f $pointGroupName; "%(frame+frame0,rot[0]))
                        f.write("setKeyframe -at rotateY -t %d -v %.15f $pointGroupName; "%(frame+frame0,rot[1]))
                        f.write("setKeyframe -at rotateZ -t %d -v %.15f $pointGroupName;\n"%(frame+frame0,rot[2]))
                        frame   += 1
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".tx\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".ty\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".tz\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".rx\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".ry\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".rz\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".sx\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".sy\");\n")
                    f.write("setAttr -lock true (\"trk_object\" + \"*\" + \".sz\");\n")



                # mocap point groups...
                if tde4.getPGroupType(pg)=="MOCAP" and camera!=None:
                    f.write("\n")
                    f.write("// create mocap point group...\n")
                    pgname  = "trk_mocap"
                    index   += 1
                    f.write("string $pointGroupName = `group -em -name  \"%s\" -parent $sceneGroupName`;\n"%pgname)
                    f.write("$pointGroupName = ($sceneGroupName + \"|\" + $pointGroupName);\n")
                    
                    # write points...
                    l   = tde4.getPointList(pg)
                    for p in l:
                        if tde4.isPointCalculated3D(pg,p):
                            name    = tde4.getPointName(pg,p)
                            name    = "Tracker%s"%validName(name)
                            p3d = tde4.getPointMoCapCalcPosition3D(pg,p,camera,1)
                            p3d = convertZup(p3d,yup)
                            f.write("\n")
                            f.write("// create point %s...\n"%name)
                            f.write("string $locator = stringArrayToString(`spaceLocator -name %s`, \"\");\n"%name)
                            f.write("$locator = (\"|\" + $locator);\n")
                            f.write("xform -t %.15f %.15f %.15f $locator;\n"%(p3d[0],p3d[1],p3d[2]))
                            for frame in range(1,noframes+1):
                                p3d = tde4.getPointMoCapCalcPosition3D(pg,p,camera,frame)
                                p3d = convertZup(p3d,yup)
                                f.write("setKeyframe -at translateX -t %d -v %.15f $locator; "%(frame+frame0,p3d[0]))
                                f.write("setKeyframe -at translateY -t %d -v %.15f $locator; "%(frame+frame0,p3d[1]))
                                f.write("setKeyframe -at translateZ -t %d -v %.15f $locator; "%(frame+frame0,p3d[2]))
                            f.write("parent $locator $pointGroupName;\n")
                    
                    f.write("\n")
                    scale   = tde4.getPGroupScale3D(pg)
                    f.write("xform -zeroTransformPivots -rotateOrder zxy -scale %.15f %.15f %.15f $pointGroupName;\n"%(scale,scale,scale))

                    # animate mocap point group...
                    f.write("\n")
                    f.write("// animating point group %s...\n"%pgname)
                    frame   = 1
                    while frame<=noframes:
                        # rot/pos...
                        p3d = tde4.getPGroupPosition3D(pg,camera,frame)
                        p3d = convertZup(p3d,yup)
                        r3d = tde4.getPGroupRotation3D(pg,camera,frame)
                        rot = convertToAngles(r3d)
                        if frame>1:
                            rot = [ angleMod360(rot0[0],rot[0]), angleMod360(rot0[1],rot[1]), angleMod360(rot0[2],rot[2]) ]
                        rot0    = rot
                        f.write("setKeyframe -at translateX -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[0]))
                        f.write("setKeyframe -at translateY -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[1]))
                        f.write("setKeyframe -at translateZ -t %d -v %.15f $pointGroupName; "%(frame+frame0,p3d[2]))
                        f.write("setKeyframe -at rotateX -t %d -v %.15f $pointGroupName; "%(frame+frame0,rot[0]))
                        f.write("setKeyframe -at rotateY -t %d -v %.15f $pointGroupName; "%(frame+frame0,rot[1]))
                        f.write("setKeyframe -at rotateZ -t %d -v %.15f $pointGroupName;\n"%(frame+frame0,rot[2]))
                        frame   += 1
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".tx\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".ty\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".tz\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".rx\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".ry\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".rz\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".sx\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".sy\");\n")
                    f.write("setAttr -lock true (\"trk_mocap\" + \"*\" + \".sz\");\n")

            

            #
            # global (scene node) transformation...
            
            p3d = tde4.getScenePosition3D()
            p3d = convertZup(p3d,yup)
            r3d = tde4.getSceneRotation3D()
            rot = convertToAngles(r3d)
            s   = tde4.getSceneScale3D()
            f.write("xform -zeroTransformPivots -rotateOrder zxy -translation %.15f %.15f %.15f -scale %.15f %.15f %.15f -rotation %.15f %.15f %.15f $sceneGroupName;\n\n"%(p3d[0],p3d[1],p3d[2],s,s,s,rot[0],rot[1],rot[2]))
            
            f.write("file -import -type \"mayaBinary\" -mergeNamespacesOnClash false -rpr \"marker\" -options \"v=0;p=17;f=0\"  -pr \"R:/filmServe/RnD/matchmove/06_mayaPlugin/asset/marker.mb\";\n")
            f.write("select -r trk_marker01 ;\n")
            f.write("editDisplayLayerMembers -noRecurse marker `ls -selection`;\n")
            f.write("parent trk_marker01 trk_marker ;\n")
            f.write("file -import -type \"mayaBinary\" -mergeNamespacesOnClash false -rpr \"human180\" -options \"v=0;\"  -pr \"R:/filmServe/RnD/matchmove/06_mayaPlugin/asset/human180.mb\";\n")
            f.write("select -r trk_human180cm_01 ;\n")
            f.write("editDisplayLayerMembers -noRecurse marker `ls -selection`;\n")
            f.write("parent trk_human180cm_01 trk_marker ;\n")
            f.write("select -r trk_human180cm_01 ;\n")
            f.write("sets -e -forceElement lambert2SG;\n")
            f.write("select -r trk_scan ;\n")
            f.write("editDisplayLayerMembers -noRecurse scan `ls -selection`;\n")


            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"Tracker\" + \"*\" + \".sz\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"trk_locator\" + \"*\" + \".sz\");\n")


            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"trk_track\" + \"*\" + \".sz\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"trk_mesh\" + \"*\" + \".sz\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".tx\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".ty\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".tz\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".rx\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".ry\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".rz\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".sx\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".sy\");\n")
            f.write("setAttr -lock true (\"trk_meshMP\" + \"*\" + \".sz\");\n")


            if LensDistortionValid:
                f.write("setAttr defaultResolution.width %s;"%(FootageWidth*1.1))
                f.write("setAttr defaultResolution.height %s;"%(FootageHeight*1.1))
            else:
                f.write("setAttr defaultResolution.width %s;"%FootageWidth)
                f.write("setAttr defaultResolution.height %s;"%FootageHeight)
                
            f.write('currentTime %s;'%(1+frame0))

            f.write("\n")
            f.close()
            tde4.postQuestionRequester("Export Maya...","Project successfully exported.","Ok")
        else:
            tde4.postQuestionRequester("Export Maya...","Error, couldn't open file.","Ok")


