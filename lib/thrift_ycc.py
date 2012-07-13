#!/usr/bin/env python

import sys, os.path
import string, re

class ThriftYcc(object):
	def __init__(self, thrift_file):
		self._thrift_file = thrift_file
		self._pfc = self._deal_top_line
		self._fd = open(thrift_file, "r")
		self._rc = [ (re.compile("namespace\s+cpp\s+(.+)"), self._deal_nm), \
					 (re.compile("include\s+\"(.+)\""), self._deal_include), \
					 (re.compile("struct\s+(\w+)(\s*{)?"), self._deal_st), \
					 (re.compile("enum\s+(\w+)(\s*{)?"), self._deal_enum), \
					 (re.compile("/\*"), self._deal_tips)
				   ]
	def err_exit(self, strerr):
		print("err:[ %s ] in file [%s]"%(strerr, self._thrift_file))
		sys.exit(-1)
	
	def run(self):
		for each in self._fd:
			line = each.strip()
			line = re.sub("/\*[^(\*/)]*\*/", "", line)
			line = re.sub("//.*", "", line)
			if line:
				self._pfc(line)
		self.on_all_end()

	def on_all_end(self):
		pass

	## struct
	def on_st_begin(self, st_name):
		pass

	def on_st_smp_field(self, index, name, type, thrift_name, vdefault):
		pass
	def on_st_vec_field(self, index, name, type, thrift_name):
		pass
	def on_st_map_field(self, index, name, type0, tname0, type1, tname1):
		pass
        def on_st_end(self):
                pass

	def on_enum_begin(self, enum_name):
		pass
	def on_child_enum(self, child_enum, vdefault):
		pass
	def on_enum_end(self):
		pass

	## nm & include
	def on_def_namespace(self, nm_array):
		pass
	def on_include(self, pre_path, thrift_name):
		pass

	def _deal_nm(self, rem, line):
		self.on_def_namespace(rem.group(1).split("."))

	def _deal_include(self, rem, line):
		pre, base_name = os.path.split(rem.group(1))
		self.on_include(pre, os.path.splitext(base_name)[0])

	def _deal_st(self, rem, line):
		self.on_st_begin(rem.group(1))
		self._pfc = self._deal_st_field

	def _deal_enum(self, rem, line):
		self.on_enum_begin(rem.group(1))
		self._pfc = self._deal_child_enum

	def _deal_tips(self, rem, line):
		self._pfc = self._deal_next_tips

	def _deal_next_tips(self, line):
		if re.match(".*\*/", line):
			self._pfc = self._deal_top_line

	def _deal_top_line(self, line):
		mress = None
		for rc, pf in self._rc:
			mress = rc.match(line)
			if mress:
				pf(mress, line)
				return
		self.err_exit("err line=%s"%(line))

	def _deal_child_enum(self, line):
                if line == "{":
                        return
                if line == "}":
                        self.on_enum_end()
                        self._pfc = self._deal_top_line
                        return
		vdefault = None
		mdef = re.match("(\w+)\s*=\s*([\d|+|-]+)\s*[,;]?\s*$", line)
		if mdef:
			vdefault = mdef.group(2)
			line = mdef.group(1)
		self.on_child_enum(line, vdefault)

	def __get_type_thrift(self, rtype):
		index = rtype.find(".")
		if index == -1:
			return "", rtype;
		return rtype[0:index], rtype[index+1:]

	def _deal_st_field(self, line):
		if line == "{":
			return
		if line == "}":
			self.on_st_end()
			self._pfc = self._deal_top_line
			return

		vdefault = None
		mdef = re.match("(.+)\s*=\s*([\w|\"|+|-]+)\s*[,;]?\s*$", line)
		if mdef:
			vdefault = mdef.group(2)
			line = mdef.group(1).strip()
			##print("line=%s, default=%s"%(line, vdefault))

		rc = re.compile("(\d+)\s*:\s*(.+)\s+(\w+)\s*[,;]?\s*$")
		mress = rc.match(line)
		if mress == None:
			self.err_exit("err field=%s"%(line))

		index = int(mress.group(1))
		type = mress.group(2).strip()
		name = mress.group(3)
		## print("type=(%s), name=%s"%(type,name))

		mtype = re.match("(\w+)\s*<(.+)>", type)
		if mtype:
			conter = mtype.group(1)

			if conter == "list":
				thrift, sty = self.__get_type_thrift(mtype.group(2))
				self.on_st_vec_field(index, name, sty, thrift)

			elif conter == "map":
				rekv = re.match("\s*(\S+)\s*,\s*(\S+)\s*", mtype.group(2))
				if rekv is None:
					self.err_exit("err map kv='%s'"%(mtype.group(2)))

				kthrift, ksty = self.__get_type_thrift(rekv.group(1))
				vthrift, vsty = self.__get_type_thrift(rekv.group(2))
				self.on_st_map_field(index, name, ksty, kthrift, vsty, vthrift)
		else:
			thrift, sty = self.__get_type_thrift(type)
			self.on_st_smp_field(index, name, sty, thrift, vdefault)


class ThriftYccTest(ThriftYcc):
	def on_def_namespace(self, nm_array):
		print("namespace cpp %s\n"%(string.join(nm_array, ".")))
	def on_include(self, pre_path, thrift_name):
		print("include %s.thrift\n"%(os.path.join(pre_path, thrift_name)))
	def on_st_begin(self, st_name):
		print("struct %s {"%(st_name))
	def on_st_end(self):
		print("}\n")

	def on_st_smp_field(self, index, name, type, thrift_name, vdefault):
		if thrift_name:
			type = thrift_name + "." + type
		if vdefault:
			name = name + " = " + vdefault
		print("\t%d:%s %s,"%(index, type, name))
	def on_st_vec_field(self, index, name, type, thrift_name):
		if thrift_name:
			type = thrift_name + "." + type
		print("\t%d:list<%s> %s,"%(index, type, name))
	def on_st_map_field(self, index, name, type0, tname0, type1, tname1):
		if tname0:
			type0 = tname0 + "." + type0
		if tname1:
			type1 = tname1 + "." + type1
		print("\t%d:map<%s, %s> %s"%(index, type0, type1, name))

        def on_enum_begin(self, enum_name):
                print("struct %s { enum {"%(enum_name))
        def on_child_enum(self, child_enum, vdefault):
		if vdefault:
			child_enum = child_enum + " = " + vdefault
                print("\t%s,"%(child_enum))
	def on_enum_end(self):
		print("};}\n")

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("usage: %s thrift_file"%(sys.argv[0]))
		sys.exit(-1)

	thrift_ycc = ThriftYccTest(sys.argv[1])
	thrift_ycc.run()


