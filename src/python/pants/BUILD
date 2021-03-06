# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

target(
  name = 'pants',
  dependencies = [
    'src/python/pants/bin:pants',
  ],
).with_description('An alias for the pants binary target.')


# TODO(John Sirois): Move this to an exposed function - consider
# whether to introduce an un-exported pants-internal backend for
# helpers like this if we don't want to export it to the world.
def read_contents(path):
  import os
  with open(os.path.join(buildfile_path(), path)) as fp:
    return fp.read()


python_library(
  name = 'pants-packaged',
  provides=setup_py(
    name='pantsbuild.pants',
    version=pants_version(),
    description='A bottom-up build tool.',
    long_description=read_contents('ABOUT.rst') + read_contents('CHANGELOG.rst'),
    url='https://github.com/pantsbuild/pants',
    license='Apache License, Version 2.0',
    zip_safe=True,
    namespace_packages=['pants'],
    classifiers=[
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
    ]
  ).with_binaries(
    # TODO(John Sirois): Switch back when target cycles have been sorted out.
    # pants='src/python/pants/bin:pants',
    pants=':_pants_transitional_publishable_binary_',
  )
)

page(name='readme',
  source='README.md',
)

# XXX move into base or thrift
python_library(
  name = 'binary_util',
  sources = ['binary_util.py'],
  dependencies = [
    '3rdparty/python/twitter/commons:twitter.common.collections',
    '3rdparty/python/twitter/commons:twitter.common.lang',
    '3rdparty/python/twitter/commons:twitter.common.log',
    'src/python/pants/base:config',
    'src/python/pants/base:exceptions',
    'src/python/pants/util:contextutil',
    'src/python/pants/util:dirutil',
  ],
)

python_library(
  name = 'thrift_util',
  sources = ['thrift_util.py'],
  dependencies = [
    ':binary_util',
  ],
)

python_library(
  name = 'version',
  sources = ['version.py'],
)
