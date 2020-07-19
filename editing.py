import sublime
import sublime_plugin
import subprocess
import difflib
import threading
import os
import time
import socket
import json

# go to balanced pair, e.g.:
# ((abc(def)))
# ^
# \--------->^
#
# returns -1 on failure


def skip_to_balanced_pair(str, i, open, close):
    count = 1
    i += 1
    while i < len(str):
        if str[i] == open:
            count += 1
        elif str[i] == close:
            count -= 1

        if count == 0:
            break
        i += 1
    if i >= len(str):
        return -1
    return i

# split balanced parens string using comma as separator
# e.g.: "ab, (1, 2), cd" -> ["ab", "(1, 2)", "cd"]
# filters out empty strings


def split_balanced(s):
    out = []
    i = 0
    beg = 0
    while i < len(s):
        if s[i] == ',':
            out.append(s[beg:i].strip())
            beg = i+1
            i += 1
        elif s[i] == '(':
            i = skip_to_balanced_pair(s, i, "(", ")")
            if i == -1:
                i = len(s)
        else:
            i += 1

    out.append(s[beg:i].strip())
    return list(filter(bool, out))


def extract_arguments_and_returns(sig):
    sig = sig.strip()
    if not sig.startswith("func"):
        return [], []

    # find first pair of parens, these are arguments
    beg = sig.find("(")
    if beg == -1:
        return [], []
    end = skip_to_balanced_pair(sig, beg, "(", ")")
    if end == -1:
        return [], []
    args = split_balanced(sig[beg+1:end])

    # find the rest of the string, these are returns
    sig = sig[end+1:].strip()
    sig = sig[1:-1] if sig.startswith("(") and sig.endswith(")") else sig
    returns = split_balanced(sig)

    return args, returns

# takes gocode's candidate and returns sublime's hint and subj


def hint_and_subj(cls, name, type):
    subj = name
    if cls == "func":
        hint = cls + " " + name
        args, returns = extract_arguments_and_returns(type)
        if returns:
            hint += "\t" + ", ".join(returns)
        if args:
            sargs = []
            for i, a in enumerate(args):
                ea = a.replace("{", "\\{").replace("}", "\\}")
                sargs.append("${{{0}:{1}}}".format(i+1, ea))
            subj += "(" + ", ".join(sargs) + ")"
        else:
            subj += "()"
    else:
        hint = cls + " " + name + "\t" + type
    return hint, subj


def diff_sanity_check(a, b):
    if a != b:
        raise Exception("diff sanity check mismatch\n-%s\n+%s" % (a, b))


class GotoolsFmtCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        src = view.substr(sublime.Region(0, view.size()))
        try:
            gofmt = subprocess.Popen(["goreturns"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
        except FileNotFoundError:
            print("goreturns not found in PATH")
            return

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


class Gocode(sublime_plugin.EventListener):
    """Sublime Text gocode integration."""

    def __init__(self):
        self.completions = None
        self.gocode_active = False

    def fetch_query_completions(self, view, prefix, location):
        """Fetches the query completions of for the given location

        Execute gocode and parse the returned csv. Once the results are generated
        are the results in as a list stored in `completions`. Once stored is the query completions
        window opened (forced).

        :param view: currently active sublime view
        :type view: sublime.View
        :param prefix: string for completions
        :type prefix: basestring
        :param locations: offset from beginning
        :type locations: int
        """

        self._location = location

        src = view.substr(sublime.Region(0, view.size()))
        filename = view.file_name()
        cloc = "c{0}".format(location)
        try:
            gocode = subprocess.Popen(["gocode", "-builtin", "-ignore-case", "-unimported-packages", "-f=csv",
                                       "autocomplete", filename, cloc], stdin=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=0x08000000)
        except FileNotFoundError:
            print("gocode not found in PATH")
            return

        out = gocode.communicate(src.encode())[0].decode()
        results = self.generate_completions(out)

        # Exit conditions:
        if len(results) == 0:
            return

        self.completions = results
        self.open_query_completions(view)

    def generate_completions(self, out):
        """ Parses the returned gocode results and generates a usable autocomplete list """

        results = []
        for line in filter(bool, out.split("\n")):
            arg = line.split(",,")
            hint, subj = hint_and_subj(arg[0], arg[1], arg[2])
            results.append([hint, subj])

        return results

    def open_query_completions(self, view):
        """Opens (forced) the sublime autocomplete window"""

        view.run_command("hide_auto_complete")
        view.run_command("auto_complete", {
            "disable_auto_insert": True,
            "next_completion_if_showing": False,
            "auto_complete_commit_on_tab": True,
        })

    def on_query_completions(self, view, prefix, locations):
        """Sublime autocomplete event handler.

        Get completions depends on current cursor position and return
        them as list of ('possible completion', 'completion type')

        :param view: currently active sublime view
        :type view: sublime.View
        :param prefix: string for completions
        :type prefix: basestring
        :param locations: offset from beginning
        :type locations: int

        :return: list of tuple(str, str)
        """
        location = locations[0]

        if not view.match_selector(location, "source.go"):
            return

        if self.completions:
            completions = self.completions
            self.completions = None
            return completions

        thread = threading.Thread(
            target=self.fetch_query_completions, args=(view, prefix, location))
        thread.start()

    def line_to_html(self, source):
        if source is None:
            return
        lines = source.split("\n")
        head = lines[0]
        if len(lines) >= 1:
            body = lines[1:]

        def ptag(ln): return "<p>{}</p>".format(ln)
        body = [ptag(l) for l in body]
        html = "<h4>{}</h4><body style=\"margin-left:1em\">{}</body>".format(
            head, "".join(body))
        return html

    def on_hover(self, view, position, hover_zone):
        if not view.match_selector(0, "source.go"):
            return
        if hover_zone != sublime.HOVER_TEXT:
            return

        src = view.substr(sublime.Region(0, view.size()))
        word = view.word(position)
        offset = word.a
        wordstr = src[word.a:word.b]
        if not wordstr[0].isalpha():
            return

        thread = threading.Thread(
            target=self.get_doc, args=(view,  offset, wordstr))
        thread.start()

    def get_doc(self, view,  offset, field):
        dirname = os.path.dirname(view.file_name())
        src = view.substr(sublime.Region(0, view.size()))

        try:
            gofmt = subprocess.Popen(["godef", "-i", "-o", str(offset), "-json"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
        except FileNotFoundError:
            print("godef not found in PATH")
            return

        sout, serr = gofmt.communicate(src.encode())

        if gofmt.returncode != 0:
            print(serr.decode(), end="")
            return

        newsrc = sout.decode()
        d = json.loads(newsrc)
        fn = d.get("filename", "")
        pkg = os.path.dirname(fn)
        q = "{}.{}".format(pkg, field) if fn != "" else field
        view.show_popup("Loading ...", flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                        location=offset, max_width=500, max_height=200)

        try:
            gofmt = subprocess.Popen(["go", "doc", "-short", q], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000, cwd=dirname)
        except FileNotFoundError:
            print("go not found in PATH")
            return

        sout, serr = gofmt.communicate()

        if gofmt.returncode != 0:
            print(serr.decode(), end="")
            view.hide_popup()
            return

        newsrc = sout.decode()

        content = self.line_to_html(newsrc)
        view.update_popup(content)

    def on_pre_save(self, view):
        if not view.match_selector(0, "source.go"):
            return
        view.run_command('gotools_fmt')

    def on_post_save(self, view):
        if not view.match_selector(0, "source.go"):
            return
        view.run_command('gotools_validate')

    def run_gocode(self):
        try:
            subprocess.call(["gocode"], creationflags=0x08000000)
        except FileNotFoundError:
            print("gocode not found in PATH")
            return

    def on_activated_async(self, view):
        if not view.match_selector(0, "source.go"):
            return

        if self.gocode_active == False:
            thread = threading.Thread(target=self.run_gocode,)
            thread.start()
