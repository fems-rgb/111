import ast
P = r"app\services\experiment_engine.py"
src = open(P, encoding="utf-8").read()
ast.parse(src)
print("SYNTAX OK, lines =", len(src.splitlines()))
print("fake code (np.random.rand):", "np.random.rand(60)" in src)
print("has AUTOCHART:", "[AUTOCHART" in src)
print("has df=_make_df:", "df = _make_df" in src)
