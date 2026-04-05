"""
Utilitário para criar/atualizar usuários diretamente no banco.
Use quando tiver problemas com HASH_LUCAS no .env do Windows,
ou para criar o primeiro admin antes de subir o sistema.

Uso:
    docker exec qualidade-app-1 python3 app/criar_usuario.py <usuario> "<Nome>" <senha> [papel]

Papéis válidos: admin | inspetor | visitante (padrão: inspetor)

Exemplos:
    docker exec qualidade-app-1 python3 app/criar_usuario.py lucas "Lucas Silva" minhasenha admin
    docker exec qualidade-app-1 python3 app/criar_usuario.py joao "João Souza" senha123 inspetor
"""
import sys
import sqlite3
import bcrypt
import os

DB_FILE     = os.getenv("DB_FILE", "/data/dados_inspecoes.db")
PAPEIS_OK   = {"admin", "inspetor", "visitante"}

def criar_ou_atualizar(usuario: str, nome: str, senha: str, papel: str = "inspetor"):
    if papel not in PAPEIS_OK:
        print(f"ERR: Papel inválido: '{papel}'. Use: admin, inspetor ou visitante.")
        sys.exit(1)

    h    = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(DB_FILE)

    # Migração silenciosa: garante que a coluna papel existe
    try:
        conn.execute("ALTER TABLE usuarios ADD COLUMN papel TEXT DEFAULT 'inspetor'")
        conn.commit()
    except Exception:
        pass

    existente = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
    if existente:
        conn.execute(
            "UPDATE usuarios SET hash_senha=?, nome=?, papel=?, ativo=1 WHERE usuario=?",
            (h, nome, papel, usuario)
        )
        print(f"OK: Usuário '{usuario}' atualizado (papel={papel}).")
    else:
        conn.execute(
            "INSERT INTO usuarios (usuario, nome, hash_senha, papel) VALUES (?,?,?,?)",
            (usuario, nome, h, papel)
        )
        print(f"OK: Usuário '{usuario}' criado com sucesso (papel={papel}).")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 app/criar_usuario.py <usuario> <nome> <senha> [papel]")
        print('Ex:  python3 app/criar_usuario.py lucas "Lucas Silva" minhasenha admin')
        sys.exit(1)

    _usuario = sys.argv[1]
    _nome    = sys.argv[2]
    _senha   = sys.argv[3]
    _papel   = sys.argv[4] if len(sys.argv) > 4 else "inspetor"

    criar_ou_atualizar(_usuario, _nome, _senha, _papel)
