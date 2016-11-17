#This Tool is written for collecting data from mantis.
#BY SOL
#DATA: 20160224




# -*- coding: utf-8 -*-


########################################################################################################################
########################################################################################################################
########## #####  # ##### # #### ###      ############# ##### #####   ###### ##### ##       #####  #####      ##########
######### # #### ## #### ## ## #### ################## # ### # ### ### ##### #### ###### ############# #################
######## ## ### ## #### ##  #######      ############ ## ## ## ### ### #### # ### ###### ####### #####     #############
####### ### ## ## #### ### # ###### ################ ### # ### ##       ## ## ## ###### ####### ############ ###########
###### #### # ## #### ### ### #### ################ #### # ### ## ##### ## ### # ###### ####### ########### ############
##### ##### ###### ##### #####  ##        ######## ##### ##### # #######  ##### ###### ####### #####       #############
########################################################################################################################
########################################################################################################################





import urllib
import urllib2
import cookielib
import xml.dom.minidom
import htmllib
import re
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui


##############################################################
#########################global class#########################
##############################################################
class ParentWindow(QtGui.QWidget):
    def __init__(self , parent=None ):
        QtGui.QWidget.__init__(self, parent)

        self.rownumber = 0
        self.shotslist = []
        self.status_time = 0
        self.shot_time = 0
        self.subshotslist = []
        self.submitdata = {}
        self.newstream = None
        self.statusClickIndex = None
        
##############################################################
##############################################################
##############################################################



#from matis_nuke_ui import Update_Version_Comment

#this class is used for processing the stream of nuke_mantis operation!
#All the operation is based on the cookie system!
#mantis is a easy website,if you want to add some new function to operate this class,please check the package of GET&POST!

class MantisStream(ParentWindow):
    #the object must include username,password.
    def __init__(self,username,password,parent=None):

        ParentWindow.__init__(self, parent)

        #initialize this class
        self.username = username
        self.password = password
        self.loginpage = 'http://192.168.0.58:13389/mantisbt/login.php'
        
        #CREATE A GLOBAL COOKIE,ALL THE REQUEST OPERATION NEED THIS! 
        self.cookie = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))


        #create the status of my account ID.
        self.loginstatus = False


        #create a data construct!
        self.projdict = {}
        self.myshotsnum = 0
        self.myshotslist = []

        self.gantItem = None

        print "Initialize Success!"


    def login(self):
        #login the mantis
        postdata = urllib.urlencode({
                                    'return':'index.php',
                                    'username':self.username,
                                    'password':self.password,
                                    'secure_session':'on'
                                    })
        req = urllib2.Request(
                            url = self.loginpage,
                            data = postdata
                            )
        self.opener.open(req)

        self.opener.open('http://192.168.0.58:13389/mantisbt/my_view_page.php')
        self.opener.open('http://192.168.0.58:13389/mantisbt/my_message_view_data.php')
        print "Login Mantis!"


    def quit(self):

        self.opener.open('http://192.168.0.58:13389/mantisbt/logout_page.php')

        print "Logout From Mantis!"





    def getAllProjections(self):
        #this function is used to get the projections in mantis!
        projectdata = urllib.urlencode({
                        'name':'project_id',
                        'class':'small',
                        'onchange':'document.forms.form_set_project.submit();',
                        'value':'0',
                        'selected':'selected'
                        })
        getProject_req = urllib2.Request(
                        url = 'http://192.168.0.58:13389/mantisbt/set_project.php',
                        data = projectdata
                        )

        projresult = self.opener.open(getProject_req)
        projresult = projresult.read()

        #update a new dictionary of projections!
        self.projdict = {}
        parseout = re.findall('<option value=.*</option>',projresult)
        for i in parseout:
            item = re.match('.*="(\d*)".*>(.+)</option>',i)
            if item:
                #print item.group(1),item.group(2)
                self.projdict[item.group(1)] = item.group(2)
                print item.group(2)

        return self.projdict





    def getShots(self,projIndex):

        if projIndex == 0:

            #this funciton is used to get all my shots in mantis!
            sheetdata = urllib.urlencode({
                    'page':'1',
                    'rows':'1000'
                    })
            myshot_req = urllib2.Request(
                    url = 'http://192.168.0.58:13389/mantisbt/my_shot_data.php',
                    data = sheetdata
                    )

            AllMyShots = self.opener.open(myshot_req)
            AllMyShots = AllMyShots.read()

        else:

            #this funtion is used to get my shots in specific projection in mantis!
            #request set project page
            sheetdata_1 = urllib.urlencode({
                    'project_id':projIndex
                    })
            myshot_req_1 = urllib2.Request(
                    url = 'http://192.168.0.58:13389/mantisbt/set_project.php',
                    data = sheetdata_1
                    )

            self.opener.open(myshot_req_1)


            #request my_shot_data page
            sheetdata_2 = urllib.urlencode({
                    'page':'1',
                    'rows':'1000'
                    })
            myshot_req_2 = urllib2.Request(
                    url = 'http://192.168.0.58:13389/mantisbt/my_shot_data.php',
                    data = sheetdata_2
                    )
            
            AllMyShots = self.opener.open(myshot_req_2)
            AllMyShots = AllMyShots.read()

        
        #parse the string we got from webpage!
        parseshotdata = re.match('{"total" : (\d+),.+"rows" :(.+)}',AllMyShots)
        if parseshotdata:
            self.myshotsnum = parseshotdata.group(1)

            myshotsrow = parseshotdata.group(2)
            myshotsrow = myshotsrow[2:]
            myshotsubdata = re.findall('{[^{^}]*}',myshotsrow)
            if myshotsubdata:
                self.myshotslist = []
                for i in myshotsubdata:

                    tempdict = {}

                    #get id value.
                    tempgroup_id = re.match('.*"id":"([^"]*)".*',i)
                    tempdata_id = tempgroup_id.group(1)
                    tempdict['Thumbnail'] = tempdata_id


                    #get shotname value.
                    tempgroup_cid = re.match('.*"category_id":"([^"]*)".*',i)
                    tempdata_cid = tempgroup_cid.group(1)
                    tempgroup_cont = re.match('.*"content":"([^"]*)".*',i)
                    tempdata_cont = tempgroup_cont.group(1)
                    if tempdata_cid != tempdata_cont:
                        tempdict['Shot'] = [tempdata_cid,tempdata_cont]
                    else:
                        tempdict['Shot'] = [tempdata_cid]


                    #get shotid value.
                    tempgroup_shotid = re.match('.*"shot_id":"(\d+)",.*',i)
                    tempdata_shotid = tempgroup_shotid.group(1)
                    tempdict['shot_id'] = tempdata_shotid


                    #get status value.
                    tempgroup_sta = re.match('.*"Status":"[^,]*>([\w-]*)<[^,]*".*',i)
                    tempdata_sta = tempgroup_sta.group(1)
                    tempdict['Status'] = tempdata_sta


                    #get project_name value.
                    tempgroup_prj = re.match('.*"project_name":"(\w+)",.*',i)
                    tempdata_prj = tempgroup_prj.group(1)
                    tempdict['project_name'] = tempdata_prj
                    
            
                    #get project_id value.
                    tempgroup_pri = re.match('.*"project_id":"(\w+)",.*',i)
                    tempdata_pri = tempgroup_pri.group(1)
                    tempdict['project_id'] = tempdata_pri
                     

                    #get status_id value.
                    tempgroup_staid = re.match('.*"status_id":"(\d+)",.*',i)
                    tempdata_staid = tempgroup_staid.group(1)
                    tempdict['status_id'] = tempdata_staid
                    

                    #get date_submitted value.
                    tempgroup_datasub = re.match('.*"date_submitted":"([\d-]+ [\d:]+)",.*',i)
                    tempdata_datasub = tempgroup_datasub.group(1)
                    tempdict['date_submitted'] = tempdata_datasub


                    self.myshotslist.append(tempdict)


        return self.myshotsnum,self.myshotslist


    def submitShots(self,shotid,version,comment):
        
        #submitPanel = Update_Version_Comment()
        #submitPanel.show()

        #give a pannel to choose vesion and add text comment.
        shotdict = {}
        for shot in self.myshotslist:
            if shot['shot_id'] == shotid:
                shotdict = shot

        #initilize the value of sheet keys
        v_bug_id = ''
        v_update_mode = 1
        v_s_report_id = ''
        v_update_comment = 1
        v_bug_update_token = ''
        v_handler_id = ''
        v_status_val = ''
        v_status = shotdict['Status']
        v_get_project = shotdict['project_id']
        v_version = version
        v_build = ''
        v_date_submitted = shotdict['date_submitted']
        v_name = ''
        v_bugnote_text = comment
        

        sheetdata = urllib.urlencode({
            'bug_id':int(shotid)
            })
        myshot_rep = urllib2.Request(
            url = 'http://192.168.0.58:13389/mantisbt/bug_update_page.php',
            data = sheetdata
            )
        #print shotid
        result = self.opener.open(myshot_rep)
        result = result.read()

        #get the value of sheet keys
        v_bug_id = int(shotid)

        m_s_report_id = re.match('[\S\s]+name="s_report_id" value="(\d+)"[\S\s]+',result)
        if m_s_report_id:
            v_s_report_id = m_s_report_id.group(1)

        m_handler_id = re.match('[\S\s]+input id="handler_id" name="handler_id" type="(\w+)" value="(\w+)"[\S\s]+',result)
        if m_handler_id:
            v_handler_id = m_handler_id.group(2)

        m_status_val = re.match('[\S\s]+input id="status_val" name="status_val" type="(\w+)"\s*value="(\d+)"[\S\s]+',result)
        if m_status_val:
            v_status_val = m_status_val.group(2)
            v_status = v_status_val

        m_name = re.match('[\S\s]+input type="(\w+)" name="name" id="name" value="(\d+)"[\S\s]+',result)
        if m_name:
            v_name = m_name.group(2)

        m_build = re.match('[\S\s]+input id="build" name="build" type="(\w+)" value="([\d-]+ [\d:]+)"[\S\s]+',result)
        if m_build:
            v_build = m_build.group(2)

        m_bug_update_token = re.match('[\S\s]+name="bug_update_token" value="(\w+)"[\S\s]+',result)
        if m_bug_update_token:
            v_bug_update_token = m_bug_update_token.group(1)

        print v_bug_id
        print v_update_mode
        print v_s_report_id
        print v_update_comment
        print v_bug_update_token
        print v_handler_id
        print v_status_val
        print v_status
        print v_get_project
        print v_version
        print v_build
        print v_date_submitted
        print v_name
        print v_bugnote_text


        sheetdata_update = urllib.urlencode({
            'bug_id'          : v_bug_id,
            'update_mode'     : v_update_mode,
            's_report_id'     : v_s_report_id,
            'update_comment'  : v_update_comment,
            'bug_update_token': v_bug_update_token,
            'handler_id'      : v_handler_id,
            'status_val'      : v_status_val,
            'status'          : v_status,
            'get_project'     : v_get_project,
            'version'         : v_version,
            'build'           : v_build,
            'date_submitted'  : v_date_submitted,
            'name'            : v_name,
            'bugnote_text'    : v_bugnote_text,
            })
        comment_update_rep = urllib2.Request(
            url = 'http://192.168.0.58:13389/mantisbt/bug_update.php',
            data = sheetdata_update
            )
        result_update = self.opener.open(comment_update_rep)
        result_update = result_update.read()






    #run when MantisWindow instance loading the data of current projection
    #loaddata will trigger this function runs.
    def getGanttData(self,projIndex):
        if projIndex == 0:

            print "Please choose a project!"

        else:

            #this funtion is used to get my shots in specific projection in mantis!
            #request set project page
            sheetdata_1 = urllib.urlencode({
                    'project_id':projIndex
                    })
            myshot_req_1 = urllib2.Request(
                    url = 'http://192.168.0.58:13389/mantisbt/set_project.php',
                    data = sheetdata_1
                    )

            self.opener.open(myshot_req_1)


            #request my_shot_data page
            sheetdata_2 = urllib.urlencode({
                    'type':'1',
                    'page':'1',
                    'rows':'1000'
                    })
            myshot_req_2 = urllib2.Request(
                    url = 'http://192.168.0.58:13389/mantisbt/vhq_gantt_chart_data.php',
                    data = sheetdata_2
                    )
            
            AllMyShots = self.opener.open(myshot_req_2)
            AllMyShots = AllMyShots.read()


            parseData = re.match(r'{"main".*"data" :(.*)}',AllMyShots)
            self.gantItem = re.findall('{[^{^}]*}',parseData.group(1))

           



    def getItemFromGanttData(self,shotname):
        self.index = None
        itemdictionary = {}
        if self.gantItem:
            for index in range(len(self.gantItem)):
                list_in_item = re.findall(r'[^{^}^:^,^"]*',self.gantItem[index])
                if list_in_item[12] == shotname:
                    self.index = index
                    break
            
            #get a dictionary of this item.
            for item in self.gantItem[self.index + 1:]:
                list_in_item = re.findall(r'[^,]*',item)
                #print list_in_item
                if re.findall(r'compositing',list_in_item[2]):
                    itemdictionary['compositing'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'CameraTracking',list_in_item[2]):
                    itemdictionary['CameraTracking'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'RotoPaint',list_in_item[2]):
                    itemdictionary['RotoPaint'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'Effects',list_in_item[2]):
                    itemdictionary['Effects'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'MattePainting',list_in_item[2]):
                    itemdictionary['MattePainting'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'Animation',list_in_item[2]):
                    itemdictionary['Animation'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                elif re.findall(r'Texturelighting',list_in_item[2]):
                    itemdictionary['Texturelighting'] = re.findall(r'[^:^"]*',list_in_item[16])[-3]
                    #print re.findall(r'[^:^"]*',list_in_item[16])[-3]
                else:
                    #print "Finish!"
                    break

        #print itemdictionary
        return itemdictionary

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import functools
import urllib2
import json

import os

import threading
import time





#rownumber = 10
#usrname = 'Comp_yangming'
#pasword = '285458486'

usrname = None
pasword = None

#versionValue = None
#commentValue = None





class MantinsWindow( ParentWindow ):
    def __init__(self , parent=None  ):
        #super(MantinsWindow, self).__init__( parent=None )

        ParentWindow.__init__(self, parent)

        ParentWindow.rownumber = 0
        ParentWindow.shotslist = []
        ParentWindow.status_time = 0
        ParentWindow.shot_time = 0

        #define login widget
        logo = QtGui.QLabel('logo')
        vhqicon = QtGui.QIcon( '/icons/icon_py/vhq.jpg' )
        pixmap = vhqicon.pixmap(251 , 117 , QtGui.QIcon.Active , QtGui.QIcon.On)
        logo.setPixmap(pixmap)

        username = QtGui.QLabel('Username')
        password = QtGui.QLabel('Password')
        self.username_context = QtGui.QLineEdit(usrname)
        self.password_context = QtGui.QLineEdit(pasword)
        self.password_context.setEchoMode(QtGui.QLineEdit.Password)
        refreshbutton = QtGui.QPushButton( "Refresh Data" )
        #self.usrname = self.username_context.text()
        #self.pasword = self.password_context.text()


        loginlayout = QtGui.QGridLayout()
        loginlayout.addWidget( username , 1 , 0)
        loginlayout.addWidget( password , 2 , 0)
        loginlayout.addWidget( self.username_context , 1 , 1)
        loginlayout.addWidget( self.password_context , 2 , 1)
        loginlayout.addWidget( refreshbutton , 3 , 1 )
        self.connect( refreshbutton , QtCore.SIGNAL('clicked()') , self.refresh)


        logolayout = QtGui.QHBoxLayout()
        logolayout.addWidget( logo )
        logolayout.addLayout( loginlayout )

        #define combo widget
        string_list = []
        self.combo = QtGui.QComboBox()
        self.combo.addItems(string_list)


        #define table widget
        self.myTable = QtGui.QTableWidget()
        self.myTable.header = [ 'Thumbnail' , '       Shot       ' , 'Status' , 'NukeScript' , '   update  ','ShotValue' , 'StatusValue']
        self.myTable.setColumnCount( len( self.myTable.header ))
        self.myTable.setHorizontalHeaderLabels( self.myTable.header )
        self.myTable.setSelectionMode( QtGui.QTableView.ExtendedSelection )
        self.myTable.setSelectionBehavior( QtGui.QTableView.SelectRows )
        self.myTable.setSortingEnabled( True )
        #self.myTable.sortByColumn( 1, QtCore.Qt.DescendingOrder )
        self.myTable.setAlternatingRowColors( True )
        self.myTable.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        self.myTable.setEditTriggers( QtGui.QAbstractItemView.NoEditTriggers )
        self.myTable.resizeColumnsToContents()
        self.myTable.resizeRowsToContents()
        self.myTable.verticalHeader().setDefaultSectionSize(50)
        self.dynamicTable( ParentWindow.rownumber )
        self.myTable.setColumnWidth(5,0)
        self.myTable.setColumnWidth(6,0)

        #sort by horizontalheader!
        self.myTable.horizontalHeader().sectionClicked.connect(self.sortByCol)

        self.myTable.setSizePolicy( QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum , QtGui.QSizePolicy.Minimum ))
        

        proglayout = QtGui.QHBoxLayout()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progText = QtGui.QLabel("                  Loading Status...      ")
        proglayout.addWidget( self.progText )
        proglayout.addWidget( self.progressBar )
        proglayout.addWidget( self.progText )
        #self.progressBar.setGeometry(30, 40, 200, 25)

        layout = QtGui.QGridLayout()
        layout.setSpacing(10)
        layout.addLayout( logolayout , 1 , 0)
        layout.addWidget( self.combo , 2 , 0 )
        layout.addWidget( self.myTable , 3 , 0 , 5 , 0)
        layout.addLayout( proglayout , 6 , 0 )
        self.progressBar.hide()
        self.progText.hide()

        #global setting of widget
        #self.getProjNow()
        self.projectname = self.combo.currentText()
        self.combo.currentIndexChanged.connect(self.loaddata)
        self.setLayout(layout)
        self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Minimum , QtGui.QSizePolicy.Minimum ))


    
    def sortByCol(self,num):
        #print num
        if num == 1:
            if ParentWindow.shot_time:
                self.myTable.sortByColumn( 5 , QtCore.Qt.AscendingOrder  )
            else:
                self.myTable.sortByColumn( 5 , QtCore.Qt.DescendingOrder )

            if ParentWindow.shot_time == 0:
                ParentWindow.shot_time = 1
            else:
                ParentWindow.shot_time = 0
        elif num == 2:
            if ParentWindow.status_time:
                self.myTable.sortByColumn( 6 , QtCore.Qt.AscendingOrder  )
            else:
                self.myTable.sortByColumn( 6 , QtCore.Qt.DescendingOrder )

            if ParentWindow.status_time == 0:
                ParentWindow.status_time = 1
            else:
                ParentWindow.status_time = 0


    #create Dynamic function of mytable!
    #signal and slot of button!
    def dynamicTable(self,numb):
        
        self.myTable.clearContents()
        self.myTable.setRowCount( numb )

        self.scriptlist = []
        self.updatelist = []
        self.thumblist = []
        self.shotname = []
        self.status = []
        self.shotvalue = []
        self.statusvalue = []

        for n in range(0, numb):
            self.scriptlist.append( 'Load' )
            self.updatelist.append( 'Update' )
            self.thumblist.append( 'thumbnail_' + str(n + 1) )
            self.shotname.append( 'shotname_' + str(n + 1) )
            self.status.append( 'status_' + str(n + 1) )
            self.shotvalue.append( 'shotvalue_' + str(n + 1) )
            self.statusvalue.append( 'statusvalue_' + str(n + 1) )

        for n in range(0, numb):
            
            #click load script signal
            self.scriptlist[n] = QtGui.QPushButton( str(self.scriptlist[n]) )
            self.myTable.setCellWidget( n , 3 , self.scriptlist[n] )
            self.connect( self.scriptlist[n] , QtCore.SIGNAL( 'clicked()' ) , functools.partial(self.loadscript , n ) )
            
            #click load asset signal
            self.updatelist[n] = QtGui.QPushButton( str(self.updatelist[n]) )
            self.myTable.setCellWidget( n , 4 , self.updatelist[n] )
            self.connect( self.updatelist[n] , QtCore.SIGNAL( 'clicked()' ) , functools.partial(self.subwindow , n) )
            
            #set icon of thumbnail
            self.thumblist[n] = QtGui.QLabel() 
            self.thumblist[n].setScaledContents(True)
            self.myTable.setCellWidget( n , 0 , self.thumblist[n] )

            #set name of shot 
            self.shotname[n] = QtGui.QLabel() 
            self.myTable.setCellWidget( n , 1 , self.shotname[n] )

            #set status of shot
            self.status[n] = MyLabel(str(n),self) 
            self.myTable.setCellWidget( n , 2 , self.status[n] )

            #set namevalue of shot 
            self.shotvalue[n] = QtGui.QTableWidgetItem() 
            self.myTable.setItem( n , 5 , self.shotvalue[n] )

            #set statusvalue of shot
            self.statusvalue[n] = QtGui.QTableWidgetItem() 
            self.myTable.setItem( n , 6 , self.statusvalue[n] )

            


    #get projection showed in combo
    def getProjNow(self):
        #reload the items of table
        self.projectname = self.combo.currentText()
        #print self.projectname



    def refresh(self):

        #request data from mantis with Class MantisStream !
        self.usrname = self.username_context.text()
        self.pasword = self.password_context.text()
        ParentWindow.newstream = MantisStream(self.usrname,self.pasword)
        ParentWindow.newstream.login()
        dict_prj = ParentWindow.newstream.getAllProjections()
        

        #get the list of keys&values of projection dictionary.
        #print dict_prj
        dict_prj_values = dict_prj.values()
        dict_prj_keys = dict_prj.keys()
        #print dict_prj_values
        dict_prj_keys.sort()
        #print dict_prj_keys
        dict_prj_values = [dict_prj[i] for i in dict_prj_keys]


        #refresh the construct of comb!
        self.combo.clear()
        self.combo.addItems( dict_prj_values )
        
        #refresh the construct of table!
        #print self.rownumber
        self.rownumber = int( ParentWindow.newstream.getShots(0)[0] )
        #print self.rownumber
        self.dynamicTable( self.rownumber )
        

        #load the data from mantis to table!
        #print self.combo.currentText()

        ParentWindow.shotslist = ParentWindow.newstream.getShots(9)[1]
        #print self.shotslist
        self.loaddata(0)
        #print self.shotslist


    
    #load the data of current projection
    def loaddata(self,index):

        self.progressBar.show()
        self.progText.show()
        self.progressBar.setValue(0) 
        #collating of data!
        if index == 0:
            ParentWindow.subshotslist = ParentWindow.shotslist
            self.subrownumber = self.rownumber
            self.myTable.setRowCount( self.subrownumber )
            projectname = 'All Projects'
            self.dynamicTable( self.subrownumber )
        else:
            projectname = self.combo.itemText( index )
            ParentWindow.subshotslist = []
            self.subrownumber = 0
            for i in ParentWindow.shotslist:
                if i['project_name'] == projectname:
                    ParentWindow.subshotslist.append(i)
                    self.subrownumber += 1
            #projectname = self.combo.itemText( index )
            #print projectname
            #refresh the construct of table!
            self.dynamicTable( self.subrownumber )

        if index != 0 and ParentWindow.subshotslist != []:
            projectID = ParentWindow.subshotslist[0]['project_id']
            def worker():
                ParentWindow.newstream.getGanttData(projectID)
                print 'Finished Update!'
                self.progressBar.setValue(100) 

            newthread = threading.Thread(target = worker)
            newthread.start()
            for i in range(100):
                time.sleep(0.2)
                if newthread.isAlive():
                    self.progressBar.setValue(i) 
                else:
                    break

        #set value of data dictionary to tablelist!
        #print projectname
        self.loadthumbnail()
        #print self.subrownumber
        #print len(ParentWindow.subshotslist)
        self.loadshot()
        self.loadstatus()
        time.sleep(0.2)
        self.progressBar.hide()
        self.progText.hide()



    def loadscript(self,n):
        projname =  ParentWindow.subshotslist[n]['project_name']
        shotnm =  ParentWindow.subshotslist[n]['Shot'][0]
        try:
            print ParentWindow.subshotslist[n]['Shot'][1]
        except:
            print "there aren't second name"

        #print ParentWindow.subshotslist[n].get('project_name')
        #print ParentWindow.subshotslist[n].get('Shot')

        #begin to analysis
        maxversionscript = FindNukeFile(projname,shotnm).openScript()
        print maxversionscript
        nuke.scriptOpen(maxversionscript)




    def subwindow(self,n):


        self.versionValue_a = None
        self.commentValue_a = None

        self.submitPanel = Update_Version_Comment( n )
        
        self.submitPanel.show()



        

    def loadthumbnail(self):
        #check if the folder exist!
        if os.path.exists('D:/Nuke_Mantis_thumnail'):
            pass
        else:
            os.makedirs('D:/Nuke_Mantis_thumnail')

        for n in range(0, self.subrownumber):
            #print n
            temppath_pic = str( ParentWindow.subshotslist[n]['Thumbnail'] )
            temppath_pic = ('/').join(temppath_pic.split('\\/'))
            temppath_pic2 = temppath_pic.split('/')[-1]
            temppath_pic_localpath = 'D:/Nuke_Mantis_thumnail/' + temppath_pic2
            
            if os.path.exists( temppath_pic_localpath ):
                pass
            else:
                self.downloadPic(temppath_pic)


            #print temppath_pic_localpath
            self.thumblist[n].setPixmap( QtGui.QPixmap( temppath_pic_localpath ) )




    def downloadPic(self,pathtail):
        #download!
        pathtail2 = pathtail.split('/')[-1]
        temppath_pic_webpath = 'http://192.168.0.58:13389/mantisbt/' + pathtail
        #print temppath_pic_webpath
        #x = json.loads( '{"foo":"%s"}' %temppath_pic_webpath )
        #x0=x['foo']
        #print x0
        try:
            conn = urllib.urlopen( temppath_pic_webpath )
            print 'D:/Nuke_Mantis_thumnail/' + pathtail2
            f = open('D:/Nuke_Mantis_thumnail/' + pathtail2 , 'wb' )
            f.write(conn.read())
            f.close()
        except:
            return




    def loadshot(self):
        for n in range(0, self.subrownumber):
            self.shotname[n].setText( str(ParentWindow.subshotslist[n]['Shot'][0]) )
            self.shotname[n].setAlignment( QtCore.Qt.AlignCenter )
            self.shotvalue[n].setText( str(self.shotname[n].text()) )   



    def loadstatus(self):
        for n in range(0, self.subrownumber):
            if str(ParentWindow.subshotslist[n]['Status']) == 'Dailies':
                self.status[n].setText( "<font color='aqua'>%s</font>"%str(ParentWindow.subshotslist[n]['Status']) )
                self.status[n].setAlignment( QtCore.Qt.AlignCenter )  
            elif str(ParentWindow.subshotslist[n]['Status']) == 'CBB':
                self.status[n].setText( "<font color='burlywood'>%s</font>"%str(ParentWindow.subshotslist[n]['Status']) )
                self.status[n].setAlignment( QtCore.Qt.AlignCenter )
            elif str(ParentWindow.subshotslist[n]['Status']) == 'Feedback':
                self.status[n].setText( "<font color='orangered'>%s</font>"%str(ParentWindow.subshotslist[n]['Status']) )
                self.status[n].setAlignment( QtCore.Qt.AlignCenter )                
            elif str(ParentWindow.subshotslist[n]['Status']) == 'Assigned':
                self.status[n].setText( "<font color='gray'>%s</font>"%str(ParentWindow.subshotslist[n]['Status']) )
                self.status[n].setAlignment( QtCore.Qt.AlignCenter )  
            else:
                self.status[n].setText( "<font color='mediumspringgreen'>%s</font>"%str(ParentWindow.subshotslist[n]['Status']) )
                self.status[n].setAlignment( QtCore.Qt.AlignCenter )               
            self.statusvalue[n].setText( str(self.status[n].text()) )   

#pane = nuke.getPaneFor('Properties.1')
#panels.registerWidgetAsPanel('MantinsWindow', 'Mantis', 'uk.co.thefoundry.MantinsWindow', True).addToPane(pane)



def add_Mantis_to_Nuke():
    pane = nuke.getPaneFor('Properties.1')
    global MantisNukeWindow
    MantisNukeWindow = panels.registerWidgetAsPanel('MantinsWindow', 'Mantis', 'uk.co.thefoundry.MantinsWindow', True)
    MantisNukeWindow.addToPane(pane)
    #print QtGui.QColor.colorNames()





########################################################################################################################import nuke
#######update your comment to mantis##########
##############################################

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui

class Update_Version_Comment( ParentWindow ):
    def __init__(self , n , parent=None ):
        #super(Update_Version_Comment, self).__init__( parent )
        ParentWindow.__init__(self, parent)
        #global versionValue,commentValue
        self.versionValue_b = None
        self.commentValue_b = None
        self.index = n
        ParentWindow.submitdata = {}


        self.versionlabel = QtGui.QLabel('Version')
        self.commentlabel = QtGui.QLabel('Comment')
        self.versionlabel.setAlignment(QtCore.Qt.AlignRight)
        self.commentlabel.setAlignment(QtCore.Qt.AlignRight)

        version_prep = ['v' + str("%03d"%i) for i in range(1,31)]
        self.combo = QtGui.QComboBox()
        self.combo.addItems(version_prep)
        self.combo.currentIndexChanged.connect(self.setVersion)

        self.comment = QtGui.QTextEdit( '' )    

        self.updatebutton = QtGui.QPushButton( "Update" )
        self.connect( self.updatebutton , QtCore.SIGNAL('clicked()') , self.update)

        layout = QtGui.QGridLayout()
        layout.addWidget( self.versionlabel , 1 , 0)
        layout.addWidget( self.commentlabel , 2 , 0)
        layout.addWidget( self.combo , 1 , 1)
        layout.addWidget( self.comment , 2 , 1)
        layout.addWidget( self.updatebutton , 3 , 1)
        self.setLayout(layout)


    def setVersion( self, index ):
        commentValue = self.combo.currentText()
        #print self.comment.text()
        

    def update(self):
        #global versionValue,commentValue
        
        self.versionValue_b = self.combo.currentText()
        self.commentValue_b = self.comment.toPlainText()

        ParentWindow.submitdata['version'] = self.versionValue_b
        ParentWindow.submitdata['bugnote_text'] = self.commentValue_b
        
        shotid =  ParentWindow.subshotslist[self.index]['shot_id']
        
        print ParentWindow.newstream.submitShots(shotid,self.versionValue_b,self.commentValue_b)
        print 'Update Success!'



########################################################################################################################
########################################################################################################################
########################################################################################################################
#Define a special QLabel widget!


class MyLabel(QtGui.QLabel,ParentWindow):

    def __init__(self,index,parent = None):
        QtGui.QLabel.__init__(self,parent)

        self.index = int(index)
        self.shotname = None
        self.projectID = None
        self.newWindow = None
        self.count = 0
        

    def setText(self,n):
        QtGui.QLabel.setText(self,n)



    def text(self):
        return QtGui.QLabel.text(self)


    def mouseReleaseEvent(self,event):

        self.shotname  = ParentWindow.subshotslist[self.index]['Shot'][0]
        dictionary = ParentWindow.newstream.getItemFromGanttData(self.shotname)
        self.newWindow = SchedulePanel(dictionary)

        #print self.shotname
        #if self.count == 0:
            #self.count = 1
            #self.newWindow.show()
            #self.newWindow.move(event.globalPos())

        #else:
            #self.newWindow.close()
            #self.count = 0
        self.newWindow.show()
        self.newWindow.move(event.globalPos())

"""
    #Abandoned function!
    def mousePressEvent(self,e):
        return

    def focusInEvent(self,event):
        return

    def focusOutEvent(self,event):
        return

    def moveEvent(self,event):
        return

    def leaveEvent(self,event):
        if self.count == 1:
            self.newWindow.close()

    def enterEvent(self,event):
        return

    def mouseMoveEvent(self,e):
        return
"""

########################################################################################################################
########################################################################################################################
########################################################################################################################
#DEFINE A NEW WIDGET TO SHOW THE ALL DEPATEMENT SCHEDULE OF A SHOT!


class SchedulePanel( QtGui.QLCDNumber,QtGui.QWidget):
    def __init__(self, dictionary , parent=None):
        super(SchedulePanel,self).__init__(parent)

        self.setWindowTitle("Complete status")
        self.resize(100,400)
        self.setNumDigits(0)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.7) 
        #url ='http://m.weather.com.cn/data/101090502.html'
        #re = urllib2.urlopen(url).read()
        #we = json.loads(re)['weatherinfo']
        print dictionary
        if dictionary.get('CameraTracking'):
            label1 = QtGui.QLabel( 'CameraTracking : %s'%setColor(dictionary['CameraTracking']) )
            label1.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label1 = QtGui.QLabel( 'CameraTracking : None ' )
            label1.setAlignment(QtCore.Qt.AlignLeft)
        if dictionary.get('Animation'):
            label2 = QtGui.QLabel( 'Animation : %s'%setColor(dictionary['Animation']) )
            label2.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label2 = QtGui.QLabel( 'Animation : None ' )
            label2.setAlignment(QtCore.Qt.AlignLeft)
        if dictionary.get('Effects'):
            label3 = QtGui.QLabel( 'Effects : %s'%setColor(dictionary['Effects']) )
            label3.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label3 = QtGui.QLabel( 'Effects : None' )
            label3.setAlignment(QtCore.Qt.AlignLeft) 
        if dictionary.get('Texturelighting'):
            label4 = QtGui.QLabel( 'Texturelighting : %s'%setColor(dictionary['Texturelighting']) )
            label4.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label4 = QtGui.QLabel( 'Texturelighting : None ' )
            label4.setAlignment(QtCore.Qt.AlignLeft)
        if dictionary.get('MattePainting'):
            label5 = QtGui.QLabel( 'MattePainting : %s'%setColor(dictionary['MattePainting']) )
            label5.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label5 = QtGui.QLabel( 'MattePainting : None ' )
            label5.setAlignment(QtCore.Qt.AlignLeft)
        if dictionary.get('RotoPaint'):
            label6 = QtGui.QLabel( 'RotoPaint : %s'%setColor(dictionary['RotoPaint']) )
            label6.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label6 = QtGui.QLabel( 'RotoPaint : None ' )
            label6.setAlignment(QtCore.Qt.AlignLeft)
        if dictionary.get('compositing'):
            label7 = QtGui.QLabel( 'Compositing : %s'%setColor(dictionary['compositing']) )
            label7.setAlignment(QtCore.Qt.AlignLeft)
        else:
            label7 = QtGui.QLabel( 'Compositing : None ' )
            label7.setAlignment(QtCore.Qt.AlignLeft)

        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget( label1 , 0, 0 )
        gridLayout.addWidget( label2 , 1, 0 )
        gridLayout.addWidget( label3 , 2, 0 )
        gridLayout.addWidget( label4 , 3, 0 )
        gridLayout.addWidget( label5 , 4, 0 )
        gridLayout.addWidget( label6 , 5, 0 )
        gridLayout.addWidget( label7 , 6, 0 )

        self.setLayout( gridLayout )
    def mousePressEvent(self,event):  
        if event.button()==QtCore.Qt.LeftButton:  
            self.dragPosition=event.globalPos()-self.frameGeometry().topLeft()  
            #print event.globalPos()
            event.accept()  
        if event.button()==QtCore.Qt.RightButton:  
            self.close()  


    def mouseMoveEvent(self,event):  
        if event.buttons() & QtCore.Qt.LeftButton:  
            self.move(event.globalPos()-self.dragPosition)  
            event.accept()  



def setColor(status):
    newstatus = status
    if status == 'Dailies':
        newstatus = "<font color='aqua'>%s</font>"%str(status)
    elif status == 'CBB':
        newstatus = "<font color='burlywood'>%s</font>"%str(status)
    elif status == 'Feedback':
        newstatus = "<font color='orangered'>%s</font>"%str(status)          
    elif status == 'Assigned':
        newstatus = "<font color='gray'>%s</font>"%str(status)
    else:
        newstatus = "<font color='mediumspringgreen'>%s</font>"%str(status) 
    return newstatus


a = MantinsWindow()
a.show()