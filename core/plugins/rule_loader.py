import os
import logging
import yaml
from dataclasses import dataclass, field
from typing import Literal
from pydantic import BaseModel, ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class RulePlugin(BaseModel):
    name: str
    version: str
    trigger_keywords: list[str]
    trigger_objects: list[str]
    severity: Literal["info", "warning", "critical"]
    instruction_template: str
    enabled: bool


class PluginLoader:
    def __init__(self):
        self.plugins: list[RulePlugin] = []
        self._observer = None

    def load_all(self, directory: str = "plugins/rules/") -> list[RulePlugin]:
        self.plugins = []
        if not os.path.exists(directory):
            logger.warning(f"Plugin directory '{directory}' does not exist.")
            return self.plugins

        for filename in os.listdir(directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, "r") as f:
                        data = yaml.safe_load(f)
                    plugin = RulePlugin(**data)
                    self.plugins.append(plugin)
                    logger.info(f"Loaded plugin: {plugin.name}")
                except (ValidationError, Exception) as e:
                    logger.warning(f"Skipping invalid plugin file '{filename}': {e}")

        return self.plugins

    def reload(self, directory: str = "plugins/rules/") -> list[RulePlugin]:
        logger.info("Reloading plugins...")
        return self.load_all(directory)

    def get_enabled(self) -> list[RulePlugin]:
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        enabled = [p for p in self.plugins if p.enabled]
        return sorted(enabled, key=lambda p: severity_order[p.severity])