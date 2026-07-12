% === Equivalences
fof(copula_identity, axiom, ! [B,X,Y] : ((be_01(B) & arg1(B,X) & arg2(B,Y)) => X = Y )).

fof(copula_to_domain, axiom, ![B,X,Y] : ((be_01(B) & arg1(B,X) & arg2(B,Y)) => domain(Y,X))).
fof(copula_to_mod, axiom, ! [B,X,Y] : ((be_01(B) & arg1(B,X) & arg2(B,Y) ) => mod(X,Y))).

%not necessarily overlap with now...
fof(mod_to_copula, axiom, ! [X,A,S] : ((mod(X,A) & s(S)) => ? [B] : (be_01(B) & aspect_state(B) & arg2(B,A) & arg1(B,X) & total_overlap(B,S) & overlap(B,now)))). 
fof(poss_to_have, axiom,
    ! [W,X,S] :
      ( ( poss(W,X) & s(S) )
     => ? [H] :
          ( have_03(H) & aspect_state(H) & arg0(H,X) & arg1(H,W)
          & total_overlap(H,S) & overlap(H,now) ) ) ).

% === Skolemization (up to 5)
fof(unique_c1, axiom, ?[X]: (c1(X) & ![Y]: (c1(Y) => Y = X))).
fof(unique_c2, axiom, ?[X]: (c2(X) & ![Y]: (c2(Y) => Y = X))).
fof(unique_c3, axiom, ?[X]: (c3(X) & ![Y]: (c3(Y) => Y = X))).
fof(unique_c4, axiom, ?[X]: (c4(X) & ![Y]: (c4(Y) => Y = X))).
fof(unique_c5, axiom, ?[X]: (c5(X) & ![Y]: (c5(Y) => Y = X))).

% % === World knowledge
fof(large_not_small, axiom, ! [X] : ~ (arg1(large_01,X) & arg1(small_01,X))).

fof(geq_monotonic, axiom, ![X]: (geq_2(X) => geq_1(X))).
%59
fof(a_few_implies_geq, axiom, ! [X] : (a_few(X) => geq_a_few(X))).

 %don't work...
% fof(geq2_not_n1, axiom, ! [X] : ~ (geq_2(X) & n1(X))).
% fof(exact2_not_six, axiom,
%     ! [X] : ( n2(X) => ~ geq_6(X) ) ).

fof(n1_excludes_plural, axiom,
    ! [X] : ~ ( n1(X) & plural(X) ) ).



% fof(currently, axiom,
%     ![X]: (include(currently, X) => overlap(X,now))).

% fof(currently_reverse, axiom,
%     ![X]: (overlap(X,now) => include(currently, X))).

% fof(found_exist, axiom,
%     ![X,S]: (found_01(X,S) => exist_01(X,S))).

% fof(n1_not_plural, axiom,
%     ![X]: (n1(X) => ~plural(X))).

% fof(plural_not_n1, axiom, 
%     ![X]: (plural(X) => ~n1(X))).

% fof(plural_not_n1, axiom, 
%     ![X]: (plural(X) => ~n1(X))).

% fof(unique_year, axiom,
%   ![X,Y]:
%     (year(X) & year(Y) => X = Y)
% ).
% fof(unique_hour, axiom,
%   ![X,Y]:
%     (hour(X) & hour(Y) => X = Y)
% ).

% === Temporal axioms
% A1: precedence is asymmetric
% fof(a1, axiom, ![X,Y]: (precede(X,Y) => ~precede(Y,X))).

% % A2: precedence is transitive
% fof(a2, axiom, ![X,Y,Z]: ((precede(X,Y) & precede(Y,Z)) => precede(X,Z))).

% % A3: overlap is reflexive
% fof(a3, axiom, ![X]: overlap(X,X)).

% % A4: overlap is symmetric
% fof(a4, axiom, ![X,Y]: (overlap(X,Y) <=> overlap(Y,X))).

% % A5: precedence excludes overlap
% fof(a5, axiom, ![X,Y]: (precede(X,Y) => ~overlap(X,Y))).

% % A6: precedence is preserved across overlap
% fof(a6, axiom, ![X,Y,Z,T]: ((precede(X,Y) & overlap(Y,Z) & precede(Z,T)) => precede(X,T))).

% % A7: trichotomy — any two intervals are related
% fof(a7, axiom, ![X,Y]: (precede(X,Y) | overlap(X,Y) | precede(Y,X))).

% A8: include definition
fof(a8, axiom, ![X,Y]: (include(X,Y) <=> (![Z]: (overlap(Z,Y) => overlap(Z,X))))).

% A8: total_overlap definition
fof(a9, axiom, ![X,Y]: (total_overlap(X,Y) <=> (include(X,Y) & include(Y,X)))).