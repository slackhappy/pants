from twitter.pants.cache.artifact_cache import ArtifactCache


class ReadWriteArtifactCache(ArtifactCache):
  """An artifact cache that delegates to one cache for reading and another for writing.

  The name is slightly misleading: all caches are read-write. But I couldn't think
  of a better one.
  """
  def __init__(self, read_artifact_cache, write_artifact_cache):
    """Either cache can be None, in which case we don't read from/write to it."""
    artifact_root = read_artifact_cache.artifact_root
    if write_artifact_cache.artifact_root != artifact_root:
      raise ValueError('Read and write artifact caches must have the same artifact root.')
    ArtifactCache.__init__(self, read_artifact_cache.log, artifact_root)
    self._read_artifact_cache = read_artifact_cache
    self._write_artifact_cache = write_artifact_cache

  def insert(self, cache_key, paths):
    if self._write_artifact_cache:
      self._write_artifact_cache.insert(cache_key, paths)

  def has(self, cache_key):
    if self._read_artifact_cache:
      return self._read_artifact_cache.has(cache_key)
    else:
      return False

  def use_cached_files(self, cache_key):
    if self._read_artifact_cache:
      return self._read_artifact_cache.use_cached_files(cache_key)
    else:
      return None

  def delete(self, cache_key):
    if self._write_artifact_cache:
      self._write_artifact_cache.delete(cache_key)

  def prune(self, age_hours):
    if self._write_artifact_cache:
      self._write_artifact_cache.prune(age_hours)

