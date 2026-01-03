from __future__ import annotations
from rk_adels.instance import Instance, Container, Item
from rk_adels.de import run_decoder_only, run_rk_de, run_rk_ade

def main():
    inst = Instance(
        name="smoke",
        container=Container(W=50,H=50,D=50),
        items=[Item(w=10,h=10,d=10) for _ in range(40)]
    )
    print("H0", run_decoder_only(inst, seconds=2, seed=1).best_eval.V)
    print("A1", run_rk_de(inst, seconds=2, seed=2, NP=20).best_eval.V)
    print("A2", run_rk_ade(inst, seconds=2, seed=3, NP=20, use_local_search=False).best_eval.V)
    print("A3", run_rk_ade(inst, seconds=2, seed=4, NP=20, use_local_search=True).best_eval.V)

if __name__ == "__main__":
    main()
