import sublime
import sublime_plugin
import threading
import os
import subprocess


def print_to_outputpane(msg):
    win = sublime.active_window()
    panel = win.create_output_panel("panel")
    panel.run_command("append", {"characters": msg})
    win.run_command('show_panel', {"panel": "output.panel"})


def hide_outputpane():
    win = sublime.active_window()
    win.run_command('hide_panel', {"panel": "output.panel"})


def diff_sanity_check(a, b):
    if a != b:
        raise Exception("diff sanity check mismatch\n-%s\n+%s" % (a, b))


class GotoolsValidateCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        dirname = os.path.dirname(view.file_name())

        thread = threading.Thread(target=self.do_vet, args=(dirname,))
        thread.start()

    def do_vet(self, work_dir):
        try:
            gvt = subprocess.Popen(["go", "vet", "."], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, creationflags=0x08000000, cwd=work_dir)
        except FileNotFoundError:
            print("go not found in PATH")
            return

        sout, serr = gvt.communicate()
        if gvt.returncode != 0:
            print(serr.decode(), end="")
            print_to_outputpane(serr.decode())
            return

        try:
            gln = subprocess.Popen(["golint", "."], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, creationflags=0x08000000, cwd=work_dir)
        except FileNotFoundError:
            print("golint not found in PATH")
            return

        sout, serr = gln.communicate()
        if gln.returncode != 0:
            print(serr.decode(), end="")
            print_to_outputpane(serr.decode())
            return

        newsrc = sout.decode()
        if newsrc != "":
            print_to_outputpane(newsrc)
        else:
            hide_outputpane()
