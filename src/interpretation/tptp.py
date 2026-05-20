def fmt_temp_var(v):
    return v.lower() if v.lower() == "now" else v.upper()

def fmt_rel(rel, id2var):
    pred = rel[0].lower().replace("-", "_")
    
    def fmt_arg(arg):
        val = id2var[arg]
        if val.isupper():  # constant
            return val.lower()
        else:  # variable
            return val.upper()
    
    if len(rel) == 3:
        return f"{pred}({fmt_arg(rel[1])},{fmt_arg(rel[2])})"
    else:
        return f"{pred}({fmt_arg(rel[1])})"

def get_relations(node, id2var):
    and_rels = [fmt_rel(rel, id2var) for rel in node['relations']['and']]
    or_rels  = [fmt_rel(rel, id2var) for rel in node['relations']['or']]
    return and_rels + [f"({' | '.join(or_rels)})"] if or_rels else and_rels

def conj(parts):
    parts = [p for p in parts if p and p.strip()]
    return " & ".join(parts)

def wrap_quant(q, var, head, relations, bodies, connective="&"):
    rel = conj(relations)
    head_part = f"{head.lower().replace('-', '_')}({var.upper()})"
    left = f"{head_part} & {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        if connective == "=>":
            return f"{q}[{var.upper()}]: ({left}\n  => ({body}))"
        else:
            return f"{q}[{var.upper()}]: ({left}\n  & ({body}))"
    else:
        return f"{q}[{var.upper()}]: ({left})"

def wrap_generalized_quant(q, var, gen_quant, head, relations, bodies, connective="&"):
    rel = conj(relations)
    head_part = f"{head.lower().replace('-', '_')}({var.upper()}) & {gen_quant.lower()}({var.upper()})"
    left = f"{head_part} & {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        return f"{q}[{var.upper()}]: ({left}\n  & ({body}))"
    else:
        return f"{q}[{var.upper()}]: ({left})"

def wrap_temp(q, var, S, head, relations, bodies, connective="&"):
    rel = conj(relations)
    head_part = f"{head.lower().replace('-', '_')}({var.upper()},{S.upper()})"
    left = f"{head_part} & {rel}" if rel else head_part
    body = conj(bodies)
    if body:
        return f"{q}[{var.upper()}]: ({left}\n  & ({body}))"
    else:
        return f"{q}[{var.upper()}]: ({left})"

def clean_formula_tptp(formula):
    return formula.replace(" & ()", "")

def interpret_tptp(root, temp_variable, id2var):

    if root is None:
        return ""

    child_formulas = [interpret_tptp(child, temp_variable, id2var) for child in root["children"]]
    relations = get_relations(root, id2var)

    if root["type"] == "∃":
        return wrap_quant("?", root["variable"], root["tar_label"], relations, child_formulas)

    if root["type"] == "∀":
        return wrap_quant("!", root["variable"], root["tar_label"], relations, child_formulas, connective="=>")

    if root["type"].startswith("Q_"):
        gen_quant = root["type"][2:]
        return wrap_generalized_quant("?", root["variable"], gen_quant, root["tar_label"], relations, child_formulas)

    if root["type"] == "T_present":
        temp = f"overlap({root['variable'].upper()},{fmt_temp_var(temp_variable)})"
        child_formulas = [interpret_tptp(child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("?", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas)

    if root["type"] == "T_past":
        temp = f"precedes({root['variable'].upper()},{fmt_temp_var(temp_variable)})"
        child_formulas = [interpret_tptp(child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("?", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas)

    if root["type"] == "T_future":
        temp = f"precedes({fmt_temp_var(temp_variable)},{root['variable'].upper()})"
        child_formulas = [interpret_tptp(child, root["variable"], id2var) for child in root["children"]]
        return wrap_temp("?", root["variable"], root['S'], root["tar_label"], relations + [temp], child_formulas)

    if root["type"] == "neg":
        return f"~({conj(child_formulas)})"

    if root["type"] == "possibility":
        return f"possibly({conj(child_formulas)})"

    if root["type"] == "necessity":
        return f"necessarily({conj(child_formulas)})"