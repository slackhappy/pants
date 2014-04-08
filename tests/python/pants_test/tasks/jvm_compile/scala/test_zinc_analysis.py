# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import unittest

from twitter.common.contextutil import Timer, temporary_dir, temporary_file_path

from pants.tasks.jvm_compile.scala.zinc_analysis import ZincAnalysis
from pants.tasks.jvm_compile.scala.zinc_analysis_parser import ZincAnalysisParser


class ZincAnalysisTest(unittest.TestCase):
  def setUp(self):
    self.total_time = 0

  def _time(self, work, msg):
    with Timer() as timer:
      ret = work()
    elapsed = timer.elapsed
    print('%s in %f seconds.' % (msg, elapsed))
    self.total_time += elapsed
    return ret

  def test_analysis_files(self):
    # Read in a bunch of analysis files.
    analysis_dir = os.path.join(os.path.dirname(__file__), 'analysis')
    analysis_files = [f for f in os.listdir(analysis_dir) if f.endswith('.analysis')]
    num_analyses = len(analysis_files)
    parser = ZincAnalysisParser('/Users/benjy/src/foursquare.web/.pants.d/scalac/classes/')

    def parse(f):
      inpath = os.path.join(analysis_dir, f)
      print('Parsing: %s' % inpath)
      return parser.parse_from_path(inpath)

    analyses = self._time(lambda: [parse(f) for f in analysis_files],
                          'Parsed %d files' % num_analyses)

    # Write them back out individually.
    with temporary_dir() as tmpdir:
      def write(f, analysis):
        outpath = os.path.join(tmpdir, f)
        print('Writing: %s' % outpath)
        analysis.write_to_path(outpath)

      def _write_all():
        for f, analysis in zip(analysis_files, analyses):
          write(f, analysis)

      self._time(_write_all, 'Wrote %d files' % num_analyses)

    # Merge them.
    merged_analysis = self._time(lambda: ZincAnalysis.merge(analyses),
                                 'Merged %d files' % num_analyses)

    # Write merged analysis to file.
    with temporary_file_path() as merged_analysis_path:
      self._time(lambda: merged_analysis.write_to_path(merged_analysis_path),
                 'Wrote merged analysis to %s' % merged_analysis_path)

      # Read merged analysis from file.
      merged_analysis2 = self._time(lambda: parser.parse_from_path(merged_analysis_path),
                                    'Read merged analysis from %s' % merged_analysis_path)

    # Split the merged analysis back to individual analyses.
    sources_per_analysis = [a.stamps.sources.keys() for a in analyses]
    split_analyses = self._time(lambda: merged_analysis2.split(sources_per_analysis, catchall=True),
                                'Split back into %d analyses' % num_analyses)

    self.assertEquals(num_analyses + 1, len(split_analyses))  # +1 for the catchall.
    catchall_analysis = split_analyses[-1]

    # We expect an empty catchall.
    self.assertEquals(0, len(catchall_analysis.stamps.sources))

    for expected_analysis, split_analysis in zip (analyses, split_analyses):
      diffs = expected_analysis.diff(split_analysis)
      self.assertEquals(expected_analysis, split_analysis, ''.join([unicode(d) for d in diffs]))

    print('Total time: %f seconds' % self.total_time)

    raise Exception('DUMMY')