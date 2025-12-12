"""
Lazy imports para reducir el tiempo de carga inicial de function_app.py
"""
from typing import Any, Optional

# Placeholders para imports pesados
_azure_mgmt_web = None
_azure_mgmt_storage = None
_azure_mgmt_compute = None
_azure_mgmt_network = None
_azure_mgmt_monitor = None
_azure_mgmt_resource = None


def get_web_client():
    """Lazy import de WebSiteManagementClient"""
    global _azure_mgmt_web
    if _azure_mgmt_web is None:
        try:
            from azure.mgmt.web import WebSiteManagementClient
            _azure_mgmt_web = WebSiteManagementClient
        except ImportError:
            _azure_mgmt_web = False
    return _azure_mgmt_web if _azure_mgmt_web is not False else None


def get_storage_client():
    """Lazy import de StorageManagementClient"""
    global _azure_mgmt_storage
    if _azure_mgmt_storage is None:
        try:
            from azure.mgmt.storage import StorageManagementClient
            _azure_mgmt_storage = StorageManagementClient
        except ImportError:
            _azure_mgmt_storage = False
    return _azure_mgmt_storage if _azure_mgmt_storage is not False else None


def get_compute_client():
    """Lazy import de ComputeManagementClient"""
    global _azure_mgmt_compute
    if _azure_mgmt_compute is None:
        try:
            from azure.mgmt.compute import ComputeManagementClient
            _azure_mgmt_compute = ComputeManagementClient
        except ImportError:
            _azure_mgmt_compute = False
    return _azure_mgmt_compute if _azure_mgmt_compute is not False else None


def get_network_client():
    """Lazy import de NetworkManagementClient"""
    global _azure_mgmt_network
    if _azure_mgmt_network is None:
        try:
            from azure.mgmt.network import NetworkManagementClient
            _azure_mgmt_network = NetworkManagementClient
        except ImportError:
            _azure_mgmt_network = False
    return _azure_mgmt_network if _azure_mgmt_network is not False else None


def get_monitor_client():
    """Lazy import de MonitorManagementClient"""
    global _azure_mgmt_monitor
    if _azure_mgmt_monitor is None:
        try:
            from azure.mgmt.monitor import MonitorManagementClient
            _azure_mgmt_monitor = MonitorManagementClient
        except ImportError:
            _azure_mgmt_monitor = False
    return _azure_mgmt_monitor if _azure_mgmt_monitor is not False else None


def get_resource_client():
    """Lazy import de ResourceManagementClient"""
    global _azure_mgmt_resource
    if _azure_mgmt_resource is None:
        try:
            from azure.mgmt.resource import ResourceManagementClient
            _azure_mgmt_resource = ResourceManagementClient
        except ImportError:
            _azure_mgmt_resource = False
    return _azure_mgmt_resource if _azure_mgmt_resource is not False else None
