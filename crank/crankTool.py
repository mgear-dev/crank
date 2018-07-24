import pymel.core as pm
import maya.cmds as cmds
from pymel import versions
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from mgear.vendor.Qt import QtCore, QtWidgets, QtGui
from mgear.core import transform, node, attribute, applyop, pyqt, utils, curve
from mgear.core import string

from . import crankUI

'''
TODO:

    layer lister:
        -Right click menu
            -Select members
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

CRANK_TAG = "_isCrankLayer"

####################################
# Layer Node
####################################


def create_layer(oSel):

    oSel = [x for x in oSel
            if x.getShapes()
            and x.getShapes()[0].type() == 'mesh']
    print oSel

    if oSel:
        result = pm.promptDialog(title='Crank Layer Name',
                                 message='Enter Name:',
                                 button=['OK', 'Cancel'],
                                 defaultButton='OK',
                                 cancelButton='Cancel',
                                 dismissString='Cancel',
                                 text="")

        if result == 'OK':
            text = pm.promptDialog(query=True, text=True)
            name = string.normalize(text)

            layer_node = create_layer_node(name, oSel)
            bs_list = create_blendshape_node(name, oSel)
            for bs in bs_list:
                layer_node.crank_layer_envelope >> bs.envelope
                idx = attribute.get_next_available_index(
                    layer_node.layer_blendshape_node)
                pm.connectAttr(bs.message,
                               layer_node.layer_blendshape_node[idx])
            pm.select(oSel)

            return layer_node


def create_blendshape_node(bsName, oSel):
    bs_list = []
    for obj in oSel:
        bs = pm.blendShape(obj,
                           name="_".join([obj.name(),
                                          bsName,
                                          "blendShape_crank"]),
                           foc=False)[0]
        print bs
        bs_list.append(bs)

    return bs_list


def create_layer_node(name, affectedElements):
        # create a transform node that contain the layer information and

    fullName = name + "_crankLayer"

    # create node
    if pm.ls(fullName):
        pm.displayWarning("{} already exist".format(fullName))
        return
    layer_node = pm.createNode("transform",
                               n=fullName,
                               p=None,
                               ss=True)
    attribute.lockAttribute(layer_node)
    # add attrs
    attribute.addAttribute(
        layer_node, CRANK_TAG, "bool", False, keyable=False)
    # affected objects
    layer_node.addAttr("layer_objects", at='message', m=True)
    layer_node.addAttr("layer_blendshape_node", at='message', m=True)
    # master envelope for on/off
    attribute.addAttribute(layer_node,
                           "crank_layer_envelope",
                           "float",
                           value=1,
                           minValue=0,
                           maxValue=1)
    # create the post-blendshapes nodes for each affected object

    # connections
    for x in affectedElements:
        idx = attribute.get_next_available_index(layer_node.layer_objects)
        print idx
        print x
        pm.connectAttr(x.message, layer_node.layer_objects[idx])

    return layer_node


def list_crank_layer_nodes():
    return [sm for sm in cmds.ls(type="transform") if cmds.attributeQuery(
        CRANK_TAG, node=sm, exists=True)]


def get_layer_affected_elements(layer_node):
    return


####################################
# sculpt frame
####################################

def add_frame_sculpt(layer_node, solo=False):

    objs = layer_node.layer_objects.inputs()
    bs_node = layer_node.layer_blendshape_node.inputs()

    # ensure other targets are set to false the edit flag

    # get current frame
    cframe = int(pm.currentTime(query=True))

    # get valid name. Check if frame is ducplicated in layer
    frame_name = "frame_{}".format(str(cframe))
    i = 1
    while layer_node.hasAttr(frame_name):
        frame_name = "frame_{}_v{}".format(str(cframe), str(i))
        i += 1

    # create frame master channel
    master_chn = attribute.addAttribute(layer_node,
                                        frame_name,
                                        "float",
                                        value=1,
                                        minValue=0,
                                        maxValue=1)

    # keyframe in range the master channel
    pm.setKeyframe(master_chn,
                   t=[cframe],
                   v=1,
                   inTangentType="linear",
                   outTangentType="linear")
    pm.setKeyframe(master_chn,
                   t=[cframe - 1, cframe + 1],
                   v=0,
                   inTangentType="linear",
                   outTangentType="linear")

    for obj, bsn in zip(objs, bs_node):
        dup = pm.duplicate(obj)[0]
        bst_name = "_".join([obj.name(), frame_name])
        pm.rename(dup, bst_name)
        indx = bsn.weight.getNumElements()
        pm.blendShape(bsn,
                      edit=True,
                      t=(obj, indx, dup, 1.0),
                      ts=True,
                      tc=True,
                      w=(indx, 1))
        pm.delete(dup)
        pm.blendShape(bsn, e=True, rtd=(0, indx))
        # is same as: bs.inputTarget[0].sculptTargetIndex.set(3)
        pm.sculptTarget(bsn, e=True, t=indx)

        # connect target to master channel
        pm.connectAttr(master_chn, bsn.attr(bst_name))

        #select affected elements
        pm.select(objs)


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

        self.__proxyModel = QtCore.QSortFilterProxyModel(self)
        self.crankUIWInst.layers_listView.setModel(self.__proxyModel)

        self.setup_crankWindow()
        self.create_layout()
        self.create_connections()
        self._refreshList()

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

    def setSourceModel(self, model):
        self.__proxyModel.setSourceModel(model)

    ###########################
    # Helper functions
    ###########################

    def _refreshList(self):
        model = QtGui.QStandardItemModel(self)
        for c_node in list_crank_layer_nodes():
            model.appendRow(QtGui.QStandardItem(c_node))
        self.setSourceModel(model)

    def _getSelectedListIndexes(self):
        layers = []
        for x in self.crankUIWInst.layers_listView.selectedIndexes():
            print x
            try:
                layers.append(pm.PyNode(x.data()))

            except pm.MayaNodeError:
                pm.displayWarning("{}  can't be find.".format(x.data()))
                return False
        return layers

    def create_layer(self):
        print "create layer now"
        create_layer(pm.selected())
        self._refreshList()

    def add_frame_sculpt(self):
        # layer_node = pm.PyNode("ddd_crankLayer")
        for layer_node in self._getSelectedListIndexes():
            add_frame_sculpt(layer_node)

    ###########################
    # create connections SIGNALS
    ###########################
    def create_connections(self):
        self.crankUIWInst.search_lineEdit.textChanged.connect(
            self.filterChanged)
        self.crankUIWInst.refresh_pushButton.clicked.connect(
            self._refreshList)
        self.crankUIWInst.createLayer_pushButton.clicked.connect(
            self.create_layer)
        self.crankUIWInst.addFrame_pushButton.clicked.connect(
            self.add_frame_sculpt)

    #############
    # SLOTS
    #############
    def filterChanged(self, filter):
        regExp = QtCore.QRegExp(filter,
                                QtCore.Qt.CaseSensitive,
                                QtCore.QRegExp.Wildcard
                                )
        self.__proxyModel.setFilterRegExp(regExp)


def openUI(*args):
    pyqt.showDialog(crankTool)

####################################


if __name__ == "__main__":

    openUI()
