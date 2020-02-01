import json, os, re, sys
from toposort import toposort_flatten
try:
	from scade_suite import run_checker
except:
	run_checker = None
import lustre_par as lp

def export_package(pack_js, path = []):
	assert pack_js[''] == 'package'
	sc_prag = pack_js.get('#',[])
	sc_open = pack_js.get('open',[])
	sc_pack = pack_js.get('package',{})
	if not all(pn in sc_pack for pn in sc_open):
		2+2
	d = {}; d1 = {}
	for k,v in pack_js.items():
		if k in ('','#','open','package'): continue
		if k in (' linenos',): continue
		if k == 'TBM':
			2+2
		if not isinstance(v,dict):
			_ = 2+2
		kind = v['']
		if   kind == 'const':
			2+2
		elif kind in ('function','node'):
			prl = []
			for vn,vt in v.get('var',{}).items():
				if isinstance(vt,dict) and 'probe' in vt:
					prl.append(vn)
			if prl != []:
				print('\t'+k + ' : '+str(prl))
				d[k] = prl
			elif path == [] and False:
				print('\t'+k + ' : '+'*********** VIDE **********')
			calls = {}
			for equ_i, equ in enumerate(v.get('let',[])):
				assert isinstance(equ,list)
				if equ[0] == '=':
					val = equ[2]
					if isinstance(val,list):
						op = val[0]
						if isinstance(op,str):
							if op.isidentifier() and op not in ('and','case','fby','if','last','mod','not','or','real','with'):
								if op in calls: print(k+ ' : multiple call : '+op)
								calls[op] = calls.get(op,[])+[equ_i]
						elif isinstance(op,list):
							assert isinstance(op[0],str)
							if op[0] in ('::','flatten','make'):
								2+2
							elif op[0] in ('activate','restart'):
								xop = op[1]
								assert isinstance(xop,str)
								if xop in calls: print(k+ ' : multiple call : '+xop)
								calls[xop] = calls.get(xop,[])+[equ_i]
							elif op[0] in ('fold','map',):
								xop = op[1]
								if isinstance(xop,str):
									if xop[0] != '$':
										if xop in calls: print(k+ ' : multiple call : '+xop)
										calls[xop] = calls.get(xop,[])+[equ_i]
								else:
									assert xop[0] == '<<>>'
									xxop = xop[1]
									assert isinstance(xxop,str)
									if xxop in calls: print(k+ ' : multiple call : '+xxop)
									calls[xxop] = calls.get(xxop,[])+[equ_i]
							elif op[0] == '<<>>':
								xop = op[1]
								assert isinstance(xop,str)
								if xop in calls: print(k+ ' : multiple call : '+xop)
								calls[xop] = calls.get(xop,[])+[equ_i]
							else:
								assert False
						else:
							assert False
			if calls != {}:
				print('\t'+k + ' calls '+str(calls))
				d1[k] = calls
		elif kind == 'sensor':
			2+2
		elif kind == 'type':
			2+2
		else:
			assert False
	for k,v in sc_pack.items():
		print('package : '+str(path)+k)
		rd, rd1 = export_package(v, path+[k])
		assert rd == {}
	return d, d1

def doit(f, out_file=None):
	""
	if isinstance(f,str) and os.path.exists(f) and f.endswith('.scade'):
		fd = open(f,'r')
		scade_sl = fd.readlines()
		fd.close()
		##
		js_file = f[:-5] + 'json'
		if not os.path.exists(js_file) or os.path.getmtime(js_file) < os.path.getmtime(f):
			print('re-generation du cache lustre.json')
			import lustre_par as lp
			scade_js = lp.parse_file(f, save_json=True)
		else:
			fd = open(js_file,'r')
			scade_js = json.load(fd)
			fd.close()
		## node : 1iere solution
#		nodes = sorted(k for k,v in scade_js.items() if isinstance(v,dict) and v.get('') == 'node')
#		if nodes:
#			node = nodes[0]
#		else:
#			functions = sorted(k for k,v in scade_js.items() if isinstance(v,dict) and v.get('') == 'function')
#			node = functions[0] if functions else None
		### node : 2ieme solution
		#m = re.fullmatch(r'.+[\\/](\w+)_KCG64[\\/]kcg_xml_filter_out\w*\.scade', f)
		#node = m.group(1) if m else None
		##
		d,d1 = export_package(scade_js)
		d2 = {k:set(v) for k,v in d1.items()}
		l = toposort_flatten(d2)
		print(l)
		node = l[-1]
		export_probes = []
		for n in l:
			has_own_probes = n in d
			has_call_probes = any(n1 in export_probes for n1 in d2.get(n,[]))
			if has_own_probes or has_call_probes:
				export_probes.append(n)
		print(export_probes)
		### contruction du type 't_probes_foo'
		types = {}
		ty_sl = []
		for n in export_probes:
			n_js = scade_js[n]
			#_lineno = n_js['_lineno']
			#inputs_linenos = n_js['inputs_linenos']
			outputs_linenos = n_js['outputs_linenos']
			scade_end_outputs = scade_sl[outputs_linenos[1]-1]
			assert scade_end_outputs.endswith(')\n')
			scade_sl[outputs_linenos[1]-1] = scade_end_outputs[:-2] + '; probes : t_probes_{})\n'.format(n)        ##### PATCH
			var_lineno = n_js['var_lineno']
			assert scade_sl[var_lineno-1].endswith('var\n')
			let_lineno = n_js['let_lineno']
			assert scade_sl[let_lineno-1].endswith('let\n')
			tel_lineno = n_js['tel_lineno']
			assert scade_sl[tel_lineno-1].endswith('tel\n')
			n_var = n_js['var']
			n_let = n_js['let']
			set_probes = ['probes = {']
			ty_own = []
			own_probes = d.get(n,[])
			for x in own_probes:
				x_ty = n_var[x]['type']
				if not isinstance(x_ty,str):
					assert isinstance(x_ty,list) and x_ty[0] == '::'
					x_ty = x_ty[1]+'::'+x_ty[2]
				ty_own.append((x,x_ty))
				set_probes.append('{0}:{0},'.format(x))			
			ty_call = []
			call_probes_locals = []
			call_probes = d1.get(n,{})
			for k,v in call_probes.items():
				assert isinstance(v,list)
				if k in export_probes:
					assert len(v) == 1
					ty_call.append((k,'t_probes_'+k))
					## ajout de la variable locale probes_pname
					call_probes_locals.append('probes_{0}:t_probes_{0};'.format(k))
					set_probes.append('{0}:probes_{0},'.format(k))	
					eq = n_let[v[0]]
					eqn = eq[3]['eq_lineno']
					scade_line = scade_sl[eqn-1]
					ind = scade_line.find('=')
					assert ind >= 0
					scade_sl[eqn-1] = scade_line[:ind] + ', probes_{} '.format(k) + scade_line[ind:]
					if isinstance(eq[2],list) and isinstance(eq[2][0], list):
						if eq[2][0][0] == 'activate':
							if 'initial default (' in scade_sl[eqn-1]: idli = eqn-1
							elif 'initial default (' in scade_sl[eqn]: idli = eqn
							elif 'initial default (' in scade_sl[eqn+1]: idli = eqn+1
							else: assert False
							id_ind = scade_sl[idli].find('initial default (')
							if ')' in scade_sl[idli][id_ind:]:
								idli1 = idli; id1_ind = scade_sl[idli1].find(')',id_ind)
							else:
								idli1 = idli+1; id1_ind = scade_sl[idli1].find(')')
								assert id1_ind >= 0
							scade_sl[idli1] = scade_sl[idli1][:id1_ind]+',default_t_probes_'+k+scade_sl[idli1][id1_ind:]
						else:
							assert False
			set_probes[-1] = set_probes[-1][:-1] + '};'
			scade_sl[let_lineno-1] = scade_sl[let_lineno-1][:-1] + ' ' + ' '.join(set_probes) + '\n'
			scade_sl[var_lineno-1] = scade_sl[var_lineno-1][:-1] + ' ' + ' '.join(call_probes_locals) + '\n'
			types[n] = (ty_own, ty_call)
			ty_sl.append('\ntype t_probes_{} = '.format(n)+'{\n')
			ty_full = ty_own+ty_call
			for a,b in ty_full[:-1]:
				ty_sl.append('\t{} : {} ,\n'.format(a,b))
			ty_sl.append('\t{} : {} '.format(*ty_full[-1])+'};\n')
			ty_sl.append('const imported default_{0} : {0};\n'.format('t_probes_'+n))
		##
		if out_file == None:
			out_file = f[:-6] + '_export_probes.scade'
		else:
			assert isinstance(out_file,str) and out_file.endswith('.scade')
		fd = open(out_file,'w')
		fd.writelines(scade_sl)
		fd.writelines(ty_sl)
		fd.close()
		##
		if node and run_checker:
			oper_list = [node]
			(retcode, stdout, stderr) = run_checker(out_file, op=','.join(oper_list))
			print('CHECKER :\nretcode = ' + str(retcode)); print('stdout = ' + stdout); print('stderr = ' + stderr)
		##
		# _js = lp.to_json(kcg_fn, kcg_fn[:-5]+'json')
	else:
		assert False, 'BAD FILE {}'.format(f)

if __name__ == '__main__':
	if len(sys.argv) != 1: ## input_scade_file
		doit(*sys.argv[1:])
	else:
		#main_dir = r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1807\MODEL'
		#prjl = ['calculer_limites_et_regimes','determiner_modes_generaux']
		#scade_file = 'kcg_xml_filter_out.scade'
		prj = 'determiner_modes_generaux'
		mdl_dir = r'\scade\Cas_etude_SafranHE_2_ATCU_S1905\MODEL\cvob_arrano1g4\c90100_modele\PAR\{}\sc'.format(prj)
		mdl_dir = 'F:'+mdl_dir
		f = mdl_dir+r'\C_{}_KCG64\kcg_xml_filter_out_with_reqs.scade'.format(prj)
		doit(f)
