import maya.cmds as maya
import maya.mel as mel
import linecache
import time
import datetime


##########################Sub message windows##################################################################
#Create a alarm message!#
alarmWindow = maya.window(title = "Message")
maya.columnLayout( adjustableColumn=False )
maya.text(label = "Please select at least one camera!")

successWindow = maya.window(title = "Message")
maya.columnLayout( adjustableColumn=False )
maya.text(label = "Success!")



##########################Main Panel to operate the animation###################################################
#Create a Panel to show the funtion knob
MainWindow = maya.window(title = "Matchmove Tool(correct animation)")
maya.columnLayout( adjustableColumn=False )
maya.frameLayout( label='Preprocessing', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.rowColumnLayout(numberOfColumns=3,columnAttach=[1,"right",0],columnWidth=[[1,80],[2,200],[2,150]])
maya.text(label="Bake Simulation",align = 'right')
maya.button(label="Press",w = 60,command = "bake()")
maya.text(label="")
maya.text(label="Pre/Post-Linear",align = 'right')
maya.button(label="Press",w = 60,command = "pre_post_Linear()")
maya.text(label="")
maya.text(label="Eular-Filter",align = 'right')
maya.button(label="Press",w = 60,command = "eular_Filter()")
maya.text(label="")
maya.setParent('..')
maya.setParent('..')
maya.frameLayout( label='Retime', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.rowColumnLayout(numberOfColumns=3,columnAttach=[1,"right",0],columnWidth=[[1,80],[2,200],[2,150]])
maya.text(label="Retime",align = 'right')
maya.button(label="Press",w = 60,command = "Objects = maya.ls(type = ['transform','camera'],selection = True);\
  maya.showWindow(alarmWindow) if Objects == [] else reTime(Objects)")
maya.text(label="")
maya.setParent('..')
maya.text(label="Replace Sequence",align = 'right')
SequenceInput = maya.textField()

commandstr = 'filename = maya.fileDialog2(fileMode=1, caption="Import Image");\
    maya.textField(SequenceInput,edit=True,w=300,fi=filename[0])'

change_Command = 'filepath = maya.textField(SequenceInput,q = True,tx = 1);\
    Objects = maya.ls(type = ["transform","camera"],selection = True);\
    maya.showWindow(alarmWindow) if Objects == [] else changeCommand_func(Objects,filepath)'

maya.textField(SequenceInput,edit=True,w=300,fi='R:/filmServe',dgc = commandstr,cc = change_Command)

#maya.button(label="Press",w = 60,command = "")
#maya.text(label="Replace Sequence",align = 'right')
maya.setParent('..')
maya.setParent('..') 
maya.frameLayout( label='ReadMe', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.text("Please select a camera you want to correct!")

maya.showWindow(MainWindow)



##########################A command to set imageName on CameraPlane#######################################################
def changeCommand_func(cameras,path):
  imagePlane = maya.imagePlane(cameras[0],q = 1,n = True)[0]
  maya.setAttr(imagePlane +".imageName", path ,type="string")



##########################preprocessing to animation node#######################################################
#A function to Pre-Linear
def bake():
  #Create a alarm message!#
  alarmWindow = maya.window(title = "Message")
  maya.columnLayout( adjustableColumn=False )
  maya.text(label = "Please select at least one camera!")

  Objects = maya.ls(type = ["transform","camera"],selection = True)
  if Objects == []:
    maya.showWindow(alarmWindow)
  else:
    curvelist_rotate = maya.ls( type="animCurveTA" )
    for rotateCurve in curvelist_rotate:
      out_attr = rotateCurve + ".output"
      destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
      if destinations != []:
        dst_node = destinations[0]
        maya.setAttr( dst_node , lock = False )
        if dst_node.split('.')[0] in Objects:
          maya.bakeResults(rotateCurve)
          maya.setAttr( dst_node , lock = True )

    curvelist_translate = maya.ls( type="animCurveTL" )
    for translateCurve in curvelist_translate:
      out_attr = translateCurve + ".output"
      destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
      if destinations != []:
        dst_node = destinations[0]
        maya.setAttr( dst_node , lock = False )
        if dst_node.split('.')[0] in Objects:
          maya.bakeResults(translateCurve)
          maya.setAttr( dst_node , lock = True )



#A function to Post-Linear
def pre_post_Linear():
  #Create a alarm message!#
  alarmWindow = maya.window(title = "Message")
  maya.columnLayout( adjustableColumn=False )
  maya.text(label = "Please select at least one camera!")

  Objects = maya.ls(type = ["transform","camera"],selection = True)
  if Objects == []:
    maya.showWindow(alarmWindow)
  else:
    for i in Objects:
      print i
      maya.setAttr( i+".tx" , lock = False )
      maya.setAttr( i+".ty" , lock = False )
      maya.setAttr( i+".tz" , lock = False )
      maya.setAttr( i+".rx" , lock = False )
      maya.setAttr( i+".ry" , lock = False )
      maya.setAttr( i+".rz" , lock = False )
      maya.setAttr( i+".sx" , lock = False )
      maya.setAttr( i+".sy" , lock = False )
      maya.setAttr( i+".sz" , lock = False )

      maya.keyTangent(inTangentType='spline',outTangentType = 'spline')
      maya.setInfinity(poi='linear',pri='linear')
      
      maya.setAttr( i+".tx" , lock = True )
      maya.setAttr( i+".ty" , lock = True )
      maya.setAttr( i+".tz" , lock = True )
      maya.setAttr( i+".rx" , lock = True )
      maya.setAttr( i+".ry" , lock = True )
      maya.setAttr( i+".rz" , lock = True )
      maya.setAttr( i+".sx" , lock = True )
      maya.setAttr( i+".sy" , lock = True )
      maya.setAttr( i+".sz" , lock = True )



#A function to Eular-Filter
def eular_Filter():
  #Create a alarm message!#
  alarmWindow = maya.window(title = "Message")
  maya.columnLayout( adjustableColumn=False )
  maya.text(label = "Please select at least one camera!")

  Objects = maya.ls(type = ["transform","camera"],selection = True)
  if Objects == []:
    maya.showWindow(alarmWindow)
  else:
    curvelist_rotate = maya.ls( type="animCurveTA" )
    for rotateCurve in curvelist_rotate:
      out_attr = rotateCurve + ".output"
      destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
      if destinations != []:
        dst_node = destinations[0]
        maya.setAttr( dst_node , lock = False )
        if dst_node.split('.')[0] in Objects:
          maya.filterCurve(rotateCurve)
          maya.setAttr( dst_node , lock = True )

    curvelist_translate = maya.ls( type="animCurveTL" )
    for translateCurve in curvelist_translate:
      out_attr = translateCurve + ".output"
      destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
      if destinations != []:
        dst_node = destinations[0]
        maya.setAttr( dst_node , lock = False )
        if dst_node.split('.')[0] in Objects:
          maya.filterCurve(translateCurve)
          maya.setAttr( dst_node , lock = True )







##########################Retime the animation node#############################################################


def reTime(selectedCameras):
  ############Sub message windows###########
  successWindow = maya.window(title = "Message")
  maya.columnLayout( adjustableColumn=False )
  maya.text(label = "Success!")


  #Get imformation of txt file!
  Filename = maya.fileDialog2(fileMode = 1 , caption='Browse Retime Imformation' , 
    startingDirectory = "R:/filmServe/1011_JA_GuiChuiDeng/VFX/sequences" )
  filename = str(Filename[0])
  myfile = open(filename)
  lines = len(myfile.readlines()) 
  linenum = int(lines)
  firstline = linecache.getline(filename, 1)
  firstline = int(firstline.split('.')[0])


  #Delete the unconnected node
  curvelist_rotate = maya.ls( type="animCurveTA" )
  for rotateCurve in curvelist_rotate:
    out_attr = rotateCurve + ".output"
    destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
    #Judge destinations is not Null
    if destinations == []:
      print "delete " + rotateCurve
      maya.delete(rotateCurve)

  #Delete the unconnected node
  curvelist_translate = maya.ls( type="animCurveTL" )
  for translateCurve in curvelist_translate:
    out_attr = translateCurve + ".output"
    destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
    #Judge destinations is not Null
    if destinations == []:
      print "delete " + translateCurve
      maya.delete(translateCurve)


  #Do Retime Operate To The Rotato Curve!
  curvelist_rotate = maya.ls( type="animCurveTA" )
  for rotateCurve in curvelist_rotate:
    out_attr = rotateCurve + ".output"
    print "disconnect " + rotateCurve
    destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
    #Judge destinations is not Null
    if destinations != []:
      dst_node = destinations[0]
      maya.setAttr( dst_node , lock = False )
      #judge if the dst_node is belong to selected camera
      if dst_node.split('.')[0] in selectedCameras:
        new_node = rotateCurve + "_Retiming" 
        maya.createNode( 'animCurveTA', n = new_node )
        print "create " + new_node
        maya.disconnectAttr(out_attr,dst_node)
        newout_attr = new_node + ".output"
        maya.connectAttr( newout_attr, dst_node )

        retimeframe = firstline - 1
        D_value = 0
        sum_value = 0
        temp = 0
        for i in range(1,linenum + 1):
          thislineGet = linecache.getline(filename, i)
          thislineGet = int(thislineGet.split('.')[0])
          lastlineGet = linecache.getline(filename, i - 1)
          if lastlineGet.split('.')[0]:
            lastlineGet = int(lastlineGet.split('.')[0])
          else:
            lastlineGet = firstline - 1
          retimeframe += 1
          if thislineGet != lastlineGet:
            value = maya.keyframe( rotateCurve, query = True , time = (thislineGet,thislineGet) , valueChange = True)
            valuefloat = float(value[0])
            maya.setKeyframe( new_node , t = retimeframe ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )

      maya.setAttr( dst_node , lock = True )




  #Do Retime Operate To The Translate Curve!
  curvelist_translate = maya.ls( type="animCurveTL" )
  for translateCurve in curvelist_translate:
    out_attr = translateCurve + ".output"
    print "disconnect " + translateCurve
    destinations = maya.connectionInfo(out_attr, destinationFromSource=True)
    #Judge destinations is not Null
    if destinations != []:
      dst_node = destinations[0]
      maya.setAttr( dst_node , lock = False )
      #judge if the dst_node is belong to selected camera
      if dst_node.split('.')[0] in selectedCameras:
        new_node = translateCurve + "_Retiming" 
        maya.createNode( 'animCurveTL', n = new_node )
        print "create " + new_node
        maya.disconnectAttr(out_attr,dst_node)
        newout_attr = new_node + ".output"
        maya.connectAttr( newout_attr, dst_node )

        retimeframe = firstline - 1
        D_value = 0
        sum_value = 0
        temp = 0
        for i in range(1,linenum + 1):
          thislineGet = linecache.getline(filename, i)
          thislineGet = int(thislineGet.split('.')[0])

          lastlineGet = linecache.getline(filename, i - 1)
          if lastlineGet.split('.')[0]:
            lastlineGet = int(lastlineGet.split('.')[0])
          else:
            lastlineGet = firstline - 1

          retimeframe += 1
          if thislineGet != lastlineGet:
            value = maya.keyframe( translateCurve, query = True , time = (thislineGet,thislineGet) , valueChange = True)
            valuefloat = float(value[0])
            maya.setKeyframe( new_node , t = retimeframe ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )

      maya.setAttr( dst_node , lock = True )
   
   
  #FINISH!
  maya.showWindow(successWindow)









