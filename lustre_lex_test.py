import lustre_lex as ll
import codecs, os

fn_list = ( \
   'lustre_test_KO.scade', \
   'lustre_test_OK.scade', \
   'F:\\', \
   )

def lex_str(s):
	""
	ll.lexer.input(s)
	t = True
	i = -1
	while t:
		t = ll.lexer.token()
		i += 1
	return i

def lex_file(fn):
	""
	print('**  {}  **'.format(fn))
	encoding = 'latin-1' # 'utf-8'
	fd = codecs.open(fn, 'r',encoding=encoding)
	s = fd.read()
	fd.close()
	i = lex_str(s)
	print(i)

for fn in fn_list:
	if os.path.isfile(fn):
		lex_file(fn)
	elif os.path.isdir(fn):
		for root, dirs, files in os.walk(fn):
			for file in files:
				if file.endswith('.scade'):
					fn = os.path.join(root,file)
					lex_file(fn)
	else:
		print('!!!!! NOT FOUND : '+fn)
