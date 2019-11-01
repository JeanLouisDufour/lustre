import lustre_par as lp
import codecs, json, os # , os.path

def tok2str(t):
	""
	if not t[0].isalpha():
		t = "'"+t+"'"
	return t
	
def lustre_check_oper(oper, package, pack_path=[]):
	"return id_list"
	assert package[''] in('package',) and oper in package
	impl = package[oper]
	assert impl[''] in ('function','node')
	if 'let' in impl:
		eqs = impl['let']
		for eq in eqs:
			assert isinstance(eq,list)
			if eq[0] == '=':
				lhs = eq[1]
				assert isinstance(lhs,list)
				rhs = eq[2]
				foo = lustre_check_expr(rhs, oper, package, pack_path)
			else:
				2+2
	else:
		2+2

def lustre_check_expr(e, oper, package, pack_path=[]):
	""
	if isinstance(e,(bool,int,str)):
		return set()
	elif isinstance(e,list):
		if isinstance(e[0], str):
			if e[0] in ('char','const','last'):
				2+2
			else: # user op
				return lustre_check_oper(e[0], package, pack_path)
		elif isinstance(e[0], list): ## operator
			2+2
		else:
			assert False
	else:
		assert False

def parse_file(fn):
	""
	print('*******************    {}       ******************'.format(fn))
	if True:
		f = codecs.open(fn, 'r')
		prg = f.read()
		f.close()
		try:
			result = lp.parser.parse(prg)
		except:
			result = None
			print("BEGIN DUMP")
			for symb in lp.parser.symstack:
				print(symb)
			print(lp.parser.statestack)
			print("END DUMP")
			raise

fn_list = ( \
   'lustre_test_KO.scade', \
   'lustre_test_OK.scade', \
   'E:\\', \
   )

for fn in fn_list:
	#with open(fn, 'r', encoding='utf-8') as f:
	#f = codecs.open(fn, 'r', encoding='utf-8')
	if os.path.isfile(fn):
		parse_file(fn)
#		assert fn.endswith('.scade')
#		js_file = fn[:-5] + 'json'
#		f = open(js_file, 'w')
#		json.dump(result, f, indent=4)
#		f.close()
	elif os.path.isdir(fn):
		for root, dirs, files in os.walk(fn):
			for file in files:
				if file.endswith('.scade'):
					fn = os.path.join(root,file)
					parse_file(fn)
	else:
		print('!!!!! NOT FOUND : '+fn)
