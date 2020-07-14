import sublime
import sublime_plugin
import subprocess
import difflib
import threading
import os


def diff_sanity_check(a, b):
    if a != b:
        raise Exception("diff sanity check mismatch\n-%s\n+%s" % (a, b))


class GotoolsTagCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view

        offset = view.sel()[0].a
        src = view.substr(sublime.Region(0, view.size()))

        dirname, filename = os.path.dirname(
            view.file_name()), os.path.basename(view.file_name())

        gofmt = subprocess.Popen(["gomodifytags", "-file", filename, "-offset", str(offset), "-transform", "snakecase", "-add-tags", "json", "-add-options",
                                  "json=omitempty"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000, cwd=dirname)
        sout, serr = gofmt.communicate(src.encode())

        if gofmt.returncode != 0:
            print(serr.decode(), end="")
            return

        newsrc = sout.decode()
        # print(newsrc)

        diff = difflib.ndiff(src.splitlines(), newsrc.splitlines())
        i = 0
        for line in diff:
            if line.startswith("?"):  # skip hint lines
                continue

            l = (len(line)-2)+1
            if line.startswith("-"):
                diff_sanity_check(view.substr(
                    sublime.Region(i, i+l-1)), line[2:])
                view.erase(edit, sublime.Region(i, i+l))
            elif line.startswith("+"):
                view.insert(edit, i, line[2:]+"\n")
                i += l
            else:
                diff_sanity_check(view.substr(
                    sublime.Region(i, i+l-1)), line[2:])
                i += l


class GotoolsRenameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        view.window().show_input_panel("New name", "",
                                       lambda x: self.rename_thread(view, x), None, None)

    def rename_thread(self, view, name):
        thread = threading.Thread(target=self.do_rename, args=(view, name))
        thread.start()

    def do_rename(self, view, name):
        src = view.substr(sublime.Region(0, view.size()))

        filename, dirname = os.path.basename(
            view.file_name()), os.path.dirname(view.file_name())
        offset = view.sel()[0].a

        gofmt = subprocess.Popen(["gorename", "-offset", "{}:#{}".format(filename, offset), "-to", name],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000, cwd=dirname)
        sout, serr = gofmt.communicate(src.encode())

        if gofmt.returncode != 0:
            print(serr.decode(), end="")
            return

        newsrc = sout.decode()
        diff = difflib.ndiff(src.splitlines(), newsrc.splitlines())
        i = 0
        for line in diff:
            if line.startswith("?"):  # skip hint lines
                continue

            l = (len(line)-2)+1
            if line.startswith("-"):
                diff_sanity_check(view.substr(
                    sublime.Region(i, i+l-1)), line[2:])
                view.erase(edit, sublime.Region(i, i+l))
            elif line.startswith("+"):
                view.insert(edit, i, line[2:]+"\n")
                i += l
            else:
                diff_sanity_check(view.substr(
                    sublime.Region(i, i+l-1)), line[2:])
                i += l
