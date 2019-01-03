import os
import shutil
from collections import defaultdict, namedtuple
from itertools import groupby

from .config import COLORS_DIR, USER_COLORS_DIR
from .helpers import ls_r, mkdir_p


PresetFile = namedtuple('PresetFile', ['name', 'path', 'default', 'is_saveable', ])


def get_theme_name_and_plugin(theme_path, colors_dir, plugin):
    from .plugin_api import PLUGIN_PATH_PREFIX
    from .plugin_loader import IMPORT_PLUGINS

    display_name = "".join(
        theme_path.rsplit(colors_dir)
    ).lstrip('/')

    rel_path = "".join(theme_path.rsplit(colors_dir))
    if not plugin and rel_path.startswith(PLUGIN_PATH_PREFIX):
        plugin_name = rel_path.split(PLUGIN_PATH_PREFIX)[1].split('/')[0]
        plugin = IMPORT_PLUGINS.get(plugin_name)
    if plugin:
        for ext in plugin.file_extensions:
            if display_name.endswith(ext):
                display_name = display_name[:-len(ext)]
                break
    return display_name, plugin


def get_presets():
    from .plugin_loader import IMPORT_PLUGINS

    def _get_sorter(colors_dir):
        return lambda x: ''.join(x.path.rsplit(colors_dir)).split('/')[0]

    all_results = {}
    for colors_dir, is_default, plugin in [
            (COLORS_DIR, True, None),
            (USER_COLORS_DIR, False, None),
    ] + [
        (plugin.plugin_theme_dir, True, plugin)
        for plugin in IMPORT_PLUGINS.values()
        if plugin.plugin_theme_dir
    ]:
        file_paths = []
        for path in ls_r(colors_dir):
            display_name, plugin = get_theme_name_and_plugin(
                path, colors_dir, plugin
            )
            file_paths.append(PresetFile(
                name=display_name,
                path=os.path.abspath(path),
                default=is_default or plugin,
                is_saveable=not is_default and not plugin,
            ))
        result = defaultdict(list)
        for dir_name, group in groupby(file_paths, _get_sorter(colors_dir)):
            result[dir_name] = sorted(list(group), key=lambda x: x.name)
        all_results[colors_dir] = dict(result)
    return all_results


def get_user_theme_path(user_theme_name):
    return os.path.join(USER_COLORS_DIR, user_theme_name.lstrip('/'))


def save_colorscheme(preset_name, colorscheme, path=None):
    colorscheme["NAME"] = preset_name
    path = path or get_user_theme_path(preset_name)
    if not os.path.exists(path):
        mkdir_p(os.path.dirname(path))
    with open(path, 'w') as file_object:
        for key, value in sorted(colorscheme.items()):
            if (
                    key not in ('NOGUI', )
            ) and (
                not key.startswith('_')
            ) and (
                value is not None
            ):
                file_object.write("{}={}\n".format(
                    key, value
                ))
    return path


def import_colorscheme(preset_name, import_path):
    new_path = get_user_theme_path(preset_name)
    if not os.path.exists(new_path):
        mkdir_p(os.path.dirname(new_path))
    shutil.copy(import_path, new_path)
    return new_path


def remove_colorscheme(preset_name):
    path = os.path.join(USER_COLORS_DIR, preset_name)
    os.remove(path)


def is_user_colorscheme(preset_path):
    return preset_path.startswith(USER_COLORS_DIR)


def is_colorscheme_exists(preset_path):
    return os.path.exists(preset_path)
