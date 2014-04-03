// Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
// Licensed under the Apache License, Version 2.0 (see LICENSE).

namespace java com.pants.examples.distance.thriftjava
namespace py com.pants.examples.distance

/**
 * Structure for expressing distance measures: 8mm, 12 parsecs, etc.
 * Not so useful on its own.
 */
struct Distance {
  1: optional string Unit;
  2: required i64 Number;
}