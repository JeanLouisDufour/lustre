import lustre_par as lp
import lustre_print
from copy import deepcopy
from collections import ChainMap

def depend_eq_list(eq_l):
	""
	l2ls_l = [None]*len(eq_l)
	v2l_d = {}; l2vs_l = [None]*len(eq_l)
	for eq_i,eq in enumerate(eq_l):
		ins,outs = depend_eq(eq)
		l2vs_l[eq_i] = ins
		for v in outs:
			assert v not in v2l_d, v
			v2l_d[v] = eq_i
	for i in range(len(eq_l)):
		l2ls_l[i] = set(v2l_d.get(v,-1) for v in l2vs_l[i])
	return l2ls_l

def depend_eq(eq):
	""
	ins = set(); outs = set()
	if eq[0] == '=':
		outs = set(eq[1]) - {'_'}
		ins = depend_expr(eq[2])
	elif eq[0] in ('assume',):
		pass
	else:
		assert False
	return ins,outs

def depend_expr(e):
	""
	s = set(); ops = set() # TBC
	if isinstance(e,list):
		op = e[0] ### il n'y a jamais de variable dans un operateur
		if isinstance(op,list):
			assert op[0] in {'<<>>','fold','foldi','map','mapi','mapfold','mapfoldi'}, e
		elif isinstance(op,str):
			pass
		else:
			assert False, e
		if op in ('case','{','::','<<>>'):
			assert False, e
		elif op in ('.default','with'):
			pl = [e[2],e[4]]
			for acc in e[3]:
				assert len(acc)==2 and acc[0] == '[', acc
				pl.append(acc[1])
		elif op in ('(','['):
			pl = e[2]
		elif op == ':':
			pl = e[2:3]
		elif op == 'fby':
			flow, latency, init = e[2:]
			pl = flow + [latency] + init
		elif op == 'merge':
			assert False
		elif op == 'transpose':
			expr, dim1, dim2 = e[2:]
			pl = expr + dim1 + dim2
		else:
			pl = e[2:] if len(e)>=2 and e[1] is None else e[1:]
		for p in pl:
			s.update(depend_expr(p))
	elif isinstance(e,str):
		assert e.isidentifier()
		s.add(e)
	elif isinstance(e,(float,int)):
		pass
	else:
		assert False, e
	return s

#######################################################################

def substitute(e, subst):
	"ne recoit que des expressions simples"
	if isinstance(e, dict):
		r = {k:substitute(v, subst) for k,v in e.items()}
	elif isinstance(e, list):
		r = [substitute(p, subst) for p in e]
	elif isinstance(e, tuple):
		r = tuple(substitute(p, subst) for p in e)
	elif isinstance(e,str):
		r = subst.get(e,e)
	elif isinstance(e,int):
		r = e
	elif e is None:
		r = e
	else:
		assert False, e
	return r

G_equipot = []
def is_in_equipot(v):
	""
	for e_i,e in enumerate(G_equipot):
		if v in e:
			return e_i
	return -1

def add_equipot(a,b):
	""
	a_i = is_in_equipot(a)
	b_i = is_in_equipot(b)
	if a_i==-1 and b_i==-1:
		G_equipot.append([a,b])
	elif a_i==-1:
		G_equipot[b_i].append(a)
	elif b_i==-1:
		G_equipot[a_i].append(b)
	else:
		G_equipot[a_i].extend(G_equipot[b_i])
		del G_equipot[b_i]

def simplify(fd):
	""
	global G_equipot
	G_equipot = []
	fd = deepcopy(fd)
	in_d = dict(fd['inputs'])
	out_d = dict(fd['outputs'])
	var_d = fd.get('var',{})
	env_d = ChainMap(var_d,in_d,out_d)
	defines_d = {}
	is_defined_at = {}
	is_defined_by = {}
	eq_l = fd['let']
	# 
	for eq_i, eq in enumerate(eq_l):
		if eq[0] == '=':
			if len(eq[1])==1 and eq[1][0]!='_' and isinstance(eq[2],str) and eq[2] in env_d:
				a = eq[1][0]
				is_defined_at[a] = eq_i
				b = eq[2]
				is_defined_by[a] = b
				if b in defines_d:
					defines_d[b].append(a)
				else:
					defines_d[b] = [a]
				add_equipot(a,b)
	#
	for EQ in G_equipot:
		foo = [i for i,x in enumerate(EQ) if x not in is_defined_at]
		if len(foo) != 1:
			assert False, EQ
		base = EQ[foo[0]]
		del EQ[foo[0]]
		assert base not in out_d
		EQ_out = [x for x in EQ if x in out_d]
		EQ = [x for x in EQ if x not in out_d]
		# phase 1 on detruit les locales non base
		subst = {v:base for v in EQ}
		for v in EQ:
			del var_d[v]
			eq_l[is_defined_at[v]] = ['assume',v,"true"]
		for eq_i, eq in enumerate(eq_l):
			if eq[0] == '=':
				eq[2] = substitute(eq[2], subst)
		# phase 2
		if EQ_out and base not in in_d:
			del var_d[base]
			fst_out = EQ_out[0]
			for v in EQ_out[1:]:
				ev = eq_l[is_defined_at[v]]
				ev[2] = fst_out
			eq_l[is_defined_at[fst_out]] = ['assume','__'+fst_out,"true"]
			eq_l = substitute(eq_l, {base:fst_out})
	fd['let'] = [eq for eq in eq_l if eq[0] != 'assume']
	#
	return fd

def simplify_pack(pack):
	""
	r_pack = {}
	for k in sorted(pack):
		if k.isidentifier() and k not in ('package','open'):
			fd = pack[k]
			kind = fd['']
			if kind in ('function','node'):
				fd = simplify(fd)
			r_pack[k] = fd
		else:
			r_pack[k] = pack[k]
	return r_pack

G_pack = None
def do_str(s):
	""
	global G_pack
	G_pack = lp.parser.parse(s, debug=False)
	pack = simplify_pack(G_pack)
	sl = lustre_print.chk_pack(None,pack)
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
		('test/scheduling/kcg_xml_filter_out.scade','mc_20times_2cores_4tasks'), \
		):
		result = do_file(fn)
		_ = 2+2
