"""Public API for the morel.serve package."""

from morel.serve.app import (
    Ask,
    Rollback,
    Stats,
    Tell,
    create,
)
from morel.serve.auth import (
    EnvironmentSecretProvider,
    Scope,
    SecretProvider,
    admin,
    assert_,
    dependency,
    token,
    viewer,
)
from morel.serve.failures import FailureKind, FailurePolicy, classify
from morel.serve.loader import Loader
from morel.serve.lock import Read, RWLock, Write, reader, writer
from morel.serve.protocol import ServingPipeline, is_serving_pipeline
from morel.serve.schema import (
    Done,
    Fill,
    Health,
    List,
    Pick,
    Query,
    serialize,
)
from morel.serve.update import (
    Default,
    Event,
    Outcome,
    Signal,
    Step,
    Updater,
)

__all__ = [
    "Ask",
    "Default",
    "Done",
    "EnvironmentSecretProvider",
    "Event",
    "FailureKind",
    "FailurePolicy",
    "Fill",
    "Health",
    "List",
    "Loader",
    "Outcome",
    "Pick",
    "Query",
    "RWLock",
    "Read",
    "Rollback",
    "Scope",
    "SecretProvider",
    "ServingPipeline",
    "Signal",
    "Stats",
    "Step",
    "Tell",
    "Updater",
    "Write",
    "admin",
    "assert_",
    "classify",
    "create",
    "dependency",
    "is_serving_pipeline",
    "reader",
    "serialize",
    "token",
    "viewer",
    "writer",
]
