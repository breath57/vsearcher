from pathlib import Path
from app.libs.exception import NotFound
from .config.path import RootPath

from .core.video import Assember, DelAnd2Pickle, Video, Chapter, Course, Searcher
from .core import vo


class VSearcher:

    def __init__(self):
        # 模仿学习那种参数
        # self.config = Config()
        pass

    def __init_path(self):
        pass

    @classmethod
    def set_output_dir(cls, relative_project_dir_path):
        RootPath.set_output_dir(relative_project_dir_path)

    @classmethod
    def set_url_prefix_local_path(cls, relative_project_dir_path):
        """ 设置URL替换前缀路径
        例如：
            project_dir: E://a/b/project_dir
            img_local_path: E://a/b/project_dir/x/ff/ss/c.png
            relative_project_dir_path: x
            url_prefix_local_path: {project_dir}/x
            url: http://localhost:5000/ff/ss/c.png
        """
        RootPath.set_url_prefix_local_path(relative_project_dir_path)

    @classmethod
    def set_step(cls, step, speed_x):
        Assember.set_step(step=step, speed_x=speed_x)

    @classmethod
    def executeVideo(cls, video_file_path) -> vo.VideoVO:
        video = Assember.executeVideo(video_path=video_file_path)
        return vo.VideoVO.create(video=video)

    @classmethod
    def executeChapter(cls, chapter_dir_path) -> vo.ChapterVO:
        chapter = Assember.executeChapter(chapter_dir_path=chapter_dir_path)
        return vo.ChapterVO.create(chapter)

    @classmethod
    def executeCourse(cls, course_dir_path) -> vo.CourseVO:
        course = Assember.executeCourse(course_dir_path=course_dir_path)
        return vo.CourseVO.create(course)

    @classmethod
    def loadResource(cls, o_path):
        if not Path(o_path).exists():
            raise NotFound('o_path对象不存在!')
        o = DelAnd2Pickle.loadPickle(o_path)
        if isinstance(o, Video):
            return vo.VideoVO.create(o)
        elif isinstance(o, Chapter):
            return vo.ChapterVO.create(o)
        elif isinstance(o, Course):
            return vo.CourseVO.create(o)

    @classmethod
    def releaseResource(cls, o_path):
        """ 释放o_path对应的pickle对象对应的所有存储资源 """
        o = DelAnd2Pickle.loadPickle(o_path=o_path)
        o.releaseResource()

    @classmethod
    def search(cls, o_or_path, key):
        return Searcher(o_or_path=o_or_path).search(key)


# class Config(dict):
#     """Works exactly like a dict but provides ways to fill it from files
#     or special dictionaries.  There are two common patterns to populate the
#     config.
#
#     Either you can fill the config from a config file::
#
#         app.config.from_pyfile('yourconfig.cfg')
#
#     Or alternatively you can define the configuration options in the
#     module that calls :meth:`from_object` or provide an import path to
#     a module that should be loaded.  It is also possible to tell it to
#     use the same module and with that provide the configuration values
#     just before the call::
#
#         DEBUG = True
#         SECRET_KEY = 'development key'
#         app.config.from_object(__name__)
#
#     In both cases (loading from any Python file or loading from modules),
#     only uppercase keys are added to the config.  This makes it possible to use
#     lowercase values in the config file for temporary values that are not added
#     to the config or to define the config keys in the same file that implements
#     the application.
#
#     Probably the most interesting way to load configurations is from an
#     environment variable pointing to a file::
#
#         app.config.from_envvar('YOURAPPLICATION_SETTINGS')
#
#     In this case before launching the application you have to set this
#     environment variable to the file you want to use.  On Linux and OS X
#     use the export statement::
#
#         export YOURAPPLICATION_SETTINGS='/path/to/config/file'
#
#     On windows use `set` instead.
#
#     :param root_path: path to which files are read relative from.  When the
#                       config object is created by the application, this is
#                       the application's :attr:`~flask.Flask.root_path`.
#     :param defaults: an optional dictionary of default values
#     """
#
#     def __init__(self, root_path: str, defaults: Optional[dict] = None) -> None:
#         dict.__init__(self, defaults or {})
#         self.root_path = root_path
#
#     @staticmethod
#     def import_string(import_name: str, silent: bool = False) -> Any:
#         """Imports an object based on a string.  This is useful if you want to
#         use import paths as endpoints or something similar.  An import path can
#         be specified either in dotted notation (``xml.sax.saxutils.escape``)
#         or with a colon as object delimiter (``xml.sax.saxutils:escape``).
#
#         If `silent` is True the return value will be `None` if the import fails.
#
#         :param import_name: the dotted name for the object to import.
#         :param silent: if set to `True` import errors are ignored and
#                        `None` is returned instead.
#         :return: imported object
#         """
#         import_name = import_name.replace( ":", "." )
#         try:
#             try:
#                 __import__( import_name )
#             except ImportError:
#                 if "." not in import_name:
#                     raise
#             else:
#                 return sys.modules[import_name]
#
#             module_name, obj_name = import_name.rsplit( ".", 1 )
#             module = __import__( module_name, globals(), locals(), [obj_name] )
#             try:
#                 return getattr( module, obj_name )
#             except AttributeError as e:
#                 raise ImportError( e ) from None
#
#         except ImportError as e:
#             if not silent:
#                 raise ImportStringError( import_name, e ).with_traceback(
#                     sys.exc_info()[2]
#                 ) from None
#
#         return None
#     def from_object(self, obj: Union[object, str]) -> None:
#         """Updates the values from the given object.  An object can be of one
#         of the following two types:
#
#         -   a string: in this case the object with that name will be imported
#         -   an actual object reference: that object is used directly
#
#         Objects are usually either modules or classes. :meth:`from_object`
#         loads only the uppercase attributes of the module/class. A ``dict``
#         object will not work with :meth:`from_object` because the keys of a
#         ``dict`` are not attributes of the ``dict`` class.
#
#         Example of module-based configuration::
#
#             app.config.from_object('yourapplication.default_config')
#             from yourapplication import default_config
#             app.config.from_object(default_config)
#
#         Nothing is done to the object before loading. If the object is a
#         class and has ``@property`` attributes, it needs to be
#         instantiated before being passed to this method.
#
#         You should not use this function to load the actual configuration but
#         rather configuration defaults.  The actual config should be loaded
#         with :meth:`from_pyfile` and ideally from a location not within the
#         package because the package might be installed system wide.
#
#         See :ref:`config-dev-prod` for an example of class-based configuration
#         using :meth:`from_object`.
#
#         :param obj: an import name or object
#         """
#         if isinstance(obj, str):
#             obj = self.import_string(obj)
#         for key in dir(obj):
#             if key.isupper():
#                 self[key] = getattr(obj, key)
#
#     def __repr__(self) -> str:
#         return f"<{type(self).__name__} {dict.__repr__(self)}>"
