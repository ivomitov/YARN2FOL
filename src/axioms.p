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

% fof(unique_proper_name, axiom,
%     ![X, Y]: ((name(X,mickey) & name(Y,mickey)) => X = Y)).