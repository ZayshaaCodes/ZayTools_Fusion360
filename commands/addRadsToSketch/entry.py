import adsk.core, traceback, math
import adsk.fusion
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_addRadsToSketch'
CMD_NAME = 'Add Rads to Sketch'
CMD_Description = 'add radiuses to corners based on the internal turn angle'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED

# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    # Create a simple text box input.
    tb = inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)
    tb.text = ''
    tb.isFullWidth = True
    tb.numRows = 50

    # tb.text += app.activeProduct.productType + '\n'
    if app.activeProduct.productType == "DesignProductType":
        root = adsk.fusion.Design.cast(app.activeProduct)

        # tb.text += '\n' + root.activeEditObject.objectType + '\n'
        if root.activeEditObject.objectType == "adsk::fusion::Sketch":
            sketch = adsk.fusion.Sketch.cast(root.activeEditObject)

            profile = sketch.profiles.item(0) 
            
            # list datadfor all the contained curves in the profileloops
            # build a collection of data to be used to add fillets between each curve based on the angle between them
            # the first element will connect with the last element
            # only add fillets between connected line3d's

            try:
                connections = []
                curves = profile.profileLoops.item(0).profileCurves
                for i in range(curves.count):
                    first = curves.item(i)
                    second = curves.item((i + 1) % curves.count)
                    
                    #line3d
                    if first.geometry.objectType == "adsk::core::Line3D" and second.geometry.objectType == "adsk::core::Line3D":
                        firstGeo = adsk.core.Line3D.cast(first.geometry)
                        secondGeo = adsk.core.Line3D.cast(second.geometry)

                        
                        
                        # add the needed data to collection: first element, first element end point, second element, second element start point
                        connections.append([first.sketchEntity, firstGeo.endPoint, second.sketchEntity, secondGeo.startPoint])

                for connection in connections:
                    tb.text += f"{Point3dToString(connection[1])} -> {Point3dToString(connection[3])}\n"
                    # type if sket entity
                    firstLine = adsk.fusion.SketchLine.cast(connection[0])
                    secondLine = adsk.fusion.SketchLine.cast(connection[2])

                    #meause theanglebetween the lines

                    angle = calculate_angle_between_lines(firstLine.geometry, secondLine.geometry)

                    tb.text += f"{connection[0].objectType} -> {connection[2].objectType}\n"
                    tb.text += f"{(angle / 3.14159*180):.4f}\n"

                    # sketch.sketchCurves.sketchArcs.addFillet(connection[0], connection[1], connection[2], connection[3], 0.1)
            except Exception as e:
                ui.messageBox(f"Error: {e}")

    # get the root components of the active design.
    #     # tb.text = object_fields_to_string(root.rootComponent)

    #     bb = adsk.core.BoundingBox3D.cast(root.rootComponent.boundingBox)
    #     min = adsk.core.Point3D.cast(bb.minPoint)
    #     max = adsk.core.Point3D.cast(bb.maxPoint)

    #     tb.text = Point3dToString(scalePoint3d(addPoint3d(min, max), 0.5))

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def calculate_angle_between_lines(line1: adsk.core.Line3D, line2: adsk.core.Line3D) -> float:
    """
    Calculates the angle between two lines.
    
    :param line1: The first line (adsk.core.Line3D).
    :param line2: The second line (adsk.core.Line3D).
    :return: The angle between the lines in radians (float).
    """
    # Get the start and end points of each line to form vectors
    start1 = line1.startPoint
    end1 = line1.endPoint
    vector1 = adsk.core.Vector3D.create(end1.x - start1.x, end1.y - start1.y, end1.z - start1.z)

    start2 = line2.startPoint
    end2 = line2.endPoint
    vector2 = adsk.core.Vector3D.create(end2.x - start2.x, end2.y - start2.y, end2.z - start2.z)

    # Normalize the vectors
    vector1.normalize()
    vector2.normalize()

    # Calculate the dot product
    dotProduct = vector1.dotProduct(vector2)

    # Ensure the dot product is within the valid range [-1, 1] to avoid numerical issues
    dotProduct = max(min(dotProduct, 1.0), -1.0)

    # Calculate the angle in radians
    angleRadians = math.acos(dotProduct)

    return angleRadians

def addPoint3d(p1: adsk.core.Point3D, p2: adsk.core.Point3D):
    return adsk.core.Point3D.create(p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

def scalePoint3d(p: adsk.core.Point3D, scale: float):
    return adsk.core.Point3D.create(p.x * scale, p.y * scale, p.z * scale)

def Point3dToString(p: adsk.core.Point3D):
    #round to nearst 10000th
    return f"({p.x:.4f}, {p.y:.4f}, {p.z:.4f})"

def object_fields_to_string(obj):
    result = []
    for attribute in dir(obj):
        # Exclude magic methods and attributes
        if not attribute.startswith('__'):
            value = getattr(obj, attribute)
            if value is None:
                result.append(f"{attribute}: None")
            else:
                result.append(f"{attribute}: {value}")
    return '\n'.join(result)

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs

    # value_input: adsk.core.ValueCommandInput = inputs.itemById('value_input')
    

# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs

    


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
