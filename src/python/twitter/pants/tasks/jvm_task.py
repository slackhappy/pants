# ==================================================================================================
# Copyright 2012 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

__author__ = 'John Sirois'

import os

from twitter.pants import get_buildroot, is_jvm, is_test
from twitter.pants.tasks import Task


class JvmTask(Task):
  def classpath(self, cp=None, confs=None):
    classpath = cp or []
    with self.context.state('classpath', []) as cp:
      classpath.extend(path for conf, path in cp if not confs or conf in confs)

    def add_resource_paths(predicate):
      bases = set()
      for target in self.context.targets():
        if predicate(target):
          if target.target_base not in bases:
            sibling_resources_base = os.path.join(os.path.dirname(target.target_base), 'resources')
            classpath.append(os.path.join(get_buildroot(), sibling_resources_base))
            bases.add(target.target_base)

    if self.context.config.getbool('jvm', 'parallel_src_paths', default=False):
      add_resource_paths(lambda t: is_jvm(t) and not is_test(t))

    if self.context.config.getbool('jvm', 'parallel_test_paths', default=False):
      add_resource_paths(lambda t: is_jvm(t) and is_test(t))

    return classpath
