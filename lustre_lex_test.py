import lustre_lex as ll
ll.scade_64 = True
ll.fatal_error = True

import codecs, os

def lex_str(s, chatty=False):
	""
	ll.lexer.input(s)
	t = True
	i = -1
	while t:
		t = ll.lexer.token()
		if chatty:
			print(t)
		i += 1
	return i

if False:
	lex_str("'T 'b''X", True)
	assert False

def test_file(fn):
	""
	print('**  {}  **'.format(fn))
	encoding = 'latin-1' # 'utf-8'
	fd = codecs.open(fn, 'r',encoding=encoding)
	s = fd.read()
	fd.close()
	i = lex_str(s)
	print(i)

def test_dir(fn):
	""
	for root, dirs, files in os.walk(fn):
		for file in files:
			if file.endswith('.scade'):
				fn = os.path.join(root,file)
				test_file(fn)

fn_list = ( \
   'lustre_test_KO.scade', \
   'lustre_test_OK.scade', \
   r'C:\Program Files\ANSYS Inc', \
   r'F:\scade', \
   )

for fn in fn_list:
	if os.path.isfile(fn):
		test_file(fn)
	elif os.path.isdir(fn):
		test_dir(fn)
	else:
		print('!!!!! NOT FOUND : '+fn)
