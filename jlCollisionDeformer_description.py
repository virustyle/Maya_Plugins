global proc jlCollisionDeformer()
{
    #get the selected geometry
    string $sel[] = `ls -sl -tr`;
    #judge if the number of selected geometry is equal to 2
    if (size($sel)==2)
    {
        #get the collidermesh deformer
        string $collider = $sel[0];
        #get the geo be deformed
        string $target = $sel[1];
        #get relatived shape node
        string $collidershape[] = `listRelatives -s $collider`;
        #create the node that deform the geo
        string $collisiondeformer[] = `deformer -typ "jlCollisionDeformer" -n "collisionDeformer" $target`;
        #create a link that connect the collider and 
        connectAttr -f ("pSphereShape1.worldMesh[0]") ("collisionDeformer.collider");
        connectAttr -f ("pSphere1.matrix") ("collisionDeformer.colliderMatrix");
        connectAttr -f ("pSphere.boundingBox.boundingBoxSize") ("collisionDeformer.colliderBBoxSize");
    }
    else
    {
        error "please select two meshes: first the collider mesh then the mesh that should be deformed.";
    }
}
