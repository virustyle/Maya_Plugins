'''
########################################################################
#                                                                      #
#             jlCollisionDeformer.py                                   #
#                                                                      #
#             Version 0.9.5.0 , last modified 2013-02-12               #
#                                                                      #
#             Copyright (C) 2010  Jan Lachauer                         #
#                                                                      #
#             Email: janlachauer@googlemail.com                        #
#                                                                      #
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# This program is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU General Public License for more details.                         #
#                                                                      #
# See http://www.gnu.org/licenses/gpl.html for a copy of the GNU       #
# General Public License.                                              #
#                                                                      #
########################################################################


I N S T A L L:

Copy the "jlCollisionDeformer.py" to your Maya plugins directory
and load the plugin via the plugin manager

Windows: Program Files\Autodesk\MayaXXXX\bin\plug-ins\
Mac OS: Users/Shared/Autodesk/maya/2011/plug-ins


U S E:

First load the plugin via Window->Settings/Prefs->Plug-in Manager
Then select the collidermesh followed by the mesh that should be deformed.
Finally execute following MEL command:
  jlCollisionDeformer()


For bugreports/questions/suggestions please don't hesitate 
to contact me: janlachauer@googlemail.com

D O N A T E:

This was written in my spare time. If you found it useful for rigging or coding, consider supporting the author:
https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7KFXBVDNNMWHW


'''

import math, sys, array, copy
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMayaMPx as OpenMayaMPx
from maya.mel import eval as meval
import maya.cmds as maya

kPluginNodeTypeName = "jlCollisionDeformer"

jlCollisionDeformerId = OpenMaya.MTypeId(0x0010A52B)


# Node definition
class jlCollisionDeformer(OpenMayaMPx.MPxDeformerNode):
    # class variables
    mmAccelParams = OpenMaya.MMeshIsectAccelParams()
    intersector = OpenMaya.MMeshIntersector()
    newpoints = OpenMaya.MFloatPointArray()
    tempArr = OpenMaya.MFloatPointArray()
    tempArr_sub = OpenMaya.MFloatPointArray()
    maxdist = 0
    baseColliderPoints = OpenMaya.MFloatPointArray()
    
    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)
    
    def compute(self,plug,dataBlock):
        # variable definitions
        vector = OpenMaya.MVector()
        normvector = OpenMaya.MVector()
        point = OpenMaya.MPoint()
        pointtemp = OpenMaya.MPoint()
        
        pointNormal = OpenMaya.MVector()
        colliderPointNormal = OpenMaya.MVector()
        distanceVector = OpenMaya.MVector()
        deformedPoints = OpenMaya.MFloatPointArray()
        deformedPointsIndices = []
        
        pointInfo = OpenMaya.MPointOnMesh() 
        
        emptyFloatArray = OpenMaya.MFloatArray()
        
        inMeshNormal = OpenMaya.MVector()
        collisionMeshNormal = OpenMaya.MVector()
        connectedPnts = []
        maxDistance = 0
        worldPoint = OpenMaya.MFloatPoint()
        
        previndex = OpenMaya.MScriptUtil().asIntPtr()
        indirPointInfo = OpenMaya.MPointOnMesh() 


        connectPointArray = OpenMaya.MIntArray()





        
        
        # Handles
        
        # deformer handle
        multiIndex = plug.logicalIndex()
        thisNode = self.thisMObject()

        
        nodeFn = OpenMaya.MFnDependencyNode(thisNode)
        
        envelope = OpenMayaMPx.cvar.MPxDeformerNode_envelope
        envelopeHandle = dataBlock.inputValue( envelope )
        envelopeValue = envelopeHandle.asFloat()
        
        offsetHandle = dataBlock.inputValue( self.offset )
        offsetValue = offsetHandle.asDouble()
        
        bulgeExtendHandle = dataBlock.inputValue( self.bulgeextend )
        bulgeExtendValue = bulgeExtendHandle.asDouble()
        
        # get bulge handle
        bulgeHandle = dataBlock.inputValue( self.bulge )
        bulgeValue = bulgeHandle.asDouble()
        
        bulgeshapeValueUtil = OpenMaya.MScriptUtil()
        bulgeshapeValue = bulgeshapeValueUtil.asFloatPtr()
        
        bulgeshapeHandle = OpenMaya.MRampAttribute(thisNode, self.bulgeshape)
        
        sculptHandle = dataBlock.inputValue( self.sculptmode )
        sculptValue = sculptHandle.asShort()
        
        backfaceHandle = dataBlock.inputValue( self.backface )
        backfaceValue = backfaceHandle.asShort()
        
        
        # intput geometry data
        input = OpenMayaMPx.cvar.MPxDeformerNode_input
        hInput = dataBlock.inputArrayValue(input)
        hInput.jumpToArrayElement(multiIndex)
        
        inputGeom = OpenMayaMPx.cvar.MPxDeformerNode_inputGeom

        groupId = OpenMayaMPx.cvar.MPxDeformerNode_groupId
        #iter_inmesh = OpenMaya.MItMeshVertex(inputGeom)
        
        hInputElement = hInput.inputValue()
        hInputGeom = hInputElement.child(inputGeom)
        
        inMesh = hInputGeom.asMesh()
        inMeshFn = OpenMaya.MFnMesh(inMesh)
        
        inPoints = OpenMaya.MFloatPointArray()
        colliderPoints = OpenMaya.MFloatPointArray()
        inMeshFn.getPoints(inPoints, OpenMaya.MSpace.kWorld)
        
        
        # copy points into array to set them later
        if self.newpoints.length() == 0 or sculptValue==0:
            self.newpoints = copy.copy(inPoints)
            self.tempArr = copy.copy(inPoints)
            self.tempArr_sub = copy.copy(inPoints)

        
        
        # output geometry data
        hOutput = dataBlock.outputValue(plug)
        hOutput.copy(hInputGeom)
        
        outMesh = hInputGeom.asMesh()
        outMeshFn = OpenMaya.MFnMesh(outMesh)
        
        
        # collider vertexlists
        pcounts = OpenMaya.MIntArray()
        pconnect = OpenMaya.MIntArray()

        #mesh vertexlists
        mesh_counts = OpenMaya.MIntArray()
        mesh_connect = OpenMaya.MIntArray()


        # collider handles
        colliderHandle = dataBlock.inputValue( self.collider )
        try:
            colliderObject = colliderHandle.asMesh()
            colliderFn = OpenMaya.MFnMesh(colliderObject)
            colliderIter = OpenMaya.MItMeshVertex ( colliderHandle.asMesh() )
            polycount = colliderFn.numPolygons()
            colliderFn.getVertices(pcounts, pconnect)
            colliderFn.getPoints(colliderPoints, OpenMaya.MSpace.kObject)
        except:
            #print "can't get collidermesh. check connection to deformer node!"
            pass


        ##############create a new MObject!#####################
        vertexcount = self.newpoints.length()
        inMeshFn.getVertices(mesh_counts,mesh_connect)
        polycount = inMeshFn.numPolygons()

        tempMeshData = OpenMaya.MFnMeshData()
        tempObject = OpenMaya.MObject()     
        tempObject = tempMeshData.create()   
        newObject = OpenMaya.MObject()  

        MeshFs = OpenMaya.MFnMesh()
        #create a DAG path      
        
        newObject = MeshFs.create(vertexcount,polycount,inPoints,mesh_counts,mesh_connect,tempObject)

        Inmesh_vertex_iter = OpenMaya.MItMeshVertex(newObject)
        ConnectIndecies = OpenMaya.MIntArray()
        ########################################################
        
        # mesh handles        
        
        dataCreator = OpenMaya.MFnMeshData() 
        newColliderData = OpenMaya.MObject(dataCreator.create())
        
        colliderMatrixHandle = dataBlock.inputValue( self.colliderMatrix )
        colliderMatrixValue = floatMMatrixToMMatrix_(colliderMatrixHandle.asFloatMatrix())
        
        # get collider boundingbox for threshold
        colliderBBSizeHandle = dataBlock.inputValue( self.colliderBBoxSize )
        colliderBBSizeValue = colliderBBSizeHandle.asDouble3()
        colliderBBVector = OpenMaya.MVector(colliderBBSizeValue[0], colliderBBSizeValue[1], colliderBBSizeValue[2])
        colliderBBSize = colliderBBVector.length()
        thresholdValue = colliderBBSize*2
        
        newColliderPoints = OpenMaya.MFloatPointArray()
        
        
        # do the deformation
        if envelopeValue != 0:
            
            # check the offset value
            if offsetValue != 0:
                baseColliderPoints = copy.copy(colliderPoints) 
                
                newColliderPoints.clear()
                for i in range(colliderPoints.length()):
                    
                    #colliderFn.getVertexNormal(i, colliderPointNormal , OpenMaya.MSpace.kObject)
                    # newColliderPoint = OpenMaya.MFloatPoint(self.baseColliderPoints[i].x+colliderPointNormal.x*offsetValue, self.baseColliderPoints[i].y+colliderPointNormal.y*offsetValue, self.baseColliderPoints[i].z+colliderPointNormal.z*offsetValue)

                    newColliderPoint = OpenMaya.MFloatPoint(colliderPoints[i].x, colliderPoints[i].y, colliderPoints[i].z)
                    
                    newColliderPoints.append(newColliderPoint)

                try:
                    colliderFn.createInPlace(colliderPoints.length(), polycount,newColliderPoints,pcounts,pconnect)
                except:
                    #print "Can't create offset copy"
                    pass
            
            # create a MMeshintersector instance and define neccessary variables
            try:
                self.intersector.create( colliderObject, colliderMatrixValue)
                self.mmAccelParams = colliderFn.autoUniformGridParams()
            except:
                #print "Can't create intersector"
                pass
            
            
            
            checkCollision = 0
            maxDeformation = 0.0
            
            # get deformer weights
            
            statuslist = []
            # direct collision deformation:
            for k in range(self.newpoints.length()):
                inMeshFn.getVertexNormal(k, pointNormal , OpenMaya.MSpace.kWorld)
                
                # define an intersection ray from the mesh that should be deformed
                raySource = OpenMaya.MFloatPoint(self.newpoints[k].x , self.newpoints[k].y , self.newpoints[k].z )
                rayDirection = OpenMaya.MFloatVector(pointNormal)
                
                point = OpenMaya.MPoint(self.newpoints[k])
                
                # MeshFn.allIntersections variables
                faceIds = None
                triIds = None
                idsSorted = True
                space = OpenMaya.MSpace.kWorld
                maxParam = thresholdValue
                tolerance = 1e-9
                
                # testBothDirs = False
                testBothDirs = True
                accelParams = self.mmAccelParams
                sortHits = True
                hitPoints1 = OpenMaya.MFloatPointArray()
                hitRayParams = OpenMaya.MFloatArray(emptyFloatArray)
                hitFaces = None
                hitTriangles = None
                hitBary1s = None
                hitBary2s = None
                
                try:
                    gotHit = colliderFn.allIntersections( raySource,rayDirection, faceIds, triIds, idsSorted, space, maxParam, testBothDirs, accelParams,sortHits, hitPoints1, hitRayParams, hitFaces, hitTriangles, hitBary1s, hitBary2s )
                except:
                    break
                
                #if gotHit == True:
                    # need this to check if collider is in range for collision, because gotHit may also be true if the collider lies half way outside the maxParam
                    
                hitCount = hitPoints1.length()
                #print hitCount
                    
                    
                for i in range(hitCount - 1):
                    #if the hit vertices place at the two part of raySource.
                    if hitRayParams[i] * hitRayParams[i+1] < 0:
                        signChange = i
                        break
                        #signChange = -1
                    else:
                        signChange = -1000
                    
                collision = 0
                
                #judge if it's hitted.
                if hitCount==2 and signChange+1 ==1 and signChange != -1000:
                    collision = 1
                elif hitCount>2 and hitCount/(signChange+1) != 2 and signChange != -1000:
                        collision = 1
                    
                    
                # if the ray intersects the collider mesh an odd number of times and the collider is in range, collision is happening
                if collision == 1:
                    statuslist.append(collision)
                        
                    checkCollision = checkCollision+1
                        
                    # add this point to the collision array
                    deformedPointsIndices.append(k)

                    deformedPoints.append(raySource)
                        
                    # get the closest point on the collider mesh
                    self.intersector.getClosestPoint( point, pointInfo)
                        
                    closePoint = OpenMaya.MPoint( pointInfo.getPoint() )
                    closePointNormal = OpenMaya.MFloatVector( pointInfo.getNormal() )
                        
                    offsetVector = OpenMaya.MVector(closePointNormal.x,closePointNormal.y,closePointNormal.z)
                        
                    # normal angle check for backface culling, if the angle is bigger then 90 the face lies on the opposite side of the collider mesh
                    angle =closePointNormal*rayDirection
                        
                    #if angle > 0 and backfaceValue == 1:
                        # ignore the backfaces, reset the point position
                    worldPoint = OpenMaya.MPoint(hitPoints1[signChange])
                    #else:
                    #    worldPoint = closePoint
                    #    worldPoint = worldPoint * colliderMatrixValue
                    
                    # update the maximum deformation distance for the bulge strength
                    deformationDistance = point.distanceTo(worldPoint)
                    if maxDeformation < deformationDistance:
                        maxDeformation = deformationDistance
                        
                    weight = self.weightValue( dataBlock, multiIndex,k)
                    
                    #A iterator for the vertex been selected.
                    #print Inmesh_vertex_iter.count()
                        
                        
                    #self.newpoints[k].x += (worldPoint.x - inPoints[k].x ) *envelopeValue*weight
                    #self.newpoints[k].y += (worldPoint.y - inPoints[k].y ) *envelopeValue*weight
                    #self.newpoints[k].z += (worldPoint.z - inPoints[k].z ) *envelopeValue*weight
                    self.tempArr[k].x += (worldPoint.x - inPoints[k].x ) *envelopeValue*weight
                    self.tempArr[k].y += (worldPoint.y - inPoints[k].y ) *envelopeValue*weight
                    self.tempArr[k].z += (worldPoint.z - inPoints[k].z ) *envelopeValue*weight

                    Inmesh_vertex_iter.next()
                    Inmesh_vertex_iter.getConnectedVertices(ConnectIndecies)
                    print ConnectIndecies


                elif collision != 1:
                    statuslist.append(collision)


            ###############################################################################
            #calculate the median value.
            #this part is design to get the adjacent vertices and weaken the unsmooth edge.
            #please don't modify this part of script.
            #inPoints,mesh_counts,mesh_connect.
            #write by Sol He.
            ###############################################################################

            #templist = []
            #for k in range(1,self.newpoints.length()-1):
            #    if statuslist[k] == 1:
            #        sumlistx = []
            #        sumlisty = []
            #        sumlistz = []
            #        for m in range(mesh_connect.length() - 1):
            #            if mesh_connect[m] == k:
            #                ind_fst = int(m/4) * 4
            #                ind_lst = int(m/4) * 4 + 4
            #                templist = mesh_connect[ind_fst:ind_lst]
            #                #print self.tempArr[templist[m - ind_fst - 1]].x
            #                #print self.tempArr[templist[m - ind_fst - 3]].x
            #                #print ind_fst,ind_lst
            #                #print templist
            #                #print m - ind_fst
            #                #print templist[m - ind_fst]
            #                #print self.tempArr[templist[m - ind_fst]].x
            #                sumlistx.append((self.tempArr[templist[m - ind_fst - 1]].x + self.tempArr[templist[m - ind_fst -3]].x))
            #                sumlisty.append((self.tempArr[templist[m - ind_fst - 1]].y + self.tempArr[templist[m - ind_fst -3]].y))
            #                sumlistz.append((self.tempArr[templist[m - ind_fst - 1]].z + self.tempArr[templist[m - ind_fst -3]].z))
            #        self.newpoints[k].x = sum(sumlistx)/8
            #        self.newpoints[k].y = sum(sumlisty)/8
            #        self.newpoints[k].z = sum(sumlistz)/8














                    #self.newpoints[k].x = self.tempArr[k].x
                    #self.newpoints[k].y = self.tempArr[k].y
                    #self.newpoints[k].z = self.tempArr[k].z


            for k in range(1,self.newpoints.length()-1):
                if statuslist[k] == 1:
                    self.newpoints[k].x = 0.25 * self.tempArr[k - 1].x + 0.5 * self.tempArr[k].x + 0.25 * self.tempArr[k + 1].x
                    self.newpoints[k].y = 0.25 * self.tempArr[k - 1].y + 0.5 * self.tempArr[k].y + 0.25 * self.tempArr[k + 1].y
                    self.newpoints[k].z = 0.25 * self.tempArr[k - 1].z + 0.5 * self.tempArr[k].z + 0.25 * self.tempArr[k + 1].z
            
            #tempArr_sub
            #for k in range(1,self.newpoints.length()-1):
            #    if statuslist[k] == 1:
            #        self.newpoints[k].x = 0.25 * self.tempArr_sub[k - 1].x + 0.5 * self.tempArr_sub[k].x + 0.25 * self.tempArr_sub[k + 1].x
            #        self.newpoints[k].y = 0.25 * self.tempArr_sub[k - 1].y + 0.5 * self.tempArr_sub[k].y + 0.25 * self.tempArr_sub[k + 1].y
            #        self.newpoints[k].z = 0.25 * self.tempArr_sub[k - 1].z + 0.5 * self.tempArr_sub[k].z + 0.25 * self.tempArr_sub[k + 1].z

            #self.tempArr.clear()

                    ###############################################################################
                    #calculate the median value.
                    #this part is design to get the adjacent vertices and weaken the unsmooth edge.
                    #please don't modify this part of script.
                    #inPoints,mesh_counts,mesh_connect.
                    #write by Sol He.
                    ###############################################################################

                    #check the vertices of each polygons.
                    #ajacent_vertices_index_list = []
                    #last_index_conect = 0
                    #print mesh_counts.length()
                    #print mesh_connect.length()
                    #for m in range(mesh_counts.length()-1):
                    #    last_index_conect += mesh_counts[m]
                    #    fisrt_index_conect = last_index_conect - mesh_counts[m]
                        #print last_index_conect
                    #    new_mesh_connect_list = mesh_connect[fisrt_index_conect:last_index_conect - 1]
                        #print mesh_connect[fisrt_index_conect:last_index_conect - 1]
                    #    for n in range(new_mesh_connect_list.length() - 1):
                        #    print n
                    #        if k == new_mesh_connect_list[n]:
                    #            ajacent_vertices_index_list.append(new_mesh_connect_list[n - 1])
                    #            ajacent_vertices_index_list.append(new_mesh_connect_list[n + 1])

                    #sum_x = 0
                    #sum_y = 0
                    #sum_z = 0
                    #for ind in ajacent_vertices_index_list:
                    #    sum_x += self.newpoints[ind].x
                    #    sum_y += self.newpoints[ind].y
                    #    sum_z += self.newpoints[ind].z

                    #self.newpoints[k].x = sum_x/len(ajacent_vertices_index_list)
                    #self.newpoints[k].y = sum_y/len(ajacent_vertices_index_list)
                    #self.newpoints[k].z = sum_z/len(ajacent_vertices_index_list)



            #maya.polyAverageVertex(deformedPoints)
            #import maya.OpenMaya as OpenMaya
            # indirect collision deformation:
            if checkCollision != 0:
                for i in range(self.newpoints.length()):
                    
                    
                    inMeshFn.getVertexNormal(i, inMeshNormal , OpenMaya.MSpace.kWorld)
                    
                    indirPoint = OpenMaya.MPoint(self.newpoints[i])
                    self.intersector.getClosestPoint( indirPoint, indirPointInfo)
                    #self.intersector.getVertexNormal(indirPointInfo.getPoint(), collisionMeshNormal, OpenMaya.MSpace.kWorld)
                    
                    #calculate the distance.
                    indirClosePoint = OpenMaya.MPoint( indirPointInfo.getPoint() )
                    
                    indirWorldPoint = indirClosePoint * colliderMatrixValue
                    
                    bulgePntsDist = indirPoint.distanceTo(indirWorldPoint)
                    
                    weight = self.weightValue( dataBlock, multiIndex,i)
                    
                    
                    # calculate the relative distance of the meshpoint based on the maximum bulgerange
                    relativedistance = bulgePntsDist/(bulgeExtendValue+0.00001)
                    
                    # get the bulge curve 
                    bulgeshapeHandle.getValueAtPosition(float(relativedistance), bulgeshapeValue)
                    bulgeAmount = OpenMaya.MScriptUtil().getFloat(bulgeshapeValue)
                    #bulgeAmount = 1
                    bulgeAmount = -abs(bulgeAmount)
                    # set the point position for indirect collision deformation



                    self.newpoints[i].x += inMeshNormal.x*bulgeExtendValue*(bulgeValue/5)*envelopeValue*bulgeAmount*maxDeformation*weight
                    self.newpoints[i].y += inMeshNormal.y*bulgeExtendValue*(bulgeValue/5)*envelopeValue*bulgeAmount*maxDeformation*weight
                    self.newpoints[i].z += inMeshNormal.z*bulgeExtendValue*(bulgeValue/5)*envelopeValue*bulgeAmount*maxDeformation*weight
                    
            
            outMeshFn.setEdgeSmoothing(True)
            outMeshFn.setPoints(self.newpoints, OpenMaya.MSpace.kWorld)
            outMeshFn.setEdgeSmoothing(True)

            dataBlock.setClean(self.outputGeom)
            
            if offsetValue != 0:
                try:
                    colliderFn.createInPlace(colliderPoints.length(), polycount,baseColliderPoints,pcounts,pconnect)
                except:
                    #print "Can't reset offset copy"
                    pass
    
    # accessoryNodeSetup used to initialize the ramp attributes
    def accessoryNodeSetup(self, cmd):
        thisNode = self.thisMObject()

        bulgeshapeHandle = OpenMaya.MRampAttribute(thisNode, self.bulgeshape)
        
        a1 = OpenMaya.MFloatArray()
        b1 = OpenMaya.MFloatArray()
        c1 = OpenMaya.MIntArray()
        
        a1.append(float(0.0))
        a1.append(float(0.2))
        a1.append(float(1.0))
        
        b1.append(float(0.0))
        b1.append(float(1.0))
        b1.append(float(0.0))
        
        c1.append(OpenMaya.MRampAttribute.kSpline)
        c1.append(OpenMaya.MRampAttribute.kSpline)
        c1.append(OpenMaya.MRampAttribute.kSpline)
        
        bulgeshapeHandle.addEntries(a1,b1,c1)
    

def floatMMatrixToMMatrix_(fm):
    mat = OpenMaya.MMatrix()
    OpenMaya.MScriptUtil.createMatrixFromList ([
        fm(0,0),fm(0, 1),fm(0, 2),fm(0, 3),
        fm(1,0),fm(1, 1),fm(1, 2),fm(1, 3),
        fm(2,0),fm(2, 1),fm(2, 2),fm(2, 3),
        fm(3,0),fm(3, 1),fm(3, 2),fm(3, 3)], mat)
    return mat


def nodeCreator():
    return OpenMayaMPx.asMPxPtr( jlCollisionDeformer() )

# initializer
def nodeInitializer():
    gAttr = OpenMaya.MFnGenericAttribute()
    
    jlCollisionDeformer.collider = gAttr.create( "collider", "coll")
    gAttr.addDataAccept( OpenMaya.MFnData.kMesh )
    gAttr.setHidden(True)
    
    
    nAttr = OpenMaya.MFnNumericAttribute()
    
    jlCollisionDeformer.bulgeextend = nAttr.create( "bulgeextend", "bex", OpenMaya.MFnNumericData.kDouble, 0.0)
    nAttr.setKeyable(True)
    nAttr.setStorable(True)
    nAttr.setSoftMin(0)
    nAttr.setSoftMax(10)
    
    jlCollisionDeformer.bulge = nAttr.create( "bulge", "blg", OpenMaya.MFnNumericData.kDouble, 1.0)
    nAttr.setKeyable(True)
    nAttr.setStorable(True)
    nAttr.setSoftMin(0)
    nAttr.setSoftMax(10)
    
    jlCollisionDeformer.offset = nAttr.create( "offset", "off", OpenMaya.MFnNumericData.kDouble, 0.0)
    nAttr.setKeyable(True)
    nAttr.setStorable(True)
    nAttr.setSoftMin(0)
    nAttr.setSoftMax(1)
    
    jlCollisionDeformer.colliderBBoxX = nAttr.create( "colliderBBoxX", "cbbX", OpenMaya.MFnNumericData.kDouble, 0.0 )
    jlCollisionDeformer.colliderBBoxY = nAttr.create( "colliderBBoxY", "cbbY", OpenMaya.MFnNumericData.kDouble, 0.0 )
    jlCollisionDeformer.colliderBBoxZ = nAttr.create( "colliderBBoxZ", "cbbZ", OpenMaya.MFnNumericData.kDouble, 0.0 )
    
    cAttr = OpenMaya.MFnCompoundAttribute()
    jlCollisionDeformer.colliderBBoxSize = cAttr.create( "colliderBBoxSize", "cbb")
    
    cAttr.addChild(jlCollisionDeformer.colliderBBoxX)
    cAttr.addChild(jlCollisionDeformer.colliderBBoxY)
    cAttr.addChild(jlCollisionDeformer.colliderBBoxZ)
    
    mAttr = OpenMaya.MFnMatrixAttribute()
    
    jlCollisionDeformer.colliderMatrix = mAttr.create("colliderMatrix", "collMatr", OpenMaya.MFnNumericData.kFloat )
    mAttr.setHidden(True)
    
    rAttr = OpenMaya.MRampAttribute()
    
    jlCollisionDeformer.bulgeshape = rAttr.createCurveRamp("bulgeshape", "blgshp")
    
    eAttr = OpenMaya.MFnEnumAttribute()
    
    jlCollisionDeformer.backface = eAttr.create("backface_culling", "bkcul", 0)
    eAttr.addField("off", 0);
    eAttr.addField("on", 1);
    eAttr.setHidden(False);
    eAttr.setKeyable(True);
    eAttr.setStorable(True); 
    
    jlCollisionDeformer.sculptmode = eAttr.create("sculpt_mode", "snmd", 0)
    eAttr.addField("off", 0);
    eAttr.addField("on", 1);
    eAttr.setHidden(False);
    eAttr.setKeyable(True);
    eAttr.setStorable(True); 
    
    
    # add attribute
    try:
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.collider )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.bulge )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.bulgeextend )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.colliderMatrix )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.backface )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.sculptmode )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.bulgeshape )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.offset )
        jlCollisionDeformer.addAttribute( jlCollisionDeformer.colliderBBoxSize )
        outputGeom = OpenMayaMPx.cvar.MPxDeformerNode_outputGeom
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.collider, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.offset, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.colliderBBoxSize, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.bulge, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.bulgeextend, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.colliderMatrix, outputGeom )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.backface, outputGeom  )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.sculptmode, outputGeom  )
        jlCollisionDeformer.attributeAffects( jlCollisionDeformer.bulgeshape, outputGeom  )
    except:
        sys.stderr.write( "Failed to create attributes of %s node\n" % kPluginNodeTypeName )
    

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Jan Lachauer", "0.9.5.0")
    try:
        mplugin.registerNode( kPluginNodeTypeName, jlCollisionDeformerId, nodeCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDeformerNode )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( jlCollisionDeformerId )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )



mel = '''
global proc jlCollisionDeformer()
{
    string $sel[] = `ls -sl -tr`;
    if (size($sel)==2)
    {
        string $collider = $sel[0];
        string $target = $sel[1];
        string $collidershape[] = `listRelatives -s $collider`;
        string $collisiondeformer[] = `deformer -typ "jlCollisionDeformer" -n "collisionDeformer" $target`;
        connectAttr -f ($collidershape[0]+".worldMesh[0]") ($collisiondeformer[0]+".collider");
        connectAttr -f ($collider+".matrix") ($collisiondeformer[0]+".colliderMatrix");
        connectAttr -f ($collider+".boundingBox.boundingBoxSize") ($collisiondeformer[0]+".colliderBBoxSize");
        polySmooth  -dv 0 -c 2 $target;

    }
    else
    {
        error "please select two meshes: first the collider mesh then the mesh that should be deformed.";
    }
}


    global proc AEjlCollisionDeformerNew( string $attributeName1, string $attributeName2) {
        checkBoxGrp -numberOfCheckBoxes 1 -label "Backface Culling" culling;
        checkBoxGrp -numberOfCheckBoxes 1 -label "Sculpt Mode" sculpt;
        
        connectControl -index 2 culling ($attributeName1);
        connectControl -index 2 sculpt ($attributeName2);
    }

    global proc AEjlCollisionDeformerReplace( string $attributeName1, string $attributeName2) {
        connectControl -index 2 culling ($attributeName1);
        connectControl -index 2 sculpt ($attributeName2);
    }

    global proc AEjlCollisionDeformerTemplate( string $nodeName )
    {
        // the following controls will be in a scrollable layout
        editorTemplate -beginScrollLayout;

            // add a bunch of common properties
            editorTemplate -beginLayout "Collision Deformer Attributes" -collapse 0;
                editorTemplate -callCustom "AEjlCollisionDeformerNew" "AEjlCollisionDeformerReplace" "backface_culling" "sculpt_mode";
                editorTemplate -addSeparator;
                editorTemplate -addControl  "bulge" ;
                editorTemplate -addControl  "bulgeextend" ;
                editorTemplate -addControl  "offset" ;
                editorTemplate -addControl  "envelope" ;
                AEaddRampControl "bulgeshape" ;
                
            editorTemplate -endLayout;

            // include/call base class/node attributes
            AEdependNodeTemplate $nodeName;

            // add any extra attributes that have been added
            editorTemplate -addExtraControls;

        editorTemplate -endScrollLayout;
    }
'''
meval( mel )
