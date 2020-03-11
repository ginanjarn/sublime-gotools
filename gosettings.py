import sublime
import os

class GolangSettings:
	def __init__(self):
		self.settings = sublime.load_settings("sublime-gotools.sublime-settings")

	def get_environment(self):
		myenv = os.environ.copy()

		goroot = self.get_settings("go_root")
		if not goroot:
			goroot = "/usr/local/go"
		gopath = self.get_settings("go_path")
		if not gopath:
			gopath = myenv["HOME"] + "/go"

		gorootbin = os.path.join(goroot,"bin")
		gopathbin = os.path.join(gopath,"bin")

		myenv["GOPATH"]=gopath
		myenv["PATH"]=":".join([gorootbin,gopathbin,myenv["PATH"]])

		return myenv

	def get_settings(self,key):
		return self.settings.get(key)