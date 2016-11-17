#This script is used for submit nuke script and get output to replace sequence in camera imagePlane.
# -*- coding: utf-8 -*-
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import os
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import sys
import subprocess
import shiboken


script_path = 'D:/'
nuke_folder = 'C:/Program Files/Nuke8.0v5/'


#All of operator on camera is included in this class.
class OperatorOnCamera():
    def __init__(self,camera):
        self.cameraShape = cmds.listRelatives( camera , shapes = True )[0]


    #CORE FUNCTION:
    def createImagePlaneNode(self):
        #get connection list on presented camera.
        if cmds.listConnections(self.cameraShape , connections = True , type = 'imagePlane') != None:
            connectlists = cmds.listConnections(self.cameraShape , connections = True , type = 'imagePlane')
            print connectlists
            for i in range(len(connectlists)/2):
                destination = connectlists[i*2]
                source      = connectlists[i*2+1] 
                sourceNode  = cmds.listRelatives( source , shapes = True )[0] + '.message'
                #Disconnect the link of imagePlane to camera.
                cmds.disconnectAttr( sourceNode , destination )
                #delete node.
                cmds.delete(source)

        #Create foreground imagePlane and background imagePlane.
        cmds.createNode( 'imagePlane', skipSelect = True , n = 'Foreground' )
        cmds.createNode( 'imagePlane', skipSelect = True , n = 'Background' )

        #Connect foreground and background imagePlane to camera.
        cmds.connectAttr('Foreground.message' , '%s.imagePlane[0]'%self.cameraShape)
        cmds.connectAttr('Background.message' , '%s.imagePlane[1]'%self.cameraShape)



    ##Set background sequence.
    def setImagePlaneSeq(self,shapeName,path):
        pathAttr  = cmds.listRelatives( shapeName , parent = True )[0] + '|' + shapeName + '.imageName'
        FrameAttr = cmds.listRelatives( shapeName , parent = True )[0] + '|' + shapeName + '.useFrameExtension'
        DepthAttr = cmds.listRelatives( shapeName , parent = True )[0] + '|' + shapeName + '.depth'
        print path
        cmds.setAttr( pathAttr  , path , type = "string" )
        cmds.setAttr( FrameAttr , 1 )
        if shapeName == 'Foreground':
            cmds.setAttr( DepthAttr , 10 )
        else:
            cmds.setAttr( DepthAttr , 1000 )
        return True





'D:/20151202_for_jon_update_verison/B012C005_140816_R0Y5/nuke/B012C005_140816_R0Y5_comp_sol_v001.nk'

####################################################################################################################
##NukeScriptOperator:
class nukeScriptOperator():
    def __init__(self,script,firstframe,lastframe):
        self.script     = script
        self.firstframe = firstframe
        self.lastframe  = lastframe
        self.SourceSeqs = None




    def writeSourceSeqScript(self):
        commandStr = "# -*- coding: utf-8 -*-\n\
import nuke\n\
import sys\n\
nuke.scriptOpen('%s')\n\
backdroplist = nuke.allNodes('BackdropNode')\n\
for i in backdroplist:\n\
    if i.knob('label').value() == 'FOOTAGE':\n\
        for j in nuke.allNodes('Read'):\n\
            if j.xpos() > i.xpos() and j.ypos() > i.ypos() and j.xpos() < i.xpos() + i['bdwidth'].value() and j.ypos() < i.ypos() + i['bdheight'].value():\n\
                print j.knob('file').value()"%self.script

        f = open(script_path + 'SourceSeq.py','w')
        f.write(commandStr)
        f.close()




    def writeRenderScript(self):
        commandStr = "# -*- coding: utf-8 -*-\n\
import nuke\n\
import sys\n\
nuke.scriptOpen('%s')\n\
writeNodeList = nuke.allNodes('Write')\n\
backdroplist = nuke.allNodes('BackdropNode')\n\
for i in backdroplist:\n\
    if i.knob('label').value() == 'RENDER TO MAYA':\n\
        for j in writeNodeList:\n\
            if j.xpos() > i.xpos() and j.ypos() > i.ypos() and j.xpos() < i.xpos() + i['bdwidth'].value() and j.ypos() < i.ypos() + i['bdheight'].value():\n\
                #firstframe = j.firstFrame()\n\
                #lastframe  = j.lastFrame()\n\
                firstframe  = %s\n\
                lastframe   = %s\n\
                nuke.execute(j , firstframe , lastframe)\n\
                print 'Success!'"%(self.script,self.firstframe,self.lastframe)

        f = open(script_path + 'Render.py','w')
        f.write(commandStr)
        f.close()




    def writeWriteSeqScript(self):
        commandStr = "# -*- coding: utf-8 -*-\n\
import nuke\n\
import sys\n\
nuke.scriptOpen('%s')\n\
writeNodeList = nuke.allNodes('Write')\n\
backdroplist = nuke.allNodes('BackdropNode')\n\
for i in backdroplist:\n\
    if i.knob('label').value() == 'RENDER TO MAYA':\n\
        for j in writeNodeList:\n\
            if j.xpos() > i.xpos() and j.ypos() > i.ypos() and j.xpos() < i.xpos() + i['bdwidth'].value() and j.ypos() < i.ypos() + i['bdheight'].value():\n\
                print j.knob('file').value()"%self.script

        f = open(script_path + 'WriteSeq.py','w')
        f.write(commandStr)
        f.close()




    def executePyScript(self,PyScript):
        nukeCommand = "%s/python.exe %s%s.py"%( nuke_folder , script_path , PyScript ) 
        
        if PyScript == 'Render':
            subPopen = subprocess.Popen( nukeCommand , cwd = nuke_folder )
            return None
        else:
            subPopen = subprocess.Popen( nukeCommand , cwd = nuke_folder , stdout = subprocess.PIPE )
            info = subPopen.communicate() 
            print info[0].strip()
            return info[0].strip()




#BUILT EXTENT PARAMENT OR CREATE A NEW PANEL?
##PySide UI -- GUI code.

class MainWindows(QtGui.QWidget):

    def __init__(self,parent = None):
        #UI init---------------------------------------------------------------------------#
        QtGui.QWidget.__init__(self,parent)
        
        #Define the element in this QWidget.
        self.logoLabel   = QtGui.QLabel("<font size='12' color='gray'><B>REPLACE IMAGEPLANE TOOL</B></font>")

        self.FFLabel   = QtGui.QLabel('First Frame')
        ff             = cmds.playbackOptions(q = True , minTime= True)
        self.FFText    = QtGui.QLineEdit()
        self.FFText.setText(str(int(ff)))

        self.LFLabel   = QtGui.QLabel('Last Frame')
        lf             = cmds.playbackOptions(q = True , maxTime= True)
        self.LFText    = QtGui.QLineEdit()
        self.LFText.setText(str(int(lf)))

        self.nukescriptLabel   = QtGui.QLabel('Nuke Script')
        self.nukescriptText    = QtGui.QLineEdit('D:/20151202_for_jon_update_verison/B012C005_140816_R0Y5/nuke/B012C005_140816_R0Y5_comp_sol_v001.nk')

        self.camLabel   = QtGui.QLabel('Camera Node')
        self.camComb    = QtGui.QComboBox()
        string_list        = cmds.listCameras()
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
        self.camComb.addItems(string_list)


        self.renderButton = QtGui.QPushButton('RENDER')
        self.connect( self.renderButton , QtCore.SIGNAL('clicked()') , self.submitRender )

        self.label         = QtGui.QLabel("State:  Input your nuke script and click RENDER button to submit rendering,\n            Then click REPLACE button to relace imageplane for selected camera.")

        self.replaceButton = QtGui.QPushButton('REPLACE')
        self.connect( self.replaceButton , QtCore.SIGNAL('clicked()') , self.replace )


        #Set the layout of QWidget.
        self.setWindowTitle("REPLACE IMAGEPLANE TOOL")
        self.resize(400,300)
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        layout.addWidget( self.logoLabel        , 1 , 1 , 2 , 2 )
        layout.addWidget( self.camLabel         , 3 , 1 ) 
        layout.addWidget( self.camComb          , 3 , 2 )
        layout.addWidget( self.FFLabel          , 4 , 1 )
        layout.addWidget( self.FFText           , 4 , 2 )
        layout.addWidget( self.LFLabel          , 5 , 1 )
        layout.addWidget( self.LFText           , 5 , 2 )
        layout.addWidget( self.nukescriptLabel  , 6 , 1 ) 
        layout.addWidget( self.nukescriptText   , 6 , 2 )
        layout.addWidget( self.label            , 10 , 1 , 11 , 2 )
        layout.addWidget( self.renderButton     , 6 , 1 , 7  , 2 )
        layout.addWidget( self.replaceButton    , 8 , 1 , 8  , 2 )
        
        self.setLayout(layout)

        PointToWindow = OpenMayaUI.MQtUtil.mainWindow()
        mainWindow = shiboken.wrapInstance(long(PointToWindow), QtGui.QWidget)
        self.setParent( mainWindow , QtCore.Qt.Window )
        

        #parament init-------------------------------------------------------------------------#
        self.camOperator = None
        self.nukeOperator = None
        self.foregroundSeq = None
        self.backgroundSeq = None






    #submit nuke script to render and get the foreground sequence.#Choose foreground and background sequence.
    def submitRender(self):
        self.nukeOperator = nukeScriptOperator(self.nukescriptText.text(),self.FFText.text(),self.LFText.text())
        
        #Get Read Node.
        self.nukeOperator.writeSourceSeqScript()
        self.foregroundSeq = self.nukeOperator.executePyScript('SourceSeq')
        print os.listdir(os.path.dirname(self.foregroundSeq))[1]
        self.foregroundSeq = os.path.dirname(self.foregroundSeq) + '/' + os.listdir(os.path.dirname(self.foregroundSeq))[1]

        #Get Write Node.
        self.nukeOperator.writeWriteSeqScript()
        self.backgroundSeq = self.nukeOperator.executePyScript('WriteSeq')
        if len(os.listdir(os.path.dirname(self.backgroundSeq))) > 1:
            self.backgroundSeq = os.path.dirname(self.backgroundSeq) + '/' + os.listdir(os.path.dirname(self.backgroundSeq))[1]


        #Submit to Render.
        self.nukeOperator.writeRenderScript()
        self.nukeOperator.executePyScript('Render')







    def replace(self):
        firstframe = self.FFText.text()
        lastframe  = self.LFText.text()
        camNode    = self.camComb.currentText()

        self.camOperator = OperatorOnCamera(camNode)
        self.camOperator.createImagePlaneNode()

        #print self.foregroundSeq
        #print self.backgroundSeq
        self.backgroundSeq = os.path.dirname(self.backgroundSeq) + '/' + os.listdir(os.path.dirname(self.backgroundSeq))[1]
        
        self.camOperator.setImagePlaneSeq( 'Foreground' , self.backgroundSeq )
        self.camOperator.setImagePlaneSeq( 'Background' , self.foregroundSeq )

        self.info = InfoWindow('Success!')
        self.info.show()




    



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





#Instantiation!
window = MainWindows()
window.show()