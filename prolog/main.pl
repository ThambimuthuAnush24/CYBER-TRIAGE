% A data-driven Prolog production-rule engine. No submitted goal is executed as code.
:- use_module(library(http/json)).
:- use_module(library(lists)).
:- dynamic observation/1, rule/6.
:- initialization(main, main).

main :-
    catch(run, E, (print_message(error,E), halt(1))).
run :-
    setup_call_cleanup(open('knowledge.json',read,S),json_read_dict(S,KB,[value_string_as(atom)]),close(S)),
    maplist(load_fact,KB.facts), maplist(load_rule,KB.rules),
    json_read_dict(current_input,Input,[value_string_as(atom)]),
    dict_pairs(Input.facts,_,Pairs), exclude(is_unknown,Pairs,Known),
    forward(Known,[],1,Final,Trace),
    findall(H,(rule(_,_,H,_,_,_),memberchk(H-yes,Final)),Heads),sort(Heads,Derived),
    (get_dict(goal,Input,Goal)->true;Goal=ransomware),
    prove(Goal,yes,Known,[],Proof),
    json_write_dict(current_output,_{derived:Derived,trace:Trace,proof:Proof}),nl.
load_fact(F) :- assertz(observation(F.id)).
load_rule(R) :- assertz(rule(R.id,R.conditions,R.conclusion,R.explanation,R.sources,R.kind)).
is_unknown(_-unknown).
condition_holds(Known,C) :- memberchk(C.fact-C.value,Known).
forward(Known,Fired,N,Final,Trace) :-
    findall(_{rule:Id,round:N,conclusion:H,conditions:Cs,explanation:E,sources:S},
      (rule(Id,Cs,H,E,S,_),\+memberchk(Id,Fired),maplist(condition_holds(Known),Cs)),Agenda),
    (Agenda=[] -> Final=Known,Trace=[]
    ; findall(H-yes,(member(T,Agenda),H=T.conclusion),New),append(Known,New,K1),sort(K1,K2),
      findall(Id,(member(T,Agenda),Id=T.rule),Ids),append(Fired,Ids,F1),N1 is N+1,
      forward(K2,F1,N1,Final,Tail),append(Agenda,Tail,Trace)).
prove(G,V,Known,_,P) :- observation(G),!,
    (memberchk(G-A,Known)->(A==V->Status=proven;Status=not_supported);A=unknown,Status=unknown),
    P=_{goal:G,value:V,status:Status,actual:A,alternatives:[]}.
prove(G,V,_,Path,P) :- memberchk(G,Path),!,
    P=_{goal:G,value:V,status:not_supported,reason:'Cycle blocked',alternatives:[]}.
prove(G,V,Known,Path,P) :-
    findall(_{rule:Id,status:Status,children:Children},
      (rule(Id,Cs,G,_,_,_),maplist(prove_condition(Known,[G|Path]),Cs,Children),
       maplist(node_status,Children,Statuses),and_status(Statuses,Status)),Alternatives),
    maplist(node_status,Alternatives,States),or_status(States,Status),
    P=_{goal:G,value:V,status:Status,alternatives:Alternatives}.
prove_condition(Known,Path,C,P) :- prove(C.fact,C.value,Known,Path,P).
node_status(N,S) :- S=N.status.
and_status(S,not_supported) :- memberchk(not_supported,S),!.
and_status(S,unknown) :- memberchk(unknown,S),!.
and_status(_,proven).
or_status(S,proven) :- memberchk(proven,S),!.
or_status(S,unknown) :- memberchk(unknown,S),!.
or_status(_,not_supported).
