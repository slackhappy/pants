# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import logging

from pants.base.payload import EmptyPayload
from pants.base.target import Target


logger = logging.getLogger(__name__)


class Dependencies(Target):
  """A set of dependencies that may be depended upon,
  as if depending upon the set of dependencies directly.

  NB: This class is commonly referred to by the alias 'target' in BUILD files.
  """

  def __init__(self, *args, **kwargs):
    """
    :param string name: The name of this target, which combined with this
      build file defines the :doc:`target address <target_addresses>`.
    :param dependencies: Other targets that this target depends on.
    :type dependencies: list of target specs
    :param exclusives: An optional map of exclusives tags. See :ref:`howto_check_exclusives`
      for details.
    """
    super(Dependencies, self).__init__(payload=EmptyPayload(), *args, **kwargs)


class DeprecatedDependencies(Dependencies):
  """A subclass for Dependencies that warns that the 'dependencies' alias is deprecated."""
  def __init__(self, *args, **kwargs):
    logger.warn("""For %s : The alias 'dependencies(..)' has been deprecated in favor of 'target(..)'""" % kwargs['address'].spec)
    super(DeprecatedDependencies, self).__init__(*args, **kwargs)
