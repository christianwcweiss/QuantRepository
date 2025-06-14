from typing import List

import pytest
from quant_core.enums.asset_type import AssetType
from quant_core.enums.stagger_method import StaggerMethod
from quant_core.utils.trade_utils import calculate_position_size, get_stagger_levels


class TestTradeUtils:
    @pytest.mark.parametrize(
        "entry_price, exit_price, n_levels, expected_levels",
        [
            [100.0, 200.0, 1, [100.0]],
            [200.0, 100.0, 1, [200.0]],
            [100.0, 200.0, 5, [100.0, 108.33, 116.67, 133.33, 158.33]],
            [200.0, 100.0, 5, [200.0, 191.67, 183.33, 166.67, 141.67]],
            [100.0, 200.0, 2, [100.0, 150.0]],
            [200.0, 100.0, 2, [200.0, 150.0]],
        ],
    )
    def test_fibonacci_staggering(
        self,
        entry_price: float,
        exit_price: float,
        n_levels: int,
        expected_levels: List[float],
    ) -> None:
        levels = get_stagger_levels(
            from_price=entry_price,
            to_price=exit_price,
            k=n_levels,
            stagger_method=StaggerMethod.FIBONACCI,
        )

        assert len(levels) == n_levels
        assert [round(level, 2) for level in levels] == [round(level, 2) for level in expected_levels]
        assert exit_price not in levels

    @pytest.mark.parametrize(
        "entry_price, exit_price, n_levels, expected_levels",
        [
            [100.0, 200.0, 1, [100.0]],
            [200.0, 100.0, 1, [200.0]],
            [100.0, 200.0, 5, [100.0, 120.0, 140.0, 160.0, 180.0]],
            [200.0, 100.0, 5, [200.0, 180.0, 160.0, 140.0, 120.0]],
            [100.0, 200.0, 2, [100.0, 150.0]],
            [200.0, 100.0, 2, [200.0, 150.0]],
        ],
    )
    def test_linear_staggering(
        self,
        entry_price: float,
        exit_price: float,
        n_levels: int,
        expected_levels: List[float],
    ) -> None:
        levels = get_stagger_levels(
            from_price=entry_price,
            to_price=exit_price,
            k=n_levels,
            stagger_method=StaggerMethod.LINEAR,
        )

        assert len(levels) == len(expected_levels)
        assert [round(level, 2) for level in levels] == [round(level, 2) for level in expected_levels]

    @pytest.mark.parametrize(
        "entry_price, exit_price, n_levels, expected_levels",
        [
            [100.0, 200.0, 1, [100.0]],
            [200.0, 100.0, 1, [200.0]],
            [100.0, 200.0, 5, [100.0, 101.52, 105.33, 114.94, 139.13]],
            [200.0, 100.0, 5, [200.0, 198.48, 194.67, 185.06, 160.87]],
            [100.0, 200.0, 2, [100.0, 109.05]],
            [200.0, 100.0, 2, [200.0, 190.95]],
        ],
    )
    def test_logarithmic_staggering(
        self,
        entry_price: float,
        exit_price: float,
        n_levels: int,
        expected_levels: List[float],
    ) -> None:
        levels = get_stagger_levels(
            from_price=entry_price,
            to_price=exit_price,
            k=n_levels,
            stagger_method=StaggerMethod.LOGARITHMIC,
        )

        assert len(levels) == len(expected_levels)
        assert [round(level, 2) for level in levels] == [round(level, 2) for level in expected_levels]

    @pytest.mark.parametrize(
        "entry_price,stop_loss_price,percentage_risk,balance,asset_type,decimal_points,lot_size,expected_size",
        [
            # LONG
            [
                3224,
                3182,
                1.0,
                30000.0,
                AssetType.COMMODITIES,
                2,
                100,
                0.07,
            ],
            [
                2390,
                2490,
                1,
                1000.0,
                AssetType.CRYPTO,
                2,
                1,
                0.1,
            ],
            [
                1.133,
                1.129,
                0.5,
                1000.0,
                AssetType.FOREX,
                5,
                100000,
                0.01,
            ],
            [
                8331,
                8278,
                0.5,
                80000,
                AssetType.INDICES,
                2,
                1.0,
                7.55,
            ],
        ],
    )
    def test_calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        percentage_risk: float,
        balance: float,
        asset_type: AssetType,
        decimal_points: int,
        lot_size: float,
        expected_size: float,
    ) -> None:
        actual_size = calculate_position_size(
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            percentage_risk=percentage_risk,
            balance=balance,
            asset_type=asset_type,
            decimal_points=decimal_points,
            lot_size=lot_size,
        )

        assert actual_size == expected_size
