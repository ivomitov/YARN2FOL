fof(be_01_identity, axiom,
    ![X, Y, S, B]: (s(S) & be_01(B,S) & arg1(B,X) & arg2(B,Y) & overlaps(B,now) => X = Y)).

% domain_be-01
fof(domain_be_01, axiom,
    ![X, Y]: (domain(X,Y) <=> ?[S,B]: (s(S) & be_01(B,S) & arg1(B,Y) & arg2(B,X)))).

% mod_be-01 % present interpretation
fof(mod_be_01, axiom,
    ![X, Y]: (mod(X,Y) <=> ?[S,B]: (s(S) & be_01(B,S) & arg1(B,X) & arg2(B,Y) & overlaps(B,now) ))). 

% poss_have_03 % present interpretation
fof(poss_have_03, axiom,
    ![X, Y]: (poss(X,Y) <=> ?[S, H]: (s(S) & have_03(H,S) & arg0(H,Y) & arg1(H,X) & overlaps(H,now)))). 

fof(currently, axiom,
    ![X]: (time(X,currently) => overlaps(X,now))).

fof(currently_reverse, axiom,
    ![X]: (overlaps(X,now) => time(X,currently))).

fof(small_not_large, axiom,
    ![X]: (arg1(small_01,X) => ~arg1(large_01,X))).

fof(large_not_small, axiom,
    ![X]: (arg1(large_01,X) => ~arg1(small_01,X))).

fof(n1_not_plural, axiom,
    ![X]: (n1(X) => ~plural(X))).

fof(plural_not_n1, axiom, 
    ![X]: (plural(X) => ~n1(X))).

% === Definiteness (up to 5)
fof(unique_c1, axiom, ?[X]: (c1(X) & ![Y]: (c1(Y) => Y = X))).
fof(unique_c2, axiom, ?[X]: (c2(X) & ![Y]: (c2(Y) => Y = X))).
fof(unique_c3, axiom, ?[X]: (c3(X) & ![Y]: (c3(Y) => Y = X))).
fof(unique_c4, axiom, ?[X]: (c4(X) & ![Y]: (c4(Y) => Y = X))).
fof(unique_c5, axiom, ?[X]: (c5(X) & ![Y]: (c5(Y) => Y = X))).