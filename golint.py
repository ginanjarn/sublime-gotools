import sublime, sublime_plugin, subprocess, os

def get_env():
	env = os.environ.copy()
	env["PATH"]=":".join(["/home/ginanjarn/go/bin","/home/ginanjarn/App/go/bin"])
	env["GOPATH"]="/home/ginanjarn/go"
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