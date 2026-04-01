# tests/test_auth.py

def test_pagina_login_carrega(client):
    """Verifica se a página HTML de login abre corretamente (Status 200)"""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sistema de Qualidade" in response.text

def test_login_demo(client):
    """Verifica se o botão de visitante cria o cookie de sessão e redireciona"""
    response = client.post("/login-demo", allow_redirects=False)
    # 303 significa que ele tentou redirecionar para o dashboard (sucesso)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "sessao" in response.cookies

def test_login_falha_senha_errada(client):
    """Verifica se o sistema barra senhas incorretas"""
    response = client.post(
        "/login", 
        data={"usuario": "admin_teste", "senha": "senha_errada"}
    )
    assert response.status_code == 200 # Retorna 200 pois recarrega o HTML do login
    assert "Usuário ou senha incorretos" in response.text

def test_login_sucesso(client):
    """Verifica se o usuário de teste consegue fazer login"""
    response = client.post(
        "/login", 
        data={"usuario": "admin_teste", "senha": "senha123"},
        allow_redirects=False
    )
    assert response.status_code == 303
    assert "sessao" in response.cookies