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
maya.setParent('..')
maya.setParent('..') 
maya.frameLayout( label='ReadMe', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.text("Please select a camera you want to correct!")

maya.showWindow(MainWindow)






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
          else:
            try:
              D_value += lastlineGet - int((linecache.getline(filename, i - 2)).split('.')[0])
              sum_value += D_value
              thislineGet += sum_value
              #print thislineGet
            except:
              thislineGet += 1
          value = maya.keyframe( rotateCurve, query = True , time = (thislineGet,thislineGet) , valueChange = True)
          if value:
            valuefloat = float(value[0])
            temp = valuefloat
            maya.setKeyframe( new_node , t = retimeframe ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )  
          else:
            maya.setKeyframe( new_node , t = retimeframe ,v = temp , itt = 'Spline' , ott = 'Spline'  )
          #print lastlineGet,thislineGet

        #add the front handle
        firstframe = maya.keyframe(rotateCurve,index=(0,0),query=True)
        firstframe = int(firstframe[0])
        tempforhandle = firstline
        if firstline > firstframe:
          D_value_2 = int((linecache.getline(filename, 3)).split('.')[0]) - int((linecache.getline(filename, 2)).split('.')[0])
          #print D_value_2
          for_handle_list = range(int(firstframe),firstline)
          for_handle_list.reverse()
          for frame in for_handle_list:
            #print frame
            tempforhandle -= D_value_2
            value = maya.keyframe( rotateCurve, query = True , time = (tempforhandle,tempforhandle) , valueChange = True)
            if value :
              valuefloat = float(value[0])
              maya.setKeyframe( new_node , t = frame ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )
      maya.filterCurve(translateCurve)
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
          else:
            try:
              D_value += lastlineGet - int((linecache.getline(filename, i - 2)).split('.')[0])
              sum_value += D_value
              thislineGet += sum_value
              #print thislineGet
            except:
              thislineGet += 1
          value = maya.keyframe( translateCurve, query = True , time = (thislineGet,thislineGet) , valueChange = True)
          if value:
            valuefloat = float(value[0])
            temp = valuefloat
            maya.setKeyframe( new_node , t = retimeframe ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )
          else:  
            #print temp
            maya.setKeyframe( new_node , t = retimeframe ,v = temp , itt = 'Spline' , ott = 'Spline'  )

          #print lastlineGet,thislineGet

        #add the front handle
        firstframe = maya.keyframe(translateCurve,index=(0,0),query=True)
        firstframe = int(firstframe[0])
        tempforhandle = firstline
        if firstline > firstframe:
          D_value_2 = int((linecache.getline(filename, 3)).split('.')[0]) - int((linecache.getline(filename, 2)).split('.')[0])
          #print D_value_2
          for_handle_list = range(int(firstframe),firstline)
          for_handle_list.reverse()
          for frame in for_handle_list:
            #print frame
            tempforhandle -= D_value_2
            value = maya.keyframe( translateCurve, query = True , time = (tempforhandle,tempforhandle) , valueChange = True)
            if value :
              valuefloat = float(value[0])
              maya.setKeyframe( new_node , t = frame ,v = valuefloat , itt = 'Spline' , ott = 'Spline'  )


      maya.filterCurve(translateCurve)
      maya.setAttr( dst_node , lock = True )
   
   
  #FINISH!
  maya.showWindow(successWindow)









