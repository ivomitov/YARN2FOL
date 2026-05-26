% domain_be-01
fof(domain_be_01, axiom,
    ![X, Y]: (domain(X,Y) <=> ?[S,B]: (s(S) & be_01(B,S) & arg1(B,Y) & arg2(B,X)))).

% mod_be-01
fof(mod_be_01, axiom,
    ![X, Y]: (mod(X,Y) <=> ?[S,B]: (s(S) & be_01(B,S) & arg1(B,X) & arg2(B,Y) & overlaps(B,now) ))).

% poss_have_03
fof(poss_have_03, axiom,
    ![X, Y]: (poss(X,Y) <=> ?[S, H]: (s(S) & have_03(H,S) & arg0(H,Y) & arg1(H,X) & overlaps(H,now)))).