"""One rule for every file this program writes:

    build the new version in a temp file, then swap it into place.

If the destination is open in Excel / Acrobat / a browser (Windows file lock),
the swap is skipped, the PREVIOUS version stays intact, and the user gets one
plain-language line telling them which file to close — the rest of the run
continues. Nothing ever half-writes or crashes on a locked file.
"""
import os


def write_via_temp(path, writer, say=None, what=None):
    """writer(tmp_path) must create the file at tmp_path.
    Returns True if `path` was updated, False if it was locked."""
    what = what or os.path.basename(path)
    say = say or (lambda m: None)
    root, ext = os.path.splitext(path)
    tmp = root + '.new' + ext          # keeps a valid extension for tools that need one
    try:
        writer(tmp)
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise
    try:
        os.replace(tmp, path)
        return True
    except PermissionError:
        try: os.remove(tmp)
        except OSError: pass
        say('%s NOT updated: the file is open in another program. '
            'Close it and click Generate again.' % what)
        return False


def write_text(path, text, say=None, what=None, encoding='utf-8', newline=None):
    def w(tmp):
        with open(tmp, 'w', encoding=encoding, newline=newline) as f:
            f.write(text)
    return write_via_temp(path, w, say, what)


def copy_file(src, dst, say=None, what=None):
    import shutil
    return write_via_temp(dst, lambda tmp: shutil.copyfile(src, tmp), say, what)
