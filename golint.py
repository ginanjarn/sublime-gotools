import sublime, sublime_plugin, subprocess, os, sys


def get_env():
	env = os.environ.copy()
	settings = sublime.load_settings("go.sublime-settings")
	gopath = settings.get("GOPATH",None)
	goroot = settings.get("GOROOT",None)

	if sys.platform != 'win32':
		if not gopath:
			print('GOPATH not defined')
			return
		if not goroot:
			print('GOROOT not defined')
			return

	env["PATH"]=":".join([os.path.join(gopath,"bin"),os.path.join(goroot,"bin")])
	env["GOPATH"]=gopath
	return env

class LintGovetCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		gofmt = subprocess.Popen(["go","vet",self.view.file_name()],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_env())
		sout, serr = gofmt.communicate()

		self.show_output(self.view,serr.decode())

	def show_output(self,view,message):
		win = view.window()		
		panel = win.create_output_panel("lint_panel")
		win.run_command('show_panel',{"panel":"output.lint_panel"})

		if message:
			panel.run_command("append",{"characters":message})
			return

		win.destroy_output_panel("lint_panel")

class Linting(sublime_plugin.EventListener):
	def on_post_save(self, view):
		if not view.match_selector(0, "source.go"):
			return
		view.run_command('lint_govet')