import lustre_par as lp

C_numeric_kind = {'numeric', 'float', 'integer', 'signed', 'unsigned'}

C_prec = [
	['.[.]','.[..]','.default','with'],
	['@'],
	['^'],
	['not','lnot'],
	['when'],
	['reverse'],
	['pre'],
	['+unaire','-unaire'], # reserve
	['*','/','mod'],
	['+','-'],
	['lsl','lsr'],
	['=','<>','<=','>=','<','>'],
	['and'],
	['or','xor'],
	['land'],
	['lor','lxor'],
	['->'],
	['if'],  ### considere comme prefix de l'expression apres 'else'
	['times']]

C_prec_d = {}
for i,ol in enumerate(C_prec):
	for o in ol:
		assert o not in C_prec_d
		C_prec_d[o] = i

def clkprb(vn,vt):
	""
	if isinstance(vt,dict):
		if 'probe' in vt:
			vn = 'probe '+vn
		if 'clock' in vt:
			vn = 'clock '+vn
	return vn

def scope(d):
	""
	body_l = []
	if True:
		signal = d.get('signal')
		var = d.get('var',{})
		let = d.get('let',[])
		if True:
			if signal:
				body_l.append('sig {};'.format(','.join(signal)))
			if var:
				body_l.append('var')
				body_l.extend('  {} : {};'.format(clkprb(vn,var[vn]), chk_type_expr(var[vn])) for vn in sorted(var))
			if signal or var or len(let) > 1:
				body_l.append('let')
			for eq in let: # = lhs rhs
				if eq[0] == '=':
					assert len(eq) in (3,4), eq
					lhs = eq[1]
					assert isinstance(lhs,list), lhs
					lhs_s = ','.join(lhs)
					rhs = eq[2]
					rhs_s,_ = chk_expr(rhs)
					if len(eq) == 4:
						assert isinstance(eq[3],dict), eq
					body_l.append('  {}= {};'.format(lhs_s,rhs_s))
				elif eq[0] == 'activate': # ACTIVATE ID_OPT if_ou_match_block
					assert len(eq) == 4 and (eq[1] == None or eq[1].isidentifier()), eq
					if eq[2][0] == 'if':
						e_s, _ = chk_expr(eq[2][1])
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
						e_s, _ = chk_expr(eq[2][1])
						for a,b in eq[2][2]:
							assert a.isidentifier(), a
							a_s,_ = chk_expr(a)
							if isinstance(b,list):
								assert b[0] == '=', b
							else:
								assert isinstance(b,dict)
								# var
								for c in b.get('let',[]):  ## parfois absent ????
									assert isinstance(c,list) and c[0] in ('=','activate'), c
					else:
						assert False, eq
					# assert all((v in out_env or v in var_env or v=='..') for v in eq[3]), eq
				elif eq[0] in ('assume','guarantee'):
					assert len(eq) == 3 and eq[1].isidentifier(), eq
					e_s,_ = chk_expr(eq[2])
					body_l.append('  {} {}: {};'.format(eq[0], eq[1],e_s))
				elif eq[0] == 'automaton':
					assert len(eq) == 4 and (eq[1] == None or eq[1].isidentifier()), eq
					body_l.append('  automaton '+(eq[1] or ''))
					for st_name,st_def in eq[2]:
						pragmas, ini_opt, fin_opt, unless_opt, data_def, until_opt = st_def
						s = 'state ' + st_name
						if fin_opt: s = 'final '+s
						if ini_opt: s = 'initial '+s
						body_l.append(s)
						sl = scope(data_def)
						body_l.extend(sl)
					#assert all((v in out_env or v in var_env or v=='..') for v in eq[3]), eq
					body_l.append('  returns {};'.format(','.join(eq[3])))
				elif eq[0] == 'emit':
					assert len(eq) == 2, eq
					_ = 2+2
				else:
					assert False
			if signal or var or len(let) > 1:
				body_l.append('tel')
	return body_l

def decl(name, d): # const function group node package sensor type
	"""
	['const', pragmas, ext, typ, val]
	['function|node',pragmas,ext,sz,p_in,p_out,tvl,spec_decl_OPT, opt_body]
	['group', pragmas, def]
	['sensor', pragmas, typ]
	['type', pragmas, ext, def, kind]
	"""
	sl = []
	if name == 'util_ClockCounter':
		_ = 2+2
	assert isinstance(d,dict), (name, d)
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
		t_s = chk_type_expr(typ)
		if not imported:
			assert value is not None
			d_s = 'const ' + name + ' : ' + t_s + ' = ' + chk_expr(value)[0] + ';'
		else:
			assert value is None
			d_s = 'const imported ' + name + ' : ' + t_s + ';'
		sl.append(d_s)
	elif kind in ('function','node'):
		#  ID pragmas interface_status  size_decl_OPT p_in p_out where_decl_OPT spec_decl_OPT opt_body
		assert {'','inputs','outputs','_lineno','inputs_linenos','outputs_linenos'} <= set(d)
		expand = any([pragma==('kcg','expand') for pragma in pragmas])
		size_decl = d.get('sizes',[])
		sizes_s = '<<'+','.join(size_decl)+'>>' if size_decl else ''
		d_s = '{}{} {}{}'.format(kind, ' imported' if imported else '', name, sizes_s)
		p_in = d['inputs']
		inputs_s = '; '.join(clkprb(vn,vt) + ' : ' + chk_type_expr(vt) for vn,vt in p_in)
		p_out = d['outputs']
		outputs_s = '; '.join(clkprb(vn,vt) + ' : ' + chk_type_expr(vt) for vn,vt in p_out)
		d_s += '({}) returns ({})'.format(inputs_s, outputs_s)
		where_l, where_k = d.get('where', ([],None))
		if where_k:
			assert where_k in C_numeric_kind
			assert len(where_l) == 1
			d_s += ' where {} {}'.format(where_l[0],where_k)
		#
		signal = d.get('signal')
		var = d.get('var',{})
		let = d.get('let')
		if imported:
			assert signal == let == None and var == {}
			d_s += ';'
			sl.append(d_s)
		else:
			assert let is not None
			sl.append(d_s)
			body_l = scope(d)
			sl.extend(body_l)
	elif kind == 'group':
		assert sorted(d) == ['','types'], sorted(d)
		types = d['types']
		assert isinstance(types,list), types
		d_s = 'group {} = ({});'.format(name, ','.join(chk_type_expr(t) for t in types))
		sl.append(d_s)
	elif kind == 'sensor':
		assert set(d) <= {'','type','#'}
		d_s = 'sensor {}: {};'.format(name, chk_type_expr(d['type']))
		sl.append(d_s)
	elif kind == 'type':
		if not imported:
			t_s = chk_type_def(d['type'])
			d_s = 'type ' + name + ' = ' + t_s + ';'
		elif len(d)==2:
			d_s = 'type imported ' + name + ';'
		elif len(d)==3:
			assert d['is'] in C_numeric_kind, d
			d_s = 'type imported ' + name + ' is ' + d['is'] + ';'
		else:
			assert False, d
		sl.append(d_s)
	else:
		assert False, kind
	return sl

G_expr_ctx = {}

def chk_expr(e, upper_prec = None):
	""
	e_s = prec = None
	if isinstance(e,list):
		op = e[0]
		if isinstance(op, str):
			prec = C_prec_d.get(op)
		if not isinstance(op, str):
			assert isinstance(op,list)
			nb_inp = -1
			if op[0] == '::':
				assert len(op) >= 3
				op_s = '::'.join(op[1:])
			elif op[0] == '<<>>':
				assert len(op) >= 3
				op_s = '(' + chk_expr(op[1])[0] + '<<'
				for x in op[2:]:
					op_s += chk_expr(x)[0] + ','
				op_s = op_s[:-1] + '>>)'
			elif op[0] == 'activate':
				"""
| ( activate operator every clock_expr ) avec clock_expr == ID | not ID | (ID match pattern)
| ( activate operator every expr default expr )
| ( activate operator every expr initial default expr )
				"""
				assert len(op) == 4
				oper_s,_ = chk_expr(op[1])
				every_s,_ = chk_expr(op[2])
				assert isinstance(op[3], dict) and list(op[3]) == ['initial'], op
				initial = op[3]['initial']
				assert len(initial) == 3 and initial[:-1] == ['(',None], initial
				init_s, _ = chk_expr(initial)
				op_s = '(activate {} every {} initial default {})'.format(oper_s, every_s, init_s)
			elif op[0] in ('flatten','make'):
				assert len(op) == 2
				t_s = chk_type_expr(op[1])
				op_s = '({} {})'.format(op[0],t_s)
			elif op[0] in ('fold','map','foldi','mapi'):
				assert len(op) == 3
				fun_s,_ = chk_expr(op[1])
				cnt_s,_ = chk_expr(op[2])
				op_s = '({} {} <<{}>>)'.format(op[0],fun_s, cnt_s)
			elif op[0] in ('mapfold','mapfoldi'):
				assert len(op) in (3,4)
				fun_s,_ = chk_expr(op[1])
				cnt_s,_ = chk_expr(op[2])
				if len(op) == 4:
					assert isinstance(op[3]['acc_nb'], int)
					op_s = '({} {} {} <<{}>>)'.format(op[0],op[3]['acc_nb'],fun_s, cnt_s)
				else:
					op_s = '({} {} <<{}>>)'.format(op[0],fun_s, cnt_s)
			elif op[0] == 'foldw':
				assert len(op) == 4
				e1_s,_ = chk_expr(op[1])
				e2_s,_ = chk_expr(op[2])
				assert isinstance(op[3],dict) and len(op[3]) == 1
				e3_s,_ = chk_expr(op[3]['if'])
				op_s = '(foldw {} <<{}>> if {})'.format(e1_s,e2_s,e3_s)
			elif op[0] == 'restart':
				assert len(op) == 3
				e1_s,_ = chk_expr(op[1])
				e2_s, _ = chk_expr(op[2])
				op_s = '(restart {} {})'.format(e1_s,e2_s)
			else:
				assert False, e
			assert nb_inp == -1 or nb_inp == len(e)-1
			e_s = op_s+'('
			for x in e[1:]:
				e_s += chk_expr(x)[0] + ','
			e_s = e_s[:-1] + ')'
		elif op == '::':
			assert len(e) >= 3
			e_s = '::'.join(e[1:])
		elif op == '<<>>':
			assert len(e) >= 3, e
			e_s = '(' + chk_expr(e[1])[0] + '<<'
			for sz in e[2:]:
				e_s += chk_expr(sz)[0] + ','
			e_s = e_s[:-1] + '>>)'
		elif op in ('-unaire','pre','reverse'): # unaires polymorphes
			assert len(e) == 3 and e[1]==None
			op_s = '-' if op[0]=='-' else op+' '
			s1,p1 = chk_expr(e[2],prec)
			e_s = op_s + s1
		elif op in ('not','real','int'): # unaires
			assert len(e) == 2
			e_s = op + ' ' + chk_expr(e[1])[0]
		elif op in ('+','-','*','/','mod','div','->','@','^'): # binaires polymorphes ou +10.0
			assert (len(e) == 4 and e[1]==None) or (len(e)==2 and op=='+'), e
			if len(e)==2:
				assert isinstance(e[1], float), e
				e_s = '+'+str(e[1])
			else:
				s1,p1 = chk_expr(e[2],prec)
				s2,p2 = chk_expr(e[3],prec)
				e_s = s1+' '+op+' '+s2 if op in ('mod','div') else s1+op+s2
		elif op in ('=','<>','<','<=','>','>='): # binaires a arguments polymorphes
			assert len(e) == 3
			e_s = chk_expr(e[1],prec)[0]+ ' '  + op+ ' '  + chk_expr(e[2],prec)[0]
		elif op in ('and','or','xor'): # binaires full static
			assert len(e) == 3
			e_s = chk_expr(e[1],prec)[0] + ' ' + op + ' ' + chk_expr(e[2],prec)[0]
		elif op in ('(','['):
			assert len(e) == 3 and e[1]==None
			assert e[2] is not None
			closing_op = ')' if op == '(' else ']'
			e_s = op + ','.join(chk_expr(expr)[0] for expr in e[2]) + closing_op
		elif op == '.[.]':
			assert len(e) == 4 and e[1]==None
			e_s = chk_expr(e[2],prec)[0] + '[' + chk_expr(e[3])[0] + ']'
		elif op == '.[..]':
			assert len(e) == 5 and e[1]==None
			e_s = chk_expr(e[2],prec)[0] + '[' + chk_expr(e[3])[0] + '..' + chk_expr(e[4])[0] + ']'
		elif op == 'fby':
			assert len(e)==5 and e[1]==None
			flow, latency, init = tuple(e[2:])
			assert isinstance(flow,list) and isinstance(latency,list) and isinstance(init,list)
			assert len(flow) == len(init) and len(latency) == 1
			if not isinstance(latency[0],(int,str)):
				assert False
			flow_s = ','.join(chk_expr(f)[0] for f in flow)
			latency_s,_ = chk_expr(latency[0])
			init_s = ','.join(chk_expr(f)[0] for f in init)
			e_s = 'fby({};{};{})'.format(flow_s, latency_s, init_s)
		elif op == 'transpose':
			assert len(e)==5 and e[1]==None
			expr, dim1, dim2 = tuple(e[2:])
			assert isinstance(expr,list) and isinstance(dim1,list) and isinstance(dim2,list)
			assert len(expr)==1 and len(dim1)==1 and len(dim2)==1
			if dim1[0]+dim2[0] != 3:
				assert False
			chk_expr(expr[0])
		elif op == '.':
			assert len(e)==4 and e[1]==None
			e_s = chk_expr(e[2])[0] + '.' + e[3]
		elif op == 'times':
			assert len(e)==3
			chk_expr(e[1], prec)
			chk_expr(e[2], prec)
		elif op == 'if':
			assert len(e)==5 and e[1]==None
			cond_s,_ = chk_expr(e[2])
			then_s,_ = chk_expr(e[3])
			else_s,_ = chk_expr(e[4], prec)
			e_s = 'if {} then {} else {}'.format(cond_s,then_s,else_s)
		elif op == 'case': # ( case expr of {{ case_expr }}+ )
			assert len(e)==4 and e[1]==None
			cond_s,_ = chk_expr(e[2])
			case_l = []
			for pat,val in e[3]:
				pat_s,_ = chk_expr(pat)
				val_s,_ = chk_expr(val)
				case_l.append(' | {} : {}'.format(pat_s,val_s))
			e_s = '(case {} of{})'.format(cond_s, ''.join(case_l))
		elif op == '{':
			assert len(e)==3 and e[1]==None
			e_s = '{'
			for field in e[2]:
				assert len(field)==2
				assert isinstance(field[0], str)
				e_s += field[0] + ': ' + chk_expr(field[1])[0] + ', '
			e_s = e_s[:-2] + '}'
		elif op == '.default':  ### ( expr . {{ index }}+ default expr )
			assert len(e)==5 and e[1]==None
			a_s,_ = chk_expr(e[2],prec)
			index_s = ''.join('['+chk_expr(acc[1])[0]+']' for acc in e[3])
			default_s,_ = chk_expr(e[4]) 	
			e_s = '({}.{} default {})'.format(a_s,index_s,default_s)
		elif op == 'with':  ### ( expr with {{ label_or_index }}+ = expr )
			assert len(e)==5 and e[1]==None
			a_s,_ = chk_expr(e[2],prec)
			index_s = ''
			for acc in e[3]:
				assert len(acc)==2
				if acc[0] == '.':
					assert isinstance(acc[1], str)
					index_s += '.'+acc[1]
				else:
					assert acc[0] == '['
					index_s += '['+chk_expr(acc[1])[0]+']'
			value_s,_ = chk_expr(e[4])
			e_s = '({} with {} = {})'.format(a_s,index_s,value_s)
			chk_expr(e[4])
		elif op == ':': # 0:'T
			assert len(e)==4 and e[1]==None
			value_s,_ = chk_expr(e[2])
			assert isinstance(e[3],str)
			e_s = '({} : {})'.format(value_s,e[3])
		elif op == 'last':
			assert len(e)==3
			assert e[1]==None
			assert isinstance(e[2],str) and e[2][0] == "'"
			e_s = op + ' ' + e[2]
		elif op == 'when':
			assert len(e)==4 and e[1]==None
			flow_s,_ = chk_expr(e[2])
			clock_s,_ = chk_expr(e[3]) # clock
			e_s = flow_s + ' when ' + clock_s
		elif op == 'merge':
			assert len(e)>=5 and e[1]==None and len(e[2])==1
			clk = e[2][0]
			clk_s,_ = chk_expr(clk)
			m_s = ';'.join(','.join(chk_expr(gi)[0] for gi in g) for g in e[3:])
			e_s = 'merge({};{})'.format(clk_s,m_s)
		elif op.isidentifier():
			e_s = op + '(' + ','.join(chk_expr(ei)[0] for ei in e[1:]) + ')'
		else:
			assert False, e
	elif isinstance(e,str):
		e_s = e
	elif isinstance(e,(float,int)):
		e_s = str(e)
	else:
		assert False, e
	if e_s is None:
		_ = 2+2
	if upper_prec is not None and prec is not None and upper_prec < prec:
		e_s = '('+e_s + ')'
	return e_s, prec

def chk_type_expr(typ0, par_env={}, collect=False):
	"""
	par_env is the local env in a function/node : sizes and generic types
	if collect, then missing type variables are added to par_env,
	            which (in this case) is a ChainMap whose 1st dict is typar_env
	"""
	td = None
	if isinstance(typ0,dict):
		assert {'type'} <= set(typ0) <= {'type','#','clock','probe','when','default','last'}
		typ = typ0['type']
	else:
		typ = typ0
	if isinstance(typ, str):
		if typ in ('bool','int','real') or \
			(typ.startswith('int') and typ[3:] in ('8','16','32','64')) or \
			(typ.startswith('uint') and typ[4:] in ('8','16','32','64')) or \
			(typ.startswith('float') and typ[5:] in ('32','64')):
			td = typ
		elif typ[0] == "'":
			td = typ
		else:
			#(td,tp) = get_declaration(typ, p_path)
			td = typ
	else:
		assert isinstance(typ, list), typ
		if typ[0]=='::':
			td = '::'.join(typ[1:])
		elif typ[0]=='{':
			assert len(typ)==2
			td = '{'
			for field in typ[1]:
				assert len(field)==2
				s = chk_type_expr(field[1], par_env, collect)
				td += '{}: {}, '.format(field[0],s)
			assert len(td) > 1
			td = td[:-2] + '}'
		elif typ[0]=='^':
			assert len(typ)==3
			s1 = chk_type_expr(typ[1])
			s2,_ = chk_expr(typ[2])
			td = '{} ^ {}'.format(s1,s2)
		else:
			assert False, typ
	if isinstance(typ0,dict):
		# clock, probe et # sont liées à l'ID, pas au type
		if 'default' in typ0:
			e_s,_ = chk_expr(typ0['default'])
			td += ' default = ' + e_s
		if 'last' in typ0:
			e_s,_ = chk_expr(typ0['last'])
			td += ' last = ' + e_s
		if 'when' in typ0:
			e_s,_ = chk_expr(typ0['when'])
			td += ' when ' + e_s
	return td

def chk_type_def(typ0):
	""
	if isinstance(typ0,dict):
		assert {'type'} <= set(typ0) <= {'type','#','clock','probe','when','default','last'}
		typ = typ0['type']
	else:
		typ = typ0
	if isinstance(typ, list) and typ[0] == 'enum':
		assert len(typ)==2 and isinstance(typ[1], list), typ0
		td = 'enum {' + ','.join(s for _,s in typ[1]) + '}'
	else:
		td = chk_type_expr(typ)
	return td

def chk_pack(name,pv):
	""
	sl = []
	if name:
		sl.append('package {}'.format(name))
	open_l = pv.get('open',[])
	for open in open_l:
		if isinstance(open,str):
			sl.append('open {};'.format(open))
		else:
			assert open[0] == '::'
			sl.append('open {};'.format('::'.join(open[1:])))
	for dn in sorted(pv):
		if dn in ('','open','package','private','#') or dn[0] == ' ': continue
		dv = pv[dn]
		sl.extend(decl(dn,dv))
	pack_d = pv.get('package',{})
	for pn in sorted(pack_d):
		sl.extend(chk_pack(pn,pack_d[pn]))
	if name:
		sl.append('end;')
	return sl

G_pack = None

def do_str(s):
	""
	global G_pack
	G_pack = lp.parser.parse(s, debug=False) 
	return chk_pack(None, G_pack)

def do_file(fn):
	""
	import codecs
	#with open(fn, 'r', encoding='utf-8') as f:
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		sl = do_str(s)
	else:
		sl = ["/* can't open {} */".format(fn)]
	return sl

if __name__ == "__main__":
	for i,fn in enumerate(( \
		'lustre_namespace_OK.scade', \
		'lustre_test_typ_OK.scade', \
		r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1905\MODEL\cvob_arrano1g4\c90100_modele\PAR\determiner_modes_generaux\sc\C_determiner_modes_generaux_KCG64\kcg_xml_filter_out.scade', \
		r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1905\MODEL\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc\C_calculer_limites_et_regimes_KCG64\kcg_xml_filter_out.scade', \
		'test/scheduling/kcg_xml_filter_out_1.scade', \
		'test/scheduling/kcg_xml_filter_out_2.scade', \
		'test/scheduling/kcg_xml_filter_out_3.scade', \
		'test/scheduling/kcg_xml_filter_out.scade', \
		)[:]):
		print('*** {} ***'.format(fn))
		sl = do_file(fn)
		fd = open('tmp{}.scade'.format(i),'w')
		fd.writelines(s+'\n' for s in sl)
		fd.close()
