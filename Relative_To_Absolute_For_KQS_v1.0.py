# -*- coding:utf-8 -*- 
#This class is used for processing relative transform information.

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import maya.cmds as cmds

#Function code.
class AnimationConversion():
    def __init__(self,grdNode,CtrNode,camNode,firstframe,lastframe):
        self.grdNode        = grdNode
        self.CtrNode        = CtrNode
        self.camNode        = camNode
        self.camNodeShape   = cmds.listRelatives(self.camNode)
        self.firstframe     = firstframe
        self.lastframe      = lastframe
        self.newcameraShape = None
        self.newcameraTrans = None


    def doConvert(self):
        #set current time to firsttime
        cmds.currentTime( self.firstframe )

        #delete old AbsoluteCamera.
        origNodes = cmds.ls('AbsoluteCamera*')
        if origNodes != []:
            for i in origNodes:
                try:
                    cmds.delete(i)
                except:
                    pass
        

        #########################################################################################################
        #create new camera to save translate data.
        self.newcameraShape = cmds.createNode( 'camera', skipSelect = True , n = 'AbsoluteCameraShape' )
        self.newcameraTrans = cmds.listRelatives('AbsoluteCameraShape',allParents=True )[0]
        

        #########################################################################################################
        #copy all the attribute of original camera to new camera
        cmds.copyAttr( self.camNode      , self.newcameraTrans , values=True )
        cmds.copyAttr( self.camNodeShape , self.newcameraShape , values=True )
        camAnimList    = cmds.listConnections( self.camNode , d = False , type = 'animCurve' , scn = True)
        for i in camAnimList:
            attrName = cmds.connectionInfo( i + '.output' , destinationFromSource=True )
            attrName = attrName[0].split('.')[-1]
            cmds.copyKey ( self.camNode        , time = (self.firstframe,self.lastframe) , attribute = attrName , option ="curve" )
            cmds.pasteKey( self.newcameraTrans , time = (self.firstframe,self.lastframe) , attribute = attrName , option = 'replace')


        #########################################################################################################
        #Change the relative animation of AbsoluteCameraShape to absolute.
        grdAnimList    = cmds.listConnections( self.grdNode        , d = False , type = 'animCurve' , scn = True)
        camConnectNode = None
        #newcamAnimList = cmds.listConnections( self.newcameraTrans , d = False , type = 'animCurve' , scn = True)
        if grdAnimList != None:
            for i in grdAnimList:
                i = i.encode('utf8')
                attrName = cmds.connectionInfo( i + '.output' , destinationFromSource=True )
                attrName = attrName[0].split('.')[-1]
                firstframevalue = cmds.getAttr( i + ".output" , time = self.firstframe )    

                for frame in range( int( self.firstframe ) , int( self.lastframe ) + 1 ):
                    camvalue = cmds.getAttr( self.camNode + "." + attrName , time = frame )  
                    cmds.setKeyframe( self.newcameraTrans , at = attrName , t = frame , v = camvalue , itt = 'Spline' , ott = 'Spline'  )

                for frame in range( int( self.firstframe ) , int( self.lastframe ) + 1 ):
                    grdvalue = cmds.getAttr( i + ".output" , time = frame )     
                    camvalue = cmds.getAttr( self.camNode + "." + attrName , time = frame )  
                    temp     = firstframevalue - grdvalue +  camvalue
                    #print temp
                    cmds.setKeyframe( self.newcameraTrans , at = attrName , t = frame , v = temp , itt = 'Spline' , ott = 'Spline'  )



        #########################################################################################################
        #Change the relative animation of train to absolute.
        if self.CtrNode != '':
            grdAnimList     = cmds.listConnections( self.grdNode , d = False , type = 'animCurve' , scn = True)
            if grdAnimList != None:
                for i in grdAnimList:
                    print i
                    i = i.encode('utf8')
                    attrName = cmds.connectionInfo( i + '.output' , destinationFromSource=True )
                    attrName = attrName[0].split('.')[-1]
                    firstframevalue = cmds.getAttr( i + ".output" , time = self.firstframe )    

                    for frame in range( int( self.firstframe ) , int( self.lastframe ) + 1 ):
                        Ctrvalue = cmds.getAttr( self.CtrNode + "." + attrName , time = frame )  
                        cmds.setKeyframe( self.CtrNode , at = attrName , t = frame , v = Ctrvalue , itt = 'Spline' , ott = 'Spline'  )

                    for frame in range( int( self.firstframe ) , int( self.lastframe ) + 1 ):
                        grdvalue = cmds.getAttr( i + ".output" , time = frame )  
                        Ctrvalue = cmds.getAttr( self.CtrNode + "." + attrName , time = frame )  
                        temp     = firstframevalue - grdvalue +  Ctrvalue
                        #print temp
                        cmds.setKeyframe( self.CtrNode , at = attrName , t = frame , v = temp , itt = 'Spline' , ott = 'Spline'  )

        
        #########################################################################################################
        #Remove the animation of ground.
        grdAnimList     = cmds.listConnections( self.grdNode , d = False , type = 'animCurve' , scn = True)
        if grdAnimList != None:
            for i in grdAnimList:
                i = i.encode('utf8')
                attrName = cmds.connectionInfo( i + '.output' , destinationFromSource=True )
                attrName = attrName[0].split('.')[-1]
                #print attrName,i + ".output",self.grdNode + "." + attrName
                cmds.disconnectAttr(i + ".output", self.grdNode + "." + attrName)

        return True



##PySide UI -- GUI code.
class MainWindows(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)

        #Define the element in this QWidget.
        self.logoLabel   = QtGui.QLabel("<font size='12' color='gray'><B>CONVERSION TOOL</B></font>")

        self.FFLabel   = QtGui.QLabel('First Frame')
        ff             = cmds.playbackOptions(q = True , minTime= True)
        self.FFText    = QtGui.QLineEdit()
        self.FFText.setText(str(int(ff)))

        self.LFLabel   = QtGui.QLabel('Last Frame')
        lf             = cmds.playbackOptions(q = True , maxTime= True)
        self.LFText    = QtGui.QLineEdit()
        self.LFText.setText(str(int(lf)))

        self.sourceLabel   = QtGui.QLabel('Ground Node')
        self.sourceText    = QtGui.QLineEdit()

        self.handleLabel   = QtGui.QLabel('Control Node')
        self.handleText    = QtGui.QLineEdit()

        self.targetLabel   = QtGui.QLabel('Camera Node')
        self.targetText    = QtGui.QComboBox()
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
        self.targetText.addItems(string_list)

        self.convertButton = QtGui.QPushButton('Convert')

        self.label         = QtGui.QLabel("State:  Input right node then click Convert button,\n            You'll get a new camera named AbsoluteCamera1.")
        self.connect( self.convertButton , QtCore.SIGNAL('clicked()') , self.convert )




        #Set the layout of QWidget.
        self.setWindowTitle("CONVERSION TOOL")
        self.resize(400,300)
        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        layout.addWidget( self.logoLabel    , 1 , 1 , 2 , 2 )
        layout.addWidget( self.FFLabel      , 3 , 1 )
        layout.addWidget( self.FFText       , 3 , 2 )
        layout.addWidget( self.LFLabel      , 4 , 1 )
        layout.addWidget( self.LFText       , 4 , 2 )
        layout.addWidget( self.sourceLabel  , 5 , 1 ) 
        layout.addWidget( self.sourceText   , 5 , 2 )
        layout.addWidget( self.handleLabel  , 6 , 1 ) 
        layout.addWidget( self.handleText   , 6 , 2 )
        layout.addWidget( self.targetLabel  , 7 , 1 ) 
        layout.addWidget( self.targetText   , 7 , 2 )
        layout.addWidget( self.label        , 8 , 1 , 8 , 2 )
        layout.addWidget( self.convertButton, 10 , 1 , 10 , 2 )

        self.setLayout(layout)




    def convert(self):
        firstframe = self.FFText.text()
        lastframe  = self.LFText.text()
        grdNode    = self.sourceText.text()
        CtrNode    = self.handleText.text()
        camNode    = self.targetText.currentText()
        AnimOBJ    = AnimationConversion( grdNode , CtrNode , camNode , firstframe , lastframe )
        try:
            if AnimOBJ.doConvert() == True:
                self.info = InfoWindow('Success!')
                self.info.show()
        except:
            self.info = InfoWindow('Failed!')
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


window = MainWindows()
window.show()