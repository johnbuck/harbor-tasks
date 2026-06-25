"""Offline parse checks for the prod-agent deliverable config + task.

Encodes spec success criterion #7: configs/prod-agent-example.yaml and
tasks/prod-behavioral/basic-knowledge-qa/task.toml parse under Harbor's config
loaders, and the YAML's import_path fields resolve to the new classes. No docker
required.

CONTRACT NOTE for the builder: the conversational task shape directory this
suite expects is ``tasks/prod-behavioral/basic-knowledge-qa/`` and the example
config is ``configs/prod-agent-example.yaml``. The YAML must set
``environment.import_path``, ``agents[0].import_path`` and
``verifier.import_path`` to the three new lib classes.
"""
import yaml

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.job.config import JobConfig
from harbor.models.task.config import TaskConfig
from harbor.utils.import_path import import_class
from harbor.verifier.base import BaseVerifier

from helpers import REPO_ROOT

CONFIG_PATH = REPO_ROOT / "configs" / "prod-agent-example.yaml"
TASK_TOML_PATH = (
    REPO_ROOT / "tasks" / "prod-behavioral" / "basic-knowledge-qa" / "task.toml"
)


def test_example_config_parses_and_import_paths_resolve():
    config = JobConfig.model_validate(yaml.safe_load(CONFIG_PATH.read_text()))

    assert config.environment.import_path, "environment.import_path must be set"
    assert config.agents and config.agents[0].import_path, (
        "an agent entry with import_path must be set"
    )
    assert config.verifier.import_path, "verifier.import_path must be set"

    # Each import_path must resolve to a subclass of the right Harbor base.
    import_class(config.environment.import_path, base=BaseEnvironment)
    import_class(config.agents[0].import_path, base=BaseAgent)
    import_class(config.verifier.import_path, base=BaseVerifier)


def test_prod_behavioral_task_toml_parses():
    TaskConfig.model_validate_toml(TASK_TOML_PATH.read_text())
