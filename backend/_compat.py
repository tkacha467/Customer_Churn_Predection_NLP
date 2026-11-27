"""Non-destructive ``Backend.* -> backend.*`` import compatibility helpers.

Why this exists:
The canonical Python package directory tracked in git is lowercase ``backend/``,
while legacy scripts, CI commands, and test modules import ``Backend.app.*``.
On case-sensitive filesystems (Linux CI) and Python's exact-case ``FileFinder``,
``import Backend`` fails unless an alias finder redirects it to ``backend``.

Using a delegating ``types.ModuleType`` proxy instead of assigning
``sys.modules[fullname] = real_mod`` or copying module files ensures:
1. ``backend.*`` modules keep their canonical ``__name__`` and ``__spec__``.
2. Importing via both ``Backend.*`` and ``backend.*`` resolves to the exact
   same module globals and singleton instances (``_stores``, ``review_service``,
   ``security_shield``).
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import types


class _AliasModule(types.ModuleType):
    """Delegating module proxy for ``Backend.* -> backend.*`` imports."""

    def __init__(self, alias_name: str, target_module: types.ModuleType) -> None:
        super().__init__(alias_name)
        object.__setattr__(self, "_target_module", target_module)

    def __getattr__(self, item: str):
        return getattr(object.__getattribute__(self, "_target_module"), item)

    def __setattr__(self, key: str, value) -> None:
        # When Python's import machinery attaches a child ``Backend.*`` proxy to a
        # parent ``Backend.*`` proxy, keep the proxy binding local so the
        # canonical ``backend.*`` package attribute is never replaced with a proxy.
        if isinstance(value, _AliasModule):
            object.__setattr__(self, key, value)
            return
        setattr(object.__getattribute__(self, "_target_module"), key, value)

    def __delattr__(self, item: str) -> None:
        delattr(object.__getattribute__(self, "_target_module"), item)

    def __dir__(self):
        return dir(object.__getattribute__(self, "_target_module"))


class _AliasLoader(importlib.abc.Loader):
    """Loader returning a delegating proxy backed by the canonical ``backend`` module."""

    def __init__(self, alias_name: str, target_module: types.ModuleType) -> None:
        self.alias_name = alias_name
        self.target_module = target_module

    def create_module(self, spec):
        proxy = _AliasModule(self.alias_name, self.target_module)
        if hasattr(self.target_module, "__path__"):
            object.__setattr__(proxy, "__path__", self.target_module.__path__)
        return proxy

    def exec_module(self, module) -> None:
        # Target module was already executed by importlib.import_module(real_name).
        return None


class BackendAliasFinder(importlib.abc.MetaPathFinder):
    """Meta-path finder mapping ``Backend`` and ``Backend.*`` to ``backend.*``."""

    @classmethod
    def find_spec(cls, fullname: str, path=None, target=None):
        if fullname == "Backend" or fullname.startswith("Backend."):
            real_name = "backend" + fullname[len("Backend"):]
            real_mod = importlib.import_module(real_name)
            return importlib.util.spec_from_loader(fullname, _AliasLoader(fullname, real_mod))
        return None


def install_backend_alias() -> bool:
    """Idempotently register :class:`BackendAliasFinder` at the head of ``sys.meta_path``.

    Returns ``True`` if newly installed, ``False`` if already registered.
    """
    for finder in sys.meta_path:
        if type(finder).__name__ == "BackendAliasFinder":
            return False
    sys.meta_path.insert(0, BackendAliasFinder())
    return True
