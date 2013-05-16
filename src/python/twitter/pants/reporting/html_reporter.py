import cgi
import operator
import os
import re
import urlparse
import uuid
from pystache.renderer import Renderer

from twitter.common.dirutil import safe_mkdir
from twitter.pants import get_buildroot
from twitter.pants.base.mustache import MustacheRenderer
from twitter.pants.goal.workunit import WorkUnit
from twitter.pants.reporting.linkify import linkify
from twitter.pants.reporting.reporter import Reporter
from twitter.pants.reporting.reporting_utils import items_to_report_element


class HtmlReporter(Reporter):
  """HTML reporting to files.

  The files are intended to be served by the ReportingServer,
  not accessed directly from the filesystem.
  """

  def __init__(self, run_tracker, html_dir, template_dir):
    Reporter.__init__(self, run_tracker)
     # The main report, and associated tool outputs, go under this dir.
    self._html_dir = html_dir

    # We render HTML from mustache templates.
    self._renderer = MustacheRenderer(Renderer(search_dirs=template_dir))

    # We serve files relative to the build root.
    self._buildroot = get_buildroot()
    self._html_path_base = os.path.relpath(self._html_dir, self._buildroot)

    # We write the main report body to this file object.
    self._report_file = None

    # We redirect stdout, stderr etc. of tool invocations to these files.
    self._output_files = {}  # path -> fileobj.

  def report_path(self):
    """The path to the main report file."""
    return os.path.join(self._html_dir, 'build.html')

  def open(self):
    """Implementation of Reporter callback."""
    safe_mkdir(os.path.dirname(self._html_dir))
    self._report_file = open(self.report_path(), 'w')

  def close(self):
    """Implementation of Reporter callback."""
    self._report_file.close()
    for f in self._output_files.values():
      f.close()

  def start_workunit(self, workunit):
    """Implementation of Reporter callback."""
    # We use these properties of the workunit to decide how to render information about it.
    is_tool = workunit.has_label(WorkUnit.TOOL)
    is_multitool = workunit.has_label(WorkUnit.MULTITOOL)
    is_test = workunit.has_label(WorkUnit.TEST)

    # Get useful properties from the workunit.
    workunit_dict = workunit.to_dict()
    if workunit_dict['cmd']:
      workunit_dict['cmd'] = linkify(self._buildroot, workunit_dict['cmd'].replace('$', '\\\\$'))

    # Create the template arguments.
    args = { 'indent': len(workunit.ancestors()) * 10,
             'html_path_base': self._html_path_base,
             'workunit': workunit_dict,
             'header_text': workunit.name,
             'initially_open': is_test or not (is_tool or is_multitool),
             'is_tool': is_tool,
             'is_multitool': is_multitool }
    args.update({ 'collapsible': lambda x: self._render_callable('collapsible', x, args) })

    # Render the workunit's div.
    s = self._renderer.render_name('workunit_start', args)

    if is_tool:
      # This workunit is a tool invocation, so render the appropriate content.
      # We use the same args, slightly modified.
      del args['initially_open']
      if is_test:
        # Have test framework stdout open by default, but not that of other tools.
        # This is an arbitrary choice, but one that turns out to be useful to users in practice.
        args['stdout_initially_open'] = True
      s += self._renderer.render_name('tool_invocation_start', args)

    # ... and we're done.
    self._emit(s)

  # CSS classes from pants.css that we use to style the header text to reflect the outcome.
  _outcome_css_classes = ['aborted', 'failure', 'warning', 'success', 'unknown']

  def end_workunit(self, workunit):
    """Implementation of Reporter callback."""
    # Create the template arguments.
    duration = workunit.duration()
    timing = '%.3f' % duration
    unaccounted_time_secs = workunit.unaccounted_time()
    unaccounted_time = '%.3f' % unaccounted_time_secs \
      if unaccounted_time_secs >= 1 and unaccounted_time_secs > 0.05 * duration \
      else None
    args = { 'workunit': workunit.to_dict(),
             'status': workunit.choose(*HtmlReporter._outcome_css_classes),
             'timing': timing,
             'unaccounted_time': unaccounted_time,
             'aborted': workunit.outcome() == WorkUnit.ABORTED }

    s = ''
    if workunit.has_label(WorkUnit.TOOL):
      s += self._renderer.render_name('tool_invocation_end', args)
    s += self._renderer.render_name('workunit_end', args)
    self._emit(s)

    # Update the timings.
    def render_timings(timings):
      timings_dict = timings.get_all()
      for item in timings_dict:
        item['timing_string'] = '%.3f' % item['timing']
      args = {
        'timings': timings_dict
      }
      return self._renderer.render_name('aggregated_timings', args)

    self._overwrite('cumulative_timings', render_timings(self.run_tracker.cumulative_timings))
    self._overwrite('self_timings', render_timings(self.run_tracker.self_timings))

    # Update the artifact cache stats.
    def render_cache_stats(artifact_cache_stats):
      def fix_detail_id(e, _id):
        return e if isinstance(e, basestring) else e + (_id, )

      msg_elements = []
      for cache_name, stat in artifact_cache_stats.stats_per_cache.items():
        msg_elements.extend([
          cache_name + ' artifact cache: ',
          # Explicitly set the detail ids, so their displayed/hidden state survives a refresh.
          fix_detail_id(items_to_report_element(stat.hit_targets, 'hit'), 'cache-hit-details'),
          ', ',
          fix_detail_id(items_to_report_element(stat.miss_targets, 'miss'), 'cache-miss-details'),
          '.'
        ])
      if not msg_elements:
        msg_elements = ['No artifact cache use.']
      return self._render_message(*msg_elements)

    self._overwrite('artifact_cache_stats',
                    render_cache_stats(self.run_tracker.artifact_cache_stats))

  def handle_output(self, workunit, label, s):
    """Implementation of Reporter callback."""
    if os.path.exists(self._html_dir):  # Make sure we're not immediately after a clean-all.
      path = os.path.join(self._html_dir, '%s.%s' % (workunit.id, label))
      if path not in self._output_files:
        f = open(path, 'w')
        self._output_files[path] = f
      else:
        f = self._output_files[path]
      f.write(self._htmlify_text(s))
      # We must flush in the same thread as the write.
      f.flush()

  def handle_message(self, workunit, *msg_elements):
    """Implementation of Reporter callback."""
    content = self._render_message(*msg_elements)

    # Generate some javascript that appends the content to the workunit's div.
    args = {
      'content_id': uuid.uuid4(),  # Identifies this content.
      'workunit_id': workunit.id,  # The workunit this reporting content belongs to.
      'content': content,  # The content to append.
      }
    s = self._renderer.render_name('append_to_workunit', args)

    # Emit that javascript to the main report body.
    self._emit(s)

  def _render_message(self, *msg_elements):
    elements = []
    detail_ids = []
    for element in msg_elements:
      # Each element can be a message or a (message, detail) pair, as received by handle_message().
      #
      # However, as an internal implementation detail, we also allow an element to be a tuple
      # (message, detail, detail_initially_visible[, detail_id])
      #
      # - If the detail exists, clicking on the text will toggle display of the detail and close
      #   all other details in this message.
      # - If detail_initially_visible is True, the detail will be displayed by default.
      #
      # Toggling is managed via detail_ids: when clicking on a detail, it closes all details
      # in this message with detail_ids different than that of the one being clicked on.
      # We allow detail_id to be explicitly specified, so that the open/closed state can be
      # preserved through refreshes. For example, when looking at the artifact cache stats,
      # if "hits" are open and "misses" are closed, we want to remember that even after
      # the cache stats are updated and the message re-rendered.
      if isinstance(element, basestring):
        element = [element]
      defaults = ('', None, None, False)
      # Map assumes None for missing values, so this will pick the default for those.
      (text, detail, detail_id, detail_initially_visible) = map(operator.or_, element, defaults)
      element_args = {'text': self._htmlify_text(text) }
      if detail is not None:
        detail_id = detail_id or uuid.uuid4()
        detail_ids.append(detail_id)
        element_args.update({
          'detail': self._htmlify_text(detail),
          'detail_initially_visible': detail_initially_visible,
          'detail-id': detail_id
        })
      elements.append(element_args)
    args = { 'elements': elements,
             'all-detail-ids': detail_ids }
    return self._renderer.render_name('message', args)

  def _emit(self, s):
    """Append content to the main report file."""
    if os.path.exists(self._html_dir):  # Make sure we're not immediately after a clean-all.
      self._report_file.write(s)
      self._report_file.flush()  # We must flush in the same thread as the write.

  def _overwrite(self, filename, s):
    """Overwrite a file with the specified contents."""
    if os.path.exists(self._html_dir):  # Make sure we're not immediately after a clean-all.
      with open(os.path.join(self._html_dir, filename), 'w') as f:
        f.write(s)

  def _render_callable(self, inner_template_name, arg_string, outer_args):
    """Handle a mustache callable.

    In a mustache template, when foo is callable, {{#foo}}arg_string{{/foo}} is replaced with the
    result of calling foo(arg_string). The callable must interpret arg_string.

    This method provides an implementation of such a callable that does the following:
      A) Parses the arg_string as CGI args.
      B) Adds them to the original args that the enclosing template was rendered with.
      C) Renders some other template against those args.
      D) Returns the resulting text.
    """
    # First render the arg_string (mustache doesn't do this for you).
    rendered_arg_string = self._renderer.render(arg_string, outer_args)
    # Parse the inner args as CGI args.
    inner_args = dict([(k, v[0]) for k, v in urlparse.parse_qs(rendered_arg_string).items()])
    # Order matters: lets the inner args override the outer args.
    args = dict(outer_args.items() + inner_args.items())
    # Render.
    return self._renderer.render_name(inner_template_name, args)

  def _htmlify_text(self, s):
    """Make text HTML-friendly."""
    colored = self._handle_ansi_color_codes(cgi.escape(str(s)))
    return linkify(self._buildroot, colored).replace('\n', '</br>')

  _ANSI_COLOR_CODE_RE = re.compile(r'\033\[((\d|;)*)m')
  def _handle_ansi_color_codes(self, s):
    """Replace ansi color sequences with spans of appropriately named css classes."""
    def ansi_code_to_css(code):
      return ' '.join(['ansi-%s' % c for c in code.split(';')])
    return '<span>' +\
           HtmlReporter._ANSI_COLOR_CODE_RE.sub(
             lambda m: '</span><span class="%s">' % ansi_code_to_css(m.group(1)), s) +\
           '</span>'
