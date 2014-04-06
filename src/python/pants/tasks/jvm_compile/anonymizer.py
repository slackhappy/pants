# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import random
import re


_default_keep = [
  'com',
  'src',
  'home',
  'Users',
  'java',
  'javac',
  'scala',
  'scalac',
  'class',
  'classes',
  'anonfun',
  'apply',
  'unapply',
  'pants',
  'd',
  'jars',
  'jar'
]

# TODO: Move somewhere more general? Could also be used to anonymize source files.

class Anonymizer(object):
  """Anonymizes names in analysis files.

  Will replace all words in word_map with the corresponding value.

  Will replace all other words with a random word from word_list, except for
  words in keep.

  Useful for obfuscating real-life analysis files so we can use them in tests without
  leaking proprietary information.
  """
  # Break on delimiters (digits, space, forward slash, dollar, period) and on
  # upper-case letters.
  _DELIMITER = r'\d|\s|/|\$|\.'
  _UPPER = r'[A-Z]'
  _UPPER_CASE_RE = re.compile(r'^%s$' % _UPPER)
  _DELIMITER_RE = re.compile(r'^%s$' % _DELIMITER)
  _BREAK_ON_RE = re.compile(r'(%s|%s)' % (_DELIMITER, _UPPER))  # Capture what we broke on.

  # Valid replacement words must be all lower-case letters, with no apostrophes etc.
  _WORD_RE = re.compile(r'^[a-z]+$')

  def __init__(self, word_map, word_list, keep=None):
    self._conversions = dict(word_map)
    for w in _default_keep if keep is None else keep:
      self._conversions[w] = w
    self._unused_words = list(set(filter(lambda s: Anonymizer._WORD_RE.match(s), word_list)))
    random.shuffle(self._unused_words)

  def convert(self, s):
    parts = Anonymizer._BREAK_ON_RE.split(s)
    parts_iter = iter(parts)
    converted_parts = []
    for p in parts_iter:
      if p == '' or Anonymizer._DELIMITER_RE.match(p):
        converted_parts.append(p)
      elif Anonymizer._UPPER_CASE_RE.match(p):
        # Join to the rest of the word, if any.
        x = p
        try:
          x += parts_iter.next()
        except StopIteration:
          pass
        converted_parts.append(self._convert_single_token(x))
      else:
        converted_parts.append(self._convert_single_token(p))
    return ''.join(converted_parts)

  def _convert_single_token(self, s):
    lower = s.lower()
    word = self._conversions.get(lower)
    if word is None:
      if not self._unused_words:
        raise Exception('Ran out of replacement words!')
      word = self._unused_words.pop()
      self._conversions[s] = word
    # Use the same capitalization as the original word.
    if s[0].isupper():
      return word.capitalize()
    else:
      return word
