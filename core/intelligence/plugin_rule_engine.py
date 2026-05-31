import logging
from dataclasses import dataclass
from core.plugins.rule_loader import PluginLoader, RulePlugin

logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    plugin_name: str
    severity: str
    instruction: str


class PluginRuleEngine:
    def __init__(self, plugin_loader: PluginLoader):
        self.plugin_loader = plugin_loader

    def evaluate(self, screen_text: str, detected_objects: list[str]) -> list[Outcome]:
        outcomes = []
        enabled_plugins = self.plugin_loader.get_enabled()

        for plugin in enabled_plugins:
            keyword_match = any(
                kw.lower() in screen_text.lower()
                for kw in plugin.trigger_keywords
            )
            object_match = any(
                obj.lower() in [o.lower() for o in detected_objects]
                for obj in plugin.trigger_objects
            )

            if keyword_match or object_match:
                outcome = Outcome(
                    plugin_name=plugin.name,
                    severity=plugin.severity,
                    instruction=plugin.instruction_template
                )
                outcomes.append(outcome)
                logger.info(f"Plugin '{plugin.name}' matched.")

        return outcomes