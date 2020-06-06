from collections import ChainMap
from copy import deepcopy
import lustre_chk
import lustre_expand
import lustre_par as lp
import lustre_util
from smtlib import smtlib
import toposort as ts

# 3000 en std
import sys
sys.setrecursionlimit(10**6)

def smtlib_read_array(arr,sz,idx,default):
	""
	e,e_t = expr(default)
	id,id_t = expr(idx)
	assert id_t == 'Int'
	for i in reversed(range(sz)):
		e = ['ite',['=',i,id], arr+'__'+str(i), e]
	return e,e_t

def typ(t):
	""
	if t == 'bool':
		st = 'Bool'
	elif t == 'int32':
		st = 'Int'
	else:
		assert False,t
	return st

G_env_d = G_arr_d = None

def expr(e):
	""
	if isinstance(e,list):
		op = e[0]
		assert isinstance(op,str)
		if op in ('and','or','not'):
			foo = [expr(f) for f in e[1:]]
			assert all(t == 'Bool' for _,t in foo)
			se = [op]+[x for x,_ in foo]
			ste = 'Bool'
		elif op in ('>','>=','<','<='):
			foo = [expr(f) for f in e[1:]]
			assert all(t == 'Int' for _,t in foo)
			se = [op]+[x for x,_ in foo]
			ste = 'Bool'
		elif op in ('=','<>'):
			foo = [expr(f) for f in e[1:]]
			assert len(foo)==2 and foo[0][1] == foo[1][1]
			se = [op if op=='=' else 'distinct']+[x for x,_ in foo]
			ste = 'Bool'
		elif op in ('+','-','*'):
			foo = [expr(f) for f in e[2:]]
			assert all(t == 'Int' for _,t in foo)
			se = [op]+[x for x,_ in foo]
			ste = 'Int'
		elif op == '.[.]':
			arr,idx = e[2:]
			if not isinstance(idx, int):
				assert False, eq
			se = arr+'__'+str(idx)
			ste = typ(G_env_d[se])
		elif op == '.default':
			arr, access, val = e[2:]
			tarr = G_arr_d[arr]
			assert tarr[0] == '^'
			telem = typ(tarr[1])
			assert isinstance(telem,str)
			szarr = tarr[2]
			assert isinstance(szarr,int)
			assert len(access)==1 and access[0][0] == '[', e
			idx = access[0][1]
			se,ste = smtlib_read_array(arr,szarr,idx,val)
			assert ste == telem, (ste,telem)
		elif op == '(':
			assert len(e[2]) == 1
			se,ste = expr(e[2][0])
		elif op == 'if':
			cond,cont_t = expr(e[2])
			assert cont_t == 'Bool'
			th, th_t = expr(e[3])
			el, el_t = expr(e[4])
			assert th_t == el_t, e
			se = ['ite',cond,th,el]
			ste = th_t
		elif op == '-unaire':
			se,ste = expr(e[2])
			assert ste == 'Int'
			se = ['-',se]
		elif op == ':':
			assert isinstance(e[2],int) and e[3]=='int32'
			se,ste = expr(e[2])
		else:
			_ = 2+2
			assert False,e
	elif isinstance(e, str):
		if e in ('false','true'):
			se = e == 'true'
			ste = 'Bool'
		else:
			se = e
			ste = typ(G_env_d[e])
	elif isinstance(e,int):
		se = e if e >= 0 else ['-',-e]
		ste = 'Int'
	else:
		assert False, e
	return se,ste
	

G_pack = None

def do_it(fd, so=None):
	""
	global G_env_d, G_arr_d
	if so is None:
		so = smtlib('QF_LIA')
		so.setOption(':produce-models','true')
	input_d = dict(fd['inputs'])
	output_d = dict(fd['outputs'])
	var_d = fd['var']
	G_arr_d = {v:t for v,t in var_d.items() if t[0]=='^'}
	G_arr_d.update({v:t for v,t in input_d.items() if t[0]=='^'})
	G_arr_d.update({v:t for v,t in output_d.items() if t[0]=='^'})
	G_env_d = ChainMap(var_d,input_d,output_d)
	for v,t in G_env_d.items():
		if t == 'bool':
			so.declareConst(v)
		elif t == 'int32':
			so.declareConst(v,'Int')
		else:
			assert t[0] == '^'
	for eq_i,eq in enumerate(fd['let']):
		if eq[0] == '=':
			assert len(eq[1])==1, eq
			vout = eq[1][0]
			if vout == '_': continue
			tout = G_env_d[vout]
			# assert tout in ('bool','int32'), tout
			if vout in G_arr_d:
				assert eq[2][0] in ('[',), eq
				continue
			se,ste = expr(eq[2])
			assert ste == typ(tout), eq
			so.Assert(['=',vout,se])
		else:
			assert eq[0] == 'assume'
	return so

def do_it_as_fun_BIZARRE(fn, fd, vout):
	""
	global G_env_d, G_arr_d
	so = smtlib('QF_LIA')
	so.setOption(':produce-models','true')
	input_d = dict(fd['inputs'])
	output_d = dict(fd['outputs'])
	var_d = fd['var']
	G_arr_d = {v:t for v,t in var_d.items() if t[0]=='^'}
	G_arr_d.update({v:t for v,t in input_d.items() if t[0]=='^'})
	G_arr_d.update({v:t for v,t in output_d.items() if t[0]=='^'})
	G_env_d = ChainMap(var_d,input_d,output_d)
	#
	eq_l = fd['let']
	l2ls_l = lustre_util.depend_eq_list(eq_l)
	if False:
		r = ts.toposort_flatten(dict(enumerate(l2ls_l)))
	else:
		sl = list(ts.toposort(dict(enumerate(l2ls_l))))
		assert -1 in sl[0] and sum(len(s) for s in sl) == len(eq_l)+1
		# sl[0] = sl[0] - {-1}
		r = []
		for s in sl: r.extend(sorted(s))
	assert len(r) >= 1 and (r[0]==-1 or -1 not in r), r
	assert len(r) == len(eq_l) + (r[0]==-1)
	#
	vout_t = typ(output_d[vout])
	vt_l = []
	for v,t in input_d.items():
		if t in ('bool','int32'):
			vt_l.append((v,typ(t)))
		else:
			assert t[0] == '^' and isinstance(t[1],str)
			vt_l.extend((v+'__'+str(i),typ(t[1])) for i in range(t[2]))
	e = vout
	assert r[0] == -1
	for eq_i in reversed(r[1:]):
		eq = eq_l[eq_i]
		if eq[0] == '=':
			assert len(eq[1])==1, eq
			vout = eq[1][0]
			if vout == '_': continue
			tout = G_env_d[vout]
			# assert tout in ('bool','int32'), tout
			if vout in G_arr_d:
				assert eq[2][0] in ('[',), eq
				continue
			se,ste = expr(eq[2])
			assert ste == typ(tout), eq
			e = ['let',[[vout,se]], e]
		else:
			assert eq[0] == 'assume'
	so.defineFun(fn,vt_l,vout_t,e)
	return so

def do_it_as_fun(fn, fd, vout, const_d, so=None):
	""
	global G_env_d, G_arr_d
	if so is None:
		so = smtlib('QF_LIA')
		so.setOption(':produce-models','true')
	input_d = dict(fd['inputs'])
	output_d = dict(fd['outputs'])
	var_d = fd['var']
	G_arr_d = {v:t for v,t in var_d.items() if t[0]=='^'}
	G_arr_d.update({v:t for v,t in input_d.items() if t[0]=='^'})
	G_arr_d.update({v:t for v,t in output_d.items() if t[0]=='^'})
	G_arr_d.update({v:t for v,t in const_d.items() if t[0]=='^'})
	G_env_d = ChainMap(var_d,input_d,output_d, const_d)
	#
	eq_l = fd['let']
	l2ls_l = lustre_util.depend_eq_list(eq_l)
	sl = list(ts.toposort(dict(enumerate(l2ls_l))))
	assert -1 in sl[0] and sum(len(s) for s in sl) == len(eq_l)+1
	sl[0] = sl[0] - {-1}
	#
	vout_t = typ(output_d[vout])
	vt_l = []
	for v,t in input_d.items():
		if t in ('bool','int32'):
			vt_l.append((v,typ(t)))
		else:
			assert t[0] == '^' and isinstance(t[1],str)
			vt_l.extend((v+'__'+str(i),typ(t[1])) for i in range(t[2]))
	e = vout
	for s in reversed(sl):
		dl = []
		for eq_i in s:
			eq = eq_l[eq_i]
			if eq[0] == '=':
				assert len(eq[1])==1, eq
				vout = eq[1][0]
				if vout == '_': continue
				tout = G_env_d[vout]
				if vout in G_arr_d:
					assert eq[2][0] in ('[',), eq
					continue
				se,ste = expr(eq[2])
				assert ste == typ(tout), eq
				dl.append([vout,se])
			else:
				assert eq[0] == 'assume'
		if dl:
			e = ['let',dl, e]
	so.defineFun(fn,vt_l,vout_t,e)
	return so

def list_inputs(fd):
	""
	ntl = []
	for v,t in fd['inputs']:
		if t in ('bool','int32'):
			ntl.append((v,typ(t)))
		else:
			assert t[0] == '^' and isinstance(t[1],str)
			for i in range(t[2]):
				ntl.append((v+'__'+str(i),typ(t[1])))
	return ntl

def do_file(fn, fun):
	""
	import codecs
	print('*** {} ***'.format(fn))
	#with open(fn, 'r', encoding='utf-8') as f:
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		pack = lp.parser.parse(s, debug=False)
		lustre_chk.chk_main(pack)
		pack = lustre_util.simplify_pack(pack)
		fd,const_l,_ = lustre_expand.do_pack(pack,fun)
		smtobj = smtlib('QF_LIA')
		smtobj.setOption(':produce-models','true')
		const_d = {c:pack[c]['type'] for c in const_l}
		for c in const_l:
			t = pack[c]['type']
			v = pack[c]['value']
			if t[0] == '^':
				ty,sz = t[1:]
				assert v[0] == '['
				vl = v[2]
				assert len(vl) == sz
				for i,vi in enumerate(vl):
					smtobj.defineFun(c+'__'+str(i),[],typ(ty),expr(vi)[0])
					const_d[c+'__'+str(i)] = ty
			else:
				assert False, c
		#fd,_,_ = lustre_expand.do_str(s, fun)
		if False:
			smtobj = do_it(fd, smtobj)
			smtobj.Assert('ok')
			smtobj.checkSat()
			smtobj.getValue(['offset_of_task_IN__'+str(i) for i in range(4)])
		else:
			ntl = list_inputs(fd)
			for n,t in ntl:
				smtobj.declareConst(n,t)
			_ = do_it_as_fun(fun,fd,'ok',const_d,smtobj)
			smtobj.Assert([fun]+[n for n,_ in ntl])
			smtobj.checkSat()
			smtobj.getValue([n for n,_ in ntl])
		smtobj.to_file('expand')
	else:
		print('pb')

if __name__ == "__main__":
	for fn, fun in ( \
		('test/scheduling/kcg_xml_filter_out.scade','mc_20times_2cores_4tasks'), \
		):
		result = do_file(fn, fun)
		_ = 2+2
