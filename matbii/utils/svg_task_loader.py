from jinja2 import Template
from collections import defaultdict
import json
import os
from pathlib import Path
from typing import Union, List

from ._error import MatbiiInternalError
from ._const import DEFAULT_SVG_INDEX_FILE, DEFAULT_TASK_PATH, DEFAULT_ENABLED_TASKS
from ._logging import _LOGGER


class MultiTaskLoader:

    def __init__(
        self,
        index_file: str = None,
        task_path: str = None,
        enabled_tasks: List[str] = None,
        index_context_file=None,
        index_context=None,
    ):
        super().__init__()
        self._loaders = dict()
        self._loaders["json"] = MultiTaskLoader.load_json
        self._loaders["svg"] = MultiTaskLoader.load_svg
        self._loaders["svg.jinja"] = self.load_svg_from_template

        self._index_file = MultiTaskLoader.resolve_path(
            index_file if index_file else DEFAULT_SVG_INDEX_FILE
        )
        self._task_path = MultiTaskLoader.resolve_path(
            task_path if task_path else DEFAULT_TASK_PATH
        )
        self._index_context = index_context
        self._index_context_file = index_context_file
        self._tasks = None
        self._enabled_tasks = None
        # do an initial load to fill some of the above variables
        self.load(enabled_tasks=enabled_tasks)

    def load(self, enabled_tasks=None):
        # find and load all tasks in the task path
        self._tasks = self.load_tasks()
        # intialise enabled tasks
        self._enabled_tasks = {task: False for task in self._tasks.keys()}
        if enabled_tasks is None:
            enabled_tasks = DEFAULT_ENABLED_TASKS
        for task in enabled_tasks:
            self.enable_task(task)

        # load the index file that will contain the tasks
        _LOGGER.debug("Loading task index from: %s", self._index_file)
        self._index_context = self._get_index_context(
            self._index_context_file, self._index_context
        )
        _LOGGER.debug("    Tasks enabled: %s", str(list(self._enabled_tasks.keys())))

    def get_index(self):
        # add tasks to the index context if they are enabled
        task_context = {
            task: data
            for task, data in self._tasks.items()
            if self._enabled_tasks[task]
        }
        return Template(MultiTaskLoader.load_svg(self._index_file)).render(
            **self._index_context, **task_context
        )

    def enable_task(self, task):
        if task not in self._tasks:
            raise MatbiiInternalError(
                f"Task: {task} was not found in {list(self._tasks.keys())}"
            )
        self._enabled_tasks[task] = True

    def disable_task(self, task):
        if task not in self._tasks:
            raise MatbiiInternalError(
                f"Task: {task} was not found in {list(self._tasks.keys())}"
            )
        self._enabled_tasks[task] = False

    def __iter__(self):
        yield from self._tasks.items()

    def _load(self, files):
        if "svg" in files:
            assert not "svg.jinja" in files
            return self._loaders["svg"](files["svg"])
        elif "svg.jinja" in files:
            assert not "svg" in files
            assert "json" in files
            return self._loaders["svg.jinja"](files["svg.jinja"], files["json"])

    @staticmethod
    def resolve_path(path: str):
        return str(Path(path).expanduser().resolve())

    @staticmethod
    def get_full_suffix(file: Union[str, Path]):
        if isinstance(file, str):
            file = Path(file)
        return ".".join(file.name.split(".")[1:])

    def _get_index_context(self, index_context_file, index_context):
        if index_context_file:
            index_context_file = Path(MultiTaskLoader.resolve_path(index_context_file))
            suffix = MultiTaskLoader.get_full_suffix(index_context_file)
            # cannot provide both... TODO proper error message
            assert index_context is None
            index_context = self._loaders[suffix](str(index_context_file))
        if index_context is None:
            index_context = dict()

        return index_context

    def load_tasks(self):
        _LOGGER.debug("Loading matbii tasks from: `%s`", self._task_path)
        _task_files = MultiTaskLoader.get_task_files(
            self._task_path,
        )
        tasks = dict()
        for name, files in _task_files.items():
            _LOGGER.debug("Loading files for task: `%s`", name)
            tasks[name] = self._load(files)
        return tasks

    @staticmethod
    def load_json(path):
        with open(path, "r", encoding="UTF-8") as json_file:
            return json.load(json_file)

    @staticmethod
    def load_svg(path):
        with open(path, "r", encoding="UTF-8") as svg_file:
            return svg_file.read()

    def load_svg_from_template(self, file, context_file):
        # current only json is supported
        assert context_file.endswith("json")
        template_context = self._loaders["json"](context_file)
        template = self._loaders["svg"](file)

        template = Template(template)
        return template.render(**template_context)

    @staticmethod
    def get_task_files(task_directory):

        # TODO use pathlib instead of os?
        # A dictionary to hold lists of files with the same name but different extensions
        files_grouped = defaultdict(dict)
        for entry in os.listdir(task_directory):
            full_path = os.path.join(task_directory, entry)
            if os.path.isfile(full_path):
                file_name, *file_extension = entry.split(".")
                file_extension = ".".join(file_extension)
                files_grouped[file_name][file_extension] = full_path
        return files_grouped

    # @staticmethod
    # def load_xml_template(template_path, template_data=None, template_data_path=None):
    #     if template_data is None:
    #         if template_data_path is None:
    #             raise MatbiiInternalError(
    #                 "One of `template_data` or `template_data_path` must be specified."
    #             )
    #         with open(template_data_path, "r", encoding="UTF-8") as json_file:
    #             template_data = json.load(json_file)

    #     with open(template_path, "r", encoding="UTF-8") as svg_file:
    #         template = svg_file.read()

    #     template = Template(template)
    #     return template.render(**template_data)
