# coding: utf-8
import lustre_par as lp
import lustre_path #G_prog = G_curr_pack = G_curr_path = None # liste de noms de packages
from lustre_path import get_pack_at_absolute_path, path_resolution
# INVARIANT :
# G_curr_pack == get_pack_at_absolute_path(G_curr_path)

from collections import ChainMap
################
import sys
if sys.version_info[0] == 2:
	STRING_CLASSES = (str,unicode)
else:
	STRING_CLASSES = (str,)
################

G_curr_env = G_curr_env2path = None

C_numeric_kind = {'numeric', 'float', 'integer', 'signed', 'unsigned'}

def chk_main(pack):
	""
	# global G_prog
	lustre_path.G_prog = pack
	chk_pack_enums(pack)
	chk_pack_opens(pack)

# 2
def chk_pack_opens(pack, path = [], env = {}, env2path = {}):
	"""
	elaboration des opens : nouvel attribut ' opens' (meme s'il n'y a aucun open)
	"""
	def xtype(d):
		""
		xt = d['']
		if xt == 'const':
			xt = d['type']
		return xt
	# global  G_curr_pack, G_curr_path
	global G_curr_env, G_curr_env2path
	assert isinstance(pack, dict) and pack.get('')=='package' and isinstance(path, list)
	lustre_path.G_curr_pack = pack; lustre_path.G_curr_path = path
	# open
	#open_al = []
	#open_cm = ChainMap({n:xtype(v) for n,v in pack.items() if n not in ('','open','package','#') and n[0] != ' '})
	open_cm = ChainMap(); open_cm_2path = ChainMap()
	for op in pack.get('open',[]):
		pa, pa_abs_path = path_resolution(op)
		#pa_export = {n:xtype(v) for n,v in pa.items() if n not in ('','open','package','#') and n[0] != ' ' and 'private' not in v}
		#pa_export.update({n:v['type'] for n,v in pa[' enums'].items() if 'private' not in v})
		pa_export = pa[' public']
		#open_al.append((op, pa_abs_path, pa_export))
		tmp = len(open_cm)
		#open_cm = open_cm.new_child(pa_export)
		open_cm.maps.append(pa_export)
		assert len(open_cm) == tmp + len(pa_export)
		open_cm_2path.maps.append(pa[' public2path'])
	local_env = ChainMap(pack[' decls'], open_cm)
	assert len(local_env) == len(open_cm) + len(pack[' decls'])
	G_curr_env = full_env = ChainMap(local_env, env)
	local_env2path = ChainMap(pack[' decls2path'], open_cm_2path)
	G_curr_env2path = full_env2path = ChainMap(local_env2path, env2path)
	# decl
	for dn,dv in pack.items():
		if dn in ('','open','package','private','#') or dn[0] == ' ': continue
		chk_decl(dn, dv)
	# pack
	for pn,pv in pack.get('package',{}).items():
		chk_pack_opens(pv, path+[pn], full_env, full_env2path)

# 1
def chk_pack_enums(pack, path = []):
	"""
	expansion des enums :
		- nouvel attribut ' enums' (meme s'il n'y a aucun enum)
		- nouveaux attributs ' decls' et ' public'
		- les2 xxx2path differents : profondeur pour decls, path complet pour public
	"""
	#global  G_curr_pack, G_curr_path
	assert isinstance(pack, dict) and pack.get('')=='package' and isinstance(path, list)
	#G_curr_pack = pack; G_curr_path = path
	# open
	pass
	# pack
	for pn,pv in pack.get('package',{}).items():
		chk_pack_enums(pv, path+[pn])
	# decl
	enum_dict = {}
	for dn, dv in pack.items():
		if dn in ('','open','package','private','#') or dn[0] == ' ': continue
		if dv == None:
			_ = 2+2
		if dv[''] != 'type': continue
		dt = dv.get('type')
		if not (isinstance(dt,list) and dt[0] == 'enum'): continue
		is_private = 'private' in dv
		for _, en in dt[1]:
			assert en.isidentifier() and en not in pack and en not in enum_dict
			en_decl = {'':'const', 'type':dn, 'value':en}
			if is_private:
				en_decl['private'] = None
			enum_dict[en] = en_decl
	# TBD : gerer les private
	pack[' enums'] = enum_dict
	decl_dict = {dn:dv for dn, dv in pack.items() if dn not in ('','open','package','private','#') and dn[0] != ' '}
	pack[' decls'] = ChainMap(decl_dict, enum_dict) ### WARNING : cycle
	lp = len(path)
	pack[' decls2path'] = {dn:lp for dn in pack[' decls']}
	pack[' public'] = {dn:dv for dn, dv in pack[' decls'].items() if 'private' not in dv}
	pack[' public2path'] = {dn:path for dn in pack[' public']}

G_ctx = []
G_calltree = {}

def chk_file(fn):
	""
	import codecs
	print('*** {} ***'.format(fn))
	#with open(fn, 'r', encoding='utf-8') as f:
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		result = chk_str(s)
	else:
		result = None
	return result

def chk_str(s):
	""
	global G_ctx
	olpddd = lp.parser.parse(s, debug=False)
	G_ctx = olpddd
	chk_main(olpddd) # chk_package(olpddd, [])
#	delta = objdiff.is_jsonable(olpddd)
#	if delta != None:
#		print('WARNING : KO json : '+str(delta))
#		# assert False
	return olpddd, G_calltree

def chk_decl(name, d): # const function group node package sensor type
	"""
	['const', pragmas, ext, typ, val]
	['function|node',pragmas,ext,sz,p_in,p_out,tvl,spec_decl_OPT, opt_body]
	['group', pragmas, def]
	['sensor', pragmas, typ]
	['type', pragmas, ext, def, kind]
	"""
	p_path = lustre_path.G_curr_path
	assert isinstance(d,dict), (name, d, p_path)
	kind = d['']
	private = 'private' in d
	imported = 'imported' in d
	pragmas = d.get('#',[])
	if name=='correct':
		_ = 2+2 ## debug
	if kind == 'const':
		assert {'','type'} <= set(d) <= {'','type','value','private','imported','#'}
		typ = d['type']
		value = d.get('value')
		chk_type_expr(typ)
		if not imported:
			chk_expr(value, p_path)
		else:
			assert value==None
	elif kind in ('function','node'):
		#  ID pragmas interface_status  size_decl_OPT p_in p_out where_decl_OPT spec_decl_OPT opt_body
		assert {'','inputs','outputs','_lineno','inputs_linenos','outputs_linenos'} <= set(d)
		expand = any([pragma==('kcg','expand') for pragma in pragmas])
		p_in = d['inputs']
		p_out = d['outputs']
		size_decl = d.get('sizes',[])
		where_l, where_k = d.get('where', ([],None))
		#
		signal = d.get('signal')
		var = d.get('var',{})
		let = d.get('let')
		body = (signal, var, let)
		szpar_env = {}; typar_env = {}
		par_env = ChainMap(typar_env, szpar_env) ## pour les appels a chk_type_expr
		inp_env = {}; out_env = {}; var_env = {}
		loc_env = ChainMap(par_env, inp_env, out_env, var_env)
		for vn in size_decl:
			assert vn not in szpar_env
			vt = 'int'
			szpar_env[vn] = {'':'const', 'type':vt, 'imported':None}
		### on collecte toutes les variables de type
		for vn,vt in p_in: # ID type_expr when_decl_OPT default_decl_OPT last_decl_OPT
			(td,tp) = chk_type_expr(vt, par_env, collect = True)
			assert td, d
			assert vn not in loc_env
			inp_env[vn] = {'':'const', 'type':vt, 'imported':None}
		#### fin de la collecte
		assert all(tp in typar_env for tp in where_l), d
		for vn,vt in p_out: # ID type_expr when_decl_OPT default_decl_OPT last_decl_OPT
			(td,tp) = chk_type_expr(vt, par_env)
			assert td, d
			assert vn not in loc_env
			out_env[vn] = {'':'const', 'type':vt, 'imported':None}
		#body = d[-1] # signal_block_OPT local_block_OPT equation_SC_STAR_OPT
		assert len(body)==3
		local_block = body[1] # if body[1]!=None else []
		for vn,vt in local_block.items(): # ID type_expr when_decl_OPT default_decl_OPT last_decl_OPT
			assert True
			(td,tp) = chk_type_expr(vt, par_env)
			assert td, d
			assert vn not in loc_env
			var_env[vn] = {'':'const', 'type':vt, 'imported':None}
		if body[-1] == None:
			assert imported
		else:
			assert not imported
			for eq in body[-1]: # = lhs rhs
				if eq[0] == '=':
					assert len(eq) in (3,4), eq
					lhs = eq[1]
					assert all((v in out_env or v in var_env or v == '_') for v in lhs), lhs
					rhs = eq[2]
					chk_expr(rhs, p_path, loc_env)
					if len(eq) == 4:
						assert isinstance(eq[3],dict), eq
				elif eq[0] == 'activate': # ACTIVATE ID_OPT if_ou_match_block
					assert len(eq) == 4 and (eq[1] == None or eq[1].isidentifier()), eq
					if eq[2][0] == 'if':
						chk_expr(eq[2][1], p_path, loc_env)
						bl = eq[2][2:]
						assert len(bl)==2, bl
						for b in bl:
							if isinstance(b, list):
								assert b[0] in ('=','if'), b
							else:
								assert isinstance(b,dict)
								# var
								for c in b.get('let',[]):  ## parfois absent ????
									assert isinstance(c,list) and c[0] in ('=','activate'), c
						_ = 2+2
					elif eq[2][0] == 'when':
						chk_expr(eq[2][1], p_path, loc_env)
						for a,b in eq[2][2]:
							assert a.isidentifier(), a
							chk_expr(a, p_path)
							if isinstance(b,list):
								assert b[0] == '=', b
							else:
								assert isinstance(b,dict)
								# var
								for c in b.get('let',[]):  ## parfois absent ????
									assert isinstance(c,list) and c[0] in ('=','activate'), c
					else:
						assert False, eq
					assert all((v in out_env or v in var_env or v=='..') for v in eq[3]), eq
				elif eq[0] in ('assume','guarantee'):
					assert len(eq) == 3 and eq[1].isidentifier(), eq
					chk_expr(eq[2], p_path, loc_env)
				elif eq[0] == 'automaton':
					assert len(eq) == 4 and (eq[1] == None or eq[1].isidentifier()), eq
					assert all(x in ('initial',None) for x in eq[2]), eq
					assert all((v in out_env or v in var_env or v=='..') for v in eq[3]), eq
				elif eq[0] == 'emit':
					assert False, eq
				else:
					assert False
	elif kind == 'group':
		assert sorted(d) == ['','types'], sorted(d)
		types = d['types']
		assert isinstance(types,list), types
		for t in types:
			 (td,tp) = chk_type_expr(t)
			 assert td, t
	elif kind == 'sensor':
		assert set(d) <= {'','type','#'}
		typ = d['type']
		(td,tp) = chk_type_expr(typ)
		assert td, typ
	elif kind == 'type':
		#pragmas, external, tdef, tkind = tuple(d[1:])
		#assert tkind in (None, 'numeric', 'float', 'integer', 'signed', 'unsigned')
		if not imported:
			(xtd,xtp) = chk_type_def(d['type'])
			assert xtd
			_ = 2+2
		else:
			assert len(d)==2 or (len(d)==3 and \
			  d['is'] in C_numeric_kind), d
	else:
		assert False, kind
	return (name, d)

G_expr_ctx = {}

def chk_expr(e, p_path, env={}):
	""
	if isinstance(e,list):
		op = e[0]
		if not isinstance(op, STRING_CLASSES):
			assert isinstance(op,list)
			nb_inp = -1
			if op[0] == '::':
				assert len(op) >= 3
				(pack, abs_path) = path_resolution(op[:-1])
				decl = pack[' public'].get(op[-1])
				assert decl and decl[''] in ('function','node'), decl
				nb_inp = len(decl['inputs'])
			elif op[0] == '<<>>':
				assert len(op) >= 3
				chk_expr(op[1], p_path, env)
				for x in op[2:]:
					chk_expr(x, p_path, env)
			elif op[0] == 'activate':
				assert len(op) == 4
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				assert isinstance(op[3], dict) and list(op[3]) == ['initial'], op
				initial = op[3]['initial']
				assert len(initial) == 3 and initial[:-1] == ['(',None], initial
				init_l = initial[2]
				_ = 2+2
			elif op[0] == 'flatten':
				assert len(op) == 2
				mty = op[1]
				td,_tp = chk_type_expr(mty)
				td1 = td['type']
				assert (len(td1)==2 and td1[0] == '{') or (len(td1)==3 and td1[0] == '^'), td
				nb_inp == 1
			elif op[0] in ('fold','map'):
				assert len(op) == 3
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				_ = 2+2
			elif op[0] in ('foldi','mapi'):
				assert len(op) == 3
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				_ = 2+2
			elif op[0] in ('mapfold','mapfoldi'):
				assert len(op) in (3,4)
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				if len(op) == 4:
					assert isinstance(op[3]['acc_nb'], int)
			elif op[0] == 'foldw':
				assert len(op) == 4
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				assert isinstance(op[3],dict) and len(op[3]) == 1
				chk_expr(op[3]['if'], p_path, env)
			elif op[0] == 'make':
				assert len(op) == 2
				mty = op[1]
				td,_tp = chk_type_expr(mty)
				td1 = td['type']
				assert len(td1)==2 and td1[0] == '{', td
				nb_inp = len(td1[1])
			elif op[0] == 'restart':
				assert len(op) == 3
				chk_expr(op[1], p_path, env)
				chk_expr(op[2], p_path, env)
				_ = 2+2
			else:
				assert False, e
			assert nb_inp == -1 or nb_inp == len(e)-1 
			for x in e[1:]:
				chk_expr(x, p_path, env)
		elif op == '::':
			assert len(e) >= 3
			(pack, abs_path) = path_resolution(e[:-1])
			decl = pack[' public'].get(e[-1])
			if decl:
				assert decl[''] in ('const','function'), decl
			else:
				assert False, e
		elif op == '<<>>':
			assert len(e) >= 3, e
			chk_expr(e[1], p_path, env)
			for sz in e[2:]:
				chk_expr(sz, p_path, env)
		elif op in ('-unaire','pre','reverse'): # unaires polymorphes
			assert len(e) == 3 and e[1]==None
			chk_expr(e[2], p_path, env)
		elif op in ('not','real','int'): # unaires
			assert len(e) == 2
			chk_expr(e[1], p_path, env)
		elif op in ('+','-','*','/','mod','div','->','@','^'): # binaires polymorphes ou +10.0
			assert (len(e) == 4 and e[1]==None) or (len(e)==2 and op=='+'), e
			if len(e)==2:
				assert isinstance(e[1], float), e
			else:
				chk_expr(e[2], p_path, env)
				chk_expr(e[3], p_path, env)
		elif op in ('=','<>','<','<=','>','>='): # binaires a arguments polymorphes
			assert len(e) == 3
			chk_expr(e[1], p_path, env)
			chk_expr(e[2], p_path, env)
		elif op in ('and','or','xor'): # binaires full static
			assert len(e) == 3
			chk_expr(e[1], p_path, env)
			chk_expr(e[2], p_path, env)
		elif op in ('(','['):
			if not (len(e) == 3 and e[1]==None):
				assert False
			if e[2] != None:
				assert isinstance(e[2],list)
				for expr in e[2]:
					chk_expr(expr, p_path, env)
		elif op == '.[.]':
			assert len(e) == 4 and e[1]==None
			chk_expr(e[2], p_path, env)
			chk_expr(e[3], p_path, env)
		elif op == '.[..]':
			assert len(e) == 5 and e[1]==None
			chk_expr(e[2], p_path, env)
			chk_expr(e[3], p_path, env)
			chk_expr(e[4], p_path, env)
		elif op == 'fby':
			assert len(e)==5 and e[1]==None
			flow, latency, init = tuple(e[2:])
			assert isinstance(flow,list) and isinstance(latency,list) and isinstance(init,list)
			assert len(flow) == len(init) and len(latency) == 1
			if not isinstance(latency[0],(int,)+STRING_CLASSES):
				assert False
			for i in range(len(flow)):
				chk_expr(flow[i], p_path, env)
				chk_expr(init[i], p_path, env)
		elif op == 'transpose':
			assert len(e)==5 and e[1]==None
			expr, dim1, dim2 = tuple(e[2:])
			assert isinstance(expr,list) and isinstance(dim1,list) and isinstance(dim2,list)
			assert len(expr)==1 and len(dim1)==1 and len(dim2)==1
			if dim1[0]+dim2[0] != 3:
				assert False
			chk_expr(expr[0], p_path, env)
		elif op == '.':
			assert len(e)==4 and e[1]==None
			chk_expr(e[2], p_path, env)
			assert isinstance(e[3],STRING_CLASSES)
		elif op == 'times':
			assert len(e)==3
			chk_expr(e[1], p_path, env)
			chk_expr(e[2], p_path, env)
		elif op == 'if':
			assert len(e)==5 and e[1]==None
			chk_expr(e[2], p_path, env)
			chk_expr(e[3], p_path, env)
			chk_expr(e[4], p_path, env)
		elif op == 'case':
			assert len(e)==4 and e[1]==None
			chk_expr(e[2], p_path, env)
			for match in e[3]:
				assert len(match)==2
				chk_expr(match[0], p_path, env)
				chk_expr(match[1], p_path, env)
		elif op == '{':
			assert len(e)==3 and e[1]==None
			for field in e[2]:
				assert len(field)==2
				assert isinstance(field[0], STRING_CLASSES)
				chk_expr(field[1], p_path, env)
		elif op in ('with','.default'):  ### normalement, les .dyn ont disparu -> à verifier
			assert len(e)==5 and e[1]==None
			chk_expr(e[2], p_path, env)
			for acc in e[3]:
				assert len(acc)==2
				if acc[0] == '.':
					assert isinstance(acc[1], STRING_CLASSES)
				else:
					assert acc[0] == '['
					chk_expr(acc[1], p_path, env) 	
			chk_expr(e[4], p_path, env)
		elif op == ':': # 0:'T
			assert len(e)==4 and e[1]==None
			chk_expr(e[2], p_path, env)
			assert isinstance(e[3],STRING_CLASSES)
		elif op == 'operator':
			assert len(e)==3
			chk_operator(e[1], p_path, env)
			for ei in e[2]:
				chk_expr(ei, p_path, env)
		elif op == 'last':
			assert len(e)==3
			assert e[1]==None
			assert isinstance(e[2],STRING_CLASSES)
		elif op == 'when':
			assert len(e)==4
			assert e[1]==None
			chk_expr(e[2], p_path, env)
			chk_expr(e[3], p_path, env) # clock
		elif op == 'merge':
			assert len(e)>=5 and e[1]==None and len(e[2])==1
			clk = e[2][0]
			chk_expr(clk, p_path, env)
			gr_sz = len(e[3])
			for g in e[3:]:
				assert len(g)==gr_sz
				for gi in g:
					chk_expr(gi, p_path, env)
		elif op.isidentifier():
			for ei in e[1:]:
				chk_expr(ei, p_path, env)
		else:
			assert False, e
	elif isinstance(e,STRING_CLASSES):
		if e in ('false','true','_'):
			pass
		elif e[0] == '$':
			assert e[-1] == '$' and e[1:-1] in ('=','<>','>','<','>=','<=','+','-','*','and','or','mod'), e
		elif e in env: ### prioritaire sur G_curr_env
			pass
		elif e in G_curr_env:
			pass
		else:
			assert False, e
	else:
		if not isinstance(e,(float,int)):
			_ = 2+2
			assert False, e

def get_declaration(dn, p_path): ### search in the DN (Declaration Namespace)
	""
	tp = None
	if isinstance(dn, STRING_CLASSES):
		assert dn.isidentifier(), dn
		td = G_curr_env.get(dn)
	elif isinstance(dn, list) and dn[0]=='::':
		(pack, tp) = path_resolution(dn[:-1])
		td = pack.get(dn[-1])
	else:
		assert False, (dn, p_path)
	assert td, (dn, p_path)
	return td,tp	

"""
Rappel : type_def ::= type_expr | enum_def

type_block ::= type {{ type_decl ; }}
type_decl ::= interface_status ID [[ = type_def ]] [[ is numeric_kind ]]
type_def ::= type_expr
| enum { ID {{ , ID }} }
numeric_kind ::= numeric | float | integer | signed | unsigned
type_expr ::= bool
| signed << expr >> | int8 | int16 | int32 | int64
| unsigned << expr >> | uint8 | uint16 | uint32 | uint64
| float32|float64
| char
| path_id
| typevar
| { field_decl {{ , field_decl }} }
| type_expr ^ expr
field_decl ::= ID : type_expr
"""

def chk_type_expr(typ, par_env={}, collect=False):
	"""
	par_env is the local env in a function/node : sizes and generic types
	if collect, then missing type variables are added to par_env,
	            which (in this case) is a ChainMap whose 1st dict is typar_env
	"""
	td,tp = None,None
	if isinstance(typ,dict):
		assert {'type'} <= set(typ) <= {'type','#','clock','probe','when','default','last'}
		typ = typ['type']
	if isinstance(typ, STRING_CLASSES):
		if typ in ('bool','int','real') or \
			(typ.startswith('int') and typ[3:] in ('8','16','32','64')) or \
			(typ.startswith('uint') and typ[4:] in ('8','16','32','64')) or \
			(typ.startswith('float') and typ[5:] in ('32','64')):
			td = typ
		elif typ[0] == "'":
			td = typ
			if collect:
				if typ not in par_env:
					par_env[typ] = {'':'type', 'imported':None}
			else:
				assert typ in par_env
		else:
			#(td,tp) = get_declaration(typ, p_path)
			td = G_curr_env.get(typ)
			if td:
				assert td[''] in ('type','group'), td
			else:
				assert False, typ
	else:
		assert isinstance(typ, list), typ
		if typ[0]=='::':
			# (td,tp) = get_declaration(typ, p_path)
			(pack, tp) = path_resolution(typ[:-1])
			td = pack.get(typ[-1])
			if td:
				assert td[''] in ('type','group'), td
			else:
				assert False, typ
		elif typ[0]=='enum':
			assert False, typ
			assert len(typ)==2
			td = typ
		elif typ[0]=='{':
			assert len(typ)==2
			for field in typ[1]:
				assert len(field)==2
				(ftd,ttp) = chk_type_expr(field[1], par_env, collect)
				assert ftd
			td = typ
		elif typ[0]=='^':
			assert len(typ)==3
			(btd,btp) = chk_type_expr(typ[1], par_env, collect)
			assert btd
			chk_expr(typ[2], lustre_path.G_curr_path, par_env)
			td = typ
		else:
			assert False, typ
	return td,tp

def chk_type_def(typ):
	""
	if isinstance(typ,dict):
		assert {'type'} <= set(typ) <= {'type','#','clock','probe','when','default','last'}
		typ1 = typ['type']
	else:
		typ1 = typ
	if isinstance(typ1, list) and typ1[0] == 'enum':
		assert len(typ1)==2 and isinstance(typ1[1], list), typ
		td,tp = typ, None
	else:
		td,tp = chk_type_expr(typ)
	return td,tp

if __name__ == "__main__":
	for fn in ( \
		'lustre_test_typ_OK.scade', \
		r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1905\MODEL\cvob_arrano1g4\c90100_modele\PAR\determiner_modes_generaux\sc\C_determiner_modes_generaux_KCG64\kcg_xml_filter_out.scade', \
		r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1905\MODEL\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc\C_calculer_limites_et_regimes_KCG64\kcg_xml_filter_out.scade', \
		'test/scheduling/kcg_xml_filter_out_1.scade', \
		'test/scheduling/kcg_xml_filter_out_2.scade', \
		'test/scheduling/kcg_xml_filter_out_3.scade', \
		'test/scheduling/kcg_xml_filter_out.scade', \
		):
		result = chk_file(fn)
		_ = 2+2
