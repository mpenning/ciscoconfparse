import inspect
from Exscript.protocols.drivers.driver import Driver
from Exscript.protocols.drivers.aironet import AironetDriver
from Exscript.protocols.drivers.aix import AIXDriver
from Exscript.protocols.drivers.arbor_peakflow import ArborPeakflowDriver
from Exscript.protocols.drivers.brocade import BrocadeDriver
from Exscript.protocols.drivers.enterasys import EnterasysDriver
from Exscript.protocols.drivers.generic import GenericDriver
from Exscript.protocols.drivers.hp_pro_curve import HPProCurveDriver
from Exscript.protocols.drivers.ios import IOSDriver
from Exscript.protocols.drivers.ios_xr import IOSXRDriver
from Exscript.protocols.drivers.junos import JunOSDriver
from Exscript.protocols.drivers.junos_erx import JunOSERXDriver
from Exscript.protocols.drivers.one_os import OneOSDriver
from Exscript.protocols.drivers.shell import ShellDriver
from Exscript.protocols.drivers.smart_edge_os import SmartEdgeOSDriver
from Exscript.protocols.drivers.vrp import VRPDriver
from Exscript.protocols.drivers.sros import SROSDriver
from Exscript.protocols.drivers.aruba import ArubaDriver
from Exscript.protocols.drivers.enterasys_wc import EnterasysWCDriver
from Exscript.protocols.drivers.fortios import FortiOSDriver

driver_classes = []
drivers        = []
driver_map     = {}

def isdriver(o):
    return inspect.isclass(o) and issubclass(o, Driver) and not o is Driver

def add_driver(cls):
    driver = cls()
    driver_classes.append(cls)
    drivers.append(driver)
    driver_map[driver.name] = driver

# Load built-in drivers.
for name, obj in locals().items():
    if isdriver(obj):
        add_driver(obj)
driver_map['unknown'] = driver_map['generic']
