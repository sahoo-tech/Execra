from fastapi import APIRouter
from core.plugins.rule_loader import PluginLoader

router = APIRouter()
plugin_loader = PluginLoader()
plugin_loader.load_all()


@router.get("/plugins")
def get_plugins():
    plugins = plugin_loader.plugins
    return [
        {
            "name": p.name,
            "version": p.version,
            "severity": p.severity,
            "enabled": p.enabled,
            "trigger_keywords": p.trigger_keywords,
            "trigger_objects": p.trigger_objects,
        }
        for p in plugins
    ]