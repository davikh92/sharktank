import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models import CounterOffer, EndingType, Offer, OfferStatus, OfferType
from negotiation_manager import NegotiationManager


def _manager():
    return NegotiationManager(
        db=None,
        session_id='session-test',
        pitch_data={'pedido_valor': 'R$ 500.000', 'pedido_equity': '10%'},
    )


def _offer(equity: str = '20%'):
    return Offer(
        id='offer-1',
        shark_id='shark-1',
        shark_name='O Financeiro',
        session_id='session-test',
        offer_type=OfferType.AGGRESSIVE,
        valor='R$ 500.000',
        equity=equity,
        status=OfferStatus.ACTIVE,
        turns_remaining=2,
        created_at_turn=1,
    )


def test_determine_ending_type_table_broken():
    manager = _manager()
    ending = manager.determine_ending_type(
        deals=[], offers_made=2, offers_withdrawn=1, original_equity=10.0
    )
    assert ending == EndingType.TABLE_BROKEN


def test_determine_ending_type_no_deal_without_offers_withdrawn():
    manager = _manager()
    ending = manager.determine_ending_type(
        deals=[], offers_made=0, offers_withdrawn=0, original_equity=10.0
    )
    assert ending == EndingType.NO_DEAL


def test_determine_ending_type_deal_bitter_for_high_equity():
    manager = _manager()
    ending = manager.determine_ending_type(
        deals=[{'shark_name': 'O Cético', 'valor': 'R$ 500.000', 'equity': '18%'}],
        offers_made=1,
        offers_withdrawn=0,
        original_equity=10.0,
    )
    assert ending == EndingType.DEAL_BITTER


def test_determine_ending_type_deal_closed_for_reasonable_equity():
    manager = _manager()
    ending = manager.determine_ending_type(
        deals=[{'shark_name': 'O Operador', 'valor': 'R$ 500.000', 'equity': '12%'}],
        offers_made=1,
        offers_withdrawn=0,
        original_equity=10.0,
    )
    assert ending == EndingType.DEAL_CLOSED


def test_evaluate_counter_offer_accepts_small_diff_when_interest_high(monkeypatch):
    manager = _manager()
    monkeypatch.setattr(random, 'random', lambda: 0.1)

    accepted = manager.evaluate_counter_offer(
        original_offer=_offer(equity='20%'),
        counter=CounterOffer(offer_id='offer-1', valor='R$ 500.000', equity='18%'),
        shark_interest=90,
        shark_confianca=75,
    )
    assert accepted is True


def test_evaluate_counter_offer_rejects_large_diff():
    manager = _manager()

    accepted = manager.evaluate_counter_offer(
        original_offer=_offer(equity='25%'),
        counter=CounterOffer(offer_id='offer-1', valor='R$ 500.000', equity='10%'),
        shark_interest=85,
        shark_confianca=80,
    )
    assert accepted is False
