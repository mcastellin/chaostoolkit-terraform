"""Top-level package for chaosterraform"""
from typing import List

from chaoslib.discovery.discover import discover_activities, initialize_discovery_result
from chaoslib.types import DiscoveredActivities, Discovery

name = "chaosterraform"
__author__ = """Manuel Castellin"""
__email__ = "manuel@castellinconsulting.com"
__version__ = "0.0.0"
__all__ = [
    "discover",
    "__version__",
]


def discover(discover_system: bool = True) -> Discovery:
    """Discover chaostoolkit activities"""
    # pylint: disable=unused-argument
    discovery = initialize_discovery_result("chaosterraform", __version__, "chaosterraform")
    discovery["activities"].extend(load_exported_activities())
    return discovery


def load_exported_activities() -> List[DiscoveredActivities]:
    """
    Extract metadata from actions and probes exposed by this extension.
    """
    activities = []
    activities.extend(discover_activities("chaosterraform.control", "control"))

    return activities
