import lustre_chk

import lustre_par as lp
import lustre_path; from lustre_path import get_pack_at_absolute_path, path_resolution

from collections import ChainMap

def smooth_setitem(d,k,v):
	""
	if k in d:
		assert d[k] == v
	else:
		d[k] = v
		
def smooth_update(d, ud):
	""
	for k,v in ud.items():
		smooth_setitem(d,k,v)

def do_file(fn, fun):
	""
	import codecs
	print('*** {} ***'.format(fn))
	#with open(fn, 'r', encoding='utf-8') as f:
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		result = do_str(s, fun)
	else:
		result = None
	return result

G_pack = []

def do_str(s, fun):
	""
	global G_pack
	G_pack = lp.parser.parse(s, debug=False)
	lustre_chk.chk_main(G_pack)
	fd0 = G_pack[fun]
	fd1 = expand_fun(fd0)
	return None

def expr_subst(e, subst):
	"ne recoit que des expressions simples"
	if isinstance(e, list):
		op = e[0]; params = e[1:]
		xop = op
		if isinstance(op,list):
			if op[0] == 'map':
				assert len(op) == 3
				iter_op = op[1]
				iter_len = op[2]
				# eff_len = expr_subst(op[3])
			else:
				_ = 2+2
		else:
			_ = 2+2
		if len(params)>=1 and isinstance(params[-1],dict):
			assert False, e
		xparams = [expr_subst(p, subst) for p in params]
		r = [xop]+xparams
	elif isinstance(e,str):
		r = subst.get(e,e)
	elif isinstance(e,int):
		r = e
	elif e == None:
		r = e
	else:
		assert False, e
	return r

expand_cnt = 0

def expand_call(opname, ef_inputs, ef_outputs, ef_sizes=[]):
	"""
	les variables d'interface disparaissent
	les variables locales sont suffixees
	"""
	global expand_cnt
	expand_cnt += 1
	suffix = '__'+str(expand_cnt)
	print(opname)
	assert all(x.isidentifier() for x in ef_inputs), ef_inputs
	assert all(x.isidentifier() for x in ef_outputs), ef_outputs
	assert all(isinstance(x,int) for x in ef_sizes), ef_sizes
	if isinstance(opname, list):
		assert opname[0] == '::'
		assert False
	fd = G_pack[opname]
	fm_sizes = fd.get('sizes',[])
	assert len(ef_sizes) == len(fm_sizes)
	subst_sz = {n:ef_sizes[n_i] for n_i, n in enumerate(fm_sizes)}
	fm_inputs = fd['inputs']
	assert len(ef_inputs) == len(fm_inputs)
	subst_in = {n:ef_inputs[n_i] for n_i, (n,_) in enumerate(fm_inputs)}
	fm_outputs = fd['outputs']
	assert len(ef_outputs) == len(fm_outputs)
	subst_out = {n:ef_outputs[n_i] for n_i, (n,_) in enumerate(fm_outputs)}
	#in_d
	var_d = fd.get('var',{})
	new_var_d = {n+suffix:v for n,v in var_d.items()}
	subst_var = {n:n+suffix for n in var_d}
	subst = ChainMap(subst_sz, subst_in, subst_out, subst_var)
	assert len(subst) == len(subst_sz) + len(subst_in) + len(subst_out) + len(subst_var)
	eq_l = fd['let']
	new_eq_l = [None] * len(eq_l)
	for eq_i,eq in enumerate(eq_l):
		assert eq[0] == '='
		new_r = [subst[x] for x in eq[1]] # expr_subst(x,subst)
		e = eq[2]
		if isinstance(e,list): 
			op = e[0]
			if isinstance(op, list):
				if op[0] == '<<>>':
					assert op[1].isidentifier()
					new_op = op[:2]
					for sz in op[2:]:
						assert isinstance(sz,int) or sz.isidentifier()
						new_sz = subst.get(sz, sz)
						assert isinstance(new_sz, int)
						new_op.append(new_sz)
				elif op[0] in ('fold','foldi','map','mapi','mapfold','mapfoldi'):
					assert len(op) in (3,4)
					if isinstance(op[1], list):
						assert op[1][0] == '<<>>' and op[1][1].isidentifier()
						new_op1 = op[1][:2]
						for sz in op[1][2:]:
							assert isinstance(sz,int) or sz.isidentifier()
							new_sz = subst.get(sz, sz)
							assert isinstance(new_sz, int)
							new_op1.append(new_sz)
					else:
						assert op[1].isidentifier() or op[1][-1] == '$', e
						new_op1 = op[1]
					new_op = [op[0], new_op1]
					sz = op[2]
					assert isinstance(sz,int) or sz.isidentifier()
					new_sz = subst.get(sz, sz)
					assert isinstance(new_sz, int)
					new_op.append(new_sz)
					if len(op) == 4:
						assert list(op[3].keys()) == ['acc_nb'] and isinstance(op[3]['acc_nb'], int)
						new_op.append(op[3])
				else:
					assert False, e
			else: # op not list
				new_op = op
			new_e = [new_op] + [expr_subst(p, subst) for p in e[1:]]
		else:
			new_e = expr_subst(e, subst)
		new_eq_l[eq_i] = ['=', new_r, new_e]
	return new_var_d,new_eq_l

def expand_fun(fd):
	""
	fd1 = fd.copy()
	fd1_var = fd1['var'] = fd['var'].copy()
	fd1_let = fd1['let'] = fd['let'].copy()
	input_d = dict(fd['inputs'])
	output_d = dict(fd['outputs'])
	var_d = fd['var']
	local_d = ChainMap(input_d,output_d,var_d)
	env_d = ChainMap(local_d, G_pack)
	eq_l = fd['let']
	patch_l = []
	### 1 - definition des patchs
	for eq_i,eq in enumerate(eq_l):
		if eq[0] == '=':
			e = eq[2]
			if isinstance(e, list):
				op = e[0]
				pl = e[1:]
				if isinstance(op, list):
					assert all(isinstance(p,str) for p in pl), eq
					nb_inp = -1
					if op[0] == '<<>>':
						new_var, new_let = expand_call(op[1], e[1:], eq[1], op[2:])
						patch_l.append((eq_i, new_var, new_let))
					elif op[0] == 'map':
						assert len(op) in (3,4)
						new_var = {}; new_let = []
						iter_nb = op[2]
						assert isinstance(iter_nb, int)
						if isinstance(op[1], list):
							assert op[1][0] == '<<>>' and op[1][1].isidentifier()
							assert False
						else:
							assert op[1].isidentifier() or op[1][-1] == '$', e
							new_op = op[1]
						for vn in eq[1]:
							vt = local_d[vn]
							assert vt[0] == '^' and vt[2] == iter_nb
							assert all((vn+'__'+str(i)) not in env_d for i in range(iter_nb))
							smooth_update(new_var, {vn+'__'+str(i):vt[1] for i in range(iter_nb)})
							new_let.append(['=', [vn], ['[',None,[vn+'__'+str(i) for i in range(iter_nb)]]])
						for vn in pl:
							vt = local_d[vn]
							assert vt[0] == '^' and vt[2] == iter_nb
							assert all((vn+'__'+str(i)) not in env_d for i in range(iter_nb))
							smooth_update(new_var, {vn+'__'+str(i):vt[1] for i in range(iter_nb)})
							for i in range(iter_nb):
								vi = vn+'__'+str(i)
								if all(vi not in eq[1] for eq in new_let):
									new_let.append(['=', [vi], ['.[.]', None, vn, i]])
								else:
									print('**** '+vi+' NOT CREATED')
						for i in range(iter_nb):
							pout = [(vn+'__'+str(i)) for vn in eq[1]]
							pin = [(vn+'__'+str(i)) for vn in pl]
							new_let.append(['=', pout, [new_op] + pin]) 
						patch_l.append((eq_i, new_var, new_let))
					else:   #
						assert False, e
				elif op in {'and', 'not', 'or'}:
					#assert all(isinstance(p,str) for p in pl), eq
					pass
				elif op.isidentifier():
					assert all(isinstance(p,str) for p in pl), eq
					new_var, new_let = expand_call(op, e[1:], eq[1])
					_ = 2+2
				else:  # [ < >= ^ (
					assert op in {'[', '<', '>=', '^', '('}, e
				_ = 2+2
			elif isinstance(e,str):
				if e.isidentifier():
					assert e in env_d, e
				else:
					assert False, e
			elif isinstance(e,int):
				pass
			else:
				assert False, e
		else:
			assert False, (i,eq)
	### 2 - application des patchs
	for eq_i, new_var, new_let in patch_l:
		_ = 2+2
	return fd1

if __name__ == "__main__":
	for fn, fun in ( \
		('test/scheduling/kcg_xml_filter_out.scade','mc_20times_2cores_4tasks'), \
		):
		result = do_file(fn, fun)
		_ = 2+2
