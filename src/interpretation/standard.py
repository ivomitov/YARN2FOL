def fmt_rel(rel, id2var):
    pred = rel[0]
    if len(rel) == 3:
        return f"{pred}({id2var[rel[1]]},{id2var[rel[2]]})"
    else:
        return f"{pred}({id2var[rel[1]]})"

def get_relations(node, id2var):
    and_rels = [fmt_rel(rel, id2var) for rel in node['relations']['and']]
    or_rels  = [fmt_rel(rel, id2var) for rel in node['relations']['or']]
    return and_rels + [f"({' ∨ '.join(or_rels)})"] if or_rels else and_rels

def conj(parts):
    parts = [p for p in parts if p and p.strip()]
    return " ∧ ".join(parts)


def wrap_quant(q, var, head, relations, bodies, connective="∧"):
    rel = conj(relations)
    head_part = f"{head}({var})"
    left = f"{head_part} ∧ {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        return f"{q}{var}. ( {left}\n {connective} ({body}) )"
    else:
        return f"{q}{var}. ( {left} )"
    
def wrap_generalized_quant(q, var, gen_quant, head, relations, bodies, connective="∧"):
    rel = conj(relations)
    head_part = f"{head}({var}) ∧ {gen_quant}({var})"
    left = f"{head_part} ∧ {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        return f"{q}{var}. ( {left}\n {connective} ({body}) )"
    else:
        return f"{q}{var}. ( {left} )"
    
def wrap_temp(q, var, S, head, relations, bodies, connective="∧"):
    rel = conj(relations)
    head_part = f"{head}({var},{S})"
    left = f"{head_part} ∧ {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        return f"{q}{var}. ( {left}\n {connective} ({body}) )"
    else:
        return f"{q}{var}. ( {left} )"

def clean_formula_std(formula):
    clean_formula = formula.replace(" ∧ ()", "")
    return clean_formula

def interpret_std(root, temp_variable, id2var):
    
    if root is None:
        return ""

    child_formulas = [interpret_std
(child, temp_variable, id2var) for child in root["children"]]
    relations = get_relations(root, id2var)

    if root["type"] == "∃":
        return wrap_quant("∃", root["variable"], root["tar_label"], relations, child_formulas, connective="∧")
    
    if root["type"] == "∀":
        return wrap_quant("∀", root["variable"], root["tar_label"], relations, child_formulas, connective="→")
    
    if root["type"].startswith("Q_"):
        gen_quant = root["type"][2:] # disallow whitespaces
        return wrap_generalized_quant("∃", root["variable"], gen_quant, root["tar_label"], relations, child_formulas, connective="∧")
    
    if root["type"] == "T_present":
        temp = f"{root['variable']}_O_{temp_variable}"
        child_formulas = [interpret_std
    (child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("∃", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas, connective="∧")

    if root["type"] == "T_past":
        temp = f"{root['variable']}≺{temp_variable}"
        child_formulas = [interpret_std
    (child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("∃", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas, connective="∧")
    
    if root["type"] == "T_future":
        temp = f"{temp_variable}≺{root['variable']}"
        child_formulas = [interpret_std
    (child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("∃", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas, connective="∧")
    
    if root["type"] == "neg":
        return f"¬ ( {conj(child_formulas)} )"
    
    if root["type"] == "possibility":
        return f"◇ ( {conj(child_formulas)} )"

    if root["type"] == "necessity":
        return f"□ ( {conj(child_formulas)} )"