import sublime
import sublime_plugin
import os, subprocess

from .gosettings import GolangSettings



class UpdateToolsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		# self.view.insert(edit, 0, "Hello, World!")
		tools = [
			"github.com/mdempsky/gocode",
			"github.com/stamblerre/gocode",
			"github.com/uudashr/gopkgs/v2/cmd/gopkgs",
			"golang.org/x/tools/cmd/guru",
			"golang.org/x/tools/cmd/gorename",
			"github.com/fatih/gomodifytags",
			"github.com/sqs/goreturns",
			"github.com/godoctor/godoctor"
		]

		for tool in tools:
			self.update(tool)

	def update(self,tool):
		env = GolangSettings()

		gofmt = subprocess.Popen(["go","get","-u","-v",tool],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment())
		sout, serr = gofmt.communicate()
		print(sout.decode())
		# print(serr.decode())
		pass
