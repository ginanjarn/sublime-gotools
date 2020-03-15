import sublime, sublime_plugin, subprocess, threading
from .gosettings import GolangSettings


class Gocode(sublime_plugin.EventListener):
	"""Sublime Text gocode integration."""

	def __init__(self):
		self.completions = None

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

		env = GolangSettings()

		gocode = subprocess.Popen(["gocode-gomod", "-f=csv", "autocomplete", filename, cloc],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env.get_environment())

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

		thread = threading.Thread(target=self.fetch_query_completions, args=(view, prefix, location))
		thread.start()
	

	def on_window_command(self, window, cmd, args):
		if cmd == "close_window":
		# if cmd == "exit":
			env = GolangSettings()

			gofmt = subprocess.Popen(["gocode-gomod","exit"],
				stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment())
			sout, serr = gofmt.communicate()
			print(serr.decode())