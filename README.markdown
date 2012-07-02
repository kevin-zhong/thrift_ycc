Name
====

thrift_ycc - thrift 文件解析器，用python编写，提供了非常细致的解析接口

Status
======

一个小工具，主要用于自动生成代码用

Description
===========
thrift 协议非常方便，可用于协议通信，数据存储等等，thrift 自带生成了c++，java，php，python等工具；
thrift 做为一种 DSL，对于普通的协议代码生成一般来说足够了，但实际上：

1，自带生成的协议语言毕竟有限，如果你用的是一类比较偏门的语言，那很可能就不能想用thrift协议
2，如果你想从thrift中搞出一点有趣的事情，比如假如你的thrift中定义的数据结构是数据库相关表
		如果再手动去写相关的sql语句，那肯定是非常枯燥蛋疼的事情
		为什么不写个脚本去分析下 thrift 文件，然后生成 sql 语句呢？多么美好的事情啊

当项目中使用 thrift 越来越多，对 thrift 越来越依赖的时候，thrift 原本自带的工具显得不够用了，
于是，能够解析thrift语法，且根据自己的需求写出一些东东的需要日益强烈，且解析 thrift 本身是一件
非常有意思的事情，值得一干；

于是在一个双周末，花了大概5个小时左右，用 python 写出了解析代码；本身解析其实还是比较简单的；
顺带完成的从 thrift -> tolua++ pgk 代码生成还是花了其中大部分时间的；

thrift_ycc.py 为解析代码，解析就一个类 ThriftYcc,蛮简单的；
支持thrift所有DSL格式，包括：
		名字空间/namespace，包含/include，enum，struct，字段，field默认值，注释等等

这个文件中的另外一个类是一个非常简单的测试类，把解析后的类再拼回到 thrift 格式，可以当作一个简单的
thrift 格式化工具；


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
		
		
至于 lib 中的另外一个文件：tolua_thrift.py 和 lua_* 等代码，是我用 thrift_ycc 写的
thrift 到 tolua++ 的 pkg 代码生成工具，这个工具会根据thrift中的“include”指令，自动
递归分析下去；还是有点小成就感的；

Btw
===========
正则表达式真的非常强大，这回用python耍了一把，python的正则表达式的功能基本来源于 perl，
但我感觉最简洁最强大的正则表达式功能还是用 perl 爽，非常简单牛逼，当然写出来的代码可读性
就...有点天书感...