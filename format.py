import sublime, sublime_plugin, subprocess, difflib
from .gosettings import GolangSettings

def diff_sanity_check(a, b):
	if a != b:
		raise Exception("diff sanity check mismatch\n-%s\n+%s" % (a, b))

def apply_changes(edit,view,src,newsrc):
		diff = difflib.ndiff(src.splitlines(), newsrc.splitlines())
		i = 0
		for line in diff:
			if line.startswith("?"): # skip hint lines
				continue

			l = (len(line)-2)+1
			if line.startswith("-"):
				diff_sanity_check(view.substr(sublime.Region(i, i+l-1)), line[2:])
				view.erase(edit, sublime.Region(i, i+l))
			elif line.startswith("+"):
				view.insert(edit, i, line[2:]+"\n")
				i += l
			else:
				diff_sanity_check(view.substr(sublime.Region(i, i+l-1)), line[2:])
				i += l

class GofmtCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		env = GolangSettings()

		src = view.substr(sublime.Region(0, view.size()))
		gofmt = subprocess.Popen(["gofmt"],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env.get_environment())
		sout, serr = gofmt.communicate(src.encode())
		if gofmt.returncode != 0:
			print(serr.decode(), end="")
			return

		newsrc = sout.decode()
		apply_changes(edit,view,src,newsrc)

class GoreturnsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		env = GolangSettings()
		
		src = view.substr(sublime.Region(0, view.size()))
		gofmt = subprocess.Popen(["goreturns"],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env.get_environment())
		sout, serr = gofmt.communicate(src.encode())
		if gofmt.returncode != 0:
			print(serr.decode(), end="")
			return

		newsrc = sout.decode()
		apply_changes(edit,view,src,newsrc)		


class Formatting(sublime_plugin.EventListener):

	def on_pre_save(self, view):
		if not view.match_selector(0, "source.go"):
			return
		view.run_command('goreturns')
		view.run_command('gofmt')