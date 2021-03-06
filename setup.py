from build.commands.installs import InstallExternals
from build.commands.help import Help
import glob
import os
from setuptools import find_packages, setup
import shutil

setup(name='FitBenchmarking',
      version='0.1.dev2',
      description='FitBenchmarking software',
      author='FitBenchmarking Team',
      url='http://github.com/fitbenchmarking/fitbenchmarking',
      license='GPL-3.0',
      entry_points={
          "console_scripts": [
              'fitbenchmarking = fitbenchmarking.cli.main:main'
          ]
      },
      packages=find_packages(exclude=('*mock*', '*test*')),
      install_requires=['docutils',
                        'numpy<1.17',
                        'matplotlib<3.0',
                        'scipy>=0.18,<1.3',
                        'bumps',
                        'sasmodels',
                        'lxml',
                        'pandas<=0.24.2',
                        'jinja2',
                        'dfogn',
                        'DFO-LS',
                        'iminuit',
                        'configparser',
                        'jinja2'],
      zip_safe=False,

      cmdclass={
          'externals': InstallExternals,
          'help': Help,
      },
      package_data={'fitbenchmarking': ['utils/default_options.ini',
                                        'templates/*']}
      )


# Clean up build files
CLEAN_FILES = ['./dist', './*.pyc', './*.tgz', './lib/*.egg-info']
CURDIR = os.path.abspath(os.curdir)

for path_spec in CLEAN_FILES:
    # Make paths absolute and relative to this path
    abs_paths = glob.glob(os.path.normpath(os.path.join(CURDIR, path_spec)))
    for path in [str(p) for p in abs_paths]:
        if not path.startswith(CURDIR):
            # Die if path in CLEAN_FILES is absolute + outside this directory
            raise ValueError("%s is not a path inside %s" % (path, CURDIR))
        print('removing %s' % os.path.relpath(path))
        shutil.rmtree(path)
