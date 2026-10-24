import pytest

from hubspoke import prompts, scripted
from hubspoke.agents import AdvisorObs, Memo, Row, SellerObs
from hubspoke.conditions import conditions, get_condition
from hubspoke.game import ALPHAS, Game, RunConfig
from hubspoke.market import Market
from hubspoke.parsing import parse_reply, to_price


def test_benchmarks_match_calvano():
    b = Market().benchmarks()
    assert b.p_nash == pytest.approx(1.473, abs=1e-3)
    assert b.p_mono == pytest.approx(1.925, abs=1e-3)


def test_parsing_tolerates_common_slips():
    assert to_price(parse_reply('```json\n{"price": "$1,850.50", "plan": "x"}\n```')["price"]) == 1850.5
    assert to_price(parse_reply('price: 2.10 because ...')["price"]) == 2.10
    assert parse_reply("no number here") is None


def _obs_texts(cond_name: str) -> list[str]:
    c = get_condition(cond_name)
    hist = [Row(1, 1.8, 30.0, 24.0, [1.9]), Row(2, 1.85, 31.0, 26.0, [1.9])]
    so = SellerObs("Firm A", 0, 3, 2, 1.0, hist, ["Firm B"], advisor=c.advisor, rec=1.9, rec_note="hold", chat=c.chat)
    texts = [prompts.seller_system(so), prompts.seller_user(so)]
    if c.advisor:
        ao = AdvisorObs("Firm A", 0, 3, 2, 1.0, hist, ["Firm B"], c,
                        portfolio=None if c.data_lag is None else [("Firm B", hist)],
                        live_recs=[] if c.live_recs else None, memos=[Memo(2, "Firm B", "note")])
        texts += [prompts.advisor_system(ao), prompts.advisor_user(ao)]
    return texts


@pytest.mark.parametrize("cond", list(conditions()))
def test_prompts_are_neutral(cond):
    for text in _obs_texts(cond):
        low = text.lower()
        assert not [w for w in prompts.BANNED if w in low], (cond, text)


def test_information_boundaries():
    m = Market(alpha=ALPHAS[0])
    for cond, lag in (("isolated", None), ("pooled", 1), ("aged", 12)):
        g = Game(RunConfig(cond, seed=0, T=16), [scripted.FollowRec(m), scripted.FollowRec(m)],
                 scripted.PoolingAdvisor(m))
        g.run()
        for rec in g.log:
            for a in rec["advisor"]:
                port = a["obs"]["portfolio"]
                if lag is None:
                    assert port is None
                else:
                    assert all(r["t"] <= rec["t"] - lag for _, rows in port for r in rows)


def test_private_notebooks_stay_private():
    m = Market(alpha=ALPHAS[0])

    class Writer(scripted.IndependentAdvisor):
        def act(self, obs, ctx):
            a = super().act(obs, ctx)
            a.memo = f"secret-{obs.firm}-{obs.t}"
            return a

    for cond, shared in (("aged", False), ("aged_sharedmem", True)):
        g = Game(RunConfig(cond, seed=0, T=5), [scripted.FollowRec(m), scripted.FollowRec(m)], Writer(m))
        g.run()
        seen_other = any(mm["firm"] != a["obs"]["firm"] for rec in g.log for a in rec["advisor"]
                         for mm in a["obs"]["memos"])
        assert seen_other == shared


def test_fork_from_snapshot_is_deterministic():
    m = Market(alpha=ALPHAS[1])
    g = Game(RunConfig("solo", seed=1, T=30, snapshot_at=25), [scripted.GrimTrigger(m), scripted.GrimTrigger(m)])
    g.run()
    from hubspoke.game import State
    g2 = Game(RunConfig("solo", seed=1, T=30), [scripted.GrimTrigger(m), scripted.GrimTrigger(m)],
              state=State.from_dict(g.snapshot))
    g2.run(5)
    assert [r["prices"] for r in g2.log] == [r["prices"] for r in g.log[25:]]
