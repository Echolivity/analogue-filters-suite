# Re-derive the MS-20 filter transfer functions (Korg35 Sallen-Key and LM13600 OTA versions). Needs sympy.
import sympy as sp
s, k, k1, k2 = sp.symbols('s k k1 k2'); Vin, V2, V3, Vo = sp.symbols('Vin V2 V3 Vo')
def sk(R1, R2, C1, C2, hp):
    a, b = (0, Vin) if hp else (Vin, 0)
    e1 = sp.Eq((a - V2) / R1 + (V3 - V2) / R2 + (k2 * Vo - V2) * s * C1, 0)
    e2 = sp.Eq((V2 - V3) / R2 + (b - V3) * s * C2, 0)
    sol = sp.solve([e1, e2, sp.Eq(Vo, k1 * V3)], [V2, V3, Vo], dict=True)[0]
    return sp.factor(sp.simplify(sol[Vo] / Vin))
print("SK equal RC HP:", sk(1, 1, 1, 1, 1))
print("Korg35 (R1=R2/3, C1=3C2) LP:", sk(sp.Rational(1, 3), 1, 3, 1, 0))
print("Korg35 (R1=R2/3, C1=3C2) HP:", sk(sp.Rational(1, 3), 1, 3, 1, 1))
sol = sp.solve([sp.Eq(V2 * (1 + s), k * Vo * s), sp.Eq(V3 * (1 + s), V2 + Vin * s), sp.Eq(Vo, V3)], [V2, V3, Vo], dict=True)[0]
print("OTA HP:", sp.factor(sp.simplify(sol[Vo] / Vin)))
