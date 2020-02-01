import lustre_par as lp
import codecs, glob, json, os

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

###########################

# def test_str(s):
	# ""
	# result = lp.parser.parse(s)
	# return result
test_str = lp.parse_str
	
# def test_file(fn, save_json = False):
	# ""
	# print('**  {}  **'.format(fn))
	# encoding = 'latin-1' # 'utf-8'
	# fd = codecs.open(fn, 'r',encoding=encoding)
	# s = fd.read()
	# fd.close()
	# js = test_str(s)
	# if save_json:
		# assert fn.endswith('.scade')
		# fnjs = fn[:-5] + 'json'
		# fd = codecs.open(fnjs, 'w', encoding = 'utf-8')
		# if False:
			# json.dump(js, fd, indent=4)
		# else:
			# s = json.dumps(js, indent=4)
			# if js != json.loads(s):
				# print('************* PB JSON ****************')
			# fd.write(s)
		# fd.close()
test_file = lp.parse_file
		
homedirs = [ os.path.join(os.getenv('USERPROFILE', r'C:\Users\Public'), 'Documents'), 'D:','E:','F:']
scadedirs = [h+r'\scade' for h in homedirs if os.path.isdir(h+r'\scade')]

for sd in scadedirs:
	for fn in glob.glob(sd+r'\**\kcg_xml_filter_out.scade', recursive=True):
		test_file(fn, True)
	assert False

def test_dir(fn):
	""
	for root, dirs, files in os.walk(fn):
		for file in files:
			if file.endswith('.scade'):
				fn = os.path.join(root,file)
				test_file(fn)

fn_list = ( \
   '_lustre_test_KO.scade', \
   '_lustre_test_OK.scade', \
   r'C:\Program Files\ANSYS Inc', \
   ) + scadedirs

for fn in fn_list:
	if os.path.isfile(fn):
		test_file(fn)
	elif os.path.isdir(fn):
		test_dir(fn)
	else:
		print('!!!!! NOT FOUND : '+fn)
