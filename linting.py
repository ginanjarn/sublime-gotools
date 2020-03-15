import sublime, sublime_plugin, subprocess
from .gosettings import GolangSettings

class GovetCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		env = GolangSettings()

		gofmt = subprocess.Popen(["go","vet",self.view.file_name()],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env.get_environment())
		sout, serr = gofmt.communicate()
		
		win = self.view.window()		
		panel = win.create_output_panel("my_panel")
		win.run_command('show_panel',{"panel":"output.my_panel"})

		if gofmt.returncode != 0:
			print(serr.decode(), end="")		
			panel.run_command("append",{"characters":serr.decode()})
			return

		win.destroy_output_panel("my_panel")

class Linting(sublime_plugin.EventListener):

	def on_post_save(self, view):
		if not view.match_selector(0, "source.go"):
			return
		view.run_command('govet')