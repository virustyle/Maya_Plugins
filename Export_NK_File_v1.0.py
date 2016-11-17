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

nukeScriptWriter = ScriptWriter()

startframe = 1
endframe = 3
fps = 5

# Create the root node, this specifies the global frame range and frame rate
rootNode = RootNode(startframe, endframe, fps)

nukeScriptWriter.addNode(rootNode)


#create the Camera2 node
campath = 'R:/filmServe/1015_JA_MaiBingBing/VFX/sequences/Test_02/TePi_001_010/Matchmove/publish/v002/TePi_001_010_track_toComp_Kiro_v002.abc'
camNode = Node('Camera2')
camNode.setKnob('inputs',0)
camNode.setKnob('read_from_file','true')
camNode.setKnob('file',campath)
camNode.setKnob('xpos',110)
camNode.setKnob('ypos',123)

nukeScriptWriter.addNode(camNode)


#Create the read node
seqpath = 'R:/filmServe/1015_JA_MaiBingBing/VFX/sequences/Test_02/TePi_001_010/Matchmove/publish/v002/TePi_001_010_track_uvExportA_EXR_jason_v002/TePi_001_010_track_uvExportA_EXR_jason_v002.####.exr'
readNode = Node("Read")
readNode.setKnob('file',seqpath)
readNode.setKnob('first',1051)
readNode.setKnob('last',1100)
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
geopath = 'R:/filmServe/1015_JA_MaiBingBing/VFX/sequences/Test_02/TePi_001_010/CG/scenes/Animation/Alembic/MBB_TePi_001_010_v009.abc'
GeoNode = Node("ReadGeo2")
GeoNode.setKnob('file',geopath)
GeoNode.setKnob('xpos',0)
GeoNode.setKnob('ypos',108)

nukeScriptWriter.addNode(GeoNode)

#create the Constant node
CnstNode = Node("Constant")
CnstNode.setKnob('inputs',0)
CnstNode.setKnob('channels','rgb')
CnstNode.setKnob('xpos',-110)
CnstNode.setKnob('ypos',120)

nukeScriptWriter.addNode(CnstNode)

#create the ScanlineRender node
scanNode = Node("ScanlineRender")
scanNode.setKnob('inputs',3)
scanNode.setKnob('projection_mode','perspective')
scanNode.setKnob('xpos',0)
scanNode.setKnob('ypos',144)
nukeScriptWriter.addNode(scanNode)

#create the Write node
writepath = 'R:/filmServe/1015_JA_MaiBingBing/VFX/sequences/Test_02/TePi_001_010/Zup_renders/Comp/TePi_001_010_slp_project_jason_v005/TePi_001_010_slp_project_jason_v005.%04d.dpx'
writeNode = Node("Write")
writeNode.setKnob('channels','rgba')
writeNode.setKnob('file',writepath)
writeNode.setKnob('file_type','dpx')
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
path = 'D:/'
scriptPath = path + "test.nk"
nukeScriptWriter.writeToDisk(scriptPath)
