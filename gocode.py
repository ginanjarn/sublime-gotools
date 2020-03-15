import sublime, sublime_plugin, subprocess, threading
from .gosettings import GolangSettings

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