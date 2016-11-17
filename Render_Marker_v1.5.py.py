# -*- coding: utf-8 -*-
#This tool is used for exporting a .abc file and then generating a .nk script,
#submit this .nk script to render farm at the end.

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya
import os.path,re,sys
import shiboken
import threading,subprocess,traceback




########################################################################################################
########################################################################################################
#######################################ScriptWriter#####################################################
########################################################################################################
########################################################################################################

def asUtf8(value):
  """ Get value as a str.  If the input was of type unicode, encode it to utf-8. """
  if isinstance(value, unicode):
    return value.encode('utf-8')
  return str(value)

def asUnicode(value):
  """ Get value as a unicode string.  If the input is not unicode, decode it from utf-8. """
  if isinstance(value, unicode):
    return value
  return str(value).decode('utf-8')

class ScriptWriter:
  def __init__(self):
    #print self
    self._nodes = []
    self._nodeOutput = ""
    
  def _postProcessNodes(self):
    rootNode = None
    dropFrameTimeCodeNodes = []
    
    for node in self._nodes:
      # find the root node
      if node.type() == "Root":
        rootNode = node
        #print rootNode
        
      # check if we have any drop frame time code nodes
      if (node.type() == "AddTimeCode"):
        try:
          startCodeString = node.knob("startcode")
          if hiero.core.Timecode.displayTypeFromString(startCodeString) == hiero.core.Timecode.kDisplayDropFrameTimecode:
            dropFrameTimeCodeNodes.append(node)
        except:
          pass
      
    # spit out an error of some kind when the script loads
    if rootNode and dropFrameTimeCodeNodes:
      timeCodeErrorScript = '''if (nuke.env['NukeVersionMajor'] < 7) and (os.path.split(nuke.env['ExecutablePath'])[1].find('Hiero') < 0):
  errorString = 'ERROR: There are AddTimeCode nodes in this script that have drop frame formatting. This version of Nuke does not support drop frames in the AddTimeCode node. Generated time codes will likely be wrong.'
  if nuke.GUI:
    nuke.message(errorString)
  else:
    print errorString
'''
      #print 1
      rootNode.setKnob("onScriptLoad", timeCodeErrorScript)
      

  def __repr__(self):
    # post process the script to add anything extra in
    self._postProcessNodes()
    #print self._nodes


    # Dealing with non-ascii is a bit tricky here.  Ideally we'd use unicode strings everywhere, only choosing an encoding when actually
    # writing the file, but that's a significant amount of work.  So, self._nodeOutput is a utf-8 string, and fileContents is unicode, which is
    # then encoded as utf-8.  This seems very hacky, but it was the only way I could figure out to stop Python from complaining.
    
    # create the script
    fileContents = unicode()
    #print fileContents,1
    for node in self._nodes:
      # reset our node output
      self._nodeOutput = ""
      
      # serialize out the node, using ourself to catch the node and knob settings
      node.serialize(self)
      #print self._nodeOutput
      #print 1

      # add the per node output to our final output
      fileContents += asUnicode(self._nodeOutput)
    #print asUtf8(fileContents)
    return asUtf8(fileContents)
  
  def addNode(self, node):
    #print 'this is' + str(node)
    if node is None:
      raise RuntimeError, "Attempting to add None as a node."
    if hasattr(node, "__iter__"):
      self._nodes.extend(node)
    else:
      self._nodes.append(node)
    
  def writeToDisk(self, scriptFilename):

    # Find the base destination directory, if it doesn't exist create it
    dstdir = os.path.dirname(scriptFilename)
    if not os.path.exists(dstdir):
      os.makedirs(dstdir)

    # Delete any existing file
    if os.path.lexists(scriptFilename):
      os.remove(scriptFilename)
      
    # create the script
    #print self._nodes
    fileContents = str(self)
    #print self

    # Then write the file
    f = open(scriptFilename, 'w')
    f.write (fileContents)
    f.close()
  
  ############################################################################################
  # Methods that allow this object to be sent to the serialize method of KnobFormatter objects
  ############################################################################################
  
  def beginSerializeNode(self, nodeType):
    self._nodeOutput += nodeType + " { \n"
  
  def endSerializeNode(self):
    self._nodeOutput += "}\n"

  def ConstendSerializeNode(self):
    self._nodeOutput += "}\nset N153da410 [stack 0]\n"

  def readgeoendSerializeNode(self):
    self._nodeOutput += "}\npush $N153da410\n"

  def serializeKnob(self, knobType, knobValue):
    self._nodeOutput += " " + knobType + " "

    # knobValue sometimes comes in as unicode, make sure it's converted to utf-8
    if isinstance(knobValue, basestring) and \
      not knobValue.startswith('{') and \
      not knobValue.startswith('"'):
      self._nodeOutput += '"' + asUtf8(knobValue) + '"'
    else:
      self._nodeOutput += str(knobValue)
    self._nodeOutput += "\n"
  
  def serializeKnobs(self, knobValues, order):
    #print knobValues,order
    for i in order:
      for (key, value) in knobValues.iteritems():
        if key == i:
          self.serializeKnob(key, value)
      
  def serializeUserKnob(self, type, knobName, text, tooltip, value):
    # should end looking like this: addUserKnob {2 projectpath l "project path" t "Stores the path to the Hiero project that this node was created with."}
    self._nodeOutput += " addUserKnob {"
    self._nodeOutput += str(type)
    self._nodeOutput += " "
    self._nodeOutput += str(knobName)
    
    if text:
      self._nodeOutput += " l \"" + asUtf8(text) + "\""
      
    if tooltip:
      self._nodeOutput += " t \"" + asUtf8(tooltip) + "\""
      
    self._nodeOutput += "}\n"
    
    if value is not None:
      # now that we've added the knob definition above, we can just serialize setting the value the same as any other knob
      self.serializeKnob(knobName, value)
      
  def serializeUserKnobs(self, userKnobs):
    # array of (type, knobName, text, tooltip, value)
    for userKnob in userKnobs:
      self.serializeUserKnob(*userKnob)
      
  def serializeNode(self, nodeType, knobValues, userKnobs, order):
    #print nodeType,knobValues
    self.beginSerializeNode(nodeType)
    self.serializeKnobs(knobValues, order)
    self.serializeUserKnobs(userKnobs)
    self.endSerializeNode()




########################################################################################################
########################################################################################################
#########################################KnobFormatter##################################################
########################################################################################################
########################################################################################################

class DefaultNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, order):
    serializer.serializeNode(nodeType, knobValues, userKnobs, order)
  

class ReadNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, order):
    # do the inputs, then file, then format string, then first frame, then last frame
    inputs = 0
    file = ""
    format = ""
    first = 0
    last = 0
    auto_alpha = "true"
    
    # pull out all of the special knobs that we care about
    # putting the rest into another list
    remainingKnobs = {}
    for (key, value) in knobValues.iteritems():
      if key == "file":
        file = value
      elif key == "format":
        format = value
      elif key == "first":
        first = value
      elif key == "last":
        last = value
      elif key == "inputs":
        inputs = value
      elif key == "auto_alpha":
        auto_alpha = value
      else:
        remainingKnobs[key] = value

    serializer.beginSerializeNode(nodeType)
    
    # write out the special knobs first
    serializer.serializeKnob("inputs", 0)
    serializer.serializeKnob("file", file)
    serializer.serializeKnob("format", format)
    serializer.serializeKnob("first", first)
    serializer.serializeKnob("last", last)
    serializer.serializeKnob("auto_alpha", auto_alpha)
    
    # write out the rest of the knobs
    serializer.serializeKnobs(remainingKnobs, order)
    serializer.serializeUserKnobs(userKnobs)
    
    serializer.endSerializeNode()


class WriteNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, order):
    priorityKnobs = ("file_type",)
      
    serializer.beginSerializeNode(nodeType)
    for knobKey in priorityKnobs:
      if knobKey in knobValues:
        serializer.serializeKnob(knobKey, knobValues[knobKey])
      
    for knobKey in knobValues.keys():
      if knobKey not in priorityKnobs:
        serializer.serializeKnob(knobKey, knobValues[knobKey])
        
    serializer.serializeUserKnobs(userKnobs)
             
    serializer.endSerializeNode()
  

# special case serialization nodes
_customKnobFormatters = {"Read": ReadNodeKnobFormatter(), "Write": WriteNodeKnobFormatter()}

def RegisterCustomNukeKnobFormatter(nodeType, nodeKnobFormatter):
  _customKnobFormatters[nodeType] = nodeKnobFormatter


########################################################################################################
########################################################################################################
#########################################BaseNode#######################################################
########################################################################################################
########################################################################################################

class Node:
  USER_KNOB_TYPE_TAB = 20
  USER_KNOB_TYPE_FILENAME = 2
  USER_KNOB_TYPE_INPUTTEXT = 1
  
  def __init__(self, nodeType, inputNode0=None, inputNodes=None, **keywords):
    
    self._userKnobs = []

    if inputNodes == None:
      self._inputNodes = {}
    else:
      self._inputNodes = inputNodes.copy()
      
    # allow a single node to be passed in
    if inputNode0 != None:
      self._inputNodes[0] = inputNode0
      
    self._nodeType = nodeType
    self._knobValues = {}
    self._knobOrder  = []

    for (kw, value) in keywords.iteritems():
      self._knobValues[kw] = value
    #print self
    #print self._knobValues
      
  def setKnob(self, knobName, knobValue):
    self._knobValues[str(knobName)] = knobValue
    self._knobOrder.append(str(knobName))
    
  def _addUserKnob(self, type, knobName, text=None, tooltip=None, value=None):
    self._userKnobs.append((type, knobName, text, tooltip, value))
    
  def addTabKnob(self, knobName, text=None, tooltip=None):
    self._addUserKnob(Node.USER_KNOB_TYPE_TAB, knobName, text)
    
  def addFilenameKnob(self, knobName, text=None, tooltip=None, value=None):
    self._addUserKnob(Node.USER_KNOB_TYPE_FILENAME, knobName, text, tooltip, value)
    
  def addInputTextKnob(self, knobName, text=None, tooltip=None, value=None):
    self._addUserKnob(Node.USER_KNOB_TYPE_INPUTTEXT, knobName, text, tooltip, value)
    
  def knob(self, knobName):
    return self._knobValues[str(knobName)]

  def serialize(self, serializer):
    if self._nodeType in _customKnobFormatters:
      knobFormatter = _customKnobFormatters[self._nodeType]
    else:
      knobFormatter = DefaultNodeKnobFormatter()
    #print knobFormatter
    return knobFormatter.serialize(serializer, self._nodeType, self._knobValues, self._userKnobs, self._knobOrder)
  
  def formatString(self, width, height, pixelAspect=None):
    if pixelAspect is not None:
      return "%i %i 0 0 %i %i %f" % (width, height, width, height, pixelAspect)
    return str(width) + " " + str(height)
    
  def setName(self, name):
    self.setKnob( 'name', name.replace(' ', '_') )
  
  def type(self):
    return self._nodeType
      
  def setInputNode(self, index, node):
    self._inputNodes[index] = node
    
  def inputNodes(self):
    return self._inputNodes

########################################################################################################
########################################################################################################
#########################################RootNode#######################################################
########################################################################################################
########################################################################################################

class RootNode(Node):
  def __init__(self, first_frame, last_frame, fps=None, stereo=None):
    Node.__init__(self, "Root", first_frame=first_frame, last_frame=last_frame, lock_range='true')
    
    if fps is not None:
      self.setKnob("fps", fps)

    if stereo == True:
      self.setKnob("views", "left #ff0000\nright #00ff00")

    # When Nuke goes to read an image, it checks if the already loaded plugins can read it
    # ffmpeg and mov reader can read mp4 and m4v files, but only if they're already loaded
    # If they're not loaded, then Nuke checks the file extension and tries to load a plugin with that
    # name (i.e. mp4Reader). But Nuke doesn't have one of those.
    # So we force it to load.
    loadMovStuffScript = '''if nuke.env['LINUX']:
  nuke.tcl('load ffmpegReader')
  nuke.tcl('load ffmpegWriter')
else:
  nuke.tcl('load movReader')
  nuke.tcl('load movWriter')'''
    self.setKnob("onScriptLoad", loadMovStuffScript)
      
  def _setLUTKnob(self, key, lut):
    # don't filter out or error on non nuke built-in luts; doing so would make it so that
    # clients couldn't have their own custom luts in Hiero and Nuke.
    
    if lut == "raw":
      lut = "linear"
    
    # If no lut is set, skip this knob
    if lut != None:
      self.setKnob(key, lut)    

  def addProjectSettings(self, projectSettings):
  
    # Check the OCIO export option
    if projectSettings['lutUseOCIOForExport']:
      # Has a ocio config been set in the Application preferences?
      ocioConfig = hiero.core.ApplicationSettings().value("ocioConfigFile")    
      if ocioConfig:
        # Enable the custom OCIO config in the root node
        self.setKnob("defaultViewerLUT", "OCIO LUTs")
        self.setKnob("OCIO_config", "custom")
        self.setKnob("customOCIOConfigPath", ocioConfig)
    else:
      # The default luts dont understand the OCIO luts
      # Only set these default luts if OCIO is not enabled
      
      # Use helper function to test validity of the lut within the project setting dictionary
      self._setLUTKnob("monitorLut", projectSettings['lutSettingViewer'])
      self._setLUTKnob("int8Lut"   , projectSettings['lutSetting8Bit']  )
      self._setLUTKnob("int16Lut"  , projectSettings['lutSetting16Bit'] )
      self._setLUTKnob("logLut"    , projectSettings['lutSettingLog']   )
      self._setLUTKnob("floatLut"  , projectSettings['lutSettingFloat'] )


########################################################################################################
########################################################################################################
#########################################CreateScripts##################################################
########################################################################################################
########################################################################################################


def CreateNukeProject(seqpathList,camDataLsit,geopath,writepath,projpath,startframe,endframe,fps,W_size,H_size,scene_view,stereo,framecolor):

    
    geopath = geopath.replace('\\', '/')
    writepath = writepath.replace('\\', '/')
    projpath = projpath.replace('\\', '/')

    nukeScriptWriter = ScriptWriter()

    # Create the root node, this specifies the global frame range and frame rate
    rootNode = RootNode(startframe, endframe, fps, stereo)
    nukeScriptWriter.addNode(rootNode)

    
    #create the Camera2 node
    camNode = Node('Camera2')
    camNode.setKnob('inputs'          ,0)
    camNode.setKnob('rot_order'       ,'ZXY')
    camNode.setKnob('frame_rate'      ,fps)
    camNode.setKnob('name'            ,'Camera1')
    if stereo == True:
        camNode.setKnob('translate'   ,'{(default '+camDataLsit[0]['translate']+' left '+camDataLsit[1]['translate']+')}')
        camNode.setKnob('rotate'      ,'{(default '+camDataLsit[0]['rotate']+' left '+camDataLsit[1]['rotate']+')}')
        camNode.setKnob('scaling'     ,'{(default '+camDataLsit[0]['scaling']+' left '+camDataLsit[1]['scaling']+')}')
        camNode.setKnob('focal'       ,'{(default '+camDataLsit[0]['focal']+' left '+camDataLsit[1]['focal']+')}')
        camNode.setKnob('haperture'   ,'{(default '+camDataLsit[0]['haperture']+' left '+camDataLsit[1]['haperture']+')}')
        camNode.setKnob('vaperture'   ,'{(default '+camDataLsit[0]['vaperture']+' left '+camDataLsit[1]['vaperture']+')}')
        camNode.setKnob('near'        ,'{(default '+camDataLsit[0]['near']+' left '+camDataLsit[1]['near']+')}')
        camNode.setKnob('far'         ,'{(default '+camDataLsit[0]['far']+' left '+camDataLsit[1]['far']+')}')
        camNode.setKnob('focal_point' ,'{(default '+camDataLsit[0]['focal_point']+' left '+camDataLsit[1]['focal_point']+')}')
        camNode.setKnob('fstop'       ,'{(default '+camDataLsit[0]['fstop']+' left '+camDataLsit[1]['fstop']+')}')
    else:
        camNode.setKnob('translate'   ,camDataLsit[0]['translate'])
        camNode.setKnob('rotate'      ,camDataLsit[0]['rotate'])
        camNode.setKnob('scaling'     ,camDataLsit[0]['scaling'])
        camNode.setKnob('focal'       ,camDataLsit[0]['focal'])
        camNode.setKnob('haperture'   ,camDataLsit[0]['haperture'])
        camNode.setKnob('vaperture'   ,camDataLsit[0]['vaperture'])
        camNode.setKnob('near'        ,camDataLsit[0]['near'])
        camNode.setKnob('far'         ,camDataLsit[0]['far'])
        camNode.setKnob('focal_point' ,camDataLsit[0]['focal_point'])
        camNode.setKnob('fstop'       ,camDataLsit[0]['fstop'])
    camNode.setKnob('xpos'            ,383)
    camNode.setKnob('ypos'            ,86)
    nukeScriptWriter.addNode(camNode)
    

    #create the Wireframe node
    WFNode = Node('Wireframe')
    WFNode.setKnob('inputs',0)
    WFNode.setKnob('line_color','{1 0 0 1}')
    WFNode.setKnob('line_color_panelDropped','true')
    WFNode.setKnob('xpos',239)
    WFNode.setKnob('ypos',-34)
    nukeScriptWriter.addNode(WFNode)
    # else:
    #     #create the Constant node
    #     ConstantNode = Node("Constant")
    #     ConstantNode.setKnob('inputs',0)
    #     ConstantNode.setKnob('channels','rgba')
    #     ConstantNode.setKnob('color'   ,'{1 0 0 1}')
    #     ConstantNode.setKnob('format'  ,"%s %s 0 0 %s %s 1"%(W_size,H_size,W_size,H_size))
    #     ConstantNode.setKnob('xpos',239)
    #     ConstantNode.setKnob('ypos',-34)
    #     nukeScriptWriter.addNode(ConstantNode)
    
    #create the ReadGeo2 node
    GeoNode = Node("ReadGeo2")
    GeoNode.setKnob('file'                , geopath)
    GeoNode.setKnob('frame_rate'          , fps)
    GeoNode.setKnob('read_on_each_frame'  , 'true')
    GeoNode.setKnob('use_geometry_colors' , 'false')
    GeoNode.setKnob('range_first'         , startframe)
    GeoNode.setKnob('range_last'          , endframe  )
    GeoNode.setKnob('scene_view'          , scene_view)
    GeoNode.setKnob('xpos'                , 239)
    GeoNode.setKnob('ypos'                , 28)
    nukeScriptWriter.addNode(GeoNode)


    #create the Constant node
    ConstantNode = Node("Constant")
    ConstantNode.setKnob('inputs',0)
    ConstantNode.setKnob('channels','rgb')
    ConstantNode.setKnob('color'   ,'{0 0 0 0}')
    ConstantNode.setKnob('format'  ,"%s %s 0 0 %s %s 1"%(W_size,H_size,W_size,H_size))
    ConstantNode.setKnob('xpos',139)
    ConstantNode.setKnob('ypos',107)
    nukeScriptWriter.addNode(ConstantNode)


    #create the ScanlineRender node
    scanNode = Node("ScanlineRender")
    scanNode.setKnob('inputs',3)
    scanNode.setKnob('antialiasing','high')
    scanNode.setKnob('motion_vectors_type','distance')
    scanNode.setKnob('xpos',239)
    scanNode.setKnob('ypos',107)
    nukeScriptWriter.addNode(scanNode)


    #create the Constant node
    ConstantNode = Node("Constant")
    ConstantNode.setKnob('inputs',0)
    ConstantNode.setKnob('channels','rgb')
    ConstantNode.setKnob('color'   ,'{%s 1}'%framecolor)
    ConstantNode.setKnob('format'  ,"%s %s 0 0 %s %s 1"%(W_size,H_size,W_size,H_size))
    ConstantNode.setKnob('xpos',339)
    ConstantNode.setKnob('ypos',250)
    nukeScriptWriter.addNode(ConstantNode)


    #create the ShuffleCopy node
    ShuffleCopyNode = Node("ShuffleCopy")
    ShuffleCopyNode.setKnob('inputs',2)
    ShuffleCopyNode.setKnob('in','rgb')
    ShuffleCopyNode.setKnob('in2'  ,'rgb')
    ShuffleCopyNode.setKnob('red'  ,"red")
    ShuffleCopyNode.setKnob('out'  ,"alpha")
    ShuffleCopyNode.setKnob('xpos',239)
    ShuffleCopyNode.setKnob('ypos',250)
    nukeScriptWriter.addNode(ShuffleCopyNode)


    #create the Premult node
    PremultNode = Node("Premult")
    PremultNode.setKnob('xpos',239)
    PremultNode.setKnob('ypos',300)
    nukeScriptWriter.addNode(PremultNode)


    #Create the read node
    readNode = Node("Read")
    readNode.setKnob('inputs',0)
    readNode.setKnob('format'  ,"%s %s 0 0 %s %s 1"%(W_size,H_size,W_size,H_size))
    seqpathStr = ''
    if stereo == True:
        seqpath_R = seqpathList[0].replace('\\', '/')
        seqpath_L = seqpathList[1].replace('\\', '/')
        seqpathStr = r'\vdefault\v' + seqpath_R + r'\vleft\v' + seqpath_L
    else:
        seqpathStr = seqpathList[0]
    readNode.setKnob('file' ,seqpathStr)
    readNode.setKnob('first',startframe)
    readNode.setKnob('last' ,endframe)
    readNode.setKnob('xpos' ,97)
    readNode.setKnob('ypos' ,350)
    nukeScriptWriter.addNode(readNode)


    #create the Merge2 node
    MergeNode = Node("Merge2")
    MergeNode.setKnob('inputs',2)
    MergeNode.setKnob('operation','over')
    MergeNode.setKnob('mix',0.8)
    MergeNode.setKnob('xpos',239)
    MergeNode.setKnob('ypos',350)
    nukeScriptWriter.addNode(MergeNode)


    #create the Write node
    writeNode = Node("Write")
    writeNode.setKnob('channels','rgba')
    writeNode.setKnob('file',writepath)
    filereg = re.compile('\S+.(exr|EXR|dpx|DPX|jpeg|JPEG|jpg|JPG|tiff|TIFF|mov|MOV)$')
    matchgroup = filereg.match(writepath)
    pathext = matchgroup.group(1)
    writeNode.setKnob('file_type',pathext.lower())
    if pathext == "mov":
      writeNode.setKnob('codec','jpeg')
    writeNode.setKnob('_jpeg_quality',1)
    writeNode.setKnob('xpos',239)
    writeNode.setKnob('ypos',400)
    writeNode.setKnob('name','Write1')
    nukeScriptWriter.addNode(writeNode)


    #create the Viewer node
    # viewNode = Node("Viewer")
    # viewNode.setKnob('input_process','false')
    # viewNode.setKnob('xpos',239)
    # viewNode.setKnob('ypos',450)
    # nukeScriptWriter.addNode(viewNode)
    

    # write the script to disk
    scriptPath = projpath
    nukeScriptWriter.writeToDisk(scriptPath)






########################################################################################################
########################################################################################################
#########################################GetDatFrmMaYa##################################################
########################################################################################################
########################################################################################################
##MayaOperator -- Core code.
class SampleData():
    def __init__(self):
        self.mayascript = cmds.file(q =1 , location = 1)
        self.abcpath    = ''
        self.fbxpath    = ''
        self.nukepath   = ''
        self.renderpath = ''


    def getCameralist(self):
        string_list     = cmds.listCameras()
        try:
            string_list.remove(u'front')
        except:
            pass
        try:
            string_list.remove(u'persp')
        except:
            pass
        try:
            string_list.remove(u'side')
        except:
            pass
        try:
            string_list.remove(u'top')
        except:
            pass
        return string_list


    def getAbcPath(self):
        projname        = os.path.splitext(os.path.basename(self.mayascript))[0]
        match = re.match(r'(\w+)(_[a-zA-Z0-9]+_[vV]\d+)',projname)
        if match:
            front = match.group(1)
            back  = match.group(2)
            self.abcpath = os.path.dirname(self.mayascript) + '/%s_wire%s.abc'%(front,back)
        else:
            self.abcpath = os.path.dirname(self.mayascript) + '/%s_wire.abc'%(projname)
        return self.abcpath


    def getFbxPath(self):
        projname        = os.path.splitext(os.path.basename(self.mayascript))[0]
        match = re.match(r'(\w+)(_[a-zA-Z0-9]+_[vV]\d+)',projname)
        if match:
            front = match.group(1)
            back  = match.group(2)
            self.fbxpath = os.path.dirname(self.mayascript) + '/%s_wire_camera%s.fbx'%(front,back)
        else:
            self.fbxpath = os.path.dirname(self.mayascript) + '/%s_wire_camera.fbx'%(projname)
        return self.fbxpath


    def getNukePath(self):
        projname        = os.path.splitext(os.path.basename(self.mayascript))[0]
        match = re.match(r'(\w+)(_[a-zA-Z0-9]+_[vV]\d+)',projname)
        if match:
            front = match.group(1)
            back  = match.group(2)
            self.nukepath = os.path.dirname(self.mayascript) + '/%s_wire%s.nk'%(front,back)
        else:
            self.nukepath = os.path.dirname(self.mayascript) + '/%s_wire.nk'%(projname)
        return self.nukepath


    def getRenderPath(self,stereo = None):
        projname        = os.path.splitext(os.path.basename(self.mayascript))[0]
        match = re.match(r'(\w+)(_[a-zA-Z0-9]+_[vV]\d+)',projname)
        if match:
            front = match.group(1)
            back  = match.group(2)
            if stereo == True:
                self.renderpath = os.path.dirname(self.mayascript) + '/%s_wire%s/%s_wire%s.####.jpg'%(front,r"_%V" + back,front,r"_%V" + back)
            else:
                self.renderpath = os.path.dirname(self.mayascript) + '/%s_wire%s/%s_wire%s.####.jpg'%(front,back,front,back)
        else:
            if stereo == True:
                self.renderpath = os.path.dirname(self.mayascript) + '/%s_wire%s/%s_wire_%s.####.jpg'%(projname,r"%V",projname,r"%V")
            else:
                self.renderpath = os.path.dirname(self.mayascript) + '/%s_wire/%s_wire.####.jpg'%(projname,projname)
        return self.renderpath


    def getFps(self):
        return


    def getCameraData(self,cameraName):
        #"translate,rotate,scaling,focal,haperture,vaperture,near,far,focal_point,fstop"#
        dictionary = {}

        #initilized the parament.
        firstframe = cmds.playbackOptions(q = True , minTime= True)
        lastframe  = cmds.playbackOptions(q = True , maxTime= True)
        translate_x = "{curve x%s"%int(firstframe)
        translate_y = "{curve x%s"%int(firstframe)
        translate_z = "{curve x%s"%int(firstframe)
        rotate_x    = "{curve x%s"%int(firstframe)
        rotate_y    = "{curve x%s"%int(firstframe)
        rotate_z    = "{curve x%s"%int(firstframe)
        scaling_x   = "{curve x%s"%int(firstframe)
        scaling_y   = "{curve x%s"%int(firstframe)
        scaling_z   = "{curve x%s"%int(firstframe)
        focal       = "{curve x%s"%int(firstframe)
        haperture   = "{curve x%s"%int(firstframe)
        vaperture   = "{curve x%s"%int(firstframe)
        near        = "{curve x%s"%int(firstframe)
        far         = "{curve x%s"%int(firstframe)
        focal_point = "{curve x%s"%int(firstframe)
        fstop       = "{curve x%s"%int(firstframe)
        
        #get value at some frame.
        for frame in range(int(firstframe),int(lastframe+1)):
            translate_x += (" " + str(cmds.getAttr( cameraName + ".tx" , time = frame )))
            translate_y += (" " + str(cmds.getAttr( cameraName + ".ty" , time = frame )))   
            translate_z += (" " + str(cmds.getAttr( cameraName + ".tz" , time = frame )))      
            rotate_x    += (" " + str(cmds.getAttr( cameraName + ".rx" , time = frame )))
            rotate_y    += (" " + str(cmds.getAttr( cameraName + ".ry" , time = frame )))   
            rotate_z    += (" " + str(cmds.getAttr( cameraName + ".rz" , time = frame )))      
            scaling_x   += (" " + str(cmds.getAttr( cameraName + ".sx" , time = frame )))
            scaling_y   += (" " + str(cmds.getAttr( cameraName + ".sy" , time = frame )))   
            scaling_z   += (" " + str(cmds.getAttr( cameraName + ".sz" , time = frame )))    
            focal       += (" " + str(cmds.getAttr( cameraName + ".focalLength"            , time = frame )))    
            haperture   += (" " + str(cmds.getAttr( cameraName + ".horizontalFilmAperture" , time = frame ) * 25.4 ))    
            vaperture   += (" " + str(cmds.getAttr( cameraName + ".verticalFilmAperture"   , time = frame ) * 25.4 ))    
            near        += (" " + str(cmds.getAttr( cameraName + ".nearClipPlane"          , time = frame )))
            far         += (" " + str(cmds.getAttr( cameraName + ".farClipPlane"           , time = frame )))
            focal_point += (" " + str(cmds.getAttr( cameraName + ".focusDistance"          , time = frame )))
            fstop       += (" " + str(cmds.getAttr( cameraName + ".fStop"                  , time = frame )))

        #finish construct!
        translate_x += "}"
        translate_y += "}"
        translate_z += "}"
        rotate_x    += "}"
        rotate_y    += "}"
        rotate_z    += "}"
        scaling_x   += "}"
        scaling_y   += "}"
        scaling_z   += "}"
        focal       += "}"
        haperture   += "}"
        vaperture   += "}"
        near        += "}"
        far         += "}"
        focal_point += "}"
        fstop       += "}"

        translate   = "{%s %s %s}"%(translate_x,translate_y,translate_z)
        rotate      = "{%s %s %s}"%(rotate_x,rotate_y,rotate_z)
        scaling     = "{%s %s %s}"%(scaling_x,scaling_y,scaling_z)
        focal       = "{%s}"%focal
        haperture   = "{%s}"%haperture
        vaperture   = "{%s}"%vaperture
        near        = "{%s}"%near
        far         = "{%s}"%far
        focal_point = "{%s}"%focal_point
        fstop       = "{%s}"%fstop

        #assign value for dictionary.
        dictionary['translate']   = translate
        dictionary['rotate']      = rotate
        dictionary['scaling']     = scaling
        dictionary['focal']       = focal
        dictionary['haperture']   = haperture
        dictionary['vaperture']   = vaperture
        dictionary['near']        = near
        dictionary['far']         = far
        dictionary['focal_point'] = focal_point
        dictionary['fstop']       = fstop

        return dictionary
 




########################################################################################################
########################################################################################################
########################################################################################################

##NukeScriptOperator:
class nukeScriptOperator():


    def __init__(self,script,firstframe,lastframe):
        self.script     = script
        self.firstframe = firstframe
        self.lastframe  = lastframe
        self.SourceSeqs = None
        self.script_path = os.path.dirname(cmds.file(q =1 , location = 1)) + '/'
        if os.path.exists('C:/Program Files/Nuke8.0v5/'):
            self.nuke_folder = 'C:/Program Files/Nuke8.0v5/'
        elif os.path.exists('C:/Program Files/Nuke8.0v1/'):
            self.nuke_folder = 'C:/Program Files/Nuke8.0v1/'
        elif os.path.exists('C:/Program Files/Nuke9.0v1/'):
            self.nuke_folder = 'C:/Program Files/Nuke9.0v1/'
        elif os.path.exists('C:/Program Files/Nuke9.0v5/'):
            self.nuke_folder = 'C:/Program Files/Nuke9.0v5/'
        elif os.path.exists('C:/Program Files/Nuke9.0v7/'):
            self.nuke_folder = 'C:/Program Files/Nuke9.0v7/'
        elif os.path.exists('C:/Program Files/Nuke9.0v9/'):
            self.nuke_folder = 'C:/Program Files/Nuke9.0v9/'
        elif os.path.exists('C:/Program Files/Nuke10.0v3/'):
            self.nuke_folder = 'C:/Program Files/Nuke10.0v3/'
        else:
            self.nuke_folder = None




    def writeRenderScript(self):
        commandStr = "# -*- coding: utf-8 -*-\n\
import nuke\n\
import sys\n\
nuke.scriptOpen('%s')\n\
writeNode  = nuke.toNode('Write1')\n\
camNode    = nuke.toNode('Camera1')\n\
firstframe  = %s\n\
lastframe   = %s\n\
camNode['reload'].execute()\n\
nuke.scriptSave()\n\
nuke.showDag(camNode)\n\
camNode.knob('reload').execute()\n\
camNode['compute_rotation'].setValue(1)\n\
camNode['compute_rotation'].setValue(0)\n\
nuke.scriptSave()\n\
nuke.execute(writeNode , firstframe , lastframe)\n\
print 'Success!'"%(self.script,self.firstframe,self.lastframe)

        f = open(self.script_path + 'Render.py','w')
        f.write(commandStr)
        f.close()




    def executePyScript(self,PyScript):
        if self.nuke_folder == None:
            return None
        nukeCommand = "%s/python.exe %s%s.py"%( self.nuke_folder , self.script_path , PyScript ) 
        #print nukeCommand
        
        if PyScript == 'Render':
            subPopen = subprocess.Popen( nukeCommand , cwd = self.nuke_folder )
            #subPopen.wait()
            #os.remove(os.path.dirname(self.mayadata.mayascript)+'/Render.py')
            return None
        else:
            subPopen = subprocess.Popen( nukeCommand , cwd = self.nuke_folder , stdout = subprocess.PIPE )
            info = subPopen.communicate() 
            print info[0].strip()
            return info[0].strip()






########################################################################################################
########################################################################################################
########################################################################################################
#####Function To Deal With DeadLine#####

def submit_script_to_deadline(projpath,startframe,endframe,writepath,dirname):
    #create plugin file
    plugin_InfoFile = "%s/nuke_plugin_info.job"%dirname

    plugin_fileHandle = open( plugin_InfoFile, "w" )

    plugin_fileHandle.write("SceneFile=%s\n"%(projpath))
    plugin_fileHandle.write("Version=8.0\n\
    Threads=0\n\
    RamUse=0\n\
    BatchMode=False\n\
    BatchModeIsMovie=False\n\
    NukeX=True\n\
    UseGpu=False\n\
    ProxyMode=False\n\
    EnforceRenderOrder=False\n\
    ContinueOnError=False\n\
    Views=\n\
    StackSize=0\n\
    ")

    plugin_fileHandle.close()

    #create submit file
    submit_InfoFile = "%s/nuke_submit_info.job"%dirname

    submit_fileHandle = open( submit_InfoFile, "w" )

    submit_fileHandle.write("Plugin=Nuke\n")
    projectname = os.path.basename(projpath)
    submit_fileHandle.write("Name=%s\n"%(projectname))
    submit_fileHandle.write("Comment=\n\
    Department=\n\
    Pool=comp_nuke\n\
    SecondaryPool= \n\
    Group=none\n\
    Priority=50\n\
    MachineLimit=0\n\
    TaskTimeoutMinutes=0\n\
    EnableAutoTimeout=False\n\
    ConcurrentTasks=1\n\
    LimitConcurrentTasksToNumberOfCpus=True\n\
    LimitGroups=\n\
    JobDependencies=\n\
    OnJobComplete=Nothing\n\
    ")
    submit_fileHandle.write("Frames=%s-%s\n"%(startframe,endframe))
    submit_fileHandle.write("ChunkSize=10\n\
    Whitelist=\n\
    OutputFilename0=%s"%(writepath))
    submit_fileHandle.close()

    subp = subprocess.Popen(["C:/Program Files/Thinkbox/Deadline7/bin/deadlinecommand.exe",\
        submit_InfoFile,\
        plugin_InfoFile])
    subp.wait()
    os.remove(submit_InfoFile)
    os.remove(plugin_InfoFile)




########################################################################################################
########################################################################################################
#########################################WindowsUIElem##################################################
########################################################################################################
########################################################################################################
#BUILT EXTENT PARAMENT OR CREATE A NEW PANEL?
##PySide UI -- GUI code.

class MainWindows(QtGui.QWidget):

    def __init__(self,parent = None):
        #UI init---------------------------------------------------------------------------#
        QtGui.QWidget.__init__(self,parent)
        self.mayadata = SampleData()


        #Define the element in this QWidget.
        logoLabel      = QtGui.QLabel("<font size='12' color='gray'><B>RENDER WIREFRAME TOOL</B></font>")
        logolayout   = QtGui.QVBoxLayout()
        logolayout.addWidget( logoLabel )
        self.frame1 = QtGui.QFrame(self)
        self.frame1.setLayout(logolayout)
        self.frame1.setGeometry(QtCore.QRect(5, 5, 390, 100))
        self.frame1.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame1.setFrameShadow(QtGui.QFrame.Raised)


        self.FFLabel    = QtGui.QLabel('First Frame')
        ff              = cmds.playbackOptions(q = True , minTime= True)
        self.FFText     = QtGui.QLineEdit()
        self.FFText.setText(str(int(ff)))
        self.LFLabel    = QtGui.QLabel('Last Frame')
        lf              = cmds.playbackOptions(q = True , maxTime= True)
        self.LFText     = QtGui.QLineEdit()
        self.LFText.setText(str(int(lf)))
        self.FPSLabel   = QtGui.QLabel('FPS')
        self.FPSText    = QtGui.QLineEdit('24')

        self.camLabel_R = QtGui.QLabel('Main Camera')
        self.camComb_R  = QtGui.QComboBox()
        self.camComb_R.addItems(self.mayadata.getCameralist())
        self.camLabel_L = QtGui.QLabel('Left Camera')
        self.camComb_L  = QtGui.QComboBox()
        self.camLabel_L.setVisible(False)
        self.camComb_L.setVisible(False)
        self.camComb_L.addItems(self.mayadata.getCameralist())
        self.stereoStat = QtGui.QCheckBox('Stereo Shot')
        self.stereoStat.stateChanged.connect(self.stereoChange)


        self.firstgridlayout = QtGui.QVBoxLayout()
        self.CameraLayout    = QtGui.QGridLayout()
        self.CameraLayout.addWidget( self.stereoStat , 1 , 1 )
        self.CameraLayout.addWidget( QtGui.QLabel('') , 1 , 2 )
        self.CameraLayout.addWidget( self.camLabel_R  , 1 , 3 )
        self.CameraLayout.addWidget( self.camComb_R   , 1 , 4 , 1 , 5 ) 
        self.CameraLayout.addWidget( QtGui.QLabel('') , 2 , 1 , 2 , 2 )          
        self.CameraLayout.addWidget( self.camLabel_L  , 2 , 3 )
        self.CameraLayout.addWidget( self.camComb_L   , 2 , 4 , 1 , 5 )
        self.firstgridlayout.addLayout( self.CameraLayout )
        self.TimeLayout      = QtGui.QHBoxLayout()
        self.TimeLayout.addWidget( self.FFLabel )
        self.TimeLayout.addWidget( self.FFText )
        self.TimeLayout.addWidget( self.LFLabel )
        self.TimeLayout.addWidget( self.LFText )
        self.TimeLayout.addWidget( self.FPSLabel )
        self.TimeLayout.addWidget( self.FPSText )     
        self.firstgridlayout.addLayout(self.TimeLayout )
        self.frame2 = QtGui.QFrame(self)
        self.frame2.setLayout(self.firstgridlayout)
        self.frame2.setGeometry(QtCore.QRect(5, 110, 390, 100))
        self.frame2.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame2.setFrameShadow(QtGui.QFrame.Raised)


        self.checkFrame     = QtGui.QCheckBox('Render Gridding')
        self.currentColor   = ColorLabel()
        self.abcfileLabel   = QtGui.QLabel('.abc File')
        self.abcfileText    = QtGui.QLineEdit('')
        self.abcfileText.setText( self.mayadata.getAbcPath() )
        self.abcfileButton  = QtGui.QPushButton('...')
        self.connect( self.abcfileButton , QtCore.SIGNAL('clicked()') , self.abcfileBrowser )
        self.exportButton   = QtGui.QPushButton('Export .abc File')
        self.connect( self.exportButton , QtCore.SIGNAL('clicked()') , self.exportAbcFile )
        self.nukescriptLabel   = QtGui.QLabel('Nuke Script')
        self.nukescriptText    = QtGui.QLineEdit('')
        self.nukescriptText.setText( self.mayadata.getNukePath() )
        self.nukescriptButton  = QtGui.QPushButton('...')
        self.connect( self.nukescriptButton , QtCore.SIGNAL('clicked()') , self.nukescriptBrowser )
        self.renderpathLabel   = QtGui.QLabel('Render Path')
        self.renderpathText    = QtGui.QLineEdit('')
        self.renderpathText.setText( self.mayadata.getRenderPath(stereo = False) )
        self.renderpathButton  = QtGui.QPushButton('...')
        self.connect( self.renderpathButton , QtCore.SIGNAL('clicked()') , self.renderpathBrowser )
        self.renderButton      = QtGui.QPushButton('Render')
        self.connect( self.renderButton , QtCore.SIGNAL('clicked()') , self.submitRender )
        #self.deadline          = QtGui.QCheckBox('Render With Deadline')
        nullLabel        = QtGui.QLabel('')


        funclayout       = QtGui.QVBoxLayout()
        secondgridlayout = QtGui.QGridLayout()
        scriptlayout     = QtGui.QHBoxLayout()
        #renderlayout     = QtGui.QHBoxLayout()
 
        secondgridlayout.addWidget( self.abcfileLabel     , 1 , 1 ) 
        secondgridlayout.addWidget( self.abcfileText      , 1 , 2 )
        secondgridlayout.addWidget( self.abcfileButton    , 1 , 3 )
        secondgridlayout.addWidget( self.exportButton     , 2 , 2 )
        secondgridlayout.addWidget( self.renderpathLabel  , 3 , 1 ) 
        secondgridlayout.addWidget( self.renderpathText   , 3 , 2 )
        secondgridlayout.addWidget( self.renderpathButton , 3 , 3 )   
        secondgridlayout.addWidget( self.nukescriptLabel  , 4 , 1 ) 
        secondgridlayout.addWidget( self.nukescriptText   , 4 , 2 )
        secondgridlayout.addWidget( self.nukescriptButton , 4 , 3 )
        funclayout.addLayout  ( secondgridlayout )
        #scriptlayout.addWidget( self.checkFrame )
        scriptlayout.addWidget( self.currentColor )
        scriptlayout.addWidget( self.renderButton )
        #renderlayout.addWidget( self.deadline )
        #renderlayout.addWidget( self.renderButton )
        funclayout.addWidget  ( nullLabel )
        funclayout.addWidget  ( self.currentColor )
        funclayout.addWidget  ( self.renderButton )
        #funclayout.addLayout  ( renderlayout )
        self.frame3 = QtGui.QFrame(self)
        self.frame3.setLayout(funclayout)
        self.frame3.setGeometry(QtCore.QRect(5, 215, 390, 220))
        self.frame3.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame3.setFrameShadow(QtGui.QFrame.Raised)
        
        label = QtGui.QLabel("State:              Click Export .abc File button to create a abc file,\n\
                        Then modify your nuke script path and click RENDER button to submit rendering.")

        #print self.CameraLayout.cellRect(1,2),self.CameraLayout.cellRect(1,1)
        #Set the layout of QWidget.
        #Globallayout.setVerticalSpacing(10)
        #self.setLayout( Globallayout )
        self.setWindowTitle("RENDER WIREFRAME TOOL v1.5")


        PointToWindow = OpenMayaUI.MQtUtil.mainWindow()
        mainWindow = shiboken.wrapInstance(long(PointToWindow), QtGui.QWidget)
        self.setParent( mainWindow , QtCore.Qt.Window )
        


        #parament init-------------------------------------------------------------------------#
        self.camOperator                     = None
        self.nukeOperator                    = None
        self.foregroundSeq                   = None
        self.backgroundSeq                   = None
        self.nuke_camera_scene_view_imported = None
        self.nuke_camera_scene_view_selected = None
        self.nuke_camera_scene_view_items    = None
        self.nuke_camera_scene_view          = None



    def stereoChange(self,index):
        if index == 0:

            self.camLabel_R.setText('Main Camera')
            self.camComb_L.setVisible(False)          
            self.camLabel_L.setVisible(False)   
            self.renderpathText.setText( self.mayadata.getRenderPath(stereo = False) )  
        else:

            self.camLabel_R.setText('Right Camera')
            self.camComb_L.setVisible(True)          
            self.camLabel_L.setVisible(True) 
            self.renderpathText.setText( self.mayadata.getRenderPath(stereo = True) )



    def abcfileBrowser(self):
        FileDialog = QtGui.QFileDialog( self , "Set Your Abc File Path", "" , 
            "Alembic File (*.abc)")
        FileDialog.setFileMode( QtGui.QFileDialog.ExistingFiles )
        
        FileDialog.open() 
        FileDialog.setDirectory(os.path.dirname(self.mayadata.mayascript))
        if FileDialog.exec_():
            fileNames = FileDialog.selectedFiles()
            for i in fileNames:
                self.abcfileText.setText(i)



    def nukescriptBrowser(self):
        FileDialog = QtGui.QFileDialog( self , "Set Your Nuke Script Path", "" , 
            "NK script (*.nk)")
        FileDialog.setFileMode( QtGui.QFileDialog.ExistingFiles )

        FileDialog.open()
        FileDialog.setDirectory(os.path.dirname(self.mayadata.mayascript))
        if FileDialog.exec_():
            fileNames = FileDialog.selectedFiles()
            for i in fileNames:
                self.nukescriptText.setText(i)



    def renderpathBrowser(self):
        FileDialog = QtGui.QFileDialog( self , "Set Your Render Path", "" , 
            "Picture (*.jpg *.tif *.dpx *.exr)")
        FileDialog.setFileMode( QtGui.QFileDialog.ExistingFiles )

        FileDialog.open()
        FileDialog.setDirectory(os.path.dirname(self.mayadata.mayascript))
        if FileDialog.exec_():
            fileNames = FileDialog.selectedFiles()
            for i in fileNames:
                self.renderpathText.setText(i)      


    #submit nuke script to render and get the foreground sequence.#Choose foreground and background sequence.
    def exportAbcFile(self):
        firstframe = self.FFText.text()
        lastframe  = self.LFText.text()
        if not self.stereoStat.isChecked():
            camNodeList = [self.camComb_R.currentText()]
        else:
            camNodeList = [self.camComb_R.currentText(),self.camComb_L.currentText()]

        selectedGeos = cmds.ls(sl=1)
        for camNode in camNodeList:
            if camNode not in selectedGeos:
              selectedGeos.append(camNode)
        print selectedGeos

        #get a string named self.nuke_camera_scene_view_items.
        self.nuke_camera_scene_view_items    = ' '
        self.nuke_camera_scene_view_imported = ' '
        self.nuke_camera_scene_view_selected = ' '
        self.nuke_camera_scene_view          = ' '
        
        index = 0
        for i in selectedGeos:

            if i not in cmds.listCameras():

                if cmds.listRelatives( i , shapes=1 ) == None:

                    children  = cmds.listRelatives( i , children=1 , fullPath=1 )

                    for j in  children:
                        self.nuke_camera_scene_view_imported += str(index) + ' '
                        self.nuke_camera_scene_view_selected += str(index) + ' '
                        self.nuke_camera_scene_view_items    += '/root' + (cmds.listRelatives( j , shapes = True ,fullPath = 1)[0].replace('|','/')).encode('utf8') + ' '
                        index = index + 1
                else:
                        self.nuke_camera_scene_view_imported += str(index) + ' '
                        self.nuke_camera_scene_view_selected += str(index) + ' '
                        self.nuke_camera_scene_view_items    += '/root' + (cmds.listRelatives( i , shapes = 1 , fullPath = 1 )[0].replace('|','/')).encode('utf8') + ' '
                        index = index + 1        
            
        self.nuke_camera_scene_view = '{{0} imported: ' + self.nuke_camera_scene_view_imported + ' selected:'\
         + self.nuke_camera_scene_view_selected + 'items: ' + self.nuke_camera_scene_view_items + '}'

        #Generate a new command string to execute.
        selectedGeos_str = ""
        path_abc_content = self.abcfileText.text()
        if selectedGeos != []:
            for i in selectedGeos:
                selectedGeos_str += (" -root " + cmds.ls( i ,long = 1 )[0] ) 
            jobArgs = "-frameRange " \
                + self.FFText.text() \
                + " " \
                + self.LFText.text() \
                + " -uvWrite -worldSpace -dataFormat ogawa " \
                + selectedGeos_str \
                + " " + "-file" + " " + str(path_abc_content)
        else:
            jobArgs = "-frameRange " \
                + self.FFText.text() \
                + " " \
                + self.LFText.text() \
                + " -uvWrite -worldSpace -dataFormat ogawa " \
                + selectedGeos_str \
                + " " + " -file " + str(path_abc_content)
            self.info = InfoWindow('Please selecte a geometry and camera at least!')
            self.info.show()
        
        #Export this abc file.
        cmds.AbcExport(jobArg = jobArgs)

        #How to export FBX file!!!
        #selectedlist = cmds.ls(sl = 1)
        #cmds.select(self.camComb.currentText())
        #fbxpath = self.mayadata.getFbxPath()
        #cmds.file( fbxpath , force = 1 , options = "groups=1;ptgroups=1;materials=1;smoothing=1;normals=1" , type = "FBX export" , preserveReferences = 1 , exportSelected = 1 , prompt = False )
        #melcommand = 'FBXExport -file "%s" -s'%fbxpath
        #maya.mel.eval(melcommand)
        #cmds.select(selectedlist)

        self.info = InfoWindow('Success!')
        self.info.show()



    def submitRender(self):
        if not self.stereoStat.isChecked():
            camNodeList = [self.camComb_R.currentText()]
        else:
            camNodeList = [self.camComb_R.currentText(),self.camComb_L.currentText()]

        seqpathList = []
        for camNode in camNodeList:
            imageplane = cmds.listConnections( cmds.listRelatives( camNode , shapes = True )[0] , connections = True , type = 'imagePlane')[-1]
            seqpath    = cmds.getAttr('%s.imageName'%imageplane)
            newseqpath = os.path.dirname(seqpath) + '/'\
             + os.path.splitext(os.path.splitext(os.path.basename(seqpath))[0])[0]\
             + '.####' + os.path.splitext(os.path.basename(seqpath))[-1]

            seqpathList.append(newseqpath)
        
        camDataLsit = []
        for camNode in camNodeList:
            camData = self.mayadata.getCameraData(camNode)
            camDataLsit.append(camData)

        #Create nuke script
        geopath    = self.abcfileText.text()
        writepath  = self.renderpathText.text()
        projpath   = self.nukescriptText.text()
        startframe = self.FFText.text()
        endframe   = self.LFText.text()
        fps        = self.FPSText.text()
        W_size     = cmds.getAttr('%s.coverageX'%imageplane)
        H_size     = cmds.getAttr('%s.coverageY'%imageplane)
        scene_view = self.nuke_camera_scene_view
        stereo     = self.stereoStat.isChecked()


        CreateNukeProject(seqpathList,camDataLsit,geopath,writepath,projpath,startframe,endframe,fps,W_size,H_size,scene_view,stereo,self.currentColor.colorText)


        #if not self.deadline.isChecked():
            #Submit to Local Render.
        self.nukeOperator = nukeScriptOperator(self.nukescriptText.text(),self.FFText.text(),self.LFText.text())

        p = os.path.dirname(self.renderpathText.text())
        if p.find(r'%V') != -1:
            try:
                os.makedirs(p.replace(r'%V','Right'))
                os.makedirs(p.replace(r'%V','Left'))
            except:
                pass
        elif not os.path.exists(p):
            os.makedirs(p)

        self.nukeOperator.writeRenderScript()
        
        self.nukeOperator.executePyScript('Render')
            #os.remove(os.path.dirname(self.mayadata.mayascript)+'/Render.py')
        # else:
        #     dirname = os.path.dirname(self.mayadata.mayascript)
        #     submit_script_to_deadline(projpath,startframe,endframe,writepath,dirname)





class ColorLabel(QtGui.QLabel):
    def __init__(self,parent=None):
        QtGui.QLabel.__init__(self,parent)
        #self.setBackgroundColor(QtGui.QColor(0,0,0))
        #self.setText('   ')
        self.setStyleSheet("background-color:rgb(255,0,0)")
        self.setFixedSize(60,20)
        self.colorText = '1 0 0'


    def mousePressEvent(self,event):
        self.colorDialog = QtGui.QColorDialog()
        self.colorDialog.currentColorChanged.connect(self.setColor)
        self.colorDialog.open()
    
    def setColor(self,color):
        unicstr = "background-color:rgb(%d,%d,%d)"%(color.red(),color.green(),color.blue())
        self.setStyleSheet(unicstr)
        self.colorText = "%f %f %f"%(color.red()/255.0,color.green()/255.0,color.blue()/255.0)
        


#PySide UI -- Info Windows
class InfoWindow(QtGui.QWidget):
    def __init__(self,errorinfo,parent=None):
        QtGui.QWidget.__init__(self,parent)

        self.ErrorText = QtGui.QTextBrowser()

        self.setLayout(QtGui.QVBoxLayout())

        self.layout().addWidget(self.ErrorText)

        self.setWindowTitle("Submit Information")
        self.resize(300,100)
        self.ErrorText.append("<font size='4' color='gray'><B>%s</B></font>"%errorinfo)
        self.setParent( window , QtCore.Qt.Window )




#Instantiation!
window = MainWindows()
window.show()