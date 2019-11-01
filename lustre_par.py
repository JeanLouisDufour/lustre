import ply.yacc as yacc
# import ply2yacc
import functools
# tokens : Get the token map from the lexer.  This is required.
# lexer : permit to force yacc to use the good lexer (in case of multiple parsers)
from lustre_lex import tokens, lexer
################
import sys
if sys.version_info[0] == 2:
	__STRING_CLASSES = (str,unicode)
else:
	__STRING_CLASSES = (str,)
################
def warning(s):
	print(s)

def flatten(ll):
	"[[1,2],[],[3,4]] ->  [1,2,3,4]"
	l = functools.reduce(lambda a, l: a+l, ll, [])
	return l

def flatten_dl(dl):
	"return dict"
	dr = {}
	for d in dl:
		assert isinstance(d,dict)
		assert set(dr).isdisjoint(set(d))
		dr.update(d)
	return dr

def dl2olpddd(dl):
	"""	les d de dl sont de la forme : [ ID   visi_OPT      kind    ... ]
		sauf dans le cas : 			   [ None path          'open']
		et   dans le cas : 			   [ ID   [visi_OPT pv] 'package']
		
		NON
		
		(name, val)
	"""
	open_list = [d['id'] for _n,d in dl if d['']=='open']
	pack_env = {n:d for n,d in dl if d['']=='package'}
	decl_env = {n:d for n,d in dl if d[''] not in ('open','package')}
	assert len(open_list) + len(pack_env) + len(decl_env) == len(dl)
	if open_list != []: decl_env['open'] = open_list
	if pack_env != {}: decl_env['package'] = pack_env
	return decl_env

def type_variables(t):
	""
	if isinstance(t, __STRING_CLASSES):
		if t[0]=="'":
			return set([t])
		else:
			return set([])
	else:
		assert isinstance(t,list)
		if t[0]=='^':
			return type_variables(t[1])
		else:
			return set([])

def append_enums(tdl):
	""
	el = []
	for td in tdl:
		if isinstance(td[5],list) and td[5][0]=='enum':
			typ,visib = tuple(td[0:2])
			xl = td[5][1]
			for (pragmas,name) in xl:
				el.append([name, visib, 'const_enum', typ])
	tdl += el			

start = 'program'  ## renvoie [ol, pd, dd, visi_opt==None]

decl_cpt = 0

# precedence = (
# 	('left', 'ARROW'),
# 	('left', 'OR', 'XOR'),
# 	('left', 'AND'),
# 	('nonassoc', '=', "LTGT", '<', '>', "LTEQ", "GTEQ"),
# 	('left', '+', '-'),
# 	('left', '*', '/', 'MOD', 'DIV'),
# 	('nonassoc', 'UMINUS'),
# 	('nonassoc', 'PRE'),
# 	('nonassoc', 'REVERSE', 'INT', 'REAL'),
# 	('left', 'WHEN'),
# 	('nonassoc', 'NOT'),
# 	('left', '^'),
# 	('left', '@'),
# 	('left','DOT', '['),
# )

def p_actions(p):
	"actions : DO data_def"
	p[0] = NotImplemented
	
def p_arrow(p):
	"arrow : actions_OPT fork"
	p[0] = NotImplemented

# def p_atom_for_cast(p):
# 	"""atom_for_cast : ID
# 			| INTEGER
# 			| FLOAT
# 	"""
# 	p[0] = p[1]

def p_case_expr(p):
	"case_expr : '|' pattern ':' expr"
	p[0] = [p[2],p[4]]

def p_clock_expr(p):
	"""clock_expr : ID
		| NOT ID
		| '(' ID MATCH pattern ')'
	"""
	p[0] =	p[1] if len(p)==2 else \
			p[1:] if len(p)==3 else \
			['=',p[2],p[4]]

def p_clocked_block(p):
	"""clocked_block :	ACTIVATE ID_OPT if_block
		| 		ACTIVATE ID_OPT match_block
	"""
	p[0] = p[1:]

def p_const_block(p):
	"""const_block : CONST const_decl_SC_STAR
	"""
	p[0] = p[2] ### [(['const']+d) for d in p[2]]

def p_const_decl(p):
	"""const_decl : interface_status IDdecl ':' type_expr
		| interface_status IDdecl ':' type_expr '=' expr
	"""
	[visib,ext] = p[1]
	[pragmas, name] = p[2]
	val = {'':'const', 'type':p[4]}
	if len(p)>=7: val['value'] = p[6]
	if visib == 'private': val['private'] = None ## flag
	if ext == 'imported': val['imported'] = None ## flag
	if pragmas != []: val['#'] = pragmas
	p[0] = (name, val)

def p_control_block(p):
	"""control_block : state_machine
		| clocked_block
	"""
	p[0] = p[1]

def p_data_def(p):
	"""data_def : equation_SC
		| scope
	"""
	p[0] = p[1]

def p_data_def_OR_if_block(p):
	"""data_def_OR_if_block : data_def
		| if_block
	"""
	p[0] = p[1]

def p_decls_single(p):
	"""decls : open_decl
		| package_decl
		| user_op_decl
	"""
	p[0] = [p[1]]

def p_decls_multiple(p):
	"""decls : group_block
		| type_block
		| const_block
		| sensor_block
	"""
	p[0] = p[1]

def p_default_decl(p):
	"default_decl : DEFAULT '=' expr"
	p[0] = p[3]

def p_else_fork(p):
	"else_fork : ELSE arrow"
	p[0] = p[2]

def p_elsif_fork(p):
	"elsif_fork : ELSIF expr arrow"
	p[0] = p[2:]

def p_emission(p):
	"emission : EMIT emission_body"
	p[0] = p[1:]

def p_emission_body(p):
	"""emission_body : NAME if_expr_OPT
		| '(' NAME_SEQ ')' if_expr_OPT
	"""
	p[0] = [p[2], p[4]] if len(p)>=5 else p[1:]
						
def p_eqs(p):
	"eqs : LET equation_SC_STAR TEL"
	p[0] = (p[2], p.lineno(1), p.lineno(3))
	
def p_equation(p):
	"""equation : simple_equation
		| ASSUME ID ':' expr
		| GUARANTEE ID ':' expr
		| emission
		| control_block return
	"""
	p[0] = p[1] if len(p)==2 else (p[1]+[p[2]] if len(p)==3 else p[1:3]+[p[4]])

def p_expr_1(p):
	'expr :	  expr1 TIMES expr'
	p[0] = [p[2],p[1],p[3]]

def p_expr_2(p):
	'expr :	  expr1'
	p[0] = p[1]

def p_expr1_1(p):
	"""expr1 : IF expr1 THEN expr1 ELSE expr1
	"""
	# 		| HASH_INTEGER IF expr1 THEN expr1 ELSE expr1
	p[0] = [p[1],None,p[2],p[4],p[6]]

def p_expr1_2(p):
	'expr1 :	  expr2'
	p[0] = p[1]
	
def p_expr2_1(p):
	"""expr2 : expr2 ARROW expr2a
		| expr2a
	"""
	# 		| expr2 HASH_INTEGER ARROW expr2a
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]
	
def p_expr2a(p):
	"""expr2a : expr2a OR expr2b
		| expr2a XOR expr2b
		| expr2b
	"""
	# 		| expr2a HASH_INTEGER OR expr2b
	#		| expr2a HASH_INTEGER XOR expr2b
	p[0] = p[1] if len(p)==2 else [p[2],p[1],p[3]]
	
def p_expr2b(p):
	"""expr2b :  expr2b AND expr2c
		| expr2c
	"""
	#		| expr2b HASH_INTEGER AND expr2c
	p[0] = p[1] if len(p)==2 else [p[2],p[1],p[3]]
	
def p_expr2c(p):
	"""expr2c : expr2d '=' expr2d
		| expr2d LTGT expr2d
		| expr2d '<' expr2d
		| expr2d '>' expr2d
		| expr2d LTEQ expr2d
		| expr2d GTEQ expr2d
		| expr2d
	"""
	#		| expr2d HASH_INTEGER '=' expr2d
	#		| expr2d HASH_INTEGER LTGT expr2d
	#		| expr2d HASH_INTEGER '<' expr2d
	#		| expr2d HASH_INTEGER '>' expr2d
	#		| expr2d HASH_INTEGER LTEQ expr2d
	#		| expr2d HASH_INTEGER GTEQ expr2d
	p[0] = p[1] if len(p)==2 else [p[2],p[1],p[3]]

def p_expr2d(p):
	"""expr2d : expr2d '+' expr2e
		| expr2d '-' expr2e
		| expr2e
	"""
	#		| expr2d HASH_INTEGER '+' expr2e
	#		| expr2d HASH_INTEGER '-' expr2e
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]

def p_expr2e(p):
	"""expr2e : expr2e '*' expr2f
		| expr2e '/' expr2f
		| expr2e MOD expr2f
		| expr2e DIV expr2f
		| expr2f
	"""
	#		| expr2e HASH_INTEGER '*' expr2f
	#		| expr2e HASH_INTEGER '/' expr2f
	#		| expr2e HASH_INTEGER MOD expr2f
	#		| expr2e HASH_INTEGER DIV expr2f
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]

def p_expr2f(p):
	"""expr2f : '-' expr2f
		| '+' expr2f
		| PRE expr2f
		| REVERSE expr2f
		| INT expr2f
		| REAL expr2f
		| expr2g
	"""
	#		| HASH_INTEGER '-' expr2f
	#		| HASH_INTEGER PRE expr2f
	#		| HASH_INTEGER REVERSE expr2f
	#		| HASH_INTEGER INT expr2f
	#		| HASH_INTEGER REAL expr2f
	p[0] =	p[1] if len(p)==2 else \
			['-unaire',None,p[2]] if p[1]=='-' else \
			[p[1],None,p[2]] if p[1] in ('pre','reverse') else \
			p[1:]

def p_expr2g(p):
	"""expr2g :	expr2g WHEN clock_expr
		| expr2h
	"""
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]
	
def p_expr2h(p):
	"""expr2h : NOT expr2h
		| expr2i
	"""
	#		| HASH_INTEGER NOT expr2h
	p[0] = p[1] if len(p)==2 else p[1:]
	
def p_expr2i(p):
	"""expr2i : expr2i '^' expr2j
		| expr2j
	"""
	#		| expr2i HASH_INTEGER '^' expr2j
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]
	
def p_expr2j(p):
	"""expr2j : expr2j '@' expr2k
		| expr2k
	"""
	#		| expr2j HASH_INTEGER '@' expr2k
	p[0] = p[1] if len(p)==2 else [p[2],None,p[1],p[3]]

def p_expr2k(p):
	"""expr2k : expr2k DOT ID
		| expr2k DOT label_or_index
		| expr2k '[' expr ']'
		| expr2k '[' expr DOTDOT expr ']'
		| expr2x
	"""
	#		| expr2k HASH_INTEGER DOT ID
	#		| expr2k HASH_INTEGER DOT label_or_index
	#		| expr2k HASH_INTEGER '[' expr ']'
	#		| expr2k HASH_INTEGER '[' expr_range ']'
	##### .dyn est temporaire, et sera remplace par un .default
	p[0] =	p[1] if len(p)==2 else \
			['.dyn',None,p[1],p[3]] if len(p)==4 and isinstance(p[3],list) else \
			['.'   ,None,p[1],p[3]] if len(p)==4                           else \
			['.[.]',None,p[1],p[3]] if len(p)==5 else \
			['.[..]',None,p[1],p[3],p[5]]

def p_expr2x_1(p):
	"""expr2x : '[' expr_SEQ_OPT ']'
		| '{' label_expr_SEQ '}'
		| '(' expr_SEQ_OPT ')'
		| LAST NAME
	"""
	#		| HASH_INTEGER '[' expr_SEQ_OPT ']'
	#		| HASH_INTEGER '{' label_expr_SEQ '}'
# 	"""expr2 : '-' expr2   	%prec UMINUS
# 			| HASH_INTEGER '-' expr2   	%prec UMINUS
# 			| HASH_INTEGER_OPT NOT expr2
# 			| HASH_INTEGER_OPT PRE expr2
# 			| HASH_INTEGER_OPT REVERSE expr2
# 			| HASH_INTEGER_OPT INT expr2
# 			| HASH_INTEGER_OPT REAL expr2
# 			| HASH_INTEGER_OPT '[' expr_SEQ_OPT ']'
# 			| HASH_INTEGER_OPT '{' label_expr_SEQ '}'
# 			| '(' expr_SEQ_OPT ')'
# 			| LAST NAME
# 	"""
	p[0] = [p[1],None,p[2]]

def p_expr2x_3(p):
	"expr2x : '(' expr2k DEFAULT expr ')'"
	#"expr2 : '(' expr2 HASH_INTEGER_OPT DOT label_or_index label_or_index_STAR DEFAULT expr ')'"
	access_list = []
	e = p[2]
	while isinstance(e,list) and e[0] in ('.','.[.]'):
		assert len(e)==4
		access_kind = '.' if e[0]=='.' else '['
		access_list = [[access_kind,e[3]]] + access_list
		e = e[2]
	if not (isinstance(e,list) and e[0] in ('.dyn',)):
		assert False
	assert len(e)==4
	p[0] = ['.default', None, e[2], [e[3]]+access_list, p[4]]

def p_expr2x_4(p):
	"expr2x : '(' expr WITH label_or_index_PLUS '=' expr ')'"
	p[0] = [p[3], None, p[2], p[4],p[6]]

def p_expr2x_5(p):
	"expr2x : '(' CASE expr OF case_expr_PLUS ')'"
	# '(' HASH_INTEGER CASE expr OF case_expr_PLUS ')'
	p[0] = [p[2], None, p[3], p[5]]
	
def p_expr2x_6(p):
	"expr2x : HASH '(' expr_SEQ ')'"
	p[0] = [p[1]]+p[3]

def p_expr2x_7(p):
	"expr2x : '(' expr2 ':' type_expr ')'"
	# '(' expr2 HASH_INTEGER ':' type_expr ')'
	p[0] = [p[3],None, p[2],p[4]]
	
def p_expr2x_last(p):
	'expr2x :	  expr3'
	p[0] = p[1]

def p_expr3_1(p):
	"""expr3 : path_id
			| NAME
			| CHAR
			| INTEGER
			| FLOAT
	"""
	p[0] = p[1]

# def p_expr3_2(p): ###  3 extensions : au-dela de typevar pour int8, uint64, ... + au dela de INTEGER pour <<param>> et 0.0
# 	"""expr3 : '(' INTEGER ':' typevar ')'
# 		| '(' INTEGER HASH_INTEGER_COLON typevar ')'
# 		| '(' INTEGER ':' ID ')'
# 		| '(' INTEGER HASH_INTEGER_COLON ID ')'
# 		| '(' ID HASH_INTEGER_COLON ID ')'
# 	"""
# 	p[0] = p[1]

# def p_expr3_2(p): ###  3 extensions : au-dela de typevar pour int8, uint64, ... + au dela de INTEGER pour <<param>> et 0.0
# 	"""expr3 : '(' atom_for_cast ':' typevar ')'
# 		| '(' atom_for_cast HASH_INTEGER_COLON typevar ')'
# 		| '(' atom_for_cast ':' ID ')'
# 		| '(' atom_for_cast HASH_INTEGER_COLON ID ')'
# 		| '(' '-' atom_for_cast HASH_INTEGER_COLON typevar ')'
# 	"""
# 	p[0] = p[1]


def p_expr3_3(p):
	"expr3 : operator '(' expr_SEQ_SEQ_OPT ')'" ## inclut fby, merge et transpose
	op = p[1]
	args = p[3]
	if op in ('fby', 'merge', 'transpose'):
		assert len(args)>=3
		p[0] = [op,None]+args
	elif args == None:
		p[0] = [op]
	else:
		assert isinstance(args,list) and len(args)==1
		p[0] = [op] + args[0]
	
# def p_expr_range(p):
# 	"expr_range : expr DOTDOT expr"
# 	p[0] = [p[2],p[1],p[3]]

def p_external(p):
	"external : IMPORTED"
	p[0] = p[1]

def p_field_decl(p):
	"field_decl : IDdecl ':' type_expr"
	[pragmas, name] = p[1]
	if pragmas != []:
		warning('lustre_par: field_decl: ignoring pragmas: '+' | '.join(pragmas))
	p[0] = (name,p[3])

def p_fork(p):
	"""fork : target
		| IF expr arrow elsif_fork_STAR else_fork_OPT END
	"""
	p[0] = p[1]

def p_group_block(p):
	"group_block : GROUP group_decl_SC_STAR"
	p[0] = p[2] ## [(['group']+d) for d in p[2]]

def p_group_decl(p):
	"""group_decl : visibility_OPT IDdecl '=' '(' type_expr_SEQ ')'
	"""
	[pragmas, name] = p[2]
	val = {'':'group', 'types':p[5]}
	if p[1] == 'private': val['private'] = None
	if pragmas != []: val['#'] = pragmas
	p[0] = (name, val)

def p_IDdecl(p):
	"IDdecl : HASH_PRAGMA_STAR ID"
	p[0] = p[1:]
	
def p_if_block(p):
	"""if_block : IF expr THEN HASH_PRAGMA_STAR data_def_OR_if_block ELSE HASH_PRAGMA_STAR data_def_OR_if_block
	"""
	p[0] = [p[1],p[2],p[5],p[8]]

def p_if_expr(p):
	"if_expr : IF expr"
	p[0] = p[2]
	
def p_interface_status(p):
	"interface_status : visibility_OPT external_OPT"
	p[0] = p[1:]

def p_iterator(p):
	"""iterator : MAP
		| FOLD
		| MAPFOLD
		| MAPFOLD INTEGER
		| MAPI
		| FOLDI
		| MAPFOLDI
		| MAPFOLDI INTEGER
	"""
	if len(p)>2:
		print('WARNING : '+str(p[1:]))
	p[0] = p[1] # if len(p)==2 else p[1:]

def p_label_expr(p):
	"label_expr : ID ':' expr"
	p[0] = [p[1],p[3]]

def p_label_or_index(p):
	"""label_or_index : DOT ID
		| '[' expr ']'
	"""
	p[0] = p[1:3]

def p_last_decl(p):
	"last_decl : LAST '=' expr"
	p[0] = p[3]
	
def p_lhs(p):
	"""lhs :	  '(' ')'
		| lhs_id_SEQ
	"""
	p[0] = p[1] if len(p)==2 else []

def p_lhs_id(p):
	"""lhs_id : ID
		| '_'
	"""
	p[0] = p[1]

def p_local_block(p):
	"local_block : VAR var_decls_SC_STAR"
	dl = flatten(p[2])
	dd = {n:v for (n,v) in dl}
	assert len(dl) == len(dd)
	p[0] = (dd, p.lineno(1))

def p_match_block(p):
	"match_block : WHEN expr MATCH match_data_def_PLUS"
	p[0] = ['when',p[2],p[4]]

def p_match_data_def(p):
	"match_data_def : '|' pattern ':' data_def"
	p[0] = [p[2],p[4]]

def p_numeric_kind(p):
	"numeric_kind : ID" # numeric | float | integer | signed | unsigned
	p[0] = p[1]

def p_op_kind(p):
	"""op_kind : FUNCTION
		| NODE
	"""
	p[0] = (p[1],p.lineno(1))

def p_open_decl(p):
	"open_decl : OPEN path_id ';'"
	p[0] = (None, {'':'open', 'id': p[2]})

def p_operator_1(p):
	"""operator : prefix
		| '(' prefix LTLT expr_SEQ_OPT GTGT ')'
		| '(' MAKE path_id ')'
		| '(' FLATTEN path_id ')'
	"""
	#		| '(' HASH_INTEGER iterator operator LTLT expr GTGT ')'
	if len(p)==2: # prefix  :  path_id ou PREFIXOP
		p[0] = p[1]
	elif len(p)==5: # MAKE/FLATTEN
		p[0] = p[2:4]
	else:
		p[0] = ['<<>>',p[2]] + p[4]

def p_operator_2(p):
	"""operator : '(' ACTIVATE operator EVERY clock_expr ')'
		| '(' ACTIVATE operator EVERY expr DEFAULT expr ')'
		| '(' ACTIVATE operator EVERY expr INITIAL DEFAULT expr ')'
	"""
	if len(p)>=9:
		val = {p[6] : p[len(p)-2]}
		p[0] = [p[2],p[3],p[5], val]
	else:
		p[0] = [p[2],p[3],p[5]]

def p_operator_3(p):
	"""operator : '(' RESTART operator EVERY expr ')'"""
	p[0] = [p[2],p[3],p[5]]

def p_operator_4(p):
	"""operator : '(' iterator operator LTLT expr GTGT ')'
		| '(' MAPW operator LTLT expr GTGT IF expr DEFAULT expr ')'
		| '(' MAPWI operator LTLT expr GTGT IF expr DEFAULT expr ')'
		| '(' FOLDW operator LTLT expr GTGT IF expr ')'
		| '(' FOLDWI operator LTLT expr GTGT IF expr ')'
	"""
	if len(p) >= 9:
		val = {'if':p[8]}
		if len(p) >= 11: val['default'] = p[10]
		p[0] = [p[2],p[3],p[5], val]
	else:
		p[0] = [p[2],p[3],p[5]]
		
def p_opt_body(p):
	"""opt_body : ';'
		| equation SC_OPT
		| signal_block_OPT local_block_OPT eqs SC_OPT
	"""
	### initialement :
	### equation_SC
	### signal_block_OPT local_block_OPT LET equation_SC_STAR TEL SC_OPT
	if len(p)==2:
		p[0] = {}
	elif len(p)==3:
		p[0] = {'let':[p[1]]}
	else:
		body = {}
		if p[1]!=None: body['signal'] = p[1]
		if p[2]!=None:
			var, vl = p[2]
			body['var'] = var
			body['var_lineno'] = vl
		if p[3]!=None:
			eqs, ll,tl = p[3]
			body['let'] = eqs
			body['let_lineno'] = ll
			body['tel_lineno'] = tl
		p[0] = body

def p_package_decl(p):
	"package_decl : PACKAGE visibility_OPT IDdecl decls_STAR END ';'"
	dl = flatten(p[4])
	val = dl2olpddd(dl)
	val[''] = 'package'
	[pragmas, name] = p[3]
	if p[2] == 'private': val['private'] = None ## flag
	if pragmas != []: val['#'] = pragmas
	p[0] = (name, val)

def p_params(p):
	"params : '(' var_decls_SEQ_OPT ')'"
	p[0] = ( (flatten(p[2]) if p[2] != None else []), (p.lineno(1),p.lineno(3)) )

# def p_path(p): ### renvoie  une liste
# 	"""path : ID
# 			| path COLONCOLON ID
# 	"""
# 	if len(p)==2:
# 		p[0] = [p[1]]
# 	else:
# 		p[0] = p[1]+[p[3]]

def p_path(p): ### renvoie une chaine ou une liste commencant par ::
	"""path : ID
			| ID COLONCOLON path
	"""
	if len(p)==2:
		p[0] = p[1]
	else:
		path = p[3]
		if isinstance(path,list):
			assert path[0]=='::'
			p[0] = ['::', p[1]] + path[1:] # on enleve le ::
		else:
			p[0] = ['::', p[1], path] 
	
def p_path_id(p): ### renvoie soit une chaine, soit un ::
	"path_id : path"
	p[0] = p[1]   # [0] if len(p[1])==1 else ['::']+p[1]

def p_pattern(p):
	"""pattern : path_id
		| CHAR
		| INTEGER
		| '-' INTEGER
		| '_'
	"""
	p[0] = p[1] if len(p)==2 else ['-unaire', None, p[2]]

def p_prefix(p):	# HASH_INTEGER_OPT
	"""prefix : path_id
		|  PREFIXOP
		| HASH_PRAGMA prefix
	"""
	p[0] = p[1] if len(p)==2 else p[2]

# def p_prefix(p):	# S/R
# 	"""prefix : HASH_PRAGMA_STAR path_id
# 		|  HASH_PRAGMA_STAR PREFIXOP
# 	"""
# 	p[0] = p[2]
		
def p_program(p):
	"program : decls_STAR"
	dl = flatten(p[1])
	dd = dl2olpddd(dl)
	dd[''] = 'package'
	p.lexer.lineno = 1
	p[0] = dd

def p_return(p):
	"return : RETURNS returns_var"
	p[0] = p[2]

def p_returns_var(p):
	"""returns_var : ID
		| DOTDOT
		| ID ',' returns_var
	"""
	p[0] = [p[1]] if len(p)==2 else [p[1]]+p[3]

def p_scope(p):
	"scope : signal_block_OPT local_block_OPT eqs_OPT"
	body = {}
	if p[1]!=None: body['signal'] = p[1]
	if p[2]!=None:
		var, vl = p[2]
		body['var'] = var
		body['var_lineno'] = vl
	if p[3]!=None:
		eqs, ll,tl = p[3]
		body['let'] = eqs
		body['let_lineno'] = ll
		body['tel_lineno'] = tl
	p[0] = body

def p_sensor_block(p):
	"sensor_block : SENSOR sensor_decl_SC_STAR"
	p[0] = flatten(p[2])

def p_sensor_decl(p):
	"sensor_decl : IDdecl_SEQ ':' type_expr"
	p_ty = p[3]
	p[0] = [(name,{'':'sensor', 'type':p_ty, '#':pragmas}) for [pragmas,name] in p[1]]

def p_signal_block(p):
	"signal_block : SIG ID_SEQ ';'"
	p[0] = p[2]
	
def p_simple_equation(p):
	"simple_equation : lhs HASH_PRAGMA_STAR '=' expr"
	attr = {'eq_lineno': p.lineno(3)}
	if p[2] != []:
		attr['#'] = p[2]
	p[0] = ['=', p[1], p[4], attr]

def p_size_decl(p):
	"size_decl : LTLT ID_SEQ_OPT GTGT"
	p[0] = p[2]

def p_spec_decl(p):
	"spec_decl : SPECIALIZE path_id"
	p[0] = p[2]
	
def p_state_decl(p):
	"state_decl : INITIAL_OPT FINAL_OPT STATE ID unless_trans_OPT data_def until_trans_OPT"
	p[0] = p[1]   ### BAD

def p_state_machine(p):
	"state_machine : AUTOMATON ID_OPT state_decl_PLUS"
	p[0] = p[1:]

def p_synchro_trans(p):
	"synchro_trans : SYNCHRO actions_OPT fork ';'"
	p[0] = p[1]   ### BAD
	
def p_target(p):
	"""target : RESTART ID
		| RESUME ID
	"""
	p[0] = p[1]
	
def p_transition(p):
	"transition : IF expr arrow"
	p[0] = p[1]   ### BAD
	
def p_type_block(p):
	"type_block : TYPE type_decl_SC_STAR"
	tdl = p[2]
	if False:
		append_enums(tdl)
	p[0] = tdl

def p_type_decl(p):
	"type_decl : interface_status IDdecl type_decl_def_OPT type_decl_kind_OPT"
	[visib,ext] = p[1]
	[pragmas, name] = p[2]
	val = {'':'type'}
	if visib == 'private': val['private'] = None
	if ext == 'imported': val['imported'] = None
	if pragmas != []: val['#'] = pragmas
	if p[3] != None: val['type'] = p[3]
	if p[4] != None: val['is'] = p[4]
	p[0] = (name, val)
	
def p_type_decl_def(p):
	"type_decl_def : '=' type_def"
	p[0] = p[2] 

def p_type_decl_kind(p):
	"type_decl_kind : IS ID"
	p[0] = p[2] 
	
def p_type_def(p):
	"""type_def : type_expr
		| ENUM '{' IDdecl_SEQ '}'
	"""
	p[0] = p[1] if len(p)==2 else ['enum', p[3]]

def p_type_expr(p):
	"""type_expr : path_id
		| INT
		| REAL
		| CHAR
		| typevar
		| '{' field_decl_SEQ '}'
		| type_expr '^' expr2j
	"""
	if len(p)==2:
		p[0] = p[1]
	elif p[1]=='{':
		p[0] = p[1:3]
	else:
		assert(p[2]=='^')
		p[0] = [p[2],p[1],p[3]]

def p_typevar(p):
	"typevar : NAME"
	p[0] = p[1]   ### BAD

def p_unless_trans(p):
	"unless_trans : UNLESS transition_SC_PLUS"
	p[0] = p[1]   ### BAD

def p_until_trans(p):
	"until_trans : UNTIL transition_SC_STAR synchro_trans_OPT"
	p[0] = p[2:]
	
def p_user_op_decl(p):
	"""user_op_decl : op_kind interface_status IDdecl size_decl_OPT params RETURNS params where_decl_OPT spec_decl_OPT opt_body
	"""
	(kind, _lineno) = p[1]
	[visib,ext] = p[2]
	[pragmas, name] = p[3]
	ty_vars = set([])
	p_sz = p[4]
	(p_in, in_linenos) = p[5]
	(p_out, out_linenos) = p[7]
	p_where = p[8]
	val = {'':kind, 'inputs':p_in, 'outputs':p_out, '_lineno':_lineno, 'inputs_linenos': in_linenos, 'outputs_linenos': out_linenos}
	if visib == 'private': val['private'] = None
	if ext == 'imported': val['imported'] = None
	if pragmas != []: val['#'] = pragmas
	if p_sz != None: val['sizes'] = p_sz
	if p_where != None: val['where'] = p_where
	for [vn,vv] in p_in+p_out:
		# assert len(vd)==2
		if isinstance(vv,dict):
			vv = vv['type']
		ty_vars |= type_variables(vv)
	where_vars, where_kind = p[8] if p[8]!=None else ([],'')
	assert ty_vars >= set(where_vars)
	if p[9] != None: val['specialize'] = p[9]
	if p[10] != None: val.update(p[10])
	tvl = [[tn,(where_kind if tn in where_vars else '')] for tn in ty_vars]
	# TBC
	p[0] = (name, val)

## il faut garder l'ordre car c'est utilise dans params
def p_var_decls(p):
	"var_decls : var_id_SEQ ':' type_expr when_decl_OPT default_decl_OPT last_decl_OPT"
	v_basic = p[4]==None and p[5]==None and p[6]==None
	vl = []
	for (name, va) in p[1]:
		assert all(name != n for (n,v) in vl)
		if v_basic and va == {}:
			va = p[3]
		else:
			va['type'] = p[3]
			if p[4] != None: va['when'] = p[4]
			if p[5] != None: va['default'] = p[5]
			if p[6] != None: va['last'] = p[6]
		vl.append([name, va])
	p[0] = vl

def p_var_id(p):
	"var_id : CLOCK_OPT PROBE_OPT IDdecl"
	[pragmas, name] = p[3]
	va = {}
	if p[1] != None: va['clock'] = None
	if p[2] != None: va['probe'] = None
	if pragmas != []: va['#'] = pragmas
	p[0] = (name, va)

def p_visibility(p):
	"""visibility : PRIVATE
		| PUBLIC
	"""
	p[0] = p[1]

def p_when_decl(p):
	"when_decl : WHEN clock_expr"
	p[0] = p[2]
	
def p_where_decl(p):
	"where_decl : WHERE typevar_SEQ numeric_kind"
	p[0] = p[2:]
	
#########  regles automatiques   ###########

def p_actions_OPT(p):
	"""actions_OPT :
		| actions
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_case_expr_PLUS(p):
	"""case_expr_PLUS : case_expr
		| case_expr_PLUS case_expr
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else [p[1]]

def p_CLOCK_OPT(p):
	"""CLOCK_OPT :
		| CLOCK
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_const_decl_SC(p):
	"const_decl_SC : const_decl ';'"
	p[0] = p[1]

def p_const_decl_SC_STAR(p):
	"""const_decl_SC_STAR :
		| const_decl_SC_STAR const_decl_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_decls_STAR(p):
	"""decls_STAR :
		| decls_STAR decls
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_default_decl_OPT(p):
	"""default_decl_OPT :
		| default_decl
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_else_fork_OPT(p):
	"""else_fork_OPT :
		| else_fork
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_elsif_fork_STAR(p):
	"""elsif_fork_STAR :
		| elsif_fork_STAR elsif_fork
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_eqs_OPT(p):
	"""eqs_OPT :
		| eqs
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_equation_SC(p):
	"equation_SC : equation ';'"
	p[0] = p[1]

def p_equation_SC_STAR(p):
	"""equation_SC_STAR :
		| equation_SC_STAR equation_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_expr_SEQ(p):
	"""expr_SEQ : expr
		| expr_SEQ ',' expr
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_expr_SEQ_OPT(p):
	"""expr_SEQ_OPT :
		| expr_SEQ
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_expr_SEQ_SEQ(p):
	"""expr_SEQ_SEQ : expr_SEQ
		| expr_SEQ_SEQ ';' expr_SEQ
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_expr_SEQ_SEQ_OPT(p):
	"""expr_SEQ_SEQ_OPT :
		| expr_SEQ_SEQ
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_external_OPT(p):
	"""external_OPT :
		| external
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_field_decl_SEQ(p):
	"""field_decl_SEQ : field_decl
		| field_decl_SEQ ',' field_decl
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_FINAL_OPT(p):
	"""FINAL_OPT :
		| FINAL
	"""
	p[0] = p[1] if len(p)>=2 else None
	
def p_group_decl_SC(p):
	"group_decl_SC : group_decl ';'"
	p[0] = p[1]

def p_group_decl_SC_STAR(p):
	"""group_decl_SC_STAR :
		| group_decl_SC_STAR group_decl_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

# def p_HASH_INTEGER_OPT(p):
# 	"""HASH_INTEGER_OPT :
# 		| HASH_INTEGER	
# 	"""
# 	p[0] = p[1] if len(p)>=2 else None

def p_HASH_PRAGMA_STAR(p):
	"""HASH_PRAGMA_STAR :
		| HASH_PRAGMA_STAR HASH_PRAGMA	
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []
	
def p_ID_OPT(p):
	"""ID_OPT :
		| ID
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_ID_SEQ(p):
	"""ID_SEQ : ID
		| ID_SEQ ',' ID
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]
	
def p_IDdecl_SEQ(p):
	"""IDdecl_SEQ : IDdecl
		| IDdecl_SEQ ',' IDdecl
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_ID_SEQ_OPT(p):
	"""ID_SEQ_OPT :
		| ID_SEQ
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_if_expr_OPT(p):
	"""if_expr_OPT :
		| if_expr
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_INITIAL_OPT(p):
	"""INITIAL_OPT :
		| INITIAL
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_label_expr_SEQ(p):
	"""label_expr_SEQ : label_expr
		| label_expr_SEQ ',' label_expr
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_label_or_index_PLUS(p):
	"""label_or_index_PLUS : label_or_index
		| label_or_index_PLUS label_or_index
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else [p[1]]
	
# def p_label_or_index_STAR(p):
# 	"""label_or_index_STAR :
# 		| label_or_index_STAR label_or_index
# 	"""
# 	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_last_decl_OPT(p):
	"""last_decl_OPT :
		| last_decl
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_lhs_id_SEQ(p):
	"""lhs_id_SEQ : lhs_id
		| lhs_id_SEQ ',' lhs_id
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_local_block_OPT(p):
	"""local_block_OPT :
		| local_block
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_match_data_def_PLUS(p):
	"""match_data_def_PLUS : match_data_def
		| match_data_def_PLUS match_data_def
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else [p[1]]

def p_NAME_SEQ(p):
	"""NAME_SEQ : NAME
		| NAME_SEQ ',' NAME
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_PROBE_OPT(p):
	"""PROBE_OPT :
		| PROBE
	"""
	p[0] = p[1] if len(p)>=2 else None
	
def p_SC_OPT(p):
	"""SC_OPT :
		| ';'
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_sensor_decl_SC(p):
	"sensor_decl_SC : sensor_decl ';'"
	p[0] = p[1]

def p_sensor_decl_SC_STAR(p):
	"""sensor_decl_SC_STAR :
		| sensor_decl_SC_STAR sensor_decl_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_signal_block_OPT(p):
	"""signal_block_OPT :
		| signal_block
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_size_decl_OPT(p):
	"""size_decl_OPT :
		| size_decl
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_spec_decl_OPT(p):
	"""spec_decl_OPT :
		| spec_decl
	"""
	p[0] = p[1] if len(p)>=2 else None
	
def p_state_decl_PLUS(p):
	"""state_decl_PLUS : state_decl
		| state_decl_PLUS state_decl
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else [p[1]]

def p_synchro_trans_OPT(p):
	"""synchro_trans_OPT :
		| synchro_trans
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_transition_SC(p):
	"transition_SC : transition ';'"
	p[0] = p[1]
	
def p_transition_SC_PLUS(p):
	"""transition_SC_PLUS : transition_SC
		| transition_SC_PLUS transition_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else [p[1]]
	
def p_transition_SC_STAR(p):
	"""transition_SC_STAR :
		| transition_SC_STAR transition_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []
	
def p_type_decl_def_OPT(p):
	"""type_decl_def_OPT :
		| type_decl_def
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_type_decl_kind_OPT(p):
	"""type_decl_kind_OPT :
		| type_decl_kind
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_type_decl_SC(p):
	"type_decl_SC : type_decl ';'"
	p[0] = p[1]

def p_type_decl_SC_STAR(p):
	"""type_decl_SC_STAR :
		| type_decl_SC_STAR type_decl_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_type_expr_SEQ(p):
	"""type_expr_SEQ : type_expr
		| type_expr_SEQ ',' type_expr
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_typevar_SEQ(p):
	"""typevar_SEQ : typevar
		| typevar_SEQ ',' typevar
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_unless_trans_OPT(p):
	"""unless_trans_OPT :
		| unless_trans
	"""
	p[0] = p[1] if len(p)>=2 else None
	
def p_until_trans_OPT(p):
	"""until_trans_OPT :
		| until_trans
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_var_decls_SC(p):
	"var_decls_SC : var_decls ';'"
	p[0] = p[1]

def p_var_decls_SC_STAR(p):
	"""var_decls_SC_STAR :
		| var_decls_SC_STAR var_decls_SC
	"""
	p[0] = p[1]+[p[2]] if len(p)>=3 else []

def p_var_decls_SEQ(p):
	"""var_decls_SEQ : var_decls
		| var_decls_SEQ ';' var_decls
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_var_decls_SEQ_OPT(p):
	"""var_decls_SEQ_OPT :
		| var_decls_SEQ
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_var_id_SEQ(p):
	"""var_id_SEQ : var_id
		| var_id_SEQ ',' var_id
	"""
	p[0] = p[1]+[p[3]] if len(p)>=4 else [p[1]]

def p_visibility_OPT(p):
	"""visibility_OPT :
		| visibility
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_when_decl_OPT(p):
	"""when_decl_OPT :
		| when_decl
	"""
	p[0] = p[1] if len(p)>=2 else None

def p_where_decl_OPT(p):
	"""where_decl_OPT :
		| where_decl
	"""
	p[0] = p[1] if len(p)>=2 else None
		
#############################################
# Error rule for syntax errors
def p_error(p):
	# p est un ply.lex.LexToke,
	print('Syntax error at token ' + str(p))
	print('parser.symstack : ' + str(parser.symstack))
	print('parser.statestack : ' + str(parser.statestack))

############################################
import json, time
def to_json(fn, js_file=None):
	""
	print('PARSING '+fn)
	t0 = time.time()
	fd = open(fn, 'r') # codecs.open(fn, 'r')
	prg = fd.read()
	fd.close()
	t1 = time.time()
	print(t1-t0)
	try:
		lexer.lineno = 1
		result = parser.parse(prg, lexer)
	except:
		### exception dans une action
		result = None
		print("BEGIN DUMP")
		print('parser.symstack : ' + str(parser.symstack))
		print('parser.statestack : ' + str(parser.statestack))
		print("END DUMP")
		raise
	t2 = time.time()
	print(t2-t1)
	if js_file == None:
		js_file = fn+'.json'
	print('SAVING '+js_file)
	fd = open(js_file, 'w')
	json.dump(result, fd, indent='\t')
	fd.close()
	t3 = time.time()
	print(t3-t2)
	return result
	
# Build the parser
parser = yacc.yacc(optimize=0)
# ply2yacc.yacc(optimize=0)

if False:
	prg = """node bar
	world
	foo
	bar
	"""
	try:
		result = parser.parse(prg)
	except:
		2+2
	#
	prg = """node foo
	world
	foo
	bar
	"""
	try:
		result = parser.parse(prg)
	except:
		2+2
	