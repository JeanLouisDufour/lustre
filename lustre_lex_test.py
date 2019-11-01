import lustre_lex as ll

fn_list = ( \
   'lustre_test_KO.scade', \
   'lustre_test_OK.scade', \
   )

def lex_str(s):
	""
	ll.lexer.input(s)
	print('*** BEGIN ***')
	while True:
		t = ll.lexer.token()
		if not t:
			break
		print(t)
	print('***** END *****')

import codecs
#with open(fn, 'r', encoding='utf-8') as f:
for fn in fn_list:
	print('****************************************\n'+fn)
	f = codecs.open(fn, 'r',encoding='utf-8')
	if f:
		s = f.read()
		f.close()
		lex_str(s)
	else:
		assert False
