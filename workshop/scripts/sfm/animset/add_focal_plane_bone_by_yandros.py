"""
Adds a focal plane bone (a transform control actually).
Created by Yandros (www.steamcommunity.com/id/yandrosprofile) © All rights reserved,
except for the "adding a bone/dag" method, which is inspired on the one in view_target_camera.py script by MulleDK19.
"""

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR

class WrongUseException(Exception):
    def __init__(self, param):
        super(WrongUseException, self).__init__(param)

def AddFocalPlaneBone():
	shot = sfm.GetCurrentShot()
	animSet = sfm.GetCurrentAnimationSet()
	
	""" Checking it is actually a camera the script is being run onto """
	if shot == None or animSet == None:
		raise WrongUseException("Please select the camera to which you would like to add a Focal Plane Bone, in the Animation Set Editor (run this script from the RMB>'Rig' menu)")
	if not animSet.HasAttribute("camera"):
		raise WrongUseException("The selected animation set is not a camera's.")
	camera = animSet.camera
	if camera.GetTypeString() != "DmeCamera":
		raise WrongUseException("The selected animation set is still not a camera's despite its 'camera' attribute ...")
	
	
	""" Adding a new 'bone' (a transform-controlled Dag) """
	#First, we create the Dag (and add it to the camera animation set).
	focalPlaneBoneDag = vs.CreateElement("DmeDag", "focalPlaneBoneDag", shot.GetFileId())
	sfmUtils.AddAttributeToElement(animSet, "focalPlaneBoneDag", vs.AT_ELEMENT, focalPlaneBoneDag)
	
	#Then we create a 'Transform Control', so that we have something to move around (e.g in the Motion Editor), and add it to the camera controls.
	focalPlaneBoneControl = vs.CreateElement("DmeTransformControl", "focalPlaneBone", shot.GetFileId())
	animSet.FindControlGroup("all").AddControl(focalPlaneBoneControl)

	#However, the Transform Control and the dag are still not linked together, we need to do it with a channel :
		#First, we create the channel (into the camera animation set), that will be working with a 'position' i.e, a 3-dimensional vector :
	positionChannel = sfmUtils.CreateChannel("focalPlaneBonePositionChannel", vs.AT_VECTOR3, None, animSet, shot)
		#Then we set the input : the 'Transform Control'
	positionChannel.fromElement = focalPlaneBoneControl
	positionChannel.fromAttribute = "valuePosition"
		#and the output : the Dag's actual position.
	positionChannel.toElement = focalPlaneBoneDag.transform
	positionChannel.toAttribute = "position"
		#Finally, we create an access to the channel from the control (so that the connection told by the channel is applied every time the control is used).
	focalPlaneBoneControl.positionChannel = positionChannel
	
	
	
	
	
	""" Unpacking FocalPlaneBone Position Coordinates """
	#First, we create an 'unpacker' : it will isolate the 'vector' coordinates into the 'x', 'y' and 'z' fields.
	focalPlaneBoneUnpack = vs.CreateElement("DmeUnpackVector3Operator","focalPlaneBoneUnpack",shot.GetFileId()) 
	animSet.AddOperator(focalPlaneBoneUnpack)
	#Then we create a connection between the FocalPlaneBoneDag 'position' and the 'vector' field of the unpacker :
	focalPlaneBoneConn = sfmUtils.CreateConnection( "focalPlaneBoneConnection", focalPlaneBoneDag.transform, "position", animSet ) #The input here : the FocalPlaneBone 'position' vector3.
	focalPlaneBoneConn.AddOutput(focalPlaneBoneUnpack, "vector") #The output here : the 'vector' field.
	
	
	
	""" Unpacking Root Transform Position Coordinates """
	posUnpack = vs.CreateElement("DmeUnpackVector3Operator","positionUnpack",shot.GetFileId())
	animSet.AddOperator(posUnpack)
	posConn = sfmUtils.CreateConnection( "positionConnection", animSet.FindControl("transform"), "valuePosition", animSet )
	posConn.AddOutput(posUnpack, "vector")
	
	
	
	""" Unpacking Orientation Coordinates (3-dimensional vector of Magnitude 1) """
	orientX,orientY,orientZ = GetOrientationCoordinates(shot, animSet, posUnpack)
	
	""" Creating the relative distance calculation """
	#We create an Expression (a calculation applied every time any of its elements change) element.
	distanceExpr = sfmUtils.CreateExpression("relativeDistance", "(u1*(x1-x2)+u2*(y1-y2)+u3*(z1-z2))", animSet ) #Here we calculate the distance between A1(x1,y1,z1) and A2(x2,y2,z2) following direction U(u1,u2,u3) i.e. the positive value of (A2-A1).U (dot product). U should be have a magnitude of 1.

	#We create the needed attributes (variables/fields) :
	distanceExpr.SetValue( "x1", 0.) # /!\ The dot after the zero is important, as we are dealing with FLOATS in Expressions, and the type of the created attribute is automatically determined by the given value (0->int, 0.->float)
	# sfmUtils.AddAttributeToElement( distanceExpr, "x1", vs.AT_FLOAT, 0. ) # <- This is what is actually happening, but it's longer to type ;)
	distanceExpr.SetValue( "y1", 0.)
	distanceExpr.SetValue( "z1", 0.)
	distanceExpr.SetValue( "x2", 0.)
	distanceExpr.SetValue( "y2", 0.)
	distanceExpr.SetValue( "z2", 0.)
	distanceExpr.SetValue( "u1", 0.)
	distanceExpr.SetValue( "u2", 0.)
	distanceExpr.SetValue( "u3", 0.)

	#We link the unpacked values to those elements :
		#Point A1 : the FocalPlaneBone
	x1Conn = sfmUtils.CreateConnection("x1Conn", focalPlaneBoneUnpack, "x", animSet) #the input (focalPlaneBoneUnpack, "x") goes with the creation of the connection.
	x1Conn.AddOutput(distanceExpr, "x1") #and finally the output
	y1Conn = sfmUtils.CreateConnection("y1Conn", focalPlaneBoneUnpack, "y", animSet) 
	y1Conn.AddOutput(distanceExpr, "y1") 
	z1Conn = sfmUtils.CreateConnection("z1Conn", focalPlaneBoneUnpack, "z", animSet) 
	z1Conn.AddOutput(distanceExpr, "z1") 
		#Point A2 : the Root Transform
	x2Conn = sfmUtils.CreateConnection("x2Conn", posUnpack, "x", animSet)
	x2Conn.AddOutput(distanceExpr, "x2")
	y2Conn = sfmUtils.CreateConnection("y2Conn", posUnpack, "y", animSet) 
	y2Conn.AddOutput(distanceExpr, "y2") 
	z2Conn = sfmUtils.CreateConnection("z2Conn", posUnpack, "z", animSet) 
	z2Conn.AddOutput(distanceExpr, "z2")
		#Direction U : the orientation 
	u1Conn = sfmUtils.CreateConnection("u1Conn", orientX, "result", animSet)
	u1Conn.AddOutput(distanceExpr, "u1")
	u2Conn = sfmUtils.CreateConnection("u2Conn", orientY, "result", animSet) 
	u2Conn.AddOutput(distanceExpr, "u2") 
	u3Conn = sfmUtils.CreateConnection("u3Conn", orientZ, "result", animSet) 
	u3Conn.AddOutput(distanceExpr, "u3") 
	

	""" Overriding the actual focal distance of the camera """
	#To do so, we look at the channel that tells the camera what its focal distance should be (here it is 'scaled_focalDistance_channel' after a look at the Element Viewer)
	#and we replace its default input (the lerp calculation from the AnimationSet slider) by the 'result' of our distanceExpr calculation.
	animSetChannels = sfmUtils.GetChannelsClipForAnimSet( animSet, shot ).channels
	for channel in animSetChannels: #we can't access 'channel.scaled_focalDistance_channel' directly.
		if channel.GetName() == "scaled_focalDistance_channel":
			channel.fromElement = distanceExpr #'from' == input and 'to' == output
			channel.fromAttribute = "result"
#End of method

			
	
def GetOrientationCoordinates(shot, animSet, posUnpack): #It should be far simpler than all this mess but I can't handle quaternion angles :/
	""" Adding an inverse ViewTarget helper """
	#Adding it :
	inverseVTAnimSet = sfmUtils.CreateModelAnimationSet( "inverse_VT_helper", "models/editor/axis_helper.mdl" )
	#Hiding it :
	inverseVTAnimSet.GetRootControlGroup().SetVisible(False)
	inverseVTAnimSet.GetRootControlGroup().SetSelectable(False)
	inverseVTAnimSet.gameModel.visible.SetValue(False)
	#Positionning it in front of the camera :
		#First we move the camera to the origin of the map:
	sfm.SetOperationMode( "Pass" ) # This makes the changes temporary (use 'Record' mode if you want to keep them saved after the script ends.)
	sfm.ClearSelection()
	sfm.SelectDag(animSet.camera)
	sfm.Move( 0, 0, 0, space="world" )
	sfm.Rotate( 0, 0, 0 )
		#Then we move our inverseVT right in front of the camera :
	sfm.Select(inverseVTAnimSet.GetName())
	sfm.Move( -1, 0, 0, space="world" ) #The '1' here will give us a vector of Magnitude 1 :D
		#Finally we constraint the inverseVT position relative to the camera's with a Parent Constraint
	sfm.ParentConstraint(animSet.GetName()+":transform", inverseVTAnimSet.GetName()+":rootTransform", mo=True)

	""" Using that helper to get the Orientation vector """
	#First, we get the inverseVT coordinates :	
	inverseVTUnpack = vs.CreateElement("DmeUnpackVector3Operator","inverseVTUnpack",shot.GetFileId()) 
	animSet.AddOperator(inverseVTUnpack)
	inverseVTConn = sfmUtils.CreateConnection( "inverseViewTargetCoordinatesConnection", inverseVTAnimSet.gameModel.transform, "position", animSet )
	inverseVTConn.AddOutput(inverseVTUnpack, "vector") 
	#Then the relative vector coordinates:
		#X
	orientationVectorX = sfmUtils.CreateExpression("orientationVectorX", "xVT-xCam", animSet ) 
	orientationVectorX.SetValue("xVT", 0.)
	orientationVectorX.SetValue("xCam", 0.)
	orientationVectorXVT_conn = sfmUtils.CreateConnection( "orientationVectorXVT_conn", inverseVTUnpack, "x", animSet )
	orientationVectorXVT_conn.AddOutput(orientationVectorX,"xVT")
	orientationVectorXCam_conn = sfmUtils.CreateConnection( "orientationVectorXCam_conn", posUnpack, "x", animSet )
	orientationVectorXCam_conn.AddOutput(orientationVectorX,"xCam")
		#Y
	orientationVectorY = sfmUtils.CreateExpression("orientationVectorY", "yVT-yCam", animSet ) 
	orientationVectorY.SetValue("yVT", 0.)
	orientationVectorY.SetValue("yCam", 0.)
	orientationVectorYVT_conn = sfmUtils.CreateConnection( "orientationVectorYVT_conn", inverseVTUnpack, "y", animSet )
	orientationVectorYVT_conn.AddOutput(orientationVectorY,"yVT")
	orientationVectorYCam_conn = sfmUtils.CreateConnection( "orientationVectorYCam_conn", posUnpack, "y", animSet )
	orientationVectorYCam_conn.AddOutput(orientationVectorY,"yCam")
		#Z
	orientationVectorZ = sfmUtils.CreateExpression("orientationVectorZ", "zVT-zCam", animSet ) 
	orientationVectorZ.SetValue("zVT", 0.)
	orientationVectorZ.SetValue("zCam", 0.)
	orientationVectorZVT_conn = sfmUtils.CreateConnection( "orientationVectorZVT_conn", inverseVTUnpack, "z", animSet )
	orientationVectorZVT_conn.AddOutput(orientationVectorZ,"zVT")
	orientationVectorZCam_conn = sfmUtils.CreateConnection( "orientationVectorZCam_conn", posUnpack, "z", animSet )
	orientationVectorZCam_conn.AddOutput(orientationVectorZ,"zCam")
	
	return orientationVectorX,orientationVectorY,orientationVectorZ
#End of method

	
	
	
try:
	AddFocalPlaneBone()
except WrongUseException as ex:
	MessageBox(None, str(ex), "Source Filmmaker", MB_ICONERROR)