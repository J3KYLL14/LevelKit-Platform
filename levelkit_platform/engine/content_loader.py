import importlib
import pkgutil
import sys

from .errors import PlainEnglishError, format_syntax_error
from .settings import CONTENT_PACKAGE


def safe_import(module_name):
    try:
        return importlib.import_module(module_name)
    except SyntaxError as err:
        raise format_syntax_error(err) from err
    except ModuleNotFoundError as err:
        raise PlainEnglishError(
            f"Python could not import '{module_name}'.\n"
            f"Plain English: a file or package that this content depends on could not be found.\n"
            f"Technical detail: {err}"
        ) from err
    except Exception as err:
        raise PlainEnglishError(
            f"Something went wrong while loading '{module_name}'.\n"
            f"Plain English: Python hit an error while reading that content file.\n"
            f"Technical detail: {err}"
        ) from err


def load_definitions(package_name, symbol):
    package = safe_import(f"{CONTENT_PACKAGE}.{package_name}")
    definitions = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = safe_import(f"{package.__name__}.{module_info.name}")
        value = getattr(module, symbol, None)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                definitions[item["id"]] = item
        else:
            definitions[value["id"]] = value
    return definitions


def load_dialogue():
    package = safe_import(f"{CONTENT_PACKAGE}.dialogue")
    dialogue = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = safe_import(f"{package.__name__}.{module_info.name}")
        value = getattr(module, "DIALOGUES", {})
        dialogue.update(value)
    return dialogue


def load_event_hooks():
    try:
        import levelkit
    except ModuleNotFoundError:
        return {"pickup": [], "enter_level": []}

    levelkit.clear_event_hooks()
    module_name = f"{CONTENT_PACKAGE}.events"
    try:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
    except ModuleNotFoundError as err:
        if err.name == module_name:
            return {"pickup": [], "enter_level": []}
        raise PlainEnglishError(
            f"Python could not import something used by '{module_name}'.\n"
            f"Plain English: an events file imports a file or package that could not be found.\n"
            f"Technical detail: {err}"
        ) from err
    except SyntaxError as err:
        raise format_syntax_error(err) from err
    except Exception as err:
        raise PlainEnglishError(
            f"Something went wrong while loading '{module_name}'.\n"
            f"Plain English: Python hit an error while reading the event hooks file.\n"
            f"Technical detail: {err}"
        ) from err

    return {key: list(value) for key, value in levelkit.EVENT_HOOKS.items()}


def load_game_config():
    module = safe_import(f"{CONTENT_PACKAGE}.game_config")
    return module.GAME_CONFIG


def load_content_module(module_name):
    return safe_import(f"{CONTENT_PACKAGE}.{module_name}")


def load_levels():
    package = safe_import(f"{CONTENT_PACKAGE}.levels")
    levels = {}
    modules = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = safe_import(f"{package.__name__}.{module_info.name}")
        level_def = module.LEVEL
        levels[level_def["id"]] = level_def
        modules[level_def["id"]] = module
    return levels, modules
