from modules.signal_engine import calculate_partial_sell_plan, calculate_rebuy_price, calculate_stop_loss, calculate_targets


def test_signal_prices():
    support = {"key_support_low": 98, "key_support_high": 102, "l1_price": 100}
    targets = calculate_targets(current_price=120, trigger_price=125, hh_price=150, l1_price=100)
    stop = calculate_stop_loss(support, {"position": "2파 말"})
    partial = calculate_partial_sell_plan(120, targets, holding_qty=10)
    rebuy = calculate_rebuy_price(partial["partial_sell_price"], support)
    assert targets["target_30d"] > 120
    assert stop == 97
    assert partial["partial_sell_qty"] == 3
    assert rebuy > 0
