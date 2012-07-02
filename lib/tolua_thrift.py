#!/usr/bin/env python

import sys, os.path
import string, re
import thrift_ycc

exe_path = os.path.abspath(os.path.dirname(sys.argv[0]))

class ThriftBase(thrift_ycc.ThriftYcc):
        def __init__(self, thrift_file, out=True):
                super(ThriftBase, self).__init__(thrift_file)
		self._isout = out
                self._includes = {}
                self._enums = []
                self._structs = []
		self._type_map = {"byte":"char", "i16":"short", "i32":"int", "i64":"long", "string":"string"}

        def on_def_namespace(self, nm_array):
                self._num = nm_array
                self._nm_str = string.join(self._num, "::")
                self._num_begin()
	def on_all_end(self):
		self._num_end()

        def on_st_begin(self, st_name):
                self._structs.append(st_name)
        def on_enum_begin(self, enum_name):
                self._enums.append(enum_name)

	def transfer_type(self, type, thrift_name):
		pth = self
                if thrift_name:
                        pth = self._includes[thrift_name]
                nm_str, type, is_out = pth.__transfer_type(type)

                if not nm_str or nm_str == self._nm_str:
			return type, is_out

		return nm_str + "::" + type, is_out

	def __transfer_type(self, type):
		if type in self._enums:
			type = "i32"
		if type in self._type_map:
			return None, self._type_map[type], True

		if type not in self._structs:
			self.err_exit("err type=(%s), cant find in %s"%(type, self._thrift_file))

		return self._nm_str, type, self._isout
		

	def _num_begin(self):
		pass
	def _num_end(self):
		pass

class ToLuaThrift(ThriftBase):
	vec_types = set()
	map_types = set()

	def __init__(self, thrift_file):
		super(ToLuaThrift, self).__init__(thrift_file, False)

	def on_include(self, pre_path, thrift_name):
		child = None
		if pre_path:
			child = ThriftBase(os.path.join(pre_path, thrift_name) + ".thrift")
		else:
			child = ToLuaThrift(thrift_name+".thrift")
		self._includes[thrift_name] = child
		self._num_end()
		child.run()
		self._num_begin()

        def on_st_begin(self, st_name):
		super(ToLuaThrift, self).on_st_begin(st_name)
                print("struct %s {"%(st_name))
        def on_st_end(self):
                print("};\n")

	def on_st_smp_field(self, index, name, type, thrift_name, vdefault):
		print("\t%s %s;"%(self.transfer_type(type, thrift_name)[0], name))

	def on_st_vec_field(self, index, name, type, thrift_name):
		type, is_out = self.transfer_type(type, thrift_name);

		if not is_out:
			ToLuaThrift.vec_types.add(self._nm_type(type, is_out))

		print("\tstd::vector<%s> %s;"%(type, name))

	def on_st_map_field(self, index, name, type0, tname0, type1, tname1):
		type0, is_out0 = self.transfer_type(type0, tname0)
		type1, is_out1 = self.transfer_type(type1, tname1)

		if not is_out0 or not is_out1:
			ToLuaThrift.map_types.add(self._nm_type(type0, is_out0) \
				+ "," + self._nm_type(type1, is_out1))

		print("\tstd::map<%s,%s> %s;"%(type0, type1, name))

	def _nm_type(self, type, is_out):
		if is_out:
			return type

		if type.find("::")>=0 or not self._nm_str:
			return type
		else:
			return self._nm_str + "::" + type

	def _num_begin(self):
		if self._num is None:
			return
		print("/*\n* %s\n*/"%(self._nm_str))
		for each in self._num:
			print("namespace %s { "%(each))
	def _num_end(self):
                if self._num is None:
                        return
                for each in self._num:
                        print("}")
		print("")

	@staticmethod
	def run_containers():
		if ToLuaThrift.vec_types:
			vec_types = string.join(list(ToLuaThrift.vec_types), ", ")

			fd = open(exe_path + "/lua_vector.tpl", "r")
			print(re.sub("__type__", vec_types, fd.read()))
			fd.close()

		if not ToLuaThrift.map_types:
			return

		vals = set()
		kvs = []
		for each in ToLuaThrift.map_types:
			key, val = string.split(each, ",")
			vals.add(val + " bool")
			kvs.append(key + " " + val)

		map_types = "\"" + string.join(kvs, "\", \"") + "\""
		pair_types = "\"" + string.join(list(vals), "\", \"") + "\""

		fd = open(exe_path + "/lua_map.tpl", "r")
		print(fd.read().replace("__pair__", pair_types).replace("__map__", map_types))
		fd.close()

class MsgMapYcc(object):
	def __init__(self):
		self._nm_val = 0
		self._dts = []

	def run(self):
		try:
			fd = open("msg_map.inc")
		except IOError, data:
			## print("open failed, err{%s}"%(data))
			return

		match_map = [("XDRIVE_MSG_MAP_BEGIN\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*([\w|:]+)\s*\)", self._on_map_begin),
			     ("XDRIVE_MSG_MAP\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", self._on_map_each),
			     ("XDRIVE_MSG_MAP_END\s*\(\s*\)", self._on_map_end),
				]

		for line in fd:
			line = line.strip()
			if not line:
				continue
			for restr, pf in match_map:
				mres = re.match(restr, line)
				if mres:
					pf(mres.groups())
					break
		self._on_all_end()

	def _on_map_begin(self, mgroup):
		self._nm_out, nm_val, self._nm_in = mgroup
		self._nm_val = (int(nm_val, 16)<<8)

	def _on_map_each(self, mgroup):
		dt_prefix, dt_val = mgroup
		if self._nm_val == 0:
			print("no nm val")
			sys.exit(-1)

		dt_val = (self._nm_val|int(dt_val, 16))
		self._dts.append((self._nm_out, self._nm_in, dt_prefix+"Req", hex(dt_val)))
		self._dts.append((self._nm_out, self._nm_in, dt_prefix+"Resp", hex(0x8000|dt_val)))

	def _on_map_end(self, mgroup):
		self._nm_val = 0

	def _on_all_end(self):
		if not self._dts:
			return

		fd = open(exe_path + "/lua_xdrive_datagram.tpl", "r")
		tpl = fd.read()

		rrename = re.compile("(^\$renaming .*$)", re.M)
		rename_tpl = rrename.search(tpl).group(1)

		cls_tpl = []
		rnm_tpl = []
		for nm_out, nm, dt, dv in self._dts:
			dt_ful = "%s::%s"%(nm, dt)

			rnm_str = rename_tpl.replace("__dt__", dt_ful).\
				replace("__dt_val__", dv).\
				replace("__shortname__", "%s_%s"%(nm_out, dt))

			cls_tpl.append("\"%s %s\""%(dt_ful, dv))
			rnm_tpl.append(rnm_str)

		print(rrename.sub(string.join(rnm_tpl, "\n"), tpl).\
			replace("__datagram__", string.join(cls_tpl, ", ")))

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("usage: %s datagram_dir thrift_file [thrift_file2..]"%(sys.argv[0]))
		sys.exit(-1)

	datagram_dir = sys.argv[1]
	os.chdir(datagram_dir+"/thrift")

	print("$pfile \"../datagram_base/datagram_base_lua.pkg\"")
	print("$#include \"/home/kevin_zhong/comm/protocal/xdrive_datagram.h\"")

	files = sys.argv[2:]
	for each in files:
		print("$#include \"./gen-cpp/" + each.split(".")[0] + "_types.h\"")
		thrift_lua = ToLuaThrift(each)
		thrift_lua.run()
	ToLuaThrift.run_containers()

	os.chdir(datagram_dir)
	msgmap_ycc = MsgMapYcc()
	msgmap_ycc.run()

