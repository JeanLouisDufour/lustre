import ply.lex as lex

fatal_error = False
scade_64 = True

literals = "#=><+-*/^@:,;[](){}|"  # . ne passe pas au parsing # on vire '

reserved_common = {
		'activate' : 'ACTIVATE',
		'and' : 'AND',
		'assume' : 'ASSUME',
		'automaton' : 'AUTOMATON',
		'case' : 'CASE',
		'clock' : 'CLOCK',
		'const' : 'CONST',
		'default' : 'DEFAULT',
		'do' : 'DO',
		'else' : 'ELSE',
		'elsif' : 'ELSIF',
		'emit' : 'EMIT',
		'end' : 'END',
		'enum' : 'ENUM',
		'every' : 'EVERY',
		'final' : 'FINAL',
		'flatten' : 'FLATTEN',
		'fold' : 'FOLD',
		'foldi' : 'FOLDI',
		'foldw' : 'FOLDW',
		'foldwi' : 'FOLDWI',
		'function' : 'FUNCTION',
		'group' : 'GROUP',
		'guarantee' : 'GUARANTEE',
		'if' : 'IF',
		'is' : 'IS',
		'imported' : 'IMPORTED',
		'initial' : 'INITIAL',
		'last' : 'LAST',
		'let' : 'LET',
		'make' : 'MAKE',
		'map' : 'MAP',
		'mapfold' : 'MAPFOLD',
		'mapi' : 'MAPI',
		'mapfoldi' : 'MAPFOLDI',
		'mapw' : 'MAPW',
		'mapwi' : 'MAPWI',
		'match' : 'MATCH',
		'mod' : 'MOD',
		'node' : 'NODE',
		'not' : 'NOT',
		'of' : 'OF',
		'open' : 'OPEN',
		'or' : 'OR',
		'package' : 'PACKAGE',
		'pre' : 'PRE',
		'private' : 'PRIVATE',
		'probe' : 'PROBE',
		'public' : 'PUBLIC',
		'restart' : 'RESTART',
		'resume' : 'RESUME',
		'returns' : 'RETURNS',
		'reverse' : 'REVERSE',
		'sensor' : 'SENSOR',
		'sig' : 'SIG',
		'specialize' : 'SPECIALIZE',
		'state' : 'STATE',
		'synchro' : 'SYNCHRO',
		'tel' : 'TEL',
		'then' : 'THEN',
		'times' : 'TIMES',
		'type' : 'TYPE',
		'unless' : 'UNLESS',
		'until' : 'UNTIL',
		'var' : 'VAR',
		'when' : 'WHEN',
		'where' : 'WHERE',
		'with' : 'WITH',
		'xor' : 'XOR',
		}

reserved_64 = {k:k.upper() for k in ('div','int','real')}

reserved_65 = {k:k.upper() for k in ('land','lor','lxor','lsl','lsr','lnot')}

reserved = (reserved_64 if scade_64 else reserved_65).copy(); reserved.update(reserved_common)

tokens = (
	'ID',
	'INTEGER',
	'FLOAT',
#	'LPAR',
#	'RPAR',
#	'EQ',
#	'COLON',
	'COLONCOLON', 'DOTDOT', 'DOT',
#	'SEMICOLON',
#	'COMMA',
#	'HAT',
#	'QUOTE',
#	'GT',
	'GTGT', 'GTEQ', 'LTGT',
#	'LT',
	'LTLT', 'LTEQ',
#	'ADD',
#	'SUB',
#	'MUL',
#	'DIV',
#	'DOLLAR',
	'ARROW',
	'CHAR',
	'NAME',
	'PREFIXOP',
# 	'HASH', # this is #
	'HASH_PRAGMA',
#	'HASH_INTEGER',
#	'HASH_INTEGER_COLON',
	) \
	+ tuple(reserved_common.values()) \
	+ tuple(reserved_64.values()) + tuple(reserved_65.values())

t_ARROW = r'->'
# t_LPAR = r'\('
# t_RPAR = r'\)'
# t_EQ = r'='
# t_COLON = r':'
t_DOT = r'\.'
t_DOTDOT = r'\.\.'
t_COLONCOLON = r'::'
# t_SEMICOLON = r';'
# t_COMMA = r','
# t_HAT = r'\^'
# t_QUOTE = r"'"
# t_GT = r'>'
t_GTGT = r'>>'
t_GTEQ = r'>='
#t_LT = r'<'
t_LTLT = r'<<'
t_LTEQ = r'<='
t_LTGT = r'<>'
# t_ADD = r'\+'
# t_SUB = r'-'
# t_MUL = r'\*'
# t_DIV = r'/'
# t_DOLLAR = r'\$'
# t_PREFIXOP = r'(\$([*/+-<=>@]|mod|div|times|and|or|xor|<>|<=|>=)\$|(+|-|not|reverse|int|real)\$)'
# t_HASH = r'\#'
#t_HASH_INTEGER = r'\#\d+'
t_ignore_HASH_INTEGER = r'\#\d+'
# t_HASH_INTEGER_COLON = t_HASH_INTEGER + r'\s*:' 

# t_ignore_space = r'\s+' # '[ \t]+'  ## \r pour Py27
## cette regle a masque SP CR LF
def t_space(t):
	r'\s+'
	tv = t.value
	t.lexer.lineno += tv.count('\n') + tv.count('\r') - tv.count('\r\n')

def t_HASH_PRAGMA(t):
	r'\#pragma(.|\n)*?\#end'
	tv = t.value
	t.lexer.lineno += tv.count('\n') + tv.count('\r') - tv.count('\r\n')
	tv = tv[7:-4].strip()
	i = 0;
	while i < len(tv) and not tv[i].isspace(): i += 1
	j = i;
	while j < len(tv) and tv[j].isspace(): j += 1
	if 0 < i < j < len(tv):
		t.value = (tv[:i], tv[j:])
	else:
		t.value = ('', tv)
	return t

# t_ignore_comment = r'/\*.*\*/'
# t_ignore_comment = r'(/\*(.|\n)*?\*/)|(//.*)'
def t_comment(t):
	r'/\*(.|\n)*?\*/'
	tv = t.value
	t.lexer.lineno += tv.count('\n') + tv.count('\r') - tv.count('\r\n')

def t_comment_2(t):
	r'--.*'
	pass

# track line numbers
# def t_newline(t):
	# r'\n'
	# t.lexer.lineno += 1 # len(t.value)

# def t_newline_2(t):
	# r'\r\n'
	# t.lexer.lineno += 1 # len(t.value)

"TODO : Scade65: $land$ | $lor$ | $lxor$ | $lsl$ | $lsr$ | lnot$ "
def t_PREFIXOP(t):
	r'(\$([*/+-<=>@]|mod|div|times|l?and|l?or|l?xor|lsl|lsr|<>|<=|>=)\$|(\+|-|l?not|reverse|int|real)\$)'
	return t

def t_ID(t):
	r'[a-zA-Z_][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value,'ID')
	return t

def t_CHAR(t):
	r"'(.|\\x..)'"
	return t

def t_NAME(t):
	r"'[a-zA-Z_][a-zA-Z_0-9]*"
	return t

def t_FLOAT(t):
	r'\d+\.\d*([eE][+-]?\d+)?'
	t.value = float(t.value)
	return t

def t_INTEGER(t):
	r'\d+'
	t.value = int(t.value)
	return t

def t_error(t):
	ch = t.value[0]
	if fatal_error:
		assert False, (ch, ord(ch))
	else:
		print("********* Bad char '{}' ({}) ************".format(ch, ord(ch)))
		t.lexer.skip(1)
	
lexer = lex.lex(optimize=0)

# if __name__ == '__main__':
