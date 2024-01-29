import adsk.core, adsk.fusion
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
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

    point_selection = inputs.addSelectionInput('point_selection', 'Select Point', 'Select a point to create a rectangle around')
    point_selection.setSelectionLimits(1, 0)
    point_selection.addSelectionFilter('SketchPoints')

    # Create a drop-down input for shape selection
    shapeDropDown = inputs.addDropDownCommandInput('shapeDropDown', 'Select Shape', adsk.core.DropDownStyles.TextListDropDownStyle)
    shapeDropDownItems = shapeDropDown.listItems
    shapeDropDownItems.add('Circle', True)
    shapeDropDownItems.add('Rectangle', False)
    
    # Create a group input for Circle with specific value fields
    circleGroup = inputs.addGroupCommandInput('circleGroup', 'Circle Parameters')
    circleGroupInputs = circleGroup.children
    circleGroupInputs.addValueInput('circleRadius', 'Radius', 'cm', adsk.core.ValueInput.createByReal(1.0))
    
    # Create a group input for Rectangle with specific value fields
    rectangleGroup = inputs.addGroupCommandInput('rectangleGroup', 'Rectangle Parameters')
    rectangleGroupInputs = rectangleGroup.children
    rectangleGroupInputs.addValueInput('rectangleWidth', 'Width', 'cm', adsk.core.ValueInput.createByReal(1.0))
    rectangleGroupInputs.addValueInput('rectangleHeight', 'Height', 'cm', adsk.core.ValueInput.createByReal(1.0))
        
    # Initially, show only the inputs for the Circle (default selection)
    circleGroup.isVisible = True
    rectangleGroup.isVisible = False

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

# renders all objects values to a string
def objectdata_to_string(obj):
    data = ''
    for attr in dir(obj):
        if not attr.startswith('__') and not callable(getattr(obj, attr)):
            #if it's a Vector3d or Point3d, print the x,y,z values else just render the default string
            attribute = getattr(obj, attr)
            if attribute.__class__.__name__ == 'Vector3D' or attribute.__class__.__name__ == 'Point3D':
                data += f'{attr}: {getattr(obj, attr).x}, {getattr(obj, attr).y}, {getattr(obj, attr).z}\n'
            else:
                data += f'{attr}: {getattr(obj, attr)}\n'
    return data

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs

    try:
        editObject = app.activeEditObject

        if editObject.classType() == 'adsk::fusion::Sketch':
            sketch = adsk.fusion.Sketch.cast(editObject)

            pointSelections = adsk.core.SelectionCommandInput.cast(inputs.itemById('point_selection'))

            points = []
            for i in range(pointSelections.selectionCount):
                point = adsk.fusion.SketchPoint.cast(pointSelections.selection(i).entity)
                points.append(point)

            # for point in points:
                # make_geometry(sketch, width, height, point)

    except Exception as e:
        ui.messageBox(f'Failed:\n{e}')


    # ui.messageBox(msg)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    try:
        pointSelections = adsk.core.SelectionCommandInput.cast(inputs.itemById('point_selection'))
        editObject = app.activeEditObject
        if editObject.classType() == 'adsk::fusion::Sketch':
            sketch = adsk.fusion.Sketch.cast(editObject)

            shapeDropDown = adsk.core.DropDownCommandInput.cast(inputs.itemById('shapeDropDown'))
            selectedShape = shapeDropDown.selectedItem.name
            for i in range(pointSelections.selectionCount):
                point = adsk.fusion.SketchPoint.cast(pointSelections.selection(i).entity)
                if selectedShape == 'Circle':
                    circleGroup = adsk.core.GroupCommandInput.cast(inputs.itemById('circleGroup'))
                    radius = circleGroup.children.itemById('circleRadius').value
                    make_circle_geometry(sketch, radius, point)
                elif selectedShape == 'Rectangle':
                    rectangleGroup = adsk.core.GroupCommandInput.cast(inputs.itemById('rectangleGroup'))
                    width = rectangleGroup.children.itemById('rectangleWidth').value
                    height = rectangleGroup.children.itemById('rectangleHeight').value
                    make_rectangle_geometry(sketch, width, height, point)
                # elif selectedShape == 'Triangle':
                #     triangleGroup = adsk.core.GroupCommandInput.cast(inputs.itemById('triangleGroup'))
                #     base = triangleGroup.children.itemById('triangleBase').value
                #     height = triangleGroup.children.itemById('triangleHeight').value
                #     make_triangle_geometry(sketch, base, height, point)

    except Exception as e:
        ui.messageBox(f'Failed:\n{e}')

#creates a center point rectangle with the given width and height
def make_rectangle_geometry(sketch: adsk.fusion.Sketch, w, h, c: adsk.fusion.SketchPoint):
    lineList = sketch.sketchCurves.sketchLines.addCenterPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(w, h, 0))
    sketch.sketchDimensions.addDistanceDimension(lineList.item(0).startSketchPoint, lineList.item(0).endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0, h + .5, 0))
    sketch.sketchDimensions.addDistanceDimension(lineList.item(1).startSketchPoint, lineList.item(1).endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-w - .5, 0, 0))

    # add horizontal and vertical constraints
    sketch.geometricConstraints.addHorizontal(lineList.item(0))
    sketch.geometricConstraints.addVertical(lineList.item(1))
    sketch.geometricConstraints.addHorizontal(lineList.item(2))
    sketch.geometricConstraints.addVertical(lineList.item(3))

    # make a diagonal line (start of 0 and 2nd line)
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(
        lineList.item(0).startSketchPoint, lineList.item(2).startSketchPoint)
    line.isConstruction = True

    # add a point and constrain it to the middle of the diagonal line
    midPoint = sketch.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))
    sketch.geometricConstraints.addMidPoint(midPoint, line)
    sketch.geometricConstraints.addCoincident(midPoint, c)

def make_circle_geometry(sketch: adsk.fusion.Sketch, r, c: adsk.fusion.SketchPoint):
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), r)

    # dimension the circle
    sketch.sketchDimensions.addDiameterDimension(circle, adsk.core.Point3D.create(0, r + .5, 0))

    sketch.geometricConstraints.addCoincident(circle.centerSketchPoint, c)



# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    # changed_input = args.input
    inputs = args.inputs

    selectedShape = adsk.core.DropDownCommandInput.cast(args.input)

    if selectedShape.id == 'shapeDropDown':
        selectedShape = selectedShape.selectedItem.name
        inputs.itemById('circleGroup').isVisible = (selectedShape == 'Circle')
        inputs.itemById('rectangleGroup').isVisible = (selectedShape == 'Rectangle')
        inputs.itemById('triangleGroup').isVisible = (selectedShape == 'Triangle')

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {selectedShape.id}')


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
