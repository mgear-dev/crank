import pymel.core as pm
import mgear
from mgear.crank import crankTool


def install():
    """Install Simple Rig submenu
    """
    pm.setParent(mgear.menu_id, menu=True)
    pm.menuItem(divider=True)
    pm.menuItem(label="Crank: Shot Sculpt", command=crankTool.openUI)
