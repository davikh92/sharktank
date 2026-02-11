import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get('SMOKE_BASE_URL', os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8000')).rstrip('/')


@pytest.mark.smoke
def test_main_flow_smoke():
    try:
        health = requests.get(f'{BASE_URL}/api/', timeout=10)
    except requests.RequestException:
        pytest.skip('Backend indisponível para smoke test (SMOKE_BASE_URL).')

    if health.status_code >= 500:
        pytest.skip('Backend indisponível para smoke test.')

    email = f'smoke-{uuid.uuid4().hex[:8]}@example.com'
    password = 'SmokePass123!'

    register = requests.post(
        f'{BASE_URL}/api/auth/register',
        json={'email': email, 'password': password},
        timeout=20,
    )
    assert register.status_code == 200, register.text

    token = register.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    session_payload = {
        'pitch': {
            'titulo': 'Smoke Startup',
            'problema': 'Fluxo manual ineficiente',
            'solucao': 'Automação com IA',
            'mercado': 'PMEs no Brasil',
            'modelo_negocio': 'SaaS mensal',
            'tracao': '10 clientes pagantes',
            'pedido_valor': 'R$ 500.000',
            'pedido_equity': '10%',
        },
        'reading_hints_enabled': True,
    }

    created = requests.post(f'{BASE_URL}/api/sessions', json=session_payload, headers=headers, timeout=30)
    assert created.status_code == 200, created.text
    session_id = created.json()['id']

    started = requests.post(f'{BASE_URL}/api/sessions/{session_id}/start', headers=headers, timeout=60)
    assert started.status_code == 200, started.text

    responded = requests.post(
        f'{BASE_URL}/api/sessions/{session_id}/respond',
        json={'content': 'Nosso CAC atual é de R$ 300 e LTV de R$ 4.200.'},
        headers=headers,
        timeout=90,
    )
    assert responded.status_code == 200, responded.text

    report = requests.post(f'{BASE_URL}/api/sessions/{session_id}/report', headers=headers, timeout=60)
    assert report.status_code in {200, 400}, report.text
