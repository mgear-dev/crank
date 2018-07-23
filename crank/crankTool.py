import datetime
import getpass
import json

import mgear
import mgear.core.icon as ico
import pymel.core as pm
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from mgear import shifter
from mgear.core import transform, node, attribute, applyop, pyqt, utils, curve
from mgear.vendor.Qt import QtCore, QtWidgets
from pymel import versions
from pymel.core import datatypes

from mgear.core import string
from . import crankUI

'''
TODO:

    layer lister:
        -Right click menu
            -Toggle ON/OFF
            -Solo
            -Random Color (for each object in the layer)
            -Ghost Create
            -Ghost Delete
            -Delete Selected Layer
            -----------
            -Add selected to layer
            -Remove selected from layer
            -----------
            -Turn Selected ON
            -Turn Selected OFF
            -----------
            -Turn All ON
            -Turn All OFF


    sculpt frame attributes:
        -frame number

'''

####################################
# Crank
####################################


# Layer Node

CRANK_TAG = "_isCrankLayer"


def create_layer_node(name, affectedElements):
	# create a transform node that contain the layer information and

    fullName = name + "_crankLayer"

    # create node
    if  pm.ls(fullName):
        pm.displayWarning("{} already exist".format(fullName))
        return
    layer_node = pm.createNode("transform",
                             n=fullName,
                             p=None,
                             ss=True)

    # add attrs
    attribute.addAttribute(
        layer_node, CRANK_TAG, "bool", False, keyable=False)
    # affected objects
    layer_node.addAttr("layer_objects", at='message', m=True)
    layer_node.addAttr("layer_blendshape_node", at='message', m=True)
    # master envelope for on/off
    attribute.addAttribute(layer_node,
                           "layer_envelope"
                           "float",
                           value=1,
                           minValue=0,
                           maxValue=1)
    # create the post-blendshapes nodes for each affected object



    # connections
    for x in affectedElements:
        idx = attribute.get_next_available_index(layer_node.layer_objects)
        pm.connectAttr(x.message, layer_node.layer_objects[idx])

    return layer_node

def list_crank_layer_nodes():
    return [sm for sm in cmds.ls(type="transform") if cmds.attributeQuery(
                CRANK_TAG, node=sm, exists=True)]

def get_layer_affected_elements(layer_node):
    return

# sculpt frame

def create_sculpt_frame(solo=False):
    return
def delete_sculpt_frame():
    return
def edit_sculpt_frame():
    return







####################################
# Crank Tool UI
####################################

class crankUIW(QtWidgets.QDialog, crankUI.Ui_Form):

    """UI Widget
    """

    def __init__(self, parent=None):
        super(crankUIW, self).__init__(parent)
        self.setupUi(self)


class crankTool(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    valueChanged = QtCore.Signal(int)
    wi_to_destroy = []

    def __init__(self, parent=None):
        self.toolName = "Crank"
        super(crankTool, self).__init__(parent)
        self.crankUIWInst = crankUIW()

        self.setup_crankWindow()
        self.create_layout()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    def setup_crankWindow(self):

        self.setObjectName(self.toolName)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle("Crank: Shot Sculpting")
        self.resize(266, 445)

    def create_layout(self):

        self.crank_layout = QtWidgets.QVBoxLayout()
        self.crank_layout.addWidget(self.crankUIWInst)
        self.crank_layout.setContentsMargins(3, 3, 3, 3)

        self.setLayout(self.crank_layout)



def openUI(*args):
    pyqt.showDialog(crankTool)

####################################


if __name__ == "__main__":

    openUI()
