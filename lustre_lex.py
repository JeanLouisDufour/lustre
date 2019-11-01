import ply.lex as lex

literals = "'=><+-*/^@:,;[](){}|"  # . ne passe pas au parsing

reserved = {
		'activate' : 'ACTIVATE',
		'and' : 'AND',
		'assume' : 'ASSUME',
		'automaton' : 'AUTOMATON',
		'case' : 'CASE',
		'clock' : 'CLOCK',
		'const' : 'CONST',
		'default' : 'DEFAULT',
		'div' : 'DIV',
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
		'int' : 'INT',
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
		'real' : 'REAL',
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
	'HASH', # this is #
	'HASH_PRAGMA',
#	'HASH_INTEGER',
#	'HASH_INTEGER_COLON',
	) + tuple(reserved.values())

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
t_HASH = r'\#'
#t_HASH_INTEGER = r'\#\d+'
t_ignore_HASH_INTEGER = r'\#\d+'
# t_HASH_INTEGER_COLON = t_HASH_INTEGER + r'\s*:' 

t_ignore_space = '[ \t]+'  ## \r pour Py27

def t_HASH_PRAGMA(t):
	r'\#pragma(.|\n)*?\#end'
	t.lexer.lineno += t.value.count('\n')
	return t

# t_ignore_comment = r'/\*.*\*/'
# t_ignore_comment = r'(/\*(.|\n)*?\*/)|(//.*)'
def t_comment(t):
	r'/\*(.|\n)*?\*/'
	t.lexer.lineno += t.value.count('\n')

def t_comment_2(t):
	r'--.*'
	pass

# track line numbers
def t_newline(t):
	r'\n'
	t.lexer.lineno += 1 # len(t.value)

def t_newline_2(t):
	r'\r\n'
	t.lexer.lineno += 1 # len(t.value)

def t_PREFIXOP(t):
	r'(\$([*/+-<=>@]|mod|div|times|and|or|xor|<>|<=|>=)\$|(\+|-|not|reverse|int|real)\$)'
	return t

def t_ID(t):
	r'[a-zA-Z_][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value,'ID')
	return t

def t_NAME(t):
	r"'[a-zA-Z_][a-zA-Z_0-9]*"
	return t

def t_CHAR(t):
	r"'.'"
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
	print("Bad char '%s'" % t.value[0])
	assert False
	t.lexer.skip(1)
	
lexer = lex.lex(optimize=0)

# if __name__ == '__main__':
