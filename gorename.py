import sublime
import sublime_plugin
import subprocess, os
from .gosettings import GolangSettings


class GorenameCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if not self.view.match_selector(0, "source.go"):
			return

		selection = self.view.sel()[0]
		win = self.view.window()

		if not selection:
			panel = win.create_output_panel("my_panel")
			win.run_command('show_panel',{"panel":"output.my_panel"})
			panel.run_command("append",{"characters":"no selection found"})
			return

		win.destroy_output_panel("my_panel")

		self.offset_arg="{}:#{}".format(self.view.file_name(),selection.begin())
		self.view.window().show_input_panel("Enter new name", "", lambda x: self.rename(self.offset_arg,x), None, None)

	def rename(self,offset,new_name):
		env = GolangSettings()

		gofmt = subprocess.Popen(["gorename","-offset",offset,"-to",new_name],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment())
		sout, serr = gofmt.communicate()
		
		win = self.view.window()
		panel = win.create_output_panel("my_panel")
		win.run_command('show_panel',{"panel":"output.my_panel"})

		if gofmt.returncode != 0:
			print(serr.decode(), end="")
			panel.run_command("append",{"characters":serr.decode()})
			return

		win.destroy_output_panel("my_panel")
