import os
import pytest
import yaml
from core.plugins.rule_loader import PluginLoader, RulePlugin
from core.intelligence.plugin_rule_engine import PluginRuleEngine


# ── helpers ──────────────────────────────────────────────────────────────────

def write_yaml(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


VALID_PLUGIN = {
    "name": "Test Plugin",
    "version": "1.0.0",
    "trigger_keywords": ["error", "null"],
    "trigger_objects": ["error_dialog"],
    "severity": "warning",
    "instruction_template": "Check for null values.",
    "enabled": True,
}

INVALID_PLUGIN = {
    "name": "Bad Plugin",
    # missing required fields
}


# ── tests ─────────────────────────────────────────────────────────────────────

def test_valid_plugin_load(tmp_path):
    plugin_dir = str(tmp_path / "rules")
    write_yaml(f"{plugin_dir}/valid.yaml", VALID_PLUGIN)

    loader = PluginLoader()
    plugins = loader.load_all(plugin_dir)

    assert len(plugins) == 1
    assert plugins[0].name == "Test Plugin"


def test_invalid_yaml_skipped(tmp_path):
    plugin_dir = str(tmp_path / "rules")
    write_yaml(f"{plugin_dir}/invalid.yaml", INVALID_PLUGIN)

    loader = PluginLoader()
    plugins = loader.load_all(plugin_dir)

    assert len(plugins) == 0


def test_hot_reload(tmp_path):
    plugin_dir = str(tmp_path / "rules")
    write_yaml(f"{plugin_dir}/valid.yaml", VALID_PLUGIN)

    loader = PluginLoader()
    loader.load_all(plugin_dir)
    assert len(loader.plugins) == 1

    # Add another plugin
    VALID_PLUGIN_2 = {**VALID_PLUGIN, "name": "Plugin 2"}
    write_yaml(f"{plugin_dir}/valid2.yaml", VALID_PLUGIN_2)

    loader.reload(plugin_dir)
    assert len(loader.plugins) == 2


def test_severity_ordering(tmp_path):
    plugin_dir = str(tmp_path / "rules")

    info_plugin = {**VALID_PLUGIN, "name": "Info Plugin", "severity": "info"}
    critical_plugin = {**VALID_PLUGIN, "name": "Critical Plugin", "severity": "critical"}
    warning_plugin = {**VALID_PLUGIN, "name": "Warning Plugin", "severity": "warning"}

    write_yaml(f"{plugin_dir}/info.yaml", info_plugin)
    write_yaml(f"{plugin_dir}/critical.yaml", critical_plugin)
    write_yaml(f"{plugin_dir}/warning.yaml", warning_plugin)

    loader = PluginLoader()
    loader.load_all(plugin_dir)
    enabled = loader.get_enabled()

    assert enabled[0].severity == "critical"
    assert enabled[1].severity == "warning"
    assert enabled[2].severity == "info"


def test_evaluate_matches(tmp_path):
    plugin_dir = str(tmp_path / "rules")
    write_yaml(f"{plugin_dir}/valid.yaml", VALID_PLUGIN)

    loader = PluginLoader()
    loader.load_all(plugin_dir)

    engine = PluginRuleEngine(loader)
    outcomes = engine.evaluate("null pointer detected", ["error_dialog"])

    assert len(outcomes) > 0
    assert outcomes[0].plugin_name == "Test Plugin"