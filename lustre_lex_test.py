
import lustre_lex as ll

prg = """
function trad0(In1 : bool) returns (Out1 : bool)
var
_L1_ : bool;
_L2_ : bool;
let
_L2_ = In1;
_L1_ = trad0_Operator1(_L2_);
Out1 = _L1_;
tel
"""

prg = '''
foo -> bar.toto
'''

prg = """
/*  
multi-line comment
*/
-- mono-line
function correct (a:'T) returns (b:'T) where 'T integer
	b = a mod 3;

type t = {lbl1: int32, lbl2: bool, lbl3:{lbl4: int32 , lbl5: float32}};
const c: t = {lbl1: 1, lbl2: true, lbl3:{lbl4 :2, lbl5 :0.5}};
const d: int32 = c.lbl1;

type t = int32;
const wordsize : int16 = 8;
type byte = t ^ wordsize;
int #1 #pragma toto #end foo = # 36;
"""

prg = """
int $and$int$-$*$*$#1 :
"""
fn_list = ('scade_examples/ADR_kcg_xml_filter_out.scade', 'scade_examples/calcul_matriciel_kcg_xml_filter_out.scade',
		'scade_examples/erts2016_kcg_xml_filter_out.scade', 'scade_examples/generiques_kcg_xml_filter_out.scade',
		'scade_examples/HYB_INTEG_kcg_xml_filter_out.scade', 'scade_examples/impls.scade',
		'scade_examples/iterateurs_kcg_xml_filter_out.scade', 'scade_examples/landing_gear_kcg_xml_filter_out.scade',
		'scade_examples/X4_kcg_xml_filter_out.scade','scade_examples/TVS_kcg_xml_filter_out.scade',)

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

if False:
	fn = 'scade_examples/landing_gear_kcg_xml_filter_out.scade'
	print(fn)
	f = open(fn, 'r')
	prg = f.read()
	f.close()


# ll.lexer.input(prg)
# print('*** BEGIN ***')
# while True:
# 	t = ll.lexer.token()
# 	if not t:
# 		break
# 	print(t)
# print('***** END *****')
