import sys
import os.path
import subprocess


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
      #print self
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
    fileContents = str(self)
    #print fileContents

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
  
  def serializeKnobs(self, knobValues):
    for (key, value) in knobValues.iteritems():
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
      
  def serializeNode(self, nodeType, knobValues, userKnobs):
    self.beginSerializeNode(nodeType)
    self.serializeKnobs(knobValues)
    self.serializeUserKnobs(userKnobs)
    self.endSerializeNode()




########################################################################################################
########################################################################################################
#########################################KnobFormatter##################################################
########################################################################################################
########################################################################################################

class DefaultNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs):
    serializer.serializeNode(nodeType, knobValues, userKnobs)
  

class ReadNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs):
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
    serializer.serializeKnobs(remainingKnobs)
    serializer.serializeUserKnobs(userKnobs)
    
    serializer.endSerializeNode()


class WriteNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs):
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
    for (kw, value) in keywords.iteritems():
      self._knobValues[kw] = value
    #print self
    #print self._knobValues
      
  def setKnob(self, knobName, knobValue):
    self._knobValues[str(knobName)] = knobValue
    
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
    
    return knobFormatter.serialize(serializer, self._nodeType, self._knobValues, self._userKnobs)
  
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
  def __init__(self, first_frame, last_frame, fps=None):
    Node.__init__(self, "Root", first_frame=first_frame, last_frame=last_frame, lock_range='true')
    
    if fps is not None:
      self.setKnob("fps", fps)
  
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


def CreateNukeProject(seqpath,campath,geopath,writepath,projpath,startframe,endframe,fps,W_size,H_size):

    seqpath = seqpath.replace('\\', '/')
    campath = campath.replace('\\', '/')
    geopath = geopath.replace('\\', '/')
    writepath = writepath.replace('\\', '/')
    projpath = projpath.replace('\\', '/')

    nukeScriptWriter = ScriptWriter()

    # Create the root node, this specifies the global frame range and frame rate
    rootNode = RootNode(startframe, endframe, fps)
    
    nukeScriptWriter.addNode(rootNode)
    
    #create the Camera2 node
    camNode = Node('Camera2')
    camNode.setKnob('inputs',0)
    camNode.setKnob('read_from_file','true')
    camNode.setKnob('file',campath)
    camNode.setKnob('xpos',110)
    camNode.setKnob('ypos',123)

    nukeScriptWriter.addNode(camNode)
    
    #Create the read node
    readNode = Node("Read")
    readNode.setKnob('file',seqpath)
    readNode.setKnob('first',startframe)
    readNode.setKnob('last',endframe)
    readNode.setKnob('xpos',0)
    readNode.setKnob('ypos',0)
    
    nukeScriptWriter.addNode(readNode)
    
    #create the UVTile2 node
    UVNode = Node("UVTile2")
    UVNode.setKnob('udim_enable','true')
    UVNode.setKnob('xpos',0)
    UVNode.setKnob('ypos',84)
    
    nukeScriptWriter.addNode(UVNode)
    
    
    #create the ReadGeo2 node
    GeoNode = Node("ReadGeo2")
    GeoNode.setKnob('file',geopath)
    GeoNode.setKnob('xpos',0)
    GeoNode.setKnob('ypos',108)

    nukeScriptWriter.addNode(GeoNode)

    #create the Constant node
    CnstNode = Node("Constant")
    CnstNode.setKnob('inputs',0)
    CnstNode.setKnob('channels','rgb')
    format_str = "\"" + str(W_size) + " " + str(H_size) + " 0 0 " + str(W_size) + " " + str(H_size) + " 1 maya_format(VHQ)" + "\""
    CnstNode.setKnob('format',format_str)
    CnstNode.setKnob('xpos',-110)
    CnstNode.setKnob('ypos',120)

    nukeScriptWriter.addNode(CnstNode)

    #create the ScanlineRender node
    scanNode = Node("ScanlineRender")
    scanNode.setKnob('inputs',3)
    scanNode.setKnob('projection_mode','uv')
    scanNode.setKnob('xpos',0)
    scanNode.setKnob('ypos',144)
    nukeScriptWriter.addNode(scanNode)

    #create the Write node
    writeNode = Node("Write")
    writeNode.setKnob('channels','rgba')
    writeNode.setKnob('file',writepath)
    writeNode.setKnob('file_type','exr')
    writeNode.setKnob('xpos',0)
    writeNode.setKnob('ypos',168)

    nukeScriptWriter.addNode(writeNode)

    #create the Viewer node
    viewNode = Node("Viewer")
    viewNode.setKnob('frame',1001)
    viewNode.setKnob('input_process','false')
    viewNode.setKnob('xpos',0)
    viewNode.setKnob('ypos',204)
    nukeScriptWriter.addNode(viewNode)
    
    # write the script to disk
    scriptPath = projpath
    nukeScriptWriter.writeToDisk(scriptPath)


########################################################################################################
########################################################################################################
#########################################MAYA UI INTERFACE##############################################
########################################################################################################
########################################################################################################

import maya.cmds as maya
maya.window(title = "Create Nuke Project v1.1(VHQ)",w = 520,h = 520)
maya.scrollLayout( 'scrollLayout' )
maya.columnLayout( adjustableColumn=True )


#####Init each var####
if not vars().has_key('seqpath'):
  seqpath = 'R:/filmServe/..exr'

if not vars().has_key('campath'):
  campath = 'R:/filmServe/..abc'
  
if not vars().has_key('geopath'):
  geopath = 'R:/filmServe/..abc'
  
if not vars().has_key('writepath'):
  writepath = 'R:/filmServe/..exr'
  
if not vars().has_key('projpath'):
  projpath = 'R:/filmServe/..nk'
  
if not vars().has_key('startframe'):
  startframe = 1001
if not vars().has_key('endframe'):
  endframe = 1100
if not vars().has_key('fps'):
  fps = 24
if not vars().has_key('W_size'):
  W_size = 2048
if not vars().has_key('H_size'):
  H_size = 2048
if not vars().has_key('abcpath'):
  abcpath = 'R:/filmServe/..abc'



####A command function to get value####
def Commandchange(knobtype,value):
  value = maya.textField(knobtype,q = 1,tx = 1)
  maya.textField(knobtype,edit=True,fi=value)
  if value == "seqpath":
    seqpath = value
  if value == "geopath":
    geopath = value
  if value == "campath":
    campath = value
  if value == "writepath":
    writepath = value
  if value == "projpath":
    projpath = value
  if value == "abcpath":
    abcpath = value

#Set the font of sub UI
Currentfont = "plainLabelFont"

maya.frameLayout( label='Nuke Path Setting', borderStyle='in' )
maya.rowColumnLayout(numberOfColumns=2,columnAttach=[1,"right",0],columnWidth=[[1,100],[2,400]])

#create the script Path input knob
maya.text(label = "Nuke Script Path",align = "right",font = Currentfont)
ScriptPath = maya.textField()
commandstr_spt = "filename = maya.fileDialog2(fileMode=1, caption='Script Path');\
      tempdata = filename[0];\
      maya.textField(ScriptPath,edit=True,fi=tempdata);\
      projpath = tempdata"
maya.textField(ScriptPath,edit=True,w=400,fi=projpath,dgc = commandstr_spt,changeCommand = "Commandchange(ScriptPath,projpath)")


#create the sequences path input knob
maya.text(label="Sequence Path",align = 'right',font = Currentfont)
Sequence = maya.textField()
commandstr_seq = "filename = maya.fileDialog2(fileMode=1, caption='Import Sequence');\
      tempdata = filename[0];\
      maya.textField(Sequence,edit=True,fi=tempdata);\
      seqpath = tempdata"
maya.textField(Sequence,edit=True,w=400,fi=seqpath,dgc = commandstr_seq,changeCommand = "Commandchange(Sequence,seqpath)")


#create the ReadGeo2 path input knob
maya.text(label="Geo Path",align = 'right',font = Currentfont)
Geo = maya.textField()
commandstr_geo = "filename = maya.fileDialog2(fileMode=1, caption='Import Geo');\
      tempdata = filename[0];\
      maya.textField(Geo,edit=True,fi=tempdata);\
      geopath = tempdata"
maya.textField(Geo,edit=True,w=400,fi=geopath,dgc = commandstr_geo,changeCommand = "Commandchange(Geo,geopath)")


#create the camera path input knob
maya.text(label="Camera Path",align = 'right',font = Currentfont)
Camera = maya.textField()
commandstr_cam = "filename = maya.fileDialog2(fileMode=1, caption='Import Camera');\
      tempdata = filename[0];\
      maya.textField(Camera,edit=True,fi=tempdata);\
      campath = tempdata"
maya.textField(Camera,edit=True,w=400,fi=campath,dgc = commandstr_cam,changeCommand = "Commandchange(Camera,campath)")


#create the write path input knob
maya.text(label="Write Path",align = 'right',font = Currentfont)
Write = maya.textField()
commandstr_wrt = "filename = maya.fileDialog2(fileMode=1, caption='Output Sequence');\
      tempdata = filename[0];\
      maya.textField(Write,edit=True,fi=tempdata);\
      writepath = tempdata"
maya.textField(Write,edit=True,w=400,fi=writepath,dgc = commandstr_wrt,changeCommand = "Commandchange(Write,writepath)")


maya.setParent( '..' )
maya.setParent( '..' )


#create the parameter of reader node
maya.frameLayout( label='Global Setting', borderStyle='in' )
maya.rowColumnLayout(numberOfColumns=6,columnAttach=[1,"right",0],columnWidth=[(1,100),(2,60),(3,60),(4,60),(5,60),(6,60)])

#maya.text(label="Seq Parameter",align = 'right',font = 'boldLabelFont')
maya.text(label="firstframe",align = 'right')
first_para = maya.textField()
maya.text(label="lastframe",align = 'right')
last_para = maya.textField()
maya.text(label="fps",align = 'right')
fps_para = maya.textField()
maya.textField(first_para,tx=startframe,w=60,edit=True,enterCommand=('maya.setFocus(\"' + last_para + '\")'))
maya.textField(last_para,tx=endframe,w=60,edit=True,enterCommand=('maya.setFocus(\"' + fps_para + '\")'))
maya.textField(fps_para,tx=fps,w=60,edit=True,enterCommand=('maya.setFocus(\"' + first_para + '\")'))


#create the format input knob
#maya.text(label="WH Parameter",align = 'right',font = 'boldLabelFont')
maya.text(label="Width",align = 'right')
width_para = maya.textField()
maya.text(label="Height",align = 'right')
height_para = maya.textField()
maya.text(label="")
maya.textField(width_para,tx=W_size,w=60,edit=True,enterCommand=('maya.setFocus(\"' + last_para + '\")'))
maya.textField(height_para,tx=H_size,w=60,edit=True,enterCommand=('maya.setFocus(\"' + fps_para + '\")'))

maya.setParent( '..' )
maya.setParent( '..' )



#create Nuke button knob
maya.frameLayout( label='Create Nuke Project', borderStyle='in' )
maya.rowColumnLayout(numberOfColumns=2,columnAttach=[1,"right",0],columnWidth=[(1,60),(2,400)])

maya.text(label = "")
maya.text(label = "")
maya.text(label = "")
maya.button(label="Create Nuke Project!",w = 300,align = "center",command = 
  'seqpath = maya.textField(Sequence,q = 1,tx = 1);\
  campath = maya.textField(Camera,q = 1,tx = 1);\
  geopath = maya.textField(Geo,q = 1,tx = 1);\
  writepath = maya.textField(Write,q = 1,tx = 1);\
  projpath = maya.textField(ScriptPath,q = 1,tx = 1);\
  startframe = maya.textField(first_para,q = 1,tx = 1);\
  endframe = maya.textField(last_para,q = 1,tx = 1);\
  fps = maya.textField(fps_para,q = 1,tx = 1);\
  W_size = maya.textField(width_para,q = 1,tx = 1);\
  H_size = maya.textField(height_para,q = 1,tx = 1);\
  CreateNukeProject(seqpath,campath,geopath,writepath,projpath,startframe,endframe,fps,W_size,H_size)')
maya.text(label = "")

maya.setParent( '..' )
maya.setParent( '..' )



#create Alembic button knob
maya.frameLayout( label='Create Alembic File', borderStyle='out' )
maya.columnLayout()

maya.frameLayout( label='           Set Alembic Parameter', borderStyle='in' )
maya.rowColumnLayout(numberOfColumns=2,columnAttach=[1,"right",0],columnWidth=[(1,100),(2,400)])
maya.text(label = "abcExport Path")
path_abc = maya.textField()
commandstr_abcpath = "filename = maya.fileDialog2(fileMode=1, caption='Export Alembic');\
      tempdata = filename[0];\
      maya.textField(path_abc,edit=True,fi=tempdata);\
      abcpath = tempdata"
maya.textField(path_abc,edit=True,w=400,fi=abcpath,dgc = commandstr_abcpath,changeCommand = "Commandchange(path_abc,abcpath)")
maya.setParent( '..' )

maya.rowColumnLayout(numberOfColumns=4,columnAttach=[1,"right",0],columnWidth=[(1,100),(2,60),(3,60),(4,60)])
#maya.text(label = "FrameRange")
maya.text(label="firstframe",align = 'right')
first_abc = maya.textField()
maya.text(label="lastframe",align = 'right')
last_abc = maya.textField()
first_abc_ff = maya.playbackOptions(q = 1, min = 1)
last_abc_lf = maya.playbackOptions(q = 1, max = 1)
maya.textField(first_abc , tx = first_abc_ff , w=60 , edit=True , enterCommand=('maya.setFocus(\"' + last_abc + '\")'))
maya.textField(last_abc , tx = last_abc_lf , w=60 , edit=True , enterCommand=('maya.setFocus(\"' + first_abc + '\")'))

maya.setParent( '..' )
maya.setParent( '..' )


maya.frameLayout( label='           Create Alembic File', borderStyle='in' )
maya.columnLayout()
path_abc_content = ""
jobArgs = ""



def getjobArg():
  selectedGeos = maya.ls(sl=1)
  selectedGeos_str = ""
  path_abc_content = maya.textField(path_abc,q = 1,tx = 1)
  if maya.ls(sl=1) != []:
    if len(selectedGeos) == 1:
      for i in selectedGeos:
        selectedGeos_str = str(i)
    else:
      for i in selectedGeos:
        selectedGeos_str += ("|" + str(i))
  
    jobArgs = "-frameRange " \
    + maya.textField(first_abc,q = 1,tx = 1) \
    + " " \
    + maya.textField(last_abc,q = 1,tx = 1) \
    + " -uvWrite -worldSpace -root " \
    + selectedGeos_str \
    + " " + "-file" + " " + str(path_abc_content)
  else:
    jobArgs = "-frameRange " \
    + maya.textField(first_abc,q = 1,tx = 1) \
    + " " \
    + maya.textField(last_abc,q = 1,tx = 1) \
    + " -uvWrite -worldSpace " \
    + " " + "-file" + " " + str(path_abc_content)
  return jobArgs

maya.button(label="Create .abc File!",w = 300,command = "Argsstr = getjobArg();\
  maya.AbcExport(jobArg = Argsstr)")

maya.text(label = "  Select the model or camera and set the framerange,\n\
  then you can click 'Create .abc File!' button to export abc file.",w = 300,al = "left")

maya.setParent( '..' )
maya.setParent( '..' )


#create button knob
maya.frameLayout( label='Release Note', borderStyle='in' )
maya.columnLayout()

maya.text(label = "")
maya.text(label="  This tool is written for created nuke project which cast UV sequence to model.",align = 'left',w = 500)
maya.text(label = "")

maya.setParent( '..' )
maya.setParent( '..' )


maya.showWindow()





########################################################################################################
######@FOR VHQ##########################################################################################
###################################################################################@Write By Sol He#####
########################################################################################################
########################################################################################################