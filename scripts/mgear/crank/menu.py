import pymel.core as pm
import mgear
from mgear.crank import crank_tool


def install():
    """Install Crank submenu
    """
    pm.setParent(mgear.menu_id, menu=True)
    pm.menuItem(divider=True)
    pm.menuItem(label="Crank: Shot Sculpt", command=crank_tool.openUI)
