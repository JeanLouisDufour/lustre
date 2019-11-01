import lustre_par as lp

def tok2str(t):
	""
	if not t[0].isalpha():
		t = "'"+t+"'"
	return t
	
if False:
	import inspect
# 	for name in dir(lp):
# 		if name.startswith('p_'):
# 			print(name)
	prod_start = ''
	prod_precedence = ()
	prod_tokens = ()
	prods = []
	for m in inspect.getmembers(lp): # paires (nom, objet)
		if m[0].startswith('p_') and m[0] != 'p_error':
			pr = m[1].__doc__
			if not (isinstance(pr,str)): # and pr.startswith(pn)):
				assert(False)
			colon = pr.find(':')
			pn = pr[0:colon].lstrip().rstrip()
			assert(m[0][2:].startswith(pn))
			prods.append(pr)
		elif m[0] == 'start':
			prod_start = m[1]
		elif m[0] == 'precedence':
			prod_precedence = m[1]
		elif m[0] == 'tokens':
			prod_tokens = m[1]
	assert(prod_start != '' and prod_tokens != ())

	with open('c/gram.y','w') as f:
		f.write('%start {}\n'.format(prod_start))
		for tok in prod_tokens:
			f.write('%token {}\n'.format(tok))
		for prec in prod_precedence:
			f.write('%{} {}\n'.format(prec[0], ' '.join(map(tok2str,prec[1:]))))
		f.write('%%\n')
		for r in sorted(prods):
			f.write(r)
			if not r.endswith(('\n','\n\t','\t\t')):
				f.write('\n')
		f.write('%%\n')
	
	### pour ocamlyacc, calcul des litteraux
	
	litt = {
		"'": 'CH_QUOTE',
		'=': 'CH_EQ',
		'>': 'CH_GT',
		'<': 'CH_LT',
		'+': 'CH_PLUS',
		'-': 'CH_MINUS',
		'*': 'CH_TIMES',
		'/': 'CH_DIV',
		'^': 'CH_HAT',
		'@': 'CH_ARROW',
		':': 'CH_COLON',
		',': 'CH_COMMA',
		';': 'CH_SC',
		'[': 'CH_LSB',
		']': 'CH_RSB',
		'(': 'CH_LB',
		')': 'CH_RB',
		'{': 'CH_LCB',
		'}': 'CH_RCB',
		'|': 'CH_BAR',
		}
	foo = (lambda s: "'"+s+"'")
	litterals = dict([(foo(k),v) for (k,v) in litt.items()])
	def replace_dict(s,d):
		""
		for (k,v) in d.items():
			s = s.replace(k,v)
		return s
	x_prods = {}
	for r in prods:
		r = replace_dict(r,litterals)
		i = r.index(':')   ### index lance une exception
		rn = r[0:i].strip()
		# print(rn)
		# r = r[i+1:].lstrip()
		dl = []
		while r.find('|',i+1)>=0:   ### find renvoie -1
			i_m1 = i;
			i = r.index('|',i+1)  ### pas tres elegant ...
			dl.append(r[i_m1+1:i].strip())
		dl.append(r[i+1:].strip())
		if rn in x_prods:
			x_prods[rn].extend(dl)
		else:
			x_prods[rn] = dl
	
	with open('ocaml/lustre_par_tmp.mly','w') as f:
		f.write('%start {}\n'.format(prod_start))
		f.write('%type <int> {}\n'.format(prod_start))
		for tok in prod_tokens:
			f.write('%token {}\n'.format(tok))
		for tok in litterals:
			f.write('%token {}\n'.format(litterals[tok]))
		for prec in prod_precedence:
			f.write('%{} {}\n'.format(prec[0], ' '.join(map(tok2str,prec[1:]))))
		f.write('%%\n')
		for rn in sorted(x_prods):
			is_OPT = rn.endswith('_OPT')
			is_SEQ = rn.endswith('_SEQ')
			is_STAR = rn.endswith('_STAR')
			f.write('{}: '.format(rn))
			dl = x_prods[rn]
			assert not(is_OPT or is_SEQ or is_STAR) or len(dl)==2
			for i,d in enumerate(dl):
				if i>0:
					f.write('\t| ')
				if d=='':
					f.write('/* empty */')
				else:
					f.write(d)
				if is_OPT and d=='':
					f.write(' { None }\n')
				elif is_OPT and d!='':
					if d.isupper():
						f.write(' { Some () }\n')
					else:
						f.write(' { Some $1 }\n')
				elif is_SEQ and d.find(' ')==-1:
					f.write(' { [$1] }\n')
				elif is_SEQ:
					f.write(' { $1::$3 }\n')
				elif is_STAR and d=='':
					f.write(' { [] }\n')
				elif is_STAR and d!='':
					f.write(' { $1::$2 }\n')
				else:
					f.write(' { 1 }\n')
			f.write(';\n')
		f.write('%%\n')
	
	assert False, "TERMINATED OK"

def lustre_check_oper(oper, package, pack_path=[]):
	"return id_list"
	assert package[''] in('package',) and oper in package
	impl = package[oper]
	assert impl[''] in ('function','node')
	if 'let' in impl:
		eqs = impl['let']
		for eq in eqs:
			assert isinstance(eq,list)
			if eq[0] == '=':
				lhs = eq[1]
				assert isinstance(lhs,list)
				rhs = eq[2]
				foo = lustre_check_expr(rhs, oper, package, pack_path)
			else:
				2+2
	else:
		2+2

def lustre_check_expr(e, oper, package, pack_path=[]):
	""
	if isinstance(e,(bool,int,str)):
		return set()
	elif isinstance(e,list):
		if isinstance(e[0], str):
			if e[0] in ('char','const','last'):
				2+2
			else: # user op
				return lustre_check_oper(e[0], package, pack_path)
		elif isinstance(e[0], list): ## operator
			2+2
		else:
			assert False
	else:
		assert False

prg0_list = []

prg1_list = [
"""
/* The order in package declaration is not relevant */
package P1
open P1;
const
iC1 : T1 = 2;
package P1
type
T1 = int32;
end;
end;
""",
"""
/* Errors due to multiple declaration via open */
package P1
type foo = int16;
end;
open P1;
const foo: bool = true;
""",
"""
/* Package opening is not transitive */
package P1
package P2
const foo: int32 = 0;
end;
open P2;
const bar: int32 = foo + 1;
end;
open P1;
const foobar: int32 = foo * 2;
""",
"""
/* Declaration using a fully qualified path */
package P1
const foo: int16 = 3;
end;
package P2
const bar: int16 = 4;
end;
const foobar: int16 = P1::foo + P2::bar;
""",
"""
/* Private visibility status: type t is unknown outside P1. This program raises an error */
package P1
type private t= int64;
const c:t=0;
end;
open P1;
const d:t= c + 1;
""",
"""
/* Imported declarations */
package ForeignArithmetics
type imported ForeignInt ;
function imported plus(x,y: ForeignInt) returns (z: ForeignInt);
function twice (x: ForeignInt) returns (y: ForeignInt) y = plus(x, x);
end;
""",
"""
/* Imported numeric type */
package ForeignArithmetics
type imported ForeignInt is integer ;
function plus_two (x: ForeignInt ) returns (y: ForeignInt ) y = x + 2;
end;
""",
"""
/*  */
function correct (a:'T) returns (b:'T) where 'T integer
	b = a mod 3;

type t = {lbl1: int32, lbl2: bool, lbl3:{lbl4: int32 , lbl5: float32}};
const c: t = {lbl1: 1, lbl2: true, lbl3:{lbl4 :2, lbl5 :0.5}};
const d: int32 = c.lbl1;

type t = int32;
const wordsize : int16 = 8;
type byte = t ^ wordsize;
""",
"""
/* Groups are always flattened */
group
G0 = (int32 , bool);
G1 = (int32 , G0);
function f1(x: int32; y: int32; z: bool) returns (r: G1)
r = (x, y, z);
function f2(v: G1) returns (a: int32; b: int32; c: bool)
a, b, c = f1(v);
""",
"""
/* Groups are used to manage multiple outputs operators */
function imported f(a, b: int32; c: bool) returns (x,y: int32);
function imported g(a,b: int32) returns (x: int32);
node ex(c: bool; a, b: int32) returns (s, t: int32)
let
s, t = if c then f(a, b, c) else (0, g(f(b, a, not c)));
tel;
""",
"""
/* A list expression can contain flows based on different clocks */
function N(x: int32; clock h: bool) returns (y: int32 when h; z: bool)
let
y,z = (x when h, true);
tel;
""",
"""
/* Sensor declaration */
sensor temp: float32;
node gradient() returns (diff: float32)
let
diff = 0.0 -> temp - pre temp;
tel;
""",
"""
/*  */
function ex4(clock h: bool; y, z: int16) returns (o1: int16; o2: bool)
let
o1 = merge (h; y when h; z when not h);
o2 = (y > z);
tel;
""",
"""
/* Valid clock expressions */
type t= enum {incr, stdby, decr};
function Sample (clock h: bool; clock k: t; x: int32) returns (y, z: int32)
let
activate when k match
| incr : y = x + 1;
| stdby : y = x ;
| decr : y = x - 1;
returns y;
z = merge (h; x when h; x when not h);
tel;
""",
"""
/* Unused local variable */
node ex3(x: int8) returns (y: int8)
var z: int8 last = 0;
let
z = 2*pre(x) + 1;
y = x - pre(x);
tel;
""",
"""
/* Overloading of an assume identifier, preventing the use of the former declaration */
const c: int32 = 0;
node ex(x: int32; b: bool) returns (y: int32)
let
assume c: true;
y = if b then x else c -> pre y;
tel;
""",
"""
/* The condition must be either Boolean or must belong to an enumerated type. This node is erroneous */
node ex1(x: int16)
returns (y: int16)
let
activate when x match
| 0: y = 0;
| _: y = 1;
returns ..;
tel;
""",
"""
/* Defined variables must have at least a definition in one of the branches. In this example, o2 has no definition */
node ex2(i: bool)
returns (o1,o2: int64)
let
activate Act if i
then o1 = 1;
else o1 = 2;
returns o1,o2;
tel;
""",
"""
/* Conditional blocks can be nested. Notice also that the last branch is empty */
type Tenum = enum {red, blue, pink, purple};
node ex3(eI1: Tenum; iI2: int32)
returns (iO1: int32 last = 0)
let
	activate when eI1 match
	| red: var iV1: int32;
		let
		iV1 = 10 + last 'iO1;
		iO1 = iV1 + iI2;
		tel
	| blue:
		let
			activate if iI2 > 0
			then iO1 = iI2 * iI2;
			else iO1 = -iI2 + last 'iO1;
			returns iO1;
		tel
	| pink: iO1 = 100 -> pre iO1 - 1;
	| purple:
	returns iO1;
tel;
""",
"""
/* The following example illustrates a causality error for variable y */
type T = enum {a, b, c};
node ex5(x: T) returns (y: T last = b)
let
activate when y match
| a: y = a -> pre(y);
| b: y = x;
| c:
returns ..;
tel
""",
"""
/* A branch of a decision block can be empty */
function ex1(i: int32)
returns (o: int32 last = 0)
let
activate if i > 0
then o = i;
else
returns o;
tel

function ex1(i: int32)
returns (o: int32 default = 4)
let
activate if i > 0
then o = i;
else
returns o;
tel
""",
"""
/* This first example browses the full syntax available within automaton */
node StateMachine_1(bI1: bool)
returns (bO1: bool default = true; iO2: int16 default = 0; bO3: bool default = false)
let
	automaton SM1
	
	initial state ST1
	unless if bI1 resume ST2;
	sig
		sig1;
	var
		iV1: int16;
	let
		iV1 = 10;
		emit 'sig1;
		bO1 = 'sig1;
		iO2 = iV1 -> pre iO2 + 2;
	tel
	
	state ST2
	sig
		sig1;
	var
		bV1: bool;
	until if true do let emit 'sig1;
			bV1 = 'sig1;
			bO3 = bV1;
			tel
		restart ST1;
	returns ..;
tel
""",
"""
/* This example illustrates some of the namespace rules that allows to overload an identifier */
type
SM1 = uint16;
node StateMachine_012(iI1: int32)
returns (iO1: int32)
let
automaton SM1
initial final state ST1
sig
SM1;
var
ST1: int32;
let
ST1 = iI1;
emit 'SM1;
iO1 = ST1 + 1;
tel
returns ..;
tel
""",
"""
/* First example */

node StateMachine_062 (iI1: int32)
returns (iO1: int32)
var bV1: bool;
let
automaton SM1
initial state ST1
var bV2: bool;
let
bV2 = false -> not pre bV2;
bV1 = iI1 <> 0;
iO1 = iI1 * 2;
tel
until if bV1 and bV2 restart ST2;
state ST2
unless if bV1 resume ST1;
returns ..;
tel

/* Second example */
node StateMachine_062 (iI1: int32)
returns (iO1: int32)
var bV1: bool;
let
automaton SM1
initial state ST1
var bV2: bool;
let
bV2 = false -> not pre bV2;
bV1 = iI1 <> 0;
iO1 = iI1 * 2;
tel
until if bV1 and bV2 restart ST2;
state ST2
unless if last 'bV1 resume ST1;
returns ..;
tel
""",
"""
/* This example illustrates the use of the default declaration */
node StateMachine_073(iI1: int16; bI2: bool)
returns (iO1: int16 default = 10; iO2: int16 default = 5 * iO1)
let
automaton SM1
initial state ST1
unless if bI2 resume ST2;
let
iO1 = iI1;
tel
until if true restart ST2;
state ST2
let
iO2 = 0 -> pre iO1 + iI1;
tel
until if true restart ST1;
returns ..;
tel
""",
"""
/* Variable iO1 cannot be defined both in the transitions of ST1 and in the body of ST2 */
node StateMachine_078(iI1: int32; bI2: bool)
returns (iO1, iO2: int32)
let
automaton
initial state ST1
unless if bI2 do iO1 = iI1 + 1; restart ST2;
until if true do iO1 = 10; restart ST2;
state ST2
unless if bI2 do iO2 = 0; restart ST1;
iO1 = 0;
until if true do iO2 = -10; restart ST1;
returns ..;
tel
""",
"""
/* Example 6 */
node StateMachine_112(iI1: int32 when bI2; clock bI2: bool)
returns (iO1: int32 when bI2)
let
automaton
initial state ST1
var iV1: int32 when bI2;
let
iV1 = (0 when bI2) -> pre iV1 + 1 when bI2;
iO1 = iI1 -> pre iV1;
tel
until if bI2 restart ST1;
returns iO1;
tel
""",
"""
/* Example 7 */
node StateMachine_063(iI1: int16)
returns (iO1: int16)
let
automaton SM1
initial state ST1
let
iO1 = iI1 * 2;
tel
until if bV1 do
var bV1: bool;
let
bV1 = iI1 > 10;
tel
restart ST2;
state ST2
returns ..;
tel
""",
"""
/* Example 8: */
node StateMachine_122 (iI1: int32; bI2: bool)
returns (iO1: int32; iO2: int32)
let
automaton
initial state ST1
let
iO1 = iI1;
iO2 = iI1 * 2;
tel
until if bI2 restart ST2;
state ST2
let
iO1 = 1 -> - iI1;
tel
until if true restart ST1;
returns ..;
tel
""",
"""
/* Example 9 */
node N() returns (x, y: int32 last = 0)
let
automaton A
initial state ST1
let tel
until if true restart ST2 ;
state ST2
var z: int32 last = 2;
let
automaton A2
initial state ST2_1
let
z = 3 + last 'z;
x = last 'x + 1;
tel
until if x mod 2 = 0 resume ST2_2;
state ST2_2
let
x = last 'x -1;
y = 0 -> pre z - 1;
tel
until if true resume ST2_2 ;
returns .. ;
tel
until if true resume ST1 ;
returns .. ;
tel
""",
"""
/* Example 11: A single state machine with two states and data flow definitions in states */
node jld() returns (o:bool)
automaton SM1
initial state EVEN
unless if i restart ODD;
let
o = true;
tel
state ODD
unless if i restart EVEN;
let
o = false;
tel
returns o ;
""",
"""
/* Example 12: SM1 has a macro state A which includes two state machines in parallel */
node jld() returns ()
automaton SM1
initial state A
let
automaton SM2
initial state B
until if 2 times 'S1 restart C;
final state C
returns .. ;
automaton SM3
initial state D
until if 2 times c restart E;
final state E
returns .. ;
tel
until
synchro do let emit 'S2; tel restart F;
state B
returns .. ;
""",
"""
/* Example 13: State B can be started on condition v, or resumed by history on condition not v. */
node jld() returns ()
automaton SM1
initial state A
unless
if not v do let emit 'S1; tel resume B;
if v do let emit 'S2; tel restart B;
state B
returns .. ;
""",
# """
# /* Example 14: The following state machine illustrates the use of fork transitions */
# node jld() returns ()
# automaton SM1
# initial state A
# until
# if c1 do let emit 'S1; tel
# if c2 do let emit 'S2; tel restart B
# else do let emit 'S3; tel
# if c4 do let emit 'S4; tel restart C
# elsif c5 do let emit 'S5; tel restart D
# else do let emit 'S6; tel restart E
# end
# end;
# state B
# state C
# state D
# state E
# returns .. ;
# """,
"""
/* The following example illustrates the semantic differences between last and pre */

node UpDownPre() returns(x:int16)
let
automaton SSM
initial state Up
let
x = 0 -> pre(x) + 1;
tel
until if (x>=3) resume Down;
state Down
let
x = 2 -> pre(x) -1;
tel
until if (x<=-3) resume Up;
returns x;
tel

node UpDownLast() returns(x:int16)
let
automaton SSM
initial state Up
let
x = 0 -> last 'x + 1;
tel
until if (x>=3) resume Down;
state Down
let
x = last 'x - 1;
tel
until if (x<=-3) resume Up;
returns x;
tel
""",
"""
/* User operators can be easily fed with list of expressions */
group G = (int64, int64, bool);
function imported f(a, b: int64; c: bool) returns (x, y: int64);
function imported g(a, b: int64) returns (x: int64);
node ex(c: bool; a, b: int64) returns (s, t: int64)
var l: G;
let
l = (a+b, a-b, c);
s, t = if c then f(l) else (0, g(f(b, a, not c)));
tel;
""",
"""
node times_behavior (n : 'a; c : bool) returns (o : bool) where 'a signed
var
v3, v4 : 'a;
let
v4 = n -> pre (v3);
v3 = if (v4 < 0)
then v4
else (if c then v4 - 1 else v4);
o = c and (v3 = 0);
tel
""",
"""
/* Valid array expressions */
const
aC1: int32^2 = [1,1];
aC2: int32^1 = [0];
function ex(aI1, aI2: int32^2; i: uint16)
returns (aO1, aO2, aO3, aO4: int32^4; aO5: int32^2^3)
let
aO1 = reverse aI2 @ reverse aI1;
aO2 = aC2 @ [[1,2,3],[2,3,4]][2*3 - 5];
aO3 = aO2 [1 .. 2] @ aI2;
aO4 = aI1 @ ([aI1,aI2].[i] default aC1);
aO5 = [[0,1],[2,3],[4,5]];
tel
""",
"""
/* Arrays can used by polymorphic operators */
type imported T;
const imported C:T;
group G=(int32, int32);
node ex(aI1, aI2: int32^2; clock clk1: bool; aI3: T)
returns (aO1, aO2: int32^2; aO3: T^2)
var v1: G;
let
v1 = (aI1[0],aI2[1]);
aO1 = fby(aI1; 1; [v1]);
aO2 = merge (clk1; aI1 when clk1; aI2 when not clk1);
aO3 = reverse (C -> aI3)^2;
tel
""",
"""
/* Structures and arrays can be fully mixed */
type
Tstr1 = {l1: int32};
Tstr2 = {l1: int32, l2: int32^2};
function ex(sI1: Tstr2; sI2: Tstr1^2)
returns (iO1: int32)
var
iV1, iV2: int32;
let
iV1 = sI1.l2[0];
iV2 = sI2[0].l1;
iO1 = iV1 + iV2;
tel
""",
"""
/* Mixed constructor can be used with indexes or labels */
type
Tstr = {l1: int32,l2: float64};
Tarr = int32^3;
function ex(sI1: Tstr; sI2:{l1:int32})
returns (sO1: Tstr; aO2: Tarr; sO3:{l1: int32})
let
sO1 = (sI1 with .l2 = 3.0);
aO2 = (sI2.l1^3 with [0] = 0);
sO3 = ((sI2 with .l1 = 1) with .l1 = 3);
tel
""",
]

prg2_list = [
"""
node RetractionSequence(
      handle : bool;
      gears_locked_up : bool;
      gears_locked_down : bool;
      doors_open : bool;
      doors_closed : bool;
      gear_shock_absorbers : bool)
    returns (
      general_EV : bool default = false;
      open_EV : bool default = false;
      close_EV : bool default = false;
      retract_EV : bool default = false)
  let
    
    automaton SM1
      state State1
        unless
          if handle restart State2;

      state State2
        unless
          if doors_open restart State3;
        var
          _L1 : bool;
          _L2 : bool;
        let
          general_EV= _L1;
          _L1= true;
          open_EV= _L2;
          _L2= true;
        tel

      state State3
        unless
          if true
            do if not gear_shock_absorbers and gears_locked_down restart State40
            elsif gear_shock_absorbers restart State5
            end;

      state State5
        unless
          if true restart State6;
        var
          _L1 : bool;
        let
          open_EV= _L1;
          _L1= false;
        tel

      state State7
        var
          _L1 : bool;
          _L2 : bool;
        let
          general_EV= _L1;
          _L1= false;
          close_EV= _L2;
          _L2= false;
        tel

      initial state State0
        unless
          if gears_locked_down and doors_closed restart State1;

      state State40
        unless
          if gears_locked_up restart State41;
        var
          _L1 : bool;
        let
          retract_EV= _L1;
          _L1= true;
        tel

      state State6
        unless
          if doors_closed do restart State7;
        var
          _L1 : bool;
        let
          close_EV= _L1;
          _L1= true;
        tel

      state State41
        unless
          if true restart State6;
        var
          _L1 : bool;
        let
          retract_EV= _L1;
          _L1= false;
        tel
    returns ..;
  tel
""",
]

prg3_list = [
"""
function CompAFDXT0_40ms() returns ()
  let
    _L2=
      (MMR_data.MMRGPS_Latitude + MMR_data.MMRGPS_LatitudeFine) / C_ConvDeg2Rad;
  tel
""",	
]

prg4_list = [
"""
function LIBEARTH_CalculerRNRE<<P_CFG_ERA_ARG>>(
      SinLat : real;
      Altitude : real)
    returns (UnSurR_NE : real^2; RN_RE : real^2)
  let
    _L4_=
      (activate #2402 LIBEARTH_CalculerRNRE_RNRE_ARG every _L8_)(_L2_, _L3_);
/* */
    _L5_=
      (activate #2403 LIBEARTH_CalculerRNRE_RNRE_ERA every not _L8_)(_L2_,
        _L3_);
/* */
    UnSurR_NE= _L1_;
    RN_RE= _L6_;
    _= P_CFG_ERA_ARG;
  tel
""",	
]

for prg in prg0_list:
	print(prg)
	result = lp.parser.parse(prg, debug=False)
	print(result)

fn_list = ('scade_examples/ADR_kcg_xml_filter_out.scade', 'scade_examples/calcul_matriciel_kcg_xml_filter_out.scade',
		'scade_examples/erts2016_kcg_xml_filter_out.scade', 'scade_examples/generiques_kcg_xml_filter_out.scade',
		'scade_examples/HYB_INTEG_kcg_xml_filter_out.scade', 'scade_examples/impls.scade',
		'scade_examples/iterateurs_kcg_xml_filter_out.scade', 'scade_examples/landing_gear_kcg_xml_filter_out.scade',
		'scade_examples/X4_kcg_xml_filter_out.scade','scade_examples/TVS_kcg_xml_filter_out.scade',)
fn0_list = ()
fn1_list = fn_list[4:5]
fn2_list = fn_list[:3]
fn3_list = fn_list[-1:]
fn4_list = ['../scade/kcg_xml_filter_out.scade']
fn5_list = [r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1_R18orig\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\PAR\determiner_modes_generaux\sc\C_determiner_modes_generaux_KCG64\kcg_xml_filter_out.scade',
		r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1_R18orig\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc\C_calculer_limites_et_regimes_KCG64\kcg_xml_filter_out.scade']
fn5_list = [r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\c90100_tc\PAR\calculer_limites_et_regimes\C_calculer_limites_et_regimes_KCG64\Cible',
		r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\c90100_tc\PAR\determiner_modes_generaux\C_determiner_modes_generaux_KCG64\Cible']
fn5_list = [r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\PAR\determiner_modes_generaux\sc\C_determiner_modes_generaux_KCG64\kcg_xml_filter_out.scade',
		r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc\C_calculer_limites_et_regimes_KCG64\Cible\kcg_xml_filter_out.scade']
fn6_list = [r'\scade\Cas_etude_SafranHE_2_ATCU_S1807\MODEL\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc\C_calculer_limites_et_regimes_KCG64',
		r'\scade\Cas_etude_SafranHE_2_ATCU_S1807\MODEL\cvob_arrano1g4\c90100_modele\PAR\determiner_modes_generaux\sc\C_determiner_modes_generaux_KCG64']
import codecs, json, os # , os.path
for fn in fn6_list:
	print('*****************************************************')
	if not fn.endswith('.scade'):
		fn += r'\kcg_xml_filter_out.scade'
	for prefix in (r'F:',r'C:\Users\F074018\Documents'):
		if os.path.exists(prefix+fn):
			fn = prefix+fn
			break
	print(fn)
	#with open(fn, 'r', encoding='utf-8') as f:
	#f = codecs.open(fn, 'r', encoding='utf-8')
	if True:
		f = codecs.open(fn, 'r')
		prg = f.read()
		f.close()
		try:
			result = lp.parser.parse(prg)
		except:
			result = None
			print("BEGIN DUMP")
			for symb in lp.parser.symstack:
				print(symb)
			print(lp.parser.statestack)
			print("END DUMP")
			raise
		assert fn.endswith('.scade')
		js_file = fn[:-5] + 'json'
		f = open(js_file, 'w')
		json.dump(result, f, indent=4)
		f.close()
		if 'Ztest_calculer_limites_et_regimes' in result:
			lustre_check_oper('Ztest_calculer_limites_et_regimes', result)

for user in ('F074018.SDS','F074018') if False else ():
	dr = 'C:/Users/' + user + '/AppData/Local/Temp/ScadeChecker'
	for son in os.listdir(dr):
		sonp = dr + '/' + son
		if os.path.isdir(sonp):
			for son2 in os.listdir(sonp):
				if son2.endswith('.scade'):
					fn = sonp + '/' + son2
					print('*****************************************************')
					print(fn)
					#with open(fn, 'r', encoding='utf-8') as f:
					f = codecs.open(fn, 'r', encoding='utf-8')
					if True:
						prg = f.read()
						result = lp.parser.parse(prg)
						print(result)
					f.close()
