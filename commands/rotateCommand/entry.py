import adsk.core
import adsk.fusion
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_rotate_cmdDialog'
CMD_NAME = 'Command Dialog Sample'
CMD_Description = 'A Fusion 360 Add-in Command with a dialog'

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
    # tb = inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)
    angle = inputs.addAngleValueCommandInput('angle', 'Angle', adsk.core.ValueInput.createByReal(0))
    angle.setManipulator( adsk.core.Point3D.create(50, 0, 0), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0))

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def addPoint3d(p1: adsk.core.Point3D, p2: adsk.core.Point3D):
    return adsk.core.Point3D.create(p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

def scalePoint3d(p: adsk.core.Point3D, scale: float):
    return adsk.core.Point3D.create(p.x * scale, p.y * scale, p.z * scale)

def Point3dToString(p: adsk.core.Point3D):
    return f"({p.x}, {p.y}, {p.z})"

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
    tb: adsk.core.AngleValueCommandInput = inputs.itemById('angle')
    # value_input: adsk.core.ValueCommandInput = inputs.itemById('value_input')
    
    # get the selected componenets
    selection = ui.activeSelections
    # list how many items are selected and their names and the type of object they are
    # Collect information
    occurrences_to_modify = []
    for i in range(selection.count):
        item = selection.item(i)
        if item.entity.objectType == "adsk::fusion::Occurrence":
            occ = adsk.fusion.Occurrence.cast(item.entity)
            if occ:
                # Store the occurrence and its initial transformation
                occurrences_to_modify.append((occ, occ.transform2))

    # Apply modifications
    for occ, initial_xform in occurrences_to_modify:
        try:
            # Your transformation logic...
            xform = initial_xform
            origin = xform.translation
            
            xform.translation = adsk.core.Vector3D.create(0, 0, 0)
            rot = adsk.core.Matrix3D.create()
            rot.setToRotation(tb.value, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
            xform.transformBy(rot)
            xform.translation = origin

            # Apply the new transformation
            # Make sure this is the correct method to apply a new transformation
            occ.transform2 = xform
            
            # Update your text box
            tb.text += f"Rotated occurrence {occ.name} by 90 degrees\n"
        except Exception as e:
            tb.text += f"Error: {str(e)}\n"
            break


    # Do something interesting
    # text = text_box.text
    # expression = value_input.expression
    # msg = f'Your text: {text}
    ui.messageBox(text_box.text)


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
