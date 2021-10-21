import lustre_par as lp
# import lustre_print
from lustre_util import substitute, simplify_pack

def expr(e):
	""
	pass

G_pack = None

def do_pack(pack):
	""
	stmt_l = []
	cst_l = sorted(n for n,v in pack.items() if isinstance(v,dict) and v.get('')=='const')
	for cst in cst_l:
		v = pack[cst]
		e = v['value']
		py_e = expr(e)
		stmt_l.append(['=',[cst],py_e])
	for k in sorted(pack):
		v = pack[k]
		if isinstance(v,dict) and v.get('')=='function':
			_ = 2+2
	return sl
	
def do_str(s):
	""
	global G_pack
	G_pack = lp.parser.parse(s, debug=False)
	pack = simplify_pack(G_pack)
	ast = do_pack(pack)
	sl = ast
	return sl

def do_file(fn):
	""
	import codecs
	print('*** {} ***'.format(fn))
	#with open(fn, 'r', encoding='utf-8') as f:
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		sl = do_str(s)
		f = codecs.open('simplify.scade', 'w',encoding='utf-8')
		f.writelines(s+'\n' for s in sl)
		f.close()
	else:
		sl = []
	return sl

if __name__ == "__main__":
	for fn, fun in ( \
		#('test/scheduling/kcg_xml_filter_out.scade','mc_20times_2corexs_4tasks'), \
		('test/scheduling/kcg_xml_filter_out.scade','mc_20ti_2co_4ta_th0'), \
		):
		result = do_file(fn)
		_ = 2+2