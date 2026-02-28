"""Module registry for auto-discovery and loading of modules."""

import importlib
import importlib.util
import inspect
import os
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from bot.core.module_base import NexusModule


class ModuleRegistry:
    """Registry for managing all Nexus modules."""

    def __init__(self):
        self._modules: Dict[str, NexusModule] = {}
        self._module_paths: Dict[str, str] = {}

    def discover_modules(self, package_path: str = None) -> List[Type[NexusModule]]:
        """
        Auto-discover all modules in the modules directory.

        Returns:
            List of module classes
        """
        if package_path is None:
            package_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            modules_path = os.path.join(package_path, "modules")
        else:
            modules_path = package_path

        module_classes = []

        # Walk through modules directory
        for importer, modname, ispkg in pkgutil.iter_modules([modules_path]):
            if ispkg:
                try:
                    # Import the module package
                    full_modname = f"bot.modules.{modname}"
                    module = importlib.import_module(full_modname)

                    # Find NexusModule subclasses
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, NexusModule)
                            and obj is not NexusModule
                            and not getattr(obj, "__abstractmethods__", None)
                        ):
                            module_classes.append(obj)
                            self._module_paths[obj.name] = full_modname

                except Exception as e:
                    print(f"Failed to load module {modname}: {e}")

        return module_classes

    def register_module(self, module_class: Type[NexusModule]) -> NexusModule:
        """
        Register a module class.

        Args:
            module_class: The module class to register

        Returns:
            Instance of the module
        """
        instance = module_class()
        self._modules[instance.name] = instance
        return instance

    def unregister_module(self, name: str) -> bool:
        """
        Unregister a module.

        Args:
            name: Name of the module to unregister

        Returns:
            True if unregistered, False if not found
        """
        if name in self._modules:
            del self._modules[name]
            return True
        return False

    def get_module(self, name: str) -> Optional[NexusModule]:
        """
        Get a module by name.

        Args:
            name: Module name

        Returns:
            Module instance or None
        """
        return self._modules.get(name)

    def get_all_modules(self) -> List[NexusModule]:
        """
        Get all registered modules.

        Returns:
            List of module instances
        """
        return list(self._modules.values())

    def get_modules_by_category(self, category: str) -> List[NexusModule]:
        """
        Get modules by category.

        Args:
            category: Category name

        Returns:
            List of module instances in that category
        """
        return [m for m in self._modules.values() if m.category.value == category]

    async def load_all(self, app=None) -> None:
        """
        Discover and load all modules.

        Args:
            app: Application context to pass to modules
        """
        module_classes = self.discover_modules()

        for module_class in module_classes:
            try:
                instance = self.register_module(module_class)
                await instance.on_load(app)
                print(f"Loaded module: {instance.name}")
            except Exception as e:
                print(f"Failed to load module {module_class.__name__}: {e}")

    async def unload_all(self) -> None:
        """Unload all modules."""
        for name, module in list(self._modules.items()):
            try:
                await module.on_unload()
                print(f"Unloaded module: {name}")
            except Exception as e:
                print(f"Error unloading module {name}: {e}")

        self._modules.clear()

    def get_module_info(self) -> List[Dict]:
        """
        Get information about all modules.

        Returns:
            List of module info dictionaries
        """
        return [module.get_info() for module in self._modules.values()]

    def check_dependencies(self) -> Dict[str, List[str]]:
        """
        Check for missing dependencies.

        Returns:
            Dictionary mapping module names to missing dependencies
        """
        missing = {}
        for name, module in self._modules.items():
            deps = module.dependencies
            missing_deps = [d for d in deps if d not in self._modules]
            if missing_deps:
                missing[name] = missing_deps
        return missing

    def check_conflicts(self) -> Dict[str, List[str]]:
        """
        Check for module conflicts.

        Returns:
            Dictionary mapping module names to conflicting modules
        """
        conflicts = {}
        for name, module in self._modules.items():
            for conflict in module.conflicts:
                if conflict in self._modules:
                    if name not in conflicts:
                        conflicts[name] = []
                    conflicts[name].append(conflict)
        return conflicts


# Global registry instance
module_registry = ModuleRegistry()
