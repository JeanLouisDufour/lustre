import lustre_chk

import lustre_par as lp
import lustre_path; from lustre_path import get_pack_at_absolute_path, path_resolution
import lustre_print
import lustre_util
from lustre_util import substitute
import toposort as ts
from collections import ChainMap
from copy import deepcopy

def smooth_setitem(d,k,v):
	""
	if k in d:
		assert d[k] == v, (k,v,d[k])
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
		f = codecs.open('expand.scade', 'w',encoding='utf-8')
		f.writelines(s+'\n' for s in result)
		f.close()
	else:
		result = None
	return result

has_none = {'-$','$+$','$-$','$*$'}
def make_def(op):
	""
	assert op[-1] == '$'
	rop = op[1:-1] if op[0] == '$' else op[:-1]
	ti = to = 'int32'
	if rop in ('and','or','not'):
		ti = 'bool'
	if rop in ('=','<>'):
		ti = "'T"
	if rop in ('and','or','not','=','<>','>','>=','<','<='):
		to = 'bool'
	if op[0] == '$': # binaire
		assert rop in ('and','or','=','<>','>','>=','<','<=','+','-','*')
		e = [rop,None,'a','b'] if op in has_none else [rop,'a','b']
		op_def = {
			'inputs': [('a',ti),('b',ti)],
			'outputs' : [('z',to)],
			'let' : [['=',['z'],e]]
			}
	else:
		assert rop in ('not','-')
		e = [rop,None,'a'] if op in has_none else [rop,'a']
		op_def = {
			'inputs': [('a',ti)],
			'outputs' : [('z',to)],
			'let' : [['=',['z'],e]]
			}
	return op_def

G_pack = []

def do_str(s, fun):
	""
	global G_pack
	G_pack = lp.parser.parse(s, debug=False)
	lustre_chk.chk_main(G_pack)
	fd0 = deepcopy(G_pack[fun])
	fd1 = expand_fun(fd0)
	sl = lustre_print.chk_pack(None,{fun+'_expand':fd1})
	return sl

def type_expr(e,fd):
	""
	if isinstance(e,int):
		ty = 'int32'
	elif isinstance(e,str):
		if e in ('false','true'):
			ty = 'bool'
		elif e in fd['var']:
			ty = fd['var'][e]
		elif e in dict(fd['outputs']):
			ty = dict(fd['outputs'])[e]
		else:
			foo = {(k if isinstance(k,str) else ''):v for k,v in fd['inputs']}
			if e in foo:
				ty = foo[e]
			else:
				assert e == '_', e
				ty = None
				assert False
	elif isinstance(e,list):
		if e[0] == '-unaire':
			ty = 'int32'
		else:
			assert False,e
	else:
		assert False,e 
	return ty

def ndim(t):
	""
	if t is None:
		assert False
	elif isinstance(t,str):
		n = 0
	elif isinstance(t,list) and t[0] == '^':
		n = 1+ndim(t[1])
	else:
		assert False
	return n

def instanciate_fun(op_def, ef_sizes):
	""
	fd = op_def
	fm_sizes = fd['sizes']
	assert len(ef_sizes) == len(fm_sizes)
	assert all(isinstance(x,int) for x in ef_sizes), ef_sizes
	subst_sz = dict(zip(fm_sizes,ef_sizes))
	new_fd = substitute(fd, subst_sz)
	del new_fd['sizes']
	return new_fd

G_array_d = {}

G_new_cnt = 100
def new_cnt():
	""
	global G_new_cnt
	G_new_cnt += 1
	if G_new_cnt == 479:
		_ = 2+2
	return G_new_cnt	

def expand_call(op_def, ef_inputs, ef_outputs, ef_sizes=[], info=[]):
	"""
	les variables d'interface disparaissent
	les variables locales sont suffixees
	"""
	expand_cnt = new_cnt()
	suffix = '__'+str(expand_cnt)
	#print(opname)
	if not all(isinstance(x,int) or (isinstance(x,str) and x.isidentifier()) or x==['-unaire', None, 1] for x,_ in ef_inputs):
		assert False, ef_inputs
	assert all(x.isidentifier() and x!='_' for x,_ in ef_outputs), ef_outputs
	if ef_sizes:
		fd = instanciate_fun(op_def, ef_sizes)
	else:
		fd = op_def.copy()
		assert 'sizes' not in fd
	fm_inputs = fd['inputs']
	assert len(ef_inputs) == len(fm_inputs)
	assert [t for _,t in ef_inputs] == [t for _,t in fm_inputs], ([t for _,t in ef_inputs] , [t for _,t in fm_inputs], info)
	subst_in = {n:ef_inputs[n_i][0] for n_i, (n,_) in enumerate(fm_inputs)}
	fm_outputs = fd['outputs']
	assert len(ef_outputs) == len(fm_outputs)
	assert [t for _,t in ef_outputs] == [t for _,t in fm_outputs], ([t for _,t in ef_outputs] , [t for _,t in fm_outputs], info)
	subst_out = {n:ef_outputs[n_i][0] for n_i, (n,_) in enumerate(fm_outputs)}
	#in_d
	var_d = fd.get('var',{})
	new_var_d = {n+suffix:v for n,v in var_d.items()}
	subst_var = {n:n+suffix for n in var_d}
	subst = ChainMap(subst_in, subst_out, subst_var)
	assert len(subst) == len(subst_in) + len(subst_out) + len(subst_var)
	eq_l = fd['let']
	new_eq_l = substitute(eq_l, subst)
	fd['inputs'] = ef_inputs
	fd['outputs'] = ef_outputs
	fd['var'] = new_var_d
	fd['let'] = new_eq_l
	new_var_d, new_eq_l = expand_scope(fd, info = info)
	return new_var_d,new_eq_l

def expand_fun(fd):
	""
	new_in = []
	for i,(v,t) in enumerate(fd['inputs']):
		nd = ndim(t)
		assert nd in (0,1), fd['inputs']
		if nd == 0:
			new_in.append([v,t])
		else:
			ty,sz = t[1:]
			new_in.extend([v+'__'+str(i),ty] for i in range(sz))
			smooth_update(fd['var'], {v:t})
			fd['let'].insert(0,['=', [v], ['[',None,[v+'__'+str(i) for i in range(sz)]]])
			G_array_d[v] = (ty,sz)
	fd['inputs'] = new_in
	fd1 = fd.copy()
	fd1['var'],fd1['let'] = expand_scope(fd)
	return fd1

#array_constructed = {}
#array_destructed = {}
def expand_scope(op_def, info=[]):
	""
	#global array_constructed, array_destructed
	array_d = {}
	var_d = op_def['var']; new_var_d = var_d.copy()
	eq_l = op_def['let']; new_eq_l = eq_l.copy()
	patch_l = []
	l2ls_l = lustre_util.depend_eq_list(eq_l)
	r = ts.toposort_flatten(dict(enumerate(l2ls_l)))
	assert len(r) >= 1 and (r[0]==-1 or -1 not in r), r
	assert len(r) == len(eq_l) + (r[0]==-1)
	### 1 - definition des patchs
	il = r[1:] if r[0]==-1 else r
	for eq_i in il:
		eq = eq_l[eq_i]
		if eq[0] == '=':
			if '_' in eq[1]:
				assert len(eq[1]) == 1 and isinstance(eq[2],str), eq
				continue
			ty_out = [type_expr(e,op_def) for e in eq[1]]
			ty_out_ndim = [ndim(t) for t in ty_out]
			ty_out_has_arrays = any(n != 0 for n in ty_out_ndim)
			e = eq[2]
			if isinstance(e, list):
				op = e[0]
				pl = e[1:]
				if isinstance(op, list):
					assert all(isinstance(p,str) or p==['-unaire', None, 1] for p in pl), eq
					if op[0] == '<<>>':
						if op[1] == 'vect_add':
							x_op_def = substitute(G_pack[op[1]],{"'T":'int32'})
						else:
							x_op_def = deepcopy(G_pack[op[1]])
						ef_inputs = [(e,type_expr(e,op_def)) for e in pl]
						ef_outputs = list(zip(eq[1],ty_out))
						new_var, new_let = expand_call(x_op_def, ef_inputs, ef_outputs, op[2:], info=info+lustre_print.scope({'let':[eq]}))
						# [print(l) for l in lustre_print.scope({'var':new_var,'let':new_let})]
						patch_l.append((eq_i, new_var, new_let))
					elif op[0] in ('fold','foldi','map','mapi','mapfold','mapfoldi'):
						assert len(op) in (3,4)
						iter = op[0]
						new_var = {}; new_let = []
						iter_nb = op[2]
						assert isinstance(iter_nb, int)
						if isinstance(op[1], list):
							assert op[1][0] == '<<>>' and op[1][1].isidentifier()
							x_op_def = deepcopy(G_pack[op[1][1]])
							x_op_def = instanciate_fun(x_op_def, op[1][2:])
							if op[1][1] == 'vect_add':
								assert op[0] == 'map', eq
								ty = var_d[pl[0]]
								assert ty[:2] == ['^','int32'], eq
								x_op_def = substitute(x_op_def,{"'T":'int32'})
						elif op[1].isidentifier():
							x_op_def = deepcopy(G_pack[op[1]])
							if op[1] == 'util_if_then_else':
								assert op[0] == 'map', eq
								ty = var_d[pl[1]]
								assert ty[0] == '^' and ty[1] in ('bool','int32'), eq
								x_op_def = substitute(x_op_def,{"'T":ty[1]})
						else:
							assert op[1][-1] == '$', e
							x_op_def = make_def(op[1])
							if op[1] in ('$=$','$<>$'): # polymorphic
								assert op[0] == 'map', eq
								ty = var_d[pl[0]]
								assert ty[:2] == ['^','int32'], eq
								x_op_def = substitute(x_op_def,{"'T":'int32'})
						if iter in ('map','mapi'):
							a = 0
						elif iter in ('fold','foldi'):
							a = 1
						else:
							a = 1 if len(op)==3 else op[3]['acc_nb']
						is_i = iter[-1]=='i'
						if is_i:
							_,vt = x_op_def['inputs'][0]
							assert vt == 'int32'
						assert len(eq[1]) == len(x_op_def['outputs'])
						for vn, (_,vt) in zip(eq[1][a:],x_op_def['outputs'][a:]):
							if vn == '_L11__453':
								_ = 2+2
							assert all((vn+'__'+str(i)) not in new_var for i in range(iter_nb))
							smooth_update(new_var, {vn+'__'+str(i):vt for i in range(iter_nb)})
							new_let.append(['=', [vn], ['[',None,[vn+'__'+str(i) for i in range(iter_nb)]]])
							assert vn not in array_d
							array_d[vn] = (vt,iter_nb)
						assert len(pl)+is_i == len(x_op_def['inputs'])
						for vn, (_,vt) in zip(pl[a:], x_op_def['inputs'][a+is_i:]):
							if vn == '_L11__453':
								_ = 2+2
							if vn in array_d:
								assert array_d[vn] == (vt,iter_nb)
							else: # ne doit arriver que pour un input
								assert all((vn+'__'+str(i)) not in new_var for i in range(iter_nb))
								smooth_update(new_var, {vn+'__'+str(i):vt for i in range(iter_nb)})
								array_d[vn] = (vt,iter_nb)
								for i in range(iter_nb):
									vi = vn+'__'+str(i)
									assert all(vi not in eq[1] for eq in new_let)
									new_let.append(['=', [vi], ['.[.]', None, vn, i]])
						# accus
						accus = [pl[:a]] + [[None]*a for i in range(iter_nb-1)] + [eq[1][:a]]
						taccus = [type_expr(e,op_def) for e in pl[:a]]
						taccus1 = [type_expr(e,op_def) for e in eq[1][:a]]
						assert taccus == taccus1
						suffix = '__'+str(new_cnt()) if a else None
						for i in range(a):
							_, vt_in = x_op_def['inputs'][i+is_i]
							_, vt_out = x_op_def['outputs'][i]
							assert vt_in == vt_out
							acc = 'acc'+str(i)+suffix
							for j in range(1,iter_nb):
								acc_name = acc+'__'+str(j)
								smooth_update(new_var, {acc_name : vt_in})
								accus[j][i] = acc_name
						new_info = lustre_print.scope({'let':[eq]})
						tarrin = [type_expr(e,op_def) for e in pl[a:]]
						for t_i,t in enumerate(tarrin):
							assert t[0] == '^' and t[2] == iter_nb
							tarrin[t_i] = t[1]
						tin = (['int32'] if is_i else []) + taccus + tarrin #[None] * (is_i+len(pl))
						tarrout = [type_expr(e,op_def) for e in eq[1][a:]]
						for t_i,t in enumerate(tarrout):
							assert t[0] == '^' and t[2] == iter_nb
							tarrout[t_i] = t[1]
						tout = taccus + tarrout
						for i in range(iter_nb):
							pout = accus[i+1]+[(vn+'__'+str(i)) for vn in eq[1][a:]]
							pin = ([i] if is_i else [])+accus[i]+[(vn+'__'+str(i)) for vn in pl[a:]]
							assert len(pin)==len(tin) and len(pout)==len(tout)
							x_var, x_let = expand_call(x_op_def, list(zip(pin,tin)), list(zip(pout,tout)), info = info+new_info+[str(i)])
							smooth_update(new_var,x_var)
							new_let.extend(x_let)
						patch_l.append((eq_i, new_var, new_let))
					else:   #
						assert False, e
				elif op in {'and', 'if', 'not', 'or','with'}:
					#assert all(isinstance(p,str) for p in pl), eq
					pass
				elif op.isidentifier():
					assert all(isinstance(p,str) for p in pl), eq
					new_info = lustre_print.scope({'let':[eq]})
					x_op_def = deepcopy(G_pack[op])
					ef_inputs = [(e,type_expr(e,op_def)) for e in pl]
					ef_outputs = [(e,type_expr(e,op_def)) for e in eq[1]]
					new_var, new_let = expand_call(x_op_def, ef_inputs, ef_outputs, info = info+new_info)
					patch_l.append((eq_i, new_var, new_let))
				else:  # [ < >= ^ (
					assert op in {'[', '=','<>','<','<=','>','>=','+','-','-unaire', '^', '(','.default'}, e
				_ = 2+2
			elif isinstance(e,str):
				if e.isidentifier():
					pass # assert e in env_d, e
				else:
					assert False, e
			elif isinstance(e,int):
				pass
			else:
				assert False, e
		else:
			assert False, (i,eq)
	### 2 - application des patchs
	for eq_i, new_var, new_let in reversed(patch_l):
		new_eq_l[eq_i] = ['assume','ASSUME'+str(new_cnt()),"true"]
		inter = set(new_var_d) & set(new_var)
		if inter != set():
			_ = 2+2
		smooth_update(new_var_d, new_var)
		new_eq_l.extend(new_let)
		_ = 2+2
	return new_var_d, new_eq_l

if __name__ == "__main__":
	for fn, fun in ( \
		('test/scheduling/kcg_xml_filter_out.scade','mc_20times_2cores_4tasks'), \
		):
		result = do_file(fn, fun)
		_ = 2+2
