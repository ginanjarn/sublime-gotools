import sublime
import sublime_plugin
import os, subprocess
from json import loads
from .gosettings import GolangSettings


class GodocCommand(sublime_plugin.EventListener):
	def on_hover(self,view, point, hover_zone):
		if not view.match_selector(0, "source.go"):
			return

		if hover_zone != sublime.HOVER_TEXT:
			return

		view.settings().set("word_separators","/\\()\"'-:,;<>~!@#$%^&*|+=[]{``~?")
		region = view.word(point)
		
		doc_value = self.get_definition(view,region,point)
		if not doc_value:
			return
		self.show_popup(view,point,doc_value)


	def show_popup(self, view, location, value):
		# view.show_popup(content, <flags>, <location>, <max_width>, <max_height>, <on_navigate>, <on_hide>)

		view.show_popup(
            value,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=location,
            # on_navigate=self.goto_definition(view,ref_path),
            on_navigate=lambda href : self.goto_definition(view,href),
            max_width=600,
            max_height=400)
		pass

	def fetch_doc(self,view,name):
		env = GolangSettings()

		working_dir = os.path.dirname(view.file_name())

		gofmt = subprocess.Popen(["go","doc",name],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment(),cwd=working_dir)
		sout, serr = gofmt.communicate()
		# print(sout.decode())
		# print(serr.decode())

		return sout.decode()

	def get_definition(self,view,region,point):
		env = GolangSettings()
		source = "{}:#{},#{}".format(view.file_name(),region.begin(),region.end())
		# print(source)
		working_dir = os.path.dirname(view.file_name())
		gofmt = subprocess.Popen(["guru","-json","describe",source],
			# stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment())
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env.get_environment(),cwd=working_dir)
		sout, serr = gofmt.communicate()
		out_str = sout.decode()
		if not out_str:
			return

		# print(out_str)
		# JSON loads
		# ret = json.loads(out_str)
		ret = loads(out_str)
		if not ret:
			return

		if ret["detail"]=="value":
			doc_value = ret["value"]["type"]
			return doc_value

		if ret["detail"]=="type":			
			if "namedef" in ret["type"]:
				definition = self.fetch_doc(view,ret["type"]["type"])
			else:
				definition = ret["type"]["type"]

			def_list = definition.split("\n")

			def_position = ret["type"].get("namepos",None)
			if def_position:
				def_list.append("<a href=\"{}\">Go to definition.</a>".format(def_position))
			# def_list.append("<a href=\"{}\">Go to definition.</a>".format(ret["type"]["namepos"]))

			html_tab = lambda s : s.replace("\t","&nbsp;&nbsp;&nbsp;&nbsp;")
			html_p = lambda s : "<p>{}</p>".format(s)

			def_list = [html_tab(i) for i in def_list]
			def_list = [html_p(i) for i in def_list]

			doc_value = "".join(def_list)
			
			return doc_value

	def goto_definition(self,view,name):
		view.window().open_file(name,sublime.ENCODED_POSITION)
		pass
		