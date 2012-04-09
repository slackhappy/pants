<?xml version="1.0"?>

<!--
=================================================================================================
Copyright 2012 Twitter, Inc.
_________________________________________________________________________________________________
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this work except in compliance with the License.
You may obtain a copy of the License in the LICENSE file, or at:

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
=================================================================================================
-->

<!-- generated by pants! -->
<projectDescription>
  <name>${project.name}</name>
  <comment></comment>
  <projects>
  </projects>
  <buildSpec>
    ## For whatever reason in a mixed scala/java project, the only jvm builder must be the scala
    ## builder circa eclipse 3.6
    % if project.has_scala:
    <buildCommand>
      <name>org.scala-ide.sdt.core.scalabuilder</name>
      <arguments>
      </arguments>
    </buildCommand>
    % else:
    <buildCommand>
      <name>org.eclipse.jdt.core.javabuilder</name>
      <arguments>
      </arguments>
    </buildCommand>
    % endif
    % if project.has_python:
    <buildCommand>
      <name>org.python.pydev.PyDevBuilder</name>
      <arguments>
      </arguments>
    </buildCommand>
    % endif
  </buildSpec>
  <natures>
    % if project.has_scala:
    <nature>org.scala-ide.sdt.core.scalanature</nature>
    % endif
    <nature>org.eclipse.jdt.core.javanature</nature>
    % if project.has_python:
    <nature>org.python.pydev.pythonNature</nature>
    % endif
  </natures>

  % if project.source_bases:
  <linkedResources>
    % for source_base, id in project.source_bases:
    <link>
      <name>${id}</name>
      ## TODO(John Sirois): What does 2 mean? - find out and document.
      <type>2</type>
      <location>${source_base}</location>
    </link>
    % endfor
  </linkedResources>
  % endif

</projectDescription>
