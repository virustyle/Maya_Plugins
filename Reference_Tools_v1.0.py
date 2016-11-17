#Use this command to find out information about references and referenced nodes. 
#A valid target is either a reference node, a reference file, or a referenced node. 
#Some flags don't require a target, see flag descriptions for more information on what effect this has. 
#When a scene contains multiple levels of file references, those edits which affect a nested reference may be stored on several different reference nodes. 
#For example: A.ma has a reference to B.ma which has a reference to C.ma which contains a poly sphere (pSphere1). 
#If you were to open B.ma and translate the sphere, an edit would be stored on CRN which refers to a node named "C:pSphere1". 
#If you were then to open A.ma and parent the sphere, an edit would be stored on BRN which refers to a node named "B:C:pSphere1". 
#It is important to note that when querying edits which affect a nested reference, the edits will be returned in the same format that they were applied. 
#In the above example, opening A.ma and querying all edits which affect C.ma, would return two edits a parent edit affecting "B:C:pSphere1", and a setAttr edit affecting "C:pSphere1". 
#Since there is currently no node named C:pSphere1 (only B:C:pSphere1) care will have to be taken when interpreting the returned information. 
#The same care should be taken when referenced DAG nodes have been parented or instanced. 
#Continuing with the previous example, let's say that you were to open A.ma and, instead of simply parenting pSphere1, you were to instance it. 
#While A.ma is open, "B:C:pSphere1" may now be an amibiguous name, replaced by "|B:C:pSphere1" and "group1|B:C:pSphere1". 
#However querying the edits which affect C.ma would still return a setAttr edit affecting "C:pSphere1" since it was applied prior to B:C:pSphere1 being instanced. 
#Some tips: 1. It is important to note that when querying edits which affect a nested reference, the edits will be returned in the same format that they were applied.. 
#              Use the '-topReference' flag to query only those edits which were applied from the currently open file. 
#           2. Use the '-onReferenceNode' flag to limit the results to those edits where are stored on a given reference node. 
#You can then use various string manipulation techniques to extrapolate the current name of any affected nodes. 

#############################################################################################
import maya.cmds as maya
#############################################################################################

#import objects from referenceNode and remove all of the namespace in reference editor and optimizing!
def optimize():
    allobjecets = maya.ls()
    filelist = maya.file(q = 1,list = 1)
    for i in filelist:
        try:
            b = maya.referenceQuery(i,referenceNode = True)
            maya.file(i,importReference = True)
        except:
            print "This is not reference file!"

    namespacelist = []
    for nodename in allobjecets:
        if nodename.endswith("RN"):
            continue
        if maya.referenceQuery(nodename,isNodeReferenced = True):
            
            if nodename.find("|") >= 0:
                name = (nodename.split('|'))[0]
                if name.find(":") >= 0:
                    newname = ":".join((name.split(":"))[0:-1])
                    namespacelist.append(newname)
            elif nodename.find("->") >= 0:
                name = (nodename.split('->'))[-1]
                if name.find(":") >= 0:
                    newname = ":".join((name.split(":"))[0:-1])
                    namespacelist.append(newname)
            else:
                if nodename.find(":") >= 0:
                    newname = ":".join((nodename.split(":"))[0:-1])
                    namespacelist.append(newname)
                    
    newnamespacelist = list(set(namespacelist))  
    newnamespacelist_2 = []
    newnamespacelist_3 = []
    for name in newnamespacelist:
        subnamelist = (name,len(name.split(":")))
        newnamespacelist_2.append(subnamelist)
        
    newnamespacelist_2.sort(key=lambda x:x[1]) 
    newnamespacelist_2.reverse()
    #print newnamespacelist_2
    for newname in newnamespacelist_2:
        newnamespacelist_3.append(newname[0])
    print newnamespacelist_3
    for newname in newnamespacelist_3:
        maya.namespace(removeNamespace = newname,mergeNamespaceWithRoot = True)



#Publish the optimized scene!
def publish():
    return





#Create the panel to implement all of above function!
MainWindow = maya.window(title = "Matchmove Tool(retime) v1.3")
maya.columnLayout( adjustableColumn=False )
maya.frameLayout( label='Operation', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.rowColumnLayout(numberOfColumns=2,columnWidth=[[1,100],[2,100]])
maya.text(label = "")
maya.text(label = "")
maya.text(label="Optimize ",align = 'right')
maya.button(label="Press",w = 100,command = "optimize()")
maya.text(label="Publish ",align = 'right')
maya.button(label="Press",w = 100,command = "publish()")
maya.text(label = "")
maya.text(label = "")
maya.setParent('..')
maya.setParent('..')
maya.frameLayout( label='Operation', borderStyle='in',marginHeight = 8,backgroundColor = [0.35,0.35,0.35] )
maya.columnLayout()
maya.text(label = "\n\
This tool is used for output a optimized scene.\n\
")
maya.showWindow(MainWindow)